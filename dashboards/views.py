# Django
from ctypes import alignment
from operator import or_
from http.client import HTTPResponse
import re
from tkinter import CENTER
import matplotlib.pyplot as plt
import numpy as np
from django import forms
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.http.response import JsonResponse, HttpResponse
from django.db.models.aggregates import Min, Max, Count
from django.db.models.functions import Cast, ExtractMonth, ExtractDay, Now, Round, Substr, ExtractYear
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, ListView, TemplateView, DetailView, DeleteView, UpdateView, FormView
from django.views.generic.base import View

# Functions
from dashboards.functions import functions, functions_ftp, functions_create, functions_excel
from aeto import settings

# Forms
from dashboards.forms.forms import EdicionManual, ExcelForm, InspeccionForm, LlantaForm, VehiculoForm, ProductoForm, RenovadorForm, DesechoForm, DesechoEditForm, ObservacionForm, ObservacionEditForm, RechazoForm, RechazoEditForm, SucursalForm, TallerForm, UsuarioForm, AplicacionForm, CompaniaForm, UsuarioEditForm

# Models
from django.contrib.auth.models import User, Group
from dashboards.models import Aplicacion, Bitacora_Edicion, Bitacora_Pro, Inspeccion, Llanta, Producto, Registro_Bitacora, Ubicacion, Vehiculo, Perfil, Bitacora, Compania, Renovador, Desecho, Observacion, Rechazo, User, TendenciaCPK

# Utilities
from multi_form_view import MultiModelFormView
import csv
from datetime import date, datetime, timedelta
from ftplib import FTP as fileTP
import json
import mimetypes
import openpyxl
from openpyxl.chart import BarChart, Reference
import os
import pandas as pd
import statistics
import xlwt

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
        
        clase1 = self.request.GET.getlist("clase")
        clase2 = self.request.GET.get("clase2")
        flota1 = self.request.GET.getlist("flota")
        flota2 = self.request.GET.get("flota2")
        pay_boton = self.request.GET.get("boton_intuitivo")

        context = super().get_context_data(**kwargs)
        vehiculos_totales = Vehiculo.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        vehiculo = Vehiculo.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        if clase1:
            vehiculo = vehiculo.filter(functions.reduce(or_, [Q(clase=c.upper()) for c in clase1]))
        if flota1:
            vehiculo = vehiculo.filter(functions.reduce(or_, [Q(ubicacion=Ubicacion.objects.get(nombre=f)) for f in flota1]))

        if flota1:
            flotas_vehiculo = vehiculos_totales.values("ubicacion").distinct()
        else:
            flotas_vehiculo = vehiculo.values("ubicacion").distinct()
        flotas = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania), id__in=flotas_vehiculo)
        
        if clase1:
            clases = vehiculos_totales.values("clase").distinct()
        else:
            clases = vehiculo.values("clase").distinct()

        bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania), numero_economico__in=vehiculo)
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        hoy = date.today()
        
        periodo_2 = hoy - timedelta(days=self.request.user.perfil.compania.periodo2_inspeccion)
        vehiculos_vistos = vehiculo.filter(ultima_inspeccion__fecha_hora__lte=periodo_2) | vehiculo.filter(ultima_inspeccion__fecha_hora__isnull=True)
        porcentaje_visto = int((vehiculos_vistos.count()/vehiculo.count()) * 100)

        filtro_sospechoso = functions.vehiculo_sospechoso(inspecciones)
        vehiculos_sospechosos = vehiculo.filter(id__in=filtro_sospechoso)
        porcentaje_sospechoso = int((vehiculos_sospechosos.count()/vehiculo.count()) * 100)

        doble_entrada = functions.doble_mala_entrada(bitacora, vehiculo)
        filtro_rojo = functions.vehiculo_rojo(llantas, doble_entrada, vehiculo)
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

        mala_entrada_ejes = functions.mala_entrada_ejes(llantas, True)

        mes_1 = hoy.strftime("%b")
        mes_2 = functions.mes_anterior(hoy)
        mes_3 = functions.mes_anterior(mes_2)
        mes_4 = functions.mes_anterior(mes_3)

        hoy1 = hoy.strftime("%m")
        hoy2 = mes_2.strftime("%m")
        hoy3 = mes_3.strftime("%m")
        hoy4 = mes_4.strftime("%m")

        vehiculo_mes1 = bitacora.filter(fecha_de_inflado__month=hoy1)
        vehiculo_mes2 = bitacora.filter(fecha_de_inflado__month=hoy2)
        vehiculo_mes3 = bitacora.filter(fecha_de_inflado__month=hoy3)
        vehiculo_mes4 = bitacora.filter(fecha_de_inflado__month=hoy4)
        
        try:
            entrada_correcta_mes_1 = round((functions.contar_entrada_correcta(llantas) / llantas.count()) * 100, 2)
        except:
            entrada_correcta_mes_1 = 0

        vehiculos_vistos_mes_1 = vehiculo.filter(ultima_inspeccion__fecha_hora__month=hoy1)
        vehiculos_vistos_mes_2 = vehiculo.filter(ultima_inspeccion__fecha_hora__month=hoy2)
        vehiculos_vistos_mes_3 = vehiculo.filter(ultima_inspeccion__fecha_hora__month=hoy3)
        vehiculos_vistos_mes_4 = vehiculo.filter(ultima_inspeccion__fecha_hora__month=hoy4)

        vehiculos_rojos_mes_1 = vehiculos_rojos


        print(vehiculos_rojos_mes_1)

        vehiculos_amarillos_mes_1 = vehiculos_amarillos

        vehiculos_sospechosos_mes_1 = vehiculos_sospechosos

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

        context["a"] = False
        context["aplicacion_sin_inspeccionar_mes_1"] = aplicacion_sin_inspeccionar_mes_1
        context["aplicacion_sin_inspeccionar_mes_2"] = aplicacion_sin_inspeccionar_mes_2
        context["aplicacion_sin_inspeccionar_mes_3"] = aplicacion_sin_inspeccionar_mes_3
        context["clase1"] = clase1
        context["clase2"] = clase2
        context["clase_sin_inspeccionar_mes_1"] = clase_sin_inspeccionar_mes_1
        context["clase_sin_inspeccionar_mes_2"] = clase_sin_inspeccionar_mes_2
        context["clase_sin_inspeccionar_mes_3"] = clase_sin_inspeccionar_mes_3
        context["clases_mas_frecuentes_infladas"] = clases
        context["entrada_correcta_mes_1"] = entrada_correcta_mes_1
        context["entrada_correcta_mes_1_cantidad"] = functions.contar_entrada_correcta(llantas)
        context["entrada_correcta_mes_2"] = 0
        context["entrada_correcta_mes_3"] = 0
        context["entrada_correcta_mes_4"] = 0
        context["estatus_profundidad"] = estatus_profundidad
        context["flota1"] = flota1
        context["flota2"] = flota2
        context["flotas"] = flotas
        context["mala_entrada_ejes"] = mala_entrada_ejes
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
        context["vehiculos_amarillos_mes_2"] = 0
        context["vehiculos_amarillos_mes_3"] = 0
        context["vehiculos_amarillos_mes_4"] = 0
        context["vehiculos_por_aplicacion_sin_inspeccionar"] = vehiculos_por_aplicacion_sin_inspeccionar
        context["vehiculos_por_clase_sin_inspeccionar"] = vehiculos_por_clase_sin_inspeccionar
        context["vehiculos_rojos"] = vehiculos_rojos.count()
        context["vehiculos_rojos_mes_1"] = vehiculos_rojos_mes_1.count()
        context["vehiculos_rojos_mes_2"] = 0
        context["vehiculos_rojos_mes_3"] = 0
        context["vehiculos_rojos_mes_4"] = 0
        context["vehiculos_sospechosos"] = vehiculos_sospechosos.count()
        context["vehiculos_sospechosos_mes_1"] = vehiculos_sospechosos_mes_1.count()
        context["vehiculos_sospechosos_mes_2"] = 0
        context["vehiculos_sospechosos_mes_3"] = 0
        context["vehiculos_sospechosos_mes_4"] = 0
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

        clase = self.request.GET.getlist("clase")
        clase2 = self.request.GET.get("clase2")
        flota = self.request.GET.getlist("flota")
        flota2 = self.request.GET.get("flota2")
        aplicacion = self.request.GET.getlist("aplicacion")
        aplicacion2 = self.request.GET.get("aplicacion2")
        compania = Compania.objects.get(compania=self.request.user.perfil.compania)
        
        context = super().get_context_data(**kwargs)
        if clase:
            vehiculo = Vehiculo.objects.filter(functions.reduce(or_, [Q(clase=c.upper()) for c in clase]), compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        elif flota:
            vehiculo = Vehiculo.objects.filter(functions.reduce(or_, [Q(ubicacion=Ubicacion.objects.get(nombre=f)) for f in flota]), compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        elif aplicacion:
            vehiculo = Vehiculo.objects.filter(functions.reduce(or_, [Q(aplicacion=Aplicacion.objects.get(nombre=a)) for a in aplicacion]), compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        else:
            vehiculo = Vehiculo.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))

        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), vehiculo__in=vehiculo)
        inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), llanta__vehiculo__in=vehiculo)
        ubicacion = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))[0]

        reemplazo_actual = functions.reemplazo_actual(llantas)
        # Te elimina los ejes vacíos
        reemplazo_actual_llantas = reemplazo_actual[0]
        reemplazo_actual_ejes = {k: v for k, v in reemplazo_actual[1].items() if v != 0}


        print(reemplazo_actual_llantas)
        print(reemplazo_actual_ejes)

        reemplazo_dual = functions.reemplazo_dual(llantas, reemplazo_actual_llantas)
        reemplazo_total = functions.reemplazo_total(reemplazo_actual_ejes, reemplazo_dual)

        """print("llantas", llantas)
        print("reemplazo_actual_llantas", reemplazo_actual_llantas)
        print("reemplazo_actual", reemplazo_actual)
        print("reemplazo_dual", reemplazo_dual)"""

        # Sin regresión
        embudo_vida1 = functions.embudo_vidas(llantas)
        pronostico_de_consumo = {k: v for k, v in embudo_vida1[1].items() if v != 0}
        presupuesto = functions.presupuesto(pronostico_de_consumo, ubicacion)

        # Con regresión
        embudo_vida2 = functions.embudo_vidas_con_regresion(inspecciones, ubicacion, 30)
        embudo_vida3 = functions.embudo_vidas_con_regresion(inspecciones, ubicacion, 60)
        embudo_vida4 = functions.embudo_vidas_con_regresion(inspecciones, ubicacion, 90)
        pronostico_de_consumo2 = {k: v for k, v in embudo_vida2[1].items() if v != 0}
        pronostico_de_consumo3 = {k: v for k, v in embudo_vida3[1].items() if v != 0}
        pronostico_de_consumo4 = {k: v for k, v in embudo_vida4[1].items() if v != 0}
        presupuesto2 = functions.presupuesto(pronostico_de_consumo2, ubicacion)
        presupuesto3 = functions.presupuesto(pronostico_de_consumo3, ubicacion)
        presupuesto4 = functions.presupuesto(pronostico_de_consumo4, ubicacion)


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

        context["aplicacion1"] = aplicacion
        context["aplicacion2"] = aplicacion2
        context["aplicaciones"] = Aplicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        context["clase1"] = clase
        context["clase2"] = clase2
        context["clases_mas_frecuentes_infladas"] = functions.clases_mas_frecuentes(vehiculo, self.request.user.perfil.compania)
        context["compania"] = str(compania)
        context["embudo"] = embudo_vida1[1]
        context["flota1"] = flota
        context["flota2"] = flota2
        context["flotas"] = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        context["presupuesto"] = presupuesto
        context["presupuesto2"] = presupuesto2
        context["presupuesto3"] = presupuesto3
        context["presupuesto4"] = presupuesto4
        context["pronostico_de_consumo"] = pronostico_de_consumo
        context["pronostico_de_consumo2"] = pronostico_de_consumo2
        context["pronostico_de_consumo3"] = pronostico_de_consumo3
        context["pronostico_de_consumo4"] = pronostico_de_consumo4
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
        vehiculos_totales = Vehiculo.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        llantas_totales = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), vehiculo__in=vehiculos_totales)

        flota1 = self.request.GET.getlist("flota")
        flota2 = self.request.GET.get("flota2")
        eje1 = self.request.GET.getlist("eje")
        eje2 = self.request.GET.get("eje2")
        vehiculo1 = self.request.GET.getlist("vehiculo")
        vehiculo2 = self.request.GET.get("vehiculo2")
        aplicacion1 = self.request.GET.getlist("aplicacion")
        aplicacion2 = self.request.GET.getlist("aplicacion2")
        posicion1 = self.request.GET.getlist("posicion")
        posicion2 = self.request.GET.getlist("posicion2")
        clase1 = self.request.GET.getlist("clase")
        clase2 = self.request.GET.getlist("clase2")
        producto1 = self.request.GET.getlist("producto")
        producto2 = self.request.GET.getlist("producto2")

        vehiculos = Vehiculo.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))

        if flota1:
            vehiculos = vehiculos.filter(functions.reduce(or_, [Q(ubicacion=Ubicacion.objects.get(nombre=f)) for f in flota1]))
        if vehiculo1:
            vehiculos = vehiculos.filter(functions.reduce(or_, [Q(numero_economico=v) for v in vehiculo1]))
        if aplicacion1:
            vehiculos = vehiculos.filter(functions.reduce(or_, [Q(aplicacion=Aplicacion.objects.get(nombre=a)) for a in aplicacion1]))
        if clase1:
            vehiculos = vehiculos.filter(functions.reduce(or_, [Q(clase=c.upper()) for c in clase1]))

        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), vehiculo__in=vehiculos)

        if eje1:
            llantas = llantas.filter(functions.reduce(or_, [Q(nombre_de_eje=e) for e in eje1]))
        if producto1:
            llantas = llantas.filter(functions.reduce(or_, [Q(producto=Producto.objects.get(producto=p)) for p in producto1]))
        if posicion1:
            llantas = llantas.filter(functions.reduce(or_, [Q(posicion=p) for p in posicion1]))

        inspecciones = Inspeccion.objects.filter(llanta__in=llantas)
        if producto1:
            productos_llanta = llantas_totales.values("producto").distinct()
        else:
            productos_llanta = llantas.values("producto").distinct()
        productos = Producto.objects.filter(id__in=productos_llanta)
        if posicion1:
            posiciones = llantas_totales.values("posicion").distinct()
        else:
            posiciones = llantas.values("posicion").distinct()
        if flota1:
            flotas_vehiculo = vehiculos_totales.values("ubicacion__nombre").distinct()
        else:
            flotas_vehiculo = vehiculos.values("ubicacion__nombre").distinct()
        flotas = Ubicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania), nombre__in=flotas_vehiculo)
        if aplicacion1:
            aplicaciones_vehiculo = vehiculos_totales.values("aplicacion__nombre").distinct()
        else:
            aplicaciones_vehiculo = vehiculos.values("aplicacion__nombre").distinct()
        aplicaciones = Aplicacion.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania), nombre__in=aplicaciones_vehiculo)
        if eje1:
            ejes = llantas_totales.values("nombre_de_eje").distinct()
        else:
            ejes = llantas.values("nombre_de_eje").distinct()
        
        if clase1:
            clases = vehiculos_totales.values("clase").distinct()
        else:
            clases = vehiculos.values("clase").distinct()

        hoy = date.today()
        mes_1 = hoy.strftime("%b")
        mes_2 = functions.mes_anterior(hoy)
        mes_3 = functions.mes_anterior(mes_2)
        mes_4 = functions.mes_anterior(mes_3)
        mes_5 = functions.mes_anterior(mes_4)
        mes_6 = functions.mes_anterior(mes_5)
        mes_7 = functions.mes_anterior(mes_6)
        mes_8 = functions.mes_anterior(mes_7)

        regresion = functions.km_proyectado(inspecciones, True)
        km_proyectado = regresion[0]
        km_x_mm = regresion[1]
        cpk = regresion[2]
        llantas_limpias = regresion[4]
        llantas_analizadas = llantas.filter(numero_economico__in=llantas_limpias)
        try:
            porcentaje_limpio = (len(llantas_limpias)/llantas.count())*100
        except:
            porcentaje_limpio = 0


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
            
            llantas_producto_total = llantas.filter(producto=producto)
            llantas_producto = llantas.filter(producto=producto, numero_economico__in=llantas_limpias)
            desgaste = functions.desgaste_irregular_producto(llantas_producto)
            porcentaje_analizadas = functions.porcentaje(llantas_producto.count(), llantas_producto_total.count())

            inspecciones_producto = Inspeccion.objects.filter(llanta__in=llantas_producto)
            regresion_producto = functions.km_proyectado(inspecciones_producto, False)
            km_proyectado_producto = regresion_producto[0]
            km_x_mm_producto = regresion_producto[1]
            cpk_producto = regresion_producto[2]
            cantidad = llantas_producto.count()
            dibujo = str(producto.dibujo).replace(" ", "_")

            valores_producto.append(km_proyectado_producto)
            valores_producto.append(km_x_mm_producto)
            valores_producto.append(cpk_producto)
            valores_producto.append(cantidad)
            valores_producto.append(desgaste)
            valores_producto.append(porcentaje_analizadas)
            valores_producto.append(dibujo)

            if dibujo != "None":
                if regresion_producto[0] != 0 or regresion_producto[3] != 0:
                    if regresion_producto[3] != []:
                        if  regresion_producto[3].pop() != 0:
                            print(regresion_producto[3])
                            comparativa_de_productos[producto] = valores_producto

                            km_productos[dibujo] = regresion_producto[0]
                            cpk_productos[dibujo] = regresion_producto[3]

        productos_sort = sorted(comparativa_de_productos.items(), key=lambda p:p[1][2])
        comparativa_de_productos = {}
        for c in productos_sort:
            comparativa_de_productos[c[0]] = c[1]
            
        comparativa_de_flotas = {}
        cpk_flotas = {}
        km_flotas = {}
        for flota in flotas:
            valores_flota = []
            
            llantas_flota = llantas.filter(vehiculo__ubicacion=flota, numero_economico__in=llantas_limpias)
            if llantas_flota:
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
            
            llantas_vehiculo = llantas.filter(vehiculo=vehiculo, numero_economico__in=llantas_limpias)
            if llantas_vehiculo:
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

            llantas_aplicacion = llantas.filter(vehiculo__aplicacion =aplicacion, numero_economico__in=llantas_limpias)
            if llantas_aplicacion:

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

            llantas_eje = llantas.filter(nombre_de_eje=eje["nombre_de_eje"], numero_economico__in=llantas_limpias)
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
                
                comparativa_de_ejes[eje["nombre_de_eje"]] = valores_eje

        comparativa_de_posiciones = {}
        for posicion in posiciones:
            valores_posicion = []

            llantas_posicion = llantas.filter(posicion=posicion["posicion"], numero_economico__in=llantas_limpias)
            inspecciones_posicion = Inspeccion.objects.filter(llanta__in=llantas_posicion)
            if inspecciones_posicion.exists():
                regresion_posicion = functions.km_proyectado(inspecciones_posicion, False)
                km_proyectado_posicion = regresion_posicion[0]
                km_x_mm_posicion = regresion_posicion[1]
                cpk_posicion = regresion_posicion[2]
                cantidad = llantas_posicion.count()

                valores_posicion.append(km_proyectado_posicion)
                valores_posicion.append(km_x_mm_posicion)
                valores_posicion.append(cpk_posicion)
                valores_posicion.append(cantidad)
                
                comparativa_de_posiciones[posicion["posicion"]] = valores_posicion

        cpk_vehiculos =  functions.cpk_vehiculo_cantidad(cpk_vehiculos)
        cpk_flotas =  functions.distribucion_cantidad(cpk_flotas)
        cpk_aplicaciones =  functions.distribucion_cantidad(cpk_aplicaciones)
        cpk_productos =  functions.distribucion_cantidad(cpk_productos)

        km_flotas =  functions.distribucion_cantidad(km_flotas)
        km_aplicaciones = functions.distribucion_cantidad(km_aplicaciones)
        km_productos = functions.distribucion_cantidad(km_productos)

        try:
            tendencia_cpk_mes2 = TendenciaCPK.objects.get(compania=Compania.objects.get(compania=self.request.user.perfil.compania), mes=2)
        except:
            tendencia_cpk_mes2 = 0
        try:
            tendencia_cpk_mes3 = TendenciaCPK.objects.get(compania=Compania.objects.get(compania=self.request.user.perfil.compania), mes=3)
        except:
            tendencia_cpk_mes3 = 0
        try:
            tendencia_cpk_mes4 = TendenciaCPK.objects.get(compania=Compania.objects.get(compania=self.request.user.perfil.compania), mes=4)
        except:
            tendencia_cpk_mes4 = 0
        try:
            tendencia_cpk_mes5 = TendenciaCPK.objects.get(compania=Compania.objects.get(compania=self.request.user.perfil.compania), mes=5)
        except:
            tendencia_cpk_mes5 = 0
        try:
            tendencia_cpk_mes6 = TendenciaCPK.objects.get(compania=Compania.objects.get(compania=self.request.user.perfil.compania), mes=6)
        except:
            tendencia_cpk_mes6 = 0
        try:
            tendencia_cpk_mes7 = TendenciaCPK.objects.get(compania=Compania.objects.get(compania=self.request.user.perfil.compania), mes=7)
        except:
            tendencia_cpk_mes7 = 0
        try:
            tendencia_cpk_mes8 = TendenciaCPK.objects.get(compania=Compania.objects.get(compania=self.request.user.perfil.compania), mes=8)
        except:
            tendencia_cpk_mes8 = 0

        print(comparativa_de_productos)
        print(cpk_productos)
        context["aplicacion1"] = aplicacion1
        context["aplicacion2"] = aplicacion2
        context["aplicaciones"] = aplicaciones
        context["clase1"] = clase1
        context["clase2"] = clase2
        context["clases"] = clases
        context["compania"] = str(self.request.user.perfil.compania)
        context["comparativa_de_aplicaciones"] = comparativa_de_aplicaciones
        context["comparativa_de_ejes"] = comparativa_de_ejes
        context["comparativa_de_flotas"] = comparativa_de_flotas
        context["comparativa_de_posiciones"] = comparativa_de_posiciones
        context["comparativa_de_productos"] = comparativa_de_productos
        context["comparativa_de_vehiculos"] = comparativa_de_vehiculos
        context["cpk"] = cpk
        context["cpk_aplicaciones"] = cpk_aplicaciones
        context["cpk_flotas"] = cpk_flotas
        context["cpk_productos"] = cpk_productos
        context["cpk_vehiculos"] = cpk_vehiculos[0]
        context["cpk_vehiculos_cantidad"] = cpk_vehiculos[1]
        context["cpk_vehiculos_cantidad_maxima"] = max(cpk_vehiculos[1])
        context["eje1"] = eje1
        context["eje2"] = eje2
        context["ejes"] = ejes
        context["flota1"] = flota1
        context["flota2"] = flota2
        context["flotas"] = flotas
        context["km_aplicaciones"] = km_aplicaciones
        context["km_flotas"] = km_flotas
        context["km_productos"] = km_productos
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
        context["posicion1"] = posicion1
        context["posicion2"] = posicion2
        context["posiciones"] = posiciones
        context["producto1"] = producto1
        context["producto2"] = producto2
        context["productos"] = productos
        context["tendencia_cpk_mes2"] = tendencia_cpk_mes2
        context["tendencia_cpk_mes3"] = tendencia_cpk_mes3
        context["tendencia_cpk_mes4"] = tendencia_cpk_mes4
        context["tendencia_cpk_mes5"] = tendencia_cpk_mes5
        context["tendencia_cpk_mes6"] = tendencia_cpk_mes6
        context["tendencia_cpk_mes7"] = tendencia_cpk_mes7
        context["tendencia_cpk_mes8"] = tendencia_cpk_mes8
        context["vehiculo1"] = vehiculo1
        context["vehiculo2"] = vehiculo2
        context["vehiculos"] = vehiculos
        return context



