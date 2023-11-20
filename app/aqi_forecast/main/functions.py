import datetime
from aqi_forecast.settings import BASE_DIR
from pickle import load
import pandas as pd

with open(f'{BASE_DIR}/main/data/min_max_data.pickle', 'rb') as f:
    min_max_data = load(f)


def get_date() -> tuple:
    date = datetime.datetime.now()
    year = date.year
    last_day_of_year = datetime.date(year=year - 1, day=31, month=12)
    diff = datetime.date(year=year, day=date.day, month=date.month) - last_day_of_year
    return diff.days, date.hour


def generate_factories_query(latitude, longitude, factories):
    query = 'select 1 as place_id,'
    for f in factories:
        radius = int(f.split('_')[-1])
        store_type = ' '.join(f.split('_')[:-1]).capitalize()
        query += f"\nmagistr.get_factories_count({latitude}, {longitude}, {radius}, {radius-1_000}, '{store_type}') as {f},"
    return query[:-1]


def scale(min_val, max_val, val):
    dif = -min_val
    new_max_val, new_val = max_val + dif, val + dif
    scaled_val = new_val / new_max_val if new_max_val else 0
    return scaled_val


def unscale_aqi(scaled_aqi):
    dif = -min_max_data['aqi']['min']
    new_max_val = min_max_data['aqi']['max'] + dif
    return (scaled_aqi * new_max_val) - dif


def get_scaled_data(features):
    res = {}
    for f in features:
        if f.startswith('state_'):
            res[f] = [features[f]]
        else:
            res[f] = [scale(min_max_data[f]['min'], min_max_data[f]['max'], features[f])]
    return pd.DataFrame.from_dict(res)
