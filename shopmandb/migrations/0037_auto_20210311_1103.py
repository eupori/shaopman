# Generated by Django 3.1.1 on 2021-03-11 11:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopmandb', '0036_subscription_request'),
    ]

    operations = [
        migrations.CreateModel(
            name='Shipping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('old_post', models.CharField(blank=True, max_length=100, null=True, verbose_name='')),
                ('new_post', models.CharField(blank=True, max_length=100, null=True, verbose_name='')),
                ('si_goon_goo', models.CharField(blank=True, max_length=100, null=True, verbose_name='')),
                ('dong', models.CharField(blank=True, max_length=100, null=True, verbose_name='')),
                ('li', models.CharField(blank=True, max_length=100, null=True, verbose_name='')),
                ('airport_fee', models.CharField(blank=True, max_length=100, null=True, verbose_name='')),
                ('sheep_fee', models.CharField(blank=True, max_length=100, null=True, verbose_name='')),
                ('cycle', models.CharField(blank=True, max_length=100, null=True, verbose_name='')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='subscription',
            name='request',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='요청사항'),
        ),
    ]
