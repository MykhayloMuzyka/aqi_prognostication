import re
import sys

import requests

from db_functions import *


if __name__ == '__main__':
    url = 'https://www.saveecobot.com/maps/cities'
    resp = requests.get(url).text
    links = list(filter(
        lambda x: not (x.endswith('oblast') or x.endswith('cities')),
        re.findall(r'(https://www.saveecobot.com/maps/.+?)"', resp))
    )
    d = {}

    for i, link in enumerate(links):
        sys.stdout.write(f'\r{i+1} of {len(links)} links processed')
        resp = requests.get(link)
        if resp.status_code == 200:
            try:
                city_id = re.findall(r'city_id : (\d+)', resp.text)[0]
                try:
                    region = re.findall(r'https://www.saveecobot.com/maps/(.+-oblast)', resp.text)[0]
                except IndexError:
                    region = link.split('/')[-1]
            except IndexError:
                pass
            finally:
                update_city_region(city_id, region)
                # write_city(city_id, link.split('/')[-1])

