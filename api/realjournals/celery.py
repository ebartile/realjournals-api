from __future__ import absolute_import, unicode_literals
import random
import os

from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "realjournals.settings")

from django.conf import settings

app = Celery('realjournals')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

if settings.SEND_BULK_EMAILS_WITH_CELERY and settings.CHANGE_NOTIFICATIONS_MIN_INTERVAL > 0:
    app.conf.beat_schedule['send-bulk-emails'] = {
        'task': 'apps.notifications.tasks.send_bulk_email',
        'schedule': settings.CHANGE_NOTIFICATIONS_MIN_INTERVAL,
        'args': (),
    }
    app.conf.beat_schedule['send-import-trades'] = {
        'task': 'apps.accounts.tasks.import_data_periodically',
        'schedule': timedelta(minutes=1),  # Adjust the interval as needed
        'args': (),
    }
