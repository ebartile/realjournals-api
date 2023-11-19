from django.apps import AppConfig

from django.db.models.signals import Signal

signal_assigned_to = Signal()
signal_assigned_users = Signal()
signal_watchers_added = Signal()
signal_members_added = Signal()
signal_mentions = Signal()
signal_comment = Signal()
signal_comment_mentions = Signal()

class NotificationsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = "apps.notifications"
    verbose_name = "Notifications"

    def ready(self):
        from . import signals as handlers
        signal_assigned_to.connect(handlers.on_assigned_to)
        signal_assigned_users.connect(handlers.on_assigned_users)
        signal_watchers_added.connect(handlers.on_watchers_added)
        signal_members_added.connect(handlers.on_members_added)
        signal_mentions.connect(handlers.on_mentions)
        signal_comment.connect(handlers.on_comment)
        signal_comment_mentions.connect(handlers.on_comment_mentions)
