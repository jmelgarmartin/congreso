import requests
from datetime import datetime
from bs4 import BeautifulSoup


def main():
    date_format = '%d/%m/%Y'
    url_congreso = 'http://www.congreso.es/portal/page/portal/Congreso/Congreso/Publicaciones/DiaSes/Pleno'

    response = requests.get(url_congreso)
    soup = BeautifulSoup(response.text, 'html.parser')
    divs = soup.findAll('div', attrs={'class': 'listado_1'})
    for div in divs:
        lis = div.findAll('li')
        for li in lis:
            if li.find('a'):
                date = datetime.strptime(li.text[:10], date_format)
                link = li.find('a', href=True)['href']

    print(date)
    print(link)
    PDF = requests.get(link).content
    print(type(PDF))




if __name__ == '__main__':
    main()
