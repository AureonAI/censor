# CENSOR

**Verificador de citações jurídicas para saída de IA.** Confere cada citação de um
texto contra o inteiro teor oficial do tribunal e devolve um veredito auditável:
confirmada, fabricada ou não-comprovável — com o motivo.

Advogados já foram sancionados por citar jurisprudência que uma IA inventou. Os
geradores de texto jurídico não verificam a própria saída. O CENSOR verifica a
saída de qualquer um deles.

---

## O que ele faz

Dada uma citação (número de processo + trecho alegado), o CENSOR baixa o inteiro
teor oficial da decisão direto do tribunal e aplica quatro camadas *fail-closed*:

| Camada | Pergunta | Recusa quando |
|---|---|---|
| Exata | o processo e o relator existem? | identificadores divergem da fonte oficial |
| Fidelidade | o trecho é fiel ao acórdão? | termos de conteúdo ausentes do inteiro teor |
| Polaridade | o resultado citado é o real? | decisão foi "desprovido" e a citação diz "provido" |
| Numérica | valores e datas conferem? | valor ou data não constam do oficial |

Se qualquer camada falha, a citação é recusada **com o motivo explícito**. O sistema
não se autocertifica: ele aponta a fonte, não afirma correção.

Fonte primária, oficial e gratuita (STJ). Sem dependência de serviço pago para
verificar.

---

## Resultado medido

Avaliação com pré-registro (critério de sucesso e falsificador declarados antes de
rodar), limiar calibrado em conjunto separado do de teste:

| Métrica | Valor |
|---|---|
| Casos de teste | 104 |
| Acurácia | **99,0%** (IC 95% Wilson: 94,8% – 99,8%) |
| Falso-positivo (aprovar fabricação) | **0,0%** em 71 fraudes |
| Falso-negativo (recusar citação fiel) | 3,0% |
| Limiar | 0,80 (fixado na calibração) |

Reproduzir:

```bash
python gerar_conjunto.py   # gera o conjunto a partir do acervo
python avaliar.py          # calibra e mede, reporta contra o pré-registro
```

### Limitações declaradas

Honestidade é requisito, não cortesia. Este resultado **não** autoriza generalização:

- Casos derivados de **3 acórdãos do STJ**, mesma matéria. As amostras são
  **correlacionadas**; o intervalo de confiança acima é otimista.
- As fraudes testadas são **mecânicas** (enxerto de valor, enxerto de autoridade,
  inversão de verbo de resultado). Fraude semanticamente sofisticada — atribuir ao
  acórdão uma tese que ele rejeitou, sem inverter verbo algum — **não foi testada**.
- Apenas 5 dos 104 casos testam inversão de polaridade. A defesa mais importante
  juridicamente tem a medição mais fraca.
- O limiar 0,80 está num ponto instável: em 0,70 o falso-positivo sobe a 31%.
- Um só tribunal. STF e TST têm estrutura de acórdão diferente e não foram testados.

---

## Estágio real

**TRL 3–4.** Prova de conceito com mecanismo medido. **Nenhum terceiro externo
avaliou o sistema.** Enquanto isso não acontecer, é uma prova de conceito, não um
produto — e nenhum número aqui substitui essa validação.

---

## Como rodar

```bash
pip install pypdf
python teste_stj_hc_1094270.py   # suite do gate: 6/6 + 3/3
python teste_fraude.py           # teste de fraude do extrator
python servico_censor.py         # serviço web local em http://localhost:8000
```

O acervo de decisões não é distribuído (conteúdo de terceiro). `montar_acervo.py`
o baixa da fonte oficial.

> Nota de acesso: o portal do STJ responde a IPs residenciais brasileiros e recusa
> requisições de datacenter (403). O acervo é montado localmente, por isso.

---

## Arquitetura

- `gate.py` — núcleo das quatro camadas
- `c7.py` — extrator de citações de texto corrido (agnóstico ao gerador)
- `servico_censor.py` — serviço web sobre o núcleo
- `EVIDENCE.md` / `ADVERSARIAL_LOG.md` / `PRIMITIVE.md` — o que foi provado, os
  ataques que venceram e o que foi corrigido, e o núcleo irredutível

## Licença

MIT.
