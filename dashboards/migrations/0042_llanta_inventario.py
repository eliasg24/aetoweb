# Generated by Django 3.0.4 on 2022-02-27 03:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0041_remove_llanta_inventario'),
    ]

    operations = [
        migrations.AddField(
            model_name='llanta',
            name='inventario',
            field=models.CharField(blank=True, choices=[('Nueva', 'Nueva'), ('Antes de Renovar', 'Antes de Renovar'), ('Antes de Desechar', 'Antes de Desechar'), ('Renovada', 'Renovada'), ('Con renovador', 'Con renovador'), ('Desecho final', 'Desecho final'), ('Servicio', 'Servicio'), ('Rodante', 'Rodante')], default='Rodante', max_length=200, null=True),
        ),
    ]
