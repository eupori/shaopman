# Generated by Django 3.1.1 on 2021-03-22 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopmandb', '0044_auto_20210322_1302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='mileage_status',
            field=models.CharField(choices=[('0', '적립예정'), ('1', '적립완료'), ('2', '미적립'), ('3', '환급예장'), ('4', '환급완료')], default='0', max_length=15),
        ),
    ]