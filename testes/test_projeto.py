"""Testa as validações, a carga sem duplicação e a consulta de dias secos com dados propositalmente errados.

Uso (na pasta principal do projeto):
    python -m unittest discover -s testes -v
"""

import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import banco  # noqa: E402
import coleta  # noqa: E402
import config  # noqa: E402

METADADOS = {"arquivo": "teste.json", "coletado_em_utc": "2026-11-01T12:00:00+00:00"}


def resposta_valida():
    dias = pd.date_range(config.DATA_INICIO, config.DATA_FIM, freq="D").strftime("%Y-%m-%d").tolist()
    return {
        "daily": {
            "time": dias,
            "temperature_2m_min": [18.0] * len(dias),
            "temperature_2m_max": [28.0] * len(dias),
            "precipitation_sum": [0.0] * len(dias),
        }
    }


def situacoes(resposta):
    brutos, tratados = banco.padronizar(resposta)
    return {item["verificacao"]: item["situacao"] for item in banco.validar(brutos, tratados)}


class TestValidacao(unittest.TestCase):
    def verificar(self, alterar, trecho, esperado):
        resposta = copy.deepcopy(resposta_valida())
        alterar(resposta["daily"])
        encontradas = {nome: situacao for nome, situacao in situacoes(resposta).items() if trecho in nome}
        self.assertTrue(encontradas, f"verificação não encontrada: {trecho}")
        self.assertIn(esperado, encontradas.values())

    def test_dados_corretos_nao_geram_erro_nem_aviso(self):
        self.assertEqual(set(situacoes(resposta_valida()).values()), {"OK"})

    def test_dia_faltando(self):
        def remover(diarios):
            for coluna in diarios:
                del diarios[coluna][5]

        self.verificar(remover, "Dias do período sem registro", "ERRO")

    def test_data_duplicada(self):
        self.verificar(lambda d: d["time"].__setitem__(5, d["time"][4]), "Datas duplicadas", "ERRO")

    def test_data_invalida(self):
        self.verificar(lambda d: d["time"].__setitem__(5, "2026-13-40"), "Datas válidas", "ERRO")

    def test_minima_maior_que_maxima(self):
        self.verificar(lambda d: d["temperature_2m_min"].__setitem__(3, 40.0), "mínima maior", "ERRO")

    def test_chuva_negativa(self):
        self.verificar(lambda d: d["precipitation_sum"].__setitem__(3, -1.0), "Precipitação negativa", "ERRO")

    def test_temperatura_fora_da_faixa(self):
        self.verificar(lambda d: d["temperature_2m_max"].__setitem__(3, 80.0), "temp_max_c fora", "ERRO")

    def test_texto_em_coluna_numerica(self):
        self.verificar(lambda d: d["precipitation_sum"].__setitem__(3, "abc"), "não numéricos em precip_mm", "ERRO")

    def test_poucos_ausentes_geram_aviso_e_nao_viram_zero(self):
        resposta = resposta_valida()
        resposta["daily"]["precipitation_sum"][3] = None
        self.assertEqual(situacoes(resposta)["Valores ausentes em precip_mm"], "AVISO")
        _, tratados = banco.padronizar(resposta)
        self.assertTrue(pd.isna(tratados.loc[3, "precip_mm"]))

    def test_variavel_inteira_ausente_interrompe_a_carga(self):
        # Caso real: o modelo era5_land devolve precipitation_sum vazio em todos os dias.
        self.verificar(
            lambda d: d.__setitem__("precipitation_sum", [None] * len(d["time"])),
            "Valores ausentes em precip_mm",
            "ERRO",
        )


    def test_arquivo_fora_de_ordem_nao_gera_falso_erro(self):
        resposta = resposta_valida()
        for coluna in resposta["daily"].values():
            coluna.reverse()
        resposta["daily"]["precipitation_sum"][3] = None
        self.assertNotIn("ERRO", situacoes(resposta).values())


