# Generated by Django 3.1.1 on 2021-03-22 19:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopmandb', '0044_auto_20210322_1302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='content',
            field=models.TextField(verbose_name='상세정보'),
        ),
        migrations.AlterField(
            model_name='product',
            name='option',
            field=models.TextField(blank=True, null=True, verbose_name='옵션'),
        ),
    ]
