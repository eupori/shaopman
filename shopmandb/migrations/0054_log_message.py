# Generated by Django 3.1.1 on 2021-04-01 10:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopmandb', '0053_auto_20210329_1309'),
    ]

    operations = [
        migrations.AddField(
            model_name='log',
            name='message',
            field=models.TextField(blank=True, verbose_name='메시지'),
        ),
    ]
