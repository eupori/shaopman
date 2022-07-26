# Generated by Django 3.1.1 on 2021-06-04 13:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopmandb', '0066_auto_20210602_0915'),
    ]

    operations = [
        migrations.CreateModel(
            name='MileageLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user_id', models.CharField(max_length=500, verbose_name='사용자 ID')),
                ('mileage', models.PositiveIntegerField(verbose_name='상품 수량')),
                ('status', models.CharField(blank=True, max_length=50000, null=True, verbose_name='상태')),
                ('message', models.TextField(blank=True, verbose_name='메시지')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
