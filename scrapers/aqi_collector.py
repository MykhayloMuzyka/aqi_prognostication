import sys

import requests
from db_functions import connect_db, get_cities, write_to_db
from datetime import datetime
from multiprocessing.dummy import Pool as ThreadPool

processed = 0


def get_data(city_id):
    date = datetime.now().strftime("%Y-%m-%d")
    url = f"https://www.saveecobot.com/maps/city_hourly_data.json?city_id={city_id}&days_back=1095&{date}T18-5"
    resp = requests.get(url)
    res = []
    if resp.status_code == 200:
        data = resp.json()['history']
        for i in data:
            if data[i]:
                res.append([city_id, i, data[i].get('a'), data[i].get('w')])
    return res


def process(city_id):
    global processed
    write_to_db(get_data(city_id), 'magistr.data', *connect_db(), header=('city_id', 'date', 'aqi', 'wind'))
    processed += 1
    sys.stdout.write(f'\r{processed} of {len(all_city_ids)} links processed')


if __name__ == '__main__':
    all_city_ids = get_cities()
    with ThreadPool(25) as pool:
        pool.map(process, all_city_ids)

