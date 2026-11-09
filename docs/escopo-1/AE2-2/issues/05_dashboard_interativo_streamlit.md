# Issue 05: Desenvolvimento do Dashboard Interativo de Visualização (Streamlit)

**Status:** Aberta / Planejada  
**Prioridade:** Média-Alta  
**Módulo:** Apresentação & Frontend  
**Responsável Técnico:** Fernando da Conceição Cordeiro Filho  
**Labels:** `streamlit`, `dashboard`, `visualizacao`, `ui-ux`, `escopo-1`

---

## 1. Contexto e Motivação
A comunicação efetiva com o público-alvo (agricultores familiares e técnicos extensionistas) exige uma interface visual limpa, acessível via navegador e responsiva em dispositivos móveis. O Streamlit foi selecionado como padrão tecnológico para a entrega da camada de apresentação, permitindo conectar diretamente o backend DuckDB aos componentes visuais interativos sem necessidade de frameworks frontend complexos.

## 2. Escopo Técnico
- Criar a aplicação Streamlit (`app/dashboard.py`) conectando diretamente ao banco `dados/observatorio.duckdb` em modo somente leitura (`read_only=True`).
- Estruturar a interface conforme o wireframe homologado na AE2-2:
  1. `Barra Lateral (Filtros & Metadados)`:
     - Identificador da localidade (`Marília-SP`).
     - Coordenadas geográficas (`-22,2139; -49,9458`) e elevação da grade (`650 m`).
     - Intervalo temporal analisado (`26/09/2026 a 25/10/2026`).
     - Sliders interativos para limiares analíticos (limiar de calor: padrão 30,0 °C; limiar de chuva relevante: padrão 1,0 mm).
     - Carimbo de data/hora da última sincronização da base.
  2. `Cabeçalho Principal`:
     - Título institucional: **Observatório Climático Local — Marília-SP**.
     - Subtítulo com declaração clara do escopo: diagnóstico histórico descritivo (não é previsão do tempo).
  3. `Linha de KPIs (3 colunas com st.metric)`:
     - Card 1: **Chuva Acumulada** (`171,5 mm`), com delta de 18 dias com chuva e volume concentrado.
     - Card 2: **Maior Sequência de Dias Secos** (`5 dias consecutivos`, 17 a 21/10).
     - Card 3: **Dias de Calor Excessivo** (`7 dias ≥ 30 °C`, representando 23,3% do período).
  4. `Painel de Gráficos (Dois painéis independentes, sem eixos duplos)`:
     - Painel Superior: **Faixa Diária de Temperatura (°C)** — da mínima à máxima, com coloração condicional de alerta para picos térmicos ≥ 30 °C e linha de referência horizontal.
     - Painel Inferior: **Precipitação Diária Acumulada (mm)** — gráfico de barras com linha de limiar em 10 mm (chuva forte).
  5. `Tabela de Dados e Resumo Semanal`:
     - Visão analítica diária interativa com filtros e ordenação (`st.dataframe`).
     - Visão agregada por semana agronômica (segunda a domingo).
  6. `Rodapé Metodológico e Limitações (st.expander)`:
     - Explicação sobre a natureza dos dados (grade espacial de reanálise ERA5/IFS da Open-Meteo).
     - Alerta explícito de que dados históricos não indicam condições futuras.
     - Declaração de licença (CC BY 4.0) e link para documentação oficial.

## 3. Critérios de Aceitação (Definition of Done)
- [ ] Aplicação executável localmente via `streamlit run app/dashboard.py`.
- [ ] Leitura rápida do banco DuckDB com cache de sessão (`@st.cache_data`).
- [ ] Conformidade visual estrita com o wireframe planejado na AE2-2.
- [ ] Ausência de gráficos com eixo duplo confuso (adotar painéis separados com escala temporal sincronizada).
- [ ] Layout responsivo para navegação em smartphones e tablets no campo.
- [ ] Seção visível e destacada informando as limitações técnicas e a fonte dos dados.