class hubView(LoginRequiredMixin, TemplateView):
    # Vista de hubView

    template_name = "hub.html"

class diagramaView(LoginRequiredMixin, TemplateView):
    # Vista de diagramaView
    
    template_name = "diagrama.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        vehiculo = Vehiculo.objects.get(pk = self.kwargs['pk'])
        llantas = Llanta.objects.filter(vehiculo=vehiculo)
        configuracion = vehiculo.configuracion

        cantidad_llantas = functions.cantidad_llantas(configuracion)
        
        context["configuracion"] = configuracion
        
        #Generacion de ejes dinamico
        vehiculo_actual = Vehiculo.objects.get(pk = self.kwargs['pk'])
        llantas_actuales = Llanta.objects.filter(vehiculo = self.kwargs['pk'])
        inspecciones_actuales = Inspeccion.objects.filter(llanta__in=llantas_actuales)
        
        #Obtencion de la lista de las llantas
        
        filtro_sospechoso = functions.vehiculo_sospechoso_llanta(inspecciones_actuales)
        llantas_sospechosas = llantas_actuales.filter(numero_economico__in=filtro_sospechoso)

        filtro_rojo = functions.vehiculo_rojo_llanta(llantas_actuales)
        llantas_rojas = llantas_actuales.filter(numero_economico__in=filtro_rojo).exclude(id__in=llantas_sospechosas)
        
        filtro_amarillo = functions.vehiculo_amarillo_llanta(llantas_actuales)
        llantas_amarillas = llantas_actuales.filter(numero_economico__in=filtro_amarillo).exclude(id__in=llantas_sospechosas).exclude(id__in=llantas_rojas)
        
        llantas_azules = llantas_actuales.exclude(id__in=llantas_sospechosas).exclude(id__in=llantas_rojas).exclude(id__in=llantas_amarillas)
        
        #Obtencion de la data
        num_ejes = vehiculo_actual.configuracion.split('.')
        ejes_no_ordenados = []
        ejes = []
        eje = 1
        color_profundidad = ""
        for num in num_ejes:
            list_temp = []
            for llanta in llantas_actuales:
                if llanta in llantas_sospechosas:
                    color_profundidad = 'purple'
                elif llanta in llantas_rojas:
                    color_profundidad = 'bad'
                elif llanta in llantas_amarillas:
                    color_profundidad = 'yellow'
                elif llanta in llantas_azules:
                    color_profundidad = 'good'
                else:
                    color_profundidad = 'bad'
                if llanta.ultima_inspeccion == None:
                    color_profundidad = 'bad'
                objetivo = llanta.vehiculo.compania.objetivo / 100
                presion_act = llanta.presion_de_salida
                presion_minima = 100 - (100 * objetivo)
                presion_maxima = 100 + (100 * objetivo)
                #print(f'{objetivo}'.center(50, "-"))
                #print(f'{presion_minima}'.center(50, "-"))
                #print(f'{presion_maxima}'.center(50, "-"))
                #print(f'{presion_act}'.center(50, "-"))
                #print(presion_act > presion_minima)
                #print(presion_act < presion_maxima)
                #print('***********************************')
                
                if presion_act > presion_minima and presion_act < presion_maxima:
                    color_presion = 'good'
                else:
                    color_presion = 'bad'
                    
                inspecciones_llanta = Inspeccion.objects.filter(llanta = llanta)
                total_inspecciones = len(inspecciones_llanta)
                
                if llanta.eje == eje:
                    eForm = EdicionManual(instance = llanta)
                    list_temp.append([llanta, color_profundidad, eForm, color_presion, total_inspecciones])
            eje += 1
            ejes_no_ordenados.append(list_temp)
        
        for eje in ejes_no_ordenados:
            if len(eje) == 2:
                lista_temp = ['', '']
                for llanta_act in eje:
                    if 'LI' in llanta_act[0].posicion:
                        lista_temp[0] = llanta_act
                        
                    elif 'RI' in llanta_act[0].posicion:
                        lista_temp[1] = llanta_act
                ejes.append(lista_temp)
                print(' 0---0')
            
            else:
                lista_temp = ['', '', '', '']
                for llanta_act in eje:
                    if 'LO' in llanta_act[0].posicion:
                        lista_temp[0] = llanta_act
                    elif 'LI' in llanta_act[0].posicion:
                        lista_temp[1] = llanta_act
                    elif 'RI' in llanta_act[0].posicion:
                        lista_temp[2] = llanta_act
                    elif 'RO' in llanta_act[0].posicion:
                        lista_temp[3] = llanta_act
                ejes.append(lista_temp)
                print('00---00')
            
            
        color = functions.entrada_correcta(vehiculo_actual)
        #print(color)
        if color == 'good':
            style = 'good'
        elif color == 'bad':
            style = 'bad'
        else:
            style = 'bad'
        
        cant_ejes = len(ejes)
        
        
        #print(vehiculo.configuracion)
        #print(ejes)
        #print(f'style: {style}')
        #print(f'llantas_sospechosas: {llantas_sospechosas}')
        #print(f'llantas_rojas: {llantas_rojas}')
        #print(f'llantas_amarillas: {llantas_amarillas}')
        #print(f'llantas_azules: {llantas_azules}')
        context['ejes'] = ejes
        context['style'] = style
        context['cant_ejes'] = cant_ejes

        return context
    
    def post(self, request, *args, **kwargs):
        #print(request.POST)
        #print(self.kwargs['pk'])
        print('---------------------')
        print('---------------------')
        ids = request.POST.getlist('ids')
        economico = request.POST.getlist('economico')
        producto = request.POST.getlist('producto')
        vida = request.POST.getlist('vida')
        montado = request.POST.getlist('montado')
        reemplazar = request.POST.getlist('reemplazar')
        profundidad = request.POST.getlist('profundidad')
        #print(ids)
        #print(reemplazar)
        #print(economico)
        #print(producto)
        #print(vida)
        #print(montado)
        #print(profundidad)
        estado_vida = ['Nueva', '1R', '2R', '3R', '4R', '5R']
        elementos = 0
        diferencias = []
        id_bitacora = None
        for id_actual in ids:
            if id_actual in reemplazar:
                print(f"Remplazando: {id_actual}".center(50, '-'))
                llanta_por_archivar = Llanta.objects.get(pk = ids[elementos])
                nueva_llanta = Llanta.objects.get(pk = ids[elementos])
                llanta_referencia = Llanta.objects.get(pk = ids[elementos])
                if profundidad[elementos] != '':
                    min_profundidad_referencia = llanta_referencia.ultima_inspeccion.min_profundidad
                #Crear la nueva llanta
                nueva_llanta.id = None
                nueva_llanta.numero_economico = str(economico[elementos])
                
                #Condiciones para que el producto se agrege
                producto_existe = True
                try:
                    producto_act = Producto.objects.get(producto=producto[elementos])
                except:
                    producto_existe = False
                if producto_existe:
                    nueva_llanta.producto = producto_act
                    
                #Condiciones para que la vida se agrege
                if vida[elementos] in estado_vida:
                    nueva_llanta.vida = vida[elementos]
                
                #Condicione para que el km se agrege
                try:
                    if montado[elementos] == '':
                        nueva_llanta.km_montado = None
                    else:
                        nueva_llanta.km_montado = int(float(montado[elementos]))
                except:
                    pass
                
                if nueva_llanta.ultima_inspeccion == None:
                    nueva_llanta.save()
                    llanta_por_archivar.numero_economico = f"{llanta_por_archivar.numero_economico} - Archivado - {llanta_por_archivar.id}"
                    llanta_por_archivar.vehiculo = None
                    llanta_por_archivar.archivado = True
                    llanta_por_archivar.save()
                else:
                    #Cambio de la profundidad
                    #nueva_llanta.ultima_inspeccion.min_profundidad = int(float(profundidad[elementos]))
                    nueva_inspeccion = nueva_llanta.ultima_inspeccion
                    nueva_inspeccion.id = None
                    nueva_inspeccion.min_profundidad = int(float(profundidad[elementos]))
                    nueva_inspeccion.save()
                    nueva_llanta.ultima_inspeccion = nueva_inspeccion
                    nueva_llanta.save()
                    nueva_inspeccion.llanta = nueva_llanta
                    nueva_inspeccion.save()
                    nueva_llanta.ultima_inspeccion = nueva_inspeccion
                    nueva_llanta.save()
                    #Archivar la llanta antigua
                    llanta_por_archivar.numero_economico = f"{llanta_por_archivar.numero_economico} - Archivado - {llanta_por_archivar.id}"
                    llanta_por_archivar.vehiculo = None
                    llanta_por_archivar.archivado = True
                    llanta_por_archivar.save()
                
                #Bitacora
                diferencias = []
                if nueva_llanta.numero_economico != llanta_referencia.numero_economico:
                    diferencias.append(f'Llanta: {nueva_llanta.posicion} se modifico su numero economico de {llanta_referencia.numero_economico} a {nueva_llanta.numero_economico}')
                if nueva_llanta.producto != llanta_referencia.producto:
                    diferencias.append(f'Llanta: {nueva_llanta.posicion} se modifico el producto de {llanta_referencia.producto} a {nueva_llanta.producto}')
                if nueva_llanta.km_montado != llanta_referencia.km_montado:
                    diferencias.append(f'Llanta: {nueva_llanta.posicion} se modifico su km de montado de {llanta_referencia.km_montado} a {nueva_llanta.km_montado}')
                if profundidad[elementos] != '':
                    if nueva_llanta.ultima_inspeccion.min_profundidad != min_profundidad_referencia:
                        diferencias.append(f'Llanta: {nueva_llanta.posicion} se modifico su minima profundidad de {min_profundidad_referencia} a {nueva_llanta.ultima_inspeccion.min_profundidad}')    
                
                print(diferencias)
                
                bitacora_cambios = Bitacora_Edicion(pk=nueva_llanta)
                
            else:
                #print(f"Actualizando: {id_actual}".center(50, '-'))
                llanta = Llanta.objects.get(pk = ids[elementos])
                llanta_referencia = Llanta.objects.get(pk = ids[elementos])
                if profundidad[elementos] != '':
                    min_profundidad_referencia = llanta_referencia.ultima_inspeccion.min_profundidad
                
                #Cambio del numero economico
                llanta.numero_economico = str(economico[elementos])
                #Condiciones para que el producto se agrege
                producto_existe = True
                try:
                    producto_act = Producto.objects.get(producto=producto[elementos])
                except:
                    producto_existe = False
                if producto_existe:
                    llanta.producto = producto_act
                    
                #Condiciones para que la vida se agrege
                if vida[elementos] in estado_vida:
                    llanta.vida = vida[elementos]
                
                #Condicione para que el km se agrege
                try:
                    if montado[elementos] == '':
                        llanta.km_montado = None
                    else:
                        llanta.km_montado = int(float(montado[elementos]))
                except:
                    pass
                
                #Cambio de la profundidad
                if profundidad[elementos] == '':
                    llanta.save()
                else:
                    llanta.ultima_inspeccion.min_profundidad = int(float(profundidad[elementos]))
                    
                    llanta.save()
                    llanta.ultima_inspeccion.save()
                
                #Bitacora
                #diferencias = []
                if llanta.numero_economico != llanta_referencia.numero_economico:
                    diferencias.append(f'Llanta: {llanta.posicion} se modifico su numero economico de {llanta_referencia.numero_economico} a {llanta.numero_economico}')
                if llanta.producto != llanta_referencia.producto:
                    diferencias.append(f'Llanta: {llanta.posicion} se modifico el producto de {llanta_referencia.producto} a {llanta.producto}')
                if llanta.km_montado != llanta_referencia.km_montado:
                    diferencias.append(f'Llanta: {llanta.posicion} se modifico su km de montado de {llanta_referencia.km_montado} a {llanta.km_montado}')
                if profundidad[elementos] != '':
                    if llanta.ultima_inspeccion.min_profundidad != min_profundidad_referencia:
                        diferencias.append(f'Llanta: {llanta.posicion} se modifico su minima profundidad de {min_profundidad_referencia} a {llanta.ultima_inspeccion.min_profundidad}')    
                        
            elementos += 1
            
        #CREACION DE BITACORA
        print(diferencias)
        if len(diferencias) > 0:
            if id_bitacora == None:
                bitacora_cambios = Bitacora_Edicion.objects.create(
                    vehiculo = llanta.vehiculo,
                    tipo = 'edicion'
                    )
                bitacora_cambios.save()
                id_bitacora = bitacora_cambios.id
                
            else:
                try:
                    bitacora_cambios = Bitacora_Edicion.objects.get(pk = id_bitacora)
                except:
                    pass
            
            for diferencia in diferencias:
                registro = Registro_Bitacora.objects.create(
                    bitacora = bitacora_cambios,
                    evento = diferencia
                )
                registro.save()
                        
            
        return redirect('dashboards:diagrama', self.kwargs['pk'])
