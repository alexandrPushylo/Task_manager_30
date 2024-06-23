# Generated by Django 4.1 on 2024-06-16 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0022_workdaysheet_is_only_read'),
    ]

    operations = [
        migrations.AddField(
            model_name='parameter',
            name='name',
            field=models.CharField(default='as', max_length=256, verbose_name='Имя переменной'),
        ),
        migrations.AlterField(
            model_name='parameter',
            name='title',
            field=models.CharField(blank=True, max_length=256, null=True, verbose_name='Название переменной'),
        ),
    ]