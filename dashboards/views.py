# Django
from http.client import HTTPResponse
import re
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.http.response import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, ListView, TemplateView, DetailView, DeleteView, UpdateView, FormView
from django.views.generic.base import View

# Functions
from dashboards.functions import functions, functions_ftp
from aeto import settings

# Forms
from dashboards.forms import ExcelForm, LlantaForm, VehiculoForm

# Models
from django.contrib.auth.models import User
from dashboards.models import Aplicacion, Bitacora_Pro, Inspeccion, Llanta, Producto, Ubicacion, Vehiculo, Perfil, Bitacora, Compania

# Utilities
from datetime import date, datetime, timedelta
import json

class LoginView(auth_views.LoginView):
    # Vista de Login

    template_name = "login.html"
    redirect_authenticated_user = True

class HomeView(LoginRequiredMixin, TemplateView):
    # Vista de nuevo home

    template_name = "home.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user)
        flotas = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        aplicaciones = Aplicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        context["user"] = user
        context["flotas"] = flotas
        context["aplicaciones"] = aplicaciones
        return context



class TireDBView(LoginRequiredMixin, TemplateView):
    # Vista de tire-dashboard1

    template_name = "tire-dashboard.html"
    def get_context_data(self, **kwargs):
        
        clase = self.request.GET.get("clase")
        flota = self.request.GET.get("flota")
        pay_boton = self.request.GET.get("boton_intuitivo")

        context = super().get_context_data(**kwargs)
        vehiculo = Vehiculo.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        if clase:
            vehiculo_clase = vehiculo.filter(clase=clase.upper())
            bitacora_clase = bitacora.filter(numero_economico__in=vehiculo_clase)
            llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), vehiculo__in=vehiculo_clase)
            inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), llanta__in=llantas)
            hoy = date.today()
            
            periodo_2 = hoy - timedelta(days=self.request.user.perfil.compania.periodo2_inspeccion)
            vehiculos_vistos = vehiculo_clase.filter(ultima_inspeccion__fecha_hora__lte=periodo_2) | vehiculo_clase.filter(ultima_inspeccion__fecha_hora__isnull=True)
            porcentaje_visto = int((vehiculos_vistos.count()/vehiculo_clase.count()) * 100)

            filtro_sospechoso = functions.vehiculo_sospechoso(inspecciones)
            vehiculos_sospechosos = vehiculo_clase.filter(id__in=filtro_sospechoso)
            porcentaje_sospechoso = int((vehiculos_sospechosos.count()/vehiculo_clase.count()) * 100)

            doble_entrada = functions.doble_entrada(bitacora_clase)
            filtro_rojo = functions.vehiculo_rojo(llantas, doble_entrada[0])
            vehiculos_rojos = vehiculo_clase.filter(id__in=filtro_rojo).exclude(id__in=vehiculos_sospechosos)
            porcentaje_rojo = int((vehiculos_rojos.count()/vehiculo_clase.count()) * 100)

            filtro_amarillo = functions.vehiculo_amarillo(llantas)
            vehiculos_amarillos = vehiculo_clase.filter(id__in=filtro_amarillo).exclude(id__in=vehiculos_rojos).exclude(id__in=vehiculos_sospechosos)
            porcentaje_amarillo = int((vehiculos_amarillos.count()/vehiculo_clase.count()) * 100)


            if pay_boton == "Dualización":
                desdualizacion_encontrada = functions.desdualizacion(llantas, True)
                if desdualizacion_encontrada:
                    desdualizacion_encontrada_existente = True
                else:
                    desdualizacion_encontrada_existente = False
                desdualizacion_actual = functions.desdualizacion(llantas, True)
                if desdualizacion_actual:
                    desdualizacion_actual_existente = True
                else:
                    desdualizacion_actual_existente = False
                
                context["pay_boton"] = "dualizacion"
                context["parametro_actual_existente"] = desdualizacion_actual_existente
                context["parametro_encontrado_existente"] = desdualizacion_encontrada_existente
                context["parametro_actual"] = desdualizacion_actual
                context["parametro_encontrado"] = desdualizacion_encontrada
            elif pay_boton == "Presión":
                presion_encontrada = functions.presion_llantas(llantas, True)
                presion_actual = functions.presion_llantas(llantas, True)
                context["pay_boton"] = "presion"
                context["parametro_actual_existente"] = presion_actual.exists()
                context["parametro_encontrado_existente"] = presion_encontrada.exists()
                context["parametro_actual"] = presion_actual
                context["parametro_encontrado"] = presion_encontrada
            else:
                desgaste_irregular_encontrado = functions.desgaste_irregular(llantas, True)
                desgaste_irregular_actual = functions.desgaste_irregular(llantas, True)
                context["pay_boton"] = "desgaste"
                context["parametro_actual_existente"] = bool(desgaste_irregular_actual)
                context["parametro_encontrado_existente"] = bool(desgaste_irregular_encontrado)
                context["parametro_actual"] = desgaste_irregular_actual
                context["parametro_encontrado"] = desgaste_irregular_encontrado


            mes_1 = hoy.strftime("%b")
            mes_2 = functions.mes_anterior(hoy)
            mes_3 = functions.mes_anterior(mes_2)
            mes_4 = functions.mes_anterior(mes_3)

            hoy1 = hoy.strftime("%m")
            hoy2 = mes_2.strftime("%m")
            hoy3 = mes_3.strftime("%m")
            hoy4 = mes_4.strftime("%m")

            vehiculos_vistos_mes_1 = vehiculo_flota.filter(ultima_inspeccion__fecha_hora__month=hoy1)
            vehiculos_vistos_mes_2 = vehiculo_flota.filter(ultima_inspeccion__fecha_hora__month=hoy2)
            vehiculos_vistos_mes_3 = vehiculo_flota.filter(ultima_inspeccion__fecha_hora__month=hoy3)
            vehiculos_vistos_mes_4 = vehiculo_flota.filter(ultima_inspeccion__fecha_hora__month=hoy4)

            vehiculos_rojos_copia = vehiculo_flota.filter(id__in=filtro_rojo)
            vehiculos_rojos_mes_1 = vehiculos_rojos_copia.filter(ultima_inspeccion__fecha_hora__month=hoy1)
            vehiculos_rojos_mes_2 = vehiculos_rojos_copia.filter(ultima_inspeccion__fecha_hora__month=hoy2).exclude(pk__in=vehiculos_rojos_mes_1)
            vehiculos_rojos_mes_3 = vehiculos_rojos_copia.filter(ultima_inspeccion__fecha_hora__month=hoy3).exclude(pk__in=vehiculos_rojos_mes_2)
            vehiculos_rojos_mes_4 = vehiculos_rojos_copia.filter(ultima_inspeccion__fecha_hora__month=hoy4).exclude(pk__in=vehiculos_rojos_mes_3)


            vehiculos_amarillos_mes_1 = vehiculos_amarillos.filter(ultima_inspeccion__fecha_hora__month=hoy1)
            vehiculos_amarillos_mes_2 = vehiculos_amarillos.filter(ultima_inspeccion__fecha_hora__month=hoy2)
            vehiculos_amarillos_mes_3 = vehiculos_amarillos.filter(ultima_inspeccion__fecha_hora__month=hoy3)
            vehiculos_amarillos_mes_4 = vehiculos_amarillos.filter(ultima_inspeccion__fecha_hora__month=hoy4)

            vehiculos_sospechosos_mes_1 = vehiculos_sospechosos.filter(ultima_inspeccion__fecha_hora__month=hoy1)
            vehiculos_sospechosos_mes_2 = vehiculos_sospechosos.filter(ultima_inspeccion__fecha_hora__month=hoy2)
            vehiculos_sospechosos_mes_3 = vehiculos_sospechosos.filter(ultima_inspeccion__fecha_hora__month=hoy3)
            vehiculos_sospechosos_mes_4 = vehiculos_sospechosos.filter(ultima_inspeccion__fecha_hora__month=hoy4)

            estatus_profundidad = functions.estatus_profundidad(llantas)

            nunca_vistos = functions.nunca_vistos(vehiculo_clase)
            renovables = functions.renovables(llantas, vehiculos_amarillos)
            sin_informacion = functions.sin_informacion(llantas)

            porcentaje_vehiculos_inspeccionados_por_aplicacion = functions.vehiculos_inspeccionados_por_aplicacion(vehiculo_clase)
            porcentaje_vehiculos_inspeccionados_por_clase = functions.vehiculos_inspeccionados_por_clase(vehiculo_clase)


            vehiculos_por_clase_sin_inspeccionar = functions.vehiculos_por_clase_sin_inspeccionar(vehiculo_clase, hoy, mes_1, mes_2.strftime("%b"), mes_3.strftime("%b"))
            clase_sin_inspeccionar_mes_1 = {}
            clase_sin_inspeccionar_mes_2 = {}
            clase_sin_inspeccionar_mes_3 = {}
            for cls in vehiculos_por_clase_sin_inspeccionar:
                clase_sin_inspeccionar_mes_1[cls["clase"]] = cls["mes1"]
                clase_sin_inspeccionar_mes_2[cls["clase"]] = cls["mes2"]
                clase_sin_inspeccionar_mes_3[cls["clase"]] = cls["mes3"]

            context["clase_sin_inspeccionar_mes_1"] = clase_sin_inspeccionar_mes_1
            context["clase_sin_inspeccionar_mes_2"] = clase_sin_inspeccionar_mes_2
            context["clase_sin_inspeccionar_mes_3"] = clase_sin_inspeccionar_mes_3
            context["clases_mas_frecuentes_infladas"] = functions.clases_mas_frecuentes(vehiculo, self.request.user.perfil.compania)
            context["estatus_profundidad"] = estatus_profundidad
            context["flotas"] = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            context["mes_1"] = mes_1
            context["mes_2"] = mes_2.strftime("%b")
            context["mes_3"] = mes_3.strftime("%b")
            context["mes_4"] = mes_4.strftime("%b")
            context["nunca_vistos"] = nunca_vistos
            context["porcentaje_amarillo"] = porcentaje_amarillo
            context["porcentaje_vehiculos_inspeccionados_por_aplicacion"] = porcentaje_vehiculos_inspeccionados_por_aplicacion
            context["porcentaje_vehiculos_inspeccionados_por_clase"] = porcentaje_vehiculos_inspeccionados_por_clase
            context["porcentaje_rojo"] = porcentaje_rojo
            context["porcentaje_sospechoso"] = porcentaje_sospechoso
            context["porcentaje_visto"] = porcentaje_visto
            context["renovables"] = renovables
            context["sin_informacion"] = sin_informacion
            context["vehiculos_amarillos"] = vehiculos_amarillos.count()
            context["vehiculos_amarillos_mes_1"] = vehiculos_amarillos_mes_1.count()
            context["vehiculos_amarillos_mes_2"] = vehiculos_amarillos_mes_2.count()
            context["vehiculos_amarillos_mes_3"] = vehiculos_amarillos_mes_3.count()
            context["vehiculos_amarillos_mes_4"] = vehiculos_amarillos_mes_4.count()
            context["vehiculos_por_clase_sin_inspeccionar"] = vehiculos_por_clase_sin_inspeccionar
            context["vehiculos_rojos"] = vehiculos_rojos.count()
            context["vehiculos_rojos_mes_1"] = vehiculos_rojos_mes_1.count()
            context["vehiculos_rojos_mes_2"] = vehiculos_rojos_mes_2.count()
            context["vehiculos_rojos_mes_3"] = vehiculos_rojos_mes_3.count()
            context["vehiculos_rojos_mes_4"] = vehiculos_rojos_mes_4.count()
            context["vehiculos_sospechosos"] = vehiculos_sospechosos.count()
            context["vehiculos_sospechosos_mes_1"] = vehiculos_sospechosos_mes_1.count()
            context["vehiculos_sospechosos_mes_2"] = vehiculos_sospechosos_mes_2.count()
            context["vehiculos_sospechosos_mes_3"] = vehiculos_sospechosos_mes_3.count()
            context["vehiculos_sospechosos_mes_4"] = vehiculos_sospechosos_mes_4.count()
            context["vehiculos_vistos"] = vehiculos_vistos.count()
            context["vehiculos_vistos_mes_1"] = vehiculos_vistos_mes_1.count()
            context["vehiculos_vistos_mes_2"] = vehiculos_vistos_mes_2.count()
            context["vehiculos_vistos_mes_3"] = vehiculos_vistos_mes_3.count()
            context["vehiculos_vistos_mes_4"] = vehiculos_vistos_mes_4.count()
            context["vehiculos_totales"] = vehiculo_clase.count()
            return context
        elif flota:
            vehiculo_flota = vehiculo.filter(ubicacion__nombre=flota)
            bitacora_flota = bitacora.filter(numero_economico__in=vehiculo_flota)
            llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), vehiculo__in=vehiculo_flota)
            inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), llanta__in=llantas)
            hoy = date.today()
            
            periodo_2 = hoy - timedelta(days=self.request.user.perfil.compania.periodo2_inspeccion)
            vehiculos_vistos = vehiculo_flota.filter(ultima_inspeccion__fecha_hora__lte=periodo_2) | vehiculo_flota.filter(ultima_inspeccion__fecha_hora__isnull=True)
            porcentaje_visto = int((vehiculos_vistos.count()/vehiculo_flota.count()) * 100)

            filtro_sospechoso = functions.vehiculo_sospechoso(inspecciones)
            vehiculos_sospechosos = vehiculo_flota.filter(id__in=filtro_sospechoso)
            porcentaje_sospechoso = int((vehiculos_sospechosos.count()/vehiculo_flota.count()) * 100)

            doble_entrada = functions.doble_entrada(bitacora_flota)
            filtro_rojo = functions.vehiculo_rojo(llantas, doble_entrada[0])
            vehiculos_rojos = vehiculo_flota.filter(id__in=filtro_rojo).exclude(id__in=vehiculos_sospechosos)
            porcentaje_rojo = int((vehiculos_rojos.count()/vehiculo_flota.count()) * 100)

            filtro_amarillo = functions.vehiculo_amarillo(llantas)
            vehiculos_amarillos = vehiculo_flota.filter(id__in=filtro_amarillo).exclude(id__in=vehiculos_rojos).exclude(id__in=vehiculos_sospechosos)
            porcentaje_amarillo = int((vehiculos_amarillos.count()/vehiculo_flota.count()) * 100)


            if pay_boton == "Dualización":
                desdualizacion_encontrada = functions.desdualizacion(llantas, True)
                if desdualizacion_encontrada:
                    desdualizacion_encontrada_existente = True
                else:
                    desdualizacion_encontrada_existente = False
                desdualizacion_actual = functions.desdualizacion(llantas, True)
                if desdualizacion_actual:
                    desdualizacion_actual_existente = True
                else:
                    desdualizacion_actual_existente = False
                
                context["pay_boton"] = "dualizacion"
                context["parametro_actual_existente"] = desdualizacion_actual_existente
                context["parametro_encontrado_existente"] = desdualizacion_encontrada_existente
                context["parametro_actual"] = desdualizacion_actual
                context["parametro_encontrado"] = desdualizacion_encontrada
            elif pay_boton == "Presión":
                presion_encontrada = functions.presion_llantas(llantas, True)
                presion_actual = functions.presion_llantas(llantas, True)
                context["pay_boton"] = "presion"
                context["parametro_actual_existente"] = presion_actual.exists()
                context["parametro_encontrado_existente"] = presion_encontrada.exists()
                context["parametro_actual"] = presion_actual
                context["parametro_encontrado"] = presion_encontrada
            else:
                desgaste_irregular_encontrado = functions.desgaste_irregular(llantas, True)
                desgaste_irregular_actual = functions.desgaste_irregular(llantas, True)
                context["pay_boton"] = "desgaste"
                context["parametro_actual_existente"] = bool(desgaste_irregular_actual)
                context["parametro_encontrado_existente"] = bool(desgaste_irregular_encontrado)
                context["parametro_actual"] = desgaste_irregular_actual
                context["parametro_encontrado"] = desgaste_irregular_encontrado


            mes_1 = hoy.strftime("%b")
            mes_2 = functions.mes_anterior(hoy)
            mes_3 = functions.mes_anterior(mes_2)
            mes_4 = functions.mes_anterior(mes_3)

            hoy1 = hoy.strftime("%m")
            hoy2 = mes_2.strftime("%m")
            hoy3 = mes_3.strftime("%m")
            hoy4 = mes_4.strftime("%m")

            vehiculos_vistos_mes_1 = vehiculo_flota.filter(ultima_inspeccion__fecha_hora__month=hoy1)
            vehiculos_vistos_mes_2 = vehiculo_flota.filter(ultima_inspeccion__fecha_hora__month=hoy2)
            vehiculos_vistos_mes_3 = vehiculo_flota.filter(ultima_inspeccion__fecha_hora__month=hoy3)
            vehiculos_vistos_mes_4 = vehiculo_flota.filter(ultima_inspeccion__fecha_hora__month=hoy4)

            vehiculos_rojos_copia = vehiculo_flota.filter(id__in=filtro_rojo)
            vehiculos_rojos_mes_1 = vehiculos_rojos_copia.filter(ultima_inspeccion__fecha_hora__month=hoy1)
            vehiculos_rojos_mes_2 = vehiculos_rojos_copia.filter(ultima_inspeccion__fecha_hora__month=hoy2).exclude(pk__in=vehiculos_rojos_mes_1)
            vehiculos_rojos_mes_3 = vehiculos_rojos_copia.filter(ultima_inspeccion__fecha_hora__month=hoy3).exclude(pk__in=vehiculos_rojos_mes_2)
            vehiculos_rojos_mes_4 = vehiculos_rojos_copia.filter(ultima_inspeccion__fecha_hora__month=hoy4).exclude(pk__in=vehiculos_rojos_mes_3)


            vehiculos_amarillos_mes_1 = vehiculos_amarillos.filter(ultima_inspeccion__fecha_hora__month=hoy1)
            vehiculos_amarillos_mes_2 = vehiculos_amarillos.filter(ultima_inspeccion__fecha_hora__month=hoy2)
            vehiculos_amarillos_mes_3 = vehiculos_amarillos.filter(ultima_inspeccion__fecha_hora__month=hoy3)
            vehiculos_amarillos_mes_4 = vehiculos_amarillos.filter(ultima_inspeccion__fecha_hora__month=hoy4)

            vehiculos_sospechosos_mes_1 = vehiculos_sospechosos.filter(ultima_inspeccion__fecha_hora__month=hoy1)
            vehiculos_sospechosos_mes_2 = vehiculos_sospechosos.filter(ultima_inspeccion__fecha_hora__month=hoy2)
            vehiculos_sospechosos_mes_3 = vehiculos_sospechosos.filter(ultima_inspeccion__fecha_hora__month=hoy3)
            vehiculos_sospechosos_mes_4 = vehiculos_sospechosos.filter(ultima_inspeccion__fecha_hora__month=hoy4)

            estatus_profundidad = functions.estatus_profundidad(llantas)

            nunca_vistos = functions.nunca_vistos(vehiculo_flota)
            renovables = functions.renovables(llantas, vehiculos_amarillos)
            sin_informacion = functions.sin_informacion(llantas)

            porcentaje_vehiculos_inspeccionados_por_aplicacion = functions.vehiculos_inspeccionados_por_aplicacion(vehiculo_flota)
            porcentaje_vehiculos_inspeccionados_por_clase = functions.vehiculos_inspeccionados_por_clase(vehiculo_flota)

            vehiculos_por_clase_sin_inspeccionar = functions.vehiculos_por_clase_sin_inspeccionar(vehiculo_flota, hoy, mes_1, mes_2.strftime("%b"), mes_3.strftime("%b"))
            clase_sin_inspeccionar_mes_1 = {}
            clase_sin_inspeccionar_mes_2 = {}
            clase_sin_inspeccionar_mes_3 = {}
            for cls in vehiculos_por_clase_sin_inspeccionar:
                clase_sin_inspeccionar_mes_1[cls["clase"]] = cls["mes1"]
                clase_sin_inspeccionar_mes_2[cls["clase"]] = cls["mes2"]
                clase_sin_inspeccionar_mes_3[cls["clase"]] = cls["mes3"]

            context["clase_sin_inspeccionar_mes_1"] = clase_sin_inspeccionar_mes_1
            context["clase_sin_inspeccionar_mes_2"] = clase_sin_inspeccionar_mes_2
            context["clase_sin_inspeccionar_mes_3"] = clase_sin_inspeccionar_mes_3
            context["clases_mas_frecuentes_infladas"] = functions.clases_mas_frecuentes(vehiculo, self.request.user.perfil.compania)
            context["estatus_profundidad"] = estatus_profundidad
            context["flotas"] = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            context["mes_1"] = mes_1
            context["mes_2"] = mes_2.strftime("%b")
            context["mes_3"] = mes_3.strftime("%b")
            context["mes_4"] = mes_4.strftime("%b")
            context["nunca_vistos"] = nunca_vistos
            context["porcentaje_amarillo"] = porcentaje_amarillo
            context["porcentaje_vehiculos_inspeccionados_por_aplicacion"] = porcentaje_vehiculos_inspeccionados_por_aplicacion
            context["porcentaje_vehiculos_inspeccionados_por_clase"] = porcentaje_vehiculos_inspeccionados_por_clase
            context["porcentaje_rojo"] = porcentaje_rojo
            context["porcentaje_sospechoso"] = porcentaje_sospechoso
            context["porcentaje_visto"] = porcentaje_visto
            context["renovables"] = renovables
            context["sin_informacion"] = sin_informacion
            context["vehiculos_amarillos"] = vehiculos_amarillos.count()
            context["vehiculos_amarillos_mes_1"] = vehiculos_amarillos_mes_1.count()
            context["vehiculos_amarillos_mes_2"] = vehiculos_amarillos_mes_2.count()
            context["vehiculos_amarillos_mes_3"] = vehiculos_amarillos_mes_3.count()
            context["vehiculos_amarillos_mes_4"] = vehiculos_amarillos_mes_4.count()
            context["vehiculos_por_clase_sin_inspeccionar"] = vehiculos_por_clase_sin_inspeccionar
            context["vehiculos_rojos"] = vehiculos_rojos.count()
            context["vehiculos_rojos_mes_1"] = vehiculos_rojos_mes_1.count()
            context["vehiculos_rojos_mes_2"] = vehiculos_rojos_mes_2.count()
            context["vehiculos_rojos_mes_3"] = vehiculos_rojos_mes_3.count()
            context["vehiculos_rojos_mes_4"] = vehiculos_rojos_mes_4.count()
            context["vehiculos_sospechosos"] = vehiculos_sospechosos.count()
            context["vehiculos_sospechosos_mes_1"] = vehiculos_sospechosos_mes_1.count()
            context["vehiculos_sospechosos_mes_2"] = vehiculos_sospechosos_mes_2.count()
            context["vehiculos_sospechosos_mes_3"] = vehiculos_sospechosos_mes_3.count()
            context["vehiculos_sospechosos_mes_4"] = vehiculos_sospechosos_mes_4.count()
            context["vehiculos_vistos"] = vehiculos_vistos.count()
            context["vehiculos_vistos_mes_1"] = vehiculos_vistos_mes_1.count()
            context["vehiculos_vistos_mes_2"] = vehiculos_vistos_mes_2.count()
            context["vehiculos_vistos_mes_3"] = vehiculos_vistos_mes_3.count()
            context["vehiculos_vistos_mes_4"] = vehiculos_vistos_mes_4.count()
            context["vehiculos_totales"] = vehiculo_flota.count()
            return context
        else:
            llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            hoy = date.today()
            
            periodo_2 = hoy - timedelta(days=self.request.user.perfil.compania.periodo2_inspeccion)
            vehiculos_vistos = vehiculo.filter(ultima_inspeccion__fecha_hora__lte=periodo_2) | vehiculo.filter(ultima_inspeccion__fecha_hora__isnull=True)
            porcentaje_visto = int((vehiculos_vistos.count()/vehiculo.count()) * 100)

            filtro_sospechoso = functions.vehiculo_sospechoso(inspecciones)
            vehiculos_sospechosos = vehiculo.filter(id__in=filtro_sospechoso)
            porcentaje_sospechoso = int((vehiculos_sospechosos.count()/vehiculo.count()) * 100)

            doble_entrada = functions.doble_entrada(bitacora)
            filtro_rojo = functions.vehiculo_rojo(llantas, doble_entrada[0])
            vehiculos_rojos = vehiculo.filter(id__in=filtro_rojo).exclude(id__in=vehiculos_sospechosos)
            porcentaje_rojo = int((vehiculos_rojos.count()/vehiculo.count()) * 100)

            filtro_amarillo = functions.vehiculo_amarillo(llantas)
            vehiculos_amarillos = vehiculo.filter(id__in=filtro_amarillo).exclude(id__in=vehiculos_rojos).exclude(id__in=vehiculos_sospechosos)
            porcentaje_amarillo = int((vehiculos_amarillos.count()/vehiculo.count()) * 100)


            if pay_boton == "Dualización":
                desdualizacion_encontrada = functions.desdualizacion(llantas, True)
                if desdualizacion_encontrada:
                    desdualizacion_encontrada_existente = True
                else:
                    desdualizacion_encontrada_existente = False
                desdualizacion_actual = functions.desdualizacion(llantas, True)
                if desdualizacion_actual:
                    desdualizacion_actual_existente = True
                else:
                    desdualizacion_actual_existente = False
                
                context["pay_boton"] = "dualizacion"
                context["parametro_actual_existente"] = desdualizacion_actual_existente
                context["parametro_encontrado_existente"] = desdualizacion_encontrada_existente
                context["parametro_actual"] = desdualizacion_actual
                context["parametro_encontrado"] = desdualizacion_encontrada
            elif pay_boton == "Presión":
                presion_encontrada = functions.presion_llantas(llantas, True)
                presion_actual = functions.presion_llantas(llantas, True)
                context["pay_boton"] = "presion"
                context["parametro_actual_existente"] = presion_actual.exists()
                context["parametro_encontrado_existente"] = presion_encontrada.exists()
                context["parametro_actual"] = presion_actual
                context["parametro_encontrado"] = presion_encontrada
            else:
                desgaste_irregular_encontrado = functions.desgaste_irregular(llantas, True)
                desgaste_irregular_actual = functions.desgaste_irregular(llantas, True)
                context["pay_boton"] = "desgaste"
                context["parametro_actual_existente"] = bool(desgaste_irregular_actual)
                context["parametro_encontrado_existente"] = bool(desgaste_irregular_encontrado)
                context["parametro_actual"] = desgaste_irregular_actual
                context["parametro_encontrado"] = desgaste_irregular_encontrado


            mes_1 = hoy.strftime("%b")
            mes_2 = functions.mes_anterior(hoy)
            mes_3 = functions.mes_anterior(mes_2)
            mes_4 = functions.mes_anterior(mes_3)

            hoy1 = hoy.strftime("%m")
            hoy2 = mes_2.strftime("%m")
            hoy3 = mes_3.strftime("%m")
            hoy4 = mes_4.strftime("%m")

            vehiculos_vistos_mes_1 = vehiculo.filter(ultima_inspeccion__fecha_hora__month=hoy1)
            vehiculos_vistos_mes_2 = vehiculo.filter(ultima_inspeccion__fecha_hora__month=hoy2)
            vehiculos_vistos_mes_3 = vehiculo.filter(ultima_inspeccion__fecha_hora__month=hoy3)
            vehiculos_vistos_mes_4 = vehiculo.filter(ultima_inspeccion__fecha_hora__month=hoy4)

            vehiculos_rojos_copia = vehiculo.filter(id__in=filtro_rojo)
            vehiculos_rojos_mes_1 = vehiculos_rojos_copia.filter(ultima_inspeccion__fecha_hora__month=hoy1)
            vehiculos_rojos_mes_2 = vehiculos_rojos_copia.filter(ultima_inspeccion__fecha_hora__month=hoy2).exclude(pk__in=vehiculos_rojos_mes_1)
            vehiculos_rojos_mes_3 = vehiculos_rojos_copia.filter(ultima_inspeccion__fecha_hora__month=hoy3).exclude(pk__in=vehiculos_rojos_mes_2)
            vehiculos_rojos_mes_4 = vehiculos_rojos_copia.filter(ultima_inspeccion__fecha_hora__month=hoy4).exclude(pk__in=vehiculos_rojos_mes_3)


            vehiculos_amarillos_mes_1 = vehiculos_amarillos.filter(ultima_inspeccion__fecha_hora__month=hoy1)
            vehiculos_amarillos_mes_2 = vehiculos_amarillos.filter(ultima_inspeccion__fecha_hora__month=hoy2)
            vehiculos_amarillos_mes_3 = vehiculos_amarillos.filter(ultima_inspeccion__fecha_hora__month=hoy3)
            vehiculos_amarillos_mes_4 = vehiculos_amarillos.filter(ultima_inspeccion__fecha_hora__month=hoy4)

            vehiculos_sospechosos_mes_1 = vehiculos_sospechosos.filter(ultima_inspeccion__fecha_hora__month=hoy1)
            vehiculos_sospechosos_mes_2 = vehiculos_sospechosos.filter(ultima_inspeccion__fecha_hora__month=hoy2)
            vehiculos_sospechosos_mes_3 = vehiculos_sospechosos.filter(ultima_inspeccion__fecha_hora__month=hoy3)
            vehiculos_sospechosos_mes_4 = vehiculos_sospechosos.filter(ultima_inspeccion__fecha_hora__month=hoy4)

            estatus_profundidad = functions.estatus_profundidad(llantas)

            nunca_vistos = functions.nunca_vistos(vehiculo)
            renovables = functions.renovables(llantas, vehiculos_amarillos)
            sin_informacion = functions.sin_informacion(llantas)

            porcentaje_vehiculos_inspeccionados_por_aplicacion = functions.vehiculos_inspeccionados_por_aplicacion(vehiculo)
            porcentaje_vehiculos_inspeccionados_por_clase = functions.vehiculos_inspeccionados_por_clase(vehiculo)

            vehiculos_por_clase_sin_inspeccionar = functions.vehiculos_por_clase_sin_inspeccionar(vehiculo, hoy1, hoy2, hoy3)
            clase_sin_inspeccionar_mes_1 = {}
            clase_sin_inspeccionar_mes_2 = {}
            clase_sin_inspeccionar_mes_3 = {}
            for cls in vehiculos_por_clase_sin_inspeccionar:
                clase_sin_inspeccionar_mes_1[cls["clase"]] = cls["mes1"]
                clase_sin_inspeccionar_mes_2[cls["clase"]] = cls["mes2"]
                clase_sin_inspeccionar_mes_3[cls["clase"]] = cls["mes3"]
            vehiculos_por_aplicacion_sin_inspeccionar = functions.vehiculos_por_aplicacion_sin_inspeccionar(vehiculo, hoy1, hoy2, hoy3)
            aplicacion_sin_inspeccionar_mes_1 = {}
            aplicacion_sin_inspeccionar_mes_2 = {}
            aplicacion_sin_inspeccionar_mes_3 = {}
            for cls in vehiculos_por_aplicacion_sin_inspeccionar:
                aplicacion_sin_inspeccionar_mes_1[cls["aplicacion__nombre"]] = cls["mes1"]
                aplicacion_sin_inspeccionar_mes_2[cls["aplicacion__nombre"]] = cls["mes2"]
                aplicacion_sin_inspeccionar_mes_3[cls["aplicacion__nombre"]] = cls["mes3"]

            print(vehiculos_por_aplicacion_sin_inspeccionar)
            print(aplicacion_sin_inspeccionar_mes_1)
            context["aplicacion_sin_inspeccionar_mes_1"] = aplicacion_sin_inspeccionar_mes_1
            context["aplicacion_sin_inspeccionar_mes_2"] = aplicacion_sin_inspeccionar_mes_1
            context["aplicacion_sin_inspeccionar_mes_3"] = aplicacion_sin_inspeccionar_mes_1
            context["clase_sin_inspeccionar_mes_1"] = clase_sin_inspeccionar_mes_1
            context["clase_sin_inspeccionar_mes_2"] = clase_sin_inspeccionar_mes_2
            context["clase_sin_inspeccionar_mes_3"] = clase_sin_inspeccionar_mes_3
            context["clases_mas_frecuentes_infladas"] = functions.clases_mas_frecuentes(vehiculo, self.request.user.perfil.compania)
            context["estatus_profundidad"] = estatus_profundidad
            context["flotas"] = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            context["mes_1"] = mes_1
            context["mes_2"] = mes_2.strftime("%b")
            context["mes_3"] = mes_3.strftime("%b")
            context["mes_4"] = mes_4.strftime("%b")
            context["nunca_vistos"] = nunca_vistos
            context["porcentaje_amarillo"] = porcentaje_amarillo
            context["porcentaje_vehiculos_inspeccionados_por_aplicacion"] = porcentaje_vehiculos_inspeccionados_por_aplicacion
            context["porcentaje_vehiculos_inspeccionados_por_clase"] = porcentaje_vehiculos_inspeccionados_por_clase
            context["porcentaje_rojo"] = porcentaje_rojo
            context["porcentaje_sospechoso"] = porcentaje_sospechoso
            context["porcentaje_visto"] = porcentaje_visto
            context["renovables"] = renovables
            context["sin_informacion"] = sin_informacion
            context["vehiculos_amarillos"] = vehiculos_amarillos.count()
            context["vehiculos_amarillos_mes_1"] = vehiculos_amarillos_mes_1.count()
            context["vehiculos_amarillos_mes_2"] = vehiculos_amarillos_mes_2.count()
            context["vehiculos_amarillos_mes_3"] = vehiculos_amarillos_mes_3.count()
            context["vehiculos_amarillos_mes_4"] = vehiculos_amarillos_mes_4.count()
            context["vehiculos_por_clase_sin_inspeccionar"] = vehiculos_por_clase_sin_inspeccionar
            context["vehiculos_rojos"] = vehiculos_rojos.count()
            context["vehiculos_rojos_mes_1"] = vehiculos_rojos_mes_1.count()
            context["vehiculos_rojos_mes_2"] = vehiculos_rojos_mes_2.count()
            context["vehiculos_rojos_mes_3"] = vehiculos_rojos_mes_3.count()
            context["vehiculos_rojos_mes_4"] = vehiculos_rojos_mes_4.count()
            context["vehiculos_sospechosos"] = vehiculos_sospechosos.count()
            context["vehiculos_sospechosos_mes_1"] = vehiculos_sospechosos_mes_1.count()
            context["vehiculos_sospechosos_mes_2"] = vehiculos_sospechosos_mes_2.count()
            context["vehiculos_sospechosos_mes_3"] = vehiculos_sospechosos_mes_3.count()
            context["vehiculos_sospechosos_mes_4"] = vehiculos_sospechosos_mes_4.count()
            context["vehiculos_vistos"] = vehiculos_vistos.count()
            context["vehiculos_vistos_mes_1"] = vehiculos_vistos_mes_1.count()
            context["vehiculos_vistos_mes_2"] = vehiculos_vistos_mes_2.count()
            context["vehiculos_vistos_mes_3"] = vehiculos_vistos_mes_3.count()
            context["vehiculos_vistos_mes_4"] = vehiculos_vistos_mes_4.count()
            context["vehiculos_totales"] = vehiculo.count()
            return context



