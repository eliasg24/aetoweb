# Generated by Django 3.2.9 on 2022-01-24 21:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0033_auto_20220124_1500'),
    ]

    operations = [
        migrations.RenameField(
            model_name='llanta',
            old_name='nombre_producto',
            new_name='producto',
        ),
    ]