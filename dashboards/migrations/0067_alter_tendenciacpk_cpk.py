# Generated by Django 4.0.3 on 2022-04-05 00:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0066_tendenciacpk'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tendenciacpk',
            name='cpk',
            field=models.FloatField(),
        ),
    ]