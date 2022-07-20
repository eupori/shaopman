# Generated by Django 3.1.5 on 2021-05-06 17:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shopmandb', '0061_order_orderer_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderEmailLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(blank=True, max_length=50, null=True, verbose_name='상태')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shopmandb.order', verbose_name='order id')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]