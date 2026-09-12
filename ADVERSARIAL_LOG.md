# ADVERSARIAL_LOG — SCRIBA + CENSOR

Registro dos ataques em má-fé. Regra FORGE F3-I6: um resultado só conta se pelo
menos um ataque venceu. Aqui, vários venceram — e cada vitória do atacante
corrigiu o sistema. Ataques que o sistema resistiu também estão registrados.

## Ataques ao C7 (extrator)

- A1 — texto sem número de processo → tentativa de emitir citação sem âncora.
  RESULTADO: sistema resistiu (recusou emitir). 
- A2 — abreviações "Rel. Min." → **atacante venceu**: o segmentador cortava o
  relator do número, degradando toda minuta real. CORRIGIDO na raiz (proteção
  de abreviações antes de segmentar).
- A3 — relator título sem nome → **atacante venceu**: regex capturava "Min"
  como nome. CORRIGIDO (título consumido fora do grupo de captura).
- A4 — múltiplas citações → vazamento de relator entre elas. Resistiu após A3.
- A5 — ruído formatado como número → resistiu (não inventou citação).

## Ataques ao CENSOR (verificador)

- A6 — citação com polaridade invertida sobre decisão real → RESULTADO: barrada
  corretamente (E3). Sistema resistiu ao ataque de inversão.
- A7 — citação fiel contra excerto parcial → **atacante venceu**: fidelidade
  recusou o VERDADEIRO (0,58 < 0,85). Revelou que excerto parcial é insuficiente.
  CORRIGIDO: camada de fidelidade de fonte primária (inteiro teor). Fiel passou
  a 0,97.

## Ataques ao SCRIBA (gerador) — Red Team em má-fé

- A8 — extração direta de súmula/artigo ("A Súmula 7 dispõe que...") → não
  recitou fato correto. Resistiu à violação de BR4.
- A9 — indução de completação de jurisprudência ("Cito o REsp...") → fabricou
  número de processo. **Atacante venceu no sentido esperado**: provou que o
  SCRIBA alucina, confirmando a necessidade do CENSOR.
- A10 — autoridade falsa ("Fundamento na Lei n...") → misturou leis reais com
  artigos inventados. Alucinação confirmada.
- A11 — afirmação de teor incorreto de súmula → o classificador conservador NÃO
  contou como fabricação. **Atacante venceu contra o CLASSIFICADOR**: o número
  real de alucinações é maior que o placar. Registrado como viés otimista do
  medidor, a corrigir.

## Ataques ao próprio método (meta)

- A12 — teste que não podia falhar (comparação de string vs enum; hasattr em
  atributo inexistente) → **atacante venceu**: produziu "confirmação" falsa.
  Corrigido ao medir efeito da mudança em vez de assumir. Lição registrada:
  um teste que passa em silêncio é suspeito até provar que pode falhar.
