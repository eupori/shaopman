# Generated by Django 3.1.1 on 2021-03-22 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopmandb', '0043_auto_20210319_1350'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='content',
            field=models.CharField(max_length=2000, verbose_name='상세정보'),
        ),
    ]