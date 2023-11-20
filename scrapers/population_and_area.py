import requests
from bs4 import BeautifulSoup
import re
from db_functions import get_cities_names_transliterated, update_stats


if __name__ == '__main__':
    cities = get_cities_names_transliterated()
    for city in cities:
        for i in range(4):
            if not i:
                url = f"""https://uk.wikipedia.org/wiki/{city.replace(' ', '_').replace("'", '%27')}"""
            elif i == 1:
                url += '_(місто)'
            elif i == 2:
                url += url.replace('місто', 'село')
            elif i == 3:
                url += url.replace('село', 'смт')
            resp = requests.get(url, verify=False)
            soup = BeautifulSoup(resp.text, 'html.parser')
            trs = soup.find_all('tr')
            area, density, population = None, None, None
            for tr in trs:
                # print(tr.find_next('td'), '\n\n\n')
                if tr.find_next('a').text in ('Площа', 'Площа\n') and not area:
                    try:
                        area = float(tr.find_next('td').text.split(' ')[0].replace('[', '').replace(']', '').replace(',', '.').replace('\n', ''))
                    except Exception:
                        pass
                if tr.find_next('a').text in ('Населення', 'Населення\n') and not population:
                    try:
                        try:
                            population = int(''.join(
                                re.sub(r"\(.+?\)", '', tr.find_next('td').find_next('td').text).split(' ')[
                                1:-1]).replace(' ', ''))
                        except Exception:
                            population = int(re.sub(r"\(.+?\)", '', tr.find_next('td').find_next('td').text))
                    except Exception:
                        pass
                if tr.find_next('a').text in ('Густота населення', 'Густота населення\n') and not density:
                    try:
                        density = float(tr.find_next('td').text.split(' ')[0].replace(',', '.'))
                    except Exception:
                        pass

                if tr.find_next('td').text in ('Площа', 'Площа\n') and not area:
                    try:
                        area = float(tr.find_next('td').find_next('td').text.split(' ')[0].replace('[', '').replace(']', '').replace(',', '.'))
                    except Exception:
                        pass
                if tr.find_next('td').text in ('Населення', 'Населення\n') and not population:
                    try:
                        try:
                            population = int(''.join(re.sub(r"\(.+?\)", '', tr.find_next('td').find_next('td').text).split(' ')[1:-1]).replace(' ', ''))
                        except Exception:
                            population = int(re.sub(r"\(.+?\)", '', tr.find_next('td').find_next('td').text))
                    except Exception:
                        pass
                if tr.find_next('td').text in ('Густота населення', 'Густота населення\n') and not density:
                    try:
                        density = float(tr.find_next('td').find_next('td').text.split(' ')[0].replace(',', '.'))
                    except Exception:
                        pass
            if sum([bool(area), bool(population), bool(density)]):
                break
        print(f"City: {city}\nArea: {area}\nPopulation: {population}\nDensity: {density}\n")
        update_stats(city, area, population, density)


