"""
Varredura de segredos antes de publicar (prevencao, nao disciplina).
Falha com codigo 1 se encontrar padrao de credencial nos arquivos rastreados.
Rodar ANTES de qualquer push:  python verificar_segredos.py
"""
import re, subprocess, sys

PADROES = [
    (r"jur_[A-Za-z0-9]{20,}", "token jurisprudencias.ai"),
    (r"sk-[A-Za-z0-9]{20,}", "chave OpenAI"),
    (r"gh[pousr]_[A-Za-z0-9]{20,}", "token GitHub"),
    (r"AKIA[0-9A-Z]{16}", "chave AWS"),
    (r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{12,}['\"]", "credencial embutida"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "chave privada"),
]

def arquivos_rastreados():
    r = subprocess.run(["git","ls-files"], capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l.strip()]

def main():
    achados = []
    for arq in arquivos_rastreados():
        try:
            conteudo = open(arq, encoding="utf-8", errors="ignore").read()
        except (IsADirectoryError, PermissionError, FileNotFoundError):
            continue
        for padrao, nome in PADROES:
            for m in re.finditer(padrao, conteudo):
                achados.append((arq, nome, m.group()[:12] + "..."))
    if achados:
        print("SEGREDOS ENCONTRADOS -- NAO PUBLIQUE:")
        for arq, nome, amostra in achados:
            print(f"  {arq}: {nome} ({amostra})")
        sys.exit(1)
    print(f"OK: {len(arquivos_rastreados())} arquivos rastreados, nenhum segredo encontrado.")

if __name__ == "__main__":
    main()
