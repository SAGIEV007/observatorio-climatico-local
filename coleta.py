"""Coleta dados meteorológicos históricos na API Open-Meteo e preserva a resposta original.

Uso:
    python coleta.py            # não refaz uma coleta que já existe
    python coleta.py --forcar   # coleta de novo; a anterior é guardada com a data no nome
"""

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone

import requests

import config

TENTATIVAS = 3


def montar_parametros():
    return {
        "latitude": config.LATITUDE,
        "longitude": config.LONGITUDE,
        "start_date": config.DATA_INICIO,
        "end_date": config.DATA_FIM,
        "daily": ",".join(config.VARIAVEIS),
        "timezone": config.FUSO_HORARIO,
    }


def baixar(parametros):
    """Faz a requisição, repetindo apenas em falhas temporárias de rede ou do servidor."""
    ultimo_erro = None
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = requests.get(config.URL_API, params=parametros, timeout=60)
            if resposta.status_code == 200:
                return resposta
            if resposta.status_code < 500 and resposta.status_code not in (408, 429):
                # Erro no pedido (ex.: data inválida): repetir não resolve.
                raise SystemExit(f"A API recusou o pedido (HTTP {resposta.status_code}): {resposta.text[:300]}")
            ultimo_erro = f"HTTP {resposta.status_code}"
        except requests.RequestException as erro:
            ultimo_erro = erro
        print(f"Tentativa {tentativa}/{TENTATIVAS} falhou: {ultimo_erro}")
        if tentativa < TENTATIVAS:
            time.sleep(2**tentativa)
    raise SystemExit(f"Coleta não concluída após {TENTATIVAS} tentativas: {ultimo_erro}")


def conferir_resposta(conteudo):
    """Garante que a resposta está completa antes de gravá-la como original."""
    dados = json.loads(conteudo)
    diarios = dados.get("daily", {})
    colunas = ["time", *config.VARIAVEIS]
    faltando = [nome for nome in ("latitude", "longitude", "elevation") if nome not in dados]
    faltando += [nome for nome in colunas if nome not in diarios]
    if faltando:
        raise SystemExit(f"Resposta da API sem os campos esperados: {faltando}")
    if len({len(diarios[nome]) for nome in colunas}) != 1:
        raise SystemExit("Resposta da API com colunas de tamanhos diferentes.")
    return dados


def guardar_coleta_anterior(momento):
    """Renomeia a coleta existente para que nenhum dado original seja sobrescrito."""
    for caminho in (config.ARQUIVO_ORIGINAL, config.ARQUIVO_METADADOS):
        if caminho.exists():
            nome_antigo = caminho.name.replace(config.NOME_ORIGINAL, f"{config.NOME_ORIGINAL}_substituido_{momento}")
            caminho.rename(caminho.with_name(nome_antigo))


def main():
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--forcar", action="store_true", help="coleta de novo mesmo que o arquivo já exista")
    forcar = argumentos.parse_args().forcar

    if config.ARQUIVO_ORIGINAL.exists() and not forcar:
        print(f"Coleta já existente, nada foi alterado: {config.ARQUIVO_ORIGINAL.relative_to(config.RAIZ).as_posix()}")
        print("Para coletar de novo, use: python coleta.py --forcar")
        return

    parametros = montar_parametros()
    resposta = baixar(parametros)
    dados = conferir_resposta(resposta.content)
    agora = datetime.now(timezone.utc).replace(microsecond=0)

    config.PASTA_ORIGINAIS.mkdir(parents=True, exist_ok=True)
    guardar_coleta_anterior(agora.strftime("%Y%m%dT%H%M%SZ"))

    # Os bytes recebidos são gravados sem nenhuma alteração.
    config.ARQUIVO_ORIGINAL.write_bytes(resposta.content)
    metadados = {
        "fonte": "Open-Meteo Historical Weather API",
        "url": resposta.url,
        "parametros": parametros,
        "coletado_em_utc": agora.isoformat(),
        "status_http": resposta.status_code,
        "arquivo": config.ARQUIVO_ORIGINAL.name,
        "tamanho_bytes": len(resposta.content),
        "sha256": hashlib.sha256(resposta.content).hexdigest(),
        "grade_devolvida": {
            "latitude": dados["latitude"],
            "longitude": dados["longitude"],
            "elevacao_m": dados["elevation"],
        },
    }
    config.ARQUIVO_METADADOS.write_text(json.dumps(metadados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Coleta concluída em {metadados['coletado_em_utc']} (UTC)")
    print(f"URL: {metadados['url']}")
    print(f"Status HTTP: {metadados['status_http']} | Dias recebidos: {len(dados['daily']['time'])}")
    print(f"Coordenadas pedidas: {config.LATITUDE}, {config.LONGITUDE}")
    print(f"Grade usada pela API: {dados['latitude']:.4f}, {dados['longitude']:.4f} (elevação {dados['elevation']:.0f} m)")
    print(f"Arquivo original: {config.ARQUIVO_ORIGINAL.relative_to(config.RAIZ).as_posix()} ({metadados['tamanho_bytes']} bytes)")
    print(f"SHA-256: {metadados['sha256']}")


if __name__ == "__main__":
    main()
