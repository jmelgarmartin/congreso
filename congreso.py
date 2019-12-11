import re

import PyPDF2
from nltk.corpus import stopwords
from nltk.tag import StanfordPOSTagger
from nltk.tokenize import word_tokenize
import spacy
from datetime import datetime
import pickle

import neo4j_connector as nc

# variables generales para la configuracion del proceso
presidencia = 'presidenta'
pagina_inicial = 0
frase_inicial = ''
codigo_documento = ''


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
    # arreglos especiales...... ye vere si puedo corregirlos mejor
    return text.replace(cod_docu, '').replace('.', ' ').replace(',', ' ') \
        .replace('š', ' ').replace(';', ' ').replace('!', ' ').replace('¡', ' ') \
        .replace('–', ' ').replace(' : ', ': ').replace('momento:', 'momento') \
        .replace('rodrí guez', 'rodríguez').replace('catalunya', 'cataluña') \
        .replace('cataluña:', 'cataluña').replace('sorprender:', 'sorprender') \
        .replace(' de:', ' de').replace('también:', 'también') \
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

    return output


def clean_parenthesis(text):
    regex = r" \(([^\)]+)\)"
    matches = re.finditer(regex, text)
    output = text
    for matchNum, match in enumerate(matches, start=1):
        t_parentesis = match.group()
        output = output.replace(t_parentesis, '')
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


def dialog_tagger(dialog, nlp, pos_tagger, create_model):
    print("INICIO TAG:")
    if create_model:
        a = len(dialog)
        b = 0
        print(a)
        while b < a:
            try:
                with open('words.pickle', 'rb') as handle:
                    words = pickle.load(handle)
                    print(datetime.now())
                    words.extend(pos_tagger.tag(dialog[b:b + 200]))
                    print(len(words))
                    print(datetime.now())
                    with open('words.pickle', 'wb') as handle:
                        pickle.dump(words, handle, protocol=pickle.HIGHEST_PROTOCOL)
            except:
                print("CREAMOS NUEVO MODELO")
                print(datetime.now())
                words = pos_tagger.tag(dialog[b:b + 400])
                with open('words.pickle', 'wb') as handle:
                    pickle.dump(words, handle, protocol=pickle.HIGHEST_PROTOCOL)
                print(datetime.now())
            b = b + 399
            print(b)
    else:
        with open('words.pickle', 'rb') as handle:
            words = pickle.load(handle)

    words = list(set(words))
    output = []

    for word in words:
        if word[1][0:2] in ['nc', 'np', 'aq']:
            output.append(word[0])
        else:
            if word[1][0:1] == 'v':
                temp = nlp(word[0])[0].lemma_
                if temp not in ['ser', 'hacer', 'ir', 'decir', 'poder', 'estar', 'llevar', 'tener']:
                    output.append(temp)
    print(output)
    return output


def cargar_dialogos(dialogs, create_model):
    graph = nc.generate_graph()
    matcher = nc.generate_nodeMatcher(graph)
    num_dialog = len(dialogs)
    print("NUMERO DE DIALOGOS: " + str(num_dialog))
    # CARGAMOS EL MODELO
    jar = 'nlp/stanford-postagger.jar'
    model = 'nlp/spanish.tagger'
    # para descargar el modelo ejecutar como admin:
    # python -m spacy download es_core_news_md
    nlp = spacy.load('es_core_news_md')
    pos_tagger = StanfordPOSTagger(model, jar, encoding='utf8')
    temp = ''
    for dialog in dialogs:
        temp = temp + dialog[1]
    temp_list = list(set(temp.split(' ')))
    # TAGUEAMOS TODAS LAS PALABRAS DISTINTAS
    list_words_tagged = dialog_tagger(temp_list, nlp, pos_tagger, create_model)
    print("PALABRAS TAGGEADAS: " + str(len(list_words_tagged)))
    for dialog in dialogs:
        print('CARGAR DIALOGOS')
        diputado = nc.return_diputado(matcher, dialog[0])
        if diputado is None:
            print("PERSONA NO ENCONTRADA: ")
            print(dialog[0])
            print(dialog[1])
        else:
            for word in dialog[1].split(' '):
                if word in list_words_tagged:
                    graph.run(nc.insert_palabra(word))
                    palabra = nc.return_palabra(matcher, word)
                    graph.create(nc.insert_relation(diputado, palabra))
        num_dialog = num_dialog - 1
        print("DIALOGOS RESTANTES: " + str(num_dialog))
    graph.run(nc.palabras_dichas())


def generate_document(list_docs, params):
    for ind, doc in enumerate(list_docs):
        print('----------------------- DOCUMENTO ' + str(ind) + ' -----------------------')
        pagina_inicial = params[doc[0]]['pagina_inicial']
        frase_inicial = params[doc[0]]['frase_inicial']
        codigo_documento = params[doc[0]]['codigo_documento']
        graph = nc.generate_graph()
        matcher = nc.generate_nodeMatcher(graph)
        document = ''
        ix = 0
        sw_primera_vez = True
        for page in doc[1].pages:
            ix = ix + 1
            if ix >= pagina_inicial:
                text = page.extractText().lower().replace('\n', '')
                ini = remove_headers(text)
                if sw_primera_vez:
                    ini = ini + text[ini:].find(frase_inicial) + len(frase_inicial)
                    sw_primera_vez = False

                cl_text = clean_text(text[ini:], codigo_documento)

                regex = r"[ ][A-Za-z]+[:]"
                matches = re.finditer(regex, cl_text)
                for matchNum, match in enumerate(matches, start=1):
                    if match.group() != ' ' + presidencia + ':':
                        diputado = nc.busca_diputado(matcher, match.group()[1:-1])
                        if diputado is None:
                            document = document.replace(match.group(), match.group()[1:-1])

                document = document + cl_text + ' '
    return document


def main(create_model):
    params = {'doc_0.pdf': {'pagina_inicial': 5,
                            'frase_inicial': '(Prolongados aplausos del Grupo Parlamentario Socialista).',
                            'codigo_documento': 'cve: dscd-13-pl-2'},
              'doc_1.pdf': {'pagina_inicial': 3,
                            'frase_inicial': '',
                            'codigo_documento': 'cve: dscd-13-pl-3'},
              }

    list_docs = obtain_documents(params)

    document = generate_document(list_docs, params)

    dialogs = generate_dialogs(document)

    dialogs_clean = clean_dialogs(dialogs)

    cargar_dialogos(dialogs_clean, create_model)


if __name__ == '__main__':
    create_model = True
    main(create_model)
    print('FIN PROCESO')
