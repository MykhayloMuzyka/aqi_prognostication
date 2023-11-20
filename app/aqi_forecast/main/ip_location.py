import requests


def get_location(ip):
    if ip == '127.0.0.1':
        response = requests.get('https://api.ipify.org')
        ip = response.text
    url = 'https://iplocation.com/'
    payload = {
        'ip': ip
    }
    resp = requests.post(url, payload)
    geo_data = resp.json()
    res = {
        'continentCode': geo_data['continent_code'],
        'countryName': geo_data['country_name'],
        'countryCode': geo_data['country_code'],
        'latitude': geo_data['lat'],
        'longitude': geo_data['lng'],
        'cityName': geo_data['city'],
        'regionName': geo_data['region_name'],
        'timeZone': geo_data['time_zone'],
        'postalCode': geo_data['postal_code']
    }
    return res
