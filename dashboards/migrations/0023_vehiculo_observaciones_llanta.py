# Generated by Django 4.0.3 on 2022-06-05 20:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0022_merge_20220604_2218'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehiculo',
            name='observaciones_llanta',
            field=models.ManyToManyField(blank=True, limit_choices_to={'nivel': 'Llanta'}, null=True, related_name='observaciones_llanta', to='dashboards.observacion'),
        ),
    ]