class TireDB2View(LoginRequiredMixin, TemplateView):
    # Vista de tire-dashboard2

    template_name = "tire-dashboard2.html"
    def get_context_data(self, **kwargs):

        clase = self.request.GET.get("clase")
        flota = self.request.GET.get("flota")
        
        if clase:
            context = super().get_context_data(**kwargs)
            vehiculo_clase = Vehiculo.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania), clase=clase.upper())
            llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), vehiculo__in=vehiculo_clase)
            inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            ubicacion = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))[0]


            reemplazo_actual = functions.reemplazo_actual(llantas)
            # Te elimina los ejes vacíos
            reemplazo_actual_llantas = reemplazo_actual[0]
            reemplazo_actual_ejes = {k: v for k, v in reemplazo_actual[1].items() if v != 0}

            reemplazo_dual = functions.reemplazo_dual(llantas, reemplazo_actual_llantas)
            reemplazo_total = functions.reemplazo_total(reemplazo_actual_ejes, reemplazo_dual)

            # Sin regresión
            embudo_vida1 = functions.embudo_vidas(llantas)
            pronostico_de_consumo = {k: v for k, v in embudo_vida1[1].items() if v != 0}
            presupuesto = functions.presupuesto(pronostico_de_consumo, ubicacion)

            # Con regresión
            #embudo_vida2 = functions.embudo_vidas_con_regresion(llantas)

            context["aplicaciones"] = Aplicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            context["clases_mas_frecuentes_infladas"] = functions.clases_mas_frecuentes(vehiculo_clase, self.request.user.perfil.compania)
            context["embudo"] = embudo_vida1[1]
            context["flotas"] = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            context["presupuesto"] = presupuesto
            context["pronostico_de_consumo"] = pronostico_de_consumo
            context["pronostico_de_consumo_contar"] = len(embudo_vida1[1]) + 1
            context["reemplazo_actual_ejes"] = reemplazo_actual_ejes
            context["reemplazo_dual"] = reemplazo_dual
            context["reemplazo_total"] = reemplazo_total

            return context

        elif flota:
            context = super().get_context_data(**kwargs)
            vehiculo_flota = Vehiculo.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania), ubicacion__nombre=flota)
            llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), vehiculo__in=vehiculo_flota)
            inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            ubicacion = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))[0]


            reemplazo_actual = functions.reemplazo_actual(llantas)
            # Te elimina los ejes vacíos
            reemplazo_actual_llantas = reemplazo_actual[0]
            reemplazo_actual_ejes = {k: v for k, v in reemplazo_actual[1].items() if v != 0}

            reemplazo_dual = functions.reemplazo_dual(llantas, reemplazo_actual_llantas)
            reemplazo_total = functions.reemplazo_total(reemplazo_actual_ejes, reemplazo_dual)

            # Sin regresión
            embudo_vida1 = functions.embudo_vidas(llantas)
            pronostico_de_consumo = {k: v for k, v in embudo_vida1[1].items() if v != 0}
            presupuesto = functions.presupuesto(pronostico_de_consumo, ubicacion)

            # Con regresión
            #embudo_vida2 = functions.embudo_vidas_con_regresion(llantas)

            context["p1"] = 50500
            context["p2"] = 11700
            context["p3"] = 20000
            
            context["p4"] = 24
            context["p5"] = 31
            context["p6"] = 40

            context["p7"] = 4
            context["p8"] = 10
            context["p9"] = 18
            context["p10"] = 25


            context["aplicaciones"] = Aplicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            context["clases_mas_frecuentes_infladas"] = functions.clases_mas_frecuentes(vehiculo_flota, self.request.user.perfil.compania)
            context["embudo"] = embudo_vida1[1]
            context["flotas"] = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            context["presupuesto"] = presupuesto
            context["pronostico_de_consumo"] = pronostico_de_consumo
            context["pronostico_de_consumo_contar"] = len(embudo_vida1[1]) + 1
            context["reemplazo_actual_ejes"] = reemplazo_actual_ejes
            context["reemplazo_dual"] = reemplazo_dual
            context["reemplazo_total"] = reemplazo_total

            return context
        
        else:
            context = super().get_context_data(**kwargs)
            vehiculo = Vehiculo.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            ubicacion = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))[0]

            reemplazo_actual = functions.reemplazo_actual(llantas)
            # Te elimina los ejes vacíos
            reemplazo_actual_llantas = reemplazo_actual[0]
            reemplazo_actual_ejes = {k: v for k, v in reemplazo_actual[1].items() if v != 0}

            reemplazo_dual = functions.reemplazo_dual(llantas, reemplazo_actual_llantas)
            reemplazo_total = functions.reemplazo_total(reemplazo_actual_ejes, reemplazo_dual)

            # Sin regresión
            embudo_vida1 = functions.embudo_vidas(llantas)
            pronostico_de_consumo = {k: v for k, v in embudo_vida1[1].items() if v != 0}
            presupuesto = functions.presupuesto(pronostico_de_consumo, ubicacion)

            # Con regresión
            embudo_vida2 = functions.embudo_vidas_con_regresion(inspecciones)

            context["p1"] = 50500
            context["p2"] = 11700
            context["p3"] = 20000
            
            context["p4"] = 24
            context["p5"] = 31
            context["p6"] = 40

            context["p7"] = 4
            context["p8"] = 10
            context["p9"] = 18
            context["p10"] = 25

            context["aplicaciones"] = Aplicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            context["clases_mas_frecuentes_infladas"] = functions.clases_mas_frecuentes(vehiculo, self.request.user.perfil.compania)
            context["embudo"] = embudo_vida1[1]
            context["flotas"] = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
            context["presupuesto"] = presupuesto
            context["pronostico_de_consumo"] = pronostico_de_consumo
            context["pronostico_de_consumo_contar"] = len(embudo_vida1[1]) + 1
            context["reemplazo_actual_ejes"] = reemplazo_actual_ejes
            context["reemplazo_dual"] = reemplazo_dual
            context["reemplazo_total"] = reemplazo_total

            return context

