import json
from django.http import HttpResponse
from django.views.generic.base import View
from django.contrib.auth.models import User, Group

from dashboards.models import Perfil, Vehiculo, Compania, Ubicacion, Aplicacion, Taller


class VehicleData(View):
    def get(self, request , *args, **kwargs):
        #Queryparams
        usuario = kwargs['usuario']
        user = User.objects.get(username = usuario)
        perfil = Perfil.objects.get(user = user)
        compania = perfil.compania
        vehiculos = Vehiculo.objects.filter(compania=compania)
        #Serializar data
        vehiculos = list(vehiculos.values())
        
        dict_context = {
            'vehiculos': vehiculos,
        }

        json_context = json.dumps(dict_context, indent=None, sort_keys=False, default=str)

        return HttpResponse(json_context, content_type='application/json')

class CompaniaData(View):
    def get(self, request , *args, **kwargs):
        #Queryparams
        usuario = kwargs['usuario']
        user = User.objects.get(username = usuario)
        perfil = Perfil.objects.get(user = user)
        compania = perfil.compania
        compania = Compania.objects.filter(compania=compania)
        #Serializar data
        print(compania)
        compania = list(compania.values())
        print(compania)
        
        dict_context = {
            'compania': compania,
        }

        json_context = json.dumps(dict_context, indent=None, sort_keys=False, default=str)

        return HttpResponse(json_context, content_type='application/json')

class SucursalData(View):
    def get(self, request , *args, **kwargs):
        #Queryparams
        usuario = kwargs['usuario']
        user = User.objects.get(username = usuario)
        perfil = Perfil.objects.get(user = user)
        compania = perfil.compania
        sucursales = Ubicacion.objects.filter(compania=compania)
        #Serializar data
        print(sucursales)
        sucursales = list(sucursales.values())
        print(sucursales)
        
        dict_context = {
            'sucursales': sucursales,
        }

        json_context = json.dumps(dict_context, indent=None, sort_keys=False, default=str)

        return HttpResponse(json_context, content_type='application/json')

class AplicacionData(View):
    def get(self, request , *args, **kwargs):
        #Queryparams
        usuario = kwargs['usuario']
        user = User.objects.get(username = usuario)
        perfil = Perfil.objects.get(user = user)
        compania = perfil.compania
        aplicaciones = Aplicacion.objects.filter(compania=compania)
        #Serializar data
        print(aplicaciones)
        aplicaciones = list(aplicaciones.values())
        print(aplicaciones)
        
        dict_context = {
            'aplicaciones': aplicaciones,
        }

        json_context = json.dumps(dict_context, indent=None, sort_keys=False, default=str)

        return HttpResponse(json_context, content_type='application/json')

class TallerData(View):
    def get(self, request , *args, **kwargs):
        #Queryparams
        usuario = kwargs['usuario']
        user = User.objects.get(username = usuario)
        perfil = Perfil.objects.get(user = user)
        compania = perfil.compania
        talleres = Taller.objects.filter(compania=compania)
        #Serializar data
        print(talleres)
        talleres = list(talleres.values())
        print(talleres)
        
        dict_context = {
            'talleres': talleres,
        }

        json_context = json.dumps(dict_context, indent=None, sort_keys=False, default=str)

        return HttpResponse(json_context, content_type='application/json')

class PerfilData(View):
    def get(self, request , *args, **kwargs):
        #Queryparams
        usuario = kwargs['usuario']
        user = User.objects.get(username = usuario)
        perfil = Perfil.objects.filter(user = user)
        #Serializar data
        print(perfil)
        perfil = list(perfil.values())
        print(perfil)
        
        dict_context = {
            'perfil': perfil,
        }

        json_context = json.dumps(dict_context, indent=None, sort_keys=False, default=str)

        return HttpResponse(json_context, content_type='application/json')