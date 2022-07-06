# Generated by Django 4.0.3 on 2022-05-26 23:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0007_llantasseleccionadas_inventario'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehiculo',
            name='configuracion',
            field=models.CharField(blank=True, choices=[('S1.D1', 'S1.D1'), ('S2.D2', 'S2.D2'), ('S2.D2.D2', 'S2.D2.D2'), ('S2.D2.D2.T4.T4', 'S2.D2.D2.T4.T4'), ('S2.D2.SP1', 'S2.D2.SP1'), ('S2.C4.D4', 'S2.C4.D4'), ('S2.D4', 'S2.D4'), ('S2.D4.SP1', 'S2.D4.SP1'), ('S2.D4.C4.SP1', 'S2.D4.C4.SP1'), ('S2.D4.D4', 'S2.D4.D4'), ('S2.D4.D4.D4', 'S2.D4.D4.D4'), ('S2.D4.D4.L2', 'S2.D4.D4.L2'), ('S2.D4.D4.SP1', 'S2.D4.D4.SP1'), ('S2.D4.D4.T4.T4', 'S2.D4.D4.T4.T4'), ('S2.D4.L4', 'S2.D4.L4'), ('S2.S2.D4', 'S2.S2.D4'), ('S2.L2.D4', 'S2.L2.D4'), ('S2.L2.D4.D4', 'S2.L2.D4.D4'), ('S2.L2.D4.D4.D2', 'S2.L2.D4.D4.D2'), ('S2.L2.D4.D4.L2', 'S2.L2.D4.D4.L2'), ('S2.L2.D4.D4.L4', 'S2.L2.D4.D4.L4'), ('S2.L2.L2.D4.D4', 'S2.L2.L2.D4.D4'), ('S2.L2.L2.D4.D4.L2', 'S2.L2.L2.D4.D4.L2'), ('S2.L2.L2.L2.D4.D4', 'S2.L2.L2.L2.D4.D4'), ('S2.L2.L2.L2.L2.D4.D4', 'S2.L2.L2.L2.L2.D4.D4'), ('S2.L4.D4', 'S2.L4.D4'), ('S2.L4.D4.D4', 'S2.L4.D4.D4'), ('T4.T4', 'T4.T4'), ('T4.T4.T4', 'T4.T4.T4'), ('T4.T4.SP1', 'T4.T4.SP1'), ('T4.T4.SP2', 'T4.T4.SP2'), ('T4.T4.T4.SP2', 'T4.T4.T4.SP2')], max_length=200, null=True),
        ),
    ]