# Cross-check: Skill `analisar-lotes` (triagem e custo na garagem)

> Feature: `006-analisar-lotes`
> Data: 2026-10-15
> Artefatos: [`requirements.md`](../requirements.md), [`roadmap.md`](../roadmap.md), [`actions.md`](../actions.md) (mais `data-delta.md`, `interfaces/cli-analise.md`, `interfaces/fipe.md`, `interfaces/distancias.md`, `investigation.md`, `onboarding.md`)
> Auditoria leitora: nenhum artefato foi alterado.

## Resumo

| Severidade | Quantidade |
|------------|------------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2 |
| LOW | 5 |

## Findings

| ID | Severidade | Eixo | Descrição | Onde está |
|----|------------|------|-----------|-----------|
| A001 | MEDIUM | Cobertura (rastreabilidade) | O RF-02 (triagem, Must, o coração da feature) e a RN-03 (lista de critérios) não são citados por identificador no roadmap nem nas ações. A cobertura existe em conteúdo (D-104 e D-105: o roteiro julga; D-107: critérios do YAML; T023 e T024), mas a lista completa da RN-03 não aparece em ação nenhuma: origem financiamento, km acima do máximo, versão fora da preferência, lote encerrado ou retirado, lance atual acima do teto e documento. O T023 fala só em "critérios do YAML e do texto `triagem`", e vários desses critérios vêm de campos que já existem no alvo (`tipos_leilao`, `quilometragem_maxima`, `preco_maximo`), não dos campos novos | `requirements.md` RF-02, RN-03 × `roadmap.md` §3.1 a §3.2 × `actions.md` T023, T024 |
| A002 | MEDIUM | Cobertura | A RN-08 permite que a skill some reparos além da reserva quando as observações citam avaria, "dizendo quanto e por quê". O contrato do `analise custo` (`interfaces/cli-analise.md`) e o D-116 não têm entrada para esse acréscimo, e nenhuma ação o cobre: o agente teria de fazer a conta à mão, contra a regra de não calcular de cabeça | `requirements.md` RN-08 × `roadmap.md` D-116 × `interfaces/cli-analise.md` × `actions.md` T007, T016, T022 |
| A003 | LOW | Cobertura (rastreabilidade) | O D-111 (ordem da evidência; Copart sem câmbio fica "a confirmar"; fotos fora desta versão) não é citado por ação; o conteúdo aparece no T023 ("ordem da evidência") | `roadmap.md` D-111 × `actions.md` T023 |
| A004 | LOW | Cobertura | O critério do RF-07 pede que o resumo da skill diga quantas páginas pagas foram lidas ("1 página paga (~US$ 0,08)"); o `analise pagina` devolve `pago` e o custo (T010, T019), mas o roteiro (T023) não cita o total no resumo | `requirements.md` RF-07 × `actions.md` T023 |
| A005 | LOW | Consistência | A RN-01 aceita um lote "por número ou link"; a linha de comando aceita só o número (`analise pagina <numero>`, `lotes --numero`). O agente pode achar o número pelo link com `analise lotes`, mas o contrato não diz | `requirements.md` RN-01 × `interfaces/cli-analise.md` |
| A006 | LOW | Sanidade do actions | O T029 (execução real) depende do OK do Rafael no meio da ação, o que foge do critério de ação atômica; é intencional (RN-05, critério de pronto) e está escrito na própria ação | `actions.md` T029 |
| A007 | LOW | Coerência com o legado | O `.gitignore` consta em `.reversa/state.json` como arquivo criado pelo instalador do Reversa; uma reinstalação (`npx reversa install`) pode recolocar `.claude/skills/` inteiro. A skill, já versionada, continua rastreada, mas arquivos novos dela passariam a ser ignorados | `roadmap.md` D-106 × `.reversa/state.json` (`created_files`) |

## Impacto e direção

Não há CRITICAL nem HIGH. Direção sugerida (edição manual ou `/reversa-clarify`; esta auditoria não altera nada):

- **A001:** citar RF-02 e RN-03 na D-104 ou D-105 e listar os critérios da RN-03 no T023 (o roteiro), lembrando quais vêm de campos já existentes do alvo; acrescentar às avaliações do T024 um caso de km acima do máximo e um de lance acima do teto.
- **A002:** dar ao `analise custo` uma entrada `--reparos-extra <valor> --motivo-reparos "<texto>"` (D-116, contrato, T007, T016, T022), ou retirar essa possibilidade da RN-08.
- **A003 a A007:** citar o D-111 no T023; incluir no roteiro o total de páginas pagas no resumo; aceitar link no `analise pagina` ou registrar que o agente converte link em número; manter a nota do T029; registrar no `regression-watch` a verificação do `.gitignore` depois de reinstalar o Reversa.

## Itens verificados que passaram

**Cobertura**
- RF-01, RF-03 a RF-11 citados no roadmap e nas ações.
- As 14 decisões (D-104 a D-117) têm ação, exceto o D-111 por identificador (A003).
- Cenários: 1 a 3 (Fluence manual, sinistrado, falta de informação) nas avaliações do T024; 4 (FIPE ambígua) no T008 e no T024; 5 (varredura em andamento) no T011.
- Os três contratos (`cli-analise`, `fipe`, `distancias`) aparecem no roadmap (§7) e batem com as decisões.
- Campos do `data-delta.md` com ação: critérios do alvo (T004, T013), `custos.yaml` (T007, T016, T027), caches (T008, T009, T017, T018), linha de triagem e descartados (T006, T015), comentários (T020, T028).

**Consistência**
- Valores do clarify iguais nos quatro documentos (5%, R$ 2.650, R$ 4,50/km, R$ 450/650, R$ 2.000, 85%, 10%) e o exemplo de R$ 71.060 (requirements RF-08, roadmap D-116, T007).
- A fórmula do lance máximo do D-116 é a da RN-08 com a margem como 10% do custo na garagem (revenda ÷ 1,10).
- Campos `cambio`, `aceitar_*`, `triagem` e bloco `padrao` com o mesmo nome no requirements, roadmap, data-delta e ações; valores `automatico`, `cvt`, `manual` sem acento em todos.
- Nenhum identificador fantasma: D-104 a D-117 existem; os RF citados existem.

**Coerência com o legado** (âncora greenfield: specs + adendos; não há `domain.md` nem `architecture.md`)
- O câmbio no motor (D-108) só descarta com certeza, coerente com a regra "na dúvida, a confirmar" e com o Milan escrevendo AUTOMATICO para CVT (adendo 005).
- A leitura do lote usa o acesso e a conduta do bot (adendos 003 e 005; regra anti-bot).
- A lista continua só por acréscimo do bot; a skill escreve pela linha de comando, sem tocar no comentário `<!-- lote -->` (E002 da 003).
- Banco inalterado; o lote descartado continua conhecido e não volta.

**Sanidade do actions**
- 33 ações; todas as dependências apontam para IDs existentes; nenhum ciclo; maior cadeia = 11 (confere com o resumo).
- Nenhum par de ações `[//]` compartilha arquivo alvo; 26 paralelizáveis (confere). T021 e T022 (mesmo `cli.py`) estão em sequência.
