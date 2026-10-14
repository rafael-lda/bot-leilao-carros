# Cross-check: Leiloeiro Milan (e o nível Apify)

> Feature: `005-leiloeiro-milan`
> Data: 2026-10-14 (segunda auditoria, depois do esclarecimento pós-audit de 2026-10-13)
> Artefatos: [`requirements.md`](../requirements.md), [`roadmap.md`](../roadmap.md), [`actions.md`](../actions.md) (mais `data-delta.md`, `interfaces/apify.md`, `interfaces/milan.md`, `investigation.md`, `onboarding.md`, `amostras/`)
> Auditoria leitora: nenhum artefato foi alterado.

## Resumo

| Severidade | Quantidade |
|------------|------------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 3 |

Da primeira auditoria (A001 a A009 de 2026-10-13), todos os achados foram resolvidos no esclarecimento, exceto o RF-10 sem decisão própria, que segue aqui como A004. Os IDs abaixo são desta auditoria.

## Findings

| ID | Severidade | Eixo | Descrição | Onde está |
|----|------------|------|-----------|-----------|
| A001 | MEDIUM | Consistência | O RF-02 exige o token "quando algum leiloeiro **ativo** usa `apify`", mas o RF-11 (e o RN-09) dizem que, com `--sem-pagos`, o token **não é exigido**, e o roadmap (D-90) também dispensa o token quando o único pago foi pulado pelo intervalo (RF-12). As ações seguem o roadmap (T007 `exigir_apify`, T016, T033), então um teste escrito pela letra do RF-02 falharia contra o RF-11 | `requirements.md` RF-02 × RF-11, RN-09 × `roadmap.md` D-90 × `actions.md` T007, T016, T033 |
| A002 | LOW | Consistência | Restos da troca automática, que agora é Won't (RN-05, RF-07): o RN-06 ainda diz "só para leiloeiros em `apify` (ou na troca automática)", e a persona "dono do orçamento" ainda diz "e para outro leiloeiro só se ele passar a bloquear" | `requirements.md` RN-06, §3 × RN-05, RF-07 |
| A003 | LOW | Consistência | O resumo executivo (§1) ainda fala em "247 lotes" e em "a página do leilão traz o lance atual"; o RF-04 usa 254 cards e 243 veículos, e o RN-03 tira o lance da página de cada lote. A frase sobre a página do leilão é verdadeira como descrição do site, mas lida sozinha sugere o desenho antigo | `requirements.md` §1 × RN-03, RF-04 |
| A004 | LOW | Cobertura (rastreabilidade) | O RF-10 (menos de 10 minutos com os 5 leiloeiros) continua sem decisão no roadmap; aparece só no critério de pronto (§10) e no T039 (dry-run real). Mesmo tratamento da 004 (A003 de lá) | `roadmap.md` §10 × `actions.md` T039 |

## Impacto e direção

Não há CRITICAL nem HIGH. Direção sugerida (correção humana ou por `/reversa-clarify`; esta auditoria não altera nada):

- **A001:** reescrever o RF-02 como "quando a varredura **inclui** leiloeiro em `apify`", com o critério cobrindo `--sem-pagos` e o intervalo.
- **A002 e A003:** retirar a menção à troca automática do RN-06 e da persona; atualizar o resumo (§1) com os números e a origem do lance de 2026-10-13.
- **A004:** opcional; o critério de pronto e o T039 já cobrem a medição.

## Itens verificados que passaram

**Cobertura**
- RF-01 a RF-14 citados no roadmap e nas ações (RF-07 como Won't, com a D-92 e o T043 registrando no backlog).
- RN-09 a RN-13 (novos) citados nas decisões D-100, D-101, D-102, D-98 e D-91, e cobertos pelas ações T011, T014, T016, T017, T028, T030, T033 a T037.
- As 18 decisões (D-86 a D-103) têm ação, diretamente ou em intervalo.
- Cenários 1 a 4 cobertos pelo T015; cenário 5 novo (varredura sem pagos) coberto pelo T016; o critério de pronto do roadmap cita os cenários 1 a 5.
- Critério do RF-05 (Creta 046) e do RF-14 (Creta com lance acima do teto) presentes no T009 e no T015; os valores do RF-05 batem com a amostra `apify_lote-15618-046_creta-sem-lance.json` e com o catálogo (km 99.020, automático, IPVA 2026 PAGO, Banco Honda).
- Critério do RF-04 (254 cards, 243 veículos, 11 materiais) bate com o censo do `investigation.md` e com o T009.

**Consistência**
- Nenhum identificador fantasma: os RF-11 a RF-14 citados no roadmap e nas ações existem no requirements; "RF-03", "RF-12", "NG-03", "EC-08" e "OQ-03" com prefixo de spec são de `coletor-lotes.md`.
- O RN-03 e o cenário 1 agora dizem o mesmo que a D-97 (lance pela página do lote, só dos candidatos).
- Limite do alerta de gasto igual nos três documentos: 80% (RN-13, RF-09, D-91, T017, T035).
- Textos das linhas da seção "Leiloeiros" iguais no requirements (RN-09, RN-10), no roadmap (D-100, D-101) e nas ações (T016, T033).
- Os dois contratos (`interfaces/apify.md`, `interfaces/milan.md`) aparecem no roadmap (§7).

**Coerência com o legado** (âncora greenfield: specs + adendos; não há `domain.md` nem `architecture.md`)
- As specs com a regra antiga sobre CAPTCHA (`coletor-lotes.md` NG-03 e decisão sobre termos de uso; `onboarding-leiloeiro-assistido.md` NG-02, EC-02) estão no delta do roadmap (§5), marcadas para correção no `/reversa-sync`.
- OQ-03 da spec do coletor respondida (RN-13, confirmada pelo Rafael).
- RF-07 como Won't coincide com a decisão 🟡 da spec do coletor (nível declarado por leiloeiro, sem troca em tempo de execução).
- Enriquecimento, semeadura, lista numerada, pátio e alertas por leiloeiro reaproveitados sem contradição com os adendos 002 a 004.

**Sanidade do actions**
- 43 ações; todas as dependências apontam para IDs existentes; nenhum ciclo; maior cadeia = 11 (confere com o resumo).
- Nenhum par de ações `[//]` compartilha arquivo alvo; 28 paralelizáveis (confere).
