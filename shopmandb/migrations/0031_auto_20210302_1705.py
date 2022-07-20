# Generated by Django 3.1.1 on 2021-03-02 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopmandb', '0030_merge_20210225_1707'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='address',
            field=models.CharField(blank=True, max_length=50, verbose_name='주소'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='address_detail',
            field=models.CharField(blank=True, max_length=50, verbose_name='상세주소'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='post_number',
            field=models.CharField(blank=True, max_length=10, verbose_name='우편 번호'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='recipient_name',
            field=models.CharField(blank=True, max_length=50, verbose_name='수령인'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='recipient_phone',
            field=models.CharField(blank=True, max_length=50, verbose_name='수령인 전화번호'),
        ),
        migrations.AddField(
            model_name='subscription',
            name='shipping_name',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='배송지명'),
        ),
    ]