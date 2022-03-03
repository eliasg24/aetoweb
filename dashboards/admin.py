# Django
from django.apps import AppConfig
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin

# Models
from django.contrib.auth.models import User
from django.db.models.fields.related import RelatedField
from dashboards.models import Aplicacion, Bitacora_Pro, Compania, Excel, FTP, Ubicacion, Vehiculo, Perfil, Bitacora, Llanta, Inspeccion, Producto

@admin.register(Bitacora)
class BitacorasAdmin(admin.ModelAdmin):
    # Admin de las Bitácoras
    list_display = ('numero_economico', 'presion_de_entrada', 'presion_de_salida', 'compania', 'fecha_de_inflado')
    search_fields= ('numero_economico',)
    list_filter = ('fecha_de_inflado', 'compania')
    def clase(self, obj):
        if obj.vehiculo:
            return obj.vehiculo.clase

@admin.register(Bitacora_Pro)
class BitacorasProAdmin(admin.ModelAdmin):
    # Admin de las Bitácoras
    list_display = ('numero_economico', 'presion_de_entrada_1', 'presion_de_salida_1', 'compania', 'fecha_de_inflado')
    search_fields= ('numero_economico',)
    list_filter = ('fecha_de_inflado', 'compania')
    verbose_name_plural = "Bitacoras Pro"


@admin.register(Ubicacion)
class UbicacionesAdmin(admin.ModelAdmin):
    # Admin de las Ubicaciones
    list_display = ('nombre', 'compania', 'rendimiento_de_nueva', 'rendimiento_de_primera', 'rendimiento_de_segunda', 'rendimiento_de_tercera', 'rendimiento_de_cuarta')
    search_fields= ('nombre',)
    list_filter = ('compania',)

@admin.register(Aplicacion)
class AplicacionesAdmin(admin.ModelAdmin):
    # Admin de las Aplicaciones
    list_display = ('nombre', 'compania')
    search_fields= ('nombre',)
    list_filter = ('compania',)


@admin.register(Vehiculo)
class VehiculosAdmin(admin.ModelAdmin):
    # Admin de los Vehículos
    list_display = ('numero_economico', 'clase', 'ubicacion', 'aplicacion', 'ultima_inspeccion', 'fecha_de_creacion')
    search_fields= ('numero_economico',)
    list_filter = ('compania', 'fecha_de_creacion', 'clase')

@admin.register(Llanta)
class LlantasAdmin(admin.ModelAdmin):
    # Admin de las Llantas
    list_display = ('id', 'numero_economico', 'ultima_inspeccion', 'nombre_de_eje', 'min_profundidad', 'vida', 'tipo_de_eje', 'eje', 'posicion', 'producto',)
    search_fields= ('numero_economico',)
    list_filter = ('vehiculo__compania', 'tipo_de_eje')
    def min_profundidad(self, obj):
        if obj.ultima_inspeccion:
            return obj.ultima_inspeccion.min_profundidad
    def max_profundidad(self, obj):
        if obj.ultima_inspeccion:
            return obj.ultima_inspeccion.max_profundidad

@admin.register(Inspeccion)
class InspeccionesAdmin(admin.ModelAdmin):
    # Admin de las Inspecciones
    list_display = ('llanta', 'fecha_hora', "km", 'min_profundidad', 'max_profundidad')
    search_fields= ('llanta',)
    list_filter = ('llanta',)
    def get_view_count(self, obj):
        return obj.llanta.producto

@admin.register(Excel)
class ExcelAdmin(admin.ModelAdmin):
    # Admin del Excel
    list_display = ('id', 'file')

@admin.register(FTP)
class FTPAdmin(admin.ModelAdmin):
    # Admin del FTP
    list_display = ('file',)

@admin.register(Compania)
class CompaniaAdmin(admin.ModelAdmin):
    # Admin del Perfil
    list_display = ('id', 'compania')
    search_fields= ('compania',)

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    # Admin del Perfil
    list_display = ('user', 'compania', 'fecha_de_creacion',)
    list_filter = ('fecha_de_creacion',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    #Admin de productos
    list_display = ('producto', 'marca', 'profundidad_inicial', 'aplicacion', 'vida', 'precio', 'costo_por_km', 'km_proyectado',)
    search_fields = ('producto',)
    list_filter = ('marca','aplicacion', 'vida',)

class ProfileInline(admin.StackedInline):
    # Alinear el admin del perfil con el de User de Django
    model = Perfil
    can_delete = False
    verbose_name_plural = "perfiles"

class UserAdmin(BaseUserAdmin):
    # Agregar el admin del perfil al admin del User de Django
    inlines = (ProfileInline,)
    list_display = ("username", "email", "is_active")

admin.site.unregister(User)
admin.site.register(User, UserAdmin)