# Django
from django.contrib.auth.models import User
from django.db import models

# Utilities
from datetime import date, datetime, timedelta

class Compania(models.Model):
    # Modelo de la Compañía

    compania = models.CharField(max_length=200, null=True)

    periodo1_inflado = models.IntegerField(default=30)
    periodo2_inflado = models.IntegerField(default=60)
    objetivo = models.IntegerField(default=10)
    periodo1_inspeccion = models.IntegerField(default=30)
    periodo2_inspeccion = models.IntegerField(default=60)
    opciones_unidades_presion = (("psi", "psi"),
                    ("bar", "bar"),
                    ("mPa", "mPa"),
                )
    opciones_unidades_distancia = (("km", "km"),
                    ("mi", "mi"),
                )
    opciones_unidades_profundidad = (("mm", "mm"),
                    ("32''", "32''"),
                )
    punto_retiro_eje_direccion = models.IntegerField(default=3)
    punto_retiro_eje_traccion = models.IntegerField(default=3)
    punto_retiro_eje_arrastre = models.IntegerField(default=3)
    punto_retiro_eje_loco = models.IntegerField(default=3)
    punto_retiro_eje_retractil = models.IntegerField(default=3)
    mm_de_desgaste_irregular = models.IntegerField(default=3)
    mm_de_diferencia_entre_duales = models.IntegerField(default=3)
    mm_parametro_sospechoso = models.FloatField(default=5)
    unidades_presion = models.CharField(max_length=200, choices=opciones_unidades_presion, default="psi")
    unidades_distancia = models.CharField(max_length=200, choices=opciones_unidades_distancia, default="km")
    unidades_profundidad = models.CharField(max_length=200, choices=opciones_unidades_profundidad, default="mm")
    valor_casco_nuevo = models.IntegerField(blank=True, null=True)
    valor_casco_1r = models.IntegerField(blank=True, null=True)
    valor_casco_2r = models.IntegerField(blank=True, null=True)
    valor_casco_3r = models.IntegerField(blank=True, null=True)
    valor_casco_4r = models.IntegerField(blank=True, null=True)
    valor_casco_5r = models.IntegerField(blank=True, null=True)
    def __str__(self):
        # Retorna el nombre de la compañía
        return f"{self.compania}"

class Ubicacion(models.Model):
    # Modelo de la Ubicación

    nombre = models.CharField(max_length=200, null=True)
    compania = models.ForeignKey(Compania, on_delete=models.CASCADE)
    rendimiento_de_nueva = models.IntegerField(default=80)
    rendimiento_de_primera = models.IntegerField(default=70)
    rendimiento_de_segunda = models.IntegerField(default=40)
    rendimiento_de_tercera = models.IntegerField(default=5)
    rendimiento_de_cuarta = models.IntegerField(default=0)
    precio_nueva = models.IntegerField(default=4000)
    precio_renovada = models.IntegerField(default=2000)
    precio_nueva_direccion = models.IntegerField(default=5500)

    def __str__(self):
        # Retorna el nombre de la ubicación
        return f"{self.nombre}"
    class Meta:
        verbose_name_plural = "Ubicaciones"
        
class Taller(models.Model):
    # Modelo del Taller

    nombre = models.CharField(max_length=200, null=True)
    compania = models.ForeignKey(Compania, on_delete=models.CASCADE)

    def __str__(self):
        # Retorna el nombre del taller
        return f"{self.nombre}"
    class Meta:
        verbose_name_plural = "Talleres"

class Aplicacion(models.Model):
    # Modelo de la Aplicación

    nombre = models.CharField(max_length=200, null=True)
    compania = models.ForeignKey(Compania, on_delete=models.CASCADE)
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.CASCADE, blank=True, null=True)
    def __str__(self):
        # Retorna el nombre de la aplicación
        return f"{self.nombre}"
    class Meta:
        verbose_name_plural = "Aplicaciones"


