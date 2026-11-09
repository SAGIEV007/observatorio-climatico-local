# Issue 04: Motor de Consultas Analíticas e Cálculo de Indicadores/KPIs (SQL DuckDB)

**Status:** Aberta / Planejada  
**Prioridade:** Alta  
**Módulo:** Análise de Dados & SQL  
**Responsável Técnico:** Fernando da Conceição Cordeiro Filho  
**Labels:** `sql`, `analytics`, `kpi`, `duckdb`, `escopo-1`

---

## 1. Contexto e Motivação
Para que o observatório gere valor efetivo aos pequenos agricultores e agrônomos, as perguntas de negócio definidas na AE1 precisam ser respondidas de forma matemática e determinística via consultas SQL. O DuckDB permite expressar cálculos analíticos avançados de forma concisa e padronizada.

## 2. Escopo Técnico
- Estruturar o arquivo `consultas.sql` contendo consultas SQL otimizadas para:
  1. `Consulta 0 (Conferência de Integridade)`:
     - Contagem de registros totais, datas distintas, data mínima, data máxima, intervalo de dias e contagem de nulos por coluna.
  2. `Consulta 1 (P1 - Distribuição e Volume de Chuva / KPI 1)`:
     - Volume total acumulado (`SUM(precip_mm)`).
     - Contagem de dias com chuva relevante (`precip_mm >= 1.0 mm`).
     - Contagem de dias com chuva intensa (`precip_mm >= 10.0 mm`, índice R10mm do ETCCDI).
     - Proporção percentual da chuva acumulada concentrada nos dias intensos.
     - Maior precipitação diária e data correspondente (`ARG_MAX(data, precip_mm)`).
  3. `Consulta 2 (P2 - Maior Sequência de Dias Secos / KPI 2)`:
     - Cálculo de ilhas de dias secos consecutivos (`precip_mm < 1.0 mm`, índice CDD do ETCCDI) utilizando a técnica de agrupamento por diferença de posição ordinal:
       `data - CAST(ROW_NUMBER() OVER (ORDER BY data) AS INTEGER) AS sequencia`.
     - Identificação da data de início, data de término e total de dias secos na maior sequência.
  4. `Consulta 3 (P3 - Frequência de Calor e Variação Térmica / KPI 3)`:
     - Contagem de dias com calor excessivo (`temp_max_c >= 30.0 °C`, índice TXge30 do Climpact).
     - Lista concatenada das datas de calor (`STRING_AGG`).
     - Temperatura máxima absoluta e dia mais quente (`ARG_MAX`).
     - Temperatura mínima absoluta e dia mais frio (`ARG_MIN`).
     - Amplitude térmica diária média (`AVG(temp_max_c - temp_min_c)`).
  5. `Consulta 4 (Resumo Semanal de Suporte)`:
     - Agrupamento temporal por semana agronômica via `DATE_TRUNC('week', data)`, consolidando chuva semanal, dias com chuva, dias de calor e médias térmicas.
- Criar script utilitário (`executar_consultas.py`) para leitura e execução automática do arquivo SQL com formatação limpa no terminal e exportação de evidências textuais.

## 3. Critérios de Aceitação (Definition of Done)
- [ ] Todas as consultas SQL executadas com sucesso no banco `dados/observatorio.duckdb`.
- [ ] Validação dos resultados analíticos para o recorte de Marília-SP:
  - KPI 1: 171,5 mm de chuva acumulada (18 dias chuvosos; 62,6% do total em 5 dias de chuva ≥ 10 mm).
  - KPI 2: 5 dias secos consecutivos (17 a 21 de outubro de 2026).
  - KPI 3: 7 dias com máxima ≥ 30 °C (pico de 33,2 °C em 29/09/2026; amplitude média de 9,2 °C).
- [ ] Resumo semanal consolidado em 5 períodos coerentes.
- [ ] Arquivo de evidências gerado em `evidencias/05_resultados_consultas.txt`.
- [ ] Testes automatizados cobrindo o algoritmo de sequências secas e agregações condicionais.