class TireDB3View(LoginRequiredMixin, TemplateView):
    # Vista de tire-dashboard3

    template_name = "tire-dashboard3.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehiculos = Vehiculo.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        
        inspecciones = Inspeccion.objects.filter(llanta__in=llantas)
        productos = Producto.objects.all()
        flotas = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        aplicaciones = Aplicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        ejes = ["Dirección", "Tracción", "Arrastre", "Loco", "Retractil"]

        hoy = date.today()
        mes_1 = hoy.strftime("%b")
        mes_2 = functions.mes_anterior(hoy)
        mes_3 = functions.mes_anterior(mes_2)
        mes_4 = functions.mes_anterior(mes_3)
        mes_5 = functions.mes_anterior(mes_4)
        mes_6 = functions.mes_anterior(mes_5)
        mes_7 = functions.mes_anterior(mes_6)
        mes_8 = functions.mes_anterior(mes_7)


        regresion_flota = functions.km_proyectado(inspecciones, True)
        km_proyectado = regresion_flota[0]
        km_x_mm = regresion_flota[1]
        cpk = regresion_flota[2]
        llantas_limpias = regresion_flota[4]
        porcentaje_limpio = (len(llantas_limpias)/llantas.count())*100

        llantas_limpias_nueva = []
        llantas_limpias_1r = []
        llantas_limpias_2r = []
        llantas_limpias_3r = []
        llantas_limpias_4r = []

        for llanta in llantas_limpias:
            if llanta.vida == "Nueva":
                llantas_limpias_nueva.append(llanta)
            elif llanta.vida == "1R":
                llantas_limpias_1r.append(llanta)
            elif llanta.vida == "2R":
                llantas_limpias_2r.append(llanta)
            elif llanta.vida == "3R":
                llantas_limpias_3r.append(llanta)
            elif llanta.vida == "4R":
                llantas_limpias_4r.append(llanta)

        comparativa_de_productos = {}
        cpk_productos = {}
        km_productos = {}
        for producto in productos:
            valores_producto = []
            
            llantas_producto = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), producto=producto, numero_economico__in=llantas_limpias)
            desgaste = functions.desgaste_irregular_producto(llantas_producto)

            inspecciones_producto = Inspeccion.objects.filter(llanta__in=llantas_producto)
            regresion_producto = functions.km_proyectado(inspecciones_producto, False)
            km_proyectado_producto = regresion_producto[0]
            km_x_mm_producto = regresion_producto[1]
            cpk_producto = regresion_producto[2]
            cantidad = llantas_producto.count()

            valores_producto.append(km_proyectado_producto)
            valores_producto.append(km_x_mm_producto)
            valores_producto.append(cpk_producto)
            km_productos[producto] = regresion_producto[0]
            cpk_productos[producto] = regresion_producto[3]
            valores_producto.append(cantidad)
            valores_producto.append(desgaste)
            
            comparativa_de_productos[producto] = valores_producto

        comparativa_de_flotas = {}
        cpk_flotas = {}
        km_flotas = {}
        for flota in flotas:
            valores_flota = []
            
            llantas_flota = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), vehiculo__ubicacion=flota, numero_economico__in=llantas_limpias)
            inspecciones_flota = Inspeccion.objects.filter(llanta__in=llantas_flota)
            regresion_flota = functions.km_proyectado(inspecciones_flota, False)
            km_proyectado_flota = regresion_flota[0]
            km_x_mm_flota = regresion_flota[1]
            cpk_flota = regresion_flota[2]
            cantidad = llantas_flota.count()

            valores_flota.append(km_proyectado_flota)
            valores_flota.append(km_x_mm_flota)
            valores_flota.append(cpk_flota)
            km_flotas[flota] = regresion_flota[0]
            cpk_flotas[flota] = regresion_flota[3]
            valores_flota.append(cantidad)
            
            comparativa_de_flotas[flota] = valores_flota

        comparativa_de_vehiculos = {}
        cpk_vehiculos = []
        for vehiculo in vehiculos:
            valores_vehiculo = []
            
            llantas_vehiculo = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), vehiculo=vehiculo, numero_economico__in=llantas_limpias)
            inspecciones_vehiculo = Inspeccion.objects.filter(llanta__in=llantas_vehiculo)
            regresion_vehiculo = functions.km_proyectado(inspecciones_vehiculo, False)
            km_proyectado_vehiculo = regresion_vehiculo[0]
            km_x_mm_vehiculo = regresion_vehiculo[1]
            cpk_vehiculo = regresion_vehiculo[2]
            cantidad = llantas_vehiculo.count()

            valores_vehiculo.append(km_proyectado_vehiculo)
            valores_vehiculo.append(km_x_mm_vehiculo)
            valores_vehiculo.append(cpk_vehiculo)
            cpk_vehiculos.append(cpk_vehiculo)
            valores_vehiculo.append(cantidad)
            
            comparativa_de_vehiculos[vehiculo.numero_economico] = valores_vehiculo

        comparativa_de_aplicaciones = {}
        cpk_aplicaciones = {}
        km_aplicaciones = {}
        for aplicacion in aplicaciones:
            valores_aplicacion = []

            llantas_aplicacion = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), vehiculo__aplicacion =aplicacion, numero_economico__in=llantas_limpias)
            inspecciones_aplicacion = Inspeccion.objects.filter(llanta__in=llantas_aplicacion)
            regresion_aplicacion = functions.km_proyectado(inspecciones_aplicacion, False)
            km_proyectado_aplicacion = regresion_aplicacion[0]
            km_x_mm_aplicacion = regresion_aplicacion[1]
            cpk_aplicacion = regresion_aplicacion[2]
            cantidad = llantas_aplicacion.count()

            valores_aplicacion.append(km_proyectado_aplicacion)
            valores_aplicacion.append(km_x_mm_aplicacion)
            valores_aplicacion.append(cpk_aplicacion)
            km_aplicaciones[aplicacion] = regresion_aplicacion[0]
            cpk_aplicaciones[aplicacion] = regresion_aplicacion[3]
            valores_aplicacion.append(cantidad)
            
            comparativa_de_aplicaciones[aplicacion] = valores_aplicacion

        comparativa_de_ejes = {}
        for eje in ejes:
            valores_eje = []

            llantas_eje = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), nombre_de_eje=eje, numero_economico__in=llantas_limpias)
            inspecciones_eje = Inspeccion.objects.filter(llanta__in=llantas_eje)
            if inspecciones_eje.exists():
                regresion_eje = functions.km_proyectado(inspecciones_eje, False)
                km_proyectado_eje = regresion_eje[0]
                km_x_mm_eje = regresion_eje[1]
                cpk_eje = regresion_eje[2]
                cantidad = llantas_eje.count()

                valores_eje.append(km_proyectado_eje)
                valores_eje.append(km_x_mm_eje)
                valores_eje.append(cpk_eje)
                valores_eje.append(cantidad)
                
                comparativa_de_ejes[eje] = valores_eje

        cpk_vehiculos =  functions.cpk_vehiculo_cantidad(cpk_vehiculos)
        cpk_flotas =  functions.distribucion_cantidad(cpk_flotas)
        cpk_aplicaciones =  functions.distribucion_cantidad(cpk_aplicaciones)
        cpk_productos =  functions.distribucion_cantidad(cpk_productos)

        km_flotas =  functions.distribucion_cantidad(km_flotas)
        km_aplicaciones = functions.distribucion_cantidad(km_aplicaciones)
        km_productos = functions.distribucion_cantidad(km_productos)

        context["comparativa_de_aplicaciones"] = comparativa_de_aplicaciones
        context["comparativa_de_ejes"] = comparativa_de_ejes
        context["comparativa_de_flotas"] = comparativa_de_flotas
        context["comparativa_de_productos"] = comparativa_de_productos
        context["comparativa_de_vehiculos"] = comparativa_de_vehiculos
        context["cpk"] = cpk
        context["cpk_aplicaciones"] = cpk_aplicaciones
        context["cpk_flotas"] = cpk_flotas
        context["cpk_productos"] = cpk_productos
        context["cpk_vehiculos"] = cpk_vehiculos[0]
        context["cpk_vehiculos_cantidad"] = cpk_vehiculos[1]
        context["cpk_vehiculos_cantidad_maxima"] = max(cpk_vehiculos[1])
        context["km_proyectado"] = km_proyectado
        context["km_x_mm"] = km_x_mm
        context["llantas_analizadas"] = llantas.count()
        context["llantas_limpias"] = len(llantas_limpias)
        context["llantas_limpias_nueva"] = len(llantas_limpias_nueva)
        context["llantas_limpias_1r"] = len(llantas_limpias_1r)
        context["llantas_limpias_2r"] = len(llantas_limpias_2r)
        context["llantas_limpias_3r"] = len(llantas_limpias_3r)
        context["llantas_limpias_4r"] = len(llantas_limpias_4r)
        context["mes_1"] = mes_1
        context["mes_2"] = mes_2.strftime("%b")
        context["mes_3"] = mes_3.strftime("%b")
        context["mes_4"] = mes_4.strftime("%b")
        context["mes_5"] = mes_5.strftime("%b")
        context["mes_6"] = mes_6.strftime("%b")
        context["mes_7"] = mes_7.strftime("%b")
        context["mes_8"] = mes_8.strftime("%b")
        context["porcentaje_limpio"] = porcentaje_limpio
        return context



