import json, os, random, re
from collections import Counter
PASTA="acervo"; SEMENTE=20260904

VERBOS=["desprovido","desproveu","provido","proveu","negou provimento","deu provimento","nao provido","improcedente","procedente","afastado","configurado","indeferiu","deferiu","desprovimento","provimento","nao conhecido","negado","concedido"]
INVERSOES=[("desprovido","provido"),("desproveu","proveu"),("negou provimento","deu provimento"),("nao provido","provido"),("improcedente","procedente"),("afastado","configurado"),("configurado","afastado"),("indeferiu","deferiu"),("desprovimento","provimento"),("nao conhecido","conhecido"),("negado","concedido")]
RUIDO=["advogado","assinado","documento eletronico","codigo de controle","relator :","agravante","agravado","interes.","signatario","e-stj","brasilia,","fls.","vda","certidao","presidiu","votaram","secretaria"]
ESTRUT=["questao em discussao","dispositivo","razoes de decidir","caso em exame","relatorio","acordao","ementa","voto","tese de julgamento"]

def limpa(t):
    for a,b in [("agra vo","agravo"),("AGRA VO","AGRAVO"),("des provido","desprovido"),("SILV A","SILVA"),("PROVIDO P ARA","PROVIDO PARA")]:
        t=t.replace(a,b)
    return re.sub(r"\s+"," ", t.replace("\n"," ").replace("\r"," ")).strip()
def norm(s):
    t=limpa(s).lower(); t=re.sub(r"[^\w\s]"," ",t)
    return re.sub(r"\s+"," ",t).strip()
def cp(v,t): return re.search(r"\b"+re.escape(v)+r"\b", t) is not None
def tem_verbo(f):
    low=f.lower(); return any(cp(v,low) for v in VERBOS)
def aceita_curta(f):
    low=f.lower().strip(" .;")
    if not tem_verbo(f): return False
    if any(low.startswith(r) or low==r for r in ESTRUT): return False
    return len([p for p in re.sub(r"[^\w\s]"," ",low).split() if len(p)>=4])>=3

def extrair(texto):
    t=limpa(texto); ped=[]
    for s in re.split(r"(?<=[.;])\s+", t):
        ped.append(s)
        if len(s)>220:
            for c in re.split(r",\s+(?=[a-z])", s):
                if len(c)>70: ped.append(c.strip().rstrip(",")+".")
    boas=[]; vis=set()
    for f in ped:
        f=f.strip()
        if not f: continue
        low=f.lower()
        if any(r in low for r in RUIDO): continue
        if re.search(r"\b[a-zA-Z]\b(?!\.)", f): continue
        curta = len(f)<40
        if curta:
            if not aceita_curta(f): continue
        else:
            if len(f)>240: continue
            if len([p for p in re.sub(r"[^\w\s]"," ",low).split() if len(p)>=5])<3: continue
        ch=low[:50]
        if ch in vis: continue
        vis.add(ch)
        if not f[0].isupper(): f=f[0].upper()+f[1:]
        if not f.rstrip().endswith((".",";")): f=f.rstrip()+"."
        boas.append(f)
    return boas

idx=json.load(open(os.path.join(PASTA,"indice.json"),encoding="utf-8"))
rng=random.Random(SEMENTE); casos=[]; npol=0; desc=0
for item in idx:
    num=item["num_registro"]
    texto=open(os.path.join(PASTA,item["arquivo"]),encoding="utf-8").read()
    of_n=norm(texto); fr=extrair(texto)
    longas=[f for f in fr if len(f)>100]
    ncv=sum(1 for f in fr if tem_verbo(f))
    pol_doc=0
    for f in fr:
        casos.append({"num":num,"trecho":f,"rotulo":"FIEL","tipo":"extraida"})
        casos.append({"num":num,"trecho":f.rstrip(".;")+", fixada indenizacao de R$ 480.000,00 a titulo de danos punitivos.","rotulo":"FABRICADA","tipo":"valor"})
        casos.append({"num":num,"trecho":f.rstrip(".;")+", conforme voto condutor do Ministro Herman Benjamin na Sexta Turma.","rotulo":"FABRICADA","tipo":"entidade"})
        low=f.lower()
        for a,b in INVERSOES:
            if cp(a,low):
                inv=re.sub(r"\b"+a+r"\b", b, f, flags=re.IGNORECASE)
                if inv.lower()!=low and norm(inv) not in of_n:
                    casos.append({"num":num,"trecho":inv,"rotulo":"FABRICADA","tipo":"polaridade"})
                    npol+=1; pol_doc+=1
                elif norm(inv) in of_n: desc+=1
                break
    # A2: inversoes ENTERRADAS em frases longas verdadeiras
    for f in longas[:12]:
        ent=f.rstrip(".;")+", tendo o recurso sido provido por unanimidade."
        if norm(ent) not in of_n:
            casos.append({"num":num,"trecho":ent,"rotulo":"FABRICADA","tipo":"pol_enterrada"})
            npol+=1
    print(f"  {num}: {len(fr)} frases | {ncv} com verbo | {pol_doc} inversoes diretas")

porg={}
for c in casos: porg.setdefault((c["rotulo"],c["tipo"]),[]).append(c)
cal=[];tes=[]
for g,l in sorted(porg.items()):
    rng.shuffle(l); m=len(l)//2
    cal+=l[:m]; tes+=l[m:]
rng.shuffle(cal); rng.shuffle(tes)
json.dump({"semente":SEMENTE,"calibracao":cal,"teste":tes}, open("conjunto_avaliacao.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nTotal {len(casos)} | cal {len(cal)} | teste {len(tes)}")
print(f"  casos de polaridade: {npol} (descartados por existirem no oficial: {desc})")
print("  teste - tipos:", dict(Counter(c["tipo"] for c in tes)))
if npol<10: print("  *** AVISO: polaridade AINDA insuficientemente medida")
