"""Protótipo de Dashboard Interativo em Streamlit — Observatório Climático Local.

Desenho técnico planejado na AE2-2 para apresentação dos resultados analíticos de Marília-SP.
Conecta-se ao banco DuckDB (dados/observatorio.duckdb) em modo somente leitura (read_only=True).

Uso:
    streamlit run app/dashboard_prototipo.py
"""

from pathlib import Path
import duckdb
import pandas as pd

# Caminhos do projeto
RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "dados" / "observatorio.duckdb"

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


def carregar_dados_duckdb():
    """Lê os dados tratados e consultas agregadas do DuckDB."""
    if not BANCO.exists():
        raise FileNotFoundError(f"Banco não encontrado em {BANCO}. Execute antes: python banco.py")
    
    with duckdb.connect(str(BANCO), read_only=True) as con:
        df_diario = con.execute("SELECT * FROM clima_diario ORDER BY data").df()
        
        kpi_chuva = con.execute("""
            SELECT ROUND(SUM(precip_mm), 1) AS chuva_acumulada_mm,
                   COUNT(*) FILTER (WHERE precip_mm >= 1) AS dias_com_chuva,
                   COUNT(*) FILTER (WHERE precip_mm >= 10) AS dias_chuva_10mm,
                   ROUND(100.0 * COALESCE(SUM(precip_mm) FILTER (WHERE precip_mm >= 10), 0) / NULLIF(SUM(precip_mm), 0), 1) AS pct_chuva_10mm
            FROM clima_diario
        """).df().iloc[0]
        
        kpi_seco = con.execute("""
            WITH dias_secos AS (
                SELECT data, data - CAST(ROW_NUMBER() OVER (ORDER BY data) AS INTEGER) AS sequencia
                FROM clima_diario WHERE precip_mm < 1
            )
            SELECT MIN(data) AS inicio, MAX(data) AS fim, COUNT(*) AS dias_secos_consecutivos
            FROM dias_secos GROUP BY sequencia
            ORDER BY dias_secos_consecutivos DESC, inicio LIMIT 1
        """).df().iloc[0]
        
        kpi_calor = con.execute("""
            SELECT COUNT(*) FILTER (WHERE temp_max_c >= 30) AS dias_de_calor,
                   MAX(temp_max_c) AS maior_temp_max_c,
                   ARG_MAX(data, temp_max_c) AS dia_mais_quente,
                   MIN(temp_min_c) AS menor_temp_min_c,
                   ARG_MIN(data, temp_min_c) AS dia_mais_frio,
                   ROUND(AVG(temp_max_c - temp_min_c), 1) AS amplitude_media_c
            FROM clima_diario
        """).df().iloc[0]
        
        df_semanal = con.execute("""
            SELECT CAST(DATE_TRUNC('week', data) AS DATE) AS semana_inicio,
                   COUNT(*) AS dias,
                   ROUND(SUM(precip_mm), 1) AS chuva_total_mm,
                   COUNT(*) FILTER (WHERE precip_mm >= 1) AS dias_com_chuva,
                   COUNT(*) FILTER (WHERE temp_max_c >= 30) AS dias_de_calor,
                   ROUND(AVG(temp_min_c), 1) AS media_temp_min_c,
                   ROUND(AVG(temp_max_c), 1) AS media_temp_max_c
            FROM clima_diario
            GROUP BY semana_inicio ORDER BY semana_inicio
        """).df()
        
    return df_diario, kpi_chuva, kpi_seco, kpi_calor, df_semanal


