# Generated by Django 5.0.6 on 2024-07-05 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0025_parameter_permissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicationtoday',
            name='is_application_send',
            field=models.BooleanField(default=False, verbose_name='Заявка отправлена?'),
        ),
        migrations.AddField(
            model_name='workdaysheet',
            name='is_all_application_send',
            field=models.BooleanField(default=False, verbose_name='Заявки отправлены?'),
        ),
    ]
