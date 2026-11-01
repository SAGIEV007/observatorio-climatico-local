"""Trata e valida os dados coletados e carrega o resultado no banco DuckDB.

Uso:
    python banco.py

Pode ser executado quantas vezes for preciso: a chave primária (localidade, data)
impede registros duplicados.
"""

import hashlib
import json

import duckdb
import pandas as pd

import config

CRIAR_TABELA = """
CREATE TABLE IF NOT EXISTS clima_diario (
    localidade      VARCHAR   NOT NULL,
    data            DATE      NOT NULL,
    latitude        DOUBLE    NOT NULL,
    longitude       DOUBLE    NOT NULL,
    temp_min_c      DOUBLE,
    temp_max_c      DOUBLE,
    precip_mm       DOUBLE    CHECK (precip_mm >= 0),
    arquivo_origem  VARCHAR   NOT NULL,
    coletado_em     TIMESTAMP NOT NULL,
    PRIMARY KEY (localidade, data),
    CHECK (temp_min_c <= temp_max_c)
)
"""

CARREGAR = """
INSERT OR REPLACE INTO clima_diario
    (localidade, data, latitude, longitude, temp_min_c, temp_max_c, precip_mm, arquivo_origem, coletado_em)
SELECT localidade, CAST(data AS DATE), latitude, longitude, temp_min_c, temp_max_c, precip_mm, arquivo_origem, coletado_em
FROM tratados
"""


def ler_original():
    """Lê o JSON original e confere se ele continua igual ao que foi coletado."""
    if not (config.ARQUIVO_ORIGINAL.exists() and config.ARQUIVO_METADADOS.exists()):
        raise SystemExit("Coleta não encontrada ou incompleta. Execute primeiro: python coleta.py --forcar")
    conteudo = config.ARQUIVO_ORIGINAL.read_bytes()
    metadados = json.loads(config.ARQUIVO_METADADOS.read_text(encoding="utf-8"))
    if hashlib.sha256(conteudo).hexdigest() != metadados["sha256"]:
        raise SystemExit("O arquivo original mudou depois da coleta (SHA-256 diferente). Carga interrompida.")
    return json.loads(conteudo), metadados


def padronizar(resposta):
    """Padroniza os nomes das colunas e converte datas e números para os tipos corretos.

    Devolve também a versão sem conversão, usada para distinguir um valor ausente
    (já vazio na API) de um valor inválido (que só ficou vazio na conversão).
    """
    brutos = pd.DataFrame(resposta["daily"]).rename(columns={"time": "data", **config.VARIAVEIS})
    tratados = brutos.copy()
    tratados["data"] = pd.to_datetime(brutos["data"], format="%Y-%m-%d", errors="coerce")
    for coluna in config.VARIAVEIS.values():
        tratados[coluna] = pd.to_numeric(brutos[coluna], errors="coerce").astype("float64")
    return brutos, tratados


def verificacao(nome, problemas, detalhe="", aviso=False):
    situacao = "OK" if problemas == 0 else ("AVISO" if aviso else "ERRO")
    return {"verificacao": nome, "problemas": int(problemas), "situacao": situacao, "detalhe": detalhe}


def validar(brutos, tratados, inicio=config.DATA_INICIO, fim=config.DATA_FIM):
    """Executa as verificações de qualidade. Nenhum valor é alterado aqui."""
    calendario = pd.date_range(inicio, fim, freq="D")
    datas = tratados["data"].dropna()
    resultado = [
        verificacao("Datas válidas (AAAA-MM-DD)", tratados["data"].isna().sum()),
        verificacao("Datas duplicadas", datas.duplicated().sum()),
        verificacao(
            f"Quantidade de registros = {len(calendario)}",
            abs(len(tratados) - len(calendario)),
            f"{len(tratados)} registros recebidos",
        ),
        verificacao("Dias do período sem registro", len(calendario.difference(datas))),
        verificacao("Datas fora do período", (~datas.between(calendario[0], calendario[-1])).sum()),
    ]

    for coluna in config.VARIAVEIS.values():
        invalidos = brutos[coluna].notna() & tratados[coluna].isna()
        resultado.append(verificacao(f"Valores não numéricos em {coluna}", invalidos.sum()))

        ausentes = int(brutos[coluna].isna().sum())
        cobertura = 1 - ausentes / max(len(brutos), 1)
        resultado.append(
            verificacao(
                f"Valores ausentes em {coluna}",
                ausentes,
                f"cobertura {cobertura:.0%}; ausentes ficam como NULL, sem troca por zero",
                aviso=cobertura >= config.COBERTURA_MINIMA,
            )
        )

    resultado.append(
        verificacao("Temperatura mínima maior que a máxima", (tratados["temp_min_c"] > tratados["temp_max_c"]).sum())
    )
    resultado.append(verificacao("Precipitação negativa", (tratados["precip_mm"] < 0).sum()))

    minimo, maximo = config.FAIXA_TEMPERATURA_C
    for coluna in ("temp_min_c", "temp_max_c"):
        fora = tratados[coluna].notna() & ~tratados[coluna].between(minimo, maximo)
        resultado.append(verificacao(f"{coluna} fora de {minimo} a {maximo} °C", fora.sum()))

    minimo, maximo = config.FAIXA_PRECIPITACAO_MM
    fora = tratados["precip_mm"].notna() & ~tratados["precip_mm"].between(minimo, maximo)
    resultado.append(verificacao(f"precip_mm fora de {minimo} a {maximo} mm", fora.sum()))
    return resultado


