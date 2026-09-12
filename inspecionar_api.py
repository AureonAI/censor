"""
inspecionar_api.py (versão 2 -- corrigida)

Primeira metade da missão de hoje: só ENXERGAR o formato real que a API
da Jurisprudencias.ai devolve, antes de qualquer adaptação do gate.py.
Não presume nenhum campo -- só imprime exatamente o que vier.

O QUE MUDOU NESTA VERSÃO: o token agora mora num arquivo separado,
chamado token.txt, na mesma pasta deste script. Isto evita o erro
anterior, causado por eu (Claude) ter escrito a mesma palavra de
marcação em dois lugares diferentes dentro do código.

Como usar:
  1. Nesta mesma pasta (D:\\GATE_VERIFICACAO), crie um arquivo novo de
     texto chamado exatamente: token.txt
  2. Abra token.txt e cole SOMENTE o token dentro -- nada de aspas,
     nada de texto explicativo, só o token puro. Salve.
  3. Rode: python inspecionar_api.py
  4. Copie TODA a saída (do começo ao fim) e me envie de volta.

Este script nunca imprime o token inteiro -- só os 6 primeiros
caracteres, para você confirmar que leu o arquivo certo. Pode copiar a
saída sem medo de expor sua chave. Mesmo assim, não compartilhe o
arquivo token.txt com mais ninguém.
"""

import gzip
import json
import os
import urllib.error
import urllib.request

PASTA_DESTE_ARQUIVO = os.path.dirname(os.path.abspath(__file__))
CAMINHO_TOKEN = os.path.join(PASTA_DESTE_ARQUIVO, "token.txt")
BASE_URL = "https://jurisprudencias.ai/api/v1"


def carregar_token() -> str:
    if not os.path.exists(CAMINHO_TOKEN):
        print(f"Não encontrei o arquivo: {CAMINHO_TOKEN}")
        print()
        print("Crie um arquivo chamado token.txt nesta mesma pasta,")
        print("cole dentro dele SOMENTE o token gerado em")
        print("jurisprudencias.ai/api-tokens (sem aspas, sem mais nada),")
        print("salve, e rode este script de novo.")
        raise SystemExit(1)

    with open(CAMINHO_TOKEN, "r", encoding="utf-8") as arquivo:
        token = arquivo.read().strip()

    if not token:
        print(f"O arquivo {CAMINHO_TOKEN} existe, mas está vazio.")
        print("Abra-o e cole o token gerado em jurisprudencias.ai/api-tokens.")
        raise SystemExit(1)

    return token


def chamar_api(token: str, caminho: str) -> dict:
    url = f"{BASE_URL}{caminho}"
    requisicao = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip",
        },
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=20) as resposta:
            corpo_bruto = resposta.read()
            if resposta.headers.get("Content-Encoding") == "gzip":
                corpo_bruto = gzip.decompress(corpo_bruto)
            corpo = corpo_bruto.decode("utf-8")
            return json.loads(corpo)
    except urllib.error.HTTPError as erro:
        print(f"ERRO HTTP {erro.code} ao chamar {url}")
        print(erro.read().decode("utf-8"))
        raise
    except urllib.error.URLError as erro:
        print(f"ERRO DE CONEXÃO ao chamar {url}: {erro.reason}")
        print("Verifique sua internet.")
        raise


TOKEN = carregar_token()
print(f"Token lido de token.txt (começa com '{TOKEN[:6]}...', {len(TOKEN)} caracteres no total)")
print()

print("=" * 78)
print("PASSO 1 -- confirmar que o token funciona (lista de tribunais)")
print("=" * 78)
tribunais = chamar_api(TOKEN, "/courts")
print(json.dumps(tribunais, indent=2, ensure_ascii=False))

print()
print("=" * 78)
print("PASSO 2 -- buscar uma decisão real do STJ sobre 'dano moral'")
print("=" * 78)
busca = chamar_api(TOKEN, "/courts/stj/decisions?q=dano+moral&page=0")
print(json.dumps(busca, indent=2, ensure_ascii=False))

print()
print("=" * 78)
print("FIM -- copie tudo o que apareceu acima (desde 'Token lido de') e envie de volta")
print("=" * 78)
