# Generated by Django 5.0.6 on 2024-07-06 10:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0026_applicationtoday_is_application_send_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='applicationtoday',
            options={'ordering': ['date', 'construction_site'], 'verbose_name': 'Заявка на объект', 'verbose_name_plural': 'Заявки на объект'},
        ),
    ]
