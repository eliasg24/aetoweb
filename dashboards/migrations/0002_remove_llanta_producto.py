# Generated by Django 3.0.4 on 2021-11-04 19:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='llanta',
            name='producto',
        ),
    ]