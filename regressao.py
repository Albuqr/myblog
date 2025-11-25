import os
import requests
from io import StringIO

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from plotnine import ggplot, aes, geom_point, geom_abline, theme, element_text, ggsave

load_dotenv()

URLX = os.getenv("URL_X")
URLY = os.getenv("URL_Y")


def carregardados(urlx: str, urly: str):
    # pega o x e y de cada arquivo

    if not urlx or not urly:
        raise ValueError("URLX ou URLY inválidos ou não encontrados")

    # limpa espaços invisíveis, quebras de linha, aspas
    urlx = urlx.strip().strip('"').strip("'")
    urly = urly.strip().strip('"').strip("'")

    # Se for caminho local (arquivo), abrir direto
    if os.path.isfile(urlx):
        with open(urlx, "r", encoding="utf-8") as f:
            x = np.loadtxt(StringIO(f.read()))
    else:
        resp_x = requests.get(urlx)
        resp_x.raise_for_status()
        x = np.loadtxt(StringIO(resp_x.text))

    if os.path.isfile(urly):
        with open(urly, "r", encoding="utf-8") as f:
            y = np.loadtxt(StringIO(f.read()))
    else:
        resp_y = requests.get(urly)
        resp_y.raise_for_status()
        y = np.loadtxt(StringIO(resp_y.text))

    x = np.asarray(x).ravel()
    y = np.asarray(y).ravel()

    if x.shape[0] != y.shape[0]:
        raise ValueError(f"Tamanhos diferentes: len(x)={len(x)}, len(y)={len(y)}")

    return x, y


def regressaomatriz(x: np.ndarray, y: np.ndarray):
    # calcula os coeficientes da regressao linear:

    X = np.column_stack((np.ones_like(x), x))

    XtX = X.T @ X
    XtX_inv = np.linalg.inv(XtX)
    Xty = X.T @ y
    beta = XtX_inv @ Xty

    a = float(beta[0])  # intercepto
    b = float(beta[1])  # inclinação

    return a, b


def fazgrafico(x: np.ndarray, y: np.ndarray, a: float, b: float,
               nome_arquivo: str = "grafico_regressao.png"):

    df = pd.DataFrame({"x": x, "y": y})

    plot = (
        ggplot(df, aes("x", "y"))
        + geom_point()
        + geom_abline(intercept=a, slope=b)
        + theme(
            axis_title_x=element_text(size=12),
            axis_title_y=element_text(size=12),
            figure_size=(6, 4),
        )
    )

    ggsave(plot, filename=nome_arquivo, dpi=300)

    return plot

    ggsave(plot=plot, filename=nome_arquivo, dpi=300)
    return plot


def f(url_x: str | None = None, url_y: str | None = None):

    if url_x is None:
        url_x = URLX
    if url_y is None:
        url_y = URLY

    # aqui o nome certo é carregardados, não carregar_dados_url
    x, y = carregardados(url_x, url_y)
    a, b = regressaomatriz(x, y)

    print(f"Intercepto (a): {a}")
    print(f"Inclinação (b): {b}")

    plot = fazgrafico(x, y, a, b)
    print("Gráfico salvo em grafico_regressao.png")

    return a, b, plot


if __name__ == "__main__":
    f()
