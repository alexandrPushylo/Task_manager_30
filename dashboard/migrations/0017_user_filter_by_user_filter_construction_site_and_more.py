# Generated by Django 4.1 on 2024-05-05 11:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0016_user_is_show_material_app_user_is_show_technic_app'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='filter_by',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Фильтр по:'),
        ),
        migrations.AddField(
            model_name='user',
            name='filter_construction_site',
            field=models.IntegerField(default=0, verbose_name='Фильтр по строительному объекту'),
        ),
        migrations.AddField(
            model_name='user',
            name='filter_foreman',
            field=models.IntegerField(default=0, verbose_name='Фильтр по строительному объекту'),
        ),
    ]