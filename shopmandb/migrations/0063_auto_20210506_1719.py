# Generated by Django 3.1.5 on 2021-05-06 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopmandb', '0062_orderemaillog'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderemaillog',
            name='message',
            field=models.TextField(blank=True, verbose_name='메시지'),
        ),
        migrations.AlterField(
            model_name='order',
            name='comment',
            field=models.TextField(blank=True, null=True, verbose_name='관리자 코멘트'),
        ),
    ]
