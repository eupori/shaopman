# Generated by Django 3.1.1 on 2021-01-28 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopmandb', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='post_number',
            field=models.CharField(max_length=10, verbose_name='우편 번호'),
        ),
    ]
