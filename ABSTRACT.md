# ABSTRACT — SCRIBA + CENSOR

## Uma frase

Um verificador que impede qualquer IA jurídica de entregar ao magistrado uma
citação que não existe, é infiel ou está invertida — conferindo cada uma contra
a fonte oficial do próprio tribunal.

## O problema real

IAs jurídicas alucinam citação. Escritórios brasileiros já foram multados pelo
STJ por citações fabricadas por IA (2026). Os geradores existentes (inclusive os
adotados por 45,8% dos tribunais) não verificam a própria saída. A fenda:
verificação de citação, agnóstica ao gerador.

## A solução, em três peças

- **CENSOR** (o produto): gate fail-closed de 4 camadas — existência, fidelidade,
  polaridade, números — contra o inteiro teor oficial. Três vereditos:
  confirmada, fabricada, não-comprovável.
- **C7** (a ponte): extrai citações de texto corrido de qualquer IA e as entrega
  ao CENSOR. Agnóstico por projeto.
- **SCRIBA** (o demonstrador): gerador soberano de texto jurídico que prova a
  integração ponta a ponta; não memoriza lei (BR4), por isso precisa do CENSOR.

## Estado honesto (dois eixos)

- Capacidade técnica: **alta**. Verifica contra fonte oficial primária, sem OCR,
  soberana; distingue fabricação de não-comprovável; barra inversão de polaridade
  em decisão real. Ninguém no mercado mapeado faz isso.
- Prontidão para mercado: **baixa/média**. Provado contra poucas decisões, um
  tribunal; sem juiz externo (fase 7 pendente); fidelidade primária ainda não
  integrada ao gate principal.

## Diferencial defensável perante o CNJ (Res. 615/2025)

Explicabilidade e supervisão humana deixam de ser promessa e viram mecanismo: o
CENSOR emite o motivo de cada veredito e opera contra a fonte oficial do próprio
Judiciário. Soberano por arquitetura, não por selo.

## Prova em 30 segundos

`python demo3.py` (elo com gate real) · `python provar_fidelidade.py` (fonte
primária) · `python red_team_scriba.py` (o gerador alucina, confirmando o CENSOR).

## Próximo passo

Endurecer a fidelidade primária contra lote multi-tribunal; integrá-la ao gate;
e pôr o conjunto no ar como serviço sem fricção, para o juiz externo (fase 7).
