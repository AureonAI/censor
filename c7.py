"""
C7 — extrator de citações jurídicas de texto corrido.

Papel no produto: recebe o texto de uma minuta gerada por QUALQUER IA jurídica
(SCRIBA, MAIA, ou um LLM genérico usado por um advogado) e extrai dela as
citações estruturadas no formato que o CENSOR consome (CitacaoAlegada), para
que cada citação passe pelas 4 camadas de verificação antes de chegar ao
magistrado.

Princípio herdado do CENSOR (fail-closed): um campo que o C7 não consegue
extrair com confiança vira None explícito — nunca um chute que se disfarça de
dado. É melhor o CENSOR saber que não tem o dado do que recebê-lo inventado.

Este é o NÚCLEO MÍNIMO (fase 3 do LIMEN). Não cobre todos os formatos de
citação do mundo — cobre o padrão brasileiro dominante e DECLARA o que não
cobre (ver limites_declarados()). Cada ampliação futura entra com seu próprio
teste de fraude, nunca antecipada sem requisito.
"""
import re
from typing import Optional, List

# Usa o CitacaoAlegada REAL do CENSOR quando o gate.py está ao lado (máquina do
# Renato, D:\CENSOR). Cai no contrato-espelho só quando roda isolado (meu
# ambiente de teste). O parser produz o MESMO objeto nos dois casos.
try:
    from gate import CitacaoAlegada  # type: ignore
except ImportError:
    from contrato_censor import CitacaoAlegada


# ---------------------------------------------------------------------------
# Padrões de reconhecimento. Cada um é uma HIPÓTESE explícita sobre como uma
# citação jurídica brasileira se apresenta em texto corrido. Documentados para
# que um terceiro entenda o que o C7 assume — e o que ele NÃO assume.
# ---------------------------------------------------------------------------

# Número de processo no padrão CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO
# (7 dígitos, 2 verificadores, ano, segmento, tribunal, origem).
# Aceita também as classes recursais comuns (REsp, HC, RE, AREsp) seguidas de
# número, porque é assim que aparecem na prosa de uma minuta.
_RE_NUM_CNJ = re.compile(
    r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b"
)
_RE_NUM_CLASSE = re.compile(
    r"\b(?:REsp|AREsp|HC|RE|AI|RHC|MS|ADI|ADPF)\s*n?[ºo\.]*\s*"
    r"[\d\.]{3,}(?:/[A-Z]{2})?\b",
    re.IGNORECASE,
)

# Relator: "Rel. Min. Fulano de Tal", "Relator: Des. Ciclano", com variações.
# O título (Min./Des./Juiz) é âncora OBRIGATÓRIA e é consumido ANTES do nome,
# fora do grupo de captura — senão o próprio título ("Min") seria capturado
# como se fosse o nome do relator (bug real pego pelo teste de fraude).
# Sem título reconhecível após "Rel.", não emitimos relator: fail-closed.
_RE_RELATOR = re.compile(
    r"\bRel(?:ator[a]?)?\.?\s*"
    r"(?:Min(?:istr[oa])?|Des(?:embargador[a]?)?|Juí?z[a]?)\.?\s+"   # título consumido
    r"([A-ZÀ-Ú][a-zà-ú]+(?:\s+(?:de|da|do|dos|das|e|[A-ZÀ-Ú][a-zà-ú]+))*)",  # nome real
)

# Tipo de decisão: só marca quando o texto DIZ. Ausência -> None (fail-closed),
# igual à filosofia do RegistroOficial do CENSOR.
_RE_TIPO = re.compile(
    r"\b(ac[óo]rd[ãa]o|decis[ãa]o\s+monocr[áa]tica|"
    r"julgamento\s+colegiado|decis[ãa]o\s+colegiada)\b",
    re.IGNORECASE,
)


def _extrair_numero(fragmento: str) -> Optional[str]:
    m = _RE_NUM_CNJ.search(fragmento)
    if m:
        return m.group(0)
    m = _RE_NUM_CLASSE.search(fragmento)
    if m:
        # normaliza espaços internos
        return re.sub(r"\s+", " ", m.group(0)).strip()
    return None


