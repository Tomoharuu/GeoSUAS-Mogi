import json

import folium
import geopandas as gpd
import pandas as pd
from branca.element import Element
from folium.plugins import Search


ARQUIVO_KML = "ABAIRRAMENTO.kml"
ARQUIVO_DIVISAO = "divisao_bairros.csv"
ARQUIVO_CAD = "cad_geral.csv"
ARQUIVO_EQUIPAMENTOS = "dados_servicos.csv"
ARQUIVO_SAIDA = "mapa_cras.html"

QUANTIDADE_MAIORES_BAIRROS = 12
BAIRRO_SEMPRE_MOSTRAR = "CENTRO"


CORES = {
    "cras": {
        "CRAS CENTRO": "red",
        "CRAS CÉSAR DE SOUZA": "blue",
        "CRAS JARDIM LAYR": "green",
        "CRAS JUNDIAPEBA I": "orange",
        "CRAS JUNDIAPEBA II": "yellow",
        "CRAS VILA BRASILEIRA": "purple",
        "CRAS VILA NOVA UNIÃO": "pink",
    },
    "creas": {
        "CREAS CENTRO": "red",
        "CREAS BRÁS CUBAS": "blue",
        "CREAS JUNDIAPEBA": "green",
    },
    "conselho": {
        "CONSELHO TUTELAR CENTRO": "red",
        "CONSELHO TUTELAR BRÁS CUBAS": "blue",
        "CONSELHO TUTELAR CÉSAR DE SOUZA": "green",
        "CONSELHO TUTELAR JUNDIAPEBA": "orange",
    },
}

def adicionar_html(mapa, conteudo):
    """Adiciona CSS ou JavaScript ao HTML do mapa."""
    mapa.get_root().html.add_child(Element(conteudo))


def limpar(valor):
    """Converte valores vazios/NaN para string vazia."""
    return "" if pd.isna(valor) else str(valor)


def json_js(dados):
    """Converte dados Python para JSON utilizável no JavaScript."""
    return json.dumps(dados, ensure_ascii=False)


gdf = gpd.read_file(ARQUIVO_KML, driver="KML")
df_cras = pd.read_csv(ARQUIVO_DIVISAO)
df_cad = pd.read_csv(ARQUIVO_CAD)
df_equipamentos = pd.read_csv(ARQUIVO_EQUIPAMENTOS)


gdf = gdf.merge(df_cras, on="NOME", how="left")

dados_bairros = {}

for _, linha in df_cras.iterrows():
    bairro = linha["Bairro Ajustado"]

    if pd.isna(bairro):
        continue

    dados_bairros[bairro] = {
        "cras": linha["CRAS"],
        "creas": linha["CREAS"],
        "conselho_tutelar": linha["Conselho Tutelar"],
    }


dados_cad = {}

for _, linha in df_cad.iterrows():
    mes = linha["MÊS"]
    medida = linha["MEDIDA"]

    if pd.isna(mes) or pd.isna(medida):
        continue

    for bairro in df_cad.columns[1:-1]:
        dados_cad.setdefault(bairro, {}).setdefault(mes, {})[
            medida
        ] = "" if pd.isna(linha[bairro]) else linha[bairro]


for bairro, dados in dados_cad.items():
    dados_bairros.setdefault(bairro, {})["cad_geral"] = dados

gdf_area = gdf.to_crs("EPSG:31983")
gdf_area["area_m2"] = gdf_area.geometry.area

maiores_bairros = (
    gdf_area.nlargest(
        QUANTIDADE_MAIORES_BAIRROS,
        "area_m2",
    )["Bairro Ajustado"]
    .dropna()
    .tolist()
)

if BAIRRO_SEMPRE_MOSTRAR not in maiores_bairros:
    maiores_bairros.append(BAIRRO_SEMPRE_MOSTRAR)


centro = gdf.geometry.union_all().centroid

m = folium.Map(
    location=[centro.y, centro.x],
    zoom_start=11,
    tiles=None,
)

folium.TileLayer(
    tiles=(
        "https://server.arcgisonline.com/"
        "ArcGIS/rest/services/"
        "World_Topo_Map/"
        "MapServer/tile/{z}/{y}/{x}"
    ),
    attr="Esri",
    name="Esri Topográfico",
    overlay=False,
    control=True,
).add_to(m)

mapa_nome = m.get_name()


def definir_estilo(feature):
    cras = feature["properties"].get("CRAS", "")

    return {
        "fillColor": CORES["cras"].get(cras, "gray"),
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.3,
    }


geojson = folium.GeoJson(
    gdf,
    style_function=definir_estilo,
).add_to(m)

geojson_nome = geojson.get_name()


