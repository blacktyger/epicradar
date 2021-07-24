# Generated by Django 3.0 on 2021-03-16 13:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('address', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.IntegerField(default=1111)),
                ('name', models.CharField(default='Default', max_length=70)),
                ('telegram_user', models.CharField(blank=True, max_length=70, null=True)),
                ('balance', models.DecimalField(blank=True, decimal_places=8, default=0, max_digits=32)),
                ('create_at', models.DateTimeField(auto_now=True)),
                ('data', jsonfield.fields.JSONField(default={})),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wallet', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
