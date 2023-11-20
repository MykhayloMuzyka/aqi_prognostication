import re
from datetime import datetime, timedelta
from multiprocessing.dummy import Pool as t_pool
from time import sleep
import requests
from bs4 import BeautifulSoup

from db_functions import *

connection, cursor = connect_db()


# def get_cities() -> list[str]:
#     cities_df = pd.read_csv('data/ua-list.csv', encoding='cp1251', delimiter=';')
#     cities_df.dropna(inplace=True)
#     return cities_df['Населений пункт'].tolist()


def get_dates() -> list[str]:
    current_year = datetime.now().year
    date = datetime(year=current_year, month=1, day=1)
    dates_list = list()
    while date < datetime.now():
        dates_list.append(date.strftime("%Y-%m-%d"))
        date += timedelta(days=1)
    return dates_list


def get_weather_info(city: str, date: str) -> list[dict] or None:
    print(f'{city} {date}')
    url = f"https://ua.sinoptik.ua/погода-{city.replace(' ', '-')}/{date}"
    resp = None
    for _ in range(10):
        resp = requests.get(url)
        if resp.status_code == 200:
            break
        elif resp.status_code == 404:
            return None
        else:
            sleep(5)
            continue
    if resp:
        try:
            soup = BeautifulSoup(resp.text, 'html.parser')
            table = soup.find('table', {'class': 'weatherDetails'})
            info_sections = table.find_all('tr')
            hours = [int(s.text.split(':')[0].strip()) for s in info_sections[1].find_all('td')]
            states = [s['title'] for s in info_sections[2].find_all('div')]
            temperatures = [float(s.text[:-1]) for s in info_sections[3].find_all('td')]
            feels_likes = [float(s.text[:-1]) for s in info_sections[4].find_all('td')]
            pressures = [float(s.text) for s in info_sections[5].find_all('td')]
            humidities = [float(s.text) for s in info_sections[6].find_all('td')]
            winds = [s['data-tooltip'] for s in info_sections[7].find_all('div')]
            directions = [s.split(',')[0] for s in winds]
            # print([float(re.search(r"\d+\.\d+", s).group()) for s in winds])
            speeds = [float(re.search(r"\d+\.\d+", s).group()) for s in winds]
            print(speeds)
            precipitations = [float(s.text) if s.text != '-' else 0.0 for s in info_sections[8].find_all('td')]
            res = list()
            for i in range(8):
                year, month, day = date.split('-')
                res.append({
                    'city': city,
                    'date': datetime(year=int(year), month=int(month), day=int(day), hour=int(hours[i]), minute=0),
                    'state': states[i], 'temperature': temperatures[i], 'feels_like': feels_likes[i],
                    'pressure': pressures[i], 'humidity': humidities[i], 'wind direction': directions[i],
                    'wind speed': speeds[i], 'precipitation': precipitations[i]
                })
            return res
        except Exception as e:
            print(e)
            return


def process_city(city_id, city):
    print(f'Start scraping city {city}.')
    try:
        to_db_list = list()
        for date in get_dates():
            info = get_weather_info(city, date)
            if info:
                to_db_list += [tuple(d.values()) for d in info]
            elif not(len(to_db_list)):
                to_db_list.append((city, date, 0, None, None, None, None, None, None, None, None))
        print(f'Processed {len(to_db_list)} rows in city {city}.')
        write_to_db([[city_id] + list(i)[1:] for i in to_db_list], 'magistr.sinoptik')
        print(f'Finish scraping city {city}')
    except Exception as e:
        print(e)


if __name__ == '__main__':
    with t_pool(32) as pool:
        pool.starmap(process_city, get_unique_cities())
