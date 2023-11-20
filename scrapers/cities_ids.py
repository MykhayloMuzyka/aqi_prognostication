import requests
from bs4 import BeautifulSoup
from db_functions import get_all_cities_names_transliterated, write_city_id

url = 'https://meteopost.com/weather/archive/'
payload = {
    'd': '14',
    'm': '09',
    'y': '2022',
    'city': '33998',
    'arc': '2',
    'days': '1'
}
resp = requests.post(url, data=payload)
soup = BeautifulSoup(resp.text, 'html.parser')
options = soup.find_all('option')
cities = get_all_cities_names_transliterated()
for city in cities:
    try:
        city_id = list(filter(lambda x: x.text.strip() == city and x['value'].isdigit(), options))[0]['value']
        write_city_id(city, city_id)
    except Exception as e:
        pass
