from mongoengine import Document, IntField, FloatField, StringField, BooleanField

class HistoryDeals(Document):
    account = IntField()
    ticket = IntField()
    order = IntField()
    time = IntField(default=0)
    time_msc = IntField(default=0)
    type = IntField()
    entry = IntField()
    magic = IntField()
    position_id = IntField()
    reason = IntField()
    volume = FloatField()
    price = FloatField()
    commission = FloatField()
    swap = FloatField()
    profit = FloatField()
    fee = FloatField()
    sl = FloatField()
    tp = FloatField()
    symbol = StringField()
    comment = StringField()
    external_id = StringField()

class Orders(Document):
    account = IntField()
    ticket = IntField()
    time_setup = IntField(default=0)
    time_setup_msc = IntField(default=0)
    time_expiration = IntField(default=0)
    time_done = IntField(default=0)
    time_done_msc = IntField(default=0)
    type = IntField()
    type_time = IntField()
    type_filling = IntField()
    state = IntField()
    magic = IntField()
    position_id = IntField()
    position_by_id = IntField()
    reason = IntField()
    volume_current = FloatField()
    volume_initial = FloatField()
    price_open = FloatField()
    sl = FloatField()
    tp = FloatField()
    price_current = FloatField()
    price_stoplimit = FloatField()
    symbol = StringField()
    comment = StringField()
    external_id = StringField()

class HistoryOrders(Document):
    account = IntField()
    ticket = IntField()
    time_setup = IntField(default=0)
    time_setup_msc = IntField(default=0)
    time_expiration = IntField(default=0)
    time_done = IntField(default=0)
    time_done_msc = IntField(default=0)
    type = IntField()
    type_time = IntField()
    type_filling = IntField()
    state = IntField()
    magic = IntField()
    position_id = IntField()
    position_by_id = IntField()
    reason = IntField()
    volume_current = FloatField()
    volume_initial = FloatField()
    price_open = FloatField()
    sl = FloatField()
    tp = FloatField()
    price_current = FloatField()
    price_stoplimit = FloatField()
    symbol = StringField()
    comment = StringField()
    external_id = StringField()

class Positions(Document):
    account = IntField()
    ticket = IntField()
    time = IntField(default=0)
    time_msc = IntField(default=0)
    time_update = IntField(default=0)
    time_update_msc = IntField(default=0)
    type = IntField()
    magic = FloatField()
    identifier = IntField()
    reason = IntField()
    volume = FloatField()
    price_open = FloatField()
    sl = FloatField()
    tp = FloatField()
    price_current = FloatField()
    swap = FloatField()
    profit = FloatField()
    symbol = StringField()
    comment = StringField()
    external_id = StringField()
