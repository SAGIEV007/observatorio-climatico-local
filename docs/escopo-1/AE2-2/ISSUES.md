# Roadmap de Implementação: Issues do Projeto (AE2-2)

**Projeto Integrador Extensionista II — Ciência de Dados — Universidade de Marília (Unimar)**  
**Aluno:** Fernando da Conceição Cordeiro Filho · **Professora:** Vangela Tatiana Madalena Banhos  
**Repositório:** [SAGIEV007/observatorio-climatico-local](https://github.com/SAGIEV007/observatorio-climatico-local)

Este documento consolida o conjunto de no mínimo seis issues técnicas planejadas para guiar a implementação futura do **Observatório Climático Local — Marília-SP**, conforme as diretrizes da Atividade de Estudo 2 (AE2-2).

---

## Matriz de Rastreabilidade e Sequenciamento de Issues

| Issue | Título da Tarefa | Módulo | Prioridade | Dependência | Status Planejado |
|---|---|---|---|---|---|
| **#01** | Pipeline de Coleta Automatizada e Preservação de Dados Brutos | Ingestão (Open-Meteo) | Alta | Nenhuma | Aberta |
| **#02** | Módulo de Tratamento, Padronização e Validação de Qualidade | Qualidade (Pandas) | Alta | Issue #01 | Aberta |
| **#03** | Camada de Persistência e Armazenamento Analítico Idempotente | Banco (DuckDB) | Alta | Issue #02 | Aberta |
| **#04** | Motor de Consultas Analíticas e Cálculo de Indicadores/KPIs | Análise (SQL) | Alta | Issue #03 | Aberta |
| **#05** | Desenvolvimento do Dashboard Interativo de Visualização | Apresentação (Streamlit) | Média-Alta | Issue #03, #04 | Aberta |
| **#06** | Módulo de Comunicação Extensionista, Boletins e Acessibilidade | Extensão & LGPD | Média | Issue #04, #05 | Aberta |

---

## Detalhamento das Issues

### [Issue 01: Pipeline de Coleta Automatizada e Preservação de Dados Brutos](issues/01_pipeline_coleta_open_meteo.md)
- **Objetivo:** Ingestão parametrizada da API histórica da Open-Meteo com tolerância a falhas de rede e gravação imutável da resposta bruta (`.json`) e metadados com hash SHA-256 (`.meta.json`).
- **Entregáveis:** Script `coleta.py`, arquivos em `dados/originais/`, logs de execução e testes de rede simulando indisponibilidade.

### [Issue 02: Módulo de Tratamento, Padronização e Validação de Qualidade](issues/02_validador_qualidade_pandas.md)
- **Objetivo:** Transformação e saneamento dos dados brutos em pandas, aplicando 8 regras estritas de qualidade com auditoria *fail-closed* e preservação de valores nulos (sem imputação artificial de zero).
- **Entregáveis:** Script de validação, arquivo `dados/tratados/clima_diario.csv`, `dados/tratados/relatorio_qualidade.json` e suite de testes com 19 cenários com dados anômalos propositais.

### [Issue 03: Camada de Persistência e Armazenamento Analítico Idempotente](issues/03_armazenamento_duckdb_idempotente.md)
- **Objetivo:** Definição do esquema da tabela única `clima_diario` no DuckDB com restrições de integridade (`CHECK`) e mecanismo de inserção idempotente (`INSERT OR REPLACE INTO ...`) via chave primária composta `(localidade, data)`.
- **Entregáveis:** Banco relacional `dados/observatorio.duckdb`, DDL auditado, testes de carga repetida sem duplicatas.

### [Issue 04: Motor de Consultas Analíticas e Cálculo de Indicadores/KPIs](issues/04_consultas_sql_indicadores_kpi.md)
- **Objetivo:** Desenvolvimento do motor de consultas SQL em `consultas.sql` para cálculo dos 3 KPIs principais (Chuva acumulada, Sequência de dias secos via window function, Frequência de calor) e resumo semanal agrupado.
- **Entregáveis:** Arquivo `consultas.sql`, script de execução `executar_consultas.py` e arquivo de evidências analíticas `evidencias/05_resultados_consultas.txt`.

### [Issue 05: Desenvolvimento do Dashboard Interativo de Visualização](issues/05_dashboard_interativo_streamlit.md)
- **Objetivo:** Construção da interface gráfica em Streamlit (`app/dashboard.py`) conectada diretamente ao DuckDB, incorporando os cards de KPIs, gráficos independentes sincronizados, tabela de dados interativa e seção expansível de limitações.
- **Entregáveis:** Aplicação Streamlit funcional, wireframe validado, suporte a navegação mobile e filtros dinâmicos de limiares agroclimáticos.

### [Issue 06: Módulo de Comunicação Extensionista, Boletins e Acessibilidade](issues/06_comunicacao_extensionista_boletim.md)
- **Objetivo:** Estruturação de canal de comunicação com pequenos agricultores familiares de Marília-SP, modelo de Boletim Agroclimático Semanal impresso/digital, glossário acessível sem hermetismo meteorológico e protocolo de conformidade com a LGPD.
- **Entregáveis:** Template de Boletim Semanal, cartilha de salvaguardas contra conclusões indevidas, termo de consentimento LGPD e documentação de devolutiva comunitária.
