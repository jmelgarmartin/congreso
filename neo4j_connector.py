from py2neo import Graph, NodeMatcher, Relationship


def generate_graph():
    neo4j_user = 'neo4j'
    #    neo4j_pass = 'congreso'
    neo4j_pass = 'capgemini'
    return Graph(secure=True, auth=(neo4j_user, neo4j_pass))


def insert_diputado(diputado):
    query = 'MERGE (d:Diputado {apellidos: "' + diputado['apellidos'].strip() + '"}) '
    query = query + 'ON CREATE SET d.nombre = "' + diputado['nombre'].strip() + '" , '
    query = query + 'd.apellidos = "' + diputado['apellidos'].strip() + '" , '
    query = query + 'd.grupo = "' + diputado['grupo'].strip() + '" RETURN d'
    return query


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


def insert_relation(diputado, palabra):
    return Relationship(diputado, 'DICE', palabra)