class Perfil(models.Model):
    # Modelo del Perfil de Usuario

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    compania = models.ForeignKey(Compania, on_delete=models.CASCADE)
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.CASCADE, blank=True, null=True)
    aplicacion = models.ForeignKey(Aplicacion, on_delete=models.CASCADE, blank=True, null=True)
    opciones_idioma = (("Español", "Español"), ("Inglés", "Inglés"))
    idioma = models.CharField(max_length=200, choices=opciones_idioma, default="Español")

    fecha_de_creacion = models.DateTimeField(auto_now_add=True)
    fecha_de_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Retorna el username
        return self.user.username
    class Meta:
        verbose_name_plural = "Perfiles"

class Vehiculo(models.Model):
    # Modelo del Vehiculo

    numero_economico = models.CharField(max_length=100)
    modelo = models.CharField(max_length=200, null=True, blank=True)
    marca = models.CharField(max_length=200, null=True, blank=True)
    compania = models.ForeignKey(Compania, on_delete=models.CASCADE)
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.CASCADE, blank=True, null=True)
    aplicacion = models.ForeignKey(Aplicacion, on_delete=models.CASCADE, blank=True, null=True)
    numero_de_llantas = models.PositiveIntegerField(default=8)
    opciones_clase = (("ARRASTRE", "Arrastre"),
                    ("TRUCK - BOX", "Truck - Box"),
                    ("VAN", "Van"),
                    ("TRACTOR - SLEEPER", "Tractor - Sleeper"),
                    ("TRACTOR - SLEEPER", "Tractor - Sleeper"),
                    ("TRUCK - DUMP", "Truck - Dump"),
                    ("TRAILER", "Trailer"),
                    ("AUTOBUS", "Autobus"),
                    ("AUTOMOVIL", "Automovil"),
                    ("AUTOTANQUE ALIMENTICIO", "Autotanque Alimenticio"),
                    ("AUTOTANQUE COMBUSTIBLE", "Autotanque Combustible"),
                    ("AUTOTANQUE QUIMICOS", "Autotanque Químicos"),
                    ("CAJA REFRIGERADO 48", "Caja Refrigerado 48"),
                    ("CAJA SECA", "Caja Seca"),
                    ("CAJA SECA 40", "Caja Seca 40"),
                    ("CAJA SECA 48", "Caja Seca 48"),
                    ("CAJA SECA 53", "Caja Seca 53"),
                    ("CAJA SECA 53 (3 EJES)", "Caja Seca 53 (3 Ejes)"),
                    ("CAMIÓN", "Camión"),
                    ("CAMIÓN - CAMAROTE", "Camión - Camarote"),
                    ("CAMIONETA", "Camioneta"),
                    ("CAMIONETA LIGERA", "Camioneta ligera"),
                    ("CORTINA", "Cortina"),
                    ("CORTINA 38", "Cortina 38"),
                    ("DOLLY", "Dolly"),
                    ("MOTOCICLETA", "Motocicleta"),
                    ("PICK-UP", "Pick-Up"),
                    ("PLATAFORMA 35", "Plataforma 35"),
                    ("PLATAFORMA 40", "Plataforma 40"),
                    ("PLATAFORMA 53", "Plataforma 53"),
                    ("PLATAFORMA 53 (3 EJES)", "Plataforma 53 (3 Ejes)"),
                    ("PORTACONTENEDOR", "Portacontenedor"),
                    ("RABON", "Rabon"),
                    ("REMOLQUE", "Remolque"),
                    ("REMOLQUE - CAJA SECA", "Remolque - Caja Seca"),
                    ("THERMOKING THORTON CAJA 25", "Thermoking Thorton Caja 25"),
                    ("TOLVA", "Tolva"),
                    ("TORTHON", "Torthon"),
                    ("TORTHON REFRIGERADO", "Torthon Refrigerado"),
                    ("TORTHON SECO", "Torthon Seco"),
                    ("TRACTOR", "Tractor"),
                    ("TRACTOCAMION", "Tractocamion"),
                    ("UTILITARIO TALLER", "Utilitario Taller"),
                    ("UTILITARIO ADMINISTRATIVO", "Utilitario Administrativo"),
                    ("YARD TRUCK", "Yard Truck")
                )
    clase = models.CharField(max_length=200, choices=opciones_clase, null=True, blank=True)
    opciones_configuracion = (("S2.D2", "S2.D2"),
                            ("S2.D2.D2", "S2.D2.D2"),
                            ("S2.D2.D2.T4.T4", "S2.D2.D2.T4.T4"),
                            ("S2.C4.D4", "S2.C4.D4"),
                            ("S2.D4", "S2.D4"),
                            ("S2.D4.SP1", "S2.D4.SP1"),
                            ("S2.D4.C4.SP1", "S2.D4.C4.SP1"),
                            ("S2.D4.D4", "S2.D4.D4"),
                            ("S2.D4.D4.D4", "S2.D4.D4.D4"),
                            ("S2.D4.D4.L2", "S2.D4.D4.L2"),
                            ("S2.D4.D4.SP1", "S2.D4.D4.SP1"),
                            ("S2.D4.D4.T4.T4", "S2.D4.D4.T4.T4"),
                            ("S2.D4.L4", "S2.D4.L4"),
                            ("S2.S2.D4", "S2.S2.D4"),
                            ("S2.L2.D4", "S2.L2.D4"),
                            ("S2.L2.D4.D4", "S2.L2.D4.D4"),
                            ("S2.L2.D4.D4.D2", "S2.L2.D4.D4.D2"),
                            ("S2.L2.D4.D4.L2", "S2.L2.D4.D4.L2"),
                            ("S2.L2.D4.D4.L4", "S2.L2.D4.D4.L4"),
                            ("S2.L2.L2.D4.D4", "S2.L2.L2.D4.D4"),
                            ("S2.L2.L2.D4.D4.L2", "S2.L2.L2.D4.D4.L2"),
                            ("S2.L2.L2.L2.D4.D4", "S2.L2.L2.L2.D4.D4"),
                            ("S2.L2.L2.L2.L2.D4.D4", "S2.L2.L2.L2.L2.D4.D4"),
                            ("S2.L4.D4", "S2.L4.D4"),
                            ("S2.L4.D4.D4", "S2.L4.D4.D4"),
                            ("T4.T4", "T4.T4"),
                            ("T4.T4.T4", "T4.T4.T4"),
                            ("T4.T4.SP1", "T4.T4.SP1")
                )
    configuracion = models.CharField(max_length=200, choices=opciones_configuracion, null=True, blank=True)
    fecha_de_inflado = models.DateField(null=True, blank=True)
    tiempo_de_inflado = models.FloatField(blank=True, null=True)
    presion_de_entrada = models.IntegerField(blank=True, null=True)
    presion_de_salida = models.IntegerField(blank=True, null=True)
    presion_establecida = models.IntegerField(blank=True, null=True, default=100)
    km = models.IntegerField(blank=True, null=True)
    ultima_bitacora_pro = models.ForeignKey("Bitacora_Pro", null=True, blank=True, on_delete=models.CASCADE, related_name="bitacoras_pro")
    ultima_inspeccion = models.ForeignKey("Inspeccion", null=True, blank=True, on_delete=models.CASCADE, related_name="inspecciones_vehiculo")
    tirecheck = models.BooleanField(default=False)

    fecha_de_creacion = models.DateField(auto_now_add=True)

    def __str__(self):
        # Retorna el número económico
        return f"{self.numero_economico}"

