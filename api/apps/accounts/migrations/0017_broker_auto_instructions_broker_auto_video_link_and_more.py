# Generated by Django 4.2.8 on 2024-01-02 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_remove_broker_instructions_remove_broker_video_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='broker',
            name='auto_instructions',
            field=models.TextField(blank=True, null=True, verbose_name='instructions'),
        ),
        migrations.AddField(
            model_name='broker',
            name='auto_video_link',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='broker',
            name='manual_instructions',
            field=models.TextField(blank=True, null=True, verbose_name='instructions'),
        ),
        migrations.AddField(
            model_name='broker',
            name='manual_video_link',
            field=models.URLField(blank=True, null=True),
        ),
    ]