class hubView(LoginRequiredMixin, TemplateView):
    # Vista de hubView

    template_name = "hub.html"

class diagramaView(LoginRequiredMixin, TemplateView):
    # Vista de diagramaView

    template_name = "diagrama.html"

class tireDiagramaView(LoginRequiredMixin, TemplateView):
    # Vista de tireDiagramaView

    template_name = "tireDiagrama.html"

class ParametroExtractoView(LoginRequiredMixin, TemplateView):
    # Vista de ParametrosExtractoView

    template_name = "parametrosExtracto.html"

class SiteMenuView(LoginRequiredMixin, TemplateView):
    # Vista de SiteMenuView

    template_name = "siteMenu.html"

class catalogoDesechosView(LoginRequiredMixin, TemplateView):
    # Vista de catalogoDesechosView

    template_name = "catalogoDesechos.html"

class catalogoProductoView(LoginRequiredMixin, TemplateView):
    # Vista de catalogoProductosView

    template_name = "catalogoProducto.html"

class catalogoRenovadoresView(LoginRequiredMixin, TemplateView):
    # Vista de catalogoRenovadoresView

    template_name = "catalogoRenovadores.html"

class CuatroUmbralesView(LoginRequiredMixin, TemplateView):
    # Vista de CatalogoDesechosView

    template_name = "cuatroUmbrales.html"

class SerialVehiculoView(LoginRequiredMixin, TemplateView):
    # Vista de CatalogoDesechosView

    template_name = "serialVehiculo.html"

class TireEyeView(LoginRequiredMixin, TemplateView):
    # Vista de TireEyeViewView

    template_name = "tireEyeView.html"

class reporteVehiculoView(LoginRequiredMixin, DetailView):
    # Vista de reporteVehiculoView

    template_name = "reporteVehiculo.html"   
    slug_field = "bitacora"
    slug_url_kwarg = "bitacora"
    queryset = Bitacora.objects.all()
    context_object_name = "bitacora"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        bitacora = self.get_object()
        hoy = date.today()
        user = User.objects.get(username=self.request.user)

        color1 = functions.entrada_correcta(bitacora)
        color2 = functions.salida_correcta(bitacora)
        
        if color1 == "good":
            signo1 = "icon-checkmark"
        else:
            signo1 = "icon-cross"
        if color2 == "good":
            signo2 = "icon-checkmark"
        else:
            signo2 = "icon-cross"

        context["color1"] = color1
        context["color2"] = color2
        context["hoy"] = hoy
        context["user"] = user
        context["signo1"] = signo1
        context["signo2"] = signo2
        return context

class reporteLlantaView(LoginRequiredMixin, TemplateView):
    # Vista de reporteLlantaView

    template_name = "reporteLlanta.html" 

class configuracionVehiculoView(LoginRequiredMixin, TemplateView):
    # Vista de configuracionVehiculoView

    template_name = "configuracionVehiculo.html" 

class configuracionLlantaView(LoginRequiredMixin, TemplateView):
    # Vista de configuracionLlantaView

    template_name = "configuracionLlanta.html" 

class almacenView(LoginRequiredMixin, TemplateView, View):
    # Vista de almacenView

    template_name = "almacen.html"

    """def form_valid(self, request):
        print("hola")
        get_llanta = self.request.GET.get("llanta")
        if get_llanta:
            llanta = Llanta.objects.get(numero_economico=get_llanta).id
            print(get_llanta)
            print(llanta)
            return reverse('dashboards:detail', kwargs={"pk": llanta})"""

    def post(self, request):
        print("hola")
        get_llanta = self.request.POST.get("llanta")
        print(get_llanta)
        if get_llanta:
            try:
                llanta = Llanta.objects.get(numero_economico=get_llanta).id
                print(llanta)
                return HttpResponseRedirect(reverse('dashboards:tireDetail', kwargs={"pk": llanta}))
            except:
                return HttpResponseRedirect(reverse_lazy('dashboards:almacen'))


    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        llantas = Llanta.objects.filter(usuario__compania=Compania.objects.get(compania=self.request.user.perfil.compania))

        llantas_nuevas = llantas.filter(inventario="Nueva")
        llantas_antes_de_renovar = llantas.filter(inventario="Antes de Renovar")
        llantas_antes_de_desechar = llantas.filter(inventario="Antes de Desechar")
        llantas_renovadas = llantas.filter(inventario="Renovada")
        llantas_con_renovador = llantas.filter(inventario="Con renovador")
        llantas_desecho_final = llantas.filter(inventario="Desecho final")
        llantas_servicio = llantas.filter(inventario="Servicio")
        llantas_rodante = llantas.filter(inventario="Rodante")

        context["llantas_nuevas"] = llantas_nuevas.count()
        context["llantas_antes_de_renovar"] = llantas_antes_de_renovar.count()
        context["llantas_antes_de_desechar"] = llantas_antes_de_desechar.count()
        context["llantas_renovadas"] = llantas_renovadas.count()
        context["llantas_con_renovador"] = llantas_con_renovador.count()
        context["llantas_desecho_final"] = llantas_desecho_final.count()
        context["llantas_servicio"] = llantas_servicio.count()
        context["llantas_rodantes"] = llantas_rodante.count()
        return context

class antesDesecharView(LoginRequiredMixin, TemplateView):
    # Vista de antesDesecharView

    template_name = "antesDesechar.html"

class antesRenovarView(LoginRequiredMixin, TemplateView):
    # Vista de antesRenovarView

    template_name = "antesRenovar.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        
        llantas_antes_de_renovar = Llanta.objects.filter(usuario__compania=Compania.objects.get(compania=self.request.user.perfil.compania), inventario="Antes de Renovar")

        context["llantas_antes_de_renovar"] = llantas_antes_de_renovar

        return context

class conRenovadorView(LoginRequiredMixin, TemplateView):
    # Vista de conRenovadorView

    template_name = "conRenovador.html"

class desechoFinalView(LoginRequiredMixin, TemplateView):
    # Vista de desechoFinalView

    template_name = "desechoFinal.html"

class nuevaView(LoginRequiredMixin, TemplateView):
    # Vista de nuevaView

    template_name = "nueva.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        llantas_nuevas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), vida="Nueva")

        context["llantas_nuevas"] = llantas_nuevas

        return context

class renovadaView(LoginRequiredMixin, TemplateView):
    # Vista de renovadaView

    template_name = "renovada.html"

