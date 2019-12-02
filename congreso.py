import requests
from datetime import datetime
from bs4 import BeautifulSoup
import os
import PyPDF2

def obtain_PDF():
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

    return requests.get(link).content

def remove_headers(page):
    output = page.find("pág. 1")
    if output > 0:
        #primera página
        output = output + 6
        inicio = page[output:].find("orden del día:")
        if inicio > 0:
            output = output + inicio + 14
        else:
            output = output + 14
    else:
        output = page.find("pág. ") + 7
    while True:
        if page[output:1].isdigit():
            output = output + 1
        else:
            break
    return output

def main():
    PDF = obtain_PDF()
    file_name = 'download.pdf'
    open(file_name, 'wb').write(PDF)
    pdfFileObj = open(file_name, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    pagina_inicial = 5
    frase_inicial = 'preguntas:'
    ix = 0
    for page in pdfReader.pages:
        ix = ix + 1
        if ix >= pagina_inicial:
            text = page.extractText().lower()
            ini = remove_headers(text)
            print(text[ini:])
            print('-----------------------------------')
            break

 #   os.remove(file_name)





if __name__ == '__main__':
    main()
