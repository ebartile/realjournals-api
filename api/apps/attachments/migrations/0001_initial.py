# Generated by Django 4.2.7 on 2023-11-18 17:40

import apps.attachments.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('accounts', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField(verbose_name='object id')),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='created date')),
                ('modified_date', models.DateTimeField(verbose_name='modified date')),
                ('name', models.CharField(blank=True, default='', max_length=500)),
                ('size', models.IntegerField(blank=True, default=None, editable=False, null=True)),
                ('attached_file', models.FileField(blank=True, max_length=500, null=True, upload_to=apps.attachments.models.get_attachment_file_path, verbose_name='attached file')),
                ('sha1', models.CharField(blank=True, default='', max_length=40, verbose_name='sha1')),
                ('is_deprecated', models.BooleanField(default=False, verbose_name='is deprecated')),
                ('from_comment', models.BooleanField(default=False, verbose_name='from comment')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('order', models.IntegerField(default=0, verbose_name='order')),
                ('status', models.CharField(blank=True, choices=[('uploaded', 'Uploaded'), ('processing', 'Processing'), ('failed', 'Failed'), ('done', 'Done')], default='uploaded', max_length=30, verbose_name='Data Status')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='accounts.account', verbose_name='account')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='content type')),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='change_attachments', to=settings.AUTH_USER_MODEL, verbose_name='owner')),
            ],
            options={
                'verbose_name': 'attachment',
                'verbose_name_plural': 'attachments',
                'ordering': ['account', 'created_date', 'id'],
                'index_together': {('content_type', 'object_id')},
            },
        ),
    ]