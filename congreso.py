import re

import PyPDF2
from nltk.corpus import stopwords
from nltk.tag import StanfordPOSTagger
from nltk.tokenize import word_tokenize
import spacy
import pickle

import neo4j_connector as nc

# variables generales para la configuracion del proceso
presidencia = 'presidenta'
vicepresidencia = 'vicepresidente'
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
    output = page.find("pág. ") + 6
    while True:
        if page[output: output + 1].isdigit():
            output = output + 1
        else:
            break
    return output


def clean_text(text, cod_docu):
    # arreglos especiales...... ye vere si puedo corregirlos mejor
    return text.replace(cod_docu, '').replace('momento:', 'momento') \
        .replace('rodrí guez', 'rodríguez').replace('catalunya', 'cataluña') \
        .replace('sanchez', 'sánchez') \
        .replace('cataluña:', 'cataluña').replace('sorprender:', 'sorprender') \
        .replace('matiz:', 'matiz').replace('yo se lo digo:', 'yo se lo digo') \
        .replace(' de:', ' de').replace('también:', 'también').replace('castejon', 'castejón') \
        .replace('cosas:', 'cosas').replace('lo repito:', 'lo repito') \
        .replace('y también dijo el señor maroto:', 'y también dijo el señor maroto') \
        .replace('decía el señor rivera:', 'decía el señor rivera') \
        .replace('puigdemont y la cup:', 'puigdemont y la cup') \
        .replace('rufián  parafraseando a borges:', 'rufián  parafraseando a borges') \
        .replace('(la señora ministra de hacienda, montero cuadrado:',
                 '(la señora ministra de hacienda, montero cuadrado') \
        .replace('sánchez es como un jinete que va en un caballo directo a un precipicio y lo que dice es:',
                 'sánchez es como un jinete que va en un caballo directo a un precipicio y lo que dice es') \
        .replace('lo que dice es:', 'lo que dice es') \
        .replace('sánchez decía:', 'sánchez decía').replace('sánchez dijo:', 'sánchez dijo') \
        .replace('sánchez  que fíjense si ha dicho cosas:', 'sánchez  que fíjense si ha dicho cosas') \
        .replace('incluso podría hablar con la señora arrimadas:', 'incluso podría hablar con la señora arrimadas') \
        .replace('ministra de hacienda  montero cuadrado:', 'ministra de hacienda  montero cuadrado') \
        .replace('patronos del señor sánchez:', 'patronos del señor sánchez') \
        .replace('victoria kent dijera:', 'victoria kent dijera').replace('borges:', 'borges') \
        .replace('?', '').replace('¿', '').replace('«', '').replace('»', '') \
        .replace('  ', ' ').replace('.', ' ').replace(',', ' ') \
        .replace('š', ' ').replace(';', ' ').replace('!', ' ').replace('¡', ' ') \
        .replace('–', ' ').replace(' : ', ': ')


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

def clean_separators(document):
    regex = r"[a-z]+:"
    matches = re.finditer(regex, document)
    output = document
    for matchNum, match in enumerate(matches, start=1):
        palabra = match.group()
        if palabra != 'cve:':
            reemplazo = palabra[:-1]
            output = output.replace(palabra, reemplazo)
    return output

def generate_dialogs(documents):
    outputs = []
    for document in documents:
        dialogs = []
        for element in split_text(document[0]):
            if element['pos_dialog_end'] == 0:
                dialogs.append([document[0][element['pos_ini']: element['pos_fin']],
                                document[0][element['pos_fin'] + 1:]])
            else:
                dialogs.append([document[0][element['pos_ini']: element['pos_fin']],
                                document[0][element['pos_fin'] + 1: element['pos_dialog_end']]])
        for ix, dialog in enumerate(dialogs):
            dialogs[ix][0] = clean_mr_mrs(clean_parenthesis(dialog[0]))
            dialogs[ix][1] = clean_mr_mrs(clean_parenthesis(dialog[1])).replace(':', ' ') \
                .replace('(', ' ').replace(')', ' ') \
                .replace('  ', ' ')
        output = []
        for dialog in dialogs:
            if dialog[0].find(presidencia) == -1:
                if dialog[0].find(vicepresidencia) == -1:
                    output.append(dialog)
        outputs.append([output, document[1].replace('cve: ', '')])
    return outputs


def clean_names(name):
    return name.replace('presidente del gobierno en funciones', 'sánchez pérez-castejón') \
        .replace('ministra de justicia en funciones', 'delgado garcía') \
        .replace('ministra de hacienda en funciones', 'montero cuadrado') \
        .replace('ministro del interior en funciones', 'grande-marlaska gómez') \
        .replace('rodrí guez hernández', 'rodríguez hernández') \
        .replace('ministro de agricultura pesca y alimentación en funciones', 'planas puchades') \
        .replace('ministro de fomento en funciones', 'ábalos meco') \
        .replace('ministra de economía y empresa en funciones', 'calviño santamaría') \
        .replace(' candidato a la presidencia del gobierno', '') \
        .replace('ministro de inclusión  seguridad social y migraciones', 'escrivá belmonte') \
        .replace('ministra de política territorial y función pública', 'darias san sebastián') \
        .replace('ministra de hacienda', 'montero cuadrado') \
        .replace('representante de la asamblea regional de murcia', 'conesa alcaraz') \
        .replace('de olano vela', 'olano vela') \
        .replace('ministro del interior', 'grande-marlaska gómez') \
        .replace('ministro de interior', 'grande-marlaska gómez') \
        .replace('ministro de agricultura pesca y alimentación', 'planas puchades') \
        .replace('ministro de transportes movilidad y agenda urbana', 'ábalos meco') \
        .replace('presidente del gobierno', 'sánchez pérez-castejón') \
        .replace('ministro de sanidad', 'illa roca')


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
        salto = 800
        a = len(dialog)
        b = 0
        print(a)
        while b < a:
            try:
                with open('words.pickle', 'rb') as handle:
                    words = pickle.load(handle)
                    words.extend(pos_tagger.tag(dialog[b:b + salto]))
                    with open('words.pickle', 'wb') as handle:
                        pickle.dump(words, handle, protocol=pickle.HIGHEST_PROTOCOL)
            except:
                print("CREAMOS NUEVO MODELO")
                words = pos_tagger.tag(dialog[b:b + salto])
                with open('words.pickle', 'wb') as handle:
                    pickle.dump(words, handle, protocol=pickle.HIGHEST_PROTOCOL)
            b = b + salto - 1
    else:
        with open('words.pickle', 'rb') as handle:
            words = pickle.load(handle)

    print("MODELO TERMINADO")
    words = list(set(words))
    output = []

    for word in words:
        temp = nlp(word[0])[0].lemma_
        if word[1][0:2] in ['nc', 'np', 'aq']:
            if temp not in ['así', 'parte', 'puede', 'hace', 'hacer', 'diputado', 'diputados', '%']:
                output.append(temp)
        else:
            if word[1][0:1] == 'v':
                if temp not in ['ser', 'hacer', 'ir', 'decir', 'poder', 'estar', 'llevar', 'tener', 'querer', 'ser']:
                    output.append(temp)

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
        temp = temp + dialog[1] + ' '
    temp_list = temp.split(' ')
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
                try:
                    lemma = nlp(word)[0].lemma_
                    if lemma in list_words_tagged:
                        graph.run(nc.insert_palabra(word))
                        graph.run(nc.insert_relation(diputado['apellidos'], word, dialog[2]))
                except:
                    pass

        num_dialog = num_dialog - 1
        print("DIALOGOS RESTANTES: " + str(num_dialog))

    graph.run(nc.palabras_dichas())
    graph.run(nc.add_labels_diputados())
    graph.run(nc.add_labels_palabras())


def clean_document(document):
    #esto es para corregir cosas anómalas añadimos, poder eliminar con regex todas las palabras en minúsculas que acaben con :


    return document.replace(
        '(aplausos  la señora ministra de hacienda  montero cuadrado:  ahora )', '').replace(
        '(el señor betoret coll:  cuéntanos el pacto con esquerra  rumores)', '').replace(
        'la señora presidenta: señorías, por favor, guarden silencio.', '').replace(
        '(el señor casado blanco: el qué  el qué)', '').replace(
        '(protestas  el señor de olano vela:  fuisteis vosotros  que tenéis mucha cara )', '').replace(
        'presidenta: señorías', '').replace(
        '(el señor sánchez pérez-castejón  candidato a la presidencia del gobierno:  ya  ya  rumores  aplausos)',
        '').replace('(la señora olano choclán:  qué vergüenza )', '').replace(
        '(protestas  un señordiputado  venga ya  el señor espinosa de los monteros simón:  a mí me daría vergüenza )',
        '').replace('casado  ha dicho literalmente:', 'casado  ha dicho literalmente').replace(
        'de la mesa el partido de la señora arrimadas:', 'de la mesa el partido de la señora arrimadas').replace(
        '(la señora ministra de hacienda en funciones  montero cuadrado:  hombre   derrotados )', '').replace(
        'el señora', 'la señora').replace('  ', ' ')


def generate_documents(list_docs, params):
    documents = []
    for ind, doc in enumerate(list_docs):
        document = ''
        print('----------------------- DOCUMENTO ' + str(ind) + ' -----------------------')
        pagina_inicial = params[doc[0]]['pagina_inicial']
        frase_inicial = params[doc[0]]['frase_inicial']
        codigo_documento = params[doc[0]]['codigo_documento']
        graph = nc.generate_graph()
        matcher = nc.generate_nodeMatcher(graph)
        ix = 0
        sw_primera_vez = True
        for page in doc[1].pages:
            ix = ix + 1
            if ix >= pagina_inicial:
                text = clean_separators(page.extractText().replace('\n', '')).lower()
                ini = remove_headers(text)
                if sw_primera_vez:
                    ini = ini + text[ini:].find(frase_inicial) + len(frase_inicial)
                    sw_primera_vez = False

                cl_text = clean_text(text[ini:], codigo_documento)

                regex = r"[ ][A-Za-z]+[:]"
                matches = re.finditer(regex, cl_text)
                for matchNum, match in enumerate(matches, start=1):
                    if (match.group() != ' ' + presidencia + ':') and (match.group() != ' ' + vicepresidencia + ':'):
                        diputado = nc.busca_diputado(matcher, match.group()[1:-1])
                        if diputado is None:
                            document = document.replace(match.group(), match.group()[1:-1])

                document = document + cl_text + ' '
        documents.append([clean_parenthesis(clean_document(document)), codigo_documento])
    return documents


def main(create_model, params):
    list_docs = obtain_documents(params)

    documents = generate_documents(list_docs, params)

    dialogs = generate_dialogs(documents)

    dialogs_clean = []
    for dialog, doc in dialogs:
        for cl_dialog in clean_dialogs(dialog):
            dialogs_clean.append([cl_dialog[0], cl_dialog[1], doc])

    cargar_dialogos(dialogs_clean, create_model)


if __name__ == '__main__':
    create_model = False
    params = {
#        'DSCD-14-PL-2.PDF': {'pagina_inicial': 7,
#                             'frase_inicial': '',
#                             'codigo_documento': 'cve: DSCD-14-PL-2'.lower()},
#        'DSCD-14-PL-3.PDF': {'pagina_inicial': 2,
#                             'frase_inicial': 'Se reanuda la sesión a las nueve de la mañana.',
#                             'codigo_documento': 'cve: DSCD-14-PL-3'.lower()},
#        'DSCD-14-PL-4.PDF': {'pagina_inicial': 2,
#                             'frase_inicial': 'y de algunos del Grupo Parlamentario Plural).',
#                             'codigo_documento': 'cve: DSCD-14-PL-4'.lower()},
#               # el 5 no existe, va por semanas, creo
#        'DSCD-14-PL-6.PDF': {'pagina_inicial': 6,
#                             'frase_inicial': 'SISTEMA DE SEGURIDAD SOCIAL. (Número de expediente 130/000002).',
#                             'codigo_documento': 'cve: DSCD-14-PL-6'.lower()},
#        'DSCD-14-PL-7.PDF': {'pagina_inicial': 7,
#                             'frase_inicial': 'Número de expediente 155/000003).',
#                             'codigo_documento': 'cve: DSCD-14-PL-7'.lower()},
        'DSCD-14-PL-8.PDF': {'pagina_inicial': 5,
                             'frase_inicial': '',
                             'codigo_documento': 'cve: DSCD-14-PL-8'.lower()},
#        'DSCD-14-PL-9.PDF': {'pagina_inicial': 6,
#                             'frase_inicial': 'presentación de esta iniciativa tiene la palabra el señor Rojas García.',
#                             'codigo_documento': 'cve: DSCD-14-PL-9'.lower()},
#        'DSCD-14-PL-10.PDF': {'pagina_inicial': 5,
#                              'frase_inicial': '(Número de expediente 180/000025).',
#                              'codigo_documento': 'cve: DSCD-14-PL-10'.lower()},
    }
    main(create_model, params)
    print('FIN PROCESO')