class servicioView(LoginRequiredMixin, TemplateView):
    # Vista de servicioView

    template_name = "servicio.html"

class rodanteView(LoginRequiredMixin, TemplateView):
    # Vista de rodanteView

    template_name = "rodante.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        llantas_nuevas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), vida="Nueva")

        context["llantas_nuevas"] = llantas_nuevas

        return context

class procesoDesechoView(LoginRequiredMixin, TemplateView):
    # Vista de procesoDesechoView

    template_name = "procesoDesecho.html"

class ordenSalidaRenView(LoginRequiredMixin, TemplateView):
    # Vista de ordenSalidaRenView

    template_name = "ordenSalidaRen.html"

class ordenEntradaView(LoginRequiredMixin, TemplateView):
    # Vista de ordenEntradaView

    template_name = "ordenEntrada.html"

class ordenLlantaView(LoginRequiredMixin, TemplateView):
    # Vista de ordenLlantaView

    template_name = "ordenLlanta.html"

class tallerDestinoView(LoginRequiredMixin, TemplateView):
# Vista de tallerDestinoView

    template_name = "tallerDestino.html"

class stockDestinoView(LoginRequiredMixin, TemplateView):
# Vista de stockDestinoView

    template_name = "stockDestino.html"


class procesoRenovadoView(LoginRequiredMixin, TemplateView):
# Vista de procesoRenovadoView

    template_name = "procesoRenovado.html"

class calendarView(LoginRequiredMixin, TemplateView):
# Vista de calendarView

    template_name = "calendar/calendar.html"

class planTrabajoView(LoginRequiredMixin, TemplateView):
# Vista de planTrabajoView

    template_name = "planTrabajo.html"

class LogoutView(LoginRequiredMixin, auth_views.LogoutView):
    # Vista de Logout
    pass

