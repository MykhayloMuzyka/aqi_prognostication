import requests
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from db_functions import write_to_db, get_all_cities_codes
from multiprocessing.dummy import Pool as ThreadPool


def get_data(date, city_code):
    try:
        url = 'https://meteopost.com/weather/archive/'
        payload = {
            'd': str(date.day),
            'm': '0' + str(date.month) if len(str(date.month)) == 1 else str(date.month),
            'y': str(date.year),
            'city': str(city_code),
            'arc': '1'
        }
        resp = requests.post(url, data=payload)
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', {'id': 'maint'})
        columns = ['date', 'temperature', 'pressure', 'wind_dir', 'wind_speed', 'humidity', 'state']
        data_list = []
        for tr in table.find('table', {'id': 'arc'}).find_all('tr')[1:]:
            tmp_data = [city_code]
            for col, data in zip(columns, tr.find_all('td')):
                if col == 'date':
                    hours, mins = data.text.replace(' ', '').strip().split(':')
                    val = datetime(year=date.year, month=date.month, day=date.day, hour=int(hours), minute=int(mins))
                    tmp_data.append(val)
                if col == 'temperature':
                    val = int(data.text[:-1])
                    tmp_data.append(val)
                if col == 'pressure':
                    val = int(data.text.replace(' ', '').strip())
                    tmp_data.append(val)
                if col == 'wind_dir':
                    val = int(data.find('img')['title'].replace('°', '').strip())
                    tmp_data.append(val)
                if col == 'wind_speed':
                    val = int(data.text.replace('м/с', '').strip())
                    tmp_data.append(val)
                if col == 'humidity':
                    val = int(data.text.replace('%', '').strip())
                    tmp_data.append(val)
                if col == 'state':
                    try:
                        val = data.find('img')['title']
                    except Exception as e:
                        val = 'null'
                    tmp_data.append(val)
            data_list.append(tmp_data)
        write_to_db(data_list, 'magistr.meteopost_weather_archive', header=['city_code'] + columns)
    except Exception as e:
        print(e)


def process(city_code):
    start_data = date(year=2020, month=8, day=16)
    finish_data = date(year=2023, month=8, day=16)
    while start_data <= finish_data:
        print(city_code, start_data)
        get_data(start_data, city_code)
        start_data += timedelta(days=1)


if __name__ == '__main__':
    with ThreadPool(13) as pool:
        pool.map(process, get_all_cities_codes())

