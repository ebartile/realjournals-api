# Generated by Django 4.2.7 on 2023-11-18 17:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StorageEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='created date')),
                ('modified_date', models.DateTimeField(auto_now=True, verbose_name='modified date')),
                ('key', models.CharField(max_length=255, verbose_name='key')),
                ('value', models.JSONField(blank=True, default=None, null=True, verbose_name='value')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='storage_entries', to=settings.AUTH_USER_MODEL, verbose_name='owner')),
            ],
            options={
                'verbose_name': 'storage entry',
                'verbose_name_plural': 'storages entries',
                'ordering': ['owner', 'key'],
                'unique_together': {('owner', 'key')},
            },
        ),
    ]