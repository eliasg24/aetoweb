# Generated by Django 3.0.4 on 2021-11-19 21:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0015_auto_20211119_1542'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inspeccion',
            name='max_profundidad',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='inspeccion',
            name='min_profundidad',
            field=models.IntegerField(),
        ),
    ]