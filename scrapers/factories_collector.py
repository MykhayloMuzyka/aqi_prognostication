from dataclasses import dataclass
from functools import partial
from multiprocessing.dummy import Pool as t_Pool
import re
import json
from urllib.parse import quote_plus
from urllib.error import HTTPError
from time import sleep

from geopy import Point
from geopy.distance import Distance, distance
import requests

from db_functions import write_to_db, connect_db

REGION_MULTIPLIER = 5
DEFAULT_REGION_VERTICAL_RADIUS = distance(meters=1068 * REGION_MULTIPLIER)
DEFAULT_REGION_HORIZONTAL_RADIUS = distance(meters=1026 * REGION_MULTIPLIER)
RESULT_THRESHOLD_FOR_REGION_SPLITTING = 100
DEFAULT_ZOOM_LEVEL = 10000.0 * REGION_MULTIPLIER

regions_num = 0
processed = 0

proxies = {
    "https": "https://...",
    "http": "http://..."
}
columns = ['place_id', 'place_name', 'google_place_url', 'sf_industry', 'full_address', 'city', 'longitude', 'latitude',
            'closed_status', 'store_type']


@dataclass
class Region:
    y_position: int
    x_position: int
    coords: Point
    vertical_sides_radius: Distance
    horizontal_sides_radius: Distance
    zoom_level: float
    subregions = []

    def split_on_subregions(self):
        subregions = []
        new_vertical_sides_length = (self.vertical_sides_radius / 2)
        new_horizontal_sides_length = (self.horizontal_sides_radius / 2)
        new_zoom_level = self.zoom_level / 2
        for y_direction, x_direction in [(0, 90), (180, 90), (0, 270), (180, 270)]:
            new_subregion_point = new_vertical_sides_length.destination(self.coords, bearing=y_direction)
            new_subregion_point = new_horizontal_sides_length.destination(new_subregion_point, bearing=x_direction)
            subregions.append(Region(
                coords=new_subregion_point, y_position=self.y_position, x_position=self.x_position,
                vertical_sides_radius=new_vertical_sides_length, horizontal_sides_radius=new_horizontal_sides_length,
                zoom_level=new_zoom_level
            ))
        self.subregions = subregions
        return subregions


def scrap_radius(center_coords: Point, radius: Distance, search_query: str):
    global regions_num
    y_regions_size_radius = round(
        (radius.km - DEFAULT_REGION_VERTICAL_RADIUS.km) / (DEFAULT_REGION_VERTICAL_RADIUS.km * 2))
    x_regions_size_radius = round(
        (radius.km - DEFAULT_REGION_HORIZONTAL_RADIUS.km) / (DEFAULT_REGION_HORIZONTAL_RADIUS.km * 2))

    regions_to_scrap = []
    for y_axis_position in range(-y_regions_size_radius, y_regions_size_radius + 1):
        for x_axis_position in range(-x_regions_size_radius, x_regions_size_radius + 1):
            y_offset = distance(kilometers=(DEFAULT_REGION_VERTICAL_RADIUS.km * 2) * y_axis_position)
            x_offset = distance(kilometers=(DEFAULT_REGION_HORIZONTAL_RADIUS.km * 2) * x_axis_position)
            region_point = y_offset.destination(center_coords, bearing=180)
            region_point = x_offset.destination(region_point, bearing=90)
            regions_to_scrap.append(Region(y_position=y_axis_position,
                                           x_position=x_axis_position,
                                           coords=region_point,
                                           vertical_sides_radius=DEFAULT_REGION_VERTICAL_RADIUS,
                                           horizontal_sides_radius=DEFAULT_REGION_HORIZONTAL_RADIUS,
                                           zoom_level=DEFAULT_ZOOM_LEVEL))
    result = {}
    while True:
        if not regions_to_scrap:
            return list(result.values())
        current_square_size = regions_to_scrap[0].vertical_sides_radius.km
        pool = t_Pool(25)
        regions_num = len(regions_to_scrap)
        regions_data = pool.map(partial(scrap_region, search_query=search_query), regions_to_scrap)
        pool.close()
        pool.join()
        regions_to_scrap = []
        for region in regions_data:
            if len(region['result']) > RESULT_THRESHOLD_FOR_REGION_SPLITTING and current_square_size > 0.02:
                regions_to_scrap.extend(region['region'].split_on_subregions())
            result.update({r['place_id']: r for r in region['result'] if r})


