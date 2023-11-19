import warnings

from .services import take_snapshot
from apps.notifications import services as notifications_services
from rest_framework import serializers

class HistoryResourceMixin(object):
    """
    Rest Framework resource mixin for resources
    susceptible to have models with history.
    """

    # This attribute will store the last history entry
    # created for this resource. It is mainly used for
    # notifications mixin.
    __last_history = None
    __object_saved = False

    def get_last_history(self):
        if not self.__object_saved:
            message = ("get_last_history() function called before any object are saved. "
                       "Seems you have a wrong mixing order on your resource.")
            warnings.warn(message, RuntimeWarning)
        return self.__last_history

    def get_object_for_snapshot(self, obj):
        """
        Method that returns a model instance ready to snapshot.
        It is by default noop, but should be overwritten when
        a snapshot-ready instance is found in one of the foreign key
        fields.
        """
        return obj

    def persist_history_snapshot(self, obj=None, delete: bool = False):
        """
        Shortcut for resources with special save/persist
        logic.
        """

        user = self.request.user
        comment = ""
        if isinstance(self.request.data, dict):
            comment = self.request.data.get("comment", "")

        if obj is None:
            obj = self.get_object()

        sobj = self.get_object_for_snapshot(obj)
        if sobj != obj:
            delete = False
        print(obj)
        notifications_services.analyze_object_for_watchers(obj, comment, user)

        self.__last_history = take_snapshot(sobj, comment=comment, user=user, delete=delete)
        self.__object_saved = True

    def perform_update(self, serializer):
        obj = serializer.save()
        self.persist_history_snapshot(obj=obj)

    def perform_save(self, serializer):
        obj = serializer.save()
        self.persist_history_snapshot(obj=obj)

    def perform_destroy(self, instance):
        self.persist_history_snapshot(obj, delete=True)
        super().perform_destroy(instance)


class TotalCommentsSerializerMixin(serializers.Serializer):
    total_comments = serializers.SerializerMethodField()

    def get_total_comments(self, obj):
        # The "total_comments" attribute is attached in the get_queryset of the viewset.
        return getattr(obj, "total_comments", 0) or 0
