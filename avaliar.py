"""
Avalia o CENSOR conforme o PRE_REGISTRO.
Calibra o limiar SOMENTE no conjunto de calibracao; mede SOMENTE no de teste.
Reporta contra o critério de sucesso e o falsificador pré-registrados.
"""
import json, math, os, re

PASTA = "acervo"
RESULTADOS=[("provido em parte","parcial"),("nao provido","negativo"),("nao conhecido","negativo"),
 ("desprovido","negativo"),("negou provimento","negativo"),("improvido","negativo"),
 ("provido","positivo"),("deu provimento","positivo"),("conhecido","positivo")]
_STOP=set("a o e de da do das dos que em no na nos nas um uma para por com sao ser foi como mais mas ou se ao aos pela pelo entre sobre sua seu suas seus este esta isso aquele qual quais tem ha nao sim".split())

def _limpa(t):
    t=t.replace("agra vo","agravo").replace("des provido","desprovido").replace("AGRA VO","AGRAVO")
    return re.sub(r"\s+"," ", t.replace("\n"," ").replace("\r"," ")).strip()
def _norm(s):
    t=_limpa(s).lower(); t=re.sub(r"[^\w\sà-ÿ]"," ",t)
    return re.sub(r"\s+"," ",t).strip()
def _cp(termo,texto): return re.search(r"\b"+re.escape(termo)+r"\b",texto) is not None
def _rp(texto):
    low=_limpa(texto).lower(); cand=[]
    for m in re.finditer(r"\b\d{1,2}\.\s+([^.]{0,60}?(?:agravo|recurso|embargos)[^.]{0,40}?(?:n[aã]o\s+)?(?:des)?provid[oa])\b",low):
        if not low[m.end():m.end()+8].strip().startswith("("): cand.append(m.group(1))
    ab=low.split(" 1.")[0] if " 1." in low else low[:600]
    for termo,_ in RESULTADOS:
        if re.search(r"\b"+re.escape(termo)+r"\b",ab): cand.append(termo); break
    if not cand: return None
    tc=" ".join(cand)
    for termo,s in RESULTADOS:
        if re.search(r"\b"+re.escape(termo)+r"\b",tc): return s,termo
    return None
def _rc(trecho):
    low=_norm(trecho)
    for termo,s in RESULTADOS:
        if _cp(termo,low): return s,termo
    return None

def score_e_polaridade(trecho, oficial):
    """Retorna (violou_polaridade, fracao_ancoras)."""
    rp=_rp(oficial); rc=_rc(trecho)
    violou = bool(rp and rc and rp[0]!=rc[0] and "parcial" not in (rp[0],rc[0]))
    on=_norm(oficial); tn=_norm(trecho)
    anc={p for p in tn.split() if len(p)>=4 and p not in _STOP}
    frac = (len(({a for a in anc if _cp(a,on)}))/len(anc)) if anc else 0.0
    return violou, frac

def prever(trecho, oficial, limiar):
    violou, frac = score_e_polaridade(trecho, oficial)
    if violou: return "FABRICADA"
    return "CONFIRMADA" if frac >= limiar else "FABRICADA"

def wilson(acertos, n, z=1.96):
    if n==0: return (0.0,0.0)
    p=acertos/n; d=1+z*z/n
    centro=(p+z*z/(2*n))/d
    margem=z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return (max(0.0,centro-margem), min(1.0,centro+margem))

def metricas(casos, acervo, limiar):
    vp=fp=vn=fn=0
    for c in casos:
        oficial=acervo.get(c["num"],"")
        pred=prever(c["trecho"], oficial, limiar)
        real=c["rotulo"]
        if real=="FIEL" and pred=="CONFIRMADA": vp+=1
        elif real=="FIEL" and pred=="FABRICADA": fn+=1
        elif real=="FABRICADA" and pred=="FABRICADA": vn+=1
        else: fp+=1
    n=vp+fp+vn+fn
    acc=(vp+vn)/n if n else 0
    tfp=fp/(fp+vn) if (fp+vn) else 0   # aprovou fabricada
    tfn=fn/(fn+vp) if (fn+vp) else 0   # recusou fiel
    prec=vp/(vp+fp) if (vp+fp) else 0
    rec=vp/(vp+fn) if (vp+fn) else 0
    return dict(vp=vp,fp=fp,vn=vn,fn=fn,n=n,acc=acc,tfp=tfp,tfn=tfn,prec=prec,rec=rec,
                ic=wilson(vp+vn,n))

def main():
    conj=json.load(open("conjunto_avaliacao.json",encoding="utf-8"))
    idx=json.load(open(os.path.join(PASTA,"indice.json"),encoding="utf-8"))
    acervo={i["num_registro"]:open(os.path.join(PASTA,i["arquivo"]),encoding="utf-8").read() for i in idx}

    print("="*72); print("FASE A -- CALIBRACAO (escolher limiar; nunca reportar acuracia daqui)")
    print("="*72)
    print(f"{'limiar':>8} {'acc':>7} {'FP%':>7} {'FN%':>7}   passa critério?")
    melhor=None
    for lim in [i/20 for i in range(4,19)]:
        m=metricas(conj["calibracao"], acervo, lim)
        ok = m["tfp"]<=0.05 and m["tfn"]<=0.20
        print(f"{lim:>8.2f} {m['acc']:>7.3f} {m['tfp']*100:>6.1f}% {m['tfn']*100:>6.1f}%   {'SIM' if ok else 'nao'}")
        # escolhe o que satisfaz o critério com maior acuracia
        if ok and (melhor is None or m["acc"]>melhor[1]["acc"]): melhor=(lim,m)
    if melhor is None:
        print("\nNENHUM limiar satisfaz o critério na calibracao.")
        print("=> FALSIFICADOR DISPARADO (3a condicao do pre-registro).")
        # ainda assim mede no teste com o melhor acc para reportar honestamente
        melhor=max(((l,metricas(conj["calibracao"],acervo,l)) for l in [i/20 for i in range(4,19)]),
                   key=lambda x:x[1]["acc"])
        print(f"   (medindo no teste com limiar de maior acuracia: {melhor[0]:.2f})")
    LIMIAR=melhor[0]
    print(f"\nLIMIAR FIXADO NA CALIBRACAO: {LIMIAR:.2f}")

    print("\n"+"="*72); print("FASE B -- TESTE (o numero que vale; limiar ja fixado)")
    print("="*72)
    m=metricas(conj["teste"], acervo, LIMIAR)
    print(f"  N = {m['n']} casos")
    print(f"  VP={m['vp']}  FP={m['fp']}  VN={m['vn']}  FN={m['fn']}")
    print(f"  acuracia ......... {m['acc']*100:.1f}%   IC95% [{m['ic'][0]*100:.1f}% , {m['ic'][1]*100:.1f}%]")
    print(f"  precisao ......... {m['prec']*100:.1f}%")
    print(f"  recall ........... {m['rec']*100:.1f}%")
    print(f"  falso-POSITIVO ... {m['tfp']*100:.1f}%  (aprovou fabricada -- erro PERIGOSO)")
    print(f"  falso-NEGATIVO ... {m['tfn']*100:.1f}%  (recusou fiel -- erro de credibilidade)")

    print("\n"+"="*72); print("VEREDITO contra o PRE-REGISTRO")
    print("="*72)
    s1=m["tfp"]<=0.05; s2=m["tfn"]<=0.20; s3=m["ic"][0]>=0.70
    print(f"  [{'OK' if s1 else 'FALHA'}] falso-positivo <= 5%      : {m['tfp']*100:.1f}%")
    print(f"  [{'OK' if s2 else 'FALHA'}] falso-negativo <= 20%     : {m['tfn']*100:.1f}%")
    print(f"  [{'OK' if s3 else 'FALHA'}] IC95 inferior >= 70%      : {m['ic'][0]*100:.1f}%")
    f1=m["tfp"]>0.15; f2=m["tfn"]>0.40
    print(f"  falsificador FP>15%: {'DISPAROU' if f1 else 'nao'}")
    print(f"  falsificador FN>40%: {'DISPAROU' if f2 else 'nao'}")
    print()
    if s1 and s2 and s3: print("  >>> NUCLEO SUSTENTADO conforme critério pre-registrado.")
    elif f1 or f2: print("  >>> NUCLEO FALHOU: falsificador disparado. Reportar como falha.")
    else: print("  >>> RESULTADO INTERMEDIARIO: nao atinge o critério, nao dispara falsificador.")
    print("\n  LIMITACAO: casos derivados de 3 acordaos do STJ, mesma materia.")
    print("  Amostras CORRELACIONADAS -- o IC acima e OTIMISTA. Sem generalizacao.")

if __name__ == "__main__":
    main()