class Inspeccion(models.Model):
    # Modelo de la Inspección
    llanta = models.ForeignKey("Llanta", on_delete=models.CASCADE, related_name="related_llanta")
    fecha_hora = models.DateTimeField(null=True, blank=True)
    tiempo_de_inspeccion = models.FloatField(blank=True, null=True, default=2)
    km = models.IntegerField(default=1000)
    presion = models.IntegerField(null=True, blank=True)
    min_profundidad = models.IntegerField()
    max_profundidad = models.IntegerField()
    observacion_1 = models.CharField(max_length=200, null=True, blank=True)
    observacion_2 = models.CharField(max_length=200, null=True, blank=True)
    observacion_3 = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        # Retorna el número económico
        return f"{self.llanta}  |  {self.fecha_hora.strftime('%d-%m-%Y %H:%M:%S')}"
    class Meta:
        verbose_name_plural = "Inspecciones"

class Producto(models.Model):
    # Modelo de productos

    producto = models.CharField(max_length=100, null=True)
    marca = models.CharField(max_length=100, null=True, blank=True)
    dibujo = models.CharField(max_length=100, null=True, blank=True)
    rango = models.CharField(max_length=100, null=True, blank=True)
    dimension = models.CharField(max_length=100, null=True, blank=True)
    profundidad_inicial = models.IntegerField(null=True)

    opciones_aplicacion = (("Dirección", "Dirección"),
                        ("Tracción", "Tracción"),
                        ("Arrastre", "Arrastre"),
                        ("Mixta", "Mixta"),
                        ("Regional", "Regional"),
                        ("Urbano", "Urbano")
                      )
    aplicacion = models.CharField(max_length=100, choices= opciones_aplicacion, null=True, blank=True)

    opciones_vida = (("Nueva", "Nueva"),
                        ("Renovada", "Renovada"),
                        ("Vitacasco", "Vitacasco"),

                    )
    vida = models.CharField(max_length=100, choices=opciones_vida, null=True)
    precio = models.IntegerField(null=True)
    km_esperado = models.IntegerField(null=True, blank=True)

    def __str__(self):
    # Retorna el producto
       return f"{self.producto}"

