from django.views.debug import ExceptionReporter
from django.utils.log import AdminEmailHandler
from django.conf import settings
from django import template
from copy import copy

class DatabaseHandler(AdminEmailHandler):
    def emit(self, record):
        from django.db import connection
        # Ensure the database connection is established.
        if connection.connection is None:
            connection.connect()

        from .models import LogEntry
        # Create a LogEntry model instance and save it to the database.
        LogEntry.objects.create(
            level=record.levelname,
            message=self.format(record),
        )

class CustomAdminEmailHandler(AdminEmailHandler):
    def emit(self,record):
        try:
            request = record.request
            subject = '%s (%s IP): %s' % (
                record.levelname,
                ('internal' if request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS
                 else 'EXTERNAL'),
                record.getMessage()
            )
        except Exception:
            subject = '%s: %s' % (
                record.levelname,
                record.getMessage()
            )
            request = None
        subject = self.format_subject(subject)

        # Since we add a nicely formatted traceback on our own, create a copy
        # of the log record without the exception data.
        no_exc_record = copy(record)
        no_exc_record.exc_info = None
        no_exc_record.exc_text = None

        if record.exc_info:
            exc_info = record.exc_info
        else:
            exc_info = (None, record.getMessage(), None)

        reporter = ExceptionReporter(request, is_email=True, *exc_info)

        error_message ="\n".join(reporter.get_traceback_text().strip().split("GET:")[0].splitlines()[-4:-1])

        message = "%s\n\n%s" % (self.format(no_exc_record), error_message)
        html_message = reporter.get_traceback_html() if self.include_html else None

        self.send_mail(subject, message, fail_silently=True, html_message=html_message)