def carregar(tratados, metadados, caminho_banco=config.BANCO):
    """Grava no DuckDB. Se a mesma localidade e data já existirem, a linha é substituída, não repetida."""
    tabela = tratados.assign(
        localidade=config.LOCALIDADE,
        latitude=config.LATITUDE,
        longitude=config.LONGITUDE,
        arquivo_origem=metadados["arquivo"],
        coletado_em=pd.Timestamp(metadados["coletado_em_utc"]).tz_convert(None),
    )
    with duckdb.connect(str(caminho_banco)) as conexao:
        conexao.execute(CRIAR_TABELA)
        antes = conexao.execute("SELECT COUNT(*) FROM clima_diario").fetchall()[0][0]
        conexao.register("tratados", tabela)
        conexao.execute(CARREGAR)
        conexao.unregister("tratados")
        depois, dias, primeiro, ultimo = conexao.execute(
            "SELECT COUNT(*), COUNT(DISTINCT data), MIN(data), MAX(data) FROM clima_diario"
        ).fetchall()[0]
    return {
        "registros_antes": antes,
        "registros_depois": depois,
        "novos": depois - antes,
        "dias_distintos": dias,
        "primeiro_dia": str(primeiro),
        "ultimo_dia": str(ultimo),
    }


def exibir_verificacoes(resultado):
    print("Verificações de qualidade:")
    for item in resultado:
        linha = f"  [{item['situacao']:<5}] {item['verificacao']}: {item['problemas']}"
        print(f"{linha} ({item['detalhe']})" if item["detalhe"] else linha)


def main():
    resposta, metadados = ler_original()
    brutos, tratados = padronizar(resposta)
    print(f"Arquivo lido: {metadados['arquivo']} (coletado em {metadados['coletado_em_utc']} UTC)")
    print(f"Colunas padronizadas: {', '.join(tratados.columns)}")
    print(f"Tipos: {', '.join(f'{coluna}={tipo}' for coluna, tipo in tratados.dtypes.astype(str).items())}")

    resultado = validar(brutos, tratados)
    exibir_verificacoes(resultado)

    config.PASTA_TRATADOS.mkdir(parents=True, exist_ok=True)
    config.ARQUIVO_QUALIDADE.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if any(item["situacao"] == "ERRO" for item in resultado):
        raise SystemExit("Carga interrompida: corrija os itens marcados como ERRO. O banco não foi alterado.")

    tratados = tratados.sort_values("data", ignore_index=True)
    tratados.to_csv(config.ARQUIVO_CSV, index=False, date_format="%Y-%m-%d", encoding="utf-8")
    carga = carregar(tratados, metadados)

    print(f"Banco: {config.BANCO.relative_to(config.RAIZ).as_posix()} | Tabela: clima_diario")
    print(f"Registros antes da carga: {carga['registros_antes']} | depois da carga: {carga['registros_depois']} | novos: {carga['novos']}")
    print(f"Dias distintos: {carga['dias_distintos']} | Período carregado: {carga['primeiro_dia']} a {carga['ultimo_dia']}")
    if carga["registros_depois"] != len(tratados):
        print("Aviso: o banco tem registros de outro recorte. Apague o banco e execute de novo, pois as consultas leem a tabela inteira.")


if __name__ == "__main__":
    main()
