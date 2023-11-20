from rest_framework.views import APIView
from rest_framework.response import Response
from pickle import load
from aqi_forecast.settings import BASE_DIR
from main.permissions import InUkrainePermission, HasActiveToken
from main.models import Factory
from main.ip_location import get_location
from main.serializers import FactorySerializer
from main.functions import get_scaled_data, unscale_aqi, get_date, generate_factories_query
from keras.models import load_model

# Create your views here.

with open(f'{BASE_DIR}/main/data/features.pickle', 'rb') as f:
    features = dict([(i, 0) for i in load(f)])

with open(f'{BASE_DIR}/main/data/states.pickle', 'rb') as f:
    states = load(f)

m = load_model(f'{BASE_DIR}/main/data/model')


class StatesView(APIView):
    permission_classes = [InUkrainePermission, HasActiveToken]

    def get(self, request):
        return Response(states)


class FactoriesView(APIView):
    permission_classes = [InUkrainePermission, HasActiveToken]

    def get(self, request):
        ip = request.META.get('REMOTE_ADDR')
        location = get_location(ip)
        latitude, longitude = location['latitude'], location['longitude']
        radius = float(request.GET.get('radius')) * 1000
        qs = Factory.objects.raw(
            f"""select *, round(CAST(public.ST_Distance(public.ST_MakePoint({longitude}, {latitude}),
                public.ST_MakePoint(longitude, latitude), true) / 1000 AS numeric), 3) as distance from magistr.factory 
                where public.ST_DWithin(public.ST_MakePoint({longitude}, {latitude}),
                public.ST_MakePoint(longitude, latitude), {radius}, true) and is_active
                order by public.ST_Distance(public.ST_MakePoint({longitude}, {latitude}), 
                public.ST_MakePoint(longitude, latitude), true)""")
        qs_json = FactorySerializer(qs, many=True).data
        return Response(qs_json)


class AqiPrognosticationView(APIView):
    permission_classes = [InUkrainePermission, HasActiveToken]

    def get(self, request):
        ip = request.META.get('REMOTE_ADDR')
        location = get_location(ip)
        latitude, longitude = location['latitude'], location['longitude']
        state_id = int(request.GET.get('state'))
        state = list(features.keys())[state_id]
        features['density'] = float(request.GET.get('density'))
        features['temperature'] = float(request.GET.get('temperature'))
        features['pressure'] = int(request.GET.get('pressure'))
        features['wind_speed'] = float(request.GET.get('wind_speed'))
        features[state] = 1
        day, hour = get_date()
        features['hour'] = hour
        features['day'] = day
        factories = [i for i in features.keys() if i.endswith('000')]
        qs = Factory.objects.raw(generate_factories_query(latitude, longitude, factories))
        for f, val in qs[0].__dict__.items():
            if f not in ('place_id', '_state'):
                features[f] = val
        features_df = get_scaled_data(features)
        predicted = m.predict(features_df, verbose=0)
        return Response({'aqi': round(unscale_aqi(predicted[0][0]))})


class AqiPrognosticationByCordsView(APIView):
    permission_classes = [InUkrainePermission, HasActiveToken]

    def get(self, request):
        latitude, longitude = request.GET.get('latitude'), request.GET.get('longitude')
        state_id = int(request.GET.get('state'))
        state = list(features.keys())[state_id]
        features['density'] = float(request.GET.get('density'))
        features['temperature'] = float(request.GET.get('temperature'))
        features['pressure'] = int(request.GET.get('pressure'))
        features['wind_speed'] = float(request.GET.get('wind_speed'))
        features[state] = 1
        day, hour = get_date()
        features['hour'] = hour
        features['day'] = day
        factories = [i for i in features.keys() if i.endswith('000')]
        qs = Factory.objects.raw(generate_factories_query(latitude, longitude, factories))
        for f, val in qs[0].__dict__.items():
            if f not in ('place_id', '_state'):
                features[f] = val
        features_df = get_scaled_data(features)
        predicted = m.predict(features_df, verbose=0)
        return Response({'aqi': round(unscale_aqi(predicted[0][0]))})


class FactoriesByCordsView(APIView):
    permission_classes = [InUkrainePermission, HasActiveToken]

    def get(self, request):
        latitude, longitude = request.GET.get('latitude'), request.GET.get('longitude')
        radius = float(request.GET.get('radius')) * 1000
        qs = Factory.objects.raw(
            f"""select *, round(CAST(public.ST_Distance(public.ST_MakePoint({longitude}, {latitude}),
                public.ST_MakePoint(longitude, latitude), true) / 1000 AS numeric), 3) as distance from magistr.factory 
                where public.ST_DWithin(public.ST_MakePoint({longitude}, {latitude}),
                public.ST_MakePoint(longitude, latitude), {radius}, true) and is_active
                order by public.ST_Distance(public.ST_MakePoint({longitude}, {latitude}), 
                public.ST_MakePoint(longitude, latitude), true)""")
        qs_json = FactorySerializer(qs, many=True).data
        return Response(qs_json)
