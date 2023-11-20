import requests
from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup
from db_functions import write_to_db, get_all_cities_codes_ids
from multiprocessing.dummy import Pool as ThreadPool


def get_data(date, city_code):
    try:
        url = 'https://meteopost.com/weather/archive/'
        payload = {
            'd': str(date.day),
            'm': '0' + str(date.month) if len(str(date.month)) == 1 else str(date.month),
            'y': str(date.year),
            'city': str(city_code),
            'arc': '2',
            'days': '1'
        }
        resp = requests.post(url, data=payload)
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', {'id': 'maint'})
        columns = ['_', 'date', '_', 'visibility_range', 'clouds', 'wind_dir', 'wind_speed', 'temperature',
                   'dewpoint', 'pressure', '_', 'precipitation', '_', 'state', '_', '_', '_', '_', '_', '_']
        data_list = []
        for tr in table.find_all('table')[2].find_all_next('tr')[1:9]:
            tmp_data = [city_code]
            for col, data in zip(columns, tr.find_all('td')):
                if col == 'date':
                    hours, mins = data.text.replace(' ', '').strip().split(':')
                    val = datetime(year=date.year, month=date.month, day=date.day, hour=int(hours), minute=int(mins))
                    tmp_data.append(val)
                if col == 'visibility_range':
                    try:
                        val = int(float(data.text.split(' ')[0]) * 1000)
                    except ValueError:
                        val = None
                    tmp_data.append(val)
                if col == 'clouds':
                    val = int(data.text)
                    tmp_data.append(val)
                if col == 'wind_dir':
                    try:
                        val = int(data.find('img')['title'].replace('°', '').strip())
                    except ValueError:
                        val = -1
                    tmp_data.append(val)
                if col == 'wind_speed':
                    val = int(data.text.replace('м/с', '').strip())
                    tmp_data.append(val)
                if col == 'temperature':
                    val = float(data.text[:-1])
                    tmp_data.append(val)
                if col == 'dewpoint':
                    try:
                        val = float(data.text.split('°')[0])
                    except ValueError:
                        val = None
                    tmp_data.append(val)
                if col == 'pressure':
                    try:
                        val = float(data.text.replace(' ', '').strip())
                    except ValueError:
                        val = None
                    tmp_data.append(val)
                if col == 'precipitation':
                    try:
                        val = float(data.text.split(' ')[0])
                    except ValueError:
                        val = 0.0
                    tmp_data.append(val)
                if col == 'state':
                    val = data.text.replace(' ', '')
                    tmp_data.append(val)
            data_list.append(tmp_data)
        write_to_db(data_list, 'magistr.meteopost_meteodata_archive', header=['city_code'] + [c for c in columns if c != '_'])
    except Exception:
        pass


def process(city_code):
    start_data = date(year=2020, month=8, day=16)
    finish_data = date(year=2023, month=8, day=16)
    while start_data <= finish_data:
        print(city_code, start_data)
        get_data(start_data, city_code)
        start_data += timedelta(days=1)


if __name__ == '__main__':
    with ThreadPool(30) as pool:
        pool.map(process, get_all_cities_codes_ids())
