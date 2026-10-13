# Cross-check: Leiloeiro Freitas

> Feature: `004-leiloeiro-freitas`
> Data: 2026-10-13
> Artefatos: [`requirements.md`](../requirements.md), [`roadmap.md`](../roadmap.md), [`actions.md`](../actions.md) (mais `data-delta.md`, `interfaces/freitas.md`, `runbook-certificado.md`, `onboarding.md`)
> Auditoria leitora: nenhum artefato foi alterado.

## Resumo

| Severidade | Quantidade |
|------------|------------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 3 |
| LOW | 4 |

## Findings

| ID | Severidade | Eixo | Descrição | Onde está |
|----|------------|------|-----------|-----------|
| A001 | MEDIUM | Consistência | Formato do pátio diverge: o critério do RF-04 espera **"Santo André - SP"**; o contrato e o T007 esperam **"SANTO ANDRE - SP"** (maiúsculas e sem acento, como o site escreve em "Visitação/Retirada"). Um teste escrito por um dos dois falha contra o outro | `requirements.md` RF-04 × `interfaces/freitas.md` §3, `actions.md` T007 |
| A002 | MEDIUM | Cobertura / Consistência | O D-77 (lotes "EM LOTEAMENTO" não são devolvidos) não tem regra no requirements, e contradiz a letra do RF-03 ("converter **cada** card") e o número do critério do RF-02 ("225 lotes"): com o D-77, a coleta lê 225 cards, mas o parser devolve 204 (225 − 21 em loteamento, dados de 2026-10-13) | `roadmap.md` D-77 × `requirements.md` RF-02, RF-03 |
| A003 | MEDIUM | Cobertura (rastreabilidade) | RF-06 (busca vazia e quebra) e RF-09 (menos de 10 minutos) não são citados pelo identificador no roadmap. Estão cobertos em conteúdo (D-74 e contrato §4; critério de pronto §10 e risco) e as ações os citam (T007, T017) | `roadmap.md` §3 |
| A004 | LOW | Consistência | O alerta de **falha de certificado** (D-84, D-85) e o runbook vão além do RF-08, que só diz "bloqueio gera alerta"; o requirements não registra essa regra nem o runbook | `requirements.md` RF-08 × `roadmap.md` D-85 |
| A005 | LOW | Consistência | A seção "Lacunas" do requirements ainda lista como abertas perguntas que o plano respondeu: pátio e despesas por leilão (variam: Santa Bárbara d'Oeste-SP × Santo André-SP; logística de R$ 350 no 8111), valores da etiqueta (só FINANCEIRA ou vazia), data no card (uma só) e troca de certificado (runbook) | `requirements.md` §10 |
| A006 | LOW | Consistência (termos) | "Despesas **operacionais**" (requirements RF-04, data-delta) e o campo/rótulo existente "Despesas **admin.**" (relatório e lista) nomeiam a mesma coisa; no Freitas a linha somará operacionais e logística | `requirements.md` RF-04 × saída existente (E002 da 003) |
| A007 | LOW | Consistência | Texto do sintoma na seção "Leiloeiros" do relatório: o runbook e o contrato dizem `falha de acesso (certificado: <host>)` (formato atual do código); o T014 diz que a seção "mostra 'falha de certificado'" | `runbook-certificado.md` §1 × `actions.md` T014 |

## Impacto e direção

Não há CRITICAL nem HIGH. Os três MEDIUM são de redação entre documentos e não mudam o desenho técnico. Direção sugerida (correção humana ou por `/reversa-clarify`; esta auditoria não altera nada):

- **A001:** escolher um formato para o pátio do Freitas. O desenho atual (como o site escreve, igual à Copart: "CAMPO GRANDE - MS") deixa os três leiloeiros uniformes; ajustar o critério do RF-04.
- **A002:** registrar no requirements a regra dos lotes em loteamento (decisão do D-77) e ajustar o critério do RF-02 para "225 cards lidos; os em loteamento contados no log".
- **A003:** citar RF-06 e RF-09 nas decisões correspondentes.
- **A004 a A007:** atualizar o requirements (RF-08 com o alerta de certificado e o runbook; lacunas respondidas; termo de despesas) e alinhar o T014 ao texto do runbook.

## Itens verificados que passaram

**Cobertura**
- RF-01 a RF-05, RF-07 e RF-08 citados em decisões do roadmap; RF-01 a RF-09 citados nas ações.
- As 12 decisões (D-74 a D-85) existem e todas são citadas por ação (diretamente ou em intervalos).
- Os 5 cenários Gherkin estão em T009; o cenário do certificado é verificado por teste de unidade (T005), já que o ponta a ponta usa transporte simulado — explícito no T009.

**Consistência**
- Nenhuma ação, nem o contrato, o data-delta ou o roteiro de teste citam decisão inexistente; "RF-12" e "RF-13" no roadmap são das specs (`coletor-lotes.md`).
- O contrato `interfaces/freitas.md` aparece no roadmap (§7) e bate com D-74 a D-85 (endpoint, `TopRows=200`, mensagem de fim, campos do card, etiqueta, loteamento, detalhe, certificado).
- Impressão digital e validade do intermediário iguais no contrato, no runbook e no LEIA-ME das amostras.

**Coerência com o legado** (âncora greenfield: specs + adendos)
- Lote descartado pelo parser (loteamento) tem precedente no Kuss (sucata pela marca, D-43), com contagem no log.
- Intermediário no repositório de confiança não afrouxa a verificação; nenhuma regra anterior trata de certificados.
- Tipo de leilão por lote não contradiz o D-15 (Vip) nem o D-39 (Kuss): cada leiloeiro tem a sua fonte; o motor só lê `tipo_leilao`.
- Enriquecimento, semeados nos documentos, formato numerado da lista, pátio e alerta por leiloeiro: reaproveitados sem mudança.

**Sanidade do actions**
- 20 ações; nenhuma dependência para ID inexistente; nenhum ciclo; maior cadeia = 8 (confere com o resumo corrigido).
- Nenhum par de ações `[//]` compartilha arquivo alvo; 16 paralelizáveis (confere).
