# Generated by Django 3.1.1 on 2021-02-04 12:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shopmandb', '0009_remove_userbox_identifier'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscription',
            name='shipping',
        ),
        migrations.AddField(
            model_name='order',
            name='identifier',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name='주문번호'),
        ),
        migrations.AddField(
            model_name='order',
            name='sub',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='shopmandb.subscription'),
        ),
        migrations.AddField(
            model_name='userbox',
            name='identifier',
            field=models.CharField(blank=True, max_length=20, unique=True, verbose_name='사용자 박스 ID'),
        ),
        migrations.AlterField(
            model_name='agentlog',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shopmandb.order', verbose_name='order id'),
        ),
        migrations.AlterField(
            model_name='orderoption',
            name='identifier',
            field=models.CharField(blank=True, max_length=20, unique=True, verbose_name='주문 옵션 id'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='identifier',
            field=models.CharField(blank=True, max_length=20, unique=True, verbose_name='결제 ID'),
        ),
        migrations.AlterField(
            model_name='product',
            name='identifier',
            field=models.CharField(blank=True, max_length=20, unique=True, verbose_name='상품번호'),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='identifier',
            field=models.CharField(blank=True, max_length=20, unique=True, verbose_name='구독 ID'),
        ),
    ]
