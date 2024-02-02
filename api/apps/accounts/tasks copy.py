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
                history_deal = {
                    'ticket': history_deal.ticket,
                    'order': history_deal.order,
                    'time': history_deal.time,
                    'time_msc': history_deal.time_msc,
                    'type': history_deal.type,
                    'entry': history_deal.entry,
                    'magic': history_deal.magic,
                    'position_id': history_deal.position_id,
                    'reason': history_deal.reason,
                    'volume': history_deal.volume,
                    'price': history_deal.price,
                    'commission': history_deal.commission,
                    'swap': history_deal.swap,
                    'profit': history_deal.profit,
                    'fee': history_deal.fee,
                    'symbol': history_deal.symbol,
                    'comment': history_deal.comment,
                    'external_id': history_deal.external_id,
                }
                if result:
                    result.update(**history_deal)
                else:
                    data_to_insert.append(HistoryDeals(account=queryset.id, **history_deal))

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
                history_order = {
                    'ticket': history_order.ticket,
                    'time_setup': history_order.time_setup,
                    'time_setup_msc': history_order.time_setup_msc,
                    'time_done': history_order.time_done,
                    'time_done_msc': history_order.time_done_msc,
                    'time_expiration': history_order.time_expiration,
                    'type': history_order.type,
                    'type_time': history_order.type_time,
                    'type_filling': history_order.type_filling,
                    'state': history_order.state,
                    'magic': history_order.magic,
                    'position_id': history_order.position_id,
                    'position_by_id': history_order.position_by_id,
                    'reason': history_order.reason,
                    'volume_initial': history_order.volume_initial,
                    'volume_current': history_order.volume_current,
                    'price_open': history_order.price_open,
                    'sl': history_order.sl,
                    'tp': history_order.tp,
                    'price_current': history_order.price_current,
                    'price_stoplimit': history_order.price_stoplimit,
                    'symbol': history_order.symbol,
                    'comment': history_order.comment,
                    'external_id': history_order.external_id,
                }
                if result:
                    result.update(**history_order)
                else:
                    data_to_insert.append(HistoryOrders(account=queryset.id, **history_order))

            if len(data_to_insert) > 0:
                HistoryOrders.objects.insert(data_to_insert)

            data_to_insert = []
            positions = queryset.positions_get(group='', ticket='', symbol='')
            Positions.objects(account=queryset.id).delete()
            for position in positions:       
                position = {
                    'ticket': position.ticket,
                    'time': position.time,
                    'time_msc': position.time_msc,
                    'time_update': position.time_update,
                    'time_update_msc': position.time_update_msc,
                    'type': position.type,
                    'magic': position.magic,
                    'identifier': position.identifier,
                    'reason': position.reason,
                    'volume': position.volume,
                    'price_open': position.price_open,
                    'sl': position.sl,
                    'tp': position.tp,
                    'price_current': position.price_current,
                    'swap': position.swap,
                    'profit': position.profit,
                    'symbol': position.symbol,
                    'comment': position.comment,
                    'external_id': position.external_id,
                }
                data_to_insert.append(Positions(account=queryset.id, **position))

            if len(data_to_insert) > 0:
                Positions.objects.insert(data_to_insert)

            data_to_insert = []
            orders = queryset.orders_get(group='', ticket='', symbol='')
            Orders.objects(account=queryset.id).delete()
            for order in orders:           
                order = {
                    'ticket': order.ticket,
                    'time_setup': order.time_setup,
                    'time_setup_msc': order.time_setup_msc,
                    'time_done': order.time_done,
                    'time_done_msc': order.time_done_msc,
                    'time_expiration': order.time_expiration,
                    'type': order.type,
                    'type_time': order.type_time,
                    'type_filling': order.type_filling,
                    'state': order.state,
                    'magic': order.magic,
                    'position_id': order.position_id,
                    'position_by_id': order.position_by_id,
                    'reason': order.reason,
                    'volume_initial': order.volume_initial,
                    'volume_current': order.volume_current,
                    'price_open': order.price_open,
                    'sl': order.sl,
                    'tp': order.tp,
                    'price_current': order.price_current,
                    'price_stoplimit': order.price_stoplimit,
                    'symbol': order.symbol,
                    'comment': order.comment,
                    'external_id': order.external_id,
                }                
                data_to_insert.append(Orders(account=queryset.id, **order))

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
