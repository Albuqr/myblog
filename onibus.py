
import os
import requests
from dotenv import load_dotenv
import folium
from statistics import mean

load_dotenv()

SPTRANS_TOKEN = os.getenv("SPTRANS_TOKEN")
TERMO_BUSCA_LINHA = os.getenv("LINHA_TERMO_BUSCA", "Lapa")
CODIGO_LINHA = os.getenv("CODIGO_LINHA")

URL = "http://api.olhovivo.sptrans.com.br/v2.1"


def autsessao():
    if not SPTRANS_TOKEN:
        raise ValueError("Token invalido ou não definido")

    s = requests.Session()
    res = s.post(f"{URL}/Login/Autenticar?token={SPTRANS_TOKEN}")
    if res.text.lower() != "true":
        raise RuntimeError(f"Falha na autenticação com SPTrans: {res.text}")
    return s


def buscalinha(sessao, termo_busca: str):
    # busca na api as linhas de onibus e retorna um json
    res = sessao.get(f"{URL}/Linha/Buscar?termosBusca={termo_busca}")
    res.raise_for_status()
    return res.json()


def buscaparadas(sessao, codigo_linha: int | str):
    # busca na api todas as paradas na linha e retorna um json
    res = sessao.get(
        f"{URL}/Parada/BuscarParadasPorLinha?codigoLinha={codigo_linha}"
    )
    res.raise_for_status()
    return res.json()


def bucarposicoes(sessao, codigo_linha: int | str):
    # busca na api a posição do onibus em tempo real 
    res = sessao.get(f"{URL}/Posicao?codigoLinha={codigo_linha}")
    res.raise_for_status()
    dados = res.json()

    # a respostra e linhas = l e veiculos = vs
    linhas = dados.get("l", [])
    if not linhas:
        return []

    veiculos = []
    for linha in linhas:
        vs = linha.get("vs", [])
        for v in vs:
            veiculos.append(v)

    return veiculos


def fazermapa(paradas: list[dict], veiculos: list[dict], nome_arquivo: str):
    # faz o mapa visual usando o folium, pins azuis são as paradas e os vermelhos são os onibus
    if not paradas and not veiculos:
        raise ValueError("Sem dados de paradas ou veículos para montar o mapa.")

    coords_lat = []
    coords_lon = []

    for p in paradas:
        coords_lat.append(p["py"])
        coords_lon.append(p["px"])

    for v in veiculos:
        coords_lat.append(v["py"])
        coords_lon.append(v["px"])

    centro_lat = mean(coords_lat)
    centro_lon = mean(coords_lon)

    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=13)

    # camadas para organização visual
    fg_paradas = folium.FeatureGroup(name="Paradas")
    fg_veiculos = folium.FeatureGroup(name="Ônibus em tempo real")

    # paradas (pins azuis)
    for p in paradas:
        folium.Marker(
            location=[p["py"], p["px"]],
            popup=f"{p['np']} ({p['ed']})",
            icon=folium.Icon(color="blue", icon="bus", prefix="fa"),
        ).add_to(fg_paradas)

    # veículos (pins vermelhos)
    for v in veiculos:
        prefixo = v.get("p", "sem prefixo")
        acessivel = v.get("a", False)
        texto_popup = f"Ônibus {prefixo}"
        if acessivel:
            texto_popup += " (acessível)"

        folium.Marker(
            location=[v["py"], v["px"]],
            popup=texto_popup,
            icon=folium.Icon(color="red", icon="bus", prefix="fa"),
        ).add_to(fg_veiculos)

    fg_paradas.add_to(m)
    fg_veiculos.add_to(m)

    folium.LayerControl().add_to(m)

    m.save(nome_arquivo)
    print(f"Mapa salvo em: {nome_arquivo}")


def f():
    # função principal, pega os dados das outras e organiza, rodando tudo junto

    if not CODIGO_LINHA:
        raise ValueError("CODIGO_LINHA não definido no .env")

    sessao = autsessao()

    # mostrar linhas do termo de busca 
    linhas = buscalinha(sessao, TERMO_BUSCA_LINHA)
    print("Algumas linhas encontradas com o termo de busca:", TERMO_BUSCA_LINHA)
    for linha in linhas[:5]:
        print(
            f"cl={linha.get('cl', linha.get('CodigoLinha'))}, "
            f"lt={linha.get('lt', linha.get('Letreiro'))}, "
            f"tp={linha.get('tp', linha.get('DenominacaoTPTS'))}, "
            f"ts={linha.get('ts', linha.get('DenominacaoTSTP'))}"
        )

    # paradas e posicoes reais
    paradas = buscaparadas(sessao, CODIGO_LINHA)
    veiculos = bucarposicoes(sessao, CODIGO_LINHA)

    print(f"Total de paradas encontradas: {len(paradas)}")
    print(f"Total de veículos em operação: {len(veiculos)}")

    nome_arquivo = f"mapa_linha_{CODIGO_LINHA}.html"
    fazermapa(paradas, veiculos, nome_arquivo)


if __name__ == "__main__":
    f()
