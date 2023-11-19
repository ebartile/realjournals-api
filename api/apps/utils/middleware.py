import os
import geoip2.database
import json
from django.conf import settings
from django.utils import timezone

class UpdateUserLocationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        path = os.path.join(settings.BASE_DIR, "GeoLite2-City.mmdb")
        self.geoip_reader = geoip2.database.Reader(path)

    def __call__(self, request):
        # Get the user's IP address from the request
        user_ip = self.get_client_ip(request)

        if user_ip:
            # Perform IP geolocation using geoip2
            try:
                response = self.geoip_reader.city(user_ip)
                location = {
                    "country": response.country.iso_code,
                    "city": response.city.name,
                    "latitude": response.location.latitude,
                    "longitude": response.location.longitude,
                }
                if request.user.is_authenticated:
                    request.user.location = location
                    request.user.state = response.subdivisions.most_specific.name
                    request.user.timezone = response.location.time_zone
                    request.user.country = response.country.iso_code
                    request.user.city = response.city.name
                    request.user.last_seen = timezone.now()
                    request.user.continent = response.continent.code
                    request.user.save()

            except geoip2.errors.AddressNotFoundError:
                location = {}
        else:
            location = {}

        # Store the user's location in the session
        request.session['user_location'] = json.dumps(location)

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
