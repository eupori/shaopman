# Generated by Django 3.1.1 on 2021-02-25 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopmandb', '0023_auto_20210222_1254'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='구독 활성화 여부'),
        ),
    ]
