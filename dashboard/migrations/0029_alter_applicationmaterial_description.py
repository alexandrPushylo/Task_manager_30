# Generated by Django 5.0.6 on 2024-07-24 17:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0028_applicationtoday_is_edited'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicationmaterial',
            name='description',
            field=models.TextField(max_length=4096, verbose_name='Описание'),
        ),
    ]