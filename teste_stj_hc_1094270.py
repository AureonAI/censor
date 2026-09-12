"""
teste_stj_hc_1094270.py

Missão combinada: testar se o gate teria recusado os erros REAIS
documentados publicamente no STJ, HC nº 1094270/MG (rel. Min. Rogerio
Schietti Cruz, decisão de 18/05/2026), noticiado pela Gran Cursos
Online e replicado por outras fontes jurídicas.

IMPORTANTE -- limite de honestidade, declarado antes do código:
Não temos acesso, neste ambiente, ao texto integral do acórdão real
nem à API de nenhum tribunal (rede sandboxed, sem acesso a domínios
.jus.br). Os "RegistroOficial" abaixo são FICTÍCIOS, construídos para
espelhar a TAXONOMIA DE ERRO relatada pela imprensa jurídica sobre o
caso real -- não são o conteúdo real do HC 1094270/MG. Isto testa a
FORMA do erro (o padrão que os tribunais já flagraram), não reproduz o
caso concreto. Por isso o status desta missão é TESTÁVEL-NÃO-TESTADO,
não TESTADO: falta ainda conectar a uma fonte externa real (DataJud,
jurisprudencias.ai) fora deste sandbox para virar TESTADO de fato.

Os três padrões de erro documentados no caso real:
  1. Relator errado (IA atribuiu a ministro que não julgou o caso)
  2. Tipo de decisão errado (IA disse "colegiada" quando era monocrática)
  3. Identificadores corretos, mas conteúdo/trecho citado INVENTADO
     mesmo com o nome do relator certo
"""

from gate import CitacaoAlegada, RegistroOficial, gate_fail_closed, Decisao

SEPARADOR = "-" * 78


def relatar(titulo: str, alegada: CitacaoAlegada, oficial):
    recibo = gate_fail_closed(alegada, oficial)
    print(SEPARADOR)
    print(f"CASO: {titulo}")
    print(f"  decisão do gate ......... {recibo.decisao.value.upper()}")
    print(f"  motivo ................... {recibo.motivo}")
    print(f"  camada exata ok? ......... {recibo.camada_exata_ok}")
    print(f"  camada fidelidade ok? .... {recibo.camada_fidelidade_ok} (score {recibo.score_fidelidade:.2f})")
    print(f"  camada polaridade ok? .... {recibo.camada_polaridade_ok}")
    print(f"  camada numérica ok? ...... {recibo.camada_numerica_ok}")
    print(f"  fonte consultada ......... {recibo.fonte_consultada}")
    esperado_recusa = not titulo.startswith("controle")
    passou = (recibo.decisao == Decisao.RECUSADA) == esperado_recusa
    print(f"  === {'PASSOU' if passou else 'FALHOU'} NO TESTE ===")
    return passou


# --- registro oficial fictício, usado como "fonte que não controlamos" ---
registro_real = RegistroOficial(
    numero_processo="HC-FICT-000001",
    relator="Min. Fictício da Silva",
    tipo_decisao="monocratica",
    texto_integral=(
        "O relator indeferiu o pedido de liminar por ausência dos requisitos "
        "do art. 312 do CPP, mantendo a prisão preventiva em razão do risco "
        "de reiteração delitiva evidenciado nos autos."
    ),
    fonte="fixture sintética (padrão de erro do HC 1094270/MG, não o texto real)",
)

resultados = []

# Padrão de erro real 1: relator errado
resultados.append(relatar(
    "padrão 1 (relator errado)",
    CitacaoAlegada(
        numero_processo="HC-FICT-000001",
        relator="Min. Outro Nome",  # IA atribuiu a quem não julgou
        tipo_decisao="monocratica",
        trecho_citado="O relator indeferiu o pedido de liminar por ausência dos requisitos do art. 312 do CPP",
    ),
    registro_real,
))

# Padrão de erro real 2: tipo de decisão errado
resultados.append(relatar(
    "padrão 2 (tipo de decisão errado)",
    CitacaoAlegada(
        numero_processo="HC-FICT-000001",
        relator="Min. Fictício da Silva",
        tipo_decisao="colegiada",  # IA disse colegiada, era monocrática
        trecho_citado="O relator indeferiu o pedido de liminar por ausência dos requisitos do art. 312 do CPP",
    ),
    registro_real,
))

# Padrão de erro real 3: identificadores corretos, conteúdo inventado
resultados.append(relatar(
    "padrão 3 (identificadores corretos, trecho inventado)",
    CitacaoAlegada(
        numero_processo="HC-FICT-000001",
        relator="Min. Fictício da Silva",
        tipo_decisao="monocratica",
        trecho_citado="O relator concedeu a liminar reconhecendo excesso de prazo na formação da culpa",
    ),
    registro_real,
))

# Padrão de erro real (implícito): processo que nem existe
resultados.append(relatar(
    "padrão 4 (número de processo inexistente)",
    CitacaoAlegada(
        numero_processo="HC-INEXISTENTE-999",
        relator="Min. Fictício da Silva",
        tipo_decisao="monocratica",
        trecho_citado="qualquer trecho",
    ),
    None,
))

# Controle: citação legítima, deve ser ACEITA
resultados.append(relatar(
    "controle (citação legítima)",
    CitacaoAlegada(
        numero_processo="HC-FICT-000001",
        relator="Min. Fictício da Silva",
        tipo_decisao="monocratica",
        trecho_citado="ausência dos requisitos do art. 312 do CPP",
    ),
    registro_real,
))

# Ataque Red Team (rodado à parte na sessão anterior, agora formalizado
# aqui como teste permanente): inverte um único veredito -- indeferiu vira
# deferiu -- mantendo o resto da frase quase idêntico. Foi este ataque que
# expôs, na primeira versão do gate (2 camadas), que semelhança de texto
# não é o mesmo que semelhança de sentido.
resultados.append(relatar(
    "ataque red team (polaridade invertida, texto quase idêntico)",
    CitacaoAlegada(
        numero_processo="HC-FICT-000001",
        relator="Min. Fictício da Silva",
        tipo_decisao="monocratica",
        trecho_citado="O relator deferiu o pedido de liminar por ausência dos requisitos do art. 312 do CPP",
    ),
    registro_real,
))

print(SEPARADOR)
total = len(resultados)
passou = sum(resultados)
print(f"RESULTADO FINAL (camadas 1-3): {passou}/{total} casos se comportaram como esperado")
print(SEPARADOR)


# --- segunda leva: ataques à camada 4 (numérica), com registro oficial ---
# --- que carrega valor monetário real, para poder testar magnitude   ---
print()
print("=" * 78)
print("SEGUNDA LEVA -- ataques de fabricação numérica (camada 4)")
print("=" * 78)

registro_com_multa = RegistroOficial(
    numero_processo="HC-FICT-000002",
    relator="Min. Fictício da Silva",
    tipo_decisao="monocratica",
    texto_integral=(
        "O relator aplicou multa de R$ 5.000,00 por litigância de má-fé, "
        "mantendo os demais termos da decisão de 10/03/2026."
    ),
    fonte="fixture sintética (padrão do ataque de magnitude descoberto nesta sessão)",
)

resultados2 = []

# Ataque red team já conhecido, agora formalizado: valor 10x maior
resultados2.append(relatar(
    "ataque numérico (multa 10x maior, mesmo texto ao redor)",
    CitacaoAlegada(
        numero_processo="HC-FICT-000002",
        relator="Min. Fictício da Silva",
        tipo_decisao="monocratica",
        trecho_citado="O relator aplicou multa de R$ 50.000,00 por litigância de má-fé",
    ),
    registro_com_multa,
))

# Controle: valor correto, deve ser aceito
resultados2.append(relatar(
    "controle numérico (valor correto)",
    CitacaoAlegada(
        numero_processo="HC-FICT-000002",
        relator="Min. Fictício da Silva",
        tipo_decisao="monocratica",
        trecho_citado="O relator aplicou multa de R$ 5.000,00 por litigância de má-fé",
    ),
    registro_com_multa,
))

# Novo ataque, ainda não tentado: data trocada em vez de valor
resultados2.append(relatar(
    "ataque numérico (data trocada)",
    CitacaoAlegada(
        numero_processo="HC-FICT-000002",
        relator="Min. Fictício da Silva",
        tipo_decisao="monocratica",
        trecho_citado="mantendo os demais termos da decisão de 22/08/2026",
    ),
    registro_com_multa,
))

print(SEPARADOR)
total2 = len(resultados2)
passou2 = sum(resultados2)
print(f"RESULTADO FINAL (camada 4): {passou2}/{total2} casos se comportaram como esperado")
print(SEPARADOR)