def _extrair_relator(fragmento: str) -> Optional[str]:
    m = _RE_RELATOR.search(fragmento)
    if m:
        nome = m.group(1).strip(" .,")
        # rejeita capturas degeneradas de 1 caractere ou pura pontuação
        if len(nome) >= 3:
            return nome
    return None


def _extrair_tipo(fragmento: str) -> Optional[str]:
    m = _RE_TIPO.search(fragmento)
    return m.group(1).lower() if m else None


def _extrair_trecho(fragmento: str, numero: Optional[str]) -> str:
    """
    O trecho citado é o que a IA afirma que a decisão diz. Heurística mínima:
    procura conteúdo entre aspas (a forma mais comum de citação literal). Se não
    houver aspas, devolve a sentença inteira como trecho alegado — o CENSOR fará
    a checagem de fidelidade sobre ela.
    """
    aspas = re.search(r"[\"“]([^\"”]{4,})[\"”]", fragmento)
    if aspas:
        return aspas.group(1).strip()
    return fragmento.strip()


# Abreviações jurídicas cujo ponto NÃO encerra sentença. Sem proteger isto, o
# segmentador corta "Rel. Min. Fulano" em três pedaços e o relator se separa do
# número de processo — bug real pego pelo teste de fraude.
_ABREVIACOES = [
    "Rel.", "Min.", "Des.", "Des.ª", "Dr.", "Dra.", "Exmo.", "Exma.",
    "Sr.", "Sra.", "art.", "arts.", "inc.", "n.", "nº.", "p.", "fl.", "fls.",
    "j.", "v.g.", "e.g.", "cf.", "proc.", "Ac.",
]
_SENTINELA = "\x00"  # marcador improvável no texto de entrada


def _segmentar(texto: str) -> List[str]:
    """
    Uma minuta tem várias citações. Segmenta por sentença, mas mantém junta a
    sentença que contém um número de processo com a vizinha seguinte, porque o
    relator e o veredito costumam vir na oração imediatamente após o número.

    Antes de segmentar, protege os pontos das abreviações jurídicas conhecidas
    (Rel., Min., ...) para que não sejam confundidos com fim de sentença.
    """
    protegido = texto
    for ab in _ABREVIACOES:
        protegido = protegido.replace(ab, ab.replace(".", _SENTINELA))
    brutas = re.split(r"(?<=[\.;])\s+(?=[A-ZÀ-Ú])", protegido)
    return [s.replace(_SENTINELA, ".") for s in brutas if s.strip()]


def extrair(texto: str) -> List[CitacaoAlegada]:
    """
    Extrai todas as citações candidatas do texto. Uma citação só é emitida se
    tiver, no mínimo, um número de processo identificável — sem número não há o
    que o CENSOR consultar na fonte externa (a camada exata precisa dele). Isso
    é fail-closed: preferimos NÃO emitir uma citação a emitir uma sem âncora.
    """
    citacoes: List[CitacaoAlegada] = []
    sentencas = _segmentar(texto)

    for i, s in enumerate(sentencas):
        numero = _extrair_numero(s)
        if not numero:
            continue
        # janela: a própria sentença + a seguinte (relator/veredito vêm depois)
        janela = s
        if i + 1 < len(sentencas):
            janela = s + " " + sentencas[i + 1]

        relator = _extrair_relator(janela)
        citacoes.append(
            CitacaoAlegada(
                numero_processo=numero,
                relator=relator if relator is not None else "",
                trecho_citado=_extrair_trecho(janela, numero),
                tipo_decisao=_extrair_tipo(janela),
            )
        )
    return citacoes


def limites_declarados() -> List[str]:
    """Fase 5 do LIMEN: o que esta versão NÃO resolve, por escrito, no ato."""
    return [
        "Só extrai citação ancorada em número de processo; citação a súmula "
        "ou artigo de lei sem número de processo não é capturada nesta versão.",
        "Relator por extração de superfície; nomes com formatação atípica "
        "(abreviações raras, grafia sem acento) podem escapar e virar campo vazio.",
        "tipo_decisao só é marcado quando o texto o diz explicitamente; "
        "ausência vira None, nunca inferência.",
        "Trecho citado assume aspas como marca de citação literal; citação "
        "parafraseada sem aspas é devolvida como sentença inteira.",
        "Não faz OCR: entrada é texto, não PDF/imagem (essa onda é futura, "
        "só entra com requisito real puxando).",
    ]
