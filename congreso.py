import PyPDF2
import re
import neo4j_connector as nc
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# variables generales para la configuracion del proceso
presidencia = ' presidenta'
pagina_inicial = 5
frase_inicial = 'del grupo parlamentario popular.'
codigo_documento = 'cve: dscd-13-pl-12'


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
        .replace('presidente del gobierno en funciones', 'sánchez pérez-castejón') \
        .replace('ministra de justicia en funciones', 'delgado garcía') \
        .replace('ministra de hacienda en funciones', 'montero cuadrado') \
        .replace('ministro del interior en funciones', 'grande-marlaska gómez') \
        .replace('rodrí guez hernández', 'rodríguez hernández') \
        .replace('š', ' ') \
        .replace('–', ' ').replace(' : ', ': ').replace('momento:', 'momento') \
        .replace('cataluña:', 'cataluña').replace('sorprender:', 'sorprender') \
        .replace('?', '').replace('¿', '') \
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
    regex3 = r"señor |señora "
    lista_ponentes = find_ponentes(text, regex1)
    for ix, ponente in enumerate(lista_ponentes):
        ponente = adjust_ponentes(ponente, regex2)
        ponente = adjust_ponentes(ponente, regex3)
        output.append(ponente)
    pos_ini_ant = 0
    for ix, pon in enumerate(reversed(output)):
        pon['pos_dialog_end'] = pos_ini_ant
        pos_ini_ant = pon['pos_ini'] - 1
        output[len(output) - 1 - ix] = pon

    return output


def clean_parenthesis(text):
    regex = r" [(].*[)]"
    matches = re.finditer(regex, text)
    output = text
    for matchNum, match in enumerate(matches, start=1):
        output = output.replace(match.group(), '')
    return output


def clean_mr_mrs(text):
    return text.replace('el señor ', '').replace('la señora ', '').replace('señor ', '').replace('señora ', '')


def generate_dialogs(document):
    dialogs = []
    for element in split_text(document):
        if element['pos_dialog_end'] == 0:
            dialogs.append([document[element['pos_ini']: element['pos_fin']],
                            document[element['pos_fin'] + 1:]])
        else:
            dialogs.append([document[element['pos_ini']: element['pos_fin']],
                            document[element['pos_fin'] + 1: element['pos_dialog_end']]])
    for ix, dialog in enumerate(dialogs):
        dialogs[ix][0] = clean_mr_mrs(clean_parenthesis(dialog[0]))
        dialogs[ix][1] = clean_mr_mrs(clean_parenthesis(dialog[1]))
    output = []
    for dialog in dialogs:
        if dialog[0].find(presidencia) > 0:
            output.append(dialog)
    return output


def clean_dialogs(dialogs):
    list_specific_stop_words = ['gracias', 'señor', 'señora', 'señorias']
    stop_words = set(stopwords.words('spanish'))

    for ix, dialog in enumerate(dialogs):
        word_tokens = word_tokenize(dialog[1])
        filtered_sentence = [w for w in word_tokens if not w in stop_words]
        filtered_sentence = [w for w in filtered_sentence if not w in list_specific_stop_words]
        dialogs[ix][1] = ' '.join(filtered_sentence)
        dialogs[ix][0] = dialog[0][:-1]
    return dialogs


def cargar_dialogos(dialogs):
    graph = nc.generate_graph()
    matcher = nc.generate_nodeMatcher(graph)
    for dialog in dialogs:
        diputado = nc.return_diputado(matcher, dialog[0])
        if diputado == None:
            print(dialog[0])
            print(dialog[1])


def main():
    file_name = 'download.pdf'
    pdfFileObj = open(file_name, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)

    document = ''
    ix = 0
    for page in pdfReader.pages:
        ix = ix + 1
        if ix >= pagina_inicial:
            text = page.extractText().lower().replace('\n', '')
            ini = remove_headers(text)
            ini = ini + text[ini:].find(frase_inicial) + len(frase_inicial)
            document = document + clean_text(text[ini:], codigo_documento) + ' '

    dialogs = generate_dialogs(document)
    dialogs = clean_dialogs(dialogs)

    cargar_dialogos(dialogs)


#    os.remove(file_name)


if __name__ == '__main__':
    main()
