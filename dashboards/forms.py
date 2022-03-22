# Django
from django import forms

# Models
from dashboards.models import Vehiculo, Excel, Llanta, Producto

class LlantaForm(forms.ModelForm):
    # Model form del Llanta
    class Meta:
        # Configuración del Form
        model = Llanta
        fields = ("numero_economico",)

class VehiculoForm(forms.ModelForm):
    # Model form del Vehiculo
    class Meta:
        # Configuración del Form
        model = Vehiculo
        fields = ("numero_economico",)

class ExcelForm(forms.ModelForm):
    # Model form del Excel
    class Meta:
        # Configuración del Form
        model = Excel
        fields = ("file",)

class ProductoForm(forms.ModelForm):
    # Model form del Producto
    class Meta:
        # Configuración del Form
        model = Producto
        fields = ["producto", 'marca', 'dibujo', 'rango', 'dimension', 'profundidad_inicial', 'aplicacion', 'vida', 'precio', 'km_esperado']
