# Generated by Django 4.0.3 on 2022-04-05 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0068_merge_20220404_2348'),
    ]

    operations = [
        migrations.AddField(
            model_name='inspeccion',
            name='presion',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
