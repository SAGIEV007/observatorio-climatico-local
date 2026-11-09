# Issue 02: Módulo de Tratamento, Padronização e Validação de Qualidade (Pandas)

**Status:** Aberta / Planejada  
**Prioridade:** Alta (Bloqueante)  
**Módulo:** Qualidade & Pré-processamento  
**Responsável Técnico:** Fernando da Conceição Cordeiro Filho  
**Labels:** `qualidade`, `pandas`, `validacao`, `data-cleaning`, `escopo-1`

---

## 1. Contexto e Motivação
A integridade analítica do observatório depende de que anomalias, dados faltantes ou inconsistências físicas sejam detectados antes da carga no banco de dados. O princípio *fail-closed* deve ser aplicado: se um erro de integridade estrutural ocorrer, o processo de ingestão é abortado para evitar a poluição do banco e cálculos enviesados.

## 2. Escopo Técnico
- Implementar módulo em Python (`banco.py`) utilizando `pandas` para estruturação do bloco `daily` retornado pela API.
- Padronização de nomes de colunas:
  - `time` → `data`
  - `temperature_2m_min` → `temp_min_c`
  - `temperature_2m_max` → `temp_max_c`
  - `precipitation_sum` → `precip_mm`
- Tipagem explícita: conversão de `data` para `datetime64[ns]` e das variáveis meteorológicas para `float64` via `pd.to_numeric(errors="coerce")`.
- Execução das 8 checagens formais do Plano de Qualidade:
  1. Completude do calendário: verificar se todas as 30 datas do intervalo contínuo (`2026-09-26` a `2026-10-25`) estão presentes sem lacunas.
  2. Unicidade de datas: verificar ausência de registros duplicados no recorte.
  3. Consistência física térmica: validar se `temp_min_c <= temp_max_c` em todos os registros.
  4. Não-negatividade da precipitação: validar se `precip_mm >= 0.0` em todos os registros.
  5. Faixa de plausibilidade térmica regional: verificar se as temperaturas estão contidas em `[-5.0, 45.0] °C`.
  6. Faixa de plausibilidade pluviométrica: verificar se a chuva diária está contida em `[0.0, 400.0] mm`.
  7. Taxa de cobertura mínima: garantir que pelo menos 90% dos registros contenham dados válidos por variável; valores ausentes permanecem como `NaN` (não substituídos por zero).
  8. Integridade criptográfica do arquivo bruto: checagem do hash SHA-256 antes da leitura.
- Exportação dos resultados em formato JSON estruturado em `dados/tratados/relatorio_qualidade.json`.
- Gravação do arquivo CSV intermediário limpo em `dados/tratados/clima_diario.csv`.

## 3. Critérios de Aceitação (Definition of Done)
- [ ] Execução das validações sem geração de falsos-positivos em dados válidos.
- [ ] Bloqueio compulsório da carga no banco caso qualquer checagem classificada como `ERRO` falhe.
- [ ] Manutenção estrita de valores nulos como `NULL`/`NaN` (proibição de imputação arbitrária de zero na chuva ausente).
- [ ] Exportação do relatório de auditoria `relatorio_qualidade.json` detalhando a situação de cada checagem (`OK`, `AVISO` ou `ERRO`).
- [ ] Testes unitários com dados propositalmente corrompidos (dias faltando, datas duplicadas, strings em colunas numéricas, chuva negativa, mínima maior que máxima).
