import geoip2.database
import json
import os
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from .models import ActivityLog
from django.conf import settings

def log_activity(action, source, ip, agent, object_type, object_id):
    content_type = ContentType.objects.get(model=object_type)

    # Perform IP geolocation using geoip2
    path = os.path.join(settings.BASE_DIR, "GeoLite2-City.mmdb")
    reader = geoip2.database.Reader(path)
    try:
        response = reader.city(ip)
        location = {
            "country": response.country.name,
            "city": response.city.name,
            "latitude": response.location.latitude,
            "longitude": response.location.longitude,
        }
    except geoip2.errors.AddressNotFoundError:
        location = {}

    # Create an activity log entry
    log_entry = ActivityLog(
        action=action,
        source=source,
        ip=ip,
        location=json.dumps(location),  # Store location as JSON
        agent=agent,
        content_type=content_type,
        object_id=object_id
    )
    log_entry.save()
