# Requirements: Skill `analisar-lotes` (triagem e custo na garagem)

> Identificador: `006-analisar-lotes`
> Data: `2026-10-15`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Uma skill de agente, `/analisar-lotes`, que trabalha sobre a lista `1OUTPUT/lotes-a-monitorar.md`. **Primeiro passo (o mais simples e o de maior uso):** triar cada lote contra o veículo-alvo nos critérios que o bot não consegue aplicar na varredura (origem financiamento, câmbio, sinistro, sucata, monta, km acima do máximo, mecânica, documento, lote encerrado ou retirado), com veredito e motivo. **Segundo passo:** para os lotes aprovados, estimar o custo com o carro na garagem em Londrina e o % da FIPE desse custo, com o lance máximo para a margem do Rafael. A skill é instrução para o agente (Claude Code, Antigravity, Codex) mais scripts determinísticos testados; o bot não muda de comportamento, exceto onde o requirements diz.

## 2. Contexto a partir do legado

Projeto greenfield com as features 001 a 005 entregues; não há `architecture.md` nem `domain.md`.

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_forward/backlog.md` item ★ "Custo na garagem em Londrina" | Skill `analisar-lotes` (une os itens 2, 3 e 8): fórmula, dados por leiloeiro, `config/custos.yaml`, script `scripts/custo_garagem.py`, formato da análise, onde guardar (`.claude/skills/` e `.agents/skills/` com exceção no `.gitignore`), primeiro caso Versa 315452. Abordagem escolhida em 2026-10-10: skill + script, não código no bot | 🟢 |
| `_reversa_forward/backlog.md` item 1 | Filtro de câmbio por veículo-alvo, prioridade do Rafael; hoje o bot não filtra câmbio | 🟢 |
| `_reversa_sdd/sdd/motor-filtros.md` | Critérios do bot: marca, modelo (contém), `excluir`, ano de modelo, lance contra o teto, km opcional, tipo de leilão; lote sem preço ou sem km passa como "a confirmar" | 🟢 |
| `_reversa_sdd/sdd/configuracao-veiculos-alvo.md` e `config/veiculos-alvo.yaml` | Campos do alvo; preferência registrada em comentário: **só câmbio automático**; notas por alvo ("só 1.6 CVT", "só 2.0 Dynamique Plus ou Privilège") em comentários e em `config/veiculos-alvo-notas.md`, que nenhum código lê | 🟢 |
| `_reversa_sdd/addenda/001` a `005` | Lista de monitoramento numerada, só por acréscimo do bot, campos (FIPE, lances, despesas, frete, manutenções, valor na garagem, pátio, km, pregão, documento, observações, link, câmbio, alvo); `1OUTPUT/comentarios-lotes-a-monitorar.md` (regras: tirar lote encerrado, retirado ou acima do teto; não mexer no `<!-- lote: ... -->`; reaparições) | 🟢 |
| `_reversa_sdd/addenda/005-leiloeiro-milan.md` | Milan e Copart só pelo acesso do bot (Apify; Copart com Imperva na página HTML): o agente não abre essas páginas pelo navegador comum; câmbio já vem preenchido no Milan | 🟢 |
| Memória do projeto (`rafael-local-e-custos`, `criterios-escolha-veiculo-alvo`) | Londrina-PR; 5% de comissão; despesa fixa por lote; referências de transferência (estimadas) e frete (sem orçamento); fórmula do lance máximo; FIPE pela API parallelum, nunca de memória | 🟡 |
| `1OUTPUT/lotes-a-monitorar.md` (2026-10-15) | 14 lotes: Fluence `DYN 20M` (manual) e `DYN 20A` sinistrado (Kuss), Copart "aguardando classificação" (sem data, FIPE e lance), "NÃO AVALIÁVEL", "MECÂNICA COM PROBLEMAS" | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Rafael, comprador | Ficar só com os lotes que de fato servem | Depois de uma varredura, roda `/analisar-lotes`; o Fluence manual e o sinistrado saem da lista com o motivo, e o Kicks da Copart ("1.6 16V", sem câmbio no título) fica "a confirmar: câmbio" 🟢 |
| Rafael, decidindo o lance | Saber quanto o carro custa na garagem e até quanto dar | Para o Versa aprovado, a análise mostra FIPE da versão, custo na garagem e % da FIPE, e o lance máximo para a margem dele 🟢 |
| Agente (Claude, Antigravity, Codex) | Seguir o mesmo roteiro, sem errar conta | Lê critérios do YAML, abre o lote pelo acesso do bot, chama o script para FIPE e custo, escreve só no bloco do lote 🟡 |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** A skill é acionada sob demanda (`/analisar-lotes`, ou "analisa os lotes da lista"), para a lista inteira ou para um lote (número ou link). Ela não roda sozinha na varredura. 🟢
   - Origem: backlog item ★ (2026-10-10)
   - Tipo: nova
2. **RN-02:** **Triagem primeiro.** Cada lote recebe um veredito: **aprovado**, **reprovado** (com o motivo e a evidência, ex.: "câmbio manual: título 'DYN 20M'") ou **a confirmar** (com o que falta, ex.: "câmbio não informado; ver fotos do painel"). Na dúvida, nunca reprova: fica "a confirmar". 🟢
   - Origem: pedido do Rafael em 2026-10-15
   - Tipo: nova
3. **RN-03:** Critérios da triagem, além dos que o bot já aplica: origem financiamento (Copart e Kuss misturam origens); câmbio aceito pelo alvo; sinistro, sucata e monta; km acima do máximo do alvo; problema mecânico ou de documento declarado ("VEÍCULO NÃO FUNCIONA", "SEM CHAVE", "MECÂNICA COM PROBLEMAS"); versão fora da preferência do alvo; lote encerrado ou retirado; lance atual acima do teto. 🟡
   - Tipo: nova
4. **RN-04:** Os critérios ficam em **uma fonte só**, o `config/veiculos-alvo.yaml`, que o bot também lê, em dois tipos: 🟢
   - **Campos fixos**, validados na carga (grafia errada ou valor inválido aborta antes da rede, como os outros campos), num bloco `padrao` que vale para todos os alvos e que cada alvo pode sobrescrever:
     - `cambio`: lista entre `automatico`, `cvt` e `manual` (padrão inicial: `[automatico, cvt]`);
     - `aceitar_sinistro` (padrão `false`), `aceitar_sucata` (`false`), `aceitar_mecanica_com_problema` (`false`), `aceitar_pequenas_avarias` (`true`).
   - **Texto livre por alvo**, `triagem: "..."`, lido só pela skill, para critérios em português que não viram campo (ex.: "Só 2.0 Dynamique Plus ou Privilège, automáticos. Fora GT Line e 1.6."). As preferências que hoje estão em comentário no YAML migram para esse campo.
   - O Rafael acrescenta e tira critérios editando o YAML: campo fixo novo exige código; critério em texto livre, não.
   - Falta de informação (ex.: "NÃO AVALIÁVEL" da Copart, câmbio não informado) não reprova: vira "a confirmar" (RN-02).
   - Origem: `config/veiculos-alvo-notas.md` ("quando uma nota virar regra, ela migra para o YAML"); esclarecimento de 2026-10-15
   - Tipo: nova

5. **RN-05:** O lote **reprovado sai da lista** e vai para `1OUTPUT/lotes-descartados.md`, com o bloco original, o motivo, a evidência e a data da triagem (reversível: basta devolver o bloco). O lote "a confirmar" fica na lista com a marcação do que falta. 🟢
   - Origem: esclarecimento de 2026-10-15; `1OUTPUT/comentarios-lotes-a-monitorar.md` (o Rafael, ou um agente a pedido dele, tira lotes da lista)
   - Tipo: nova

6. **RN-06:** A skill só altera o bloco do lote analisado: nunca o comentário `<!-- lote: ... -->`, nunca a numeração, nunca outro bloco. Não roda enquanto uma varredura estiver em andamento (a varredura acrescenta blocos no mesmo arquivo). 🟢
   - Origem: `1OUTPUT/comentarios-lotes-a-monitorar.md`; trava da varredura (`dados/varredura.lock`)
   - Tipo: nova
7. **RN-07:** A evidência vem, nesta ordem: (a) o que já está no bloco (título, observações, câmbio, km); (b) a página do lote, lida **pelo acesso do bot** (mesmo nível e conduta: `script` ou `apify`, 5 s por host), só quando (a) não basta. Página do Milan custa ~US$ 0,08 pelo Apify; a skill informa quantas páginas pagas leu. 🟡
   - Origem: adendos 003 (Imperva na Copart) e 005 (Apify no Milan)
   - Tipo: nova
8. **RN-08:** **Custo na garagem** (depois da triagem, só para aprovados): lance + comissão + despesa fixa do lote + frete do pátio até Londrina + transferência + reserva de reparos; ao lado, o % da FIPE. **Lance máximo** ≈ (revenda − transferência − frete − reparos − margem − despesa fixa) ÷ (1 + comissão). As contas são feitas por script determinístico, nunca de cabeça. Valores iniciais em `config/custos.yaml`, todos editáveis pelo Rafael: 🟡
   - comissão **5%** do lance;
   - despesa fixa **a do lote** quando o bot preencheu; senão **R$ 2.650** (mediana do Vip);
   - frete **R$ 4,50 por km** do pátio até Londrina, **marcado como estimativa** até haver orçamento real de guincho;
   - transferência **R$ 450** (documento do PR) ou **R$ 650** (outro estado);
   - reserva de reparos **R$ 2.000** por carro (a skill pode somar mais quando as observações citam avaria, dizendo quanto e por quê);
   - revenda **85% da FIPE**;
   - margem desejada **10% sobre o custo na garagem**.
   - Origem: memória `rafael-local-e-custos`; backlog item ★; esclarecimento de 2026-10-15 (valores sugeridos e aceitos como ponto de partida)
   - Tipo: nova

9. **RN-09:** **FIPE pela API**, nunca de memória: registrar código FIPE e mês de referência. Se o título do lote couber em mais de uma versão FIPE plausível, listar as opções com valor em vez de escolher. 🟢
   - Origem: memória `criterios-escolha-veiculo-alvo`; backlog item ★
   - Tipo: nova
10. **RN-10:** A skill nunca dá lance, não faz login e não contorna proteção anti-bot por conta própria (usa o acesso do bot, regra anti-bot da 005). 🟢
    - Tipo: mantida
11. **RN-11:** **Pregão que já passou não reprova** (decisão do Rafael em 2026-10-15, fase de investigação da viabilidade dos leilões): o lote é julgado pelos outros critérios e ganha a linha `Resultado do pregão` com o que o site mostra. O Kuss não divulga o valor final, só se houve lance e se foi presencial ou online (evento 897, verificado em 2026-10-15); o apelido de quem deu lance nunca é gravado. 🟢
    - Tipo: nova (ajuste depois da primeira rodada de avaliações)
12. **RN-12:** A skill aproveita o que a primeira rodada mostrou: grava o **câmbio deduzido** do título ou da página no campo Câmbio, cita as **reaparições** no resumo (mesmo modelo, ano e final de placa) e dá, só no resumo, uma **referência de lance máximo** para os lotes "a confirmar" pela versão automática mais barata. 🟢
    - Tipo: nova (ajuste depois da primeira rodada de avaliações)

13. **RN-13:** (emenda de 2026-10-15, pedido do Rafael) Lote **"a confirmar" é reconferido em toda execução** da skill: ela lê o lote no site, atualiza no bloco o **Lance atual** e o **Pregão** quando mudaram e julga de novo (a triagem nova substitui a antiga, com a data do dia). O **resultado do pregão** é lido e informado **por leiloeiro**, com o que cada site divulga, registrado em `.claude/skills/analisar-lotes/references/resultados-por-leiloeiro.md`: Kuss só o tipo do último lance; Copart tira o lote da busca pública; Vip mostra a situação final e o último lance; Freitas, o status e o maior lance; Milan, o estado, sem o valor. 🟢
    - Tipo: nova (emenda antes do sync)

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve oferecer a skill `analisar-lotes` em `.claude/skills/` e em `.agents/skills/`, versionada no git (exceção no `.gitignore`), acionável pela lista inteira ou por um lote | Must | `/analisar-lotes` e `/analisar-lotes 3` funcionam; `git ls-files` lista a skill | 🟢 |
| RF-02 | A skill deve triar cada lote pelos critérios da RN-03, lendo os critérios do `veiculos-alvo.yaml` (RN-04) | Must | Na lista de 2026-10-15: Fluence `DYN 20M` reprovado por câmbio manual; Fluence `DYN 20A` sinistrado reprovado por sinistro; Kicks do Kuss "S DRCT CVT" aprovado no câmbio (CVT); Kicks da Copart "1.6 16V" "a confirmar: câmbio" | 🟡 |
| RF-03 | A skill deve escrever no bloco do lote uma linha de triagem com data, veredito, motivo e evidência, e dar ao fim um resumo (aprovados, reprovados por motivo, a confirmar) | Must | Bloco ganha `- **Triagem (15/10/2026):** reprovado — câmbio manual (título "DYN 20M")`; o comentário `<!-- lote -->` fica igual | 🟢 |
| RF-04 | A skill deve mover o lote reprovado para `1OUTPUT/lotes-descartados.md` com motivo, evidência e data (RN-05) | Must | O Fluence `DYN 20M` sai da lista e aparece no arquivo de descartados com "câmbio manual (título 'DYN 20M')"; os números dos outros blocos não mudam | 🟢 |
| RF-05 | O sistema deve aceitar no `veiculos-alvo.yaml` o bloco `padrao`, os campos fixos de critério (com sobrescrita por alvo) e o texto livre `triagem` (RN-04), validados na carga | Must | `cambio: [automatico, cvt]` no padrão vale para todos; um alvo com `cambio: [manual]` sobrescreve; `cambio: [automático]` (grafia errada) aborta citando a linha; `triagem` aceita qualquer texto | 🟢 |
| RF-06 | O bot deve aplicar o critério de câmbio quando o lote já traz o câmbio (hoje, Milan), descartando na varredura o que o alvo não aceita | Should | Com o alvo "só automático", um lote do Milan com câmbio "manual" não é candidato | 🟡 |
| RF-07 | A skill deve ler a página do lote pelo acesso do bot (script de apoio que usa os clientes e o nível do leiloeiro), só quando o bloco não basta, e informar as páginas pagas lidas | Should | Para um lote do Milan, a página vem pelo Apify e o resumo diz "1 página paga (~US$ 0,08)"; nenhum acesso direto do agente ao site | 🟡 |
| RF-08 | A skill deve calcular, para os aprovados, o custo na garagem e o % da FIPE, por script determinístico com `config/custos.yaml` (RN-08) | Should | Lance R$ 61.000, despesa R$ 2.650, pátio a 380 km, documento de outro estado: lance R$ 61.000 + comissão R$ 3.050 + despesa R$ 2.650 + frete R$ 1.710 (estimativa) + transferência R$ 650 + reparos R$ 2.000 = R$ 71.060; a mesma entrada dá sempre o mesmo resultado | 🟢 |
| RF-09 | A skill deve consultar a FIPE pela API, com código e mês, e listar as versões candidatas quando houver ambiguidade (RN-09) | Should | "NISSAN VERSA 1.6 16V — 2017" (Copart) gera a lista das versões 1.6 de 2017 com valor, sem escolher | 🟢 |
| RF-10 | A skill deve calcular o lance máximo para a margem configurada (RN-08) | Could | Linha "Lance máximo para margem de 10%: R$ …" no bloco, pela fórmula da RN-08 com revenda a 85% da FIPE | 🟢 |
| RF-11 | A skill deve recusar rodar com a varredura em andamento, dizendo por quê | Must | Com `dados/varredura.lock` ativo, a skill para sem escrever | 🟢 |
| RF-12 | O sistema deve permitir gravar no bloco os campos `Câmbio` e `Resultado do pregão` pela linha de comando (RN-11, RN-12) | Must | `analise anotar 1 --campo "Resultado do pregão" --valor "13/10: último lance presencial; valor não divulgado pelo site"` grava a linha antes do Link; outro campo é recusado | 🟢 |
| RF-13 | A leitura do lote do Kuss deve trazer o resultado do pregão (último lance presencial, online ou sem lance), sem o apelido (RN-11) | Should | Lote 282164 do evento 897: "último lance presencial; valor não divulgado pelo site" | 🟢 |
| RF-14 | A leitura do lote deve trazer o resultado do pregão nos cinco leiloeiros e, com o pregão aberto, o lance atual; a lista deve aceitar gravar `Lance atual` e `Pregão`; a skill deve reconferir os "a confirmar" e informar os resultados por leiloeiro (RN-13) | Must | Vip 310800: "condicional negada; último lance R$ 13.000"; Freitas 8103/3: "vendido; maior lance R$ 43.500"; Milan 15618/001: "vendido; valor não divulgado pelo site"; Copart fora da busca: "saiu da busca pública…" | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Qualidade | Scripts de apoio com testes sem rede (FIPE e acesso simulados); o `SKILL.md` redigido e avaliado com o `skill-creator` sobre lotes reais da lista (casos de aprovação, reprovação e "a confirmar") | Decisão de 2026-10-15: Reversa para o registro e o código, `skill-creator` para a qualidade da skill | 🟢 |
| Portabilidade | Mesma skill para Claude Code (`.claude/skills/`) e Antigravity/Codex (`.agents/skills/`) | Backlog item ★ | 🟢 |
| Custo | Página paga só quando necessária; total informado | RN-07; adendo 005 | 🟢 |
| Segurança | Nenhum segredo no `SKILL.md` nem nos scripts; tokens só do `.env` | RN-08 da 001 | 🟢 |
| Rastreabilidade | Toda reprovação traz a evidência (trecho do título, observação ou página) | RN-02 | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Fluence manual é reprovado pelo câmbio
  Dado o alvo Fluence com câmbio aceito "automático"
  E o lote 2 "IMP RENAULT/FLUENCE DYN 20M — 2015" na lista
  Quando o Rafael roda /analisar-lotes
  Então o lote 2 fica reprovado com o motivo "câmbio manual" e a evidência "DYN 20M"

Cenário: Fluence sinistrado é reprovado
  Dado o lote 3 com a observação "SINISTRADO - NOS DOCUMENTOS CONSTA RECUPERADO DE SINISTRO"
  E o alvo que não aceita sinistro
  Quando o Rafael roda /analisar-lotes
  Então o lote 3 fica reprovado com o motivo "sinistro"

Cenário: Falta de informação não reprova
  Dado um lote da Copart "aguardando classificação" sem câmbio no título
  Quando o Rafael roda /analisar-lotes
  Então o lote fica "a confirmar" com o que falta (câmbio, lance e data)

Cenário: Versão ambígua na FIPE não é escolhida pela skill
  Dado um lote aprovado "NISSAN VERSA 1.6 16V — 2017"
  Quando a skill consulta a FIPE
  Então o bloco lista as versões 1.6 de 2017 com valor e código, sem escolher uma

Cenário: Varredura em andamento
  Dado uma varredura em execução
  Quando o Rafael roda /analisar-lotes
  Então a skill não altera a lista e explica que a varredura está rodando
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 a RF-05, RF-11 | Must | Triagem é o primeiro uso pedido pelo Rafael e a de maior frequência |
| RF-06 a RF-09 | Should | Câmbio no bot onde há dado; leitura da página; custo e FIPE (segundo passo) |
| RF-10 | Could | Depende de margem e revenda configuradas |
| Custo automático no Telegram | Won't (nesta feature) | Evolução prevista: a skill vira o protótipo e o cálculo migra para o bot (backlog item ★, passo 8) |

## 9. Esclarecimentos

### Sessão 2026-10-15

- **Q:** Quais campos de critério entram no `veiculos-alvo.yaml` e com que valores padrão? Dá para acrescentar e tirar depois?
  **R:** Bloco `padrao` com campos fixos validados (`cambio: [automatico, cvt]`, `aceitar_sinistro: false`, `aceitar_sucata: false`, `aceitar_mecanica_com_problema: false`, `aceitar_pequenas_avarias: true`), sobrescrevíveis por alvo, mais o texto livre `triagem` por alvo, lido só pela skill. Sim: o Rafael edita o YAML; campo fixo novo exige código, critério em texto livre não. Falta de informação vira "a confirmar". (Sugestão aceita.) Registrado em RN-04 e RF-05.
- **Q:** O que fazer com o lote reprovado?
  **R:** Mover para um arquivo de descartados, informando o motivo. Registrado em RN-05 e RF-04 (`1OUTPUT/lotes-descartados.md`, com motivo, evidência e data).
- **Q:** Quais valores no `config/custos.yaml`?
  **R:** Os sugeridos, como ponto de partida editável: comissão 5%; despesa fixa do lote ou R$ 2.650; frete R$ 4,50/km (estimativa até haver orçamento); transferência R$ 450 (PR) ou R$ 650 (outro estado); reparos R$ 2.000; revenda 85% da FIPE; margem 10% sobre o custo na garagem. Registrado em RN-08, RF-08 e RF-10.

## 10. Lacunas

- 🟡 Verificação técnica para o plano: como o script de apoio lê a página do lote de cada leiloeiro pelo acesso do bot (Vip, Kuss, Copart, Freitas, Milan), e se a página da Copart (Imperva) tem alternativa pública; disponibilidade e formato da API FIPE (parallelum); como estimar a distância do pátio até Londrina (tabela no `custos.yaml` ou cálculo).
- 🟡 Frete real: trocar a estimativa de R$ 4,50/km quando o Rafael tiver um orçamento de guincho.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-15 | Emenda antes do sync: reconferência dos "a confirmar" e resultado do pregão por leiloeiro (RN-13, RF-14) | Claude |
| 2026-10-15 | Ajuste do Rafael depois da primeira rodada de avaliações: pregão passado não reprova e ganha o resultado (RN-11, RF-12, RF-13); câmbio deduzido, reaparições e referência de lance (RN-12) | Claude |
| 2026-10-15 | Sessão de esclarecimento: critérios no YAML (RN-04, RF-05), descartados (RN-05, RF-04), valores de custo (RN-08, RF-08, RF-10) | `/reversa-clarify` |
| 2026-10-15 | Versão inicial gerada por `/reversa-requirements` a partir do backlog item ★, do pedido do Rafael de triagem primeiro e da lista de 2026-10-15 | reversa |
