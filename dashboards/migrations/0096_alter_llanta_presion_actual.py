# Generated by Django 4.0.3 on 2022-04-20 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0095_alter_vehiculo_configuracion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='llanta',
            name='presion_actual',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]