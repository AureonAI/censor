# EVIDENCE — SCRIBA + CENSOR

Registro do que foi **provado**, com número e fonte. Nada aqui é afirmado sem
medição reproduzível. Onde a prova é parcial, está declarado como parcial.

## O que o conjunto faz

Um gerador de texto jurídico (SCRIBA) que redige no estilo de peça judicial sem
memorizar fato jurídico, acoplado por um extrator (C7) a um verificador fail-closed
(CENSOR) que confere cada citação contra a fonte oficial antes de ela chegar ao
magistrado.

## Evidências medidas

### E1 — SCRIBA não memoriza lei/jurisprudência (fronteira BR4)
- Método: Red Team em má-fé, 6 vetores de ataque (extração direta, indução por
  completação, autoridade falsa, indução de valor).
- Resultado: **0 recitações** de fato jurídico correto em 6 ataques.
- Consequência: a classificação de baixo risco (BR4, CNJ 615/2025) tem lastro
  empírico — o modelo não reproduz lei/súmula de memória.
- Commit: 78d047b.

### E2 — SCRIBA alucina citação quando sozinho
- Mesmo Red Team: **≥2 fabricações** de fato específico (ex.: "salário mínimo
  fixado em 1/4 do salário mínimo internacional"; "REsp 361.437" fabricado).
- Nota de honestidade: o classificador é conservador; o número real de
  alucinações é provavelmente maior (afirmou teor incorreto de súmula que não
  foi contado como fabricação por não bater âncora).
- Consequência: prova empírica da NECESSIDADE do CENSOR. O SCRIBA sozinho não é
  seguro para uso; o par é a unidade mínima viável.

### E3 — CENSOR barra inversão de polaridade em decisão real
- Método: teste vivo contra jurisprudencias.ai; citação fiel vs adulterada
  (veredito invertido) sobre decisão real do STJ.
- Resultado: fiel ACEITA; adulterada RECUSADA com motivo correto ("registro
  oficial usa 'desprovido', peça alegada usa 'provido'").
- Commit: 6a7240c.

### E4 — Fidelidade de fonte primária (inteiro teor oficial do STJ)
- Método: download do inteiro teor oficial (PDF-texto, 9 páginas, 22.464 chars,
  sem OCR) e verificação de trecho fiel vs fabricado contra o acórdão completo.
- Resultado: fiel CONFIRMADA (sim=0,974); fabricado FABRICADA (sim=0,519).
  Separação de 0,45 com limiar em 0,80 no meio do vão.
- Consequência: fecha o furo do excerto parcial (que dava só 0,58 para o fiel).
  Fonte primária, oficial, gratuita, soberana.
- Commit: a04e57e.

### E5 — Elo ponta a ponta com gate real
- Texto → C7 extrai citação → CENSOR verifica. Aceita o fiel, barra o falso,
  com o gate.py real (não espelho). Commit: d518aed.

## O que NÃO está provado (limites honestos)

- L1 — Tudo acima foi provado contra **poucas decisões** (E3/E4: uma decisão;
  E1/E2: seis ataques). Não há validação em lote nem multi-tribunal (STF, TST
  têm formato distinto).
- L2 — **Nenhum terceiro externo** rodou o conjunto (fase 7 do LIMEN pendente).
  Até isso, é "funciona na nossa máquina", não "produto validado".
- L3 — A camada de fidelidade primária ainda é módulo à parte, não integrada ao
  gate.py como fidelidade padrão.
- L4 — Cobertura de polaridade é lista fechada de antônimos; inversão fora do
  léxico escapa.
- L5 — SCRIBA v1 é backbone 0,5B; qualidade de minuta profissional sustentada
  não foi avaliada por jurista.