class VehiculoAPI(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        jd = json.loads(request.body)
        vehiculo = Vehiculo.objects.get(numero_economico=jd['numero_economico'], compania=Compania.objects.get(compania=jd['compania']))
        vehiculo.fecha_de_inflado=date.today()
        vehiculo.tiempo_de_inflado=jd['tiempo_de_inflado']
        vehiculo.presion_de_entrada=jd['presion_de_entrada']
        vehiculo.presion_de_salida=jd['presion_de_salida']
        vehiculo.save()
        Bitacora.objects.create(numero_economico=vehiculo,
                compania=Compania.objects.get(compania=jd['compania']),
                fecha_de_inflado=date.today(),
                tiempo_de_inflado=jd['tiempo_de_inflado'],
                presion_de_entrada=jd['presion_de_entrada'],
                presion_de_salida=jd['presion_de_salida']
                )
        return JsonResponse(jd)


class PulpoProAPI(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        jd = json.loads(request.body)
        vehiculo = Vehiculo.objects.get(numero_economico=jd['numero_economico'], compania=Compania.objects.get(compania=jd['compania']))
        bi = Bitacora_Pro.objects.create(numero_economico=vehiculo,
                                compania=Compania.objects.get(compania=jd['compania']),
                                fecha_de_inflado=date.today(),
                                tiempo_de_inflado=jd['tiempo_de_inflado'],
        )
        presiones_de_entrada = eval(jd['presiones_de_entrada'])
        presiones_de_salida = eval(jd['presiones_de_salida'])
        numero_de_llantas = vehiculo.numero_de_llantas
        if numero_de_llantas == len(presiones_de_entrada):

            if len(presiones_de_entrada) >= 1:
                bi.presion_de_entrada_1 = presiones_de_entrada[0]
                bi.presion_de_salida_1 = presiones_de_salida[0]
                if len(presiones_de_entrada) >= 2:
                    bi.presion_de_entrada_2 = presiones_de_entrada[1]
                    bi.presion_de_salida_2 = presiones_de_salida[1]
                    if len(presiones_de_entrada) >= 3:
                        bi.presion_de_entrada_3 = presiones_de_entrada[2]
                        bi.presion_de_salida_3 = presiones_de_salida[2]
                        if len(presiones_de_entrada) >= 4:
                            bi.presion_de_entrada_4 = presiones_de_entrada[3]
                            bi.presion_de_salida_4 = presiones_de_salida[3]
                            if len(presiones_de_entrada) >= 5:
                                bi.presion_de_entrada_5 = presiones_de_entrada[4]
                                bi.presion_de_salida_5 = presiones_de_salida[4]
                                if len(presiones_de_entrada) >= 6:
                                    bi.presion_de_entrada_6 = presiones_de_entrada[5]
                                    bi.presion_de_salida_6 = presiones_de_salida[5]
                                    if len(presiones_de_entrada) >= 7:
                                        bi.presion_de_entrada_7 = presiones_de_entrada[6]
                                        bi.presion_de_salida_7 = presiones_de_salida[6]
                                        if len(presiones_de_entrada) >= 8:
                                            bi.presion_de_entrada_8 = presiones_de_entrada[7]
                                            bi.presion_de_salida_8 = presiones_de_salida[7]
                                            if len(presiones_de_entrada) >= 9:
                                                bi.presion_de_entrada_9 = presiones_de_entrada[8]
                                                bi.presion_de_salida_9 = presiones_de_salida[8]
                                                if len(presiones_de_entrada) >= 10:
                                                    bi.presion_de_entrada_10 = presiones_de_entrada[9]
                                                    bi.presion_de_salida_10 = presiones_de_salida[9]
                                                    if len(presiones_de_entrada) >= 11:
                                                        bi.presion_de_entrada_11 = presiones_de_entrada[10]
                                                        bi.presion_de_salida_11 = presiones_de_salida[10]
                                                        if len(presiones_de_entrada) >= 12:
                                                            bi.presion_de_entrada_12 = presiones_de_entrada[11]
                                                            bi.presion_de_salida_12 = presiones_de_salida[11]
            bi.save()
    
            vehiculo.fecha_de_inflado=date.today()
            vehiculo.tiempo_de_inflado=jd['tiempo_de_inflado']
            vehiculo.ultima_bitacora= bi
            vehiculo.save()
            return JsonResponse(jd)

class TireEyeAPI(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        jd = json.loads(request.body)
        llanta = Llanta.objects.get(numero_economico=jd['numero_economico'], compania=Compania.objects.get(compania=jd['compania']))
        Inspeccion.objects.create(llanta=llanta,
                                fecha_hora=date.today(),
                                km=jd['km'],
                                min_profundidad=jd['min_profundidad'],
                                max_profundidad=jd['max_profundidad']
        )
        return JsonResponse(jd)


class PulpoView(LoginRequiredMixin, ListView):
    # Vista del dashboard pulpo
    template_name = "pulpo.html"
    model = Vehiculo
    
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        vehiculo = Vehiculo.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        hoy = date.today()

        #functions_ftp.ftp()
        #functions_ftp.ftp_1()
        #functions_ftp.ftp2(self.request.user.perfil)
        ultimo_mes = hoy - timedelta(days=31)

        mes_1 = hoy.strftime("%b")
        mes_2 = functions.mes_anterior(hoy)
        mes_3 = functions.mes_anterior(mes_2)
        mes_4 = functions.mes_anterior(mes_3)
        mes_5 = functions.mes_anterior(mes_4)

        hoy1 = hoy.strftime("%m")
        hoy2 = mes_2.strftime("%m")
        hoy3 = mes_3.strftime("%m")
        hoy4 = mes_4.strftime("%m")
        hoy5 = mes_5.strftime("%m")


        vehiculo_fecha = vehiculo.filter(fecha_de_inflado__range=[ultimo_mes, hoy])
        vehiculo_fecha_barras_1 = vehiculo.filter(fecha_de_inflado__month=hoy1)
        vehiculo_fecha_barras_2 = vehiculo.filter(fecha_de_inflado__month=hoy2)
        vehiculo_fecha_barras_3 = vehiculo.filter(fecha_de_inflado__month=hoy3)
        vehiculo_fecha_barras_4 = vehiculo.filter(fecha_de_inflado__month=hoy4)
        vehiculo_fecha_barras_5 = vehiculo.filter(fecha_de_inflado__month=hoy5)
        vehiculo_mes1 = bitacora.filter(fecha_de_inflado__month=hoy1)
        vehiculo_mes2 = bitacora.filter(fecha_de_inflado__month=hoy2)
        vehiculo_mes3 = bitacora.filter(fecha_de_inflado__month=hoy3)
        vehiculo_mes4 = bitacora.filter(fecha_de_inflado__month=hoy4)

        entrada_correcta_contar = functions.contar_entrada_correcta(vehiculo_fecha)
        mala_entrada_contar_mes1 = functions.contar_mala_entrada(vehiculo_mes1)
        mala_entrada_contar_mes2 = functions.contar_mala_entrada(vehiculo_mes2)
        mala_entrada_contar_mes3 = functions.contar_mala_entrada(vehiculo_mes3)
        mala_entrada_contar_mes4 = functions.contar_mala_entrada(vehiculo_mes4)


        entrada_correcta_contar_barras_mes1 = functions.contar_entrada_correcta(vehiculo_fecha_barras_1)
        entrada_correcta_contar_barras_mes2 = functions.contar_entrada_correcta(vehiculo_fecha_barras_2)
        entrada_correcta_contar_barras_mes3 = functions.contar_entrada_correcta(vehiculo_fecha_barras_3)
        entrada_correcta_contar_barras_mes4 = functions.contar_entrada_correcta(vehiculo_fecha_barras_4)
        entrada_correcta_contar_barras_mes5 = functions.contar_entrada_correcta(vehiculo_fecha_barras_5)


        doble_entrada = functions.doble_entrada(bitacora)
        doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculo)

        vehiculo_periodo = vehiculo.filter(fecha_de_inflado__lte=ultimo_mes) | vehiculo.filter(fecha_de_inflado=None)
        vehiculo_periodo_status = {}
        mala_entrada_periodo = functions.mala_entrada(vehiculo_periodo)
        for v in vehiculo_periodo:
            if v in doble_mala_entrada:
                vehiculo_periodo_status[v] = "Doble Entrada"
            elif v in mala_entrada_periodo:
                vehiculo_periodo_status[v] = "Mala Entrada"
            else:
                vehiculo_periodo_status[v] = "Entrada Correctas"

        vehiculo_malos_status = {}
        bitacora_mala = bitacora.filter(numero_economico__in=vehiculo)
        mala_entrada = functions.mala_entrada(vehiculo)
        for v in vehiculo:
            if v in doble_mala_entrada:
                vehiculo_malos_status[v] = "Doble Entrada"
            elif v in mala_entrada:
                vehiculo_malos_status[v] = "Mala Entrada"





        my_profile = Perfil.objects.get(user=self.request.user)

        radar_min = functions.radar_min(vehiculo_fecha, self.request.user.perfil.compania)
        radar_max = functions.radar_max(vehiculo_fecha, self.request.user.perfil.compania)
        radar_min_resta = functions.radar_min_resta(radar_min, radar_max)

        """functions.crear_1(numero_economico="P5",
        compania="pruebacal",
        ubicacion="DOS",
        aplicacion="FORANEO",
        clase="CAMIONETA",
        configuracion="S2.D2", 
        tiempo_de_inflado=2.5,
        presion_de_entrada=100,
        presion_de_salida=100,
        presion_establecida=100)"""

        #functions.crear_3(Vehiculo.objects.get(numero_economico="P5"))

        context["aplicaciones"] = Aplicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        context["aplicaciones_mas_frecuentes_infladas"] = functions.aplicaciones_mas_frecuentes(vehiculo_fecha, vehiculo, self.request.user.perfil.compania)
        context["bitacoras"] = bitacora
        context["boton_intuitivo"] = "Vehículos Vencidos"
        context["doble_entrada"] = doble_entrada
        context["cantidad_inflado"] = vehiculo_fecha.count()
        context["cantidad_inflado_1"] = vehiculo_fecha_barras_1.count()
        context["cantidad_inflado_2"] = vehiculo_fecha_barras_2.count()
        context["cantidad_inflado_3"] = vehiculo_fecha_barras_3.count()
        context["cantidad_inflado_4"] = vehiculo_fecha_barras_4.count()
        context["cantidad_inflado_5"] = vehiculo_fecha_barras_5.count()
        context["cantidad_entrada"] = entrada_correcta_contar
        context["cantidad_entrada_barras_mes1"] = entrada_correcta_contar_barras_mes1
        context["cantidad_entrada_barras_mes2"] = entrada_correcta_contar_barras_mes2
        context["cantidad_entrada_barras_mes3"] = entrada_correcta_contar_barras_mes3
        context["cantidad_entrada_barras_mes4"] = entrada_correcta_contar_barras_mes4
        context["cantidad_entrada_barras_mes5"] = entrada_correcta_contar_barras_mes5
        context["cantidad_entrada_mes1"] = mala_entrada_contar_mes1
        context["cantidad_entrada_mes2"] = mala_entrada_contar_mes2
        context["cantidad_entrada_mes3"] = mala_entrada_contar_mes3
        context["cantidad_entrada_mes4"] = mala_entrada_contar_mes4
        context["cantidad_total"] = vehiculo.count()
        context["clases_compania"] = functions.clases_mas_frecuentes(vehiculo, self.request.user.perfil.compania)
        context["clases_mas_frecuentes_infladas"] = functions.clases_mas_frecuentes(vehiculo_fecha, self.request.user.perfil.compania)
        context["compania"] = self.request.user.perfil.compania
        context["flotas"] = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        context["hoy"] = hoy
        context["mes_1"] = mes_1
        context["mes_2"] = mes_2.strftime("%b")
        context["mes_3"] = mes_3.strftime("%b")
        context["mes_4"] = mes_4.strftime("%b")
        context["mes_5"] = mes_5.strftime("%b")
        context["porcentaje_inflado"] = functions.porcentaje(vehiculo_fecha.count(), vehiculo.count())
        context["porcentaje_entrada_correcta"] = functions.porcentaje(entrada_correcta_contar, vehiculo_fecha.count())
        context["radar_min"] = radar_min_resta
        context["radar_max"] = radar_max
        context["rango_1"] = my_profile.compania.periodo1_inflado
        context["rango_2"] = my_profile.compania.periodo2_inflado
        context["rango_3"] = my_profile.compania.periodo1_inflado + 1
        context["rango_4"] = my_profile.compania.periodo2_inflado + 1
        context["tiempo_promedio"] = functions.inflado_promedio(vehiculo_fecha)
        context["vehiculos"] = vehiculo_fecha
        print(vehiculo_malos_status)
        print(vehiculo_periodo_status)
        print(vehiculo)
        context["vehiculos_malos"] = vehiculo_malos_status
        context["vehiculos_periodo"] = vehiculo_periodo_status
        context["vehiculos_todos"] = vehiculo

        return context


def buscar(request):
    # Busca por fecha, localidad o clase
    
    my_profile = Perfil.objects.get(user=request.user)
    vehiculo = Vehiculo.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
    bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
    hoy = date.today()
    ultimo_mes = hoy - timedelta(days=31)
    clase = request.GET.get("clase")
    fecha = request.GET.get("fecha1")
    flota = request.GET.get("flota")
    boton_intuitivo = request.GET.get("boton_intuitivo")
    if fecha == "Seleccionar Fecha":
        fecha = False
    

    # Buscar por fecha
    if fecha:
        
        # Definir si se toma en cuenta el mes, la semana o el día
        
        
        dividir_fecha = functions.convertir_rango(fecha)
        primera_fecha = datetime.strptime(dividir_fecha[0], "%m/%d/%Y").date()
        segunda_fecha = datetime.strptime(dividir_fecha[1], "%m/%d/%Y").date()
        vehiculo_fecha = vehiculo.filter(fecha_de_inflado__range=[primera_fecha, segunda_fecha])
    
        vehiculo_fecha_barras = vehiculo.filter(fecha_de_inflado__month=hoy.month)
        vehiculo_fecha_barras_2 = vehiculo.filter(fecha_de_inflado__month=hoy.month - 1)
        
        doble_entrada = functions.doble_entrada(bitacora)
        doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculo)

        # Vehículos del periodo 2 y 3
        ultimo_mes = hoy - timedelta(days=31)
        vehiculo_periodo = vehiculo.filter(fecha_de_inflado__lte=ultimo_mes) | vehiculo.filter(fecha_de_inflado=None)

        # Status de los vehículos
        
        bitacora_periodo = bitacora.filter(numero_economico__in=vehiculo_periodo)
        vehiculo_periodo_status = {}
        mala_entrada = functions.mala_entrada(vehiculo_periodo)
        for v in vehiculo_periodo:
            if v in doble_mala_entrada:
                vehiculo_periodo_status[v] = "Doble Entrada"
            elif v in mala_entrada:
                vehiculo_periodo_status[v] = "Mala Entrada"
            else:
                vehiculo_periodo_status[v] = True

        # Convertir formato de fecha
        fecha_con_formato = functions.convertir_fecha(fecha)

        # Saber el tiempo de inflado promedio
        tiempo_promedio = functions.inflado_promedio(vehiculo_fecha)


        # Sacar el porcentaje de los vehículos inflados que hay dentro de los vehículos
        porcentaje_inflado = functions.porcentaje(vehiculo_fecha.count(), vehiculo.count())

        # Sacar cuántos vehículos tienen la entrada correcta
        entrada_correcta_contar = functions.contar_entrada_correcta(vehiculo_fecha)
        
        mes_1 = hoy.strftime("%b")
        mes_2 = functions.mes_anterior(hoy)
        mes_3 = functions.mes_anterior(mes_2)
        mes_4 = functions.mes_anterior(mes_3)

        vehiculo_mes1 = bitacora.filter(fecha_de_inflado__month=hoy.month)
        vehiculo_mes2 = bitacora.filter(fecha_de_inflado__month=hoy.month - 1)
        vehiculo_mes3 = bitacora.filter(fecha_de_inflado__month=hoy.month - 2)
        vehiculo_mes4 = bitacora.filter(fecha_de_inflado__month=hoy.month - 3)
        
        entrada_correcta_contar_mes1 = functions.contar_entrada_correcta(vehiculo_mes1)
        entrada_correcta_contar_mes2 = functions.contar_entrada_correcta(vehiculo_mes2)
        entrada_correcta_contar_mes3 = functions.contar_entrada_correcta(vehiculo_mes3)
        entrada_correcta_contar_mes4 = functions.contar_entrada_correcta(vehiculo_mes4)

        entrada_correcta_contar_barras_mes1 = functions.contar_entrada_correcta(vehiculo_fecha_barras)
        entrada_correcta_contar_barras_mes2 = functions.contar_entrada_correcta(vehiculo_fecha_barras_2)


        # Sacar el porcentaje de los vehículos con entrada correcta que hay dentro de los vehículos seleccionados
        porcentaje_entrada_correcta = functions.porcentaje(entrada_correcta_contar, vehiculo_fecha.count())

        # Calcular la proporción del radar 
        radar_min = functions.radar_min(vehiculo_fecha, request.user.perfil.compania)
        radar_max = functions.radar_max(vehiculo_fecha, request.user.perfil.compania)
        radar_min_resta = functions.radar_min_resta(radar_min, radar_max)

        return render(request, "pulpo.html", {
                                            "aplicaciones_mas_frecuentes_infladas": functions.aplicaciones_mas_frecuentes(vehiculo_fecha, vehiculo, request.user.perfil.compania),
                                            "bitacoras": bitacora,
                                            "boton_intuitivo": "Vehículos Vencidos",
                                            "doble_entrada": doble_entrada,
                                            "cantidad_entrada": entrada_correcta_contar,
                                            "cantidad_entrada_barras_mes1": entrada_correcta_contar_barras_mes1,
                                            "cantidad_entrada_barras_mes2": entrada_correcta_contar_barras_mes2,
                                            "cantidad_entrada_mes1": entrada_correcta_contar_mes1,
                                            "cantidad_entrada_mes2": entrada_correcta_contar_mes2,
                                            "cantidad_entrada_mes3": entrada_correcta_contar_mes3,
                                            "cantidad_entrada_mes4": entrada_correcta_contar_mes4,
                                            "cantidad_inflado": vehiculo_fecha.count(),
                                            "cantidad_inflado_1": vehiculo_fecha_barras.count(),
                                            "cantidad_inflado_2": vehiculo_fecha_barras_2.count(),
                                            "cantidad_total": vehiculo.count(),
                                            "clases_compania": functions.clases_mas_frecuentes(vehiculo, request.user.perfil.compania),
                                            "clases_mas_frecuentes_infladas": functions.clases_mas_frecuentes(vehiculo_fecha, request.user.perfil.compania),
                                            "fecha":fecha,
                                            "fecha_con_formato":fecha_con_formato,
                                            "flotas": Ubicacion.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania)),
                                            "hoy": hoy,
                                            "mes_1": mes_1,
                                            "mes_2": mes_2.strftime("%b"),
                                            "mes_3": mes_3.strftime("%b"),
                                            "mes_4": mes_4.strftime("%b"),
                                            "porcentaje_inflado":porcentaje_inflado,
                                            "porcentaje_entrada_correcta":porcentaje_entrada_correcta,
                                            "radar_min": radar_min_resta,
                                            "radar_max": radar_max,
                                            "rango_1": my_profile.compania.periodo1_inflado,
                                            "rango_2": my_profile.compania.periodo2_inflado,
                                            "rango_3": my_profile.compania.periodo1_inflado + 1,
                                            "rango_4": my_profile.compania.periodo2_inflado + 1,
                                            "tiempo_promedio": tiempo_promedio,
                                            "vehiculos": vehiculo_fecha,
                                            "vehiculos_periodo": vehiculo_periodo_status,
                                            "vehiculos_todos": vehiculo
                                        })

    elif clase:

        vehiculo_clase = vehiculo.filter(clase=clase.upper())
        bitacora_clase = bitacora.filter(numero_economico__in=vehiculo_clase)
        vehiculo_fecha = vehiculo_clase.filter(fecha_de_inflado__range=[ultimo_mes, hoy])

        vehiculo_fecha_barras = vehiculo_clase.filter(fecha_de_inflado__month=hoy.month)
        vehiculo_fecha_barras_2 = vehiculo_clase.filter(fecha_de_inflado__month=hoy.month - 1)
        vehiculo_fecha_barras_3 = vehiculo_clase.filter(fecha_de_inflado__month=hoy.month - 2)
        vehiculo_fecha_barras_4 = vehiculo_clase.filter(fecha_de_inflado__month=hoy.month - 3)
        vehiculo_fecha_barras_5 = vehiculo_clase.filter(fecha_de_inflado__month=hoy.month - 4)

        doble_entrada = functions.doble_entrada(bitacora_clase)
        doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculo)

        # Vehículos del periodo 2 y 3
        ultimo_mes = hoy - timedelta(days=31)
        vehiculo_periodo = vehiculo_clase.filter(fecha_de_inflado__lte=ultimo_mes) | vehiculo_clase.filter(fecha_de_inflado=None)

        # Status de los vehículos
        bitacora_periodo = bitacora.filter(numero_economico__in=vehiculo_periodo)
        vehiculo_periodo_status = {}
        mala_entrada_periodo = functions.mala_entrada(vehiculo_periodo)
        for v in vehiculo_periodo:
            if v in doble_mala_entrada:
                vehiculo_periodo_status[v] = "Doble Entrada"
            elif v in mala_entrada_periodo:
                vehiculo_periodo_status[v] = "Mala Entrada"
            else:
                vehiculo_periodo_status[v] = "Entrada Correctas"

        # Convertir formato de fecha
        fecha_con_formato = functions.convertir_fecha(fecha)

        # Saber el tiempo de inflado promedio
        tiempo_promedio = functions.inflado_promedio(vehiculo_clase)


        # Sacar el porcentaje de los vehículos inflados que hay dentro de los vehículos
        porcentaje_inflado = functions.porcentaje(vehiculo_fecha.count(), vehiculo_clase.count())

        # Sacar cuántos vehículos tienen la entrada correcta
        entrada_correcta_contar = functions.contar_entrada_correcta(vehiculo_fecha)
        
        mes_1 = hoy.strftime("%b")
        mes_2 = functions.mes_anterior(hoy)
        mes_3 = functions.mes_anterior(mes_2)
        mes_4 = functions.mes_anterior(mes_3)
        mes_5 = functions.mes_anterior(mes_4)

        vehiculo_mes1 = bitacora_clase.filter(fecha_de_inflado__month=hoy.month)
        vehiculo_mes2 = bitacora_clase.filter(fecha_de_inflado__month=hoy.month - 1)
        vehiculo_mes3 = bitacora_clase.filter(fecha_de_inflado__month=hoy.month - 2)
        vehiculo_mes4 = bitacora_clase.filter(fecha_de_inflado__month=hoy.month - 3)
        
        mala_entrada_contar_mes1 = functions.contar_mala_entrada(vehiculo_mes1)
        mala_entrada_contar_mes2 = functions.contar_mala_entrada(vehiculo_mes2)
        mala_entrada_contar_mes3 = functions.contar_mala_entrada(vehiculo_mes3)
        mala_entrada_contar_mes4 = functions.contar_mala_entrada(vehiculo_mes4)

        entrada_correcta_contar_barras_mes1 = functions.contar_entrada_correcta(vehiculo_fecha_barras)
        entrada_correcta_contar_barras_mes2 = functions.contar_entrada_correcta(vehiculo_fecha_barras_2)
        entrada_correcta_contar_barras_mes3 = functions.contar_entrada_correcta(vehiculo_fecha_barras_3)
        entrada_correcta_contar_barras_mes4 = functions.contar_entrada_correcta(vehiculo_fecha_barras_4)
        entrada_correcta_contar_barras_mes5 = functions.contar_entrada_correcta(vehiculo_fecha_barras_5)

        # Sacar el porcentaje de los vehículos con entrada correcta que hay dentro de los vehículos seleccionados
        porcentaje_entrada_correcta = functions.porcentaje(entrada_correcta_contar, vehiculo_fecha.count())

        # Calcular la proporción del radar 
        radar_min = functions.radar_min(vehiculo_clase, request.user.perfil.compania)
        radar_max = functions.radar_max(vehiculo_clase, request.user.perfil.compania)
        radar_min_resta = functions.radar_min_resta(radar_min, radar_max)

        return render(request, "pulpo.html", {
                                            "aplicaciones_mas_frecuentes_infladas": functions.aplicaciones_mas_frecuentes(vehiculo_fecha, vehiculo_clase, request.user.perfil.compania),
                                            "bitacoras": bitacora_clase,
                                            "boton_intuitivo": "Vehículos Vencidos",
                                            "doble_entrada": doble_entrada,
                                            "cantidad_entrada": entrada_correcta_contar,
                                            "cantidad_entrada_barras_mes1": entrada_correcta_contar_barras_mes1,
                                            "cantidad_entrada_barras_mes2": entrada_correcta_contar_barras_mes2,
                                            "cantidad_entrada_barras_mes3": entrada_correcta_contar_barras_mes3,
                                            "cantidad_entrada_barras_mes4": entrada_correcta_contar_barras_mes4,
                                            "cantidad_entrada_barras_mes5": entrada_correcta_contar_barras_mes5,
                                            "cantidad_entrada_mes1": mala_entrada_contar_mes1,
                                            "cantidad_entrada_mes2": mala_entrada_contar_mes2,
                                            "cantidad_entrada_mes3": mala_entrada_contar_mes3,
                                            "cantidad_entrada_mes4": mala_entrada_contar_mes4,
                                            "cantidad_inflado": vehiculo_fecha.count(),
                                            "cantidad_inflado_1": vehiculo_fecha_barras.count(),
                                            "cantidad_inflado_2": vehiculo_fecha_barras_2.count(),
                                            "cantidad_inflado_3": vehiculo_fecha_barras_3.count(),
                                            "cantidad_inflado_4": vehiculo_fecha_barras_4.count(),
                                            "cantidad_inflado_5": vehiculo_fecha_barras_5.count(),
                                            "cantidad_total": vehiculo_clase.count(),
                                            "clase": clase,
                                            "clases_compania": functions.clases_mas_frecuentes(vehiculo, request.user.perfil.compania),
                                            "clases_mas_frecuentes_infladas": functions.clases_mas_frecuentes(vehiculo_fecha, request.user.perfil.compania),
                                            "fecha":fecha,
                                            "fecha_con_formato":fecha_con_formato,
                                            "flotas": Ubicacion.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania)),
                                            "hoy": hoy,
                                            "mes_1": mes_1,
                                            "mes_2": mes_2.strftime("%b"),
                                            "mes_3": mes_3.strftime("%b"),
                                            "mes_4": mes_4.strftime("%b"),
                                            "mes_5": mes_5.strftime("%b"),
                                            "porcentaje_inflado":porcentaje_inflado,
                                            "porcentaje_entrada_correcta":porcentaje_entrada_correcta,
                                            "radar_min": radar_min_resta,
                                            "radar_max": radar_max,
                                            "rango_1": my_profile.compania.periodo1_inflado,
                                            "rango_2": my_profile.compania.periodo2_inflado,
                                            "rango_3": my_profile.compania.periodo1_inflado + 1,
                                            "rango_4": my_profile.compania.periodo2_inflado + 1,
                                            "tiempo_promedio": tiempo_promedio,
                                            "vehiculos": vehiculo_clase,
                                            "vehiculos_periodo": vehiculo_periodo_status,
                                            "vehiculos_todos": vehiculo_clase
                                        })
    elif flota:

        vehiculo_flota = vehiculo.filter(ubicacion=Ubicacion.objects.get(nombre=flota))
        bitacora_flota = bitacora.filter(numero_economico__in=vehiculo_flota)
        vehiculo_fecha = vehiculo_flota.filter(fecha_de_inflado__range=[ultimo_mes, hoy])

        vehiculo_fecha_barras = vehiculo_flota.filter(fecha_de_inflado__month=hoy.month)
        vehiculo_fecha_barras_2 = vehiculo_flota.filter(fecha_de_inflado__month=hoy.month - 1)
        vehiculo_fecha_barras_3 = vehiculo_flota.filter(fecha_de_inflado__month=hoy.month - 2)
        vehiculo_fecha_barras_4 = vehiculo_flota.filter(fecha_de_inflado__month=hoy.month - 3)
        vehiculo_fecha_barras_5 = vehiculo_flota.filter(fecha_de_inflado__month=hoy.month - 4)

        doble_entrada = functions.doble_entrada(bitacora_flota)
        doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculo)

        # Vehículos del periodo 2 y 3
        ultimo_mes = hoy - timedelta(days=31)
        vehiculo_periodo = vehiculo_flota.filter(fecha_de_inflado__lte=ultimo_mes) | vehiculo_flota.filter(fecha_de_inflado=None)

        # Status de los vehículos
        bitacora_periodo = bitacora.filter(numero_economico__in=vehiculo_periodo)
        vehiculo_periodo_status = {}
        mala_entrada_periodo = functions.mala_entrada(vehiculo_periodo)
        for v in vehiculo_periodo:
            if v in doble_mala_entrada:
                vehiculo_periodo_status[v] = "Doble Entrada"
            elif v in mala_entrada_periodo:
                vehiculo_periodo_status[v] = "Mala Entrada"
            else:
                vehiculo_periodo_status[v] = "Entrada Correctas"

        # Convertir formato de fecha
        fecha_con_formato = functions.convertir_fecha(fecha)

        # Saber el tiempo de inflado promedio
        tiempo_promedio = functions.inflado_promedio(vehiculo_flota)


        # Sacar el porcentaje de los vehículos inflados que hay dentro de los vehículos
        porcentaje_inflado = functions.porcentaje(vehiculo_fecha.count(), vehiculo_flota.count())

        # Sacar cuántos vehículos tienen la entrada correcta
        entrada_correcta_contar = functions.contar_entrada_correcta(vehiculo_fecha)
        
        mes_1 = hoy.strftime("%b")
        mes_2 = functions.mes_anterior(hoy)
        mes_3 = functions.mes_anterior(mes_2)
        mes_4 = functions.mes_anterior(mes_3)
        mes_5 = functions.mes_anterior(mes_4)

        vehiculo_mes1 = bitacora_flota.filter(fecha_de_inflado__month=hoy.month)
        vehiculo_mes2 = bitacora_flota.filter(fecha_de_inflado__month=hoy.month - 1)
        vehiculo_mes3 = bitacora_flota.filter(fecha_de_inflado__month=hoy.month - 2)
        vehiculo_mes4 = bitacora_flota.filter(fecha_de_inflado__month=hoy.month - 3)
        
        mala_entrada_contar_mes1 = functions.contar_mala_entrada(vehiculo_mes1)
        mala_entrada_contar_mes2 = functions.contar_mala_entrada(vehiculo_mes2)
        mala_entrada_contar_mes3 = functions.contar_mala_entrada(vehiculo_mes3)
        mala_entrada_contar_mes4 = functions.contar_mala_entrada(vehiculo_mes4)

        entrada_correcta_contar_barras_mes1 = functions.contar_entrada_correcta(vehiculo_fecha_barras)
        entrada_correcta_contar_barras_mes2 = functions.contar_entrada_correcta(vehiculo_fecha_barras_2)
        entrada_correcta_contar_barras_mes3 = functions.contar_entrada_correcta(vehiculo_fecha_barras_3)
        entrada_correcta_contar_barras_mes4 = functions.contar_entrada_correcta(vehiculo_fecha_barras_4)
        entrada_correcta_contar_barras_mes5 = functions.contar_entrada_correcta(vehiculo_fecha_barras_5)

        # Sacar el porcentaje de los vehículos con entrada correcta que hay dentro de los vehículos seleccionados
        porcentaje_entrada_correcta = functions.porcentaje(entrada_correcta_contar, vehiculo_fecha.count())

        # Calcular la proporción del radar 
        radar_min = functions.radar_min(vehiculo_flota, request.user.perfil.compania)
        radar_max = functions.radar_max(vehiculo_flota, request.user.perfil.compania)
        radar_min_resta = functions.radar_min_resta(radar_min, radar_max)

        return render(request, "pulpo.html", {
                                            "aplicaciones_mas_frecuentes_infladas": functions.aplicaciones_mas_frecuentes(vehiculo_fecha, vehiculo_flota, request.user.perfil.compania),
                                            "bitacoras": bitacora_flota,
                                            "boton_intuitivo": "Vehículos Vencidos",
                                            "doble_entrada": doble_entrada,
                                            "cantidad_entrada": entrada_correcta_contar,
                                            "cantidad_entrada_barras_mes1": entrada_correcta_contar_barras_mes1,
                                            "cantidad_entrada_barras_mes2": entrada_correcta_contar_barras_mes2,
                                            "cantidad_entrada_barras_mes3": entrada_correcta_contar_barras_mes3,
                                            "cantidad_entrada_barras_mes4": entrada_correcta_contar_barras_mes4,
                                            "cantidad_entrada_barras_mes5": entrada_correcta_contar_barras_mes5,
                                            "cantidad_entrada_mes1": mala_entrada_contar_mes1,
                                            "cantidad_entrada_mes2": mala_entrada_contar_mes2,
                                            "cantidad_entrada_mes3": mala_entrada_contar_mes3,
                                            "cantidad_entrada_mes4": mala_entrada_contar_mes4,
                                            "cantidad_inflado": vehiculo_fecha.count(),
                                            "cantidad_inflado_1": vehiculo_fecha_barras.count(),
                                            "cantidad_inflado_2": vehiculo_fecha_barras_2.count(),
                                            "cantidad_inflado_3": vehiculo_fecha_barras_3.count(),
                                            "cantidad_inflado_4": vehiculo_fecha_barras_4.count(),
                                            "cantidad_inflado_5": vehiculo_fecha_barras_5.count(),
                                            "cantidad_total": vehiculo_flota.count(),
                                            "clases_compania": functions.clases_mas_frecuentes(vehiculo, request.user.perfil.compania),
                                            "clases_mas_frecuentes_infladas": functions.clases_mas_frecuentes(vehiculo_fecha, request.user.perfil.compania),
                                            "fecha":fecha,
                                            "fecha_con_formato":fecha_con_formato,
                                            "flota": flota,
                                            "flotas": Ubicacion.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania)),
                                            "hoy": hoy,
                                            "mes_1": mes_1,
                                            "mes_2": mes_2.strftime("%b"),
                                            "mes_3": mes_3.strftime("%b"),
                                            "mes_4": mes_4.strftime("%b"),
                                            "mes_5": mes_5.strftime("%b"),
                                            "porcentaje_inflado":porcentaje_inflado,
                                            "porcentaje_entrada_correcta":porcentaje_entrada_correcta,
                                            "radar_min": radar_min_resta,
                                            "radar_max": radar_max,
                                            "rango_1": my_profile.compania.periodo1_inflado,
                                            "rango_2": my_profile.compania.periodo2_inflado,
                                            "rango_3": my_profile.compania.periodo1_inflado + 1,
                                            "rango_4": my_profile.compania.periodo2_inflado + 1,
                                            "tiempo_promedio": tiempo_promedio,
                                            "vehiculos": vehiculo_flota,
                                            "vehiculos_periodo": vehiculo_periodo_status,
                                            "vehiculos_todos": vehiculo_flota
                                        })
    elif boton_intuitivo:
        ultimo_mes = hoy - timedelta(days=31)

        mes_1 = hoy.strftime("%b")
        mes_2 = functions.mes_anterior(hoy)
        mes_3 = functions.mes_anterior(mes_2)
        mes_4 = functions.mes_anterior(mes_3)

        vehiculo_fecha = vehiculo.filter(fecha_de_inflado__range=[ultimo_mes, hoy])
        vehiculo_fecha_barras = vehiculo.filter(fecha_de_inflado__month=hoy.month)
        vehiculo_fecha_barras_2 = vehiculo.filter(fecha_de_inflado__month=hoy.month - 1)
        vehiculo_mes1 = bitacora.filter(fecha_de_inflado__month=hoy.month)
        vehiculo_mes2 = bitacora.filter(fecha_de_inflado__month=hoy.month - 1)
        vehiculo_mes3 = bitacora.filter(fecha_de_inflado__month=hoy.month - 2)
        vehiculo_mes4 = bitacora.filter(fecha_de_inflado__month=hoy.month - 3)

        entrada_correcta_contar = functions.contar_entrada_correcta(vehiculo_fecha)
        entrada_correcta_contar_mes1 = functions.contar_entrada_correcta(vehiculo_mes1)
        entrada_correcta_contar_mes2 = functions.contar_entrada_correcta(vehiculo_mes2)
        entrada_correcta_contar_mes3 = functions.contar_entrada_correcta(vehiculo_mes3)
        entrada_correcta_contar_mes4 = functions.contar_entrada_correcta(vehiculo_mes4)

        entrada_correcta_contar_barras_mes1 = functions.contar_entrada_correcta(vehiculo_fecha_barras)
        entrada_correcta_contar_barras_mes2 = functions.contar_entrada_correcta(vehiculo_fecha_barras_2)

        doble_entrada = functions.doble_entrada(bitacora)
        doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculo)

        vehiculo_periodo = vehiculo.filter(fecha_de_inflado__lte=ultimo_mes) | vehiculo.filter(fecha_de_inflado=None)
        bitacora_periodo = bitacora.filter(numero_economico__in=vehiculo_periodo)
        mala_entrada = functions.mala_entrada(vehiculo_periodo)
        vehiculo_periodo_status = {}

        if boton_intuitivo == "Vehículos Vencidos":
            for v in vehiculo_periodo:
                if v in doble_mala_entrada:
                    vehiculo_periodo_status[v] = "Doble Entrada"
                elif v in mala_entrada:
                    vehiculo_periodo_status[v] = "Mala Entrada"
                else:
                    vehiculo_periodo_status[v] = True

        elif boton_intuitivo == "Malas Entradas":
            vehiculo_periodo = vehiculo
            bitacora_periodo = bitacora.filter(numero_economico__in=vehiculo_periodo)
            mala_entrada = functions.mala_entrada(vehiculo_periodo)
            for v in vehiculo_periodo:
                if v in doble_mala_entrada:
                    vehiculo_periodo_status[v] = "Doble Entrada"
                elif v in mala_entrada:
                    vehiculo_periodo_status[v] = "Mala Entrada"


        my_profile = Perfil.objects.get(user=request.user)

        radar_min = functions.radar_min(vehiculo_fecha, request.user.perfil.compania)
        radar_max = functions.radar_max(vehiculo_fecha, request.user.perfil.compania)
        radar_min_resta = functions.radar_min_resta(radar_min, radar_max)


        return render(request, "pulpo.html", {
                                            "aplicaciones": Aplicacion.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania)),
                                            "aplicaciones_mas_frecuentes_infladas": functions.aplicaciones_mas_frecuentes(vehiculo_fecha, vehiculo, request.user.perfil.compania),
                                            "bitacoras": bitacora,
                                            "boton_intuitivo": boton_intuitivo,
                                            "doble_entrada": doble_entrada,
                                            "cantidad_inflado": vehiculo_fecha.count(),
                                            "cantidad_inflado_1": vehiculo_fecha_barras.count(),
                                            "cantidad_inflado_2": vehiculo_fecha_barras_2.count(),
                                            "cantidad_entrada": entrada_correcta_contar,
                                            "cantidad_entrada_barras_mes1": entrada_correcta_contar_barras_mes1,
                                            "cantidad_entrada_barras_mes2": entrada_correcta_contar_barras_mes2,
                                            "cantidad_entrada_mes1": entrada_correcta_contar_mes1,
                                            "cantidad_entrada_mes2": entrada_correcta_contar_mes2,
                                            "cantidad_entrada_mes3": entrada_correcta_contar_mes3,
                                            "cantidad_entrada_mes4": entrada_correcta_contar_mes4,
                                            "cantidad_total": vehiculo.count(),
                                            "clases_compania": functions.clases_mas_frecuentes(vehiculo, request.user.perfil.compania),
                                            "clases_mas_frecuentes_infladas": functions.clases_mas_frecuentes(vehiculo_fecha, request.user.perfil.compania),
                                            "compania": request.user.perfil.compania,
                                            "flotas": Ubicacion.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania)),
                                            "hoy": hoy,
                                            "mes_1": mes_1,
                                            "mes_2": mes_2.strftime("%b"),
                                            "mes_3": mes_3.strftime("%b"),
                                            "mes_4": mes_4.strftime("%b"),
                                            "porcentaje_inflado": functions.porcentaje(vehiculo_fecha.count(), vehiculo.count()),
                                            "porcentaje_entrada_correcta": functions.porcentaje(entrada_correcta_contar, vehiculo_fecha.count()),
                                            "radar_min": radar_min_resta,
                                            "radar_max": radar_max,
                                            "rango_1": my_profile.compania.periodo1_inflado,
                                            "rango_2": my_profile.compania.periodo2_inflado,
                                            "rango_3": my_profile.compania.periodo1_inflado + 1,
                                            "rango_4": my_profile.compania.periodo2_inflado + 1,
                                            "tiempo_promedio": functions.inflado_promedio(vehiculo_fecha),
                                            "vehiculos": vehiculo_fecha,
                                            "vehiculos_periodo": vehiculo_periodo_status,
                                            "vehiculos_todos": vehiculo,
                                        })



    else:
        return redirect("dashboards:pulpo")

