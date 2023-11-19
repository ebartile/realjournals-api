from rest_framework import viewsets
from rest_framework.response import Response
from django.db.models import Sum
from .models import Transaction
from .serializers import TransactionSerializer
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from apps.accounts.permissions import IsAccountAdmin, HasAccountPerm

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = (IsAuthenticated(), IsAccountAdmin())

    def get_queryset(self):
        qs = super().get_queryset()
        qs.filter(account=self.kwargs['id'])
        return qs

    def get_permissions(self):
        # if self.action == "total_amount":
        #     self.permission_classes = (IsAdminUser(),)
        return self.permission_classes

    @action(detail=False, methods=['GET'])
    def total_amount(self, request, *args, **kwargs):
        qs = self.get_queryset()
        total_earnings = qs.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        return Response({'total_earnings': total_earnings}, status=status.HTTP_200_OK)
