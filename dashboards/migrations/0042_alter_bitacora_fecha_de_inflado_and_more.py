# Generated by Django 4.0.3 on 2022-07-10 23:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0041_alter_llanta_nombre_de_eje'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bitacora',
            name='fecha_de_inflado',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='bitacora_pro',
            name='fecha_de_inflado',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='llanta',
            name='fecha_de_inflado',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vehiculo',
            name='fecha_de_inflado',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