class Llanta(models.Model):
    # Modelo de la Llanta

    numero_economico = models.CharField(max_length=200, null=True)
    usuario = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    compania = models.ForeignKey(Compania, on_delete=models.CASCADE, default=6)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, null=True, blank=True)
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.CASCADE, blank=True, null=True)
    opciones_vida = (("Nueva", "Nueva"),
                            ("1R", "1R"),
                            ("2R", "2R"),
                            ("3R", "3R"),
                            ("4R", "4R"),
                            ("5R", "5R"),
                )
    vida = models.CharField(max_length=200, choices=opciones_vida, null=True, blank=True, default="Nueva")
    tipo_de_eje = models.CharField(max_length=4, null=True, blank=True)
    eje = models.IntegerField(blank=True, null=True)
    posicion = models.CharField(max_length=4, null=True, blank=True)
    presion_de_entrada = models.IntegerField(blank=True, null=True)
    presion_de_salida = models.IntegerField(blank=True, null=True)
    presion_establecida = models.IntegerField(blank=True, null=True, default=100)
    fecha_de_inflado = models.DateField(null=True, blank=True)
    ultima_inspeccion = models.ForeignKey(Inspeccion, null=True, blank=True, on_delete=models.CASCADE, related_name="inspecciones")
    opciones_de_eje = (("Dirección", "Dirección"),
                        ("Tracción", "Tracción"),
                        ("Arrastre", "Arrastre"),
                        ("Loco", "Loco"),
                        ("Retractil", "Retractil")
                )
    nombre_de_eje = models.CharField(max_length=200, choices=opciones_de_eje, null=True, blank=True)
    producto = models.ForeignKey(Producto, null=True, blank=True, on_delete=models.CASCADE)
    opciones_de_inventario = (("Nueva", "Nueva"),
                        ("Antes de Renovar", "Antes de Renovar"),
                        ("Antes de Desechar", "Antes de Desechar"),
                        ("Renovada", "Renovada"),
                        ("Con renovador", "Con renovador"),
                        ("Desecho final", "Desecho final"),
                        ("Servicio", "Servicio"),
                        ("Rodante", "Rodante")
                )
    inventario = models.CharField(max_length=200, choices=opciones_de_inventario, null=True, blank=True, default="Rodante")
    km_montado = models.IntegerField(blank=True, null=True)
    tirecheck = models.BooleanField(default=False)
    archivado = models.BooleanField(default=False)

    def __str__(self):
        # Retorna el número económico
        return f"{self.numero_economico}"

