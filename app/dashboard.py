"""Painel do Observatório Climático Local (Marília-SP) em Streamlit.

Lê o DuckDB em modo somente leitura e calcula tudo com indicadores.py, o mesmo módulo
do boletim; nenhum número do painel é digitado à mão.

Uso (na pasta principal do projeto):
    streamlit run app/dashboard.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import config  # noqa: E402
import indicadores as ind_mod  # noqa: E402
from indicadores import br, dia  # noqa: E402


@st.cache_data(ttl=600)
def carregar_base() -> pd.DataFrame:
    return ind_mod.ler_base(config.BANCO)


@st.cache_data(ttl=600)
def carregar_qualidade() -> list[dict]:
    if not config.ARQUIVO_QUALIDADE.exists():
        return []
    return json.loads(config.ARQUIVO_QUALIDADE.read_text(encoding="utf-8"))


def barra_lateral() -> tuple[float, float]:
    st.sidebar.header("Filtros")
    st.sidebar.markdown(f"**Localidade:** {config.LOCALIDADE}")
    st.sidebar.caption(f"Latitude {config.LATITUDE} · Longitude {config.LONGITUDE}")
    limiar_chuva = st.sidebar.slider("Dia com chuva a partir de (mm)", 0.5, 5.0, ind_mod.LIMIAR_CHUVA_MM, 0.5)
    limiar_calor = st.sidebar.slider("Dia de calor a partir de (°C)", 25.0, 36.0, ind_mod.LIMIAR_CALOR_C, 0.5)
    st.sidebar.caption("Os limiares mudam as contagens do painel. O boletim usa os padrões: 1 mm e 30 °C.")
    st.sidebar.divider()
    st.sidebar.caption(f"Fonte: {ind_mod.FONTE}")
    st.sidebar.caption("Banco: DuckDB, aberto somente para leitura.")
    return limiar_chuva, limiar_calor


def cartoes(ind: ind_mod.Indicadores) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Chuva acumulada", f"{br(ind.chuva_total_mm)} mm", f"{ind.dias_com_chuva} dias com chuva", delta_color="off", delta_arrow="off")
    c1.caption(f"{br(ind.pct_chuva_intensa)}% da água caiu em {ind.dias_chuva_intensa} dias com 10 mm ou mais.")
    periodo_seco = f"{dia(ind.seca.inicio)} a {dia(ind.seca.fim)}" if ind.seca.dias else "nenhum"
    c2.metric("Maior sequência sem chuva", f"{ind.seca.dias} dias", periodo_seco, delta_color="off", delta_arrow="off")
    c2.caption(f"Dia sem chuva = menos de {br(ind.limiar_chuva)} mm. Dia sem dado interrompe a sequência.")
    pct_calor = 100 * ind.dias_de_calor / ind.dias_na_base
    c3.metric(
        f"Dias com máxima ≥ {br(ind.limiar_calor)} °C",
        f"{ind.dias_de_calor} ({br(pct_calor, 0)}%)",
        f"pico {br(ind.maior_maxima_c)} °C em {dia(ind.dia_mais_quente)}",
        delta_color="off",
        delta_arrow="off",
    )
    if ind.calor_seguido.dias:
        c3.caption(
            f"Maior sequência de calor: {ind.calor_seguido.dias} dias "
            f"({dia(ind.calor_seguido.inicio)} a {dia(ind.calor_seguido.fim)})."
        )


EIXO_DATA = alt.X("data:T", title=None, axis=alt.Axis(format="%d/%m", labelAngle=0, tickCount=6))


def grafico_temperatura(df: pd.DataFrame) -> alt.Chart:
    longo = df.melt(id_vars="data", value_vars=["temp_min_c", "temp_max_c"], var_name="serie", value_name="graus")
    longo["serie"] = longo["serie"].map({"temp_min_c": "mínima", "temp_max_c": "máxima"})
    cores = alt.Scale(domain=["máxima", "mínima"], range=["#c0392b", "#2a78d6"])
    return (
        alt.Chart(longo)
        .mark_line(point=True)
        .encode(
            x=EIXO_DATA,
            y=alt.Y("graus:Q", title="°C", scale=alt.Scale(zero=False)),
            color=alt.Color("serie:N", title=None, scale=cores, legend=alt.Legend(orient="top")),
            tooltip=[alt.Tooltip("data:T", format="%d/%m/%Y"), "serie:N", "graus:Q"],
        )
    )


def grafico_chuva(df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_bar(color="#2a78d6")
        .encode(
            x=EIXO_DATA,
            y=alt.Y("precip_mm:Q", title="mm"),
            tooltip=[alt.Tooltip("data:T", format="%d/%m/%Y"), alt.Tooltip("precip_mm:Q", title="chuva (mm)")],
        )
    )


def aba_graficos(df: pd.DataFrame, ind: ind_mod.Indicadores) -> None:
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**Temperatura mínima e máxima por dia (°C)**")
        st.altair_chart(grafico_temperatura(df), width="stretch")
        st.caption(
            f"Noite mais fria: {dia(ind.dia_mais_frio)} ({br(ind.menor_minima_c)} °C). "
            f"Diferença média entre máxima e mínima: {br(ind.amplitude_media_c)} °C."
        )
    with g2:
        st.markdown("**Chuva por dia (mm)**")
        st.altair_chart(grafico_chuva(df), width="stretch")
        st.caption(f"Maior chuva: {br(ind.maior_chuva_mm)} mm em {dia(ind.dia_maior_chuva)}.")


def aba_qualidade(qualidade: list[dict]) -> None:
    if not qualidade:
        st.warning("Relatório de qualidade não encontrado. Rode: python banco.py")
        return
    tabela = pd.DataFrame(qualidade)
    erros = int((tabela["situacao"] == "ERRO").sum())
    avisos = int((tabela["situacao"] == "AVISO").sum())
    st.markdown(
        f"**{len(tabela)} checagens · {erros} erros · {avisos} avisos.** "
        "Com qualquer erro a carga é recusada; ausentes ficam como vazio, nunca como zero."
    )
    st.dataframe(tabela, hide_index=True, width="stretch")


def main() -> None:
    st.set_page_config(page_title="Observatório Climático Local · Marília-SP", page_icon="⛅", layout="wide")
    try:
        df = carregar_base()
    except FileNotFoundError as erro:
        st.error(str(erro))
        st.stop()
    if df.empty:
        st.error("O banco existe, mas a tabela clima_diario está vazia. Rode: python banco.py")
        st.stop()
    limiar_chuva, limiar_calor = barra_lateral()
    ind = ind_mod.calcular(df, limiar_chuva=limiar_chuva, limiar_calor=limiar_calor)

    st.title("Observatório Climático Local · Marília-SP")
    st.markdown(
        f"Chuva e temperatura de **{ind.primeiro_dia:%d/%m/%Y} a {ind.ultimo_dia:%d/%m/%Y}** "
        f"({ind.dias_na_base} dias), para apoiar agricultores familiares da região. "
        "**Olha para o que já aconteceu: não é previsão do tempo.**"
    )
    cartoes(ind)
    st.divider()
    graficos, semanal, qualidade, boletim, dados = st.tabs(
        ["Gráficos", "Por semana", "Qualidade dos dados", "Boletim", "Tabela completa"]
    )
    with graficos:
        aba_graficos(df, ind)
    with semanal:
        st.dataframe(ind_mod.resumo_semanal(df, limiar_chuva, limiar_calor), hide_index=True, width="stretch")
        st.caption("Semanas de segunda a domingo; a primeira e a última podem ter menos de 7 dias.")
    with qualidade:
        aba_qualidade(carregar_qualidade())
    with boletim:
        for frase in ind_mod.frases_boletim(ind_mod.calcular(df)):
            st.markdown(f"- {frase}")
    with dados:
        st.dataframe(df, hide_index=True, width="stretch")

    with st.expander("Limitações e cuidados"):
        st.markdown(
            "- Os valores são **estimativas de modelo** (reanálise) para uma célula de grade a cerca de 4 km da sede; "
            "não são medições de uma estação local.\n"
            "- A chuva varia muito em poucos quilômetros: um pluviômetro na propriedade é a referência para decisão.\n"
            "- São só 30 dias: **não servem para falar de tendência climática** de longo prazo.\n"
            "- Decisões de plantio, irrigação e manejo devem ser orientadas pela assistência técnica (CATI/CDRS).\n"
            "- Weather data by Open-Meteo.com, licença CC BY 4.0."
        )


main()
