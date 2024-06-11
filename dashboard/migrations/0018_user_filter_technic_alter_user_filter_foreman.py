# Generated by Django 4.1 on 2024-05-05 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0017_user_filter_by_user_filter_construction_site_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='filter_technic',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Фильтр по технике'),
        ),
        migrations.AlterField(
            model_name='user',
            name='filter_foreman',
            field=models.IntegerField(default=0, verbose_name='Фильтр по прорабу'),
        ),
    ]