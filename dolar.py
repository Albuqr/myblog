import os
import calendar
from datetime import datetime

import requests
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

BCB_API = os.getenv(
    "BCB_API",
    "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata"
)

BCB_DOLAR_ENDPOINT = os.getenv(
    "BCB_DOLAR_ENDPOINT",
    "CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
)

MES_ANO = os.getenv("DOLAS_MES_ANO", "082021")


def datas_mes(mmyyyy: str):
    # recebe uma string como mes/ano e devolve o primeiro e ultimo dia como datetime

    primeiro = datetime.strptime(mmyyyy, "%m%Y")
    ultimodia = calendar.monthrange(primeiro.year, primeiro.month)[1]
    ultimo = primeiro.replace(day=ultimodia)
    return primeiro, ultimo


def dolardados(mmyyyy: str):
    # pega os dados da cotação no periodo escolhido, mes/ano

    inicio, fim = datas_mes(mmyyyy)

    # url base pra pegar os dados em json
    url = (
    f"{BCB_API}/"
    f"{BCB_DOLAR_ENDPOINT}?"
    f"@dataInicial='{inicio.strftime('%m-%d-%Y')}'&"
    f"@dataFinalCotacao='{fim.strftime('%m-%d-%Y')}'&"
    "$top=10000&$format=json"
)

    resposta = requests.get(url)
    resposta.raise_for_status()
    dados = resposta.json()["value"]
    return dados


def organizardados(dados, mmyyyy: str):
    # organiza os dados do json em dataframe, basicamente faz um calendario,
    # dia que nao tiver cotação fica com a mesma do dia anterior

    df = pd.DataFrame(dados)
    df["data"] = pd.to_datetime(df["dataHoraCotacao"]).dt.date
    df = df[["data", "cotacaoVenda"]].sort_values("data")

    inicio, fim = datas_mes(mmyyyy)
    calendario = pd.date_range(start=inicio, end=fim).date
    df_full = pd.DataFrame({"data": calendario})

    df_full = df_full.merge(df, on="data", how="left")

    df_full["cotacaoVenda"] = df_full["cotacaoVenda"].ffill()

    return df_full


def plot(df: pd.DataFrame, mmyyyy: str):
    # usa o plotly pra fazer o grafico do valor do dolar

    titulo = f"Cotação do Dólar – {mmyyyy[:2]}/{mmyyyy[2:]}"
    fig = px.line(df, x="data", y="cotacaoVenda", title=titulo)
    fig.update_layout(
        xaxis_title="Data",
        yaxis_title="Cotação de venda (R$)"
    )
    return fig


def f(mmyyyy: str | None = None):
    # função principal, pega o mes/ano do .env e organiza os dados das outras funções

    if mmyyyy is None:
        mmyyyy = MES_ANO

    dados = dolardados(mmyyyy)
    df_tratado = organizardados(dados, mmyyyy)
    fig = plot(df_tratado, mmyyyy)
    fig.show()
    return df_tratado, fig