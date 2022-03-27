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
from dashboards.forms import ExcelForm, LlantaForm, VehiculoForm, ProductoForm, RenovadorForm, DesechoForm, DesechoEditForm, ObservacionForm, ObservacionEditForm, RechazoForm, RechazoEditForm, SucursalForm, TallerForm, UsuarioForm, AplicacionForm, CompaniaForm, UsuarioEditForm

# Models
from django.contrib.auth.models import User, Group
from dashboards.models import Aplicacion, Bitacora_Pro, Inspeccion, Llanta, Producto, Ubicacion, Vehiculo, Perfil, Bitacora, Compania, Renovador, Desecho, Observacion, Rechazo, User

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

        reemplazo_dual = functions.reemplazo_dual(llantas, reemplazo_actual_llantas)
        reemplazo_total = functions.reemplazo_total(reemplazo_actual_ejes, reemplazo_dual)

        print("llantas", llantas)
        print("reemplazo_actual_llantas", reemplazo_actual_llantas)
        print("reemplazo_actual", reemplazo_actual)
        print("reemplazo_dual", reemplazo_dual)

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

            valores_producto.append(km_proyectado_producto)
            valores_producto.append(km_x_mm_producto)
            valores_producto.append(cpk_producto)
            valores_producto.append(cantidad)
            valores_producto.append(desgaste)
            valores_producto.append(porcentaje_analizadas)
            valores_producto.append(producto.dibujo)

            comparativa_de_productos[producto] = valores_producto

            km_productos[producto] = regresion_producto[0]
            cpk_productos[producto] = regresion_producto[3]

            
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

        print("comparativa_de_flotas", comparativa_de_flotas)
        print("comparativa_de_posiciones", comparativa_de_posiciones)

        cpk_vehiculos =  functions.cpk_vehiculo_cantidad(cpk_vehiculos)
        cpk_flotas =  functions.distribucion_cantidad(cpk_flotas)
        cpk_aplicaciones =  functions.distribucion_cantidad(cpk_aplicaciones)
        cpk_productos =  functions.distribucion_cantidad(cpk_productos)

        km_flotas =  functions.distribucion_cantidad(km_flotas)
        km_aplicaciones = functions.distribucion_cantidad(km_aplicaciones)
        km_productos = functions.distribucion_cantidad(km_productos)

        context["aplicacion1"] = aplicacion1
        context["aplicacion2"] = aplicacion2
        context["aplicaciones"] = aplicaciones
        context["clase1"] = clase1
        context["clase2"] = clase2
        context["clases"] = clases
        print(self.request.user.perfil.compania)
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

class reporteLlantaView(LoginRequiredMixin, DetailView):
    # Vista de reporteLlantaView

    template_name = "reporteLlanta.html"
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

        #functions_excel.excel_inspecciones()
        #functions_excel.excel_inspecciones()
        #functions_excel.agregarExcel()
        #functions_ftp.ftp()
        #functions_ftp.ftp_1()
        #functions_ftp.ftp2(self.request.user.perfil)
        ultimo_mes = hoy - timedelta(days=31)

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
    fecha1 = request.GET.get("fechaInicio")
    fecha2 = request.GET.get("fechaFin")
    flota = request.GET.get("flota")
    boton_intuitivo = request.GET.get("boton_intuitivo")


    # Buscar por fecha
    if fecha1 and fecha2:
        
        # Definir si se toma en cuenta el mes, la semana o el día
        
        
        fecha1 = functions.convertir_rango(fecha1)
        fecha2 = functions.convertir_rango(fecha2)
        primera_fecha = datetime.strptime(fecha1, "%Y/%m/%d").date()
        segunda_fecha = datetime.strptime(fecha2, "%Y/%m/%d").date()
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
        fecha_con_formato1 = functions.convertir_fecha(fecha1)
        fecha_con_formato2 = functions.convertir_fecha(fecha2)

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
                                            "compania": request.user.perfil.compania,
                                            "fecha1":fecha1,
                                            "fecha2":fecha2,
                                            "fecha_con_formato1":fecha_con_formato1,
                                            "fecha_con_formato2":fecha_con_formato2,
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
        fecha_con_formato1 = functions.convertir_fecha(fecha1)
        fecha_con_formato2 = functions.convertir_fecha(fecha2)

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
                                            "compania": request.user.perfil.compania,
                                            "fecha1":fecha1,
                                            "fecha2":fecha2,
                                            "fecha_con_formato1":fecha_con_formato1,
                                            "fecha_con_formato2":fecha_con_formato2,
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
        fecha_con_formato = functions.convertir_fecha(fecha1)

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
                                            "compania": request.user.perfil.compania,
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
        fecha_con_formato = functions.convertir_fecha(fecha1)

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
                                            "compania": request.user.perfil.compania,
                                            "fecha1":fecha1,
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

