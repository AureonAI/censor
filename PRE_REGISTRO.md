# PRÉ-REGISTRO — Medição de acurácia do CENSOR

Escrito e congelado **ANTES** de rodar o experimento, conforme Fase 1 do Método
STEMMA. O critério de sucesso e o falsificador estão declarados aqui; o resultado
será reportado contra este documento, seja bom ou mau.

## Pergunta central

Com que acurácia o CENSOR distingue citação fiel de citação fabricada, quando o
adversário não sou eu?

## Protocolo (corrigido após GPT-RED — 4 ataques venceram)

### Geração do conjunto

**Citações FIÉIS** — extraídas automaticamente dos inteiros teores do acervo, com
filtro de qualidade obrigatório (correção do Ataque 2):
- frase completa: inicia em maiúscula, termina em pontuação
- 60 a 200 caracteres
- sem palavra quebrada por hifenização de PDF
- contém pelo menos 6 termos de conteúdo
- NÃO é cabeçalho (sem "ADVOGADO", "RELATOR :", "ASSINADO")

**Citações FABRICADAS** — geradas por adversário externo a mim (correção do Ataque 1):
- fonte primária: o SCRIBA (alucinação real, medida nesta sessão)
- os prompts saem dos próprios acórdãos do acervo, não de temas que eu escolho
- fallback determinístico se o SCRIBA falhar: mutações mecânicas sobre as fiéis
  (inversão de polaridade, troca de valor, troca de entidade)

### Divisão obrigatória (correção do Ataque 4)

O conjunto é dividido em dois, com semente fixa e reproduzível:
- **CALIBRAÇÃO (50%)** — usado SOMENTE para escolher o limiar
- **TESTE (50%)** — usado SOMENTE para medir; nunca visto na calibração

Reportar acurácia no conjunto de calibração é proibido. O número que vale é o do
conjunto de teste, com o limiar fixado antes de olhá-lo.

### Métricas a reportar

- Verdadeiro-positivo / falso-positivo / verdadeiro-negativo / falso-negativo
- Precisão, recall, acurácia
- **Taxa de falso-positivo** (aprovar fabricada) — o erro PERIGOSO
- **Taxa de falso-negativo** (recusar fiel) — o erro que destrói credibilidade
- Intervalo de confiança de 95% (Wilson) para a acurácia
- Curva de limiar: acurácia em função do limiar, no conjunto de CALIBRAÇÃO

## Critério de sucesso (pré-registrado)

O núcleo se sustenta se, no conjunto de TESTE:
- taxa de falso-positivo ≤ 5% (quase nunca aprova fabricação), E
- taxa de falso-negativo ≤ 20% (recusa poucas fiéis), E
- limite inferior do IC 95% da acurácia ≥ 70%

## Falsificador (pré-registrado)

O núcleo **falha** se qualquer uma destas ocorrer:
- taxa de falso-positivo > 15% — significa que deixa fraude passar com frequência
  inaceitável para uso jurídico
- taxa de falso-negativo > 40% — significa que um usuário real veria quase metade
  de suas citações legítimas rejeitadas, e abandonaria a ferramenta
- não existir limiar algum que satisfaça ambos simultaneamente — significa que a
  abordagem por âncoras tem um teto e precisa de outra técnica

Se o falsificador disparar, será reportado como falha, não reenquadrado como
sucesso parcial.

## Limitação declarada de saída (correção do Ataque 3)

O acervo tem **3 decisões**, todas do STJ, todas sobre dano moral. Portanto:
- as citações geradas são **correlacionadas**, não independentes
- N citações sobre 3 acórdãos NÃO equivalem a N amostras independentes
- o IC 95% calculado é **otimista**; o intervalo real é mais largo
- nenhuma generalização para outros tribunais ou matérias é autorizada por este
  experimento

Este experimento mede se o mecanismo funciona no domínio testado. Não mede
desempenho em produção nem generalização.
