"""Testa os indicadores usados pelo painel e pelo boletim.

Os mesmos números precisam sair do SQL (consultas.sql) e do Python (indicadores.py):
se um dos dois mudar sozinho, o teste de concordância falha.

Uso (na pasta principal do projeto):
    python -m unittest discover -s testes -v
"""

import sys
import unittest
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
import indicadores  # noqa: E402


def tabela(chuvas, maximas=None, minimas=None, inicio="2026-09-26"):
    dias = pd.date_range(inicio, periods=len(chuvas), freq="D")
    return pd.DataFrame(
        {
            "data": dias,
            "precip_mm": pd.array(chuvas, dtype="Float64"),
            "temp_max_c": pd.array(maximas if maximas is not None else [28.0] * len(chuvas), dtype="Float64"),
            "temp_min_c": pd.array(minimas if minimas is not None else [18.0] * len(chuvas), dtype="Float64"),
        }
    )


class TestSequencias(unittest.TestCase):
    def test_maior_sequencia_seca_e_a_mais_longa_e_a_primeira_no_empate(self):
        df = tabela([0, 0, 5, 0, 0, 0, 5, 0, 0, 0])
        seq = indicadores.maior_sequencia(df, df["precip_mm"] < 1)
        self.assertEqual(seq.dias, 3)
        self.assertEqual(seq.inicio, pd.Timestamp("2026-09-29"))
        self.assertEqual(seq.fim, pd.Timestamp("2026-10-01"))

    def test_dia_sem_dado_quebra_a_sequencia_e_nao_conta_como_seco(self):
        df = tabela([0, 0, None, 0, 0, 0])
        seq = indicadores.maior_sequencia(df, df["precip_mm"] < 1)
        self.assertEqual(seq.dias, 3)
        self.assertEqual(seq.inicio, pd.Timestamp("2026-09-29"))

    def test_data_faltando_quebra_a_sequencia(self):
        df = tabela([0, 0, 0, 0]).drop(index=2).reset_index(drop=True)
        seq = indicadores.maior_sequencia(df, df["precip_mm"] < 1)
        self.assertEqual(seq.dias, 2)

    def test_sem_nenhum_dia_na_condicao_devolve_zero(self):
        df = tabela([5, 5, 5])
        seq = indicadores.maior_sequencia(df, df["precip_mm"] < 1)
        self.assertEqual(seq.dias, 0)
        self.assertIsNone(seq.inicio)


class TestIndicadores(unittest.TestCase):
    def test_limiares_mudam_as_contagens(self):
        df = tabela([0.5, 2, 12, 0], maximas=[29, 31, 33, 30])
        padrao = indicadores.calcular(df)
        self.assertEqual(padrao.dias_com_chuva, 2)
        self.assertEqual(padrao.dias_de_calor, 3)
        exigente = indicadores.calcular(df, limiar_chuva=5, limiar_calor=32)
        self.assertEqual(exigente.dias_com_chuva, 1)
        self.assertEqual(exigente.dias_de_calor, 1)

    def test_porcentagem_de_chuva_intensa_sem_chuva_fica_zero(self):
        ind = indicadores.calcular(tabela([0, 0, 0]))
        self.assertEqual(ind.chuva_total_mm, 0)
        self.assertEqual(ind.pct_chuva_intensa, 0)

    def test_ausente_nao_vira_zero_na_soma_nem_na_cobertura(self):
        ind = indicadores.calcular(tabela([10, None, 10]))
        self.assertEqual(ind.chuva_total_mm, 20)
        self.assertEqual(ind.dias_sem_dado_chuva, 1)


class TestConcordanciaComSQL(unittest.TestCase):
    """O painel (Python) e as consultas oficiais (SQL) precisam dar o mesmo resultado na base real."""

    @classmethod
    def setUpClass(cls):
        if not config.BANCO.exists():
            raise unittest.SkipTest("banco ainda não criado (rode python banco.py)")
        cls.df = indicadores.ler_base(config.BANCO)
        cls.ind = indicadores.calcular(cls.df)
        with duckdb.connect(str(config.BANCO), read_only=True) as con:
            cls.sql_chuva = con.execute(
                "SELECT ROUND(SUM(precip_mm),1), COUNT(*) FILTER (WHERE precip_mm>=1),"
                " COUNT(*) FILTER (WHERE precip_mm>=10) FROM clima_diario"
            ).fetchone()
            cls.sql_calor = con.execute(
                "SELECT COUNT(*) FILTER (WHERE temp_max_c>=30), MAX(temp_max_c), MIN(temp_min_c),"
                " ROUND(AVG(temp_max_c-temp_min_c),1) FROM clima_diario"
            ).fetchone()

    def test_chuva_igual_ao_sql(self):
        self.assertEqual(
            (self.ind.chuva_total_mm, self.ind.dias_com_chuva, self.ind.dias_chuva_intensa),
            self.sql_chuva,
        )

    def test_calor_igual_ao_sql(self):
        self.assertEqual(
            (self.ind.dias_de_calor, self.ind.maior_maxima_c, self.ind.menor_minima_c, self.ind.amplitude_media_c),
            self.sql_calor,
        )

    def test_maior_sequencia_seca_da_base_real(self):
        self.assertEqual(self.ind.seca.dias, 5)
        self.assertEqual(self.ind.seca.inicio, pd.Timestamp("2026-10-17"))


class TestBoletim(unittest.TestCase):
    def test_boletim_tem_aviso_de_que_nao_e_previsao_e_cita_a_fonte(self):
        ind = indicadores.calcular(tabela([0, 12, 0], maximas=[31, 25, 26]))
        texto = " ".join(indicadores.frases_boletim(ind)).lower()
        self.assertIn("não é previsão", texto)
        self.assertIn("open-meteo", texto)
        self.assertIn("12,0 mm", texto)


if __name__ == "__main__":
    unittest.main()
