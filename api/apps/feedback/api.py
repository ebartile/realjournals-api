from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from apps.utils.exceptions import BadRequest
from rest_framework.permissions import IsAuthenticated
from . import serializers
from . import services

import copy


class FeedbackViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.FeedbackEntrySerializer

    def create(self, request, **kwargs):

        data = copy.deepcopy(request.data)
        data.update({"full_name": request.user.get_full_name(),
                     "email": request.user.email})

        serializer = self.serializer_class(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.object = serializer.save()

        extra = {
            "HTTP_HOST":  request.META.get("HTTP_HOST", None),
            "HTTP_REFERER": request.META.get("HTTP_REFERER", None),
            "HTTP_USER_AGENT": request.META.get("HTTP_USER_AGENT", None),
        }
        services.send_feedback(self.object, extra, reply_to=[request.user.email])

        return Response(serializer.data, status=status.HTTP_200_OK)
