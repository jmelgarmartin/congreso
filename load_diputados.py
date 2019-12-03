import re
import neo4j_connector as nc


def load_diputados(diputados):
    graph = nc.generate_graph()
    graph.delete_all()
    graph.run('CREATE CONSTRAINT ON (d:Diputado) ASSERT d.apellidos IS UNIQUE')
    graph.run('CREATE CONSTRAINT ON p:Palabra) ASSERT p.palabra IS UNIQUE')
    for diputado in diputados:
        graph.run(nc.insert_diputado(diputado))


def main():
    f_diputados = open('diputados.txt', 'r').readlines()
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