def scrap_region(region: Region, search_query: str):
    global processed
    map_objects = []
    page_num = 1
    for i in range(30):
        resp = fetch_google_map_region_search(region.coords, search_query, zoom=region.zoom_level, page=page_num)
        if not resp:
            break
        resp_json = parse_json_from_response(resp)
        region_page_data = parse_google_maps_search_api_response(resp_json)
        map_objects.extend(region_page_data)
        if len(region_page_data) < 20:
            break
        page_num += 1
        sleep(0.01)
    if [i.values() for i in map_objects if i]:
        write_to_db([list(i.values()) for i in map_objects if i], 'magistr.factory', *connect_db(), columns,
                    on_conflict=True, id_tag='place_id')
    processed += 1
    print(f"Processed {processed} of {regions_num} squares of query {search_query} ({processed / regions_num * 100} %). "
          f"Found {len([i.values() for i in map_objects if i])} places")
    return {'region': region, 'result': map_objects}


def parse_json_from_response(response):
    unescaped_response = response.content.decode('unicode_escape').encode('latin1').decode()
    resp_matches = re.search(r"\'\n(\[{1,2}.+\])\"?,", unescaped_response)
    resp_json = resp_matches[1] if resp_matches else None
    if not resp_json:
        print('empty response body' + response.text)
        return []
    data = json.loads(resp_json)
    return data


def parse_google_maps_search_api_response(data):
    if len(data[0][1]) == 1:
        return []
    result = []
    for place_list in [d for d in data[0][1] if len(d) > 13 and d[14] and d[14][11]]:
        try:
            result.append(parse_google_maps_place(data[0][0], place_list[14]))
        except (IndexError, TypeError):
            print(f'skipped place.\nplace list: {place_list[14]}')
    return result


def parse_google_maps_place(search_query, place):
    d = place
    country = d[88][2][1] if d[88] and d[88][2] else None
    if country == 'UA':
        status = 'Open'
        try:
            if d[203][1][5][0] in ('Permanently closed', 'Temporarily closed'):
                status = d[203][1][5][0]
        except (TypeError, IndexError):
            pass
        try:
            place_url = f'https://www.google.com/maps/place/{quote_plus(d[11])}/@{d[9][2]},' \
                        f'{d[9][3]},10z/data=!3m1!4b1!4m5!3m4!1s{d[10]}!8m2!3d50.0052297!4d36.24389' \
                        f'?authuser=0&hl=us'
            store_type = d[13][0] if d[13] else None
            place_dict = {
                'place_id': d[10],
                'place_name': d[11],
                'google_place_url': place_url,
                'sf_industry': search_query,
                'full_address': d[39],
                'city': d[183][0][3][1][0][0].split(', ')[0] if d[183] and d[183][0] and d[183][0][3] and d[183][0][3][
                    1]
                                                                and d[183][0][3][1][0] else None,
                'longitude': Point(d[9][2:]).longitude,
                'latitude': Point(d[9][2:]).latitude,
                'closed_status': status,
                'store_type': store_type,
            }
            return place_dict
        except Exception as e:
            print(e)
            return None