class Bitacora(models.Model):
    # Modelo de la Bitácora

    numero_economico = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    compania = models.ForeignKey(Compania, on_delete=models.CASCADE)
    fecha_de_inflado = models.DateField(null=True, blank=True)
    tiempo_de_inflado = models.FloatField(blank=True, null=True, default=2)
    presion_de_entrada = models.IntegerField(blank=True, null=True, default=100)
    presion_de_salida = models.IntegerField(blank=True, null=True, default=100)
    presion_establecida = models.IntegerField(blank=True, null=True, default=100)

    def __str__(self):
        # Retorna el número económico
        return f"{self.numero_economico}"

class Bitacora_Pro(models.Model):
    # Modelo de la Bitácora del Pulpo Pro

    numero_economico = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    compania = models.ForeignKey(Compania, on_delete=models.CASCADE)
    fecha_de_inflado = models.DateField(null=True, blank=True)
    tiempo_de_inflado = models.FloatField(blank=True, null=True)
    presion_de_entrada_1 = models.IntegerField(blank=True, null=True)
    presion_de_salida_1 = models.IntegerField(blank=True, null=True)
    presion_de_entrada_2 = models.IntegerField(blank=True, null=True)
    presion_de_salida_2 = models.IntegerField(blank=True, null=True)
    presion_de_entrada_3 = models.IntegerField(blank=True, null=True)
    presion_de_salida_3 = models.IntegerField(blank=True, null=True)
    presion_de_entrada_4 = models.IntegerField(blank=True, null=True)
    presion_de_salida_4 = models.IntegerField(blank=True, null=True)
    presion_de_entrada_5 = models.IntegerField(blank=True, null=True)
    presion_de_salida_5 = models.IntegerField(blank=True, null=True)
    presion_de_entrada_6 = models.IntegerField(blank=True, null=True)
    presion_de_salida_6 = models.IntegerField(blank=True, null=True)
    presion_de_entrada_7 = models.IntegerField(blank=True, null=True)
    presion_de_salida_7 = models.IntegerField(blank=True, null=True)
    presion_de_entrada_8 = models.IntegerField(blank=True, null=True)
    presion_de_salida_8 = models.IntegerField(blank=True, null=True)
    presion_de_entrada_9 = models.IntegerField(blank=True, null=True)
    presion_de_salida_9 = models.IntegerField(blank=True, null=True)
    presion_de_entrada_10 = models.IntegerField(blank=True, null=True)
    presion_de_salida_10 = models.IntegerField(blank=True, null=True)
    presion_de_entrada_11 = models.IntegerField(blank=True, null=True)
    presion_de_salida_11 = models.IntegerField(blank=True, null=True)
    presion_de_entrada_12 = models.IntegerField(blank=True, null=True)
    presion_de_salida_12 = models.IntegerField(blank=True, null=True)

    def __str__(self):
        # Retorna el número económico
        return f"{self.numero_economico}"
    class Meta:
        verbose_name_plural = "Bitacoras Pro"

class Excel(models.Model):
    # Modelo del Excel
    compania = models.ForeignKey(Compania, on_delete=models.CASCADE)
    file = models.FileField(upload_to="files/", null=False)

class FTP(models.Model):
    file = models.CharField(max_length=200)

