# Generated by Django 4.0.3 on 2022-06-16 23:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0024_merge_20220605_1934'),
    ]

    operations = [
        migrations.AddField(
            model_name='llanta',
            name='fecha_de_balanceado',
            field=models.DateField(blank=True, null=True),
        ),
    ]
