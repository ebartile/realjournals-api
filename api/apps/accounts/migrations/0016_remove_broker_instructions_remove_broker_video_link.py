# Generated by Django 4.2.8 on 2024-01-02 15:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_broker_instructions_broker_video_link'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='broker',
            name='instructions',
        ),
        migrations.RemoveField(
            model_name='broker',
            name='video_link',
        ),
    ]