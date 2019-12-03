import requests
from bs4 import BeautifulSoup
import os
import PyPDF2
import re


def obtain_PDF():
    url_congreso = 'http://www.congreso.es/portal/page/portal/Congreso/Congreso/Publicaciones/DiaSes/Pleno'

    response = requests.get(url_congreso)
    soup = BeautifulSoup(response.text, 'html.parser')
    divs = soup.findAll('div', attrs={'class': 'listado_1'})

    link = ''
    for div in divs:
        lis = div.findAll('li')
        for li in lis:
            print(li)
            if li.find('a'):
                link = li.find('a', href=True)['href']

    return requests.get(link).content


def remove_headers(page):
    output = page.find("pág. 1")
    if output > 0:
        # primera página
        output = output + 6
        inicio = page[output:].find("orden del día:")
        if inicio > 0:
            output = output + inicio + 14
        else:
            output = output + 14
    else:
        output = page.find("pág. ") + 6
    while True:
        if page[output:1].isdigit():
            output = output + 1
        else:
            break
    return output


def clean_text(text, cod_docu):
    return text.replace(cod_docu, '').replace('.', ' ').replace(',', ' ') \
        .replace('presidente del gobierno en funciones', 'sánchez pérez-castejón').replace('š', ' ')\
        .replace('–', ' ')\
        .replace('  ', ' ')


def find_ponentes(text, regex):
    output = []
    matches = re.finditer(regex, text)

    for matchNum, match in enumerate(matches, start=1):
        output_dict = {'pos_ini': match.start(),
                       'pos_fin': match.end(),
                       'text': match.group()}
        output.append(output_dict)

    return output


def adjust_ponentes(ponente, regex):
    matches = re.finditer(regex, ponente['text'])

    for matchNum, match in enumerate(matches, start=1):
        output = {'pos_ini': ponente['pos_ini'] + match.start(),
                  'pos_fin': ponente['pos_fin'],
                  'text': match.group()}

    return output


def split_text(text):
    output = []
    regex1 = r"el señor .{1,90}[:]|la señora .{1,90}[:]"
    regex2 = r"el señor |la señora "
    lista_ponentes = find_ponentes(text, regex1)
    for ix, ponente in enumerate(lista_ponentes):
        ponente = adjust_ponentes(ponente, regex2)
        output.append(ponente)
    pos_ini_ant = 0
    for ix, pon in enumerate(reversed(output)):
        pon['pos_dialog_end'] = pos_ini_ant
        pos_ini_ant = pon['pos_ini'] - 1
        output[len(output) - 1 - ix] = pon

    return output


def main():
    #   PDF = obtain_PDF()
    file_name = 'download.pdf'
    #   open(file_name, 'wb').write(PDF)
    pdfFileObj = open(file_name, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    # PARAMETROS
    pagina_inicial = 5
    frase_inicial = 'del grupo parlamentario popular.'
    codigo_documento = 'cve: dscd-13-pl-12'

    document = ''
    ix = 0
    for page in pdfReader.pages:
        ix = ix + 1
        if ix >= pagina_inicial:
            text = page.extractText().lower().replace('\n', '')
            ini = remove_headers(text)
            ini = ini + text[ini:].find(frase_inicial) + len(frase_inicial)
            document = document + clean_text(text[ini:], codigo_documento) + ' '
            if ix > pagina_inicial + 1:
                break
    dialogs = []
    for element in split_text(document):
        if element['pos_dialog_end'] == 0:
            dialogs.append((document[element['pos_ini']: element['pos_fin']],
                            document[element['pos_fin'] + 1:]))
        else:
            dialogs.append((document[element['pos_ini']: element['pos_fin']],
                            document[element['pos_fin'] + 1: element['pos_dialog_end']]))
    print('@##########')
    for dialog in dialogs:
        print(dialog)


#    os.remove(file_name)


if __name__ == '__main__':
    main()
