import requests
from db_functions import get_cities_names, update_coordinates


def get_coordinates(city, region):
    city = ' '.join(city.split('-')[:-1]) if city[-1] in '0123456789' else ' '.join(city.split('-'))
    url = 'https://coordinates-converter.com/en/converter-api/get_osm'
    payload = {
        '_action': 'get_osm',
        's': f'{city}, {region}, ukraine'
    }
    resp = requests.post(url, payload).json()
    if type(resp) == dict:
        return resp['lat'], resp['lon']
    else:
        return resp[0]['lat'], resp[0]['lon']


if __name__ == '__main__':
    for city, region in get_cities_names():
        try:
            coordinates = get_coordinates(city, region)
            update_coordinates(city, region, coordinates)
        except IndexError as e:
            print(None)
