# Generated by Django 4.1 on 2024-04-04 10:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0010_applicationmaterial_is_cancelled_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicationtoday',
            name='construction_site',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.constructionsite', verbose_name='Строительный объект'),
        ),
    ]