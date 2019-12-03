import re
from py2neo import Graph


def load_diputados(diputados):
    neo4j_user = 'neo4j'
    neo4j_pass = 'congreso'
    graph = Graph(secure=True, auth=(neo4j_user, neo4j_pass))
    graph.delete_all()
    graph.run('CREATE CONSTRAINT ON (d:Diputado) ASSERT d.apellidos IS UNIQUE')
    for diputado in diputados:
        query = 'MERGE (d:Diputado {apellidos: "' + diputado['apellidos'].strip() + '"}) '
        query = query + 'ON CREATE SET d.nombre = "' + diputado['nombre'].strip() + '" , '
        query = query + 'd.apellidos = "' + diputado['apellidos'].strip() + '" , '
        query = query + 'd.grupo = "' + diputado['grupo'].strip() + '" RETURN d'
        graph.run(query)


def main():
    f_diputados = open('diputados.txt', 'r').readlines()
    grupos = []
    groups_names = {
        '(GCUP-EC-GC)': 'Grupo Podemos',
        '(GV (EAJ-PNV))': 'Grupo Vasco',
        '(GR)': 'Grupo Republicano',
        '(GCs)': 'Grupo Ciudadanos',
        '(GVOX)': 'Grupo Vox',
        '(GMx)': 'Grupo Mixto',
        '(GS)': 'Grupo Socialista',
        '(GP)': 'Grupo Popular'
    }
    diputados = []
    for line in f_diputados:
        data = line.replace('\n', '')

        if data != '':
            apellidos, nombre = data.split(',')
            regex = r" [(].*[)]"
            matches = re.findall(regex, nombre)
            nombre = nombre.replace(matches[0], '').lstrip()
            grupo = groups_names[matches[0].lstrip()]
            diputado = {'apellidos': apellidos.lower(),
                        'nombre': nombre.lower(),
                        'grupo': grupo}
            diputados.append(diputado)

    load_diputados(diputados)


if __name__ == '__main__':
    main()
