"""
gate.py -- mecânica de aceite/recusa auditável, extraída por engenharia
reversa e destilação do pipeline de anonimização do portfólio (camada
exata + camada de fidelidade + camada de polaridade + camada numérica +
gate fail-closed + proveniência por unidade), aplicada aqui a verificação
de citação de precedente jurídico. Nenhuma linha deste arquivo trata de
dado pessoal ou anonimização -- a mecânica foi generalizada de propósito.

Quatro camadas, cada uma cobrindo um tipo de fabricação diferente:
  1. Exata       -- identificadores estruturados (nº processo, relator, tipo)
  2. Fidelidade  -- o trecho citado existe mesmo, verbatim ou quase, no
                    texto oficial?
  3. Polaridade  -- o veredito citado é o MESMO veredito do texto oficial,
                    não um resultado oposto disfarçado de texto parecido?
  4. Numérica    -- valores monetários, percentuais, prazos e datas citados
                    batem com os valores realmente presentes no oficial?

Gate fail-closed: só aceita se as quatro camadas passarem. Uma recusa
sempre declara o motivo -- nunca "não sei", sempre "recusei, e por quê".
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from enum import Enum
from typing import Optional


class Decisao(Enum):
    ACEITA = "aceita"
    RECUSADA = "recusada"


@dataclass(frozen=True)
class RegistroOficial:
    """O que uma fonte externa (não controlada por nós) devolveria para
    um número de processo real. Em produção: resposta de API de
    tribunal, DataJud, ou agregador como jurisprudencias.ai.

    Dois campos são opcionais de propósito, porque a fonte real que
    testamos (jurisprudencias.ai) NÃO devolve os dois:

    tipo_decisao: fica None quando a fonte não distingue monocrática de
      colegiada. Quando None, a camada exata simplesmente não checa esse
      aspecto -- e diz isso explicitamente, em vez de fingir que
      verificou.

    cobertura_completa: True só quando texto_integral é o texto INTEIRO
      da decisão. Quando a fonte só dá um excerto (como a
      jurisprudencias.ai dá), isto fica False, e qualquer recusa das
      camadas de fidelidade/polaridade/numérica passa a vir acompanhada
      do aviso de que a ausência pode ser só porque o trecho consultado
      é parcial -- não prova fabricação, só falta de confirmação."""
    numero_processo: str
    relator: str
    texto_integral: str
    fonte: str
    tipo_decisao: Optional[str] = None
    cobertura_completa: bool = True


@dataclass(frozen=True)
class CitacaoAlegada:
    """O que a IA produziu e quer inserir na peça."""
    numero_processo: str
    relator: str
    trecho_citado: str
    tipo_decisao: Optional[str] = None


@dataclass(frozen=True)
class Recibo:
    """Proveniência por unidade processada. Todo Recibo é definitivo e
    poderia, em produção, ser assinado e versionado (VESTIGIUM/SIGILLUM)."""
    decisao: Decisao
    motivo: str
    camada_exata_ok: bool
    camada_fidelidade_ok: bool
    camada_polaridade_ok: bool
    camada_numerica_ok: bool
    score_fidelidade: float
    fonte_consultada: str
    hash_registro_oficial: str
    timestamp: str


def camada_exata(alegada: CitacaoAlegada, oficial: RegistroOficial) -> tuple[bool, str]:
    if alegada.numero_processo != oficial.numero_processo:
        return False, "número de processo não corresponde ao registro oficial consultado"
    if alegada.relator.strip().lower() != oficial.relator.strip().lower():
        return False, (
            f"relator divergente: peça alega '{alegada.relator}', "
            f"registro oficial traz '{oficial.relator}'"
        )

    if oficial.tipo_decisao is None:
        return True, (
            "número de processo e relator conferem com o registro oficial "
            "(tipo de decisão NÃO verificado -- a fonte consultada não fornece esse dado)"
        )

    if alegada.tipo_decisao is None:
        return True, (
            "número de processo e relator conferem com o registro oficial "
            "(tipo de decisão não checado -- a peça alegada não especificou)"
        )

    if alegada.tipo_decisao.strip().lower() != oficial.tipo_decisao.strip().lower():
        return False, (
            f"tipo de decisão divergente: peça alega '{alegada.tipo_decisao}', "
            f"registro oficial traz '{oficial.tipo_decisao}'"
        )
    return True, "identificadores conferem com o registro oficial"


_RESULTADOS_POL = [("provido em parte","parcial"),("nao provido","negativo"),("nao conhecido","negativo"),("desprovido","negativo"),("negou provimento","negativo"),("improvido","negativo"),("provido","positivo"),("deu provimento","positivo"),("conhecido","positivo")]

def _limpa_pol(t):
    t = t.replace("agra vo","agravo").replace("des provido","desprovido")
    return re.sub(r"\s+"," ", t.replace("\n"," ").replace("\r"," ")).strip()

def _resultado_proprio(texto):
    low = _limpa_pol(texto).lower(); cand=[]
    for m in re.finditer(r"\b\d{1,2}\.\s+([^.]{0,60}?(?:agravo|recurso|embargos)[^.]{0,40}?(?:n[aã]o\s+)?(?:des)?provid[oa])\b", low):
        if not low[m.end():m.end()+8].strip().startswith("("): cand.append(m.group(1))
    ab = low.split(" 1.")[0] if " 1." in low else low[:600]
    for termo,_ in _RESULTADOS_POL:
        if re.search(r"\b"+re.escape(termo)+r"\b", ab): cand.append(termo); break
    if not cand: return None
    tc=" ".join(cand)
    for termo,sent in _RESULTADOS_POL:
        if re.search(r"\b"+re.escape(termo)+r"\b", tc): return sent,termo
    return None

def _resultado_citacao(trecho):
    low = _limpa_pol(trecho).lower()
    for termo,sent in _RESULTADOS_POL:
        if re.search(r"\b"+re.escape(termo)+r"\b", low): return sent,termo
    return None

def camada_fidelidade(
    alegada: CitacaoAlegada, oficial: RegistroOficial, limiar: float = 0.70
) -> tuple[bool, str, float]:
    """Fidelidade por ANCORAS + POLARIDADE contra o inteiro teor oficial.
    Aceita parafrase fiel e barra fabricacao. Mesma assinatura e retorno."""
    import re as _re
    _STOP = set("a o e de da do das dos que em no na nos nas um uma para por com sao ser foi como mais mas ou se ao aos pela pelo entre sobre sua seu suas seus este esta isso aquele qual quais tem ha nao sim".split())
    _POL = [("deu provimento","negou provimento"),("provido","desprovido"),("configurado","afastado"),("procedente","improcedente"),("deferiu","indeferiu"),("conhecido","nao conhecido")]
    def _norm(s):
        t = s.lower().replace("-\n","").replace("\r"," ").replace("\n"," ")
        t = _re.sub(r"[^\w\s\u00e0-\u00ff]"," ",t)
        return _re.sub(r"\s+"," ",t).strip()
    def _cp(termo, texto):
        return _re.search(r"\b"+_re.escape(termo)+r"\b", texto) is not None
    trecho = alegada.trecho_citado.strip()
    texto = oficial.texto_integral
    if not texto or not texto.strip():
        aviso = " [AVISO: inteiro teor oficial indisponivel; verificacao humana recomendada]" if not oficial.cobertura_completa else ""
        return False, "NAO_COMPROVAVEL: inteiro teor oficial indisponivel" + aviso, 0.0
    oficial_n = _norm(texto)
    _rp = _resultado_proprio(texto)
    _rc = _resultado_citacao(trecho)
    if _rp and _rc and _rp[0] != _rc[0] and "parcial" not in (_rp[0], _rc[0]):
        return False, f"FABRICADA: polaridade invertida (decisao foi \x27{_rp[1]}\x27, citacao alega \x27{_rc[1]}\x27)", 0.0
    oficial_n = _norm(texto)
    tn = _norm(trecho)
    anc = {p for p in tn.split() if len(p) >= 4 and p not in _STOP}
    if not anc:
        return False, "NAO_COMPROVAVEL: citacao sem termos de conteudo verificaveis", 0.0
    pres = {a for a in anc if _cp(a, oficial_n)}
    frac = len(pres) / len(anc)
    if frac >= limiar:
        return True, f"CONFIRMADA: {len(pres)}/{len(anc)} ancoras presentes no inteiro teor oficial; polaridade coerente", round(frac, 3)
    return False, f"FABRICADA: apenas {len(pres)}/{len(anc)} ancoras presentes no inteiro teor oficial (limiar {limiar})", round(frac, 3)


    # Pares de polaridade jurídica: (marcador_A, marcador_B) são resultados
    # opostos. A lista é pequena de propósito -- cada par foi escolhido por
    # ser um veredito que muda o resultado prático da decisão. Isto NÃO é
    # exaustivo; é um V1 deliberadamente pequeno e auditável, não uma
    # tentativa de cobrir toda a língua portuguesa jurídica de uma vez.
PARES_POLARIDADE: tuple[tuple[str, str], ...] = (
    ("indeferiu", "deferiu"),
    ("indeferido", "deferido"),
    ("negou provimento", "deu provimento"),
    ("negou", "concedeu"),
    ("denegou", "concedeu"),
    ("denegada", "concedida"),
    ("improcedente", "procedente"),
    ("condenou", "absolveu"),
    ("condenado", "absolvido"),
    ("manteve a prisão", "revogou a prisão"),
    ("manteve", "revogou"),
    ("confirmou", "reformou"),
    ("negou seguimento", "deu seguimento"),
    # Adicionados após rodar contra dado real do STJ (02/09/2026) -- este é
    # o vocabulário mais comum de todos nos acórdãos reais que vimos, e
    # não estava coberto até aqui:
    ("desprovido", "provido"),
    ("desprovidos", "providos"),
    ("desproveu", "proveu"),
    ("não provido", "provido"),
    ("não provida", "provida"),
)


def _aviso_cobertura_parcial(oficial: RegistroOficial) -> str:
    if oficial.cobertura_completa:
        return ""
    return (
        " [AVISO: fonte oferece apenas excerto parcial, não o texto integral -- "
        "esta recusa pode ser só ausência no trecho disponível, não fabricação "
        "confirmada; verificação humana direta na fonte é recomendada]"
    )


def _contem_palavra(marcador: str, texto: str) -> bool:
    """Checagem por fronteira de palavra, não por substring cega.

    Sem isto, 'provido' seria encontrado DENTRO de 'desprovido' (e
    'procedente' dentro de 'improcedente'), o que inverteria o sentido
    exato que esta camada existe para proteger. Bug real, encontrado ao
    testar contra vocabulário de decisão de tribunal de verdade
    (02/09/2026), corrigido antes de qualquer teste novo."""
    padrao = r"\b" + re.escape(marcador) + r"\b"
    return re.search(padrao, texto) is not None


def camada_polaridade(
    alegada: CitacaoAlegada, oficial: RegistroOficial
) -> tuple[bool, str]:
    """Camada 3 -- a que faltava. Verifica se o veredito citado pela IA é
    o MESMO veredito do documento oficial, não apenas um texto parecido.

    Limite declarado, sem maquiagem: isto cobre só os pares listados acima.
    'True' aqui significa 'nenhum conflito nos pares conhecidos', não
    'polaridade garantidamente correta'. Fora do lexicon, esta camada é
    cega -- e isso precisa aparecer no motivo, não ficar escondido."""
    texto_oficial = oficial.texto_integral.lower()
    texto_alegado = alegada.trecho_citado.lower()

    for marcador_a, marcador_b in PARES_POLARIDADE:
        oficial_usa_a = _contem_palavra(marcador_a, texto_oficial)
        oficial_usa_b = _contem_palavra(marcador_b, texto_oficial)
        alegado_usa_a = _contem_palavra(marcador_a, texto_alegado)
        alegado_usa_b = _contem_palavra(marcador_b, texto_alegado)

        if oficial_usa_a and alegado_usa_b and not alegado_usa_a:
            return False, (
                f"polaridade invertida: registro oficial usa '{marcador_a}', "
                f"peça alegada usa '{marcador_b}' (resultado oposto)"
                f"{_aviso_cobertura_parcial(oficial)}"
            )
        if oficial_usa_b and alegado_usa_a and not alegado_usa_b:
            return False, (
                f"polaridade invertida: registro oficial usa '{marcador_b}', "
                f"peça alegada usa '{marcador_a}' (resultado oposto)"
                f"{_aviso_cobertura_parcial(oficial)}"
            )

    return True, "nenhum conflito de polaridade nos pares conhecidos (cobertura limitada ao lexicon)"


# Padrões numéricos reconhecidos. Cada categoria captura um TIPO de
# afirmação factual que costuma ser o alvo de fabricação de alto custo
# (valor de multa, tempo de pena, prazo, data) -- coisas que "parecem"
# just um número a mais, mas mudam o resultado prático da citação.
PADROES_NUMERICOS: dict[str, re.Pattern] = {
    "valor_monetario": re.compile(r"R\$\s?([\d\.]+,\d{2})"),
    "percentual": re.compile(r"(\d+(?:,\d+)?)\s?%"),
    "duracao_anos": re.compile(r"(\d+)\s?anos?\b"),
    "duracao_meses": re.compile(r"(\d+)\s?meses?\b"),
    "duracao_dias": re.compile(r"(\d+)\s?dias?\b"),
    "data": re.compile(r"(\d{1,2}/\d{1,2}/\d{2,4})"),
    "salarios_minimos": re.compile(r"(\d+(?:,\d+)?)\s?sal[aá]rios?[\s-]m[ií]nimos?", re.IGNORECASE),
}


def _normalizar_valor_brl(valor_str: str) -> Decimal:
    """Converte '50.000,00' (formato brasileiro) em Decimal('50000.00'),
    para que a comparação não dependa de como o número foi escrito."""
    limpo = valor_str.replace(".", "").replace(",", ".")
    return Decimal(limpo)


def _extrair_afirmacoes_numericas(texto: str) -> dict[str, set[str]]:
    achados: dict[str, set[str]] = {}
    for categoria, padrao in PADROES_NUMERICOS.items():
        achados[categoria] = set(padrao.findall(texto))
    return achados


def camada_numerica(alegada: CitacaoAlegada, oficial: RegistroOficial) -> tuple[bool, str]:
    """Camada 4 -- a que faltava depois do ataque de valor monetário.
    Extrai valores, percentuais, prazos e datas do trecho alegado e
    confere se cada um deles também aparece no texto oficial.

    Limite declarado, sem maquiagem: só reconhece os padrões listados
    acima (formato brasileiro de moeda, %, 'X anos/meses/dias', datas
    DD/MM/AAAA, salários mínimos). Um valor escrito por extenso ("cinco
    mil reais") ou um formato fora desses passa batido por esta camada --
    isso é um limite conhecido, não uma garantia de cobertura total."""
    achados_oficial = _extrair_afirmacoes_numericas(oficial.texto_integral)
    achados_alegado = _extrair_afirmacoes_numericas(alegada.trecho_citado)

    for categoria, valores_alegados in achados_alegado.items():
        if not valores_alegados:
            continue
        valores_oficiais = achados_oficial.get(categoria, set())

        if categoria == "valor_monetario":
            try:
                oficiais_norm = {_normalizar_valor_brl(v) for v in valores_oficiais}
                for v in valores_alegados:
                    if _normalizar_valor_brl(v) not in oficiais_norm:
                        return False, (
                            f"valor monetário citado ('R$ {v}') não corresponde a "
                            f"nenhum valor do registro oficial ({sorted(valores_oficiais) or 'nenhum encontrado'})"
                            f"{_aviso_cobertura_parcial(oficial)}"
                        )
            except InvalidOperation:
                return False, f"valor monetário mal formatado na peça alegada: '{valores_alegados}'"
        else:
            for v in valores_alegados:
                if v not in valores_oficiais:
                    return False, (
                        f"{categoria.replace('_', ' ')} citado ('{v}') não corresponde a "
                        f"nenhum valor do registro oficial ({sorted(valores_oficiais) or 'nenhum encontrado'})"
                        f"{_aviso_cobertura_parcial(oficial)}"
                    )

    return True, "nenhuma divergência numérica encontrada nas categorias reconhecidas (cobertura limitada aos padrões declarados)"


# ---------------------------------------------------------------------
# Retroalimentação COM FREIO: o gate nunca aprende sozinho. Ele só
# REGISTRA candidatos a expressão nova de polaridade, para revisão
# humana obrigatória (revisar_candidatos.py). Nenhuma linha deste bloco
# altera PARES_POLARIDADE em tempo de execução -- isso só acontece se um
# humano, depois de olhar o candidato, editar o código à mão.
#
# Por quê o freio: um sistema que aprende suas próprias regras de
# verificação a partir das próprias inferências deixa de ser um
# verificador -- vira um espelho. "Nenhum sistema se autocertifica" não
# é só uma frase; é a diferença entre um gate e um placebo de gate.
# ---------------------------------------------------------------------

CAMINHO_CANDIDATOS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "candidatos_revisao.jsonl"
)

# Faixa de "quase passou": abaixo do limiar de aceite, mas perto o
# suficiente para sugerir paráfrase legítima (possível vocabulário de
# polaridade que ainda não conhecemos) em vez de fabricação grosseira.
ZONA_CANDIDATA_MIN = 0.60


def _e_candidato_a_novo_padrao(recibo_parcial: dict) -> bool:
    """Um caso é candidato quando: exata e numérica passaram, polaridade
    não viu conflito (está cega, não contraditando), e a fidelidade
    falhou por pouco -- exatamente o perfil de 'talvez seja uma
    expressão que ainda não está no lexicon', não de erro grosseiro."""
    return (
        recibo_parcial["exata_ok"]
        and recibo_parcial["numerica_ok"]
        and recibo_parcial["polaridade_ok"]
        and not recibo_parcial["fidelidade_ok"]
        and ZONA_CANDIDATA_MIN <= recibo_parcial["score"] < recibo_parcial["limiar"]
    )


def _registrar_candidato(
    alegada: CitacaoAlegada, oficial: RegistroOficial, score: float, limiar: float
) -> None:
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "numero_processo": alegada.numero_processo,
        "trecho_alegado": alegada.trecho_citado,
        "texto_oficial": oficial.texto_integral,
        "score_fidelidade": round(score, 3),
        "limiar": limiar,
        "fonte": oficial.fonte,
        "status_revisao": "pendente",
    }
    try:
        with open(CAMINHO_CANDIDATOS, "a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
    except OSError:
        # Falha ao registrar candidato nunca deve derrubar o gate em si --
        # é um mecanismo auxiliar, não parte da decisão de aceite/recusa.
        pass


def gate_fail_closed(
    alegada: CitacaoAlegada, oficial: Optional[RegistroOficial]
) -> Recibo:
    agora = datetime.now(timezone.utc).isoformat()

    if oficial is None:
        return Recibo(
            decisao=Decisao.RECUSADA,
            motivo="número de processo não encontrado em nenhuma fonte externa consultada",
            camada_exata_ok=False,
            camada_fidelidade_ok=False,
            camada_polaridade_ok=False,
            camada_numerica_ok=False,
            score_fidelidade=0.0,
            fonte_consultada="nenhuma",
            hash_registro_oficial="",
            timestamp=agora,
        )

    exata_ok, motivo_exata = camada_exata(alegada, oficial)
    fidelidade_ok, motivo_fidelidade, score = camada_fidelidade(alegada, oficial)
    polaridade_ok, motivo_polaridade = camada_polaridade(alegada, oficial)
    numerica_ok, motivo_numerica = camada_numerica(alegada, oficial)
    hash_oficial = hashlib.sha256(oficial.texto_integral.encode("utf-8")).hexdigest()

    limiar_fidelidade = 0.85  # mesmo valor default de camada_fidelidade
    if _e_candidato_a_novo_padrao({
        "exata_ok": exata_ok,
        "numerica_ok": numerica_ok,
        "polaridade_ok": polaridade_ok,
        "fidelidade_ok": fidelidade_ok,
        "score": score,
        "limiar": limiar_fidelidade,
    }):
        _registrar_candidato(alegada, oficial, score, limiar_fidelidade)

    if exata_ok and fidelidade_ok and polaridade_ok and numerica_ok:
        decisao = Decisao.ACEITA
        motivo = "identificadores, conteúdo, polaridade e valores numéricos conferem com o registro oficial"
    else:
        decisao = Decisao.RECUSADA
        checagens = (
            (exata_ok, motivo_exata),
            (fidelidade_ok, motivo_fidelidade),
            (polaridade_ok, motivo_polaridade),
            (numerica_ok, motivo_numerica),
        )
        partes = [m for ok, m in checagens if not ok]
        motivo = " | ".join(partes)

    return Recibo(
        decisao=decisao,
        motivo=motivo,
        camada_exata_ok=exata_ok,
        camada_fidelidade_ok=fidelidade_ok,
        camada_polaridade_ok=polaridade_ok,
        camada_numerica_ok=numerica_ok,
        score_fidelidade=score,
        fonte_consultada=oficial.fonte,
        hash_registro_oficial=hash_oficial,
        timestamp=agora,
    )
