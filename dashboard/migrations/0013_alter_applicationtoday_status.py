# Generated by Django 4.1 on 2024-04-06 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0012_technicsheet_count_application'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicationtoday',
            name='status',
            field=models.CharField(blank=True, default='saved', max_length=255, null=True, verbose_name='Статус заявки'),
        ),
    ]
