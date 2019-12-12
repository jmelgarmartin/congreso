import dash
import dash_cytoscape as cyto
import dash_html_components as html
import pandas as pd

import neo4j_connector as nc

graph = nc.generate_graph()
print(nc.add_labels_diputados())
graph.run(nc.add_labels_diputados())
graph.run(nc.add_labels_palabras())

df = pd.DataFrame(graph.run(nc.return_graph()).to_data_frame())
print('--------')
print(df)
print('--------')
diputados = list(set(df['diputado'].to_list()))
palabras = list(set(df['palabra'].to_list()))
print(diputados)
print(palabras)

app = dash.Dash(__name__)
app.layout = html.Div([
    cyto.Cytoscape(
        id='cytoscape',
        elements=[
            {'data': {'id': 'one', 'label': 'Node 1'}, 'position': {'x': 50, 'y': 50}},
            {'data': {'id': 'two', 'label': 'Node 2'}, 'position': {'x': 200, 'y': 200}},
            {'data': {'source': 'one', 'target': 'two', 'label': 'Node 1 to 2'}}
        ],
        layout={'name': 'preset'}
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
