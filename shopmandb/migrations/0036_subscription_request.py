# Generated by Django 3.1.1 on 2021-03-11 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopmandb', '0035_auto_20210310_1446'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='request',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='현관비밀번호'),
        ),
    ]