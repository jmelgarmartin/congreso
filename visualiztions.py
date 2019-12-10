import graphistry


def main():
    NEO4J_CREDS = {'uri': 'http://localhost:7474', 'auth': ('neo4j', 'capgemini')}
    graphistry.register(bolt=NEO4J_CREDS)
#    graphistry.cypher("MATCH g=(p:Palabra)<--(d:Diputado) WHERE p.veces > 3 RETURN g").plot()

    graphistry.cypher("CALL db.schema()").plot()

if __name__ == '__main__':
    main()
    print('FIN PROCESO')


