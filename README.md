# Observatório Climático Local: Marília-SP

Projeto Integrador Extensionista II, curso de Ciência de Dados, Universidade de Marília (Unimar).
Aluno: Fernando da Conceição Cordeiro Filho. Professora: Vangela Tatiana Madalena Banhos.

Relatório desta etapa: [docs/escopo-1/AE2](docs/escopo-1/AE2/Relatorio_AE2_Observatorio_Climatico_Local.pdf).

## Objetivo e público-alvo

Transformar dados meteorológicos públicos em indicadores simples sobre chuva e temperatura, para apoiar
**pequenos agricultores familiares da região de Marília-SP** e os técnicos que os orientam. O projeto
olha para o que já aconteceu: não faz previsão do tempo.

## Fonte, localidade, período e variáveis

| Item | Valor |
|---|---|
| Fonte | [API histórica da Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api) (`/v1/archive`), modelo padrão "Best match" |
| Localidade | Marília-SP, latitude -22,2139 e longitude -49,9458 |
| Período | 26/09/2026 a 25/10/2026 (30 dias consecutivos), fuso `America/Sao_Paulo` |
| Variáveis | temperatura mínima diária, temperatura máxima diária e precipitação diária acumulada |

## Resultados desta etapa

| Indicador | Resultado |
|---|---|
| KPI 1: chuva acumulada | 171,5 mm, em 18 dias com pelo menos 1 mm |
| KPI 2: maior sequência de dias secos | 5 dias (17 a 21/10) |
| KPI 3: dias de calor (máxima de pelo menos 30 °C) | 7 dias, dos quais 5 entre 26 e 30/09 |

## Estrutura dos arquivos

```text
config.py                 recorte do projeto (local, datas, variáveis) e caminhos
coleta.py                 coleta na API e preservação do JSON original
banco.py                  tratamento, validação e carga no DuckDB
consultas.sql             consultas usadas nas análises
executar_consultas.py     executa consultas.sql e mostra os resultados
comparar_fontes.py        teste de sensibilidade entre modelos da fonte (não grava no banco)
requirements.txt          dependências, com versões fixas
testes/                   testes das validações, da carga e da consulta de dias secos
dados/originais/          resposta original da API (.json) e dados da coleta (.meta.json)
dados/tratados/           tabela tratada (.csv) e relatório de qualidade (.json)
dados/observatorio.duckdb banco de dados
evidencias/               saídas reais de cada etapa, citadas no relatório
docs/escopo-1/AE2/        relatório em PDF
```

## Preparação do ambiente

É preciso ter Python 3.11 ou mais recente.

```bash
git clone https://github.com/SAGIEV007/observatorio-climatico-local.git
cd observatorio-climatico-local
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate (cmd) ou .venv\Scripts\Activate.ps1 (PowerShell)
pip install -r requirements.txt
```

## Ordem e comandos de execução

```bash
python coleta.py                 # 1. coleta e guarda o JSON original
python banco.py                  # 2. trata, valida e carrega no DuckDB
python executar_consultas.py     # 3. mostra os resultados de consultas.sql
```

Comandos opcionais:

```bash
python -m unittest discover -s testes   # testes com dados propositalmente errados
python comparar_fontes.py               # compara modelos da fonte (precisa de internet)
```

**Execução repetida.** O JSON original já está no repositório, então `coleta.py` não refaz a coleta nem altera
o arquivo. Para coletar de novo, use `python coleta.py --forcar`: a coleta anterior é guardada com outro nome.
`banco.py` pode ser executado quantas vezes for preciso: a chave primária `(localidade, data)` impede registros
duplicados e a tabela continua com 30 linhas.

## Como gerar ou acessar o banco

O banco pronto está em `dados/observatorio.duckdb`. Para gerá-lo de novo, apague esse arquivo e execute
`python banco.py`. Para estudar outra localidade ou outro período, altere `config.py` e apague o banco antes de
executar `python banco.py`, pois as consultas leem a tabela inteira. Para consultá-lo:

```python
import duckdb

conexao = duckdb.connect("dados/observatorio.duckdb", read_only=True)
print(conexao.execute("SELECT * FROM clima_diario ORDER BY data LIMIT 5").df())
```

## Principais limitações

- **Não são medições de uma estação de Marília.** São estimativas de modelos e reanálise para uma célula de grade
  cujo centro fica a cerca de 4,4 km do ponto pedido. A chuva real em uma propriedade pode ser bem diferente.
- **A fonte influencia o resultado.** No mesmo período, o modelo `era5_seamless` indicou 149,2 mm de chuva contra
  171,5 mm do modelo padrão (`evidencias/06_comparacao_de_fontes.txt`).
- **Trinta dias não descrevem o clima da região** e não há comparação com a média histórica.
- **O limiar de 30 °C é uma triagem**, sem ajuste para cada cultura.
- **Análise histórica não é previsão.** Os resultados não indicam o que vai acontecer nos próximos dias.

## Dados pessoais

A base contém apenas dados meteorológicos. Registros da comunidade, se houver em etapas futuras, dependem de
consentimento e anonimização, seguindo a LGPD, e não serão versionados: `dados/comunidade/` está no `.gitignore`.

## Licença e Atribuição dos Dados

Dados: [Weather data by Open-Meteo.com](https://open-meteo.com/), licença
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Generated using Copernicus Climate Change Service information.
Todos os dados e resultados apresentados derivam da execução real registrada em `evidencias/`.