class tireDiagramaView(LoginRequiredMixin, TemplateView):
    # Vista de tireDiagramaView

    template_name = "tireDiagrama.html"

class ParametroExtractoView(LoginRequiredMixin, TemplateView):
    # Vista de ParametrosExtractoView

    template_name = "parametrosExtracto.html"

class SiteMenuView(LoginRequiredMixin, TemplateView):
    # Vista de SiteMenuView

    template_name = "siteMenu.html"


class catalogoProductoView(LoginRequiredMixin, CreateView):
    # Vista de catalogoProductosView

    template_name = "catalogoProducto.html"
    form_class = ProductoForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        productos = Producto.objects.all()[::-1]
        context["productos"] = productos

        return context
    
    def get_success_url(self):
        return reverse_lazy("dashboards:catalogoProductos")

class catalogoProductoEditView(LoginRequiredMixin, DetailView, UpdateView):
    # Vista de catalogoProductoEditView

    template_name = "catalogoProducto.html"
    slug_field = "producto"
    slug_url_kwarg = "producto"
    queryset = Producto.objects.all()
    context_object_name = "producto"
    model = Producto
    fields = ["id", "producto", 'marca', 'dibujo', 'rango', 'dimension', 'profundidad_inicial', 'aplicacion', 'vida', 'precio', 'km_esperado']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        productos = Producto.objects.all()[::-1]
        context["productos"] = productos

        return context

    def get_success_url(self):
        return reverse_lazy("dashboards:catalogoProductos")

def catalogoProductoDeleteView(request):
    if request.method =="POST":
        producto = Producto.objects.get(id=request.POST.get("id"))
        producto.delete()
        return redirect("dashboards:catalogoProductos")
    return redirect("dashboards:catalogoProductos")


class catalogoRenovadoresView(LoginRequiredMixin, CreateView):
    # Vista de catalogoRenovadoresView

    template_name = "catalogoRenovadores.html"
    form_class = RenovadorForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        compania = Compania.objects.get(compania=self.request.user.perfil.compania)
        renovadores = Renovador.objects.all()[::-1]
        context["renovadores"] = renovadores
        context["compania"] = compania

        return context
    
    def get_success_url(self):
        return reverse_lazy("dashboards:catalogoRenovadores")

class catalogoRenovadoresEditView(LoginRequiredMixin, DetailView, UpdateView):
    # Vista de catalogoRenovadoresEditView

    template_name = "catalogoRenovadores.html"
    slug_field = "renovador"
    slug_url_kwarg = "renovador"
    queryset = Renovador.objects.all()
    context_object_name = "renovador"
    model = Renovador
    fields = ["id", "nombre", 'ciudad', 'marca']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compania = Compania.objects.get(compania=self.request.user.perfil.compania)
        renovadores = Renovador.objects.all()[::-1]
        context["renovadores"] = renovadores
        context["compania"] = compania

        return context

    def get_success_url(self):
        return reverse_lazy("dashboards:catalogoRenovadores")

def catalogoRenovadoresDeleteView(request):
    if request.method =="POST":
        renovador = Renovador.objects.get(id=request.POST.get("id"))
        renovador.delete()
        return redirect("dashboards:catalogoRenovadores")
    return redirect("dashboards:catalogoRenovadores")

class catalogoDesechosView(LoginRequiredMixin, CreateView):
    # Vista de catalogoDesechosView

    template_name = "catalogoDesechos.html"
    form_class = DesechoForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        desechos = Desecho.objects.all()[::-1]
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        context["desechos"] = desechos
        context["llantas"] = llantas

        return context
    
    def get_success_url(self):
        return reverse_lazy("dashboards:catalogoDesechos")

class catalogoDesechosEditView(LoginRequiredMixin, DetailView, UpdateView):
    # Vista de catalogoDesechosEditView

    template_name = "catalogoDesechos.html"
    slug_field = "desecho"
    slug_url_kwarg = "desecho"
    queryset = Desecho.objects.all()
    context_object_name = "desecho"
    form_class = DesechoEditForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        desechos = Desecho.objects.all()[::-1]
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        context["desechos"] = desechos
        context["llantas"] = llantas

        return context

    def get_success_url(self):
        return reverse_lazy("dashboards:catalogoDesechos")

def catalogoDesechosDeleteView(request):
    if request.method =="POST":
        desecho = Desecho.objects.get(id=request.POST.get("id"))
        desecho.delete()
        return redirect("dashboards:catalogoDesechos")
    return redirect("dashboards:catalogoDesechos")


class catalogoObservacionesView(LoginRequiredMixin, CreateView):
    # Vista de catalogoObservacionesView

    template_name = "catalogoObservaciones.html"
    form_class = ObservacionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        observaciones = Observacion.objects.all()[::-1]
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        context["observaciones"] = observaciones
        context["llantas"] = llantas

        return context
    
    def get_success_url(self):
        return reverse_lazy("dashboards:catalogoObservaciones")

class catalogoObservacionesEditView(LoginRequiredMixin, DetailView, UpdateView):
    # Vista de catalogoObservacionesEditView

    template_name = "catalogoObservaciones.html"
    slug_field = "observacion"
    slug_url_kwarg = "observacion"
    queryset = Observacion.objects.all()
    context_object_name = "observacion"
    form_class = ObservacionEditForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        observaciones = Observacion.objects.all()[::-1]
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        context["observaciones"] = observaciones
        context["llantas"] = llantas

        return context

    def get_success_url(self):
        return reverse_lazy("dashboards:catalogoObservaciones")

def catalogoObservacionesDeleteView(request):
    if request.method =="POST":
        observacion = Observacion.objects.get(id=request.POST.get("id"))
        observacion.delete()
        return redirect("dashboards:catalogoObservaciones")
    return redirect("dashboards:catalogoObservaciones")

class catalogoRechazosView(LoginRequiredMixin, CreateView):
    # Vista de catalogoRechazosView

    template_name = "catalogoRechazo.html"
    form_class = RechazoForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        rechazos = Rechazo.objects.all()[::-1]
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        context["rechazos"] = rechazos
        context["llantas"] = llantas

        return context
    
    def get_success_url(self):
        return reverse_lazy("dashboards:catalogoRechazos")

class catalogoRechazosEditView(LoginRequiredMixin, DetailView, UpdateView):
    # Vista de catalogoRechazosEditView

    template_name = "catalogoRechazo.html"
    slug_field = "rechazo"
    slug_url_kwarg = "rechazo"
    queryset = Rechazo.objects.all()
    context_object_name = "rechazo"
    form_class = RechazoEditForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rechazos = Rechazo.objects.all()[::-1]
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        context["rechazos"] = rechazos
        context["llantas"] = llantas

        return context

    def get_success_url(self):
        return reverse_lazy("dashboards:catalogoRechazos")

def catalogoRechazosDeleteView(request):
    if request.method =="POST":
        rechazo = Rechazo.objects.get(id=request.POST.get("id"))
        rechazo.delete()
        return redirect("dashboards:catalogoRechazos")
    return redirect("dashboards:catalogoRechazos")

class companyFormularioView(LoginRequiredMixin, CreateView):
    # Vista de companyFormularioView

    template_name = "formularios/company.html"
    model = Compania
    fields = ["compania", "periodo1_inflado", "periodo2_inflado", "objetivo", "periodo1_inspeccion", "periodo2_inspeccion", "punto_retiro_eje_direccion", "punto_retiro_eje_traccion", "punto_retiro_eje_arrastre", "punto_retiro_eje_loco", "punto_retiro_eje_retractil", "mm_de_desgaste_irregular", "mm_de_diferencia_entre_duales", "mm_parametro_sospechoso", "unidades_presion", "unidades_distancia", "unidades_profundidad", "valor_casco_nuevo", "valor_casco_1r", "valor_casco_2r", "valor_casco_3r", "valor_casco_4r", "valor_casco_5r"]

    def get_success_url(self):
        return reverse_lazy("dashboards:config")

class sucursalFormularioView(LoginRequiredMixin, CreateView):
    # Vista de sucursalFormularioView

    template_name = "formularios/sucursal.html"
    form_class = SucursalForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companias = Compania.objects.all()

        context["companias"] = companias
        return context

    def get_success_url(self):
        return reverse_lazy("dashboards:config")

class tallerFormularioView(LoginRequiredMixin, CreateView):
    # Vista de tallerFormularioView

    template_name = "formularios/taller.html"
    form_class = TallerForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companias = Compania.objects.all()

        context["companias"] = companias
        return context

    def get_success_url(self):
        return reverse_lazy("dashboards:config")

