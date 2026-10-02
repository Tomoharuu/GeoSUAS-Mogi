import folium

m = folium.Map((-23.55233585417125, -46.18997249002586), zoom_start=11)

popup = folium.GeoJsonPopup(fields=["NOME","CRAS", "CREAS"])
popup2 = folium.GeoJsonPopup(fields=["NOME","CRAS", "CREAS"])
popup3 = folium.GeoJsonPopup(fields=["NOME","CRAS", "CREAS"])
geo_json_data = 'bairros_mogi.geojson'

cras = folium.FeatureGroup(name="CRAS", show=True).add_to(m)
creas = folium.FeatureGroup(name="CREAS", show=False).add_to(m)
conselho_tutelar = folium.FeatureGroup(name="Conselho Tutelar", show=False).add_to(m)

camada_cras = folium.GeoJson(
    geo_json_data,
    style_function=lambda feature: {
        "fillColor": 
        "purple" if "CRAS Centro" == feature["properties"]["CRAS"] else
        "brown" if "CRAS Cesar de Souza" == feature["properties"]["CRAS"] else
        "orange" if "CRAS Jardim Layr" == feature["properties"]["CRAS"] else
        "red" if "CRAS Jundiapeba I" == feature["properties"]["CRAS"] else
        "gray" if "CRAS Jundiapeba II" == feature["properties"]["CRAS"] else
        "green" if "CRAS Vila Brasileira" == feature["properties"]["CRAS"] else
        "blue" if "CRAS Vila Nova Uniao" == feature["properties"]["CRAS"] else
        "#ffff00",


        "color": 
        "purple" if "CRAS Centro" == feature["properties"]["CRAS"] else
        "brown" if "CRAS Cesar de Souza" == feature["properties"]["CRAS"] else
        "orange" if "CRAS Jardim Layr" == feature["properties"]["CRAS"] else
        "red" if "CRAS Jundiapeba I" == feature["properties"]["CRAS"] else
        "gray" if "CRAS Jundiapeba II" == feature["properties"]["CRAS"] else
        "green" if "CRAS Vila Brasileira" == feature["properties"]["CRAS"] else
        "blue" if "CRAS Vila Nova Uniao" == feature["properties"]["CRAS"] else
        "#ffff00",
        "weight": 1

    },
    popup=popup,
    popup_keep_highlighted=True,
).add_to(cras)


folium.GeoJson(
    geo_json_data,
    style_function=lambda feature: {
        "fillColor": 
        "red" if "CREAS Bras Cubas" == feature["properties"]["CREAS"] else
        "blue" if "CREAS Centro" == feature["properties"]["CREAS"] else
        "green" if "CREAS Jundiapeba" == feature["properties"]["CREAS"] else
        "#ffff00",


        "color": 
        "red" if "CREAS Bras Cubas" == feature["properties"]["CREAS"] else
        "blue" if "CREAS Centro" == feature["properties"]["CREAS"] else
        "green" if "CREAS Jundiapeba" == feature["properties"]["CREAS"] else
        "#ffff00",
        "weight": 1

    },
    popup=popup2,
    popup_keep_highlighted=True,
).add_to(creas)

folium.GeoJson(
    geo_json_data,
    style_function=lambda feature: {
        "fillColor": 
        "blue" if "Conselho Tutelar Bras Cubas" == feature["properties"]["CONSELHO TUTELAR"] else
        "red" if "Conselho Tutelar Centro" == feature["properties"]["CONSELHO TUTELAR"] else
        "green" if "Conselho Tutelar Cesar de Souza" == feature["properties"]["CONSELHO TUTELAR"] else
        "purple" if "Conselho Tutelar Jundiapeba" == feature["properties"]["CONSELHO TUTELAR"] else
        "#ffff00",


        "color": 
        "blue" if "Conselho Tutelar Bras Cubas" == feature["properties"]["CONSELHO TUTELAR"] else
        "red" if "Conselho Tutelar Centro" == feature["properties"]["CONSELHO TUTELAR"] else
        "green" if "Conselho Tutelar Cesar de Souza" == feature["properties"]["CONSELHO TUTELAR"] else
        "purple" if "Conselho Tutelar Jundiapeba" == feature["properties"]["CONSELHO TUTELAR"] else
        "#ffff00",
        "weight": 1

    },
    popup=popup3,
    popup_keep_highlighted=True,
).add_to(conselho_tutelar)


cras.add_to(m)
creas.add_to(m)
conselho_tutelar.add_to(m)


from folium.plugins import GroupedLayerControl

GroupedLayerControl(
    groups={
        'Mapas': [cras, creas, conselho_tutelar]
    },
    collapsed=False  # Set to True to collapse the control by default
).add_to(m)

folium.plugins.Geocoder(add_marker=True, zoom=16, provider="nominatim", placeholder="Busca por Endereço", position="topright").add_to(m)

from folium.plugins import Search
statesearch = Search(
    layer=camada_cras,
    geom_type="Polygon",
    placeholder="Busca por Bairro                        ",
    collapsed=False,
    search_label="NOME",
    weight=1,
    position="topright"
).add_to(m)


import pandas as pd
sheet_id = "1BiVm9wWnWdpBOsUoHi2UIqZYwX4EyBpg"

df = pd.read_excel(f"https://docs.google.com/spreadsheets/export?id={sheet_id}&format=xlsx")

from pandasql import sqldf
query = '''
SELECT DISTINCT Categoria
from df
WHERE Status == "Ativo" AND Secretaria == "Assistência"
'''
query = sqldf(query, globals())
names_list = query['Categoria'].tolist()
#print(names_list)

lista = ["Serviço de Acolhimento Institucional para Crianças e Adolescentes", "Serviço de Convivência e Fortalecimento de Vínculos para crianças/ adolescentes"]
lista = names_list
combinado = []
for item in lista:
    item = folium.FeatureGroup(name=item, show=False).add_to(m)
    combinado.append(item)


for index, row in df.iterrows():
    for i, categoria in enumerate(lista):
        if row['Categoria'] == categoria and row['Secretaria'] == 'Assistência' and row['Status'] == 'Ativo':
            folium.Marker(
                location=[row['Longitude'], row['Latitude']],
                tooltip=f"""<div><ul style="background-color:LightSkyBlue; padding:5px">
                <b>{row['Rede de equipamento']}</b></ul>
                <b>Categoria</b><br>{row['Categoria']}<br><br>
                <b>Endereço</b><br>{row['Endereço']}
                </div>""",
                popup=f"""<div style="width:500px"><ul style="background-color:LightSkyBlue; padding:5px">
                <b>{row['Rede de equipamento']}</b></ul>
                <b>Categoria</b><br>{row['Categoria']}<br><br>
                <b>Endereço</b><br>{row['Endereço']}<br><br>
                <img 
                style="max-height:200px; display: block; margin-left: auto; margin-right: auto;" 
                src="{row['Imagem']}">
                </div>""",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(combinado[i])



from folium.plugins import GroupedLayerControl

GroupedLayerControl(
    groups={
        'Serviços Socioassistenciais': combinado
    },
    collapsed=True, 
    exclusive_groups=False,
    position = 'topleft'
).add_to(m)


m.save("index.html")