class TestColeta(unittest.TestCase):
    def test_resposta_incompleta_e_recusada(self):
        sem_elevacao = {"latitude": 0, "longitude": 0, **resposta_valida()}
        with self.assertRaises(SystemExit):
            coleta.conferir_resposta(json.dumps(sem_elevacao).encode())

    def test_colunas_de_tamanhos_diferentes_sao_recusadas(self):
        resposta = {"latitude": 0, "longitude": 0, "elevation": 0, **resposta_valida()}
        del resposta["daily"]["precipitation_sum"][0]
        with self.assertRaises(SystemExit):
            coleta.conferir_resposta(json.dumps(resposta).encode())

    def test_limite_de_requisicoes_e_tentado_de_novo(self):
        recusa, sucesso = mock.Mock(status_code=429), mock.Mock(status_code=200)
        with (
            mock.patch("coleta.requests.get", side_effect=[recusa, sucesso]),
            mock.patch("coleta.time.sleep"),
            mock.patch("builtins.print"),
        ):
            self.assertIs(coleta.baixar({}), sucesso)


class TestBanco(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.caminho = Path(self.pasta.name) / "teste.duckdb"

    def tearDown(self):
        self.pasta.cleanup()

    def consulta(self, trecho):
        texto = config.CONSULTAS.read_text(encoding="utf-8")
        return next(bloco for bloco in re.split(r"(?m)^(?=-- Consulta )", texto) if bloco.startswith(trecho))

    def test_carga_repetida_nao_duplica(self):
        _, tratados = banco.padronizar(resposta_valida())
        primeira = banco.carregar(tratados, METADADOS, self.caminho)
        segunda = banco.carregar(tratados, METADADOS, self.caminho)
        self.assertEqual(primeira["novos"], 30)
        self.assertEqual(segunda["novos"], 0)
        self.assertEqual(segunda["registros_depois"], 30)

    def test_nova_coleta_substitui_o_valor_da_mesma_data(self):
        _, tratados = banco.padronizar(resposta_valida())
        banco.carregar(tratados, METADADOS, self.caminho)
        tratados.loc[0, "precip_mm"] = 7.5
        banco.carregar(tratados, METADADOS, self.caminho)
        with duckdb.connect(str(self.caminho), read_only=True) as conexao:
            total, chuva = conexao.execute(
                f"SELECT COUNT(*), MAX(precip_mm) FROM clima_diario WHERE data = DATE '{config.DATA_INICIO}'"
            ).fetchall()[0]
        self.assertEqual((total, chuva), (1, 7.5))

    def test_tabela_recusa_minima_maior_que_maxima(self):
        _, tratados = banco.padronizar(resposta_valida())
        tratados.loc[0, "temp_min_c"] = 40.0
        with self.assertRaises(duckdb.ConstraintException):
            banco.carregar(tratados, METADADOS, self.caminho)

    def test_porcentagem_fica_zero_sem_dia_de_10mm(self):
        resposta = resposta_valida()
        resposta["daily"]["precipitation_sum"][:] = [2.0] * 30
        _, tratados = banco.padronizar(resposta)
        banco.carregar(tratados, METADADOS, self.caminho)
        with duckdb.connect(str(self.caminho), read_only=True) as conexao:
            resultado = conexao.execute(self.consulta("-- Consulta 1")).df().iloc[0]
        self.assertEqual(resultado["pct_chuva_10mm"], 0.0)

    def test_dia_sem_dado_encerra_a_sequencia_de_dias_secos(self):
        resposta = resposta_valida()
        chuva = resposta["daily"]["precipitation_sum"]
        chuva[:] = [5.0] * 30
        chuva[2:6] = [0.0] * 4  # 4 dias secos
        chuva[10:15] = [0.0, 0.0, None, 0.0, 0.0]  # 2 + sem dado + 2: não pode virar 5
        _, tratados = banco.padronizar(resposta)
        banco.carregar(tratados, METADADOS, self.caminho)
        with duckdb.connect(str(self.caminho), read_only=True) as conexao:
            linhas = conexao.execute(self.consulta("-- Consulta 2")).fetchall()
        self.assertEqual(linhas[0][2], 4)
        self.assertEqual(str(linhas[0][0]), "2026-09-28")
        self.assertEqual(str(linhas[0][1]), "2026-10-01")
        self.assertEqual([linha[2] for linha in linhas[1:]], [2, 2])


if __name__ == "__main__":
    unittest.main()
