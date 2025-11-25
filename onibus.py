from datetime import datetime, timedelta
import os
import requests
from folium import Map, Marker, Icon
from dotenv import load_dotenv, find_dotenv

# carrega variaveis do .env
load_dotenv(find_dotenv())

# url base da api sptrans
API_ONIBUS = "http://api.olhovivo.sptrans.com.br/v2.1"


def autenticarsessao(token: str):
    # autentica na api e devolve sessao http

    sessao = requests.Session()
    resposta = sessao.post(f"{API_ONIBUS}/Login/Autenticar?token={token}")
    if resposta.text != "true":
        raise Exception("falha na autenticacao")
    return sessao


def buscacodigolinha(sessao: requests.Session, termo_linha: str):
    # busca codigo interno da linha a partir do termo

    resp = sessao.get(f"{API_ONIBUS}/Linha/Buscar?termosBusca={termo_linha}")
    dados_linha = resp.json()
    return dados_linha[0]["cl"]


def buscarparadaslinha(sessao: requests.Session, cod_linha: int):
    # busca paradas associadas a linha

    resp = sessao.get(
        f"{API_ONIBUS}/Parada/BuscarParadasPorLinha?codigoLinha={cod_linha}"
    )
    return resp.json()


def buscarposicaorealtime(sessao: requests.Session, cod_linha: int):
    # busca posicao em tempo real dos onibus da linha

    resp = sessao.get(f"{API_ONIBUS}/Posicao/Linha?codigoLinha={cod_linha}")
    return resp.json()


def fazmapa(paradas, posicoes_rt):
    # monta mapa com paradas e onibus

    if paradas:
        lat_med = sum(p["py"] for p in paradas) / len(paradas)
        lon_med = sum(p["px"] for p in paradas) / len(paradas)
        centro_mapa = [lat_med, lon_med]
    else:
        centro_mapa = [-23.55052, -46.633308]  # fallback centro sp

    mapa = Map(location=centro_mapa, zoom_start=14)
    todos_pontos = []

    # marca paradas
    for p in paradas:
        todos_pontos.append([p["py"], p["px"]])
        Marker(
            location=[p["py"], p["px"]],
            popup=f"Parada: {p['np']}",
            icon=Icon(color="blue", icon="info-sign"),
            z_index_offset=0,
        ).add_to(mapa)

    # marca onibus em tempo real
    if posicoes_rt.get("vs"):
        for bus in posicoes_rt["vs"]:
            todos_pontos.append([bus["py"], bus["px"]])

            utc_time = datetime.fromisoformat(bus["ta"].replace("Z", "+00:00"))
            br_time = utc_time - timedelta(hours=3)  # utc-3
            popup_text = f"Onibus: {bus['p']}\nHorario: {br_time.strftime('%H:%M:%S')}"

            Marker(
                location=[bus["py"], bus["px"]],
                popup=popup_text,
                icon=Icon(color="red", icon="bus", prefix="fa"),
                z_index_offset=1000,
            ).add_to(mapa)
    else:
        Marker(
            location=centro_mapa,
            popup="nao ha onibus em tempo real",
            icon=Icon(color="gray", icon="exclamation-sign"),
            z_index_offset=1000,
        ).add_to(mapa)

    # ajusta zoom pelo conjunto de pontos
    if todos_pontos:
        mapa.fit_bounds(todos_pontos)

    return mapa


def f(termo_linha: str | None = None):
    # fluxo principal: autentica, busca dados e monta mapa

    if termo_linha is None:
        termo_linha = "8000"  # linha padrao

    token_onibus = os.getenv("SPTRANS_TOKEN")
    if not token_onibus:
        raise ValueError("variavel SPTRANS_TOKEN nao encontrada no .env")

    sessao = autenticarsessao(token_onibus)
    cod_linha = buscacodigolinha(sessao, termo_linha)
    paradas = buscarparadaslinha(sessao, cod_linha)
    posicoes_rt = buscarposicaorealtime(sessao, cod_linha)

    mapa_onibus = fazmapa(paradas, posicoes_rt)
    return mapa_onibus


# executa fluxo e mostra mapa no post
mapa = f()
mapa