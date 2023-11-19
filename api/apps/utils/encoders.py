"""
Helper classes for parsers.
"""
from django.db.models.query import QuerySet
from django.utils.functional import Promise
from django.utils import timezone
# from django.utils.deprecation import CallableBool
from django.utils.encoding import force_str

import datetime
import decimal
import types
import json


class JSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time/timedelta,
    decimal types, and generators.
    """
    def default(self, o):
        # For Date Time string spec, see ECMA 262
        # http://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15
        if isinstance(o, Promise):
            return force_str(o)
        # elif isinstance(o, CallableBool):
        #     return bool(o)
        elif isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith("+00:00"):
                r = r[:-6] + "Z"
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.time):
            if timezone and timezone.is_aware(o):
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        elif isinstance(o, datetime.timedelta):
            return str(o.total_seconds())
        elif isinstance(o, decimal.Decimal):
            return str(o)
        elif isinstance(o, QuerySet):
            return list(o)
        elif hasattr(o, "tolist"):
            return o.tolist()
        elif hasattr(o, "__getitem__"):
            try:
                return dict(o)
            except:
                pass
        elif hasattr(o, "__iter__"):
            return [i for i in o]

        return super(JSONEncoder, self).default(o)


SafeDumper = None
