# Generated by Django 4.2.8 on 2024-01-01 21:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_alter_account_start_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='start_date',
        ),
    ]