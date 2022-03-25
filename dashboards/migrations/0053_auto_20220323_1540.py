# Generated by Django 3.0.4 on 2022-03-23 21:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0052_auto_20220322_1904'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='observacion',
            options={'verbose_name_plural': 'Observaciones'},
        ),
        migrations.AddField(
            model_name='compania',
            name='valor_casco_1r',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='compania',
            name='valor_casco_2r',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='compania',
            name='valor_casco_3r',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='compania',
            name='valor_casco_4r',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='compania',
            name='valor_casco_5r',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='compania',
            name='valor_casco_nuevo',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