class usuarioFormularioView(LoginRequiredMixin, CreateView):
    # Vista de usuarioFormularioView

    template_name = "formularios/usuario.html"
    form_class = UsuarioForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companias = Compania.objects.all()
        ubicaciones = Ubicacion.objects.all()
        aplicaciones = Aplicacion.objects.all()
        context["aplicaciones"] = aplicaciones
        context["companias"] = companias
        context["sucursales"] = ubicaciones
        return context

    def form_valid(self, form):
        # Save form data
        c = {'form': form, }
        user = form.save(commit=False)
        groups = form.cleaned_data['groups']
        groups = Group.objects.get(name=groups)
        compania = form.cleaned_data['compania']
        compania = Compania.objects.get(compania=compania)
        ubicacion = form.cleaned_data['ubicacion']
        ubicacion = Ubicacion.objects.get(nombre=ubicacion)
        aplicacion = form.cleaned_data['aplicacion']
        aplicacion = Aplicacion.objects.get(nombre=aplicacion)
        password = form.cleaned_data['password']
        repeat_password = form.cleaned_data['repeat_password']
        if password != repeat_password:
            messages.error(self.request, "Passwords do not Match", extra_tags='alert alert-danger')
            return render(self.request, self.template_name, c)
        user.set_password(password)
        user.save()
        
        Perfil.objects.create(user=user, compania=compania, ubicacion=ubicacion, aplicacion=aplicacion)
        user.groups.add(groups)
        
        return super(usuarioFormularioView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dashboards:config")

class aplicacionFormularioView(LoginRequiredMixin, CreateView):
    # Vista de aplicacionFormularioView

    template_name = "formularios/aplicacion.html"
    form_class = AplicacionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companias = Compania.objects.all()
        ubicaciones = Ubicacion.objects.all()

        context["companias"] = companias
        context["sucursales"] = ubicaciones
        return context

    def get_success_url(self):
        return reverse_lazy("dashboards:config")

class perdidaRendimientoView(LoginRequiredMixin, TemplateView):
# Vista de perdidaRendimientoView

    template_name = "informes/perdida-rendimiento.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        compania = Compania.objects.get(compania=self.request.user.perfil.compania)
        ubicaciones = Ubicacion.objects.filter(compania=compania)
        aplicaciones = Aplicacion.objects.filter(compania=compania)
        
        context["aplicaciones"] = aplicaciones
        context["compania"] = compania
        context["sucursales"] = ubicaciones
        return context

class inspeccionVehiculo(LoginRequiredMixin, TemplateView):
    # Vista de inspeccionVehiculo

    template_name = "inspeccion-vehiculo.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

#Generacion de ejes dinamico
        vehiculo_actual = Vehiculo.objects.get(pk = self.kwargs['pk'])
        llantas_actuales = Llanta.objects.filter(vehiculo = self.kwargs['pk'])
        inspecciones_actuales = Inspeccion.objects.filter(llanta__in=llantas_actuales)
        
        #Obtencion de la lista de las llantas
        
        filtro_sospechoso = functions.vehiculo_sospechoso_llanta(inspecciones_actuales)
        llantas_sospechosas = llantas_actuales.filter(numero_economico__in=filtro_sospechoso)

        filtro_rojo = functions.vehiculo_rojo_llanta(llantas_actuales)
        llantas_rojas = llantas_actuales.filter(numero_economico__in=filtro_rojo).exclude(id__in=llantas_sospechosas)
        
        filtro_amarillo = functions.vehiculo_amarillo_llanta(llantas_actuales)
        llantas_amarillas = llantas_actuales.filter(numero_economico__in=filtro_amarillo).exclude(id__in=llantas_sospechosas).exclude(id__in=llantas_rojas)
        
        llantas_azules = llantas_actuales.exclude(id__in=llantas_sospechosas).exclude(id__in=llantas_rojas).exclude(id__in=llantas_amarillas)
        
        #Obtencion de la data
        num_ejes = vehiculo_actual.configuracion.split('.')
        ejes_no_ordenados = []
        ejes = []
        eje = 1
        color_profundidad = ""
        for num in num_ejes:
            list_temp = []
            for llanta in llantas_actuales:
                if llanta in llantas_sospechosas:
                    color_profundidad = 'purple'
                elif llanta in llantas_rojas:
                    color_profundidad = 'bad'
                elif llanta in llantas_amarillas:
                    color_profundidad = 'yellow'
                elif llanta in llantas_azules:
                    color_profundidad = 'good'
                if llanta.ultima_inspeccion == None:
                    color_profundidad = 'bad'
                    
                objetivo = llanta.vehiculo.compania.objetivo / 100
                presion_act = llanta.presion_de_salida
                presion_minima = 100 - (100 * objetivo)
                presion_maxima = 100 + (100 * objetivo)
                #print(f'{objetivo}'.center(50, "-"))
                #print(f'{presion_minima}'.center(50, "-"))
                #print(f'{presion_maxima}'.center(50, "-"))
                #print(f'{presion_act}'.center(50, "-"))
                #print(presion_act > presion_minima)
                #print(presion_act < presion_maxima)
                #print('***********************************')
                
                if presion_act > presion_minima and presion_act < presion_maxima:
                    color_presion = 'good'
                else:
                    color_presion = 'bad'
                                    
                if llanta.eje == eje:
                    eForm = InspeccionForm(instance = llanta.ultima_inspeccion) 
                    list_temp.append([llanta, color_profundidad, eForm, color_presion])
            eje += 1
            ejes_no_ordenados.append(list_temp)
        
        for eje in ejes_no_ordenados:
            if len(eje) == 2:
                lista_temp = ['', '']
                for llanta_act in eje:
                    if 'LI' in llanta_act[0].posicion:
                        lista_temp[0] = llanta_act
                        
                    elif 'RI' in llanta_act[0].posicion:
                        lista_temp[1] = llanta_act
                ejes.append(lista_temp)
                print(' 0---0')
            
            else:
                lista_temp = ['', '', '', '']
                for llanta_act in eje:
                    if 'LO' in llanta_act[0].posicion:
                        lista_temp[0] = llanta_act
                    elif 'LI' in llanta_act[0].posicion:
                        lista_temp[1] = llanta_act
                    elif 'RI' in llanta_act[0].posicion:
                        lista_temp[2] = llanta_act
                    elif 'RO' in llanta_act[0].posicion:
                        lista_temp[3] = llanta_act
                ejes.append(lista_temp)
                print('00---00')
            
            
        color = functions.entrada_correcta(vehiculo_actual)
        #print(color)
        if color == 'good':
            style = 'good'
        elif color == 'bad':
            style = 'bad'
        else:
            style = 'bad'
        
        cant_ejes = len(ejes)
        
        
        #print(vehiculo.configuracion)
        #print(ejes)
        #print(f'style: {style}')
        #print(f'llantas_sospechosas: {llantas_sospechosas}')
        #print(f'llantas_rojas: {llantas_rojas}')
        #print(f'llantas_amarillas: {llantas_amarillas}')
        #print(f'llantas_azules: {llantas_azules}')
        context['ejes'] = ejes
        context['style'] = style
        context['cant_ejes'] = cant_ejes

        return context
    
    def post(self, request, *args, **kwargs):
        #print(request.POST)
        print(self.kwargs['pk'])
        print('---------------------')
        print('---------------------')
        ids = request.POST.getlist('ids')
        llanta = request.POST.getlist('llanta')
        km = request.POST.getlist('km')
        min_profundidad = request.POST.getlist('min_profundidad')
        observacion_1 = request.POST.getlist('observacion_1')
        observacion_2 = request.POST.getlist('observacion_2')
        observacion_3 = request.POST.getlist('observacion_3')
        reemplazar = request.POST.getlist('reemplazar')
        print(ids)
        print(reemplazar)
        print(llanta)
        print(km)
        print(min_profundidad)
        print(observacion_1)
        print(observacion_2)
        print(observacion_3)
        elementos = 0
        for id_actual in ids:
            if id_actual in reemplazar:
                print(f"Remplazando: {id_actual}".center(50, '-'))                
            else:
                print(f"Actualizando: {id_actual}".center(50, '-'))
                llanta_act = Llanta.objects.get(pk = ids[elementos])
                print(llanta_act.ultima_inspeccion)
                inspeccion_act = llanta_act.ultima_inspeccion
                inspeccion_act.km = int(float(km[elementos]))
                inspeccion_act.min_profundidad = int(float(min_profundidad[elementos]))
                if observacion_1[elementos] == "":
                    inspeccion_act.observacion_1 = None
                else:
                    inspeccion_act.observacion_1 = observacion_1[elementos]
                    
                if observacion_2[elementos] == "":
                    inspeccion_act.observacion_2 = None
                else:
                    inspeccion_act.observacion_2 = observacion_2[elementos]
                    
                if observacion_3[elementos] == "":
                    inspeccion_act.observacion_3 = None
                else:
                    inspeccion_act.observacion_3 = observacion_3[elementos]
                print(str(inspeccion_act.llanta))
                print(str(llanta[elementos]))
                print(str(inspeccion_act.llanta) != str(llanta[elementos]))
                if str(inspeccion_act.llanta) != str(llanta[elementos]):
                    try:
                        llanta_asignada = Llanta.objects.get(numero_economico = str(llanta[elementos]))
                        inspeccion_act.llanta = llanta_asignada
                        llanta_act.ultima_inspeccion = None
                        llanta_act.save()
                    except:
                        pass
                
                inspeccion_act.save()
                #llanta.ultima_inspeccion.save()
            elementos += 1
        return redirect('dashboards:inspeccionVehiculo', self.kwargs['pk'])

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
        vehiculo = bitacora.numero_economico
        llantas = Llanta.objects.filter(vehiculo = vehiculo)
        
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
          
          
        #Obtencion de la data
        num_ejes = vehiculo.configuracion.split('.')
        ejes = []
        eje = 1
        for num in num_ejes:
            list_temp = []
            for llanta in llantas:
                #print(llanta.eje)
                if llanta.eje == eje:
                    list_temp.append(llanta)
            eje += 1
            ejes.append(list_temp)
            list_temp = []
            
        #print(ejes)       

        context["color1"] = color1
        context["color2"] = color2
        context["hoy"] = hoy
        context["user"] = user
        context["signo1"] = signo1
        context["signo2"] = signo2
        context['ejes'] = ejes
        return context

class reporteLlantaView(LoginRequiredMixin, DetailView):
    # Vista de reporteLlantaView

    template_name = "reporteLlanta.html"
    slug_field = "bitacora"
    slug_url_kwarg = "bitacora"
    queryset = Bitacora.objects.all()
    context_object_name = "bitacora"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        bitacora = Bitacora.objects.get(id=self.kwargs['pk'])
        llanta = Llanta.objects.get(id=self.kwargs['llanta'])
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
        context["llanta"] = llanta
        context["user"] = user
        context["signo1"] = signo1
        context["signo2"] = signo2
        return context

class configuracionVehiculoView(LoginRequiredMixin, TemplateView):
    # Vista de configuracionVehiculoView

    template_name = "configuracionVehiculo.html" 
    
    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        #Declaracion de variables
        
        #Generacion de ejes dinamico
        vehiculo_actual = Vehiculo.objects.get(pk = self.kwargs['pk'])
        llantas_actuales = Llanta.objects.filter(vehiculo = self.kwargs['pk'])
        inspecciones_actuales = Inspeccion.objects.filter(llanta__in=llantas_actuales)
        
        #Obtencion de la lista de las llantas
        
        filtro_sospechoso = functions.vehiculo_sospechoso_llanta(inspecciones_actuales)
        llantas_sospechosas = llantas_actuales.filter(numero_economico__in=filtro_sospechoso)

        filtro_rojo = functions.vehiculo_rojo_llanta(llantas_actuales)
        llantas_rojas = llantas_actuales.filter(numero_economico__in=filtro_rojo).exclude(id__in=llantas_sospechosas)
        
        filtro_amarillo = functions.vehiculo_amarillo_llanta(llantas_actuales)
        llantas_amarillas = llantas_actuales.filter(numero_economico__in=filtro_amarillo).exclude(id__in=llantas_sospechosas).exclude(id__in=llantas_rojas)
        
        llantas_azules = llantas_actuales.exclude(id__in=llantas_sospechosas).exclude(id__in=llantas_rojas).exclude(id__in=llantas_amarillas)
        
        #Obtencion de la data
        num_ejes = vehiculo_actual.configuracion.split('.')
        ejes_no_ordenados = []
        ejes = []
        eje = 1
        color_profundidad = ""
        for num in num_ejes:
            list_temp = []
            for llanta in llantas_actuales:
                if llanta in llantas_sospechosas:
                    color_profundidad = 'purple'
                elif llanta in llantas_rojas:
                    color_profundidad = 'bad'
                elif llanta in llantas_amarillas:
                    color_profundidad = 'yellow'
                elif llanta in llantas_azules:
                    color_profundidad = 'good'
                if llanta.ultima_inspeccion == None:
                    color_profundidad = 'bad'
                
                objetivo = llanta.vehiculo.compania.objetivo / 100
                presion_act = llanta.presion_de_salida
                presion_minima = 100 - (100 * objetivo)
                presion_maxima = 100 + (100 * objetivo)
                #print(f'{objetivo}'.center(50, "-"))
                #print(f'{presion_minima}'.center(50, "-"))
                #print(f'{presion_maxima}'.center(50, "-"))
                #print(f'{presion_act}'.center(50, "-"))
                #print(presion_act > presion_minima)
                #print(presion_act < presion_maxima)
                #print('***********************************')
                
                if presion_act > presion_minima and presion_act < presion_maxima:
                    color_presion = 'good'
                else:
                    color_presion = 'bad'
                
                if llanta.eje == eje:
                    list_temp.append([llanta, color_profundidad, color_presion])
            eje += 1
            ejes_no_ordenados.append(list_temp)
        
        for eje in ejes_no_ordenados:
            if len(eje) == 2:
                lista_temp = ['', '']
                for llanta_act in eje:
                    if 'LI' in llanta_act[0].posicion:
                        lista_temp[0] = llanta_act
                        
                    elif 'RI' in llanta_act[0].posicion:
                        lista_temp[1] = llanta_act
                ejes.append(lista_temp)
                print(' 0---0')
            
            else:
                lista_temp = ['', '', '', '']
                for llanta_act in eje:
                    if 'LO' in llanta_act[0].posicion:
                        lista_temp[0] = llanta_act
                    elif 'LI' in llanta_act[0].posicion:
                        lista_temp[1] = llanta_act
                    elif 'RI' in llanta_act[0].posicion:
                        lista_temp[2] = llanta_act
                    elif 'RO' in llanta_act[0].posicion:
                        lista_temp[3] = llanta_act
                ejes.append(lista_temp)
                print('00---00')
            
            
        color = functions.entrada_correcta(vehiculo_actual)
        #print(color)
        if color == 'good':
            style = 'good'
        elif color == 'bad':
            style = 'bad'
        else:
            style = 'bad'
        
        cant_ejes = len(ejes)
        
        
        #print(vehiculo.configuracion)
        #print(ejes)
        #print(f'style: {style}')
        #print(f'llantas_sospechosas: {llantas_sospechosas}')
        #print(f'llantas_rojas: {llantas_rojas}')
        #print(f'llantas_amarillas: {llantas_amarillas}')
        #print(f'llantas_azules: {llantas_azules}')
        context['ejes'] = ejes
        context['style'] = style
        context['cant_ejes'] = cant_ejes
        
        
        return context

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
        print("jd['presiones_de_entrada']", jd['presiones_de_entrada'])
        presiones_de_entrada = eval(jd['presiones_de_entrada'])
        presiones_de_salida = eval(jd['presiones_de_salida'])
        print("presiones_de_entrada", presiones_de_entrada)
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
    
            vehiculo.ultima_bitacora_pro= bi
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
        bitacora_pro = Bitacora_Pro.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        hoy = date.today()

        #functions_create.crear_de_bitacora_el_vehiculo()
        #functions_create.crear_clase_en_vehiculo()
        #functions_create.crear_configuracion()
        #functions_excel.excel_vehiculos2()
        #functions_ftp.ftp()
        #functions_ftp.ftp_1()
        #functions_ftp.ftp2(self.request.user.perfil)
        ultimo_mes = hoy - timedelta(days=31)

        #functions_create.tirecheck_llanta()
        #functions_create.borrar_ultima_inspeccion_vehiculo()
        #functions_excel.excel_vehiculos()
        #functions_excel.excel_llantas(User.objects.get(username="equipo-logistico"))
        #functions_excel.excel_inspecciones()

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

        vehiculo_fecha = vehiculo.filter(fecha_de_inflado__range=[ultimo_mes, hoy]) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__range=[ultimo_mes, hoy])
        vehiculo_fecha_barras_1 = vehiculo.filter(fecha_de_inflado__month=hoy1) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__month=hoy1)
        vehiculo_fecha_barras_2 = vehiculo.filter(fecha_de_inflado__month=hoy2) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__month=hoy2)
        vehiculo_fecha_barras_3 = vehiculo.filter(fecha_de_inflado__month=hoy3) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__month=hoy3)
        vehiculo_fecha_barras_4 = vehiculo.filter(fecha_de_inflado__month=hoy4) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__month=hoy4)
        vehiculo_fecha_barras_5 = vehiculo.filter(fecha_de_inflado__month=hoy5) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__month=hoy5)
        
        vehiculo_mes1 = bitacora.filter(fecha_de_inflado__month=hoy1)
        vehiculo_mes2 = bitacora.filter(fecha_de_inflado__month=hoy2)
        vehiculo_mes3 = bitacora.filter(fecha_de_inflado__month=hoy3)
        vehiculo_mes4 = bitacora.filter(fecha_de_inflado__month=hoy4)

        vehiculo_pro_mes1 = bitacora_pro.filter(fecha_de_inflado__month=hoy1)
        vehiculo_pro_mes2 = bitacora_pro.filter(fecha_de_inflado__month=hoy2)
        vehiculo_pro_mes3 = bitacora_pro.filter(fecha_de_inflado__month=hoy3)
        vehiculo_pro_mes4 = bitacora_pro.filter(fecha_de_inflado__month=hoy4)

        entrada_correcta_contar = functions.contar_entrada_correcta(vehiculo_fecha)
        mala_entrada_contar_mes1 = functions.contar_mala_entrada(vehiculo_mes1)
        mala_entrada_contar_mes2 = functions.contar_mala_entrada(vehiculo_mes2)
        mala_entrada_contar_mes3 = functions.contar_mala_entrada(vehiculo_mes3)
        mala_entrada_contar_mes4 = functions.contar_mala_entrada(vehiculo_mes4)

        mala_entrada_contar_mes1 += functions.contar_mala_entrada(vehiculo_pro_mes1)
        mala_entrada_contar_mes2 += functions.contar_mala_entrada(vehiculo_pro_mes2)
        mala_entrada_contar_mes3 += functions.contar_mala_entrada(vehiculo_pro_mes3)
        mala_entrada_contar_mes4 += functions.contar_mala_entrada(vehiculo_pro_mes4)


        entrada_correcta_contar_barras_mes1 = functions.contar_entrada_correcta(vehiculo_fecha_barras_1)
        entrada_correcta_contar_barras_mes2 = functions.contar_entrada_correcta(vehiculo_fecha_barras_2)
        entrada_correcta_contar_barras_mes3 = functions.contar_entrada_correcta(vehiculo_fecha_barras_3)
        entrada_correcta_contar_barras_mes4 = functions.contar_entrada_correcta(vehiculo_fecha_barras_4)
        entrada_correcta_contar_barras_mes5 = functions.contar_entrada_correcta(vehiculo_fecha_barras_5)


        doble_entrada = functions.doble_entrada(bitacora) 
        doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculo)

        doble_entrada_pro = functions.doble_entrada_pro(bitacora_pro) 
        doble_mala_entrada_pro = functions.doble_mala_entrada_pro(bitacora_pro, vehiculo)

        print(doble_entrada)
        print(doble_mala_entrada)

        vehiculo_periodo = vehiculo.filter(fecha_de_inflado__lte=ultimo_mes) | vehiculo.filter(fecha_de_inflado=None) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__lte=ultimo_mes)
        vehiculo_periodo_status = {}
        mala_entrada_periodo = functions.mala_entrada(vehiculo_periodo) | functions.mala_entrada_pro(vehiculo_periodo)
        for v in vehiculo_periodo:
            if v in doble_mala_entrada or v in doble_mala_entrada_pro:
                vehiculo_periodo_status[v] = "Doble Entrada"
            elif v in mala_entrada_periodo:
                vehiculo_periodo_status[v] = "Mala Entrada"
            else:
                vehiculo_periodo_status[v] = "Entrada Correctas"

        vehiculo_malos_status = {}
        mala_entrada = functions.mala_entrada(vehiculo) | functions.mala_entrada_pro(vehiculo)
        for v in vehiculo:
            if v in doble_mala_entrada or v in doble_mala_entrada_pro:
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
        context["bitacoras_pro"] = bitacora_pro
        context["boton_intuitivo"] = "Vehículos Vencidos"
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
        context["doble_entrada"] = doble_entrada
        context["doble_entrada_pro"] = doble_entrada_pro
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
        context["vehiculos_malos"] = vehiculo_malos_status
        context["vehiculos_periodo"] = vehiculo_periodo_status
        context["vehiculos_todos"] = vehiculo
        functions_ftp.ftp_descarga()
        return context


def buscar(request):
    # Busca por fecha, localidad o clase
    
    my_profile = Perfil.objects.get(user=request.user)
    vehiculo = Vehiculo.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
    vehiculos_totales = Vehiculo.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
    bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
    bitacora_pro = Bitacora_Pro.objects.filter(compania=Compania.objects.get(compania= request.user.perfil.compania))
    hoy = date.today()
    ultimo_mes = hoy - timedelta(days=31)
    clase1 = request.GET.getlist("clase")
    flota1 = request.GET.getlist("flota")
    fecha1 = request.GET.get("fechaInicio")
    fecha2 = request.GET.get("fechaFin")
    boton_intuitivo = request.GET.get("boton_intuitivo")


    # Buscar por fecha

    fecha_con_formato1 = None
    fecha_con_formato2 = None
    clase = None
    flota = None
    if clase1:
        clase = clase1
        vehiculo = vehiculo.filter(functions.reduce(or_, [Q(clase=c.upper()) for c in clase1]))
    if flota1:
        flota = flota1
        vehiculo = vehiculo.filter(functions.reduce(or_, [Q(ubicacion=Ubicacion.objects.get(nombre=f)) for f in flota1]))

    if flota1:
        flotas_vehiculo = vehiculos_totales.values("ubicacion").distinct()
    else:
        flotas_vehiculo = vehiculo.values("ubicacion").distinct()

    flotas = Ubicacion.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania), id__in=flotas_vehiculo)
    
    if clase1:
        clases = vehiculos_totales.values_list("clase", flat=True).distinct()
    else:
        clases = vehiculo.values_list("clase", flat=True).distinct()
    
    if fecha1 and fecha2:
        fecha1 = functions.convertir_rango(fecha1)
        fecha2 = functions.convertir_rango(fecha2)
        primera_fecha = datetime.strptime(fecha1, "%Y/%m/%d").date()
        segunda_fecha = datetime.strptime(fecha2, "%Y/%m/%d").date()
        # Convertir formato de fecha
        fecha_con_formato1 = functions.convertir_fecha(fecha1)
        fecha_con_formato2 = functions.convertir_fecha(fecha2)

        vehiculo_fecha = vehiculo.filter(fecha_de_inflado__range=[primera_fecha, segunda_fecha]) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__range=[primera_fecha, segunda_fecha])
    else:
        vehiculo_fecha = vehiculo.filter(fecha_de_inflado__range=[ultimo_mes, hoy]) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__range=[ultimo_mes, hoy])
    
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
    
    vehiculo_fecha_barras_1 = vehiculo.filter(fecha_de_inflado__month=hoy1) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__month=hoy1)
    vehiculo_fecha_barras_2 = vehiculo.filter(fecha_de_inflado__month=hoy2) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__month=hoy2)
    vehiculo_fecha_barras_3 = vehiculo.filter(fecha_de_inflado__month=hoy3) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__month=hoy3)
    vehiculo_fecha_barras_4 = vehiculo.filter(fecha_de_inflado__month=hoy4) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__month=hoy4)
    vehiculo_fecha_barras_5 = vehiculo.filter(fecha_de_inflado__month=hoy5) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__month=hoy5)

    vehiculo_mes1 = bitacora.filter(fecha_de_inflado__month=hoy1)
    vehiculo_mes2 = bitacora.filter(fecha_de_inflado__month=hoy2)
    vehiculo_mes3 = bitacora.filter(fecha_de_inflado__month=hoy3)
    vehiculo_mes4 = bitacora.filter(fecha_de_inflado__month=hoy4)

    vehiculo_pro_mes1 = bitacora_pro.filter(fecha_de_inflado__month=hoy1)
    vehiculo_pro_mes2 = bitacora_pro.filter(fecha_de_inflado__month=hoy2)
    vehiculo_pro_mes3 = bitacora_pro.filter(fecha_de_inflado__month=hoy3)
    vehiculo_pro_mes4 = bitacora_pro.filter(fecha_de_inflado__month=hoy4)


    entrada_correcta_contar = functions.contar_entrada_correcta(vehiculo_fecha)
    mala_entrada_contar_mes1 = functions.contar_mala_entrada(vehiculo_mes1)
    mala_entrada_contar_mes2 = functions.contar_mala_entrada(vehiculo_mes2)
    mala_entrada_contar_mes3 = functions.contar_mala_entrada(vehiculo_mes3)
    mala_entrada_contar_mes4 = functions.contar_mala_entrada(vehiculo_mes4)

    mala_entrada_contar_mes1 += functions.contar_mala_entrada(vehiculo_pro_mes1)
    mala_entrada_contar_mes2 += functions.contar_mala_entrada(vehiculo_pro_mes2)
    mala_entrada_contar_mes3 += functions.contar_mala_entrada(vehiculo_pro_mes3)
    mala_entrada_contar_mes4 += functions.contar_mala_entrada(vehiculo_pro_mes4)


    entrada_correcta_contar_barras_mes1 = functions.contar_entrada_correcta(vehiculo_fecha_barras_1)
    entrada_correcta_contar_barras_mes2 = functions.contar_entrada_correcta(vehiculo_fecha_barras_2)
    entrada_correcta_contar_barras_mes3 = functions.contar_entrada_correcta(vehiculo_fecha_barras_3)
    entrada_correcta_contar_barras_mes4 = functions.contar_entrada_correcta(vehiculo_fecha_barras_4)
    entrada_correcta_contar_barras_mes5 = functions.contar_entrada_correcta(vehiculo_fecha_barras_5)


    doble_entrada = functions.doble_entrada(bitacora)
    doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculo)

    doble_entrada_pro = functions.doble_entrada_pro(bitacora_pro) 
    doble_mala_entrada_pro = functions.doble_mala_entrada_pro(bitacora_pro, vehiculo)

    vehiculo_periodo = vehiculo.filter(fecha_de_inflado__lte=ultimo_mes) | vehiculo.filter(fecha_de_inflado=None) | vehiculo.filter(ultima_bitacora_pro__fecha_de_inflado__lte=ultimo_mes)
    vehiculo_periodo_status = {}
    mala_entrada_periodo = functions.mala_entrada(vehiculo_periodo) | functions.mala_entrada_pro(vehiculo_periodo)
    for v in vehiculo_periodo:
        if v in doble_mala_entrada or v in doble_mala_entrada_pro:
            vehiculo_periodo_status[v] = "Doble Entrada"
        elif v in mala_entrada_periodo:
            vehiculo_periodo_status[v] = "Mala Entrada"
        else:
            vehiculo_periodo_status[v] = "Entrada Correctas"

    vehiculo_malos_status = {}
    mala_entrada = functions.mala_entrada(vehiculo) | functions.mala_entrada_pro(vehiculo)
    for v in vehiculo:
        if v in doble_mala_entrada:
            vehiculo_malos_status[v] = "Doble Entrada"
        elif v in mala_entrada:
            vehiculo_malos_status[v] = "Mala Entrada"

    my_profile = Perfil.objects.get(user=request.user)

    radar_min = functions.radar_min(vehiculo_fecha, request.user.perfil.compania)
    radar_max = functions.radar_max(vehiculo_fecha, request.user.perfil.compania)
    radar_min_resta = functions.radar_min_resta(radar_min, radar_max)

    return render(request, "pulpo.html", {
                                        "aplicaciones": Aplicacion.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania)),
                                        "aplicaciones_mas_frecuentes_infladas": functions.aplicaciones_mas_frecuentes(vehiculo_fecha, vehiculo, request.user.perfil.compania),
                                        "bitacoras": bitacora,
                                        "bitacoras_pro": bitacora_pro,
                                        "boton_intuitivo": "Vehículos Vencidos",
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
                                        "cantidad_inflado_1": vehiculo_fecha_barras_1.count(),
                                        "cantidad_inflado_2": vehiculo_fecha_barras_2.count(),
                                        "cantidad_inflado_3": vehiculo_fecha_barras_3.count(),
                                        "cantidad_inflado_4": vehiculo_fecha_barras_4.count(),
                                        "cantidad_inflado_5": vehiculo_fecha_barras_5.count(),
                                        "cantidad_total": vehiculo.count(),
                                        "clase": clase,
                                        "clase1": clase1,
                                        "clases_compania": clases,
                                        "clases_mas_frecuentes_infladas": functions.clases_mas_frecuentes(vehiculo_fecha, request.user.perfil.compania),
                                        "compania": request.user.perfil.compania,
                                        "doble_entrada": doble_entrada,
                                        "doble_entrada_pro": doble_entrada_pro,
                                        "fecha1":fecha1,
                                        "fecha2":fecha2,
                                        "fecha_con_formato1":fecha_con_formato1,
                                        "fecha_con_formato2":fecha_con_formato2,
                                        "flota": flota,
                                        "flota1": flota1,
                                        "flotas": flotas,
                                        "hoy": hoy,
                                        "mes_1": mes_1,
                                        "mes_2": mes_2.strftime("%b"),
                                        "mes_3": mes_3.strftime("%b"),
                                        "mes_4": mes_4.strftime("%b"),
                                        "mes_5": mes_5.strftime("%b"),
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
                                        "vehiculos_malos": vehiculo_malos_status,
                                        "vehiculos_periodo": vehiculo_periodo_status,
                                        "vehiculos_todos": vehiculo
                                    })

