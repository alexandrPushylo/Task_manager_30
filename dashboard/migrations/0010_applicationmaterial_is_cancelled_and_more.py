# Generated by Django 4.1 on 2024-03-31 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0009_alter_applicationtoday_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicationmaterial',
            name='is_cancelled',
            field=models.BooleanField(default=False, verbose_name='Отменена?'),
        ),
        migrations.AddField(
            model_name='applicationtechnic',
            name='is_cancelled',
            field=models.BooleanField(default=False, verbose_name='Отменена?'),
        ),
    ]