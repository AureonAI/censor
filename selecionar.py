import re

POLARIDADE = [
    ("deu provimento", "negou provimento"),
    ("provido", "desprovido"),
    ("configurado", "afastado"),
    ("procedente", "improcedente"),
    ("deferiu", "indeferiu"),
    ("conhecido", "nao conhecido"),
]

def _norm(s):
    return re.sub(r"\s+", " ", s.lower())

def polaridade_da_decisao(excerpt):
    t = _norm(excerpt)
    for pos, neg in POLARIDADE:
        if re.search(r"\b" + re.escape(neg) + r"\b", t):
            return ("negativo", neg, (pos, neg))
        if re.search(r"\b" + re.escape(pos) + r"\b", t):
            return ("positivo", pos, (pos, neg))
    return None

def escolher_decisao_utilizavel(decisoes):
    for d in decisoes:
        num = (d.get("process_number") or "").strip()
        exc = d.get("excerpt") or ""
        if not num or not exc:
            continue
        pol = polaridade_da_decisao(exc)
        if pol:
            return d, pol
    return None, None
