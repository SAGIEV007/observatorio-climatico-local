"""Gera o Boletim Agroclimático (1 página) para a devolutiva à comunidade.

Usa os mesmos cálculos do painel (indicadores.py). Saída em docs/final/:
boletim_marilia.html e, se houver Chromium/Chrome disponível, boletim_marilia.pdf.

Uso (na pasta principal do projeto):
    python boletim.py
"""

from __future__ import annotations

import html
import shutil
import subprocess
import sys
from pathlib import Path

import config
import indicadores as ind_mod
from indicadores import br, dia

PASTA_SAIDA = config.RAIZ / "docs" / "final"
SAIDA_HTML = PASTA_SAIDA / "boletim_marilia.html"
SAIDA_PDF = PASTA_SAIDA / "boletim_marilia.pdf"
NAVEGADORES = ("chromium", "chromium-browser", "google-chrome", "chrome-headless-shell")

CSS = """
@page { size: A4; margin: 1.4cm 1.6cm; }
body { font: 11.5pt/1.45 "Liberation Sans", Arial, sans-serif; color: #1b1b19; margin: 0; }
h1 { font-size: 19pt; margin: 0 0 2pt; color: #0f2540; }
.sub { margin: 0 0 12pt; color: #44433f; }
.cartoes { display: flex; gap: 10pt; margin: 0 0 12pt; }
.cartao { flex: 1; border: 1pt solid #c9c8c1; border-radius: 6pt; padding: 8pt 10pt; }
.cartao b { display: block; font-size: 20pt; color: #0f2540; }
.cartao span { font-size: 9.5pt; color: #44433f; }
ul { padding-left: 16pt; margin: 0 0 10pt; }
li { margin-bottom: 5pt; }
table { width: 100%; border-collapse: collapse; font-size: 10pt; margin: 0 0 10pt; }
th, td { border: 0.6pt solid #b9b8b1; padding: 3pt 5pt; text-align: left; }
th { background: #efeee9; }
.aviso { border-left: 4pt solid #c0392b; background: #fbf1ef; padding: 7pt 10pt; font-size: 10pt; }
.rodape { margin-top: 10pt; font-size: 8.5pt; color: #55544f; }
"""


def esc(texto: object) -> str:
    return html.escape(str(texto), quote=False)


def montar_html(ind: ind_mod.Indicadores, semanas) -> str:
    frases = ind_mod.frases_boletim(ind)
    cartoes = [
        (f"{br(ind.chuva_total_mm)} mm", f"de chuva em {ind.dias_com_chuva} dias"),
        (f"{ind.seca.dias} dias", f"seguidos sem chuva ({dia(ind.seca.inicio)} a {dia(ind.seca.fim)})"),
        (f"{ind.dias_de_calor} dias", f"com máxima de {br(ind.limiar_calor, 0)} °C ou mais (pico {br(ind.maior_maxima_c)} °C)"),
    ]
    linhas = "".join(
        f"<tr><td>{s.de:%d/%m} a {s.ate:%d/%m}</td><td>{s.dias}</td><td>{br(s.chuva_mm)}</td>"
        f"<td>{s.dias_com_chuva}</td><td>{s.dias_de_calor}</td>"
        f"<td>{br(s.media_minima_c)} a {br(s.media_maxima_c)}</td></tr>"
        for s in semanas.itertuples()
    )
    blocos = "".join(f'<div class="cartao"><b>{esc(v)}</b><span>{esc(t)}</span></div>' for v, t in cartoes)
    itens = "".join(f"<li>{esc(f)}</li>" for f in frases[:-1])
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Boletim Agroclimático · {esc(config.LOCALIDADE)}</title><style>{CSS}</style></head><body>
<h1>Boletim Agroclimático · {esc(config.LOCALIDADE)}</h1>
<p class="sub">Como foram a chuva e a temperatura de {ind.primeiro_dia:%d/%m/%Y} a {ind.ultimo_dia:%d/%m/%Y}
· Observatório Climático Local (projeto de extensão, Ciência de Dados, Unimar)</p>
<div class="cartoes">{blocos}</div>
<ul>{itens}</ul>
<table><tr><th>Semana</th><th>Dias</th><th>Chuva (mm)</th><th>Dias com chuva</th>
<th>Dias de calor</th><th>Média da mínima a média da máxima (°C)</th></tr>{linhas}</table>
<p class="aviso"><b>Atenção:</b> {esc(frases[-1])}</p>
<p class="rodape">Para decidir plantio, irrigação ou manejo, procure a Casa da Agricultura (CATI/CDRS) do seu
município. Dados: Weather data by Open-Meteo.com (CC BY 4.0). Este boletim não usa nenhum dado pessoal.</p>
</body></html>"""


def achar_navegador() -> str | None:
    for nome in NAVEGADORES:
        caminho = shutil.which(nome)
        if caminho:
            return caminho
    candidatos = sorted(
        Path.home().glob(".cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell"),
        key=lambda p: int(p.parent.parent.name.rsplit("-", 1)[-1]),
    )
    return str(candidatos[-1]) if candidatos else None


def gerar_pdf(origem: Path, destino: Path) -> bool:
    navegador = achar_navegador()
    if navegador is None:
        print("Chromium não encontrado: abra o HTML no navegador e use Imprimir > Salvar como PDF.")
        return False
    comando = [navegador, "--headless", "--no-sandbox", "--no-pdf-header-footer",
               f"--print-to-pdf={destino}", origem.as_uri()]
    resultado = subprocess.run(comando, capture_output=True, text=True, timeout=120)
    if resultado.returncode != 0 or not destino.exists():
        print(f"Falha ao gerar o PDF: {resultado.stderr.strip()[:300]}")
        return False
    return True


def main() -> int:
    df = ind_mod.ler_base(config.BANCO)
    ind = ind_mod.calcular(df)
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    SAIDA_HTML.write_text(montar_html(ind, ind_mod.resumo_semanal(df)), encoding="utf-8")
    print(f"HTML: {SAIDA_HTML.relative_to(config.RAIZ)}")
    if gerar_pdf(SAIDA_HTML, SAIDA_PDF):
        print(f"PDF:  {SAIDA_PDF.relative_to(config.RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
