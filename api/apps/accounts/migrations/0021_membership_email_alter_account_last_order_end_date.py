# Generated by Django 4.2.9 on 2024-01-10 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_remove_account_last_end_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='email',
            field=models.EmailField(blank=True, default=None, max_length=255, null=True, verbose_name='email'),
        ),
        migrations.AlterField(
            model_name='account',
            name='last_order_end_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last order end date'),
        ),
    ]
