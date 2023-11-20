import psycopg2
import pandas as pd
from db_functions import connect_db


def meteopost_weather_df():
    con, cur = connect_db()
    query = """select c.id, c.area, c.population, c.density, m.date, m.temperature, m.pressure, m.wind_dir, m.wind_speed, 
               m.humidity, m.state, a.aqi from magistr.city c
               join magistr.aqi_data a on a.city_id = c.id
               join magistr.meteopost_weather_archive m on c.city_code = m.city_code and a.date = m.date"""
    return pd.read_sql_query(query, con)


def meteopost_meteodata_df():
    con, cur = connect_db()
    query = """ select c.id, c.area, c.population, c.density, m.date, m.visibility_range, m.clouds, m.wind_dir, m.wind_speed,
                m.temperature, m.dewpoint,  m.pressure, m.precipitation, m.state, a.aqi from magistr.city c
                join magistr.aqi_data a on a.city_id = c.id
                join magistr.meteopost_meteodata_archive m on c.city_code_id = m.city_code and a.date = m.date"""
    return pd.read_sql_query(query, con)


def sinoptik_df():
    con, cur = connect_db()
    query = """  select c.id, c.area, c.population, c.density, m.date, m.wind_dir
    , m.wind_speed, m.temperature,
                 m.pressure, m.precipitation, m.state, m.feels_like, m.humidity, a.aqi from magistr.city c
                 join magistr.aqi_data a on a.city_id = c.id
                 join magistr.sinoptik m on c.id = m.city_id and a.date = m.date"""
    return pd.read_sql_query(query, con)


def factories_count_df():
    con, cur = connect_db()
    query = """ select * from magistr.factories_count"""
    return pd.read_sql_query(query, con)


def factories_count_sectors_df():
    con, cur = connect_db()
    query = """ select * from magistr.factories_count_sectors_new"""
    return pd.read_sql_query(query, con)


def factories_count_meteopost_df():
    con, cur = connect_db()
    query = """select c.area, c.population, c.density, m.date, m.visibility_range, m.clouds, m.wind_dir, m.wind_speed,
                m.temperature, m.dewpoint,  m.pressure, m.precipitation, m.state, f.*, a.aqi from magistr.city c
                join magistr.aqi_data a on a.city_id = c.id
                join magistr.meteopost_meteodata_archive m on c.city_code_id = m.city_code and a.date = m.date
                join magistr.factories_count f on c.id = f.city_id"""
    return pd.read_sql_query(query, con)


def factories_count_sectors_meteopost_df():
    con, cur = connect_db()
    query = """select c.area, c.population, c.density, m.date, m.visibility_range, m.clouds, m.wind_dir, m.wind_speed,
                m.temperature, m.dewpoint,  m.pressure, m.precipitation, m.state, f.*, a.aqi from magistr.city c
                join magistr.aqi_data a on a.city_id = c.id
                join magistr.meteopost_meteodata_archive m on c.city_code_id = m.city_code and a.date = m.date
                join magistr.factories_count_sectors f on c.id = f.city_id"""
    return pd.read_sql_query(query, con)


def process_wind_dir(wind_dir):
    dirs = {
        'Північний': 360,
        'Північно-східний': 45,
        'Східний': 90,
        'Південно-східний': 135,
        'Південний': 180,
        'Південно-західний': 225,
        'Західний': 270,
        'Північно-західний': 315
    }
    if type(wind_dir) == str:
        return dirs[wind_dir]
    if wind_dir == 0:
        return 360
    return round(wind_dir, -1)


def generate_factories_query():
    query = 'select distinct store_type from magistr.factory where is_active'
    con, cur = connect_db()
    cur.execute(query)
    types = [i[0] for i in cur.fetchall()]
    query = 'select id as city_id'
    for t in types:
        for r in range(1_000, 20_001, 1_000):
            query += f",\nmagistr.get_factories_count(lat, lon, {r}, {r-1_000}, '{t}') as {t.lower().replace(' ', '_')}_{r}"
    query += '\nfrom magistr.city'
    return query


if __name__ == '__main__':
    meteopost_weather_df = meteopost_weather_df()
    meteopost_meteodata_df = meteopost_meteodata_df()
    sinoptik_df = sinoptik_df()

    df = pd.concat([meteopost_weather_df.filter(['id', 'area', 'population', 'density','date', 'temperature', 'pressure', 'wind_dir', 'wind_speed', 'state', 'aqi']),
                    meteopost_meteodata_df.filter(['id', 'area', 'population', 'density','date', 'temperature', 'pressure', 'wind_dir', 'wind_speed', 'state', 'aqi']),
                   sinoptik_df.filter(['id', 'area', 'population', 'density','date', 'temperature', 'pressure', 'wind_dir', 'wind_speed', 'state', 'aqi'])])
    df['wind_dir'] = df['wind_dir'].apply(process_wind_dir)
    df['state'] = df['state'].apply(lambda x: x.lower() if x else 'спокійно')
    df = df.rename(columns={'id': 'city_id'})
    print(df)
    # df.to_csv('data/weather_with_area.csv')
    factories_df = factories_count_sectors_df()
    print(factories_df)
    res_df = pd.DataFrame.merge(df, factories_df, how='left', on='city_id')
    print(res_df)
    res_df.to_csv('data/weather_with_area_with_factories_sectors_final.csv')
