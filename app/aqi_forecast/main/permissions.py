import datetime
import pytz
from rest_framework import permissions
from main.ip_location import get_location
from aqi_forecast.models import Token

utc = pytz.UTC


class InUkrainePermission(permissions.BasePermission):
    message = 'Requests are available only from Ukraine.'

    def has_permission(self, request, view):
         location = get_location(request.META.get('REMOTE_ADDR'))
         return location['countryName'] == 'Ukraine'


class HasActiveToken(permissions.BasePermission):
    message = 'Token is expired.'

    def has_permission(self, request, view):
        token = request.META.get('HTTP_TOKEN', None)
        if not token:
            self.message = 'Token is not provided.'
            return False
        token = Token.objects.get(token=token)
        if not token:
            self.message = 'Wrong token.'
            return False
        return utc.localize(datetime.datetime.now() - datetime.timedelta(days=token.duration)) < token.created_at