def fetch_google_map_region_search(region_center_coords: Point, search_query: str, zoom: float,
                                   locale='US', lang='en', page=1):
    paination = f'!8i{page * 20 - 20}' if page > 1 else ""
    url = f'http://www.google.com/search?tbm=map&authuser=0&hl={lang}&gl={locale}' \
          f'&pb=!4m12!1m3!1d{zoom}!2d{region_center_coords.longitude}!3d{region_center_coords.latitude}!2m3!1f0' \
          f'!2f0!3f0!3m2!1i1429!2i577!4f13.1!7i20{paination}!10b1!12m8!1m1!18b1!2m3!5m1!6e2!20e3!10b1!16b1' \
          f'!19m4!2m3!1i360!2i120!4i8!20m57!2m2!1i203!2i100!3m2!2i4!5b1!6m6!1m2!1i86!2i86!1m2!1i408!2i240!7m42!1m3' \
          f'!1e1!2b0!3e3!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3!1m3!1e8!2b0!3e3!1m3!1e10!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e9' \
          f'!2b1!3e2!1m3!1e10!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e10!2b0!3e4!2b1!4b1!9b0!22m6!1sRBeBYcPhLuSWjgb2jpbwAQ:2265' \
          f'!2s1i:0,t:20588,p:RBeBYcPhLuSWjgb2jpbwAQ:2265!4m1!2i20588!7e81!12e3!24m56!1m20!13m8!2b1!3b1!4b1!6i1' \
          f'!8b1!9b1!14b1!20b1!18m10!3b1!4b1!5b1!6b1!9b1!12b0!13b1!14b1!15b0!17b0!2b1!5m5!2b1!3b1!5b1!6b1!7b1' \
          f'!10m1!8e3!14m1!3b1!17b1!20m2!1e3!1e6!24b1!25b1!26b1!29b1!30m1!2b1!36b1!43b1!52b1!55b1!56m2!1b1!3b1' \
          f'!65m5!3m4!1m3!1m2!1i224!2i298!89b1!26m4!2m3!1i80!2i92!4i8!30m28!1m6!1m2!1i0!2i0!2m2!1i458!2i577!1m6' \
          f'!1m2!1i1379!2i0!2m2!1i1429!2i577!1m6!1m2!1i0!2i0!2m2!1i1429!2i20!1m6!1m2!1i0!2i557!2m2!1i1429!2i577' \
          f'!31b1!34m17!2b1!3b1!4b1!6b1!8m5!1b1!3b1!4b1!5b1!6b1!9b1!12b1!14b1!20b1!23b1!25b1!26b1!37m1!1e81!42b1' \
          f'!46m1!1e9!47m0!49m5!3b1!6m1!1b1!7m1!1e3!50m44!1m39!2m7!1u3!4z0JLRltC00LrRgNC40YLQviDQt9Cw0YDQsNC3' \
          f'!5e1!9s0ahUKEwiIyZzs1vnzAhXXFXcKHchCBG8Q_KkBCAQoAQ!10m2!3m1!1e1!2m7!1u2' \
          f'!4z0J3QsNC50LrRgNCw0YnRliDQvtGG0ZbQvdC60Lg!5e1!9s0ahUKEwiIyZzs1vnzAhXXFXcKHchCBG8Q_KkBCAUoAg!10m2!2m1' \
          f'!1e1!2m7!1u1!4z0JTQtdGI0LXQstGWINC80ZbRgdGG0Y8!5e1!9s0ahUKEwiIyZzs1vnzAhXXFXcKHchCBG8Q_KkBCAYoAw' \
          f'!10m2!1m1!1e1!2m7!1u1!4z0JTQvtGA0L7Qs9GWINC80ZbRgdGG0Y8!5e1' \
          f'!9s0ahUKEwiIyZzs1vnzAhXXFXcKHchCBG8Q_KkBCAcoBA!10m2!1m1!1e2!3m1!1u3!3m1!1u2!3m1!1u1!4BIAE!2e2!3m2!1b1' \
          f'!3b1!59BQ2dBd0Fn!65m1!1b1!67m2!7b1!10b1!69i580' \
          f'&q={search_query}&nfpr=1&tch=1&ech=15&psi=RBeBYcPhLuSWjgb2jpbwAQ.1635850054284.1'
    for _ in range(16):
        try:
            resp = requests.get(url, timeout=20, verify=False, proxies=proxies,
                                headers={'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7'})
            resp.raise_for_status()
            parse_json_from_response(resp)
        except HTTPError:
            print(f'google maps api fetching invalid response. ')
            sleep(2)
            continue
        except Exception as e:
            print(e)
            sleep(2)
            continue
        return resp


if __name__ == '__main__':
    for query in ('Виробництво', 'Фабрика', 'АЕС', 'ГЕС', 'ТЕС', 'ТЕЦ'):
        scrap_radius(Point(49.017909, 31.475995), distance(kilometers=1400), query)
        processed = 0
