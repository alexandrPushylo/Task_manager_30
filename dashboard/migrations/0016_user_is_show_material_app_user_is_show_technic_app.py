# Generated by Django 4.1 on 2024-04-27 15:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0015_user_is_show_absent_app_user_is_show_saved_app'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_show_material_app',
            field=models.BooleanField(default=True, verbose_name='Показывать заявки на материалы'),
        ),
        migrations.AddField(
            model_name='user',
            name='is_show_technic_app',
            field=models.BooleanField(default=True, verbose_name='Показывать заявки на технику'),
        ),
    ]
