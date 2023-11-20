import psycopg2


def connect_db():
    DB_CREDS = {
        'host': 'localhost',
        'database': 'postgres',
        'user': 'postgres',
        'password': 'password',
        'port': 5432
    }
    con = psycopg2.connect(**DB_CREDS)
    return con, con.cursor()


def write_city(city_id, city_name):
    query = f"insert into magistr.city (id, name) values ({city_id}, '{city_name}') on conflict do nothing"
    con, cur = connect_db()
    cur.execute(query)
    con.commit()
    con.close()


def get_cities():
    query = f"select id from magistr.city"
    con, cur = connect_db()
    cur.execute(query)
    res = [i[0] for i in cur.fetchall()]
    con.close()
    return res


def get_cities_names():
    query = f"select name, region from magistr.city"
    con, cur = connect_db()
    cur.execute(query)
    res = cur.fetchall()
    con.close()
    return res


def get_cities_names_transliterated():
    query = f"""select name_transliterated from magistr.city where (area is null and population is null)
or (population is null and density is null)
or (area is null and density is null);"""
    con, cur = connect_db()
    cur.execute(query)
    res = [i[0] for i in cur.fetchall()]
    con.close()
    return res


def get_all_cities_names_transliterated():
    query = f"""select name_transliterated from magistr.city"""
    con, cur = connect_db()
    cur.execute(query)
    res = [i[0] for i in cur.fetchall()]
    con.close()
    return res


def get_all_cities_codes():
    query = f"""select city_code from magistr.city where city_code is not null"""
    con, cur = connect_db()
    cur.execute(query)
    res = [i[0] for i in cur.fetchall()]
    con.close()
    return res


def get_all_cities_codes_ids():
    query = f"""select city_code_id from magistr.city where city_code_id is not null"""
    con, cur = connect_db()
    cur.execute(query)
    res = [i[0] for i in cur.fetchall()]
    con.close()
    return res


def write_city_id(city, idx):
    con, cur = connect_db()
    city = cur.mogrify('%s', [city]).decode()
    idx = cur.mogrify('%s', [idx]).decode()
    query = f"update magistr.city set city_code_id={idx} where name_transliterated={city}"
    cur.execute(query)
    con.commit()
    con.close()


def update_stats(city, area, population, density):
    con, cur = connect_db()
    area = cur.mogrify('%s', [area]).decode()
    population = cur.mogrify('%s', [population]).decode()
    density = cur.mogrify('%s', [density]).decode()
    city = cur.mogrify('%s', [city]).decode()
    query = f"update magistr.city set area={area}, population={population}, density={density} " \
            f"where name_transliterated = {city}"
    cur.execute(query)
    con.commit()
    con.close()


def write_to_db(to_db_list, table_name, header=None, id_tag=None, on_conflict=False):
    connection, cursor = connect_db()
    signs = '(' + ('%s,' * len(to_db_list[0]))[:-1] + ')'
    try:
        args_str = b','.join(cursor.mogrify(signs, x) for x in to_db_list)
        args_str = args_str.decode()
        if header:
            column_names = '(' + ', '.join([f"{x}" for x in header]) + ')'
            insert_statement = f'INSERT INTO {table_name + column_names} VALUES'
        else:
            insert_statement = f'INSERT INTO {table_name} VALUES'
        conflict_statement = """ ON CONFLICT DO NOTHING"""
        if on_conflict:
            update_string = ','.join(["{0} = excluded.{0}".format(e) if e != 'store_type' else
                                      "store_type = "
                                      "     case "
                                      "         when excluded.store_type!=any(string_to_array((select store_type from magistr.factory where place_id=excluded.place_id), ',')) "
                                      "         then (select store_type from magistr.factory where place_id=excluded.place_id) || ',' || excluded.store_type "
                                      "         else (select store_type from magistr.factory where place_id=excluded.place_id)"
                                      "     end"
                                      for e in header])
            conflict_statement = """ ON CONFLICT ("{0}") DO UPDATE SET {1};""".format(id_tag, update_string)
        cursor.execute(insert_statement + args_str + conflict_statement)
        connection.commit()
        # logger.success(f'saved {len(to_db_list)} rows in {table_name} table')
    except Exception as e:
        print(e)
        # logger.error(str(e))
        connection.rollback()


def update_city_region(city_id, region):
    con, cur = connect_db()
    query = f"update magistr.city set region='{region}' where id={city_id}"
    cur.execute(query)
    con.commit()
    con.close()


def update_coordinates(city, region, coordinates):
    lat, lon = coordinates
    con, cur = connect_db()
    query = f"update magistr.city set lat={lat}, lon={lon} where name='{city}' and region='{region}'"
    cur.execute(query)
    con.commit()
    con.close()


def get_unique_cities() -> list or None:
    _, cur = connect_db()
    try:
        cur.execute("SELECT id, name_transliterated FROM magistr.city where city_code is not null or city_code_id is not null")
        return cur.fetchall()
    except Exception as e:
        pass


def get_all_calculations() -> list:
    query = 'select optimizer, activation, layers, first_layer_output from magistr.nn_features'
    con, cur = connect_db()
    cur.execute(query)
    res = [tuple(i) for i in cur.fetchall()]
    con.close()
    return res


def write_nn_features(data):
    query = f"insert into magistr.nn_features ({','.join(list(data.keys()))}) values {tuple(data.values())}"
    con, cur = connect_db()
    cur.execute(query)
    con.commit()
    con.close()