javascript_bairros = f"""
<script>
const dadosBairros = {json_js(dados_bairros)};
const maioresBairros = {json_js(maiores_bairros)};
const coresMapas = {json_js(CORES)};

let tipoMapaAtual = "cras";

function obterCorBairro(feature) {{
    if (!feature?.properties) return "gray";

    const propriedade = {{
        cras: "CRAS",
        creas: "CREAS",
        conselho: "Conselho Tutelar"
    }}[tipoMapaAtual];

    const equipamento = feature.properties[propriedade] || "";

    return coresMapas[tipoMapaAtual]?.[equipamento] || "gray";
}}

function atualizarCoresMapa() {{
    {geojson_nome}.eachLayer(layer => {{
        layer.setStyle({{
            fillColor: obterCorBairro(layer.feature),
            color: "black",
            weight: 1,
            fillOpacity: 0.3
        }});
    }});
}}

function trocarTipoMapa(tipo) {{
    if (!["cras", "creas", "conselho"].includes(tipo)) {{
        tipo = "cras";
    }}

    tipoMapaAtual = tipo;
    atualizarCoresMapa();
}}

document.addEventListener("DOMContentLoaded", function() {{

    {geojson_nome}.eachLayer(layer => {{

        layer.on("click", function() {{

            const bairro =
                layer.feature.properties["Bairro Ajustado"];

            const dados = dadosBairros[bairro] || {{}};

            window.parent.postMessage({{
                tipo: "bairro_clicado",
                bairro: bairro,
                cras: dados.cras || "Não informado",
                creas: dados.creas || "Não informado",
                conselho_tutelar:
                    dados.conselho_tutelar || "Não informado",
                cad_geral: dados.cad_geral || {{}}
            }}, "*");
        }});
    }});

    atualizarCoresMapa();
}});

window.addEventListener("message", function(event) {{

    if (!event.data) return;

    if (event.data.tipo === "trocar_mapa") {{
        trocarTipoMapa(event.data.mapa);
    }}
}});
</script>
"""

adicionar_html(m, javascript_bairros)


Search(
    layer=geojson,
    geom_type="Polygon",
    placeholder="Busca por Bairro (ex: JARDIM CAMILA)",
    collapsed=False,
    search_label="Bairro Ajustado",
    weight=1,
    position="topright",
    case_sensitive=False,
    initial=False,
).add_to(m)


for _, linha in gdf.iterrows():

    bairro = linha["Bairro Ajustado"]

    if pd.isna(bairro):
        continue

    ponto = linha.geometry.representative_point()

    folium.Marker(
        location=[ponto.y, ponto.x],
        icon=folium.DivIcon(
            html=(
                f'<div class="texto-bairro" '
                f'data-bairro="{bairro}">{bairro}</div>'
            ),
            class_name="marcador-bairro",
        ),
    ).add_to(m)


css_nomes = """
<style>
.marcador-bairro.leaflet-interactive {
    background: transparent !important;
    pointer-events: none !important;
    border: none !important;
    box-shadow: none !important;
}

.texto-bairro {
    display: none;
    position: absolute;
    pointer-events: none;
    color: #222;
    background: rgba(255, 255, 255, 0.80);
    border: 1px solid rgba(0, 0, 0, 0.25);
    border-radius: 6px;
    padding: 3px 7px;
    font-size: 10px;
    font-weight: bold;
    white-space: nowrap;
    text-align: center;
    width: max-content;
    transform: translate(-50%, -50%);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
}
</style>
"""

adicionar_html(m, css_nomes)


javascript_nomes = f"""
<script>
document.addEventListener("DOMContentLoaded", function() {{

    function atualizarNomesBairros() {{

        const zoom = {mapa_nome}.getZoom();

        document.querySelectorAll(".texto-bairro").forEach(nome => {{

            const bairro = nome.dataset.bairro;

            nome.style.display =
                zoom >= 13 || maioresBairros.includes(bairro)
                    ? "block"
                    : "none";
        }});
    }}

    {mapa_nome}.on("zoomend", atualizarNomesBairros);

    atualizarNomesBairros();
}});
</script>
"""

adicionar_html(m, javascript_nomes)


