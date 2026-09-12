"""
Teste de fraude do C7 — fase 3 do LIMEN.

A regra: o primeiro código não é uma feature, é um ataque que tenta enganar o
sistema. Aprovar o caso legítimo não conta. O que conta é: quando o texto tenta
induzir o parser a INVENTAR um dado, ele se recusa (campo vazio/None) em vez de
entregar um chute disfarçado de fato ao CENSOR.

Cada teste declara o ATAQUE e o comportamento SEGURO esperado.
Rode:  python teste_fraude.py
"""
from c7 import extrair, limites_declarados
from contrato_censor import CitacaoAlegada

RESET = "\033[0m"; VERDE = "\033[92m"; VERM = "\033[91m"; AMAR = "\033[93m"


def ok(cond, msg):
    print((VERDE + "  PASS " + RESET if cond else VERM + "  FAIL " + RESET) + msg)
    return cond


falhas = 0


def bloco(titulo):
    print("\n" + AMAR + titulo + RESET)


# ---------------------------------------------------------------------------
bloco("CONTROLE — citação legítima e completa deve ser extraída inteira")
texto = ('Conforme o REsp 1.234.567/SP, Rel. Min. Nancy Andrighi, o acórdão '
         'assentou que "o dano moral prescinde de prova do prejuízo".')
c = extrair(texto)
falhas += not ok(len(c) == 1, f"extraiu exatamente 1 citação (extraiu {len(c)})")
if c:
    falhas += not ok("1.234.567/SP" in c[0].numero_processo, "número correto")
    falhas += not ok("Nancy" in c[0].relator, f"relator capturado: {c[0].relator!r}")
    falhas += not ok(c[0].tipo_decisao == "acórdão", f"tipo: {c[0].tipo_decisao!r}")

# ---------------------------------------------------------------------------
bloco("FRAUDE 1 — texto SEM número de processo não pode virar citação")
# Ataque: prosa jurídica que soa como citação mas não tem âncora consultável.
# Se o C7 emitir uma CitacaoAlegada aqui, ele entrega ao CENSOR algo que a
# camada exata não tem como verificar — falha perigosa.
texto = ('A jurisprudência pacífica do Superior Tribunal, conforme entendimento '
         'do Relator, firmou que o prazo é decadencial e não prescricional.')
c = extrair(texto)
falhas += not ok(len(c) == 0,
                 f"recusou emitir citação sem número (emitiu {len(c)})")

# ---------------------------------------------------------------------------
bloco("FRAUDE 2 — relator ausente vira campo VAZIO, não invenção")
# Ataque: número real, mas nenhum relator no texto. O parser não pode 'chutar'
# um nome plausível. Campo vazio é a resposta honesta.
texto = 'Vide o HC 123.456/RJ, no qual se discutiu a nulidade da prova.'
c = extrair(texto)
falhas += not ok(len(c) == 1, f"extraiu a citação com número (extraiu {len(c)})")
if c:
    falhas += not ok(c[0].relator == "",
                     f"relator vazio (honesto), veio: {c[0].relator!r}")

# ---------------------------------------------------------------------------
bloco("FRAUDE 3 — tipo_decisao não declarado vira None, não inferência")
# Ataque: número + relator, mas o texto NÃO diz se é acórdão ou monocrática.
# Inferir seria fingir que checou. Espelha a filosofia do RegistroOficial.
texto = 'O AREsp 987.654/MG, Rel. Min. Fulano de Tal, tratou da matéria.'
c = extrair(texto)
if ok(len(c) == 1, f"extraiu 1 (extraiu {len(c)})"):
    falhas += not ok(c[0].tipo_decisao is None,
                     f"tipo None (não inferido), veio: {c[0].tipo_decisao!r}")
else:
    falhas += 1

# ---------------------------------------------------------------------------
bloco("FRAUDE 4 — múltiplas citações na mesma minuta, sem vazamento entre elas")
# Ataque: duas citações próximas. O relator de uma não pode 'vazar' para a
# outra. Cada citação carrega só o que é dela.
texto = ('Primeiro, o REsp 111.111/SP, Rel. Min. Alfa, negou provimento. '
         'Depois, o REsp 222.222/RJ, Rel. Min. Beta, deu provimento ao pleito.')
c = extrair(texto)
falhas += not ok(len(c) == 2, f"extraiu 2 citações distintas (extraiu {len(c)})")
if len(c) == 2:
    r0 = c[0].relator + " | " + c[1].relator
    falhas += not ok("Alfa" in c[0].relator and "Beta" in c[1].relator,
                     f"relatores não vazaram entre citações: {r0!r}")

# ---------------------------------------------------------------------------
bloco("FRAUDE 5 — número formatado de modo estranho não é 'consertado' às cegas")
# Ataque: algo que PARECE número mas está quebrado. O parser não deve remendar
# para parecer válido; ou reconhece o padrão real, ou não emite.
texto = 'Ref.: processo 12-34 do gabinete, sem relator informado.'
c = extrair(texto)
falhas += not ok(len(c) == 0,
                 f"não inventou citação a partir de ruído (emitiu {len(c)})")

# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if falhas == 0:
    print(VERDE + f"RESULTADO: núcleo do C7 resistiu a todos os ataques." + RESET)
else:
    print(VERM + f"RESULTADO: {falhas} falha(s) — núcleo NÃO está pronto." + RESET)
print("=" * 60)

print("\nLimites declarados desta versão (fase 5 do LIMEN):")
for lim in limites_declarados():
    print("  - " + lim)
