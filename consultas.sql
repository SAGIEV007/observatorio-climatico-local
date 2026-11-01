-- Observatório Climático Local: consultas analíticas
-- Banco: dados/observatorio.duckdb | Tabela: clima_diario
-- Para executar todas e ver os resultados: python executar_consultas.py
-- Limiares de 1 mm e 10 mm: mesmas referências dos índices do ETCCDI (dia chuvoso, CDD e R10mm).
-- Limiar de 30 °C: índice TXge30 do Climpact, usado aqui como triagem, sem ajuste por cultura.
-- Esses índices foram criados para meses e anos e aqui são aplicados ao período de 30 dias.

-- Consulta 0 | Conferência da base: registros, cobertura do período e valores ausentes
SELECT COUNT(*) AS registros,
       COUNT(DISTINCT data) AS dias_distintos,
       MIN(data) AS primeiro_dia,
       MAX(data) AS ultimo_dia,
       DATE_DIFF('day', MIN(data), MAX(data)) + 1 AS dias_no_intervalo,
       COUNT(*) - COUNT(temp_min_c) AS nulos_temp_min,
       COUNT(*) - COUNT(temp_max_c) AS nulos_temp_max,
       COUNT(*) - COUNT(precip_mm) AS nulos_precip
FROM clima_diario;

-- Consulta 1 | P1: quanto choveu e como a chuva se distribuiu? (KPI 1)
SELECT ROUND(SUM(precip_mm), 1) AS chuva_acumulada_mm,
       COUNT(*) FILTER (WHERE precip_mm >= 1) AS dias_com_chuva,
       COUNT(*) FILTER (WHERE precip_mm >= 10) AS dias_chuva_10mm,
       ROUND(100.0 * COALESCE(SUM(precip_mm) FILTER (WHERE precip_mm >= 10), 0)
             / NULLIF(SUM(precip_mm), 0), 1) AS pct_chuva_10mm,
       MAX(precip_mm) AS maior_chuva_mm,
       ARG_MAX(data, precip_mm) FILTER (WHERE precip_mm > 0) AS dia_maior_chuva
FROM clima_diario;

-- Consulta 2 | P2: qual foi o maior período sem chuva relevante? (KPI 2)
-- Dia seco: abaixo de 1 mm. Subtrair a posição do dia da própria data dá o mesmo valor
-- enquanto os dias secos são consecutivos; um dia com chuva ou sem dado encerra a sequência.
WITH dias_secos AS (
    SELECT data, data - CAST(ROW_NUMBER() OVER (ORDER BY data) AS INTEGER) AS sequencia
    FROM clima_diario WHERE precip_mm < 1
)
SELECT MIN(data) AS inicio, MAX(data) AS fim, COUNT(*) AS dias_secos_consecutivos
FROM dias_secos GROUP BY sequencia
ORDER BY dias_secos_consecutivos DESC, inicio LIMIT 3;

-- Consulta 3 | P3: com que frequência o calor e a variação térmica pediram atenção? (KPI 3)
SELECT COUNT(*) FILTER (WHERE temp_max_c >= 30) AS dias_de_calor,
       STRING_AGG(STRFTIME(data, '%d/%m'), ', ' ORDER BY data)
           FILTER (WHERE temp_max_c >= 30) AS datas_de_calor,
       MAX(temp_max_c) AS maior_temp_max_c, ARG_MAX(data, temp_max_c) AS dia_mais_quente,
       MIN(temp_min_c) AS menor_temp_min_c, ARG_MIN(data, temp_min_c) AS dia_mais_frio,
       ROUND(AVG(temp_max_c - temp_min_c), 1) AS amplitude_media_c
FROM clima_diario;

-- Consulta 4 | Apoio: resumo por semana (segunda a domingo), base para um boletim ao público
SELECT CAST(DATE_TRUNC('week', data) AS DATE) AS semana_inicio,
       COUNT(*) AS dias,
       ROUND(SUM(precip_mm), 1) AS chuva_mm,
       COUNT(*) FILTER (WHERE precip_mm >= 1) AS dias_com_chuva,
       COUNT(*) FILTER (WHERE temp_max_c >= 30) AS dias_de_calor,
       ROUND(AVG(temp_min_c), 1) AS media_temp_min_c,
       ROUND(AVG(temp_max_c), 1) AS media_temp_max_c
FROM clima_diario
GROUP BY semana_inicio
ORDER BY semana_inicio;

-- Consulta 5 | Evidência: estrutura da tabela carregada
DESCRIBE clima_diario;

-- Consulta 6 | Evidência: primeiras linhas da tabela carregada
SELECT localidade, data, temp_min_c, temp_max_c, precip_mm, coletado_em
FROM clima_diario
ORDER BY data
LIMIT 5;