class ConfigView(LoginRequiredMixin, CreateView):
    # Vista del dashboard configuración
    template_name = "config.html"
    form_class = ExcelForm
    success_url = reverse_lazy('dashboards:pulpo')

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user)
        context["user"] = user
        return context

class SearchView(LoginRequiredMixin, ListView):
    # Vista del dashboard buscar_vehiculos
    template_name = "buscar_vehiculos.html"
    model = Vehiculo
    ordering = ("-fecha_de_creacion")
    form_class = VehiculoForm

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        vehiculos = Vehiculo.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        
        filtro_sospechoso = functions.vehiculo_sospechoso(inspecciones)
        vehiculos_sospechosos = vehiculos.filter(id__in=filtro_sospechoso)

        doble_entrada = functions.doble_entrada(bitacora)
        filtro_rojo = functions.vehiculo_rojo(llantas, doble_entrada[0])
        vehiculos_rojos = vehiculos.filter(id__in=filtro_rojo).exclude(id__in=vehiculos_sospechosos)

        filtro_amarillo = functions.vehiculo_amarillo(llantas)
        vehiculos_amarillos = vehiculos.filter(id__in=filtro_amarillo).exclude(id__in=vehiculos_rojos).exclude(id__in=vehiculos_sospechosos)

        vehiculos_verdes = vehiculos.exclude(id__in=vehiculos_rojos).exclude(id__in=vehiculos_sospechosos).exclude(id__in=vehiculos_amarillos)

        context["vehiculos_amarillos"] = vehiculos_amarillos
        context["vehiculos_rojos"] = vehiculos_rojos
        context["vehiculos_sospechosos"] = vehiculos_sospechosos
        context["vehiculos_verdes"] = vehiculos_verdes
        context["cantidad_amarillos"] = vehiculos_amarillos.count()
        context["cantidad_rojos"] = vehiculos_rojos.count()
        context["cantidad_sospechosos"] = vehiculos_sospechosos.count()
        context["cantidad_total"] = vehiculos.count()
        context["cantidad_verdes"] = vehiculos_verdes.count()

        return context



