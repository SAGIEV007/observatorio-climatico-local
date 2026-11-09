# Issue 03: Camada de Persistência e Armazenamento Analítico Idempotente (DuckDB)

**Status:** Aberta / Planejada  
**Prioridade:** Alta (Bloqueante)  
**Módulo:** Banco de Dados & Armazenamento  
**Responsável Técnico:** Fernando da Conceição Cordeiro Filho  
**Labels:** `duckdb`, `sql`, `modelagem`, `idempotencia`, `escopo-1`

---

## 1. Contexto e Motivação
O Observatório Climático Local necessita de um motor analítico colunar (OLAP) embutido, veloz e sem dependência de serviços externos pesados. O DuckDB foi selecionado pela sua capacidade de lidar com SQL analítico moderno (Window Functions, CTEs, agregação vetorial) diretamente em arquivo local (`dados/observatorio.duckdb`). A carga deve ser estritamente idempotente para permitir reexecuções seguras.

## 2. Escopo Técnico
- Definir e aplicar o DDL da tabela principal `clima_diario` no DuckDB:
  ```sql
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
  );
  ```
- Implementar chave primária composta `(localidade, data)` garantindo unicidade espaço-temporal dos registros.
- Incorporar restrições a nível de tabela:
  - `CHECK (precip_mm >= 0)`
  - `CHECK (temp_min_c <= temp_max_c)`
- Implementar estratégia de carga transacional idempotente via SQL:
  ```sql
  INSERT OR REPLACE INTO clima_diario
      (localidade, data, latitude, longitude, temp_min_c, temp_max_c, precip_mm, arquivo_origem, coletado_em)
  SELECT localidade, CAST(data AS DATE), latitude, longitude, temp_min_c, temp_max_c, precip_mm, arquivo_origem, coletado_em
  FROM tratados;
  ```
- Registrar metadados adicionais em cada registro: `arquivo_origem` e `coletado_em` (UTC) para rastreabilidade de linhagem de dados (*data lineage*).
- Retornar estatísticas da carga: total de linhas antes, total após a carga, novos registros inseridos e período coberto.

## 3. Critérios de Aceitação (Definition of Done)
- [ ] Criação determinística do arquivo `dados/observatorio.duckdb` e da tabela `clima_diario`.
- [ ] Bloqueio de duplicatas: executar a carga sucessivas vezes deve manter exatamente 30 registros sem erros de colisão de chave primária.
- [ ] Validação prática das restrições de `CHECK`: inserção de dados inconsistentes deve ser rejeitada pelo motor DuckDB.
- [ ] Teste automatizado de carga repetida comprovando idempotência total (`novos = 0` na segunda execução).
- [ ] Desempenho sub-segundo para criação, carga e verificação.
