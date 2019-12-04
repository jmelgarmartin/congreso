import PyPDF2
import re
import neo4j_connector as nc
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tag import StanfordPOSTagger

# variables generales para la configuracion del proceso
presidencia = 'presidenta'
pagina_inicial = 5
frase_inicial = '(Prolongados aplausos del Grupo Parlamentario Socialista).'
codigo_documento = 'cve: dscd-13-pl-2'


def obtain_documents(params):
    file_name = 'files/'
    output = []
    for key in params.keys():
        pdfFileObj = open(file_name + key, 'rb')
        output.append([key, PyPDF2.PdfFileReader(pdfFileObj)])
    return output


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
        .replace('š', ' ').replace(';', ' ').replace('!', ' ').replace('¡', ' ') \
        .replace('–', ' ').replace(' : ', ': ').replace('momento:', 'momento') \
        .replace('rodrí guez', 'rodríguez').replace('catalunya', 'cataluña') \
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
        dialogs[ix][1] = clean_mr_mrs(clean_parenthesis(dialog[1])).replace(':', ' ') \
            .replace('(', ' ').replace(')', ' ') \
            .replace('  ', ' ')
    output = []
    for dialog in dialogs:
        if dialog[0].find(presidencia) == -1:
            output.append(dialog)
    return output


def clean_names(name):
    return name.replace('presidente del gobierno en funciones', 'sánchez pérez-castejón') \
        .replace('ministra de justicia en funciones', 'delgado garcía') \
        .replace('ministra de hacienda en funciones', 'montero cuadrado') \
        .replace('ministro del interior en funciones', 'grande-marlaska gómez') \
        .replace('rodrí guez hernández', 'rodríguez hernández') \
        .replace('ministro de agricultura pesca y alimentación en funciones', 'planas puchades') \
        .replace('ministro de fomento en funciones', 'ábalos meco') \
        .replace('ministra de economía y empresa en funciones', 'calviño santamaría') \
        .replace(' candidato a la presidencia del gobierno', '')


def clean_dialogs(dialogs):
    list_specific_stop_words = ['gracias', 'señor', 'señora', 'señorías', 'presidenta', 'ministro', 'ustedes',
                                'usted', 'si', ]
    stop_words = set(stopwords.words('spanish'))

    for ix, dialog in enumerate(dialogs):
        word_tokens = word_tokenize(dialog[1])
        filtered_sentence = [w for w in word_tokens if not w in stop_words]
        filtered_sentence = [w for w in filtered_sentence if not w in list_specific_stop_words]
        dialogs[ix][1] = ' '.join(filtered_sentence)
        dialogs[ix][0] = clean_names(dialog[0][:-1])
    return dialogs


def dialog_tagger(dialog):
    jar = 'nlp/stanford-postagger.jar'
    model = 'nlp/spanish.tagger'
    pos_tagger = StanfordPOSTagger(model, jar, encoding='utf8')
    words = pos_tagger.tag([dialog])
    output = []
    for word in words:
        if word[1][0:2] in ['nc', 'np', 'aq']:
            output.append(word[0])
    return output


def cargar_dialogos(dialogs):
    graph = nc.generate_graph()
    matcher = nc.generate_nodeMatcher(graph)
    for dialog in dialogs:
        diputado = nc.return_diputado(matcher, dialog[0])
        if diputado == None:
            print("PERSONA NO ENCONTRADA: ")
            print(dialog[0])
            print(dialog[1])
        else:
            for word in dialog_tagger(dialog[1]):
                graph.run(nc.insert_palabra(word))
                palabra = nc.return_palabra(matcher, word)
                graph.create(nc.insert_relation(diputado, palabra))


def main():
    params = {'doc_0.pdf': {'pagina_inicial': 5,
                            'frase_inicial': '(Prolongados aplausos del Grupo Parlamentario Socialista).',
                            'codigo_documento': 'cve: dscd-13-pl-2'},
              'doc_1.pdf': {'pagina_inicial': 3,
                            'frase_inicial': '',
                            'codigo_documento': 'cve: dscd-13-pl-3'},
              }

    list_docs = obtain_documents(params)

    for ind, doc in enumerate(list_docs):
        print('----------------------- DOCUMENTO ' + str(ind) + ' -----------------------')
        pagina_inicial = params[doc[0]]['pagina_inicial']
        frase_inicial = params[doc[0]]['frase_inicial']
        codigo_documento = params[doc[0]]['codigo_documento']
        graph = nc.generate_graph()
        matcher = nc.generate_nodeMatcher(graph)
        document = ''
        ix = 0
        for page in doc[1].pages:
            ix = ix + 1
            if ix >= pagina_inicial:
                text = page.extractText().lower().replace('\n', '')
                ini = remove_headers(text)
                ini = ini + text[ini:].find(frase_inicial) + len(frase_inicial)
                document = document + clean_text(text[ini:], codigo_documento) + ' '

                regex = r"[ ][A-Za-z]+[:]"
                matches = re.finditer(regex, document)
                for matchNum, match in enumerate(matches, start=1):
                    diputado = nc.busca_diputado(matcher, match.group()[1:-1])
                    if diputado == None:
                        document = document.replace(match.group(), match.group()[1:-1])

        dialogs = generate_dialogs(document)
        dialogs = clean_dialogs(dialogs)

        cargar_dialogos(dialogs)


if __name__ == '__main__':
    main()
