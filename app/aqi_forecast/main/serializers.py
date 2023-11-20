from rest_framework import serializers


class FactorySerializer(serializers.Serializer):
    place_id = serializers.CharField()
    place_name = serializers.CharField()
    google_place_url = serializers.CharField()
    full_address = serializers.CharField()
    city = serializers.CharField()
    longitude = serializers.FloatField()
    latitude = serializers.FloatField()
    store_type = serializers.CharField()
    distance = serializers.FloatField()
