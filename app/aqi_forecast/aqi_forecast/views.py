from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from main.ip_location import get_location
from main.permissions import HasActiveToken


class HealthView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response("It's alive!")


class LocationView(APIView):
    permission_classes = [HasActiveToken]

    def get(self, request):
        ip = request.META.get('REMOTE_ADDR')
        location = get_location(ip)
        return Response(location)