def main():
    if not HAS_STREAMLIT:
        print("Para executar o painel interativo, instale o Streamlit:")
        print("pip install streamlit")
        print("Depois execute: streamlit run app/dashboard_prototipo.py")
        return

    st.set_page_config(
        page_title="Observatório Climático Local — Marília-SP",
        page_icon="⛅",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    df_diario, kpi_chuva, kpi_seco, kpi_calor, df_semanal = carregar_dados_duckdb()

    # Sidebar: Filtros e Configuração
    st.sidebar.title("⚙️ Configurações & Filtros")
    st.sidebar.markdown("**Localidade:** Marília-SP")
    st.sidebar.caption("Latitude: -22.2139 | Longitude: -49.9458 | Grade API: 650 m de elevação")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Período Analisado (30 dias):**")
    st.sidebar.info("26/09/2026 a 25/10/2026")
    
    limiar_calor = st.sidebar.slider("Limiar de Calor Excessivo (°C)", min_value=25.0, max_value=38.0, value=30.0, step=0.5)
    limiar_chuva = st.sidebar.slider("Limiar de Chuva Relevante (mm)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)
    
    st.sidebar.markdown("---")
    st.sidebar.caption("🗄️ **Banco:** DuckDB (OLAP colunar, modo read-only)")
    st.sidebar.caption("📡 **Fonte:** Open-Meteo Historical Weather API (CC BY 4.0)")

    # Cabeçalho Principal
    st.title("Observatório Climático Local: Marília-SP")
    st.markdown(
        "**Projeto Integrador Extensionista II · Bacharelado em Ciência de Dados · Universidade de Marília (Unimar)**  \n"
        "Diagnóstico histórico descritivo para suporte à agricultura familiar regional. "
        "*Este painel olha para o passado recente e não realiza previsões futuras.*"
    )

    st.markdown("---")

    # Linha de KPIs (3 Métricas)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Chuva Acumulada no Período",
            value=f"{kpi_chuva['chuva_acumulada_mm']:.1f} mm",
            delta=f"{kpi_chuva['dias_com_chuva']} dias com chuva (≥ {limiar_chuva} mm)"
        )
        st.caption(f"Concentração: {kpi_chuva['pct_chuva_10mm']:.1f}% da água caiu em {kpi_chuva['dias_chuva_10mm']} dias intensos (≥ 10 mm).")

    with col2:
        st.metric(
            label="Maior Sequência de Dias Secos",
            value=f"{kpi_seco['dias_secos_consecutivos']} dias",
            delta="17/10 a 21/10 (estiagem breve)",
            delta_color="inverse"
        )
        st.caption("Ausência de veranico prolongado no período; umidade preservada.")

    with col3:
        dias_calor_filtrado = (df_diario["temp_max_c"] >= limiar_calor).sum()
        pct_calor = 100.0 * dias_calor_filtrado / len(df_diario)
        st.metric(
            label=f"Dias de Calor (Máxima ≥ {limiar_calor:.1f} °C)",
            value=f"{dias_calor_filtrado} dias ({pct_calor:.1f}%)",
            delta=f"Pico: {kpi_calor['maior_temp_max_c']:.1f} °C ({pd.to_datetime(kpi_calor['dia_mais_quente']).strftime('%d/%m')})",
            delta_color="off"
        )
        st.caption("5 dos dias de calor ocorreram consecutivamente de 26 a 30 de setembro.")

    st.markdown("---")

    # Gráficos Analíticos
    st.subheader("Visualizações Temporais")
    aba_graficos, aba_tabela, aba_semanal = st.tabs(["📈 Gráficos Diários", "📋 Tabela de Dados Completa", "📅 Resumo Semanal"])

    with aba_graficos:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("#### Faixa Térmica Diária (°C)")
            st.line_chart(df_diario.set_index("data")[["temp_min_c", "temp_max_c"]])
            st.caption("Evolução da temperatura mínima e máxima diária ao longo dos 30 dias.")

        with col_g2:
            st.markdown("#### Precipitação Diária Acumulada (mm)")
            st.bar_chart(df_diario.set_index("data")["precip_mm"])
            st.caption("Volume diário de chuva. Destaque para o pico de 37,0 mm em 25/10/2026.")

    with aba_tabela:
        st.markdown("#### Tabela Completa (30 registros — Tabela `clima_diario`)")
        st.dataframe(df_diario[["localidade", "data", "temp_min_c", "temp_max_c", "precip_mm", "coletado_em"]], use_container_width=True)

    with aba_semanal:
        st.markdown("#### Resumo Agregado por Semana (Segunda a Domingo)")
        st.dataframe(df_semanal, use_container_width=True)

    # Rodapé Metodológico e Limitações
    with st.expander("ℹ️ Metodologia, Limitações e Comunicação Extensionista"):
        st.markdown("""
        - **Natureza dos Dados:** Dados meteorológicos extraídos da API pública Open-Meteo (`/v1/archive`), modelo *Best match* (reanálise ERA5/IFS). Representam estimativas para uma célula de grade (~4,4 km de distância da sede municipal) com elevação de 650 m.
        - **Incerteza Espacial:** A precipitação local pode variar substancialmente em distâncias de poucos quilômetros. Os indicadores servem como diagnóstico referencial, não substituindo medições de pluviômetros de propriedade.
        - **Análise Histórica vs. Previsão:** Este painel descreve o que **já ocorreu** entre 26/09/2026 e 25/10/2026. **Não é previsão do tempo.**
        - **Recomendações Agronômicas:** Decisões de época de plantio, dimensionamento de irrigação ou manejo fitossanitário devem ser orientadas por engenheiros agrônomos e pela assistência técnica regional (CATI/CDRS).
        - **Licença:** Weather data by Open-Meteo.com, licença [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
        """)


if __name__ == "__main__":
    main()
