"""Executa as consultas de consultas.sql no banco DuckDB e exibe os resultados.

Uso:
    python executar_consultas.py
"""

import re

import duckdb
import pandas as pd

import config


def separar_consultas(texto):
    """Cada consulta começa por um comentário no formato '-- Consulta N | título'."""
    blocos = re.split(r"(?m)^(?=-- Consulta )", texto)[1:]
    return [(bloco.splitlines()[0].removeprefix("-- ").strip(), bloco) for bloco in blocos]


def main():
    if not config.BANCO.exists():
        raise SystemExit("Banco não encontrado. Execute primeiro: python coleta.py e python banco.py")

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_colwidth", None)
    texto = config.CONSULTAS.read_text(encoding="utf-8")
    with duckdb.connect(str(config.BANCO), read_only=True) as conexao:
        for titulo, consulta in separar_consultas(texto):
            print(titulo)
            print(conexao.execute(consulta).df().to_string(index=False))
            print()


if __name__ == "__main__":
    main()
