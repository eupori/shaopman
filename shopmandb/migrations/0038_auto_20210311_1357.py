# Generated by Django 3.1.1 on 2021-03-11 13:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopmandb', '0037_auto_20210311_1103'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shipping',
            name='sheep_fee',
        ),
        migrations.AddField(
            model_name='shipping',
            name='ship_fee',
            field=models.PositiveIntegerField(blank=True, max_length=100, null=True, verbose_name=''),
        ),
        migrations.AlterField(
            model_name='shipping',
            name='airport_fee',
            field=models.PositiveIntegerField(blank=True, max_length=100, null=True, verbose_name=''),
        ),
    ]