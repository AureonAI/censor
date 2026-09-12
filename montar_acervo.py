import io, os, json, urllib.parse, urllib.request

BASE = "https://processo.stj.jus.br/SCON/GetInteiroTeorDoAcordao"
PASTA = "acervo"
SEMENTE = [
    ("202504102465", "2026-06-29", "Raul Araujo"),
    ("202404013916", "2026-06-29", "Afranio Vilela"),
    ("202500434916", "2026-06-18", "Joao Otavio de Noronha"),
]

def url_ita(num, data):
    d = str(data).strip()
    if "-" in d and len(d)==10:
        a,m,dia = d.split("-"); d = f"{dia}/{m}/{a}"
    return f"{BASE}?num_registro={num}&dt_publicacao={urllib.parse.quote(d, safe='')}"

def baixar(num, data):
    from pypdf import PdfReader
    req = urllib.request.Request(url_ita(num,data), headers={"User-Agent":"Mozilla/5.0"})
    b = urllib.request.urlopen(req, timeout=60).read()
    if b[:4]!=b"%PDF": return ""
    return "".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(b)).pages)

os.makedirs(PASTA, exist_ok=True)
indice = []
print("Montando acervo soberano do STJ...")
print("="*60)
for num, data, relator in SEMENTE:
    try:
        texto = baixar(num, data)
    except Exception as e:
        print(f"  {num}: ERRO {type(e).__name__}: {e}"); continue
    if not texto.strip():
        print(f"  {num}: inteiro teor indisponivel"); continue
    with open(os.path.join(PASTA, f"{num}.txt"), "w", encoding="utf-8") as f:
        f.write(texto)
    indice.append({"num_registro":num,"data_publicacao":data,"relator":relator,"chars":len(texto),"arquivo":f"{num}.txt"})
    print(f"  {num}: salvo ({len(texto)} chars) rel. {relator}")
with open(os.path.join(PASTA,"indice.json"),"w",encoding="utf-8") as f:
    json.dump(indice, f, ensure_ascii=False, indent=2)
print("="*60)
print(f"Acervo com {len(indice)} decisoes salvo em {PASTA}\\")