class ConfigView(LoginRequiredMixin, MultiModelFormView):
    # Vista del dashboard configuración
    template_name = "config.html"
    form_classes = {"companiaform": CompaniaForm,
                    "usuarioform": UsuarioEditForm,
                    "excelform": ExcelForm}
    success_url = reverse_lazy('dashboards:config')

    """def forms_valid(self, form):
        # Save form data
        user = form.save(commit=False)
        compania_form = forms['companiaform'].save(commit=False)
        groups = form.cleaned_data['groups']
        groups = Group.objects.get(name=groups)
        idioma = form.cleaned_data['idioma']
        user.save()
        
        perfil = Perfil.objects.get(user=user)
        perfil.idioma = idioma
        perfil.save()
        user.groups.add(groups)
        
        return super(ConfigView, self).forms_valid(form)"""

    def get_context_data(self, **kwargs):

        context = super(ConfigView, self).get_context_data(**kwargs)
        user = User.objects.get(username=self.request.user)
        groups_names = Group.objects.all()
        compania = Compania.objects.get(compania=self.request.user.perfil.compania)
        
        if self.request.method=='POST' and 'periodo1_inflado' in self.request.POST:
            compania.periodo1_inflado = self.request.POST.get("periodo1_inflado")
            compania.periodo2_inflado = self.request.POST.get("periodo2_inflado")
            compania.objetivo = self.request.POST.get("objetivo")
            compania.periodo1_inspeccion = self.request.POST.get("periodo1_inspeccion")
            compania.periodo2_inspeccion = self.request.POST.get("periodo2_inspeccion")
            compania.punto_retiro_eje_direccion = self.request.POST.get("punto_retiro_eje_direccion")
            compania.punto_retiro_eje_traccion = self.request.POST.get("punto_retiro_eje_traccion")
            compania.punto_retiro_eje_arrastre = self.request.POST.get("punto_retiro_eje_arrastre")
            compania.mm_de_desgaste_irregular = self.request.POST.get("mm_de_desgaste_irregular")
            compania.mm_de_diferencia_entre_duales = self.request.POST.get("mm_de_diferencia_entre_duales")
            compania.save()
        elif self.request.method=='POST' and 'email' in self.request.POST:
            user.email = self.request.POST.get("email")
            user.username = self.request.POST.get("username")
            user.idioma = self.request.POST.get("idioma")
            groups = Group.objects.get(name=self.request.POST.get("groups"))
            user.groups.clear()
            user.groups.add(groups)
            user.save()
        elif self.request.method=='POST' and self.request.FILES.get("file"):
            file = self.request.FILES.get("file")
            archivo = os.path.abspath(os.getcwd()) + r"\files.xlsx"
            fp = open(archivo,'wb')
            for chunk in file.chunks():
                fp.write(chunk)
  
            wb_obj = openpyxl.load_workbook(archivo)
            sheet_obj = wb_obj.active
            
            for i in range(sheet_obj.max_row):
                numero_economico = sheet_obj.cell(row=i + 2, column=1).value
                try:
                    try:
                        vehiculo = Vehiculo.objects.get(numero_economico=numero_economico, compania=Compania.objects.get(compania=compania))
                    except:
                        modelo = sheet_obj.cell(row=i + 2, column=2).value
                        marca = sheet_obj.cell(row=i + 2, column=3).value
                        ubicacion = sheet_obj.cell(row=i + 2, column=4).value
                        aplicacion = sheet_obj.cell(row=i + 2, column=5).value
                        clase = sheet_obj.cell(row=i + 2, column=6).value
                        configuracion = sheet_obj.cell(row=i + 2, column=7).value
                        presion_establecida = sheet_obj.cell(row=i + 2, column=8).value
                        numero_de_llantas = functions.cantidad_llantas(configuracion)

                        ubicacion = Ubicacion.objects.get(nombre=ubicacion, compania=compania)

                        aplicacion = Aplicacion.objects.get(nombre=aplicacion, compania=compania)

                        Vehiculo.objects.create(numero_economico=numero_economico,
                                            modelo=modelo,
                                            marca=marca,
                                            compania=compania,
                                            ubicacion=ubicacion,
                                            aplicacion=aplicacion,
                                            numero_de_llantas=numero_de_llantas,
                                            clase=clase.upper(),
                                            configuracion=configuracion,
                                            presion_establecida=presion_establecida
                                            )
                except:
                    pass
            fp.close()
            wb_obj.close()
            os.remove(os.path.abspath(archivo))
        elif self.request.method=='POST' and self.request.FILES.get("file2"):
            file = self.request.FILES.get("file2")
            archivo = os.path.abspath(os.getcwd()) + r"\files.xlsx"
            fp = open(archivo,'wb')
            for chunk in file.chunks():
                fp.write(chunk)
  
            wb_obj = openpyxl.load_workbook(archivo)
            sheet_obj = wb_obj.active
            
            for i in range(sheet_obj.max_row):
                numero_economico = str(sheet_obj.cell(row=i + 2, column=1).value)
                try:
                    try:
                        llanta = Llanta.objects.get(numero_economico=numero_economico, compania=Compania.objects.get(compania=compania))
                    except:
                        vehiculo = str(sheet_obj.cell(row=i + 2, column=2).value)
                        ubicacion = str(sheet_obj.cell(row=i + 2, column=3).value)
                        vida = str(sheet_obj.cell(row=i + 2, column=4).value)
                        posicion = str(sheet_obj.cell(row=i + 2, column=5).value)
                        producto = str(sheet_obj.cell(row=i + 2, column=6).value)

                        vehiculo = Vehiculo.objects.get(numero_economico=vehiculo)
                        ubicacion = Ubicacion.objects.get(nombre=ubicacion, compania=compania)
                        tipo_de_eje = vehiculo.configuracion.split(".")[int(posicion[0]) - 1]
                        eje = posicion[0]
                        if tipo_de_eje[0] == "S":
                            nombre_de_eje = "Dirección"
                        elif tipo_de_eje[0] == "D":
                            nombre_de_eje = "Tracción"
                        elif tipo_de_eje[0] == "T":
                            nombre_de_eje = "Arrastre"
                        elif tipo_de_eje[0] == "C":
                            nombre_de_eje = "Loco"
                        elif tipo_de_eje[0] == "L":
                            nombre_de_eje = "Retractil"
                        producto = Producto.objects.get(producto=producto)
                        inventario = "Rodante"

                        Llanta.objects.create(numero_economico=numero_economico,
                                            usuario=user.perfil,
                                            compania=compania,
                                            vehiculo=vehiculo,
                                            ubicacion=ubicacion,
                                            vida=vida,
                                            tipo_de_eje=tipo_de_eje,
                                            eje=int(eje),
                                            posicion=posicion,
                                            presion_establecida=vehiculo.presion_establecida,
                                            nombre_de_eje=nombre_de_eje,
                                            producto=producto,
                                            inventario=inventario
                                            )
                except:
                    pass


        context["user"] = user
        context["groups_names"] = groups_names
        return context

