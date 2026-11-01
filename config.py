"""Recorte do projeto e caminhos usados por todos os scripts.

Para estudar outra localidade ou outro período, altere este arquivo e use um
banco novo (apague dados/observatorio.duckdb), pois consultas.sql lê a tabela inteira.
"""

from pathlib import Path

# Recorte do Observatório Climático Local
LOCALIDADE = "Marília-SP"
ID_LOCALIDADE = "marilia-sp"
LATITUDE = -22.2139
LONGITUDE = -49.9458
DATA_INICIO = "2026-09-26"
DATA_FIM = "2026-10-25"
FUSO_HORARIO = "America/Sao_Paulo"

# Nome na API Open-Meteo -> nome padronizado na tabela
VARIAVEIS = {
    "temperature_2m_min": "temp_min_c",
    "temperature_2m_max": "temp_max_c",
    "precipitation_sum": "precip_mm",
}

URL_API = "https://archive-api.open-meteo.com/v1/archive"

# Faixas de plausibilidade para a validação (com folga para eventos extremos)
FAIXA_TEMPERATURA_C = (-5, 45)
FAIXA_PRECIPITACAO_MM = (0, 400)

# Mínimo de dias com dado por variável; abaixo disso a carga é interrompida
COBERTURA_MINIMA = 0.9

# Caminhos
RAIZ = Path(__file__).resolve().parent
PASTA_ORIGINAIS = RAIZ / "dados" / "originais"
PASTA_TRATADOS = RAIZ / "dados" / "tratados"
PASTA_EVIDENCIAS = RAIZ / "evidencias"
NOME_ORIGINAL = f"open_meteo_{ID_LOCALIDADE}_{DATA_INICIO}_{DATA_FIM}"
ARQUIVO_ORIGINAL = PASTA_ORIGINAIS / f"{NOME_ORIGINAL}.json"
ARQUIVO_METADADOS = PASTA_ORIGINAIS / f"{NOME_ORIGINAL}.meta.json"
ARQUIVO_CSV = PASTA_TRATADOS / "clima_diario.csv"
ARQUIVO_QUALIDADE = PASTA_TRATADOS / "relatorio_qualidade.json"
BANCO = RAIZ / "dados" / "observatorio.duckdb"
CONSULTAS = RAIZ / "consultas.sql"
