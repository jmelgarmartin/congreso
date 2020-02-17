from py2neo import Graph, NodeMatcher, Relationship


def generate_graph():
    neo4j_user = 'neo4j'
    #    neo4j_pass = 'congreso'
    neo4j_pass = 'atsistemas'
    return Graph(secure=True, auth=(neo4j_user, neo4j_pass))


def insert_diputado(diputado):
    query = 'MERGE (d:Diputado {apellidos: "' + diputado['apellidos'].strip() + '"}) '
    query = query + 'ON CREATE SET d.nombre = "' + diputado['nombre'].strip() + '" , '
    query = query + 'd.apellidos = "' + diputado['apellidos'].strip() + '" , '
    query = query + 'd.grupo = "' + diputado['grupo'].strip() + '" RETURN d'
    return query


def asignar_partidos():
    # AÑADIR NUEVOS LABELS A UN NODO
    # AÑADIMOS COMO TIPO DE NODO EL PARTIDO A CADA DIPUTADO
    query = 'MATCH (d:Diputado) '
    query = query + 'WITH d, d.grupo as group '
    query = query + 'CALL apoc.create.addLabels(d, [group]) YIELD node '
    query = query + 'RETURN count(d) as count'
    return query


def palabras_dichas():
    # ACTUALIZAR NUMERO DE VECES QUE SE DICE UNA PALABRA
    query = 'MATCH (:Diputado)-[r]->(p:Palabra) '
    query = query + 'WITH p.palabra as pal, SUM(r.veces) as veces '
    query = query + 'MATCH (pala:Palabra) '
    query = query + 'WHERE pala.palabra = pal '
    query = query + 'SET pala.veces = veces '
    return query

def add_labels_diputados():
    # Para Cytoscape
    return '''
    MATCH (d:Diputado) 
    SET d.label = d.apellidos + ' '  + d.nombre ,
    d.veces = 50
    RETURN d
    '''

def add_labels_palabras():
    # Para Cytoscape
    return '''
       MATCH (p:Palabra) 
       SET p.label = p.palabra 
       RETURN p
       '''


def insert_palabra(palabra):
    query = 'MERGE (p:Palabra {palabra: "' + palabra.strip() + '"}) '
    query = query + 'ON CREATE SET p.palabra = "' + palabra.strip() + '" RETURN p'
    return query


def generate_nodeMatcher(graph):
    return NodeMatcher(graph)


def busca_diputado(matcher, word):
    return matcher.match("Diputado", apellidos__contains=word).first()


def return_diputado(matcher, apellidos):
    return matcher.match("Diputado", apellidos=apellidos).first()


def return_palabra(matcher, palabra):
    return matcher.match("Palabra", palabra=palabra).first()

def return_lista_palabras():
    return 'MATCH (p:Palabra) RETURN p'

def return_grupos_palabras(palabra):
    query = 'MATCH(d: Diputado)-[r: DICE]->(p:Palabra) '
    query = query + 'WHERE p.palabra = "' + palabra + '" '
    query = query + 'RETURN DISTINCT(d.grupo) as grupo'
    return query


def insert_relation(diputado, palabra):
    query ='MATCH(d: Diputado {apellidos: "' + diputado + '"}) '
    query = query + 'MERGE (p:Palabra {palabra: "' + palabra + '"}) '
    query = query + 'MERGE (d) -[r:DICE]->(p) '
    query = query + 'ON CREATE SET r.veces = 1, r.grupo = d.grupo '
    query = query + 'ON MATCH SET r.veces = r.veces + 1'
    return query

def return_graph():
    return '''MATCH (d:Diputado)-[r]->(p:Palabra) 
    WHERE p.veces > 2 
    RETURN d as diputado, p as palabra 
    LIMIT 25
    '''



