"""Roda o painel Streamlit sem navegador e confere que abre sem erro e reage aos filtros.

Uso (na pasta principal do projeto):
    python -m unittest discover -s testes -v
"""

import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import config  # noqa: E402

try:
    from streamlit.testing.v1 import AppTest
except ImportError:  # pragma: no cover
    AppTest = None


@unittest.skipIf(AppTest is None, "streamlit não instalado")
@unittest.skipUnless(config.BANCO.exists(), "banco ainda não criado (rode python banco.py)")
class TestPainel(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(RAIZ / "app" / "dashboard.py"), default_timeout=60).run()

    def test_abre_sem_erro_com_tres_cartoes(self):
        self.assertEqual(list(self.app.exception), [])
        self.assertEqual(len(self.app.metric), 3)
        self.assertEqual(self.app.metric[0].value, "171,5 mm")

    def test_filtro_de_calor_muda_o_cartao(self):
        antes = self.app.metric[2].value
        self.app.sidebar.slider[1].set_value(32.0).run()
        self.assertNotEqual(self.app.metric[2].value, antes)
        self.assertEqual(list(self.app.exception), [])

    def test_avisa_que_nao_e_previsao(self):
        textos = " ".join(m.value for m in self.app.markdown)
        self.assertIn("não é previsão", textos)


if __name__ == "__main__":
    unittest.main()