class ConfigView(LoginRequiredMixin, MultiModelFormView):
    # Vista del dashboard configuración
    template_name = "config.html"
    form_classes = {"companiaform": CompaniaForm,
                    "usuarioform": UsuarioEditForm}
    success_url = reverse_lazy('dashboards:config')

    def forms_valid(self, form):
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
        
        return super(ConfigView, self).forms_valid(form)

    def get_context_data(self, **kwargs):

        context = super(ConfigView, self).get_context_data(**kwargs)
        context.update({"some_context_value": 'blah blah blah',
                "some_other_context_value": 'blah'})
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
        
        print(vehiculos)
        print(bitacora)
        print(llantas)
        print(inspecciones)

        filtro_sospechoso = functions.vehiculo_sospechoso(inspecciones)
        vehiculos_sospechosos = vehiculos.filter(id__in=filtro_sospechoso)

        doble_entrada = functions.doble_mala_entrada(bitacora, vehiculos)
        filtro_rojo = functions.vehiculo_rojo(llantas, doble_entrada, vehiculos)
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
    print(fecha)
    if num:
        vehiculos = Vehiculo.objects.filter(numero_economico__icontains=num, compania=Compania.objects.get(compania=request.user.perfil.compania))
        bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania))
        inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania))
        
        filtro_sospechoso = functions.vehiculo_sospechoso(inspecciones)
        vehiculos_sospechosos = vehiculos.filter(id__in=filtro_sospechoso)

        doble_entrada = functions.doble_mala_entrada(bitacora, vehiculos)
        filtro_rojo = functions.vehiculo_rojo(llantas, doble_entrada, vehiculos)
        vehiculos_rojos = vehiculos.filter(id__in=filtro_rojo).exclude(id__in=vehiculos_sospechosos)

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

        vehiculos = Vehiculo.objects.filter(fecha_de_inflado__range=[primera_fecha, segunda_fecha], compania=Compania.objects.get(compania=request.user.perfil.compania))
        bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania))
        inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania))
        
        filtro_sospechoso = functions.vehiculo_sospechoso(inspecciones)
        vehiculos_sospechosos = vehiculos.filter(id__in=filtro_sospechoso)

        doble_entrada = functions.doble_mala_entrada(bitacora, vehiculos)
        filtro_rojo = functions.vehiculo_rojo(llantas, doble_entrada, vehiculos)
        vehiculos_rojos = vehiculos.filter(id__in=filtro_rojo).exclude(id__in=vehiculos_sospechosos)

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

        vehiculos = Vehiculo.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
        bitacora = Bitacora.objects.filter(compania=Compania.objects.get(compania=request.user.perfil.compania))
        llantas = Llanta.objects.filter(vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania))
        inspecciones = Inspeccion.objects.filter(llanta__vehiculo__compania=Compania.objects.get(compania=request.user.perfil.compania))
        
        filtro_sospechoso = functions.vehiculo_sospechoso(inspecciones)
        vehiculos_sospechosos = vehiculos.filter(id__in=filtro_sospechoso)

        doble_entrada = functions.doble_mala_entrada(bitacora, vehiculos)
        filtro_rojo = functions.vehiculo_rojo(llantas, doble_entrada, vehiculos)
        vehiculos_rojos = vehiculos.filter(id__in=filtro_rojo).exclude(id__in=vehiculos_sospechosos)

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
            if cantidad_llantas >= 2:
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
        plt.savefig(os.path.abspath(os.getcwd()) + r"\files\files\ComparacionFlotas.png", dpi = 70, bbox_inches="tight")

        img_flotas = openpyxl.drawing.image.Image(os.path.abspath(os.getcwd()) + r"\files\files\ComparacionFlotas.png")

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
        plt.savefig(os.path.abspath(os.getcwd()) + r"\files\files\ComparacionAplicaciones.png", dpi = 70, bbox_inches="tight")

        img_aplicaciones = openpyxl.drawing.image.Image(os.path.abspath(os.getcwd()) + r"\files\files\ComparacionAplicaciones.png")

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
        plt.savefig(os.path.abspath(os.getcwd()) + r"\files\files\ComparacionEjes.png", dpi = 70, bbox_inches="tight")

        img_ejes = openpyxl.drawing.image.Image(os.path.abspath(os.getcwd()) + r"\files\files\ComparacionEjes.png")

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
        plt.savefig(os.path.abspath(os.getcwd()) + r"\files\files\ComparacionProductos.png", dpi = 70, bbox_inches="tight")

        img_producto = openpyxl.drawing.image.Image(os.path.abspath(os.getcwd()) + r"\files\files\ComparacionProductos.png")

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
        plt.savefig(os.path.abspath(os.getcwd()) + r"\files\files\ComparacionClases.png", dpi = 70, bbox_inches="tight")

        img_clases = openpyxl.drawing.image.Image(os.path.abspath(os.getcwd()) + r"\files\files\ComparacionClases.png")

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

        FILE_PATH = os.path.abspath(os.getcwd()) + r"\files\files\Inspections_Bulk.csv"
        file = open(FILE_PATH, "r", encoding="latin-1", newline='')
        next(file, None)
        reader = csv.reader(file, delimiter=",")
        iteracion = 0

        for row in reader:
            if row[4][:10] in lista_fechas:
                iteracion += 1
                llanta = row[12]
                FILE_PATH = os.path.abspath(os.getcwd()) + r"\files\files\RollingStock2022_03_25_040126.csv"
                file2 = open(FILE_PATH, "r", encoding="latin-1", newline='')
                next(file2, None)
                reader2 = csv.reader(file2, delimiter=",")
                for row2 in reader2:
                    try:
                        llanta2 = row2[9]
                        if llanta == llanta2:

                            producto = row2[10]
                            FILE_PATH = os.path.abspath(os.getcwd()) + r"\files\files\Products2022_03_25_043513.csv"
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
                            FILE_PATH = os.path.abspath(os.getcwd()) + r"\files\files\Vehicles2022_03_25_043019.csv"
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
                        porcentaje = round((prom - min_profundidad) * profundidad_inicial, 2)
                except:
                    porcentaje = None
                    profundidad_inicial = None
                
                try:
                    if min_profundidad >= 1000:
                        dinero_perdido = 0
                    else:
                        dinero_perdido = round((precio * porcentaje) / 100, 2)
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