"""Compara a precipitação e as temperaturas de diferentes modelos da Open-Meteo no mesmo recorte.

Teste de sensibilidade, à parte da base principal: não grava nada no banco.
Mostra quanto os indicadores dependem do modelo usado pela fonte.

Uso:
    python comparar_fontes.py
"""

from datetime import datetime, timezone

import pandas as pd

import coleta
import config

# Padrão da API (usado na base principal), modelo de alta resolução e reanálises
MODELOS = ["best_match", "ecmwf_ifs", "era5_seamless", "era5_land"]


def resumir(modelo):
    resposta = coleta.baixar({**coleta.montar_parametros(), "models": modelo}).json()
    dias = pd.DataFrame(resposta["daily"]).rename(columns=config.VARIAVEIS)
    chuva = dias["precip_mm"]
    secos = chuva.lt(1)
    # Sem nenhum dado de chuva, as contagens ficam vazias em vez de zero.
    tem_chuva = chuva.notna().any()
    return {
        "modelo": modelo,
        "grade_lat": round(resposta["latitude"], 4),
        "grade_lon": round(resposta["longitude"], 4),
        "dias_sem_chuva_informada": int(chuva.isna().sum()),
        "chuva_mm": round(chuva.sum(min_count=1), 1),
        "dias_chuva": int(chuva.ge(1).sum()) if tem_chuva else None,
        "maior_seca_dias": int(secos.groupby((~secos).cumsum()).sum().max()) if tem_chuva else None,
        "dias_30c": int(dias["temp_max_c"].ge(30).sum()),
        "tmax_c": dias["temp_max_c"].max(),
        "tmin_c": dias["temp_min_c"].min(),
    }


def main():
    agora = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    print(f"Comparação feita em {agora} (UTC) | {config.LOCALIDADE} | {config.DATA_INICIO} a {config.DATA_FIM}")
    pd.set_option("display.width", 200)
    print(pd.DataFrame([resumir(modelo) for modelo in MODELOS], dtype=object).to_string(index=False))


if __name__ == "__main__":
    main()
