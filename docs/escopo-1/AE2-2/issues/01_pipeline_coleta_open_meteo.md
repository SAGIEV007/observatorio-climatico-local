# Issue 01: Pipeline de Coleta Automatizada e Preservação de Dados Brutos (Open-Meteo API)

**Status:** Aberta / Planejada  
**Prioridade:** Alta (Bloqueante)  
**Módulo:** Ingestão de Dados  
**Responsável Técnico:** Fernando da Conceição Cordeiro Filho  
**Labels:** `coleta`, `api`, `ingestao`, `seguranca`, `escopo-1`

---

## 1. Contexto e Motivação
O Observatório Climático Local depende de uma ingestão resiliente e reprodutível de séries históricas meteorológicas da API da Open-Meteo (`https://archive-api.open-meteo.com/v1/archive`). Para garantir a integridade dos dados e auditoria científica, a extração deve ser automatizada com tratamento de falhas transientes e preservação estrita do arquivo bruto original (`raw data preservation`), garantindo que nenhum dado seja descartado ou alterado antes do pipeline de tratamento.

## 2. Escopo Técnico
- Implementar script Python (`coleta.py`) utilizando a biblioteca `requests` para envio de requisições HTTP GET parametrizadas.
- Parâmetros obrigatórios:
  - `latitude`: `-22.2139` (Marília-SP)
  - `longitude`: `-49.9458` (Marília-SP)
  - `start_date`: `2026-09-26`
  - `end_date`: `2026-10-25` (30 dias consecutivos)
  - `daily`: `temperature_2m_min,temperature_2m_max,precipitation_sum`
  - `timezone`: `America/Sao_Paulo`
- Persistir a resposta bruta em disco no formato JSON dentro de `dados/originais/`.
- Gerar arquivo de metadados correspondente (`.meta.json`) registrando:
  - URL completa da requisição
  - Parâmetros utilizados
  - Timestamp ISO 8601 da coleta em UTC
  - Status HTTP retornado
  - Hash criptográfico SHA-256 do arquivo JSON bruto
  - Coordenadas geográficas reais e elevação da grade utilizada pelo modelo da API.
- Implementar mecanismo de retry exponencial com timeout configurável (mínimo de 3 tentativas para códigos 429 e 5xx).
- Implementar salvaguarda de idempotência: não sobrescrever o arquivo existente caso uma coleta já tenha sido executada, a menos que o parâmetro `--forcar` seja explicitamente passado.

## 3. Critérios de Aceitação (Definition of Done)
- [ ] Execução bem-sucedida com retorno HTTP 200 e recebimento exato dos 30 dias solicitados.
- [ ] Arquivo JSON salvo com permissões adequadas em `dados/originais/open_meteo_marilia-sp_2026-09-26_2026-10-25.json`.
- [ ] Metadados salvos em `.meta.json` com SHA-256 conferido e comprovado.
- [ ] Testes unitários cobrindo cenários de sucesso, erro de rede (Timeout), código HTTP de erro (500/404) e preservação de idempotência.
- [ ] Zero dependência de chaves de API secretas (fonte aberta e gratuita sob licença CC BY 4.0).