class SearchView(LoginRequiredMixin, ListView):
    # Vista del dashboard buscar_vehiculos
    template_name = "buscar_vehiculos.html"
    model = Vehiculo
    ordering = ("-fecha_de_creacion")
    form_class = VehiculoForm

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        vehiculos = Vehiculo.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania), tirecheck=False)
        bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        bitacora_pro = Bitacora_Pro.objects.filter(compania=Compania.objects.get(compania=self.request.user.perfil.compania))
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), tirecheck=False)
        inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=self.request.user.perfil.compania), llanta__tirecheck=False)
        
        filtro_sospechoso = functions.vehiculo_sospechoso(inspecciones)
        vehiculos_sospechosos = vehiculos.filter(id__in=filtro_sospechoso)

        doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculos)
        filtro_rojo = functions.vehiculo_rojo(llantas, doble_mala_entrada, vehiculos)
        doble_mala_entrada_pro = functions.doble_mala_entrada_pro(bitacora_pro, vehiculos)
        filtro_rojo_pro = functions.vehiculo_rojo(llantas, doble_mala_entrada_pro, vehiculos)
        vehiculos_rojos = vehiculos.filter(id__in=filtro_rojo).exclude(id__in=vehiculos_sospechosos) | vehiculos.filter(id__in=filtro_rojo_pro).exclude(id__in=vehiculos_sospechosos)


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
    print(fecha)
    if num:
        vehiculos = Vehiculo.objects.filter(numero_economico__icontains=num, compania=Compania.objects.get(compania=request.user.perfil.compania), tirecheck=False)
        bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
        bitacora_pro = Bitacora_Pro.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania), tirecheck=False)
        inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania), llanta__tirecheck=False)
        
        filtro_sospechoso = functions.vehiculo_sospechoso(inspecciones)
        vehiculos_sospechosos = vehiculos.filter(id__in=filtro_sospechoso)

        doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculos)
        filtro_rojo = functions.vehiculo_rojo(llantas, doble_mala_entrada, vehiculos)
        doble_mala_entrada_pro = functions.doble_mala_entrada_pro(bitacora_pro, vehiculos)
        filtro_rojo_pro = functions.vehiculo_rojo(llantas, doble_mala_entrada_pro, vehiculos)
        vehiculos_rojos = vehiculos.filter(id__in=filtro_rojo).exclude(id__in=vehiculos_sospechosos) | vehiculos.filter(id__in=filtro_rojo_pro).exclude(id__in=vehiculos_sospechosos)

        filtro_amarillo = functions.vehiculo_amarillo(llantas)
        vehiculos_amarillos = vehiculos.filter(id__in=filtro_amarillo).exclude(id__in=vehiculos_rojos).exclude(id__in=vehiculos_sospechosos)

        vehiculos_verdes = vehiculos.exclude(id__in=vehiculos_rojos).exclude(id__in=vehiculos_sospechosos).exclude(id__in=vehiculos_amarillos)
        return render(request, "buscar_vehiculos.html", {
                                                "vehiculos_amarillos": vehiculos_amarillos,
                                                "vehiculos_rojos": vehiculos_rojos,
                                                "vehiculos_sospechosos": vehiculos_sospechosos,
                                                "vehiculos_verdes": vehiculos_verdes,
                                                "cantidad_amarillos": vehiculos_amarillos.count(),
                                                "cantidad_rojos": vehiculos_rojos.count(),
                                                "cantidad_sospechosos": vehiculos_sospechosos.count(),
                                                "cantidad_total": vehiculos.count(),
                                                "cantidad_verdes": vehiculos_verdes.count()
        })
    elif fecha and fecha != "Seleccionar Fecha":
        dividir_fecha = functions.convertir_rango2(fecha)
        primera_fecha = datetime.strptime(dividir_fecha[0], "%m/%d/%Y").date()
        segunda_fecha = datetime.strptime(dividir_fecha[1], "%m/%d/%Y").date()

        vehiculos = Vehiculo.objects.filter(fecha_de_inflado__range=[primera_fecha, segunda_fecha], compania=Compania.objects.get(compania=request.user.perfil.compania), tirecheck=False)
        bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
        bitacora_pro = Bitacora_Pro.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania), tirecheck=False)
        inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania), llanta__tirecheck=False)
        
        filtro_sospechoso = functions.vehiculo_sospechoso(inspecciones)
        vehiculos_sospechosos = vehiculos.filter(id__in=filtro_sospechoso)

        doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculos)
        filtro_rojo = functions.vehiculo_rojo(llantas, doble_mala_entrada, vehiculos)
        doble_mala_entrada_pro = functions.doble_mala_entrada_pro(bitacora_pro, vehiculos)
        filtro_rojo_pro = functions.vehiculo_rojo(llantas, doble_mala_entrada_pro, vehiculos)
        vehiculos_rojos = vehiculos.filter(id__in=filtro_rojo).exclude(id__in=vehiculos_sospechosos) | vehiculos.filter(id__in=filtro_rojo_pro).exclude(id__in=vehiculos_sospechosos)


        filtro_amarillo = functions.vehiculo_amarillo(llantas)
        vehiculos_amarillos = vehiculos.filter(id__in=filtro_amarillo).exclude(id__in=vehiculos_rojos).exclude(id__in=vehiculos_sospechosos)

        vehiculos_verdes = vehiculos.exclude(id__in=vehiculos_rojos).exclude(id__in=vehiculos_sospechosos).exclude(id__in=vehiculos_amarillos)

        return render(request, "buscar_vehiculos.html", {
                                                "vehiculos_amarillos": vehiculos_amarillos,
                                                "vehiculos_rojos": vehiculos_rojos,
                                                "vehiculos_sospechosos": vehiculos_sospechosos,
                                                "vehiculos_verdes": vehiculos_verdes,
                                                "cantidad_amarillos": vehiculos_amarillos.count(),
                                                "cantidad_rojos": vehiculos_rojos.count(),
                                                "cantidad_sospechosos": vehiculos_sospechosos.count(),
                                                "cantidad_total": vehiculos.count(),
                                                "cantidad_verdes": vehiculos_verdes.count(),
        })
    else:

        vehiculos = Vehiculo.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania), tirecheck=False)
        bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
        bitacora_pro = Bitacora_Pro.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania), tirecheck=False)
        inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania), llanta__tirecheck=False)
        
        filtro_sospechoso = functions.vehiculo_sospechoso(inspecciones)
        vehiculos_sospechosos = vehiculos.filter(id__in=filtro_sospechoso)

        doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculos)
        filtro_rojo = functions.vehiculo_rojo(llantas, doble_mala_entrada, vehiculos)
        doble_mala_entrada_pro = functions.doble_mala_entrada_pro(bitacora_pro, vehiculos)
        filtro_rojo_pro = functions.vehiculo_rojo(llantas, doble_mala_entrada_pro, vehiculos)
        vehiculos_rojos = vehiculos.filter(id__in=filtro_rojo).exclude(id__in=vehiculos_sospechosos) | vehiculos.filter(id__in=filtro_rojo_pro).exclude(id__in=vehiculos_sospechosos)

        filtro_amarillo = functions.vehiculo_amarillo(llantas)
        vehiculos_amarillos = vehiculos.filter(id__in=filtro_amarillo).exclude(id__in=vehiculos_rojos).exclude(id__in=vehiculos_sospechosos)

        vehiculos_verdes = vehiculos.exclude(id__in=vehiculos_rojos).exclude(id__in=vehiculos_sospechosos).exclude(id__in=vehiculos_amarillos)

        return render(request, "buscar_vehiculos.html", {
                                                "vehiculos_amarillos": vehiculos_amarillos,
                                                "vehiculos_rojos": vehiculos_rojos,
                                                "vehiculos_sospechosos": vehiculos_sospechosos,
                                                "vehiculos_verdes": vehiculos_verdes,
                                                "cantidad_amarillos": vehiculos_amarillos.count(),
                                                "cantidad_rojos": vehiculos_rojos.count(),
                                                "cantidad_sospechosos": vehiculos_sospechosos.count(),
                                                "cantidad_total": vehiculos.count(),
                                                "cantidad_verdes": vehiculos_verdes.count(),
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
        inspecciones_llanta = Inspeccion.objects.filter(llanta=llanta)
        vehiculo = llanta.vehiculo
        llantas = Llanta.objects.filter(vehiculo=vehiculo)
        inspecciones = Inspeccion.objects.filter(llanta__in=llantas)

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
        mes_5 = functions.mes_anterior(mes_4)
        mes_6 = functions.mes_anterior(mes_5)
        mes_7 = functions.mes_anterior(mes_6)
        mes_8 = functions.mes_anterior(mes_7)

        hoy1 = hoy.strftime("%m")
        hoy2 = mes_2.strftime("%m")
        hoy3 = mes_3.strftime("%m")
        hoy4 = mes_4.strftime("%m")
        hoy5 = mes_5.strftime("%m")
        hoy6 = mes_6.strftime("%m")
        hoy7 = mes_7.strftime("%m")
        hoy8 = mes_8.strftime("%m")


        color = functions.entrada_correcta_actual(vehiculo)

        vehiculo_mes1 = bitacora.filter(fecha_de_inflado__month=hoy1)
        vehiculo_mes2 = bitacora.filter(fecha_de_inflado__month=hoy2)
        vehiculo_mes3 = bitacora.filter(fecha_de_inflado__month=hoy3)
        vehiculo_mes4 = bitacora.filter(fecha_de_inflado__month=hoy4)
        vehiculo_mes5 = bitacora.filter(fecha_de_inflado__month=hoy5)
        vehiculo_mes6 = bitacora.filter(fecha_de_inflado__month=hoy6)
        vehiculo_mes7 = bitacora.filter(fecha_de_inflado__month=hoy7)
        vehiculo_mes8 = bitacora.filter(fecha_de_inflado__month=hoy8)

        mala_entrada_contar_mes1 = functions.contar_mala_entrada(vehiculo_mes1)
        mala_entrada_contar_mes2 = functions.contar_mala_entrada(vehiculo_mes2)
        mala_entrada_contar_mes3 = functions.contar_mala_entrada(vehiculo_mes3)
        mala_entrada_contar_mes4 = functions.contar_mala_entrada(vehiculo_mes4)
        mala_entrada_contar_mes5 = functions.contar_mala_entrada(vehiculo_mes5)
        mala_entrada_contar_mes6 = functions.contar_mala_entrada(vehiculo_mes6)
        mala_entrada_contar_mes7 = functions.contar_mala_entrada(vehiculo_mes7)
        mala_entrada_contar_mes8 = functions.contar_mala_entrada(vehiculo_mes8)

        doble_entrada = functions.doble_entrada(bitacora)
        doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculo)

        filtro_sospechoso = functions.vehiculo_sospechoso_llanta(inspecciones)
        llantas_sospechosas = llantas.filter(numero_economico__in=filtro_sospechoso)

        filtro_rojo = functions.vehiculo_rojo_llanta(llantas)
        llantas_rojas = llantas.filter(numero_economico__in=filtro_rojo).exclude(id__in=llantas_sospechosas)
        
        filtro_amarillo = functions.vehiculo_amarillo_llanta(llantas)
        llantas_amarillas = llantas.filter(numero_economico__in=filtro_amarillo).exclude(id__in=llantas_sospechosas).exclude(id__in=llantas_rojas)
        
        llantas_azules = llantas.exclude(id__in=llantas_sospechosas).exclude(id__in=llantas_rojas).exclude(id__in=llantas_amarillas)
        
        if llanta in llantas_sospechosas:
            color_profundidad = 'purple'
        elif llanta in llantas_rojas:
            color_profundidad = 'bad'
        elif llanta in llantas_amarillas:
            color_profundidad = 'yellow'
        elif llanta in llantas_azules:
            color_profundidad = 'good'

        if doble_mala_entrada:
            message = "Doble mala entrada"
            color = "bad"
        elif color == "bad":
            message = "Tiene mala entrada"
        else:
            message = None

        problemas_abiertos = []
        if message:
            problemas_abiertos.append([llanta, message])
        if color_profundidad == "bad":
            problemas_abiertos.append([llanta, "Profundidad abajo del punto de retiro"])
        if color_profundidad == "yellow":
            problemas_abiertos.append([llanta, "Profundidad en el punto de retiro"])

        regresion_llanta = functions.km_proyectado_llanta(inspecciones_llanta)
        try:
            km_proyectado = round(regresion_llanta[0])
            km_x_mm = round(regresion_llanta[1])
            cpk = round(regresion_llanta[2], 3)
        except:
            km_proyectado = 0
            km_x_mm = 0
            cpk = 0

        comportamiento_de_desgaste = functions.comportamiento_de_desgaste(inspecciones_llanta)

        desgaste_mensual = functions.desgaste_mensual(inspecciones_llanta)

        context["bitacoras"] = bitacora
        context["cantidad_doble_entrada_mes1"] = doble_entrada[1]["mes1"]
        context["cantidad_doble_entrada_mes2"] = doble_entrada[1]["mes2"]
        context["cantidad_doble_entrada_mes3"] = doble_entrada[1]["mes3"]
        context["cantidad_doble_entrada_mes4"] = doble_entrada[1]["mes4"]
        context["cantidad_doble_entrada_mes5"] = doble_entrada[1]["mes5"]
        context["cantidad_doble_entrada_mes6"] = doble_entrada[1]["mes6"]
        context["cantidad_doble_entrada_mes7"] = doble_entrada[1]["mes7"]
        context["cantidad_doble_entrada_mes8"] = doble_entrada[1]["mes8"]
        context["cantidad_entrada_mes1"] = mala_entrada_contar_mes1
        context["cantidad_entrada_mes2"] = mala_entrada_contar_mes2
        context["cantidad_entrada_mes3"] = mala_entrada_contar_mes3
        context["cantidad_entrada_mes4"] = mala_entrada_contar_mes4
        context["cantidad_entrada_mes5"] = mala_entrada_contar_mes5
        context["cantidad_entrada_mes6"] = mala_entrada_contar_mes6
        context["cantidad_entrada_mes7"] = mala_entrada_contar_mes7
        context["cantidad_entrada_mes8"] = mala_entrada_contar_mes8
        context["color"] = color
        context["color_profundidad"] = color_profundidad
        context["cpk"] = cpk
        context["desgastes"] = comportamiento_de_desgaste
        context["desgaste_mensual"] = desgaste_mensual
        context["entradas"] = entradas_correctas
        context["hoy"] = hoy
        context["km_proyectado"] = km_proyectado
        context["km_x_mm"] = km_x_mm
        context["mes_1"] = mes_1
        context["mes_2"] = mes_2.strftime("%b")
        context["mes_3"] = mes_3.strftime("%b")
        context["mes_4"] = mes_4.strftime("%b")
        context["mes_5"] = mes_5.strftime("%b")
        context["mes_6"] = mes_6.strftime("%b")
        context["mes_7"] = mes_7.strftime("%b")
        context["mes_8"] = mes_8.strftime("%b")
        context["message"] = message
        context["problemas_abiertos"] = problemas_abiertos
        context["vehiculo"] = vehiculo
        context["vehiculo_mes1"] = vehiculo_mes1.count()
        context["vehiculo_mes2"] = vehiculo_mes2.count()
        context["vehiculo_mes3"] = vehiculo_mes3.count()
        context["vehiculo_mes4"] = vehiculo_mes4.count()
        context["vehiculo_mes5"] = vehiculo_mes5.count()
        context["vehiculo_mes6"] = vehiculo_mes6.count()
        context["vehiculo_mes7"] = vehiculo_mes7.count()
        context["vehiculo_mes8"] = vehiculo_mes8.count()
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
        vehiculo = Vehiculo.objects.get(pk=self.kwargs['pk'])
        llantas = Llanta.objects.filter(vehiculo=vehiculo, tirecheck=False)
        inspecciones = Inspeccion.objects.filter(llanta__in=llantas)
        bitacora = Bitacora.objects.filter(numero_economico=Vehiculo.objects.get(numero_economico=vehiculo.numero_economico), compania=Compania.objects.get(compania=self.request.user.perfil.compania))
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
        mes_5 = functions.mes_anterior(mes_4)
        mes_6 = functions.mes_anterior(mes_5)
        mes_7 = functions.mes_anterior(mes_6)
        mes_8 = functions.mes_anterior(mes_7)



        hoy1 = hoy.strftime("%m")
        hoy2 = mes_2.strftime("%m")
        hoy3 = mes_3.strftime("%m")
        hoy4 = mes_4.strftime("%m")
        hoy5 = mes_5.strftime("%m")
        hoy6 = mes_6.strftime("%m")
        hoy7 = mes_7.strftime("%m")
        hoy8 = mes_8.strftime("%m")



        color = functions.entrada_correcta_actual(vehiculo)

        if bitacora:
            vehiculo_mes1 = bitacora.filter(fecha_de_inflado__month=hoy1)
            vehiculo_mes2 = bitacora.filter(fecha_de_inflado__month=hoy2)
            vehiculo_mes3 = bitacora.filter(fecha_de_inflado__month=hoy3)
            vehiculo_mes4 = bitacora.filter(fecha_de_inflado__month=hoy4)
            vehiculo_mes5 = bitacora.filter(fecha_de_inflado__month=hoy5)
            vehiculo_mes6 = bitacora.filter(fecha_de_inflado__month=hoy6)
            vehiculo_mes7 = bitacora.filter(fecha_de_inflado__month=hoy7)
            vehiculo_mes8 = bitacora.filter(fecha_de_inflado__month=hoy8)

            mala_entrada_contar_mes1 = functions.contar_mala_entrada(vehiculo_mes1)
            mala_entrada_contar_mes2 = functions.contar_mala_entrada(vehiculo_mes2)
            mala_entrada_contar_mes3 = functions.contar_mala_entrada(vehiculo_mes3)
            mala_entrada_contar_mes4 = functions.contar_mala_entrada(vehiculo_mes4)
            mala_entrada_contar_mes5 = functions.contar_mala_entrada(vehiculo_mes5)
            mala_entrada_contar_mes6 = functions.contar_mala_entrada(vehiculo_mes6)
            mala_entrada_contar_mes7 = functions.contar_mala_entrada(vehiculo_mes7)
            mala_entrada_contar_mes8 = functions.contar_mala_entrada(vehiculo_mes8)

            doble_entrada = functions.doble_entrada(bitacora)
            doble_mala_entrada = functions.doble_mala_entrada(bitacora, vehiculo)

            if doble_mala_entrada:
                message = "Doble mala entrada"
                color = "bad"
            elif color == "bad":
                message = "Baja presión"
            else:
                message = None

            configuracion = vehiculo.configuracion
            cantidad_llantas = functions.cantidad_llantas(configuracion)

            posiciones = llantas.values("posicion").distinct()
            ejes = llantas.values("nombre_de_eje").distinct()

            comparativa_de_posiciones = {}
            for posicion in posiciones:
                valores_posicion = []

                llantas_posicion = llantas.filter(posicion=posicion["posicion"])
                inspecciones_posicion = Inspeccion.objects.filter(llanta__in=llantas_posicion)
                if inspecciones_posicion.exists():
                    regresion_posicion = functions.km_proyectado(inspecciones_posicion, False)
                    km_proyectado = regresion_posicion[0]
                    profundidad = regresion_posicion[6]

                    valores_posicion.append(km_proyectado)
                    valores_posicion.append(profundidad)
                    
                    comparativa_de_posiciones[posicion["posicion"]] = valores_posicion

            comparativa_de_ejes = {}
            for eje in ejes:
                valores_eje = []

                llantas_eje = llantas.filter(nombre_de_eje=eje["nombre_de_eje"])
                inspecciones_eje = Inspeccion.objects.filter(llanta__in=llantas_eje)
                if inspecciones_eje.exists():
                    regresion_eje = functions.km_proyectado(inspecciones_eje, False)
                    km_x_mm_eje = regresion_eje[1]

                    valores_eje.append(km_x_mm_eje)
                    
                    comparativa_de_ejes[eje["nombre_de_eje"]] = valores_eje
            
            regresion_vehiculo = functions.km_proyectado(inspecciones, False)
            cpk_vehiculo = regresion_vehiculo[3]
            cpk_vehiculo = round(sum(cpk_vehiculo), 3)

            reemplazo_actual = functions.reemplazo_actual2(llantas)
            reemplazo_actual_ejes = {k: v for k, v in reemplazo_actual.items() if v != 0}

            context["bitacoras"] = bitacora
            context["cantidad_doble_entrada_mes1"] = doble_entrada[1]["mes1"]
            context["cantidad_doble_entrada_mes2"] = doble_entrada[1]["mes2"]
            context["cantidad_doble_entrada_mes3"] = doble_entrada[1]["mes3"]
            context["cantidad_doble_entrada_mes4"] = doble_entrada[1]["mes4"]
            context["cantidad_doble_entrada_mes5"] = doble_entrada[1]["mes5"]
            context["cantidad_doble_entrada_mes6"] = doble_entrada[1]["mes6"]
            context["cantidad_doble_entrada_mes7"] = doble_entrada[1]["mes7"]
            context["cantidad_doble_entrada_mes8"] = doble_entrada[1]["mes8"]
            context["cantidad_entrada_mes1"] = mala_entrada_contar_mes1
            context["cantidad_entrada_mes2"] = mala_entrada_contar_mes2
            context["cantidad_entrada_mes3"] = mala_entrada_contar_mes3
            context["cantidad_entrada_mes4"] = mala_entrada_contar_mes4
            context["cantidad_entrada_mes5"] = mala_entrada_contar_mes5
            context["cantidad_entrada_mes6"] = mala_entrada_contar_mes6
            context["cantidad_entrada_mes7"] = mala_entrada_contar_mes7
            context["cantidad_entrada_mes8"] = mala_entrada_contar_mes8
            context["cantidad_inflado"] = inflado
            context["cantidad_llantas"] = cantidad_llantas
            context["color"] = color
            context["comparativa_de_ejes"] = comparativa_de_ejes
            context["comparativa_de_posiciones"] = comparativa_de_posiciones
            context["configuracion"] = configuracion
            context["cpk_vehiculo"] = cpk_vehiculo
            context["doble_entrada"] = doble_entrada
            context["entradas"] = entradas_correctas
            context["fecha"] = fecha
            context["hoy"] = hoy
            context["mes_1"] = mes_1
            context["mes_2"] = mes_2.strftime("%b")
            context["mes_3"] = mes_3.strftime("%b")
            context["mes_4"] = mes_4.strftime("%b")
            context["mes_5"] = mes_5.strftime("%b")
            context["mes_6"] = mes_6.strftime("%b")
            context["mes_7"] = mes_7.strftime("%b")
            context["mes_8"] = mes_8.strftime("%b")
            context["message"] = message
            context["reemplazo_actual_ejes"] = reemplazo_actual_ejes
            context["vehiculo_mes1"] = vehiculo_mes1.count()
            context["vehiculo_mes2"] = vehiculo_mes2.count()
            context["vehiculo_mes3"] = vehiculo_mes3.count()
            context["vehiculo_mes4"] = vehiculo_mes4.count()
            context["vehiculo_mes5"] = vehiculo_mes5.count()
            context["vehiculo_mes6"] = vehiculo_mes6.count()
            context["vehiculo_mes7"] = vehiculo_mes7.count()
            context["vehiculo_mes8"] = vehiculo_mes8.count()
            
        #Generacion de ejes dinamico
        vehiculo_actual = Vehiculo.objects.get(pk = self.kwargs['pk'])
        llantas_actuales = Llanta.objects.filter(vehiculo = self.kwargs['pk'], tirecheck=False)
        inspecciones_actuales = Inspeccion.objects.filter(llanta__in=llantas_actuales)
        
        #Obtencion de la lista de las llantas
        
        filtro_sospechoso = functions.vehiculo_sospechoso_llanta(inspecciones_actuales)
        llantas_sospechosas = llantas_actuales.filter(numero_economico__in=filtro_sospechoso)

        filtro_rojo = functions.vehiculo_rojo_llanta(llantas_actuales)
        llantas_rojas = llantas_actuales.filter(numero_economico__in=filtro_rojo).exclude(id__in=llantas_sospechosas)
        
        filtro_amarillo = functions.vehiculo_amarillo_llanta(llantas_actuales)
        llantas_amarillas = llantas_actuales.filter(numero_economico__in=filtro_amarillo).exclude(id__in=llantas_sospechosas).exclude(id__in=llantas_rojas)
        
        llantas_azules = llantas_actuales.exclude(id__in=llantas_sospechosas).exclude(id__in=llantas_rojas).exclude(id__in=llantas_amarillas)
        
        #Obtencion de la data
        num_ejes = vehiculo_actual.configuracion.split('.')
        ejes_no_ordenados = []
        ejes = []
        eje = 1
        color_profundidad = ""
        for num in num_ejes:
            list_temp = []
            for llanta in llantas_actuales:
                if llanta in llantas_sospechosas:
                    color_profundidad = 'purple'
                elif llanta in llantas_rojas:
                    color_profundidad = 'bad'
                elif llanta in llantas_amarillas:
                    color_profundidad = 'yellow'
                elif llanta in llantas_azules:
                    color_profundidad = 'good'
                if llanta.ultima_inspeccion == None:
                    color_profundidad = 'bad'
                objetivo = llanta.vehiculo.compania.objetivo / 100
                presion_act = llanta.presion_de_salida
                presion_minima = 100 - (100 * objetivo)
                presion_maxima = 100 + (100 * objetivo)
                #print(f'{objetivo}'.center(50, "-"))
                #print(f'{presion_minima}'.center(50, "-"))
                #print(f'{presion_maxima}'.center(50, "-"))
                #print(f'{presion_act}'.center(50, "-"))
                #print(presion_act > presion_minima)
                #print(presion_act < presion_maxima)
                #print('***********************************')
                if presion_act > presion_minima and presion_act < presion_maxima:
                    color_presion = 'good'
                else:
                    color_presion = 'bad'
                
                if llanta.eje == eje:
                    list_temp.append([llanta, color_profundidad, color_presion])
            eje += 1
            ejes_no_ordenados.append(list_temp)
        
        for eje in ejes_no_ordenados:
            if len(eje) == 2:
                lista_temp = ['', '']
                for llanta_act in eje:
                    if 'LI' in llanta_act[0].posicion:
                        lista_temp[0] = llanta_act
                        
                    elif 'RI' in llanta_act[0].posicion:
                        lista_temp[1] = llanta_act
                ejes.append(lista_temp)
                print(' 0---0')
            
            else:
                lista_temp = ['', '', '', '']
                for llanta_act in eje:
                    if 'LO' in llanta_act[0].posicion:
                        lista_temp[0] = llanta_act
                    elif 'LI' in llanta_act[0].posicion:
                        lista_temp[1] = llanta_act
                    elif 'RI' in llanta_act[0].posicion:
                        lista_temp[2] = llanta_act
                    elif 'RO' in llanta_act[0].posicion:
                        lista_temp[3] = llanta_act
                ejes.append(lista_temp)
                print('00---00')

        
            
            
        color = functions.entrada_correcta_actual(vehiculo_actual)
        #print(color)
        if bitacora:
            if doble_mala_entrada:
                color == 'bad'
                style = 'bad'
            elif color == 'good':
                style = 'good'
            elif color == 'bad':
                style = 'bad'
            else:
                style = 'bad'
        else:
            style = 'good'
        
        cant_ejes = len(ejes)
        
        if len(llantas_actuales) == 0:
            sin_llantas = True
        else:
            sin_llantas = False
        
        problemas_abiertos = []
        try:
            for eje in ejes:
                if len(eje) == 2:
                    if message:
                        problemas_abiertos.append([eje[0][0], message])
                    if eje[0][1] == "bad":
                        problemas_abiertos.append([eje[0][0], "Profundidad abajo del punto de retiro"])
                    if eje[0][1] == "yellow":
                        problemas_abiertos.append([eje[0][0], "Profundidad en el punto de retiro"])
                    if message:
                        problemas_abiertos.append([eje[1][0], message])
                    if eje[1][1] == "bad":
                        problemas_abiertos.append([eje[1][0], "Profundidad abajo del punto de retiro"])
                    if eje[1][1] == "yellow":
                        problemas_abiertos.append([eje[1][0], "Profundidad en el punto de retiro"])
                else:
                    if message:
                        problemas_abiertos.append([eje[0][0], message])
                    if eje[0][1] == "bad":
                        problemas_abiertos.append([eje[0][0], "Profundidad abajo del punto de retiro"])
                    if eje[0][1] == "yellow":
                        problemas_abiertos.append([eje[0][0], "Profundidad en el punto de retiro"])
                    if message:
                        problemas_abiertos.append([eje[1][0], message])
                    if eje[1][1] == "bad":
                        problemas_abiertos.append([eje[1][0], "Profundidad abajo del punto de retiro"])
                    if eje[1][1] == "yellow":
                        problemas_abiertos.append([eje[1][0], "Profundidad en el punto de retiro"])
                    if message:
                        problemas_abiertos.append([eje[2][0], message])
                    if eje[2][1] == "bad":
                        problemas_abiertos.append([eje[2][0], "Profundidad abajo del punto de retiro"])
                    if eje[2][1] == "yellow":
                        problemas_abiertos.append([eje[2][0], "Profundidad en el punto de retiro"])
                    if message:
                        problemas_abiertos.append([eje[3][0], message])
                    if eje[3][1] == "bad":
                        problemas_abiertos.append([eje[3][0], "Profundidad abajo del punto de retiro"])
                    if eje[3][1] == "yellow":
                        problemas_abiertos.append([eje[3][0], "Profundidad en el punto de retiro"])
        except:
            pass

        #print(len(llantas_actuales))
        #print(sin_llantas)
        #print(problemas_abiertos)
        #print(vehiculo.configuracion)
        #print(ejes)
        #print(f'style: {style}')
        #print(f'llantas_sospechosas: {llantas_sospechosas}')
        #print(f'llantas_rojas: {llantas_rojas}')
        #print(f'llantas_amarillas: {llantas_amarillas}')
        #print(f'llantas_azules: {llantas_azules}')
        context['ejes'] = ejes
        context['style'] = style
        context['cant_ejes'] = cant_ejes
        context['problemas_abiertos'] = problemas_abiertos
        context['sin_llantas'] = sin_llantas
        context['presion_maxima'] = int(float(presion_maxima))
        context['presion_minima'] = int(float(presion_minima))
        
        #Generacion de las bitacoras
        bitacora_edicion = Bitacora_Edicion.objects.filter(vehiculo = vehiculo_actual)
        context['bitacora_edicion'] = bitacora_edicion
        return context


class ReporteDeCambios(ListView):
    template_name= 'reporteDeCambios.html'
    model = Bitacora_Edicion
    
    def get_queryset(self):
        return Bitacora_Edicion.objects.filter(pk = self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bitacora = Bitacora_Edicion.objects.get(pk = self.kwargs['pk'])
        context['bitacora'] = bitacora
        context['registros'] = Registro_Bitacora.objects.filter(bitacora = bitacora)
        return context


def download_rendimiento_de_llanta(request):
    # Define Django project base directory
    # content-type of response
    vehiculos = Vehiculo.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
    llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania), vehiculo__in=vehiculos)
    inspecciones = Inspeccion.objects.filter(llanta__in=llantas)

    regresion = functions.km_proyectado(inspecciones, True)
    llantas_limpias = regresion[4]
    llantas_analizadas = llantas.filter(numero_economico__in=llantas_limpias)

    response = HttpResponse(content_type='application/ms-excel')

	#decide file name
    response['Content-Disposition'] = 'attachment; filename="LlantasAnalizadas.xls"'

	#creating workbook
    wb = xlwt.Workbook(encoding='utf-8')

	#adding sheet
    ws = wb.add_sheet("sheet1")

	# Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
	# headers are bold
    font_style.font.bold = True

	#column header names, you can use your own headers here
    columns = ['Llanta', 'Vehiculo', 'Posición', 'Km actual', 'Km proyectado', 'CPK', 'Sucursal', 'Aplicación', 'Clase', 'Nombre de eje', 'Producto', 'Min profundidad']

    #write column headers in sheet
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    #get your data, from database or from a text file...
    for my_row in range(len(llantas_analizadas)):
        ws.write(my_row + 1, 0, str(llantas_analizadas[my_row]), font_style)
        ws.write(my_row + 1, 1, str(llantas_analizadas.values("vehiculo__numero_economico")[my_row]["vehiculo__numero_economico"]), font_style)
        ws.write(my_row + 1, 2, str(llantas_analizadas.values("posicion")[my_row]["posicion"]), font_style)
        ws.write(my_row + 1, 3, str(llantas_analizadas.values("ultima_inspeccion__km")[my_row]["ultima_inspeccion__km"]), font_style)
        ws.write(my_row + 1, 4, str(regresion[5][my_row]), font_style)
        ws.write(my_row + 1, 5, str(regresion[3][my_row]), font_style)
        ws.write(my_row + 1, 6, str(llantas_analizadas.values("vehiculo__ubicacion__nombre")[my_row]["vehiculo__ubicacion__nombre"]), font_style)
        ws.write(my_row + 1, 7, str(llantas_analizadas.values("vehiculo__aplicacion__nombre")[my_row]["vehiculo__aplicacion__nombre"]), font_style)
        ws.write(my_row + 1, 8, str(llantas_analizadas.values("vehiculo__clase")[my_row]["vehiculo__clase"]), font_style)
        ws.write(my_row + 1, 9, str(llantas_analizadas.values("nombre_de_eje")[my_row]["nombre_de_eje"]), font_style)
        ws.write(my_row + 1, 10, str(llantas_analizadas.values("producto__producto")[my_row]["producto__producto"]), font_style)
        ws.write(my_row + 1, 11, str(llantas_analizadas.values("ultima_inspeccion__min_profundidad")[my_row]["ultima_inspeccion__min_profundidad"]), font_style)


    wb.save(response)
    return response