df_equipamentos["Status"] = (
    df_equipamentos["Status"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
)

df_equipamentos = df_equipamentos[
    df_equipamentos["Status"] == "ativo"
].copy()


for coluna in ["Latitude", "Longitude"]:
    df_equipamentos[coluna] = pd.to_numeric(
        df_equipamentos[coluna]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(",", ".", regex=False),
        errors="coerce",
    )

df_equipamentos.dropna(
    subset=["Latitude", "Longitude"],
    inplace=True,
)


categorias_equipamentos = sorted(
    {
        limpar(categoria)
        for categoria in df_equipamentos["Categoria"]
        if limpar(categoria)
    },
    key=str.casefold,
)


equipamentos_layer = folium.FeatureGroup(
    name="Equipamentos",
    show=False,
)

servicos_busca = []


for indice, (_, linha) in enumerate(
    df_equipamentos.iterrows()
):

    campos = {
        chave: limpar(linha.get(coluna, ""))
        for chave, coluna in {
            "nome": "Rede de equipamento",
            "secretaria": "Secretaria",
            "categoria": "Categoria",
            "endereco": "Endereço",
            "bairro": "Bairro",
            "telefone": "Telefone",
            "status": "Status",
            "observacao": "Observação",
            "imagem": "Imagem",
        }.items()
    }

    popup_html = f"""
    <div style="
        width:400px;
        max-height:450px;
        overflow-y:auto;
        font-family:Arial,sans-serif;
    ">

        <h3 style="
            margin:0 0 2px;
            font-size:12px;
            font-weight:bold;
            background-color:LightSkyBlue;
            padding:5px;
        ">
            {campos["nome"]}
        </h3>

        <p>
            <b>Categoria:</b><br>
            {campos["categoria"]}
        </p>

        <p>
            <b>Endereço:</b> {campos["endereco"]}<br>
            <b>Bairro:</b> {campos["bairro"]}<br>
            <b>Telefone:</b> {campos["telefone"]}
        </p>

        <p>
            <b>Observação:</b><br>
            {campos["observacao"]}
        </p>
    """

    if campos["imagem"]:
        popup_html += f"""
        <div style="margin-top:10px;">
            <img
                src="{campos["imagem"]}"
                style="
                    max-width:100%;
                    max-height:200px;
                    border-radius:6px;
                "
            >
        </div>
        """

    popup_html += "</div>"

    marcador = folium.Marker(
        location=[
            linha["Latitude"],
            linha["Longitude"],
        ],
        popup=folium.Popup(
            popup_html,
            max_width=400,
        ),
        tooltip=campos["nome"],
        icon=folium.Icon(
            color="blue",
            icon="info-sign",
        ),
    )

    marcador.options["categoriaEquipamento"] = campos["categoria"]
    marcador.options["indiceEquipamento"] = indice

    marcador.add_to(equipamentos_layer)

    servicos_busca.append({
        "id": indice,
        "nome": campos["nome"],
        "categoria": campos["categoria"],
        "endereco": campos["endereco"],
        "bairro": campos["bairro"],
        "latitude": linha["Latitude"],
        "longitude": linha["Longitude"],
    })


equipamentos_layer.add_to(m)

equipamentos_nome = equipamentos_layer.get_name()


javascript_equipamentos = f"""
<script>
const categoriasEquipamentos =
    {json_js(categorias_equipamentos)};

const servicosBusca =
    {json_js(servicos_busca)};

let mostrarEquipamentos = false;
let categoriasSelecionadas = [];

document.addEventListener("DOMContentLoaded", function() {{

    window.parent.postMessage({{
        tipo: "categorias_equipamentos",
        categorias: categoriasEquipamentos
    }}, "*");

    window.parent.postMessage({{
        tipo: "servicos_equipamentos",
        servicos: servicosBusca
    }}, "*");
}});


function atualizarEquipamentos() {{

    {equipamentos_nome}.eachLayer(marker => {{

        const categoria =
            marker.options.categoriaEquipamento || "";

        const categoriaVisivel =
            !categoriasSelecionadas.length ||
            categoriasSelecionadas.includes(categoria);

        if (mostrarEquipamentos && categoriaVisivel) {{
            marker.addTo({mapa_nome});
        }} else {{
            {mapa_nome}.removeLayer(marker);
        }}
    }});
}}


function localizarServico(id) {{

    let encontrado = null;

    {equipamentos_nome}.eachLayer(marker => {{

        if (marker.options.indiceEquipamento === id) {{
            encontrado = marker;
        }}

        {mapa_nome}.removeLayer(marker);
    }});

    if (!encontrado) return;

    const latLng = encontrado.getLatLng();

    encontrado.addTo({mapa_nome});

    {mapa_nome}.setView(
        latLng,
        Math.max({mapa_nome}.getZoom(), 16),
        {{ animate: true }}
    );

    setTimeout(() => {{
        encontrado.openPopup();
    }}, 400);
}}



window.addEventListener("message", function(event) {{

    if (!event.data) return;

    switch (event.data.tipo) {{

        case "toggle_equipamentos":
            mostrarEquipamentos =
                Boolean(event.data.mostrar);
            atualizarEquipamentos();
            break;

        case "filtro_equipamentos":
            categoriasSelecionadas =
                event.data.categorias || [];
            atualizarEquipamentos();
            break;

        case "localizar_servico":
            localizarServico(event.data.id);
            break;

        case "trocar_mapa":
            trocarTipoMapa(event.data.mapa);
            break;
    }}
}});
</script>
"""

adicionar_html(m, javascript_equipamentos)

m.save(ARQUIVO_SAIDA)
print("Operação concluída com sucesso!")