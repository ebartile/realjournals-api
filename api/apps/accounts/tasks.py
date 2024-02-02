from pymongo import UpdateOne
from celery import shared_task
from .models import Account
from apps.journals.models import HistoryOrders, HistoryDeals, Orders, Positions
from realjournals.celery import app
from datetime import datetime, timedelta
from django.utils import timezone

@app.task
def import_data_periodically():
    accounts = Account.objects.filter(account_type='AUTO', has_be_configured=True)

    for queryset in accounts:
        try:
            queryset.account_info()

            if queryset.last_deal_end_date:
                date_from = queryset.last_deal_end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                date_from = queryset.start_date.strftime("%Y-%m-%dT%H:%M:%SZ")

            date_to = _date_to = queryset.end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

            date_format = "%Y-%m-%dT%H:%M:%SZ"
            date_from = int(datetime.strptime(date_from, date_format).timestamp())
            date_to = int(datetime.strptime(date_to, date_format).timestamp())

            history_deals = queryset.history_deals_get(date_from=date_from, date_to=date_to, group='', ticket='', position='')

            data_to_insert = []
            for history_deal in history_deals: 
                queryset.last_deal_end_date = _date_to
                result = HistoryDeals.objects(account=queryset.id, ticket=history_deal.ticket).first()
                if result:
                    result.update(**history_deal._asdict())
                else:
                    data_to_insert.append(HistoryDeals(account=queryset.id, **history_deal._asdict()))

            if len(data_to_insert) > 0:
                HistoryDeals.objects.insert(data_to_insert)
            
            if queryset.last_order_end_date:
                date_from = queryset.last_order_end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                date_from = queryset.start_date.strftime("%Y-%m-%dT%H:%M:%SZ")

            date_to = _date_to = queryset.end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            date_from = int(datetime.strptime(date_from, date_format).timestamp())
            date_to = int(datetime.strptime(date_to, date_format).timestamp())

            data_to_insert = []
            history_orders = queryset.history_orders_get(date_from=date_from, date_to=date_to, group='', ticket='', position='')
            for history_order in history_orders:           
                queryset.last_order_end_date = _date_to
                result = HistoryOrders.objects(account=queryset.id, ticket=history_order.ticket).first()
                if result:
                    result.update(**history_order._asdict())
                else:
                    data_to_insert.append(HistoryOrders(account=queryset.id, **history_order._asdict()))

            if len(data_to_insert) > 0:
                HistoryOrders.objects.insert(data_to_insert)

            data_to_insert = []
            positions = queryset.positions_get(group='', ticket='', symbol='')
            Positions.objects(account=queryset.id).delete()
            for position in positions:       
                data_to_insert.append(Positions(account=queryset.id, **position._asdict()))

            if len(data_to_insert) > 0:
                Positions.objects.insert(data_to_insert)

            data_to_insert = []
            orders = queryset.orders_get(group='', ticket='', symbol='')
            Orders.objects(account=queryset.id).delete()
            for order in orders:           
                data_to_insert.append(Orders(account=queryset.id, **order._asdict()))

            if len(data_to_insert) > 0:
                Orders.objects.insert(data_to_insert)

            queryset.has_be_configured = True
            queryset.save()
        except ValueError as e:
            print(e)
            queryset.last_deal_end_date = timezone.now() - timedelta(days=365*10)
            queryset.last_order_end_date = timezone.now() - timedelta(days=365*10)
            queryset.has_be_configured = False
            queryset.save()