"""class Pulpo(models.Model):
    # Modelo del Pulpo
    compania = models.ForeignKey(Compania, on_delete=models.CASCADE)
    aplicaciones = models.ForeignKey(Aplicacion, on_delete=models.CASCADE)
    bitacoras = models.ForeignKey(Bitacora, on_delete=models.CASCADE)
    doble_entrada = models.JSONField(null=True, blank=True)
    cantidad_doble_entrada = models.JSONField(null=True, blank=True)
    cantidad_inflado = models.IntegerField(blank=True, null=True)
    cantidad_inflado_1 = models.IntegerField(blank=True, null=True)
    cantidad_inflado_2 = models.IntegerField(blank=True, null=True)
    cantidad_entrada = models.IntegerField(blank=True, null=True)
    cantidad_entrada_barras_mes1 = models.IntegerField(blank=True, null=True)
    cantidad_entrada_barras_mes2 = models.IntegerField(blank=True, null=True)
    cantidad_entrada_mes1 = models.IntegerField(blank=True, null=True)
    cantidad_entrada_mes2 = models.IntegerField(blank=True, null=True)
    cantidad_entrada_mes3 = models.IntegerField(blank=True, null=True)
    cantidad_entrada_mes4 = models.IntegerField(blank=True, null=True)
    cantidad_total = models.IntegerField(blank=True, null=True)
    clases_mas_frecuentes_infladas = models.JSONField(null=True, blank=True)
    flotas = models.ForeignKey(Ubicacion, on_delete=models.CASCADE)
    hoy = models.DateField(null=True, blank=True)"""

class TendenciaCPK(models.Model):
    # Modelo de la Tendencia CPK
    compania = models.ForeignKey(Compania, on_delete=models.CASCADE)
    mes = models.IntegerField()
    cpk = models.FloatField()
    cantidad = models.CharField(max_length=200)
    opciones_vida = (("Nueva", "Nueva"),
                        ("1R", "1R"),
                        ("2R", "2R"),
                        ("3R", "3R"),
                        ("4R", "4R"),
                        ("5R", "5R"),
            )
    vida = models.CharField(max_length=200, choices=opciones_vida)
    calificacion = models.IntegerField()

class Renovador(models.Model):
    # Modelo del Renovador
    nombre = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=200)
    marca = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = "Renovadores"

class Desecho(models.Model):
    # Modelo del Desecho
    llanta = models.ForeignKey(Llanta, on_delete=models.CASCADE)
    zona_de_llanta = models.CharField(max_length=200)
    condicion = models.CharField(max_length=200)
    razon = models.CharField(max_length=200)

class Observacion(models.Model):
    # Modelo de la Observación
    llanta = models.ForeignKey(Llanta, on_delete=models.CASCADE)
    observacion = models.CharField(max_length=200)
    opciones_de_color = (("Verde", "Verde"),
                ("Amarillo", "Amarillo"),
                ("Rojo", "Rojo"),
                ("Morado", "Morado"),
        )
    color = models.CharField(max_length=200, choices=opciones_de_color)
    
    class Meta:
        verbose_name_plural = "Observaciones"

class Rechazo(models.Model):
    # Modelo del Rechazo
    llanta = models.ForeignKey(Llanta, on_delete=models.CASCADE)
    razon = models.CharField(max_length=200)


class Bitacora_Edicion(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now=True)
    tipo = models.CharField(max_length=500)
    
    def __str__(self):
        # Retorna el número económico
        return f"{self.tipo} |{self.id} | {self.vehiculo} | {self.fecha.strftime('%Y %m %d')}"

class Registro_Bitacora(models.Model):
    bitacora = models.ForeignKey(Bitacora_Edicion, on_delete=models.CASCADE)
    evento = models.CharField(max_length=500)
    def __str__(self):
        # Retorna el número económico
        return f"{self.id} | {self.bitacora.vehiculo} | {self.evento}"