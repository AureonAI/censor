"""
CENSOR -- camada de fidelidade por ANCORAS + POLARIDADE (v3, soberana).
Fonte oficial: inteiro teor do STJ, direto, gratuito, sem agregador.
Aceita parafrase fiel (o que uma IA generativa produz) e barra fabricacao.
Tres estados: CONFIRMADA / FABRICADA / NAO_COMPROVAVEL.
"""
import io, re, urllib.parse, urllib.request

BASE_ITA = "https://processo.stj.jus.br/SCON/GetInteiroTeorDoAcordao"
STOPWORDS = set("a o e de da do das dos que em no na nos nas um uma para por com sao ser foi como mais mas ou se ao aos pela pelo entre sobre sua seu suas seus este esta isso aquele qual quais tem ha nao sim".split())
POLARIDADE = [("deu provimento","negou provimento"),("provido","desprovido"),("configurado","afastado"),("procedente","improcedente"),("deferiu","indeferiu"),("conhecido","nao conhecido")]

def url_inteiro_teor(num, data):
    d = str(data).strip()
    if "-" in d and len(d)==10:
        a,m,dia = d.split("-"); d = f"{dia}/{m}/{a}"
    return f"{BASE_ITA}?num_registro={num}&dt_publicacao={urllib.parse.quote(d, safe='')}"

def baixar_inteiro_teor(num, data):
    from pypdf import PdfReader
    try:
        req = urllib.request.Request(url_inteiro_teor(num,data), headers={"User-Agent":"Mozilla/5.0"})
        b = urllib.request.urlopen(req, timeout=60).read()
        if b[:4]!=b"%PDF": return ""
        return "".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(b)).pages)
    except Exception:
        return ""

def _norm(s):
    t = s.lower().replace("-\n","").replace("\r"," ").replace("\n"," ")
    t = re.sub(r"[^\w\sáéíóúâêôãõàç]"," ",t)
    return re.sub(r"\s+"," ",t).strip()

def _cp(termo, texto):
    return re.search(r"\b"+re.escape(termo)+r"\b", texto) is not None

def _polaridade(texto):
    t = _norm(texto)
    for pos,neg in POLARIDADE:
        if _cp(neg,t): return (neg,pos,neg)
        if _cp(pos,t): return (pos,pos,neg)
    return None

def verificar_fidelidade(trecho_citado, texto_oficial, limiar_ancora=0.70):
    """Retorna (estado, score, motivo)."""
    if not texto_oficial.strip():
        return "NAO_COMPROVAVEL", 0.0, "inteiro teor indisponivel na fonte oficial"
    oficial = _norm(texto_oficial)
    pc = _polaridade(trecho_citado)
    if pc:
        termo, pos, neg = pc; oposto = pos if termo==neg else neg
        if _cp(oposto, oficial) and not _cp(termo, oficial):
            return "FABRICADA", 0.0, f"polaridade invertida: citacao diz '{termo}', oficial diz '{oposto}'"
    anc = {p for p in _norm(trecho_citado).split() if len(p)>=4 and p not in STOPWORDS}
    if not anc:
        return "NAO_COMPROVAVEL", 0.0, "citacao sem termos de conteudo verificaveis"
    pres = {a for a in anc if _cp(a, oficial)}
    frac = len(pres)/len(anc)
    if frac >= limiar_ancora:
        return "CONFIRMADA", round(frac,3), f"{len(pres)}/{len(anc)} ancoras presentes; polaridade coerente"
    return "FABRICADA", round(frac,3), f"so {len(pres)}/{len(anc)} ancoras presentes no inteiro teor"