def search(request):
    num = request.GET.get("numero_economico")
    fecha = request.GET.get("fecha1")
    if num:
        vehiculos = Vehiculo.objects.filter(numero_economico__icontains=num, compania=Compania.objects.get(compania=request.user.perfil.compania))
        bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
        
        doble_entrada = functions.doble_entrada(bitacora)
        vehiculos_rojos = vehiculos.filter(numero_economico__in=doble_entrada)

        vehiculos_verdes = vehiculos.exclude(numero_economico__in=doble_entrada)
        return render(request, "buscar_vehiculos.html", {
                                                "vehiculos_rojos": vehiculos_rojos,
                                                "vehiculos_verdes": vehiculos_verdes,
                                                "cantidad_rojos": vehiculos_rojos.count(),
                                                "cantidad_total": vehiculos.count(),
                                                "cantidad_verdes": vehiculos_verdes.count()
        })
    elif fecha:
        dividir_fecha = functions.convertir_rango(fecha)
        primera_fecha = datetime.strptime(dividir_fecha[0], "%m/%d/%Y").date()
        segunda_fecha = datetime.strptime(dividir_fecha[1], "%m/%d/%Y").date()

        vehiculos = Vehiculo.objects.filter(fecha_de_inflado__range=[primera_fecha, segunda_fecha], compania=Compania.objects.get(compania=request.user.perfil.compania))
        bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
        
        doble_entrada = functions.doble_entrada(bitacora)
        vehiculos_rojos = vehiculos.filter(numero_economico__in=doble_entrada)

        vehiculos_verdes = vehiculos.exclude(numero_economico__in=doble_entrada)
        return render(request, "buscar_vehiculos.html", {
                                                "fecha": fecha,
                                                "vehiculos_rojos": vehiculos_rojos,
                                                "vehiculos_verdes": vehiculos_verdes,
                                                "cantidad_rojos": vehiculos_rojos.count(),
                                                "cantidad_total": vehiculos.count(),
                                                "cantidad_verdes": vehiculos_verdes.count()
        })
    else:

        vehiculos = Vehiculo.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
        bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
        
        doble_entrada = functions.doble_entrada(bitacora)
        vehiculos_rojos = vehiculos.filter(numero_economico__in=doble_entrada)

        vehiculos_verdes = vehiculos.exclude(numero_economico__in=doble_entrada)
        return render(request, "buscar_vehiculos.html", {
                                                "vehiculos_rojos": vehiculos_rojos,
                                                "vehiculos_verdes": vehiculos_verdes,
                                                "cantidad_rojos": vehiculos_rojos.count(),
                                                "cantidad_total": vehiculos.count(),
                                                "cantidad_verdes": vehiculos_verdes.count()
        })


class tireDetailView(LoginRequiredMixin, DetailView):
    # Vista de tireDetailView

    template_name = "tireDetail.html"
    slug_field = "llanta"
    slug_url_kwarg = "llanta"
    queryset = Llanta.objects.all()
    context_object_name = "llanta"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        llanta = self.get_object()
        vehiculo = llanta.vehiculo

        try:
            bitacora = Bitacora.objects.filter(numero_economico=Vehiculo.objects.get(numero_economico=vehiculo.numero_economico), compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        except:
            bitacora = None
        entradas_correctas = functions.entrada_correcta(bitacora)

        hoy = date.today()
        mes_1 = hoy.strftime("%b")
        mes_2 = functions.mes_anterior(hoy)
        mes_3 = functions.mes_anterior(mes_2)
        mes_4 = functions.mes_anterior(mes_3)
        hoy1 = hoy.strftime("%m")
        hoy2 = mes_2.strftime("%m")
        hoy3 = mes_3.strftime("%m")
        hoy4 = mes_4.strftime("%m")

        color = functions.entrada_correcta(vehiculo)

        vehiculo_mes1 = bitacora.filter(fecha_de_inflado__month=hoy1)
        vehiculo_mes2 = bitacora.filter(fecha_de_inflado__month=hoy2)
        vehiculo_mes3 = bitacora.filter(fecha_de_inflado__month=hoy3)
        vehiculo_mes4 = bitacora.filter(fecha_de_inflado__month=hoy4)

        mala_entrada_contar_mes1 = functions.contar_mala_entrada(vehiculo_mes1)
        mala_entrada_contar_mes2 = functions.contar_mala_entrada(vehiculo_mes2)
        mala_entrada_contar_mes3 = functions.contar_mala_entrada(vehiculo_mes3)
        mala_entrada_contar_mes4 = functions.contar_mala_entrada(vehiculo_mes4)

        doble_entrada = functions.doble_entrada(bitacora)
        doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculo)

        if doble_mala_entrada:
            vehiculo_status = "Doble Entrada"
            message = "Doble mala entrada"
            color = "bad"
        elif color == "bad":
            vehiculo_status = "Mala Entrada"
            message = "Tiene mala entrada"
        else:
            vehiculo_status = "Entrada Correctas"
            message = None

        context["bitacora"] = bitacora
        context["cantidad_doble_entrada_mes1"] = doble_entrada[1]["mes1"]
        context["cantidad_doble_entrada_mes2"] = doble_entrada[1]["mes2"]
        context["cantidad_doble_entrada_mes3"] = doble_entrada[1]["mes3"]
        context["cantidad_doble_entrada_mes4"] = doble_entrada[1]["mes4"]
        context["cantidad_entrada_mes1"] = mala_entrada_contar_mes1
        context["cantidad_entrada_mes2"] = mala_entrada_contar_mes2
        context["cantidad_entrada_mes3"] = mala_entrada_contar_mes3
        context["cantidad_entrada_mes4"] = mala_entrada_contar_mes4
        context["entradas"] = entradas_correctas
        context["hoy"] = hoy
        context["mes_1"] = mes_1
        context["mes_2"] = mes_2.strftime("%b")
        context["mes_3"] = mes_3.strftime("%b")
        context["mes_4"] = mes_4.strftime("%b")
        context["message"] = message
        context["vehiculo"] = vehiculo
        context["vehiculo_mes1"] = vehiculo_mes1.count()
        context["vehiculo_mes2"] = vehiculo_mes2.count()
        context["vehiculo_mes3"] = vehiculo_mes3.count()
        context["vehiculo_mes4"] = vehiculo_mes4.count()

        return context


class DetailView(LoginRequiredMixin, DetailView):
    # Vista del dashboard detail
    template_name = "detail.html"
    slug_field = "vehiculo"
    slug_url_kwarg = "vehiculo"
    queryset = Vehiculo.objects.all()
    context_object_name = "vehiculo"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        vehiculo = self.get_object()
        llantas = Llanta.objects.filter(vehiculo=vehiculo)
        try:
            bitacora = Bitacora.objects.filter(numero_economico=Vehiculo.objects.get(numero_economico=vehiculo.numero_economico), compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        except:
            bitacora = None
        entradas_correctas = functions.entrada_correcta(bitacora)
        fecha = functions.convertir_fecha(str(vehiculo.fecha_de_inflado))
        if vehiculo.fecha_de_inflado:
            inflado = 1
        else:
            inflado = 0

        hoy = date.today()

        mes_1 = hoy.strftime("%b")
        mes_2 = functions.mes_anterior(hoy)
        mes_3 = functions.mes_anterior(mes_2)
        mes_4 = functions.mes_anterior(mes_3)

        hoy1 = hoy.strftime("%m")
        hoy2 = mes_2.strftime("%m")
        hoy3 = mes_3.strftime("%m")
        hoy4 = mes_4.strftime("%m")

        color = functions.entrada_correcta(vehiculo)

        if bitacora:
            vehiculo_mes1 = bitacora.filter(fecha_de_inflado__month=hoy1)
            vehiculo_mes2 = bitacora.filter(fecha_de_inflado__month=hoy2)
            vehiculo_mes3 = bitacora.filter(fecha_de_inflado__month=hoy3)
            vehiculo_mes4 = bitacora.filter(fecha_de_inflado__month=hoy4)

            mala_entrada_contar_mes1 = functions.contar_mala_entrada(vehiculo_mes1)
            mala_entrada_contar_mes2 = functions.contar_mala_entrada(vehiculo_mes2)
            mala_entrada_contar_mes3 = functions.contar_mala_entrada(vehiculo_mes3)
            mala_entrada_contar_mes4 = functions.contar_mala_entrada(vehiculo_mes4)


            doble_entrada = functions.doble_entrada(bitacora)
            doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculo)

            if doble_mala_entrada:
                vehiculo_status = "Doble Entrada"
                message = "Doble mala entrada"
                color = "bad"
            elif color == "bad":
                vehiculo_status = "Mala Entrada"
                message = "Tiene mala entrada"
            else:
                vehiculo_status = "Entrada Correctas"
                message = None

            configuracion = vehiculo.configuracion
            cantidad_llantas = functions.cantidad_llantas(configuracion)

            context["bitacora"] = bitacora
            context["cantidad_doble_entrada_mes1"] = doble_entrada[1]["mes1"]
            context["cantidad_doble_entrada_mes2"] = doble_entrada[1]["mes2"]
            context["cantidad_doble_entrada_mes3"] = doble_entrada[1]["mes3"]
            context["cantidad_doble_entrada_mes4"] = doble_entrada[1]["mes4"]
            context["cantidad_entrada_mes1"] = mala_entrada_contar_mes1
            context["cantidad_entrada_mes2"] = mala_entrada_contar_mes2
            context["cantidad_entrada_mes3"] = mala_entrada_contar_mes3
            context["cantidad_entrada_mes4"] = mala_entrada_contar_mes4
            context["cantidad_inflado"] = inflado
            context["cantidad_llantas"] = cantidad_llantas
            context["color"] = color
            context["configuracion"] = configuracion
            context["doble_entrada"] = doble_entrada
            context["entradas"] = entradas_correctas
            context["fecha"] = fecha
            context["hoy"] = hoy
            context["llanta1"] = llantas[0]
            context["llanta2"] = llantas[1]
            if cantidad_llantas >= 4:
                context["llanta3"] = llantas[2]
                context["llanta4"] = llantas[3]
                if cantidad_llantas >= 6:
                    context["llanta5"] = llantas[4]
                    context["llanta6"] = llantas[5]
                    if cantidad_llantas >= 8:
                        context["llanta7"] = llantas[6]
                        context["llanta8"] = llantas[7]
                        context["llanta9"] = llantas[7]
                        context["llanta10"] = llantas[7]
                        context["llanta11"] = llantas[7]
                        context["llanta12"] = llantas[7]
                        context["llanta13"] = llantas[7]
                        context["llanta14"] = llantas[7]
                        if cantidad_llantas >= 10:
                            context["llanta9"] = llantas[8]
                            context["llanta10"] = llantas[9]
                            if cantidad_llantas >= 12:
                                context["llanta11"] = llantas[10]
                                context["llanta12"] = llantas[11]
                                if cantidad_llantas >= 14:
                                    context["llanta13"] = llantas[12]
                                    context["llanta14"] = llantas[13]
            context["mes_1"] = mes_1
            context["mes_2"] = mes_2.strftime("%b")
            context["mes_3"] = mes_3.strftime("%b")
            context["mes_4"] = mes_4.strftime("%b")
            context["message"] = message
            context["vehiculo_mes1"] = vehiculo_mes1.count()
            context["vehiculo_mes2"] = vehiculo_mes2.count()
            context["vehiculo_mes3"] = vehiculo_mes3.count()
            context["vehiculo_mes4"] = vehiculo_mes4.count()
            context["vehiculo_status"] = vehiculo_status
        return context
