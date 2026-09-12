# Contribuindo com o CENSOR

O CENSOR verifica citacoes juridicas contra o inteiro teor oficial. A contribuicao
mais valiosa nao e mais codigo — e **tentar quebrar o verificador**.

## Como ajudar de verdade

- **Fraude que passa.** Se voce conhece Direito, construa uma citacao falsa que o
  CENSOR aprove indevidamente. Abra uma issue com a citacao e a decisao real. Cada
  fraude que passa e um caso de teste que torna o sistema mais forte.
- **Falso-negativo.** Uma citacao legitima que o CENSOR recusa. Igualmente valiosa.
- **Outro tribunal.** O CENSOR so foi testado no STJ. STF, TST e tribunais estaduais
  tem estrutura de acordao diferente. Relatos de como a verificacao se comporta neles
  sao bem-vindos.

## Padrao

Toda mudanca de logica vem com um teste que a prova. A suite (make test) precisa
passar. Medicoes seguem o pre-registro em PRE_REGISTRO.md: criterio e falsificador
declarados antes de rodar.

## Estagio

Prova de conceito (TRL 3-4). Nenhuma validacao externa ainda. Honestidade sobre
limites e requisito, nao cortesia — veja as limitacoes declaradas no README.
