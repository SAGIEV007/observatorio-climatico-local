"""Indicadores do Observatório Climático Local, calculados a partir da tabela clima_diario.

Uma única fonte de cálculo para o painel (app/dashboard.py) e para o boletim extensionista
(boletim.py). Os resultados são conferidos contra as consultas oficiais em consultas.sql
pelo teste testes/test_indicadores.py.

Regras: valor ausente continua ausente (nunca vira zero) e quebra qualquer sequência;
nada aqui é previsão, apenas descrição do período coletado.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

LIMIAR_CHUVA_MM = 1.0  # dia com chuva relevante
LIMIAR_CHUVA_INTENSA_MM = 10.0  # dia de chuva intensa
LIMIAR_CALOR_C = 30.0  # dia de calor
FONTE = "Open-Meteo (API histórica, modelo Best match; licença CC BY 4.0)"


@dataclass(frozen=True)
class Sequencia:
    dias: int
    inicio: pd.Timestamp | None
    fim: pd.Timestamp | None


@dataclass(frozen=True)
class Indicadores:
    dias_na_base: int
    primeiro_dia: pd.Timestamp
    ultimo_dia: pd.Timestamp
    limiar_chuva: float
    limiar_calor: float
    chuva_total_mm: float
    dias_com_chuva: int
    dias_chuva_intensa: int
    pct_chuva_intensa: float
    maior_chuva_mm: float | None
    dia_maior_chuva: pd.Timestamp | None
    dias_sem_dado_chuva: int
    seca: Sequencia
    dias_de_calor: int
    calor_seguido: Sequencia
    maior_maxima_c: float | None
    dia_mais_quente: pd.Timestamp | None
    menor_minima_c: float | None
    dia_mais_frio: pd.Timestamp | None
    amplitude_media_c: float | None


def ler_base(caminho_banco: Path) -> pd.DataFrame:
    """Lê clima_diario em modo somente leitura, ordenada por data."""
    if not Path(caminho_banco).exists():
        raise FileNotFoundError(f"Banco não encontrado em {caminho_banco}. Rode antes: python banco.py")
    with duckdb.connect(str(caminho_banco), read_only=True) as con:
        df = con.execute(
            "SELECT localidade, data, temp_min_c, temp_max_c, precip_mm, coletado_em FROM clima_diario ORDER BY data"
        ).df()
    df["data"] = pd.to_datetime(df["data"])
    for coluna in ("temp_min_c", "temp_max_c", "precip_mm"):
        df[coluna] = df[coluna].astype("Float64")
    return df


def maior_sequencia(df: pd.DataFrame, condicao: pd.Series) -> Sequencia:
    """Maior bloco de dias consecutivos em que a condição é verdadeira.

    Dia ausente (NA) ou data pulada encerra o bloco. No empate vale o primeiro bloco.
    """
    datas = pd.to_datetime(df["data"]).reset_index(drop=True)
    marcado = condicao.reset_index(drop=True).fillna(False).astype(bool)
    melhor = Sequencia(0, None, None)
    inicio, tamanho, anterior = None, 0, None
    for data, ok in zip(datas, marcado):
        continua = ok and tamanho > 0 and (data - anterior).days == 1
        if continua:
            tamanho += 1
        elif ok:
            inicio, tamanho = data, 1
        else:
            tamanho = 0
        if tamanho > melhor.dias:
            melhor = Sequencia(tamanho, inicio, data)
        anterior = data
    return melhor


def _extremo(df: pd.DataFrame, coluna: str, maior: bool) -> tuple[float | None, pd.Timestamp | None]:
    validos = df.dropna(subset=[coluna])
    if validos.empty:
        return None, None
    indice = validos[coluna].idxmax() if maior else validos[coluna].idxmin()
    return float(validos.at[indice, coluna]), pd.Timestamp(validos.at[indice, "data"])


def calcular(
    df: pd.DataFrame,
    limiar_chuva: float = LIMIAR_CHUVA_MM,
    limiar_calor: float = LIMIAR_CALOR_C,
    limiar_intensa: float = LIMIAR_CHUVA_INTENSA_MM,
) -> Indicadores:
    """Calcula os 3 KPIs (chuva, seca, calor) e os extremos para os limiares escolhidos."""
    if df.empty:
        raise ValueError("base vazia: nada para calcular")
    chuva = df["precip_mm"]
    chuva_total = round(float(chuva.sum(skipna=True)), 1)
    chuva_intensa = float(chuva[chuva >= limiar_intensa].sum(skipna=True))
    pct = round(100.0 * chuva_intensa / chuva_total, 1) if chuva_total > 0 else 0.0
    maior_chuva, dia_maior_chuva = _extremo(df, "precip_mm", maior=True)
    maxima, dia_quente = _extremo(df, "temp_max_c", maior=True)
    minima, dia_frio = _extremo(df, "temp_min_c", maior=False)
    amplitude = (df["temp_max_c"] - df["temp_min_c"]).mean(skipna=True)
    return Indicadores(
        dias_na_base=len(df),
        primeiro_dia=pd.Timestamp(df["data"].min()),
        ultimo_dia=pd.Timestamp(df["data"].max()),
        limiar_chuva=limiar_chuva,
        limiar_calor=limiar_calor,
        chuva_total_mm=chuva_total,
        dias_com_chuva=int((chuva >= limiar_chuva).sum()),
        dias_chuva_intensa=int((chuva >= limiar_intensa).sum()),
        pct_chuva_intensa=pct,
        maior_chuva_mm=maior_chuva,
        dia_maior_chuva=dia_maior_chuva,
        dias_sem_dado_chuva=int(chuva.isna().sum()),
        seca=maior_sequencia(df, chuva < limiar_chuva),
        dias_de_calor=int((df["temp_max_c"] >= limiar_calor).sum()),
        calor_seguido=maior_sequencia(df, df["temp_max_c"] >= limiar_calor),
        maior_maxima_c=maxima,
        dia_mais_quente=dia_quente,
        menor_minima_c=minima,
        dia_mais_frio=dia_frio,
        amplitude_media_c=None if pd.isna(amplitude) else round(float(amplitude), 1),
    )


def resumo_semanal(
    df: pd.DataFrame, limiar_chuva: float = LIMIAR_CHUVA_MM, limiar_calor: float = LIMIAR_CALOR_C
) -> pd.DataFrame:
    """Resumo por semana (segunda a domingo), base do boletim."""
    semana = pd.to_datetime(df["data"]).dt.to_period("W-SUN").dt.start_time
    grupos = df.assign(semana_inicio=semana).groupby("semana_inicio", as_index=False)
    return grupos.agg(
        de=("data", "min"),
        ate=("data", "max"),
        dias=("data", "count"),
        chuva_mm=("precip_mm", lambda s: round(float(s.sum(skipna=True)), 1)),
        dias_com_chuva=("precip_mm", lambda s: int((s >= limiar_chuva).sum())),
        dias_de_calor=("temp_max_c", lambda s: int((s >= limiar_calor).sum())),
        media_minima_c=("temp_min_c", lambda s: round(float(s.mean(skipna=True)), 1)),
        media_maxima_c=("temp_max_c", lambda s: round(float(s.mean(skipna=True)), 1)),
    )


def br(numero: float | None, casas: int = 1) -> str:
    """Número no formato brasileiro (vírgula decimal)."""
    if numero is None:
        return "sem dado"
    return f"{numero:.{casas}f}".replace(".", ",")


def dia(data: pd.Timestamp | None) -> str:
    return "sem dado" if data is None else data.strftime("%d/%m")


def frases_boletim(ind: Indicadores) -> list[str]:
    """Frases curtas, em linguagem simples, para o boletim ao público."""
    frases = [
        f"Entre {dia(ind.primeiro_dia)} e {dia(ind.ultimo_dia)}/{ind.ultimo_dia.year} choveu "
        f"{br(ind.chuva_total_mm)} mm em {ind.dias_com_chuva} dias. "
        f"A maior chuva foi de {br(ind.maior_chuva_mm)} mm, em {dia(ind.dia_maior_chuva)}.",
        f"{br(ind.pct_chuva_intensa)}% da água veio em {ind.dias_chuva_intensa} dias de chuva forte "
        "(10 mm ou mais): a chuva veio concentrada, não espalhada.",
    ]
    if ind.seca.dias:
        frases.append(
            f"O maior período sem chuva relevante foi de {ind.seca.dias} dias seguidos "
            f"({dia(ind.seca.inicio)} a {dia(ind.seca.fim)})."
        )
    frases.append(
        f"Houve {ind.dias_de_calor} dias com máxima de {br(ind.limiar_calor, 0)} °C ou mais; "
        f"o mais quente foi {dia(ind.dia_mais_quente)} ({br(ind.maior_maxima_c)} °C) "
        f"e a noite mais fria foi {dia(ind.dia_mais_frio)} ({br(ind.menor_minima_c)} °C)."
    )
    frases.append(
        "Isto descreve o que já aconteceu: não é previsão do tempo. São estimativas de modelo para a região "
        "de Marília, não medição de uma estação local; a chuva pode variar de um sítio para outro. "
        f"Fonte: {FONTE}."
    )
    return frases
