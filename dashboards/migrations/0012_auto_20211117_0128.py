# Generated by Django 3.0.4 on 2021-11-17 07:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0011_auto_20211117_0114'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vehiculo',
            name='fecha_hora_de_inspeccion',
        ),
        migrations.AddField(
            model_name='vehiculo',
            name='ultima_inspeccion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inspecciones_vehiculo', to='dashboards.Inspeccion'),
        ),
    ]
