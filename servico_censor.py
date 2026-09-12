import json, os, re
from http.server import BaseHTTPRequestHandler, HTTPServer

PASTA_ACERVO = "acervo"
RESULTADOS = [("provido em parte","parcial"),("nao provido","negativo"),("nao conhecido","negativo"),("desprovido","negativo"),("negou provimento","negativo"),("improvido","negativo"),("provido","positivo"),("deu provimento","positivo"),("conhecido","positivo")]
_STOP = set("a o e de da do das dos que em no na nos nas um uma para por com sao ser foi como mais mas ou se ao aos pela pelo entre sobre sua seu suas seus este esta isso aquele qual quais tem ha nao sim".split())

def _limpa(t):
    t = t.replace("agra vo","agravo").replace("des provido","desprovido")
    return re.sub(r"\s+"," ", t.replace("\n"," ").replace("\r"," ")).strip()
def _norm(s):
    t = _limpa(s).lower(); t = re.sub(r"[^\w\sà-ÿ]"," ",t)
    return re.sub(r"\s+"," ",t).strip()
def _cp(termo, texto):
    return re.search(r"\b"+re.escape(termo)+r"\b", texto) is not None

def resultado_proprio(texto):
    low = _limpa(texto).lower(); cand=[]
    for m in re.finditer(r"\b\d{1,2}\.\s+([^.]{0,60}?(?:agravo|recurso|embargos)[^.]{0,40}?(?:n[aã]o\s+)?(?:des)?provid[oa])\b", low):
        if not low[m.end():m.end()+8].strip().startswith("("): cand.append(m.group(1))
    ab = low.split(" 1.")[0] if " 1." in low else low[:600]
    for termo,_ in RESULTADOS:
        if re.search(r"\b"+re.escape(termo)+r"\b", ab): cand.append(termo); break
    if not cand: return None
    tc=" ".join(cand)
    for termo,sent in RESULTADOS:
        if re.search(r"\b"+re.escape(termo)+r"\b", tc): return sent,termo
    return None
def resultado_citacao(trecho):
    low=_norm(trecho)
    for termo,sent in RESULTADOS:
        if _cp(termo,low): return sent,termo
    return None

def verificar(trecho, oficial, limiar=0.70):
    if not oficial.strip(): return "NAO_COMPROVAVEL",0.0,"inteiro teor indisponivel no acervo"
    rp=resultado_proprio(oficial); rc=resultado_citacao(trecho)
    if rp and rc and rp[0]!=rc[0] and "parcial" not in (rp[0],rc[0]):
        return "FABRICADA",0.0,f"polaridade invertida: decisao foi '{rp[1]}', citacao alega '{rc[1]}'"
    on=_norm(oficial); tn=_norm(trecho)
    anc={p for p in tn.split() if len(p)>=4 and p not in _STOP}
    if not anc: return "NAO_COMPROVAVEL",0.0,"citacao sem termos verificaveis"
    pres={a for a in anc if _cp(a,on)}; frac=len(pres)/len(anc)
    if frac>=limiar: return "CONFIRMADA",round(frac,3),f"resultado '{rp[1] if rp else 'coerente'}'; {len(pres)}/{len(anc)} ancoras presentes"
    return "FABRICADA",round(frac,3),f"apenas {len(pres)}/{len(anc)} ancoras presentes"

def carregar_acervo():
    ac={}; ip=os.path.join(PASTA_ACERVO,"indice.json")
    if not os.path.exists(ip): return ac
    for it in json.load(open(ip,encoding="utf-8")):
        p=os.path.join(PASTA_ACERVO,it["arquivo"])
        if os.path.exists(p): ac[it["num_registro"]]={"texto":open(p,encoding="utf-8").read()}
    return ac
ACERVO=carregar_acervo()

def analisar(minuta):
    res=[]; sent=re.split(r"(?<=[.;])\s+", minuta)
    for s in sent:
        for num in ACERVO:
            if num in s:
                e,sc,m=verificar(s.strip(), ACERVO[num]["texto"])
                res.append({"num":num,"trecho":s.strip(),"estado":e,"score":sc,"motivo":m}); break
    return res

PAGINA="""<!DOCTYPE html><html lang=pt-BR><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>CENSOR</title><style>body{font-family:Georgia,serif;max-width:820px;margin:40px auto;padding:0 20px;color:#1a1a1a;background:#faf8f4}h1{font-size:1.6em;border-bottom:2px solid #8a7050;padding-bottom:8px}.sub{color:#666;font-size:.9em;margin-top:-6px}textarea{width:100%;height:200px;font-size:1em;padding:12px;border:1px solid #bbb;border-radius:6px;box-sizing:border-box;font-family:Georgia,serif}button{background:#8a7050;color:#fff;border:0;padding:12px 28px;font-size:1em;border-radius:6px;cursor:pointer;margin-top:10px}button:hover{background:#6d5840}.card{border-left:5px solid #ccc;background:#fff;padding:14px 18px;margin:14px 0;border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,.08)}.CONFIRMADA{border-color:#2e7d32}.FABRICADA{border-color:#c62828}.NAO_COMPROVAVEL{border-color:#f9a825}.selo{font-weight:bold;font-size:.85em}.CONFIRMADA .selo{color:#2e7d32}.FABRICADA .selo{color:#c62828}.NAO_COMPROVAVEL .selo{color:#f9a825}.trecho{font-style:italic;color:#444;margin:6px 0}.motivo{font-size:.9em;color:#555}.vazio{color:#888;font-style:italic}</style></head><body><h1>CENSOR</h1><p class=sub>Verificacao de citacoes contra o inteiro teor oficial do STJ. Cole uma minuta.</p><textarea id=m placeholder="Cole a minuta com citacoes de acordaos do STJ..."></textarea><button onclick=ver()>Verificar citacoes</button><div id=r></div><script>async function ver(){const m=document.getElementById("m").value,r=document.getElementById("r");r.innerHTML="<p class=vazio>Verificando...</p>";const resp=await fetch("/analisar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({minuta:m})}),d=await resp.json();r.innerHTML=d.length?d.map(x=>`<div class="card ${x.estado}"><div class=selo>${x.estado} · processo ${x.num} · score ${x.score}</div><div class=trecho>"${x.trecho}"</div><div class=motivo>${x.motivo}</div></div>`).join(""):"<p class=vazio>Nenhuma citacao reconhecida.</p>"}</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(PAGINA.encode("utf-8"))
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0)); d=json.loads(self.rfile.read(n) or b"{}")
        b=json.dumps(analisar(d.get("minuta","")),ensure_ascii=False).encode("utf-8")
        self.send_response(200); self.send_header("Content-Type","application/json; charset=utf-8"); self.end_headers(); self.wfile.write(b)

if __name__=="__main__":
    print(f"Acervo: {len(ACERVO)} decisoes {list(ACERVO)}")
    print("No ar em http://localhost:8000  (feche a janela para parar)")
    HTTPServer(("127.0.0.1",8000),H).serve_forever()
