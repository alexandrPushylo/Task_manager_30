# Generated by Django 4.1 on 2024-03-23 16:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_alter_technic_supervisor_technic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='driversheet',
            name='date',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.workdaysheet', verbose_name='Дата'),
        ),
    ]
