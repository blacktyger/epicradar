# Generated by Django 3.2 on 2021-07-28 20:50

from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Coin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=10)),
                ('symbol', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('most_recent', models.BooleanField(default=True)),
                ('country', models.CharField(max_length=3)),
                ('symbol', models.CharField(max_length=3)),
                ('value', models.DecimalField(decimal_places=8, default=1, max_digits=32)),
                ('data', jsonfield.fields.JSONField(default={})),
            ],
        ),
        migrations.CreateModel(
            name='Explorer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('most_recent', models.BooleanField(default=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('circulating', models.IntegerField()),
                ('blocktime', models.IntegerField()),
                ('height', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Network',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('most_recent', models.BooleanField(default=True)),
                ('timestamp', models.DateTimeField(auto_now=True)),
                ('height', models.IntegerField()),
                ('diff', jsonfield.fields.JSONField(default=dict)),
                ('hash', jsonfield.fields.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='Orderbook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('most_recent', models.BooleanField(default=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('data', jsonfield.fields.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='Pancake',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('most_recent', models.BooleanField(default=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('data', jsonfield.fields.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='Stellar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('most_recent', models.BooleanField(default=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('data', jsonfield.fields.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='Vitex',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('most_recent', models.BooleanField(default=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('data', jsonfield.fields.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='Price',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('most_recent', models.BooleanField(default=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('value', models.DecimalField(decimal_places=8, default=-1, max_digits=32)),
                ('coin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.coin')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.currency')),
            ],
        ),
    ]