def download_reemplazo_estimado(request):
    # Define Django project base directory
    # content-type of response
    llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania))
    inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania))
    ubicacion = Ubicacion.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))[0]

    embudo_vida1 = functions.embudo_vidas(llantas)
    embudo_vida2 = functions.embudo_vidas_con_regresion(inspecciones, ubicacion, 30)
    embudo_vida3 = functions.embudo_vidas_con_regresion(inspecciones, ubicacion, 60)
    embudo_vida4 = functions.embudo_vidas_con_regresion(inspecciones, ubicacion, 90)

    periodo = []
    for llanta in llantas:
        if llanta in embudo_vida1[0]:
            periodo.append("Hoy")
        elif llanta in embudo_vida2[0]:
            periodo.append("30 días")
        elif llanta in embudo_vida3[0]:
            periodo.append("60 días")
        elif llanta in embudo_vida4[0]:
            periodo.append("90 días")
        else:
            periodo.append("-")

    response = HttpResponse(content_type='application/ms-excel')

	#decide file name
    response['Content-Disposition'] = 'attachment; filename="LlantasReemplazoEstimado.xls"'

	#creating workbook
    wb = xlwt.Workbook(encoding='utf-8')

	#adding sheet
    ws = wb.add_sheet("sheet1")

	# Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
	# headers are bold
    font_style.font.bold = True

	#column header names, you can use your own headers here
    columns = ['Llanta', 'Vehiculo', 'Posición', 'Sucursal', 'Aplicación', 'Clase', 'Nombre de eje', 'Producto', 'Min profundidad', 'Periodo']

    #write column headers in sheet
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    #get your data, from database or from a text file...
    for my_row in range(len(llantas)):
        ws.write(my_row + 1, 0, str(llantas[my_row]), font_style)
        ws.write(my_row + 1, 1, str(llantas.values("vehiculo__numero_economico")[my_row]["vehiculo__numero_economico"]), font_style)
        ws.write(my_row + 1, 2, str(llantas.values("posicion")[my_row]["posicion"]), font_style)
        ws.write(my_row + 1, 3, str(llantas.values("vehiculo__ubicacion__nombre")[my_row]["vehiculo__ubicacion__nombre"]), font_style)
        ws.write(my_row + 1, 4, str(llantas.values("vehiculo__aplicacion__nombre")[my_row]["vehiculo__aplicacion__nombre"]), font_style)
        ws.write(my_row + 1, 5, str(llantas.values("vehiculo__clase")[my_row]["vehiculo__clase"]), font_style)
        ws.write(my_row + 1, 6, str(llantas.values("nombre_de_eje")[my_row]["nombre_de_eje"]), font_style)
        ws.write(my_row + 1, 7, str(llantas.values("producto__producto")[my_row]["producto__producto"]), font_style)
        ws.write(my_row + 1, 8, str(llantas.values("ultima_inspeccion__min_profundidad")[my_row]["ultima_inspeccion__min_profundidad"]), font_style)
        ws.write(my_row + 1, 9, str(periodo[my_row]), font_style)

    wb.save(response)
    return response

def informe_de_perdida_y_rendimiento(request):    

    if request.method =="POST":
        flota1 = request.POST.getlist("sucursal")
        aplicacion1 = request.POST.getlist("aplicacion")
        fecha1 = request.POST.get("fechaInicio")
        fecha2 = request.POST.get("fechaFin")
        fecha1 = functions.convertir_rango(fecha1)
        fecha2 = functions.convertir_rango(fecha2)
        primera_fecha = datetime.strptime(fecha1, "%Y/%m/%d").date()
        segunda_fecha = datetime.strptime(fecha2, "%Y/%m/%d").date()

        compania = Compania.objects.get(compania=request.user.perfil.compania)
        inicio = datetime(primera_fecha.year, primera_fecha.month, primera_fecha.day)
        fin    = datetime(segunda_fecha.year, segunda_fecha.month, segunda_fecha.day)
        lista_fechas = [(inicio + timedelta(days=d)).strftime("%Y-%m-%d") for d in range((fin - inicio).days + 1)]

        vehiculos = Vehiculo.objects.filter(compania=Compania.objects.get(compania=compania))

        if flota1:
            vehiculos = vehiculos.filter(functions.reduce(or_, [Q(ubicacion=Ubicacion.objects.get(nombre=f)) for f in flota1]))
        if aplicacion1:
            vehiculos = vehiculos.filter(functions.reduce(or_, [Q(aplicacion=Aplicacion.objects.get(nombre=a)) for a in aplicacion1]))

        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=compania), vehiculo__in=vehiculos)
        inspecciones = Inspeccion.objects.filter(llanta__in=llantas)
        productos_llanta = llantas.values("producto").distinct()
        productos = Producto.objects.filter(id__in=productos_llanta)
        flotas_vehiculo = vehiculos.values("ubicacion__nombre").distinct()
        flotas = Ubicacion.objects.filter(compania=compania, nombre__in=flotas_vehiculo)
        aplicaciones_vehiculo = vehiculos.values("aplicacion__nombre").distinct()
        aplicaciones = Aplicacion.objects.filter(compania=Compania.objects.get(compania=compania), nombre__in=aplicaciones_vehiculo)
        ejes = llantas.values("nombre_de_eje").distinct()
        clases = vehiculos.values("clase").distinct()

        regresion = functions.km_proyectado(inspecciones, True)
        llantas_limpias = regresion[4]

        comparativa_de_productos = {}
        for producto in productos:
            valores_producto = []

            llantas_producto_total = llantas.filter(producto=producto)
            llantas_producto = llantas.filter(producto=producto, numero_economico__in=llantas_limpias)

            print("llantas_producto", llantas_producto)

            inspecciones_producto = Inspeccion.objects.filter(llanta__in=llantas_producto)
            regresion_producto = functions.km_proyectado(inspecciones_producto, False)
            km_proyectado_producto = regresion_producto[0]
            cpk_producto = regresion_producto[2]

            valores_producto.append(km_proyectado_producto)
            valores_producto.append(cpk_producto)
            print("valores_producto", valores_producto)

            dibujo = producto.dibujo
            valores_producto.append(dibujo)
            if dibujo and km_proyectado_producto != 0:
                comparativa_de_productos[producto] = valores_producto

        comparativa_de_flotas = {}
        for flota in flotas:
            valores_flota = []

            llantas_flota = llantas.filter(vehiculo__ubicacion=flota, numero_economico__in=llantas_limpias)
            if llantas_flota:
                inspecciones_flota = Inspeccion.objects.filter(llanta__in=llantas_flota)
                regresion_flota = functions.km_proyectado(inspecciones_flota, False)
                km_proyectado_flota = regresion_flota[0]
                cpk_flota = regresion_flota[2]

                valores_flota.append(km_proyectado_flota)
                valores_flota.append(cpk_flota)

                comparativa_de_flotas[flota] = valores_flota

        comparativa_de_aplicaciones = {}
        for aplicacion in aplicaciones:
            valores_aplicacion = []

            llantas_aplicacion = llantas.filter(vehiculo__aplicacion =aplicacion, numero_economico__in=llantas_limpias)
            if llantas_aplicacion:

                inspecciones_aplicacion = Inspeccion.objects.filter(llanta__in=llantas_aplicacion)
                regresion_aplicacion = functions.km_proyectado(inspecciones_aplicacion, False)
                km_proyectado_aplicacion = regresion_aplicacion[0]
                cpk_aplicacion = regresion_aplicacion[2]

                valores_aplicacion.append(km_proyectado_aplicacion)
                valores_aplicacion.append(cpk_aplicacion)

                comparativa_de_aplicaciones[aplicacion] = valores_aplicacion

        comparativa_de_ejes = {}
        for eje in ejes:
            valores_eje = []

            llantas_eje = llantas.filter(nombre_de_eje=eje["nombre_de_eje"], numero_economico__in=llantas_limpias)
            inspecciones_eje = Inspeccion.objects.filter(llanta__in=llantas_eje)
            if inspecciones_eje.exists():
                regresion_eje = functions.km_proyectado(inspecciones_eje, False)
                km_proyectado_eje = regresion_eje[0]
                cpk_eje = regresion_eje[2]

                valores_eje.append(km_proyectado_eje)
                valores_eje.append(cpk_eje)

                comparativa_de_ejes[eje["nombre_de_eje"]] = valores_eje

        comparativa_de_clases = {}
        for clase in clases:
            valores_clase = []

            llantas_clase = llantas.filter(vehiculo__clase=clase["clase"].upper(), numero_economico__in=llantas_limpias)
            inspecciones_clase = Inspeccion.objects.filter(llanta__in=llantas_clase)
            if inspecciones_clase.exists():
                regresion_clase = functions.km_proyectado(inspecciones_clase, False)
                km_proyectado_clase = regresion_clase[0]
                cpk_clase = regresion_clase[2]

                valores_clase.append(km_proyectado_clase)
                valores_clase.append(cpk_clase)

                comparativa_de_clases[clase["clase"]] = valores_clase

        print(comparativa_de_flotas)
        print(comparativa_de_aplicaciones)
        print(comparativa_de_ejes)
        print(comparativa_de_productos)
        print(comparativa_de_clases)


        eje_titulos_flota = []
        for i in range(len(comparativa_de_flotas)):
            com_flota_titulo = list(comparativa_de_flotas.keys())[i]
            eje_titulos_flota.append(com_flota_titulo)

        eje_y1_flota = []
        for i in range(len(comparativa_de_flotas)):
            com_flota_uno_valor = list(comparativa_de_flotas.values())[i][0]
            eje_y1_flota.append(com_flota_uno_valor)

        eje_y2_flota = []
        for i in range(len(comparativa_de_flotas)):
            com_flota_uno_valor = list(comparativa_de_flotas.values())[i][1]
            eje_y2_flota.append(com_flota_uno_valor)

        x_pos = np.arange(len(eje_titulos_flota))

        fig, ax = plt.subplots()
        fontsize = 14

        ax2 = ax.twinx()

        ax.bar(x_pos, eje_y1_flota, align='center', alpha=0.5, ecolor='black',
        capsize=3, width=0.2, color='r', label='data1')

        ax2.bar(x_pos+0.2, eje_y2_flota, align='center', alpha=0.5, ecolor='black',
        capsize=3, width=0.2, color='b', label='data2')

        for p in ax.patches:
            ax.annotate(np.round(p.get_height(),decimals=2), (p.get_x()+p.get_width()/2., p.get_height()), ha='center', va='top', xytext=(0, 10), textcoords='offset points')
        for p in ax2.patches:
            ax2.annotate(np.round(p.get_height(),decimals=3), (p.get_x()+p.get_width()/2., p.get_height()), ha='center', va='top', xytext=(0, 10), textcoords='offset points')

        ax.set_ylabel('Km proyectado')
        ax2.set_ylabel('CPK')

        ax.set_xticks(x_pos)
        ax.set_xticklabels(eje_titulos_flota, fontsize=fontsize)
        ax.set_title('Comparativa flotas')


        plt.grid()
        plt.savefig(os.path.abspath(os.getcwd()) + r"/aetoweb/files/files/ComparacionFlotas.png", dpi = 70, bbox_inches="tight")

        img_flotas = openpyxl.drawing.image.Image(os.path.abspath(os.getcwd()) + r"/aetoweb/files/files/ComparacionFlotas.png")

        eje_titulos_aplicaciones = []
        for i in range(len(comparativa_de_aplicaciones)):
            com_titulo = list(comparativa_de_aplicaciones.keys())[i]
            eje_titulos_aplicaciones.append(com_titulo)

        eje_y1_aplicaciones = []
        for i in range(len(comparativa_de_aplicaciones)):
            com_uno_valor = list(comparativa_de_aplicaciones.values())[i][0]
            eje_y1_aplicaciones.append(com_uno_valor)

        eje_y2_aplicaciones = []
        for i in range(len(comparativa_de_aplicaciones)):
            com_uno_valor = list(comparativa_de_aplicaciones.values())[i][1]
            eje_y2_aplicaciones.append(com_uno_valor)
        x_pos = np.arange(len(eje_titulos_aplicaciones))
        fig, ax = plt.subplots()
        fontsize = 14
        ax2 = ax.twinx()
        ax.bar(x_pos, eje_y1_aplicaciones, align='center', alpha=0.5, ecolor='black',
        capsize=3, width=0.2, color='r', label='data1')
        ax2.bar(x_pos+0.2, eje_y2_aplicaciones, align='center', alpha=0.5, ecolor='black',
        capsize=3, width=0.2, color='b', label='data2')

        for p in ax.patches:
            ax.annotate(np.round(p.get_height(),decimals=2), (p.get_x()+p.get_width()/2., p.get_height()), ha='center', va='top', xytext=(0, 10), textcoords='offset points')
        for p in ax2.patches:
            ax2.annotate(np.round(p.get_height(),decimals=3), (p.get_x()+p.get_width()/2., p.get_height()), ha='center', va='top', xytext=(0, 10), textcoords='offset points')

        ax.set_ylabel('Km proyectado')
        ax2.set_ylabel('CPK')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(eje_titulos_aplicaciones, fontsize=fontsize)
        ax.set_title('Comparación aplicaciones')
        plt.grid()
        plt.savefig(os.path.abspath(os.getcwd()) + r"/aetoweb/files/files/ComparacionAplicaciones.png", dpi = 70, bbox_inches="tight")

        img_aplicaciones = openpyxl.drawing.image.Image(os.path.abspath(os.getcwd()) + r"/aetoweb/files/files/ComparacionAplicaciones.png")

        eje_titulos_ejes = []
        for i in range(len(comparativa_de_ejes)):
            com_ejes_titulo = list(comparativa_de_ejes.keys())[i]
            eje_titulos_ejes.append(com_ejes_titulo)

        eje_y1_ejes = []
        for i in range(len(comparativa_de_ejes)):
            com_ejes_valor1 = list(comparativa_de_ejes.values())[i][0]
            eje_y1_ejes.append(com_ejes_valor1)

        eje_y2_ejes = []
        for i in range(len(comparativa_de_ejes)):
            com_ejes_valor2 = list(comparativa_de_ejes.values())[i][1]
            eje_y2_ejes.append(com_ejes_valor2)

        x_pos = np.arange(len(eje_titulos_ejes))

        fig, ax = plt.subplots()
        fontsize = 14

        ax2 = ax.twinx()

        ax.bar(x_pos, eje_y1_ejes, alpha=0.5, ecolor='black',
        capsize=3, width=0.2, color='r', label='data1')

        ax2.bar(x_pos+0.2, eje_y2_ejes, alpha=0.5, ecolor='black',
        capsize=3, width=0.2, color='b', label='data2')

        for p in ax.patches:
            ax.annotate(np.round(p.get_height(),decimals=2), (p.get_x()+p.get_width()/2., p.get_height()), ha='center', va='top', xytext=(0, 10), textcoords='offset points')
        for p in ax2.patches:
            ax2.annotate(np.round(p.get_height(),decimals=3), (p.get_x()+p.get_width()/2., p.get_height()), ha='center', va='top', xytext=(0, 10), textcoords='offset points')

        ax.set_ylabel('Km proyectado')
        ax2.set_ylabel('CPK')


        ax.set_xlabel(eje_titulos_ejes[int(x_pos)])
        ax.set_xticklabels(eje_titulos_ejes, fontsize=fontsize)
        ax.set_title('Comparativa ejes')

        plt.grid()
        plt.savefig(os.path.abspath(os.getcwd()) + r"/aetoweb/files/files/ComparacionEjes.png", dpi = 70, bbox_inches="tight")

        img_ejes = openpyxl.drawing.image.Image(os.path.abspath(os.getcwd()) + r"/aetoweb/files/files/ComparacionEjes.png")

        eje_titulos_producto = []
        for i in range(len(comparativa_de_productos)):
            com_titulo = list(comparativa_de_productos.values())[i][2]
            eje_titulos_producto.append(com_titulo)

        eje_y1_producto = []
        for i in range(len(comparativa_de_productos)):
            com_uno_valor = list(comparativa_de_productos.values())[i][0]
            eje_y1_producto.append(com_uno_valor)

        eje_y2_producto = []
        for i in range(len(comparativa_de_productos)):
            com_uno_valor = list(comparativa_de_productos.values())[i][1]
            eje_y2_producto.append(com_uno_valor)

        x_pos = np.arange(len(eje_titulos_producto))

        fig, ax = plt.subplots()
        fontsize = 14

        ax2 = ax.twinx()

        ax.bar(x_pos, eje_y1_producto, align='center', alpha=0.5, ecolor='black',
        capsize=3, width=0.2, color='r', label='data1')

        ax2.bar(x_pos+0.2, eje_y2_producto, align='center', alpha=0.5, ecolor='black',
        capsize=3, width=0.2, color='b', label='data2')

        for p in ax.patches:
            ax.annotate(np.round(p.get_height(),decimals=2), (p.get_x()+p.get_width()/2., p.get_height()), ha='center', va='top', xytext=(0, 10), textcoords='offset points')
        for p in ax2.patches:
            ax2.annotate(np.round(p.get_height(),decimals=3), (p.get_x()+p.get_width()/2., p.get_height()), ha='center', va='top', xytext=(0, 10), textcoords='offset points')

        ax.set_ylabel('Km proyectado')
        ax2.set_ylabel('CPK')


        ax.set_xticks(x_pos)
        ax.set_xticklabels(eje_titulos_producto, fontsize=fontsize)
        ax.set_title('Comparativa productos')
        plt.grid()
        plt.savefig(os.path.abspath(os.getcwd()) + r"/aetoweb/files/files/ComparacionProductos.png", dpi = 70, bbox_inches="tight")

        img_producto = openpyxl.drawing.image.Image(os.path.abspath(os.getcwd()) + r"/aetoweb/files/files/ComparacionProductos.png")

        eje_titulos_clase = []
        for i in range(len(comparativa_de_clases)):
            com_clase_titulo = list(comparativa_de_clases.keys())[i]
            eje_titulos_clase.append(com_clase_titulo)

        eje_y1_clase = []
        for i in range(len(comparativa_de_clases)):
            com_clase_uno_valor = list(comparativa_de_clases.values())[i][0]
            eje_y1_clase.append(com_clase_uno_valor)

        eje_y2_clase = []
        for i in range(len(comparativa_de_clases)):
            com_clase_uno_valor = list(comparativa_de_clases.values())[i][1]
            eje_y2_clase.append(com_clase_uno_valor)

        x_pos = np.arange(len(eje_titulos_clase))

        fig, ax = plt.subplots()
        fontsize = 14

        ax2 = ax.twinx()

        ax.bar(x_pos, eje_y1_clase, align='center', alpha=0.5, ecolor='black',
        capsize=3, width=0.2, color='r', label='data1')

        ax2.bar(x_pos+0.2, eje_y2_clase, align='center', alpha=0.5, ecolor='black',
        capsize=3, width=0.2, color='b', label='data2')

        for p in ax.patches:
            ax.annotate(np.round(p.get_height(),decimals=2), (p.get_x()+p.get_width()/2., p.get_height()), ha='center', va='top', xytext=(0, 10), textcoords='offset points')
        for p in ax2.patches:
            ax2.annotate(np.round(p.get_height(),decimals=3), (p.get_x()+p.get_width()/2., p.get_height()), ha='center', va='top', xytext=(0, 10), textcoords='offset points')

        ax.set_ylabel('Km proyectado')
        ax2.set_ylabel('CPK')

        ax.set_xticks(x_pos)
        ax.set_xticklabels(eje_titulos_clase, fontsize=fontsize)
        ax.set_title('Comparativa clases')
        plt.grid()
        plt.savefig(os.path.abspath(os.getcwd()) + r"/aetoweb/files/files/ComparacionClases.png", dpi = 70, bbox_inches="tight")

        img_clases = openpyxl.drawing.image.Image(os.path.abspath(os.getcwd()) + r"/aetoweb/files/files/ComparacionClases.png")

        #creating workbook
        wb = openpyxl.Workbook()
        wb.create_sheet("Perdida")
        reporte = wb.get_sheet_by_name('Perdida')
        wb.remove(wb['Sheet'])

        wb.create_sheet("Rendimiento")
        reporte2 = wb.get_sheet_by_name('Rendimiento')

        reporte2.add_image(img_flotas, 'A1')
        reporte2.add_image(img_aplicaciones, 'L1')
        reporte2.add_image(img_ejes, 'A20')
        reporte2.add_image(img_producto, 'L20')
        reporte2.add_image(img_clases, 'A40')

        e1 = reporte.cell(row=1, column=1, value='VehicleRegistrationNumber')
        e2 = reporte.cell(row=1, column=2, value='CompanyName')
        e3 = reporte.cell(row=1, column=3, value='FleetName')
        e4 = reporte.cell(row=1, column=4, value='LocationName')
        e5 = reporte.cell(row=1, column=5, value='InspectionBeginTime')
        e6 = reporte.cell(row=1, column=6, value='InspectionFullNumber')
        e7 = reporte.cell(row=1, column=7, value='Inspection_Mileage')
        e8 = reporte.cell(row=1, column=8, value='VehicleClassName')
        e9 = reporte.cell(row=1, column=9, value='AxleConfigurationName')
        e10 = reporte.cell(row=1, column=10, value='VehicleMakeName')
        e11 = reporte.cell(row=1, column=11, value='VehicleModelName')
        e12 = reporte.cell(row=1, column=12, value='VehicleStatusId')
        e12 = reporte.cell(row=1, column=13, value='TyreSerialNumber')
        e12 = reporte.cell(row=1, column=14, value='Wheel_Position')
        e12 = reporte.cell(row=1, column=15, value='TyreMakeName')
        e12 = reporte.cell(row=1, column=16, value='TyrePatternName')
        e12 = reporte.cell(row=1, column=17, value='TyreSizeName')
        e12 = reporte.cell(row=1, column=18, value='TyreLifeName')
        e12 = reporte.cell(row=1, column=19, value='TD1')
        e12 = reporte.cell(row=1, column=20, value='TD2')
        e12 = reporte.cell(row=1, column=21, value='TD3')
        e12 = reporte.cell(row=1, column=22, value='Profundidad inicial')
        e12 = reporte.cell(row=1, column=23, value='Precio')
        e12 = reporte.cell(row=1, column=24, value='Min profundidad')
        e12 = reporte.cell(row=1, column=25, value='Prom')
        e12 = reporte.cell(row=1, column=26, value='%')
        e12 = reporte.cell(row=1, column=27, value='Dinero perdido 1')
        e12 = reporte.cell(row=1, column=28, value='Punto de retiro')
        e12 = reporte.cell(row=1, column=29, value='Pérdida total')

        FILE_PATH = os.path.abspath(os.getcwd()) + r"/aetoweb/files/files/Inspections_Bulk.csv"
        file = open(FILE_PATH, "r", encoding="latin-1", newline='')
        next(file, None)
        reader = csv.reader(file, delimiter=",")
        iteracion = 0

        for row in reader:
            if row[4][:10] in lista_fechas:
                iteracion += 1
                llanta = row[12]
                FILE_PATH = os.path.abspath(os.getcwd()) + r"/aetoweb/files/files/RollingStock2022_03_25_040126.csv"
                file2 = open(FILE_PATH, "r", encoding="latin-1", newline='')
                next(file2, None)
                reader2 = csv.reader(file2, delimiter=",")
                for row2 in reader2:
                    try:
                        llanta2 = row2[9]
                        if llanta == llanta2:

                            producto = row2[10]
                            FILE_PATH = os.path.abspath(os.getcwd()) + r"/aetoweb/files/files/Products2022_03_25_043513.csv"
                            file3 = open(FILE_PATH, "r", encoding="latin-1", newline='')
                            next(file3, None)
                            reader3 = csv.reader(file3, delimiter=",")
                            for row3 in reader3:
                                producto2 = row3[4]
                                if producto == producto2:
                                    profundidad_inicial = float(row3[10])
                                    precio = float(row3[12])


                            numero_de_eje = int(row2[17]) - 1
                            vehiculo = row2[6]
                            FILE_PATH = os.path.abspath(os.getcwd()) + "/aetoweb/files/files/Vehicles2022_03_25_043019.csv"
                            file4 = open(FILE_PATH, "r", encoding="latin-1", newline='')
                            next(file4, None)
                            reader4 = csv.reader(file4, delimiter=",")
                            for row4 in reader4:
                                vehiculo2 = row4[9]
                                if vehiculo == vehiculo2:
                                    configuracion = row4[14].split(".")
                                    if configuracion[numero_de_eje][0] == "S":
                                        punto_de_retiro = compania.punto_retiro_eje_direccion
                                    elif configuracion[numero_de_eje][0] == "D":
                                        punto_de_retiro = compania.punto_retiro_eje_traccion
                                    elif configuracion[numero_de_eje][0] == "T":
                                        punto_de_retiro = compania.punto_retiro_eje_arrastre
                                    elif configuracion[numero_de_eje][0] == "C":
                                        punto_de_retiro = compania.punto_retiro_eje_loco
                                    elif configuracion[numero_de_eje][0] == "L":
                                        punto_de_retiro = compania.punto_retiro_eje_retractil

                    except:
                        pass

                tds = [float(row[18]), float(row[19]), float(row[20])]
                min_profundidad = min(tds)
                prom = round(statistics.mean(tds), 2)
                try:
                    if profundidad_inicial == 0:
                        porcentaje = 0
                    else:
                        porcentaje = round((prom - min_profundidad) / profundidad_inicial, 2)
                except:
                    porcentaje = None
                    profundidad_inicial = None

                try:
                    if min_profundidad >= 1000:
                        dinero_perdido = 0
                    else:
                        dinero_perdido = round((precio * porcentaje), 2)
                except:
                    dinero_perdido = None
                    precio = None

                try:
                    perdida_total = round((min_profundidad - punto_de_retiro) * dinero_perdido)
                except:
                    perdida_total = None
                    punto_de_retiro = None

                column1 = reporte.cell(row=iteracion + 1, column=1)
                column1.value = row[0]
                column2 = reporte.cell(row=iteracion + 1, column=2)
                column2.value = row[1]
                column3 = reporte.cell(row=iteracion + 1, column=3)
                column3.value = row[2]
                column4 = reporte.cell(row=iteracion + 1, column=4)
                column4.value = row[3]
                column5 = reporte.cell(row=iteracion + 1, column=5)
                column5.value = row[4]
                column6 = reporte.cell(row=iteracion + 1, column=6)
                column6.value = row[5]
                column7 = reporte.cell(row=iteracion + 1, column=7)
                column7.value = row[6]
                column8 = reporte.cell(row=iteracion + 1, column=8)
                column8.value = row[7]
                column9 = reporte.cell(row=iteracion + 1, column=9)
                column9.value = row[8]
                column10 = reporte.cell(row=iteracion + 1, column=10)
                column10.value = row[9]
                column11 = reporte.cell(row=iteracion + 1, column=11)
                column11.value = row[10]
                column12 = reporte.cell(row=iteracion + 1, column=12)
                column12.value = row[11]
                column13 = reporte.cell(row=iteracion + 1, column=13)
                column13.value = row[12]
                column14 = reporte.cell(row=iteracion + 1, column=14)
                column14.value = row[13]
                column15 = reporte.cell(row=iteracion + 1, column=15)
                column15.value = row[14]
                column16 = reporte.cell(row=iteracion + 1, column=16)
                column16.value = row[15]
                column17 = reporte.cell(row=iteracion + 1, column=17)
                column17.value = row[16]
                column18 = reporte.cell(row=iteracion + 1, column=18)
                column18.value = row[17]
                column19 = reporte.cell(row=iteracion + 1, column=19)
                column19.value = row[18]
                column20 = reporte.cell(row=iteracion + 1, column=20)
                column20.value = row[19]
                column21 = reporte.cell(row=iteracion + 1, column=21)
                column21.value = row[20]
                column22 = reporte.cell(row=iteracion + 1, column=22)
                column22.value = profundidad_inicial
                column23 = reporte.cell(row=iteracion + 1, column=23)
                column23.value = precio
                column24 = reporte.cell(row=iteracion + 1, column=24)
                column24.value = min_profundidad
                column25 = reporte.cell(row=iteracion + 1, column=25)
                column25.value = prom
                column26 = reporte.cell(row=iteracion + 1, column=26)
                column26.value = porcentaje
                column27 = reporte.cell(row=iteracion + 1, column=27)
                column27.value = dinero_perdido
                column28 = reporte.cell(row=iteracion + 1, column=28)
                column28.value = punto_de_retiro
                column29 = reporte.cell(row=iteracion + 1, column=29)
                column29.value = perdida_total

        file.close()

        response = HttpResponse(content_type='application/ms-excel')

        #decide file name
        response['Content-Disposition'] = 'attachment; filename="InformePerdidaYRendimiento.xlsx"'

        wb.save(response)
        return response

def ftp_newpick(request):

    functions_ftp.ftp_descarga()
