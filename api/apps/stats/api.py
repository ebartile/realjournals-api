from rest_framework import viewsets
from rest_framework.response import Response
from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

class StatisticsViewSet(viewsets.ViewSet):
    serializer_class = None  # You might want to define a serializer class here

    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['GET'])
    def total_earnings(self, request, *args, **kwargs):
        return Response({'total_earnings': 10}, status=status.HTTP_200_OK)
