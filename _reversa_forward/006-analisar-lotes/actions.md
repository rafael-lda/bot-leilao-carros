# Actions: Skill `analisar-lotes` (triagem e custo na garagem)

> Identificador: `006-analisar-lotes`
> Data: `2026-10-15`
> Roadmap: `_reversa_forward/006-analisar-lotes/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 33 |
| Paralelizáveis (`[//]`) | 26 |
| Maior cadeia de dependência | 11 (T001 → T002 → T010 → T019 → T021 → T022 → T023 → T024 → T025 → T029 → T032) |

Convenções: `src/bot_leilao/` é abreviado como `src/…`. Testes antes do núcleo (TDD); a suíte anterior (727 testes) continua verde ao fim de cada etapa.

Rede: nenhum teste acessa a rede (FIPE, mapas e sites simulados). Rede real só no T024 (avaliações do `skill-creator`, que leem páginas e FIPE de verdade) e no T029 (execução real), com páginas do Milan pagas só se necessárias.

Política de escrita: `allowLegacyEdits: true`, `allowedPaths` vazio (liberação irrestrita). Caminhos tocados: `src/**`, `tests/**`, `config/veiculos-alvo.yaml`, `config/custos.yaml`, `.gitignore`, `.claude/skills/analisar-lotes/**`, `.agents/skills/analisar-lotes/**`, `README.md`, e (fora do git) `1OUTPUT/comentarios-lotes-a-monitorar.md`, `1OUTPUT/lotes-a-monitorar.md` e `1OUTPUT/lotes-descartados.md` (só pela linha de comando, na execução real).

| Etapa | Ações | Conteúdo |
|-------|-------|----------|
| 1 | T001 a T012 | Fixtures, simuladores, `.gitignore` e todos os testes (falham até a etapa 2) |
| 2 | T013 a T022 | Critérios no YAML, câmbio no motor, módulo `analise` (lista, custo, distância, FIPE, página) e linha de comando |
| 3 | T023 a T033 | `SKILL.md` com o `skill-creator` (rascunho, avaliações, cópia), configurações do Rafael, execução real e documentação |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Fixtures em `tests/fixtures/analise/`: cópia da lista de 2026-10-15 (14 lotes); respostas da parallelum (`references`, anos e valor do 023140-1) e do site oficial (`ConsultarTabelaDeReferencia`, valor) iguais às verificadas; Nominatim (Londrina, Curitiba) e OSRM (386 km) | - | `[//]` | `tests/fixtures/analise/` | 🟢 | `[X]` |
| T002 | Em `tests/apoio.py`: `SiteFipe` (parallelum e site oficial, com modos de falha e limite 429), `SiteMapas` (Nominatim e OSRM, com falha), `lista_de_teste(raiz)` que copia a fixture para `1OUTPUT/`; roteamento dos hosts no `CenarioE2E` | T001 | `[//]` | `tests/apoio.py` | 🟢 | `[X]` |
| T003 | `.gitignore`: `.claude/skills/` e `.agents/skills/` viram `…/skills/*` com a exceção `!…/skills/analisar-lotes/` (D-106); conferir com `git check-ignore` que as skills do Reversa continuam fora | - | `[//]` | `.gitignore` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | (RF-05) Critérios no YAML: `padrao` aplicado a todos; alvo sobrescreve campo a campo; `cambio` só com `automatico`, `cvt`, `manual` (grafia errada como `automático` aborta citando alvo e campo); `aceitar_*` só booleano; `triagem` texto não vazio; arquivo sem `padrao` nem campos continua válido e aceita tudo (D-107) | - | `[//]` | `tests/test_config_veiculos.py` | 🟢 | `[X]` |
| T005 | (RF-06) Câmbio no motor: lote "manual" contra alvo `[automatico, cvt]` descartado; "automático" contra `[cvt]` não descartado; "CVT" contra `[manual]` descartado; lote sem câmbio passa; alvo sem `cambio` aceita tudo; contagem no log (D-108) | - | `[//]` | `tests/test_motor_criterios.py` | 🟢 | `[X]` |
| T006 | (RF-03, RF-04, RN-05, RN-06) Lista: lê os blocos da fixture (número, id, título, campos); `triar` aprovado e a confirmar inserem a linha antes de `- **Link:**` e substituem a anterior; reprovado move o bloco para `lotes-descartados.md` com a linha de descarte, e os outros blocos ficam byte a byte iguais; `devolver` traz de volta; número inexistente é erro; comentário `<!-- lote -->` intacto (D-112) | T001 | `[//]` | `tests/test_analise_lista.py` | 🟢 | `[X]` |
| T007 | (RF-08, RF-10) Custo: `custos.yaml` criado com os valores do clarify se ausente; campo inválido é erro; exemplo do requirements (lance R$ 61.000, despesa R$ 2.650, 380 km pela tabela, documento de SC) = R$ 71.060; % da FIPE; lance máximo pela fórmula do D-116; despesa ausente usa o padrão marcado; distância desconhecida deixa o frete "a confirmar"; `reparos_extra` com motivo soma ao total e aparece nas parcelas (D-116) | - | `[//]` | `tests/test_analise_custos.py` | 🟢 | `[X]` |
| T008 | (RF-09) FIPE: candidatas por marca, termos e ano com valor, código, mês e fonte; valor por código; parallelum fora ou com 429 → site oficial; as duas fora → "FIPE indisponível"; cache por mês evita nova consulta e é ignorado quando o mês muda (D-114) | T002 | `[//]` | `tests/test_analise_fipe.py` | 🟢 | `[X]` |
| T009 | Distância: tabela do `custos.yaml` vence; cache; Nominatim + OSRM gravam no cache (386 km); falha ou pátio só com UF → None; no máximo 1 consulta por segundo ao Nominatim (D-115) | T002 | `[//]` | `tests/test_analise_distancias.py` | 🟢 | `[X]` |
| T010 | (RF-07) Página do lote pelo acesso do bot: Vip (texto com "Câmbio"), Kuss (evento e sequência tirados do link; observações do detalhe), Copart (busca com `query=<lote>`), Freitas (detalhe), Milan (pelo Apify, `pago` verdadeiro e custo estimado); texto limpo até 8.000 caracteres; link do lote convertido no número do bloco; nenhuma chamada local ao Milan (D-110) | T002 | `[//]` | `tests/test_analise_pagina.py` | 🟢 | `[X]` |
| T011 | (RF-01, RF-11, RN-01) Linha de comando (número ou link do lote): `analise lotes [--numero]`, `pagina`, `triar`, `devolver`, `fipe-candidatos`, `fipe-valor`, `custo`, `anotar-custo` com saída JSON e códigos 0/1/3; com a trava da varredura ocupada, os que escrevem saem com 3 sem alterar nada; `anotar-custo` preenche FIPE, % da FIPE, Despesas admin., Frete, Valor estimado na garagem e Lance máximo (D-104, D-117) | T002 | `[//]` | `tests/test_cli_analise.py` | 🟢 | `[X]` |
| T012 | (RF-01) Skill: `.claude/skills/analisar-lotes/SKILL.md` e `.agents/skills/analisar-lotes/SKILL.md` existem e são idênticos (pasta inteira); cabeçalho com `name` e `description`; nenhum token ou segredo no texto; `git ls-files` lista a skill (D-106) | - | `[//]` | `tests/test_skill_analisar_lotes.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T013 | `config/veiculos.py`: bloco `padrao`, campos de critério e `triagem` no `VeiculoAlvo`, com a sobrescrita e a validação (D-107) | T004 | `[//]` | `src/…/config/veiculos.py` | 🟢 | `[X]` |
| T014 | `filtro/motor.py`: câmbio quando conhecido, só com certeza; contagem no log e em `descartados_sem_casar` (D-108) | T005, T013 | - | `src/…/filtro/motor.py` | 🟢 | `[X]` |
| T015 | `analise/lista.py`: leitura dos blocos, linha de triagem, mover para descartados, devolver, escrita atômica (D-112) | T006 | `[//]` | `src/…/analise/lista.py` | 🟢 | `[X]` |
| T016 | `analise/custos.py`: `custos.yaml` (criação, validação) e cálculo (parcelas, total, % da FIPE, lance máximo) (D-116) | T007 | `[//]` | `src/…/analise/custos.py` | 🟢 | `[X]` |
| T017 | `analise/distancias.py`: tabela, cache, Nominatim e OSRM (D-115) | T009 | `[//]` | `src/…/analise/distancias.py` | 🟢 | `[X]` |
| T018 | `analise/fipe.py`: parallelum, reserva no site oficial, cache por mês, candidatas por termos (D-114) | T008 | `[//]` | `src/…/analise/fipe.py` | 🟢 (🟡 estabilidade das fontes) | `[X]` |
| T019 | `analise/pagina.py`: leitura do lote por leiloeiro com os clientes e o nível do bot, campos do parser e texto limpo (D-110) | T010 | `[//]` | `src/…/analise/pagina.py` | 🟢 | `[X]` |
| T020 | Texto padrão do arquivo de comentários (`COMENTARIOS_MONITORAMENTO`): linha de triagem e arquivo de descartados (D-113) | - | `[//]` | `src/…/notificacao/relatorio.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T021 | Linha de comando: `analise lotes`, `pagina`, `triar`, `devolver` (com a trava da varredura nos que escrevem) (D-104) | T011, T015, T019 | - | `src/…/cli.py` | 🟢 | `[X]` |
| T022 | Linha de comando: `analise fipe-candidatos`, `fipe-valor`, `custo`, `anotar-custo` (D-104, D-117) | T021, T016, T017, T018 | - | `src/…/cli.py` | 🟢 | `[X]` |
| T023 | (RF-02, RF-03, RN-03) Rascunho do `SKILL.md` com o `skill-creator`: gatilhos; roteiro da triagem com **todos os critérios da RN-03** e a origem de cada um (campos já existentes do alvo: tipo de leilão, ano, teto contra o lance atual, km máximo; campos novos: câmbio, sinistro, sucata, mecânica, pequenas avarias; texto `triagem`: versão preferida; estado do lote: encerrado, retirado, documento); ordem da evidência e Copart sem câmbio "a confirmar" (D-111); "na dúvida, a confirmar"; resumo com aprovados, reprovados, a confirmar e **total de páginas pagas**; confirmação do Rafael antes de mover; custo para os aprovados com reparos extras quando houver avaria; tudo só pela linha de comando (D-104, D-105, D-111, RN-01 a RN-10) | T022 | - | `.claude/skills/analisar-lotes/SKILL.md` | 🟢 | `[X]` |
| T024 | Avaliações com o `skill-creator`: casos com a lista de 2026-10-15 e o veredito esperado de cada lote (`investigation.md` §5), mais os cenários de FIPE ambígua, de varredura em andamento, de km acima do máximo e de lance atual acima do teto (lotes da fixture alterados); rodar, comparar e ajustar o `SKILL.md` até acertar; guardar as avaliações na pasta da skill | T023 | - | `.claude/skills/analisar-lotes/evals/` | 🟡 | `[X]` |
| T025 | Cópia idêntica da skill em `.agents/skills/analisar-lotes/` (teste do T012 verde) (D-106) | T024, T003, T012 | - | `.agents/skills/analisar-lotes/` | 🟢 | `[X]` |
| T026 | Migrar o `config/veiculos-alvo.yaml` do Rafael: `padrao` e texto `triagem` por alvo a partir dos comentários atuais, mostrando o diff (D-109) | T013 | `[//]` | `config/veiculos-alvo.yaml` | 🟡 | `[X]` |
| T027 | `config/custos.yaml` versionado com os valores do clarify (D-116) | T016 | `[//]` | `config/custos.yaml` | 🟢 | `[X]` |
| T028 | Atualizar o `1OUTPUT/comentarios-lotes-a-monitorar.md` existente com as regras novas (D-113) | T020 | `[//]` | `1OUTPUT/comentarios-lotes-a-monitorar.md` | 🟢 | `[X]` |
| T029 | Execução real de `/analisar-lotes` sobre a lista atual: a skill mostra o resumo ao Rafael e só move os reprovados com o OK dele; registrar o resultado nas Notas (páginas lidas, custo do Apify, FIPE e custos dos aprovados) | T025, T026, T027, T028 | - | (execução) | 🟡 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T030 | README: a skill (`/analisar-lotes`), critérios no YAML (`padrao`, `triagem`), `custos.yaml`, arquivo de descartados, subcomandos `analise` | T025, T027 | `[//]` | `README.md` | 🟢 | `[X]` |
| T031 | Seção "Feature 006" em `tests/RASTREABILIDADE.md`, conferida mecanicamente | T025 | `[//]` | `tests/RASTREABILIDADE.md` | 🟢 | `[X]` |
| T032 | Ajustar `onboarding.md` com o que a execução real mostrou | T029 | `[//]` | `_reversa_forward/006-…/onboarding.md` | 🟢 | `[X]` |
| T033 | Backlog: item ★ marcado como feito (skill), item 1 (filtro de câmbio) atualizado com o que o bot já faz e o que a skill cobre | T029 | `[//]` | `_reversa_forward/backlog.md` | 🟢 | `[X]` |

## Ajustes depois da primeira rodada de avaliações (2026-10-15)

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T034 | (RF-12) `anotar_campo` na lista e subcomando `analise anotar` com a trava; testes (D-118) | T021 | - | `src/…/analise/lista.py` | 🟢 | `[X]` |
| T035 | (RF-13) Resultado do pregão do Kuss na leitura do lote, sem apelido; `SiteKuss` com `op=T`; teste (D-119) | T019 | - | `src/…/analise/pagina.py` | 🟢 | `[X]` |
| T036 | (RN-11, RN-12) `SKILL.md`: pregão passado não reprova e ganha o resultado; câmbio deduzido gravado; reaparições e referência de lance no resumo | T024 | - | `.claude/skills/analisar-lotes/SKILL.md` | 🟢 | `[X]` |
| T037 | Segunda rodada de avaliações (triagem completa e custo do lote 1) com o resultado esperado novo | T036 | - | `.claude/skills/analisar-lotes/evals/` | 🟢 | `[X]` |

## Notas de execução

- **Ajustes do audit (2026-10-15):** A001 a A005 aplicados antes da etapa 1 (critérios da RN-03 e D-111 no T023, casos novos no T024, reparos extras, link do lote).
- **T001 (2026-10-15):** as fixtures da FIPE são respostas reais das duas fontes (mesmos códigos de modelo: Nissan 43, Versa SL Aut. 7628 e Mec. 7629; R$ 62.464 e R$ 61.547 em out/2026); a rota Londrina → Curitiba deu 385 km (385.207 m); a página real de um anúncio do Vip foi guardada (`vip_anuncio_310800.html`).
- **T002 (2026-10-15):** `CenarioE2E` ganhou `fipe` e `mapas`; o campo `transporte_analise` das dependências é ligado quando existir (criado no T021).
- **Etapa 1 concluída (2026-10-15):** T001–T012. Suíte: 729 passando (727 anteriores + 2 da skill que já valem: nenhum segredo e `.gitignore`); 36 falhando e 5 módulos sem coletar (`test_analise_*`), à espera das etapas 2 e 3.
- **T014 (2026-10-15):** `cambio_aceito` no motor; o descarte por câmbio soma em `descartados_sem_casar` (sem contador próprio no log).
- **T018 (2026-10-15):** quando a parallelum responde mas o código não tem o ano, é erro (não cai na reserva); a reserva entra só com a fonte fora. O cache guarda apenas o mês de referência atual.
- **T021 (2026-10-15):** os logs do console iam para a saída padrão e misturariam com o JSON; `configurar_logs(console=False)` nos subcomandos `analise` (só o arquivo de log). `Dependencias` ganhou `transporte_analise` (FIPE e mapas). Um `%` no texto de ajuda do `custo` quebrava o argparse (`%%`).
- **Teste com dados reais (2026-10-15):** `analise lotes --numero 2` com a lista e a config reais; `fipe-candidatos` Renault "fluence dynamique 2.0" 2015 pela parallelum: Aut. R$ 44.351 (025174-7), Mec. R$ 43.177 (025173-9).
- **Etapa 2 concluída (2026-10-15):** T013–T022; 811 testes passando; 2 falhando (a skill, etapa 3).
- **T023/T024 (2026-10-15), primeira rodada de avaliações** (4 casos, cópias da lista; nenhuma na lista real): com a skill 19/19 verificações; sem a skill (caso 1) 6/7, ~3× o tempo e o dobro de tokens, com edição à mão. O agente sem a skill achou as reaparições (13 = 3, 14 = 2), gravou o câmbio deduzido e deu referência de lance máximo para os "a confirmar": as três ideias entraram na skill (T036).
- **Decisão do Rafael (2026-10-15):** pregão que já passou não reprova; o resultado é anotado (fase de investigação da viabilidade). O Kuss não divulga o valor final (evento 897: 179 últimos lances presenciais, 163 online, 4 sem lance, nenhum valor) (RN-11, D-119).
- **T037 (2026-10-15), segunda rodada:** 20/20 verificações (triagem completa 14/14; custo do lote 1 6/6). A verificação "lote 1 aprovado" do caso 1 estava errada: no teste o alvo Kicks tinha km máximo e o Kuss não informa km, então "a confirmar — km" é o certo pela regra da skill; a verificação foi corrigida. A triagem completa passou de 2,4 para 7,1 minutos (lê páginas dos pregões passados e calcula referências).
- **T026 (2026-10-15):** migração do `veiculos-alvo.yaml` aprovada pelo Rafael e gravada (bloco `padrao` e textos `triagem` tirados dos comentários).
- **T028 (2026-10-15):** o `comentarios-lotes-a-monitorar.md` real era igual ao texto antigo do bot (sem edição do Rafael) e foi trocado pelo texto novo.
- **T029 (2026-10-15), execução real na lista do Rafael:** resumo mostrado e gravação autorizada por ele. 1 aprovado (lote 1, Kicks S Direct CVT: FIPE R$ 76.451, R$ 51.883 na garagem, 68% da FIPE, lance máximo R$ 49.850); 5 reprovados para `lotes-descartados.md` (2 e 14 câmbio manual e mecânica; 3 e 13 sinistro; 11 Duster 2.0); 8 a confirmar (Copart). Reaparições: 13 = 3 e 14 = 2. Resultado do pregão de 13/10 nos lotes 1, 2 e 3 (último lance presencial, valor não divulgado). 23 comandos, nenhuma falha, nenhuma página paga. Cópia da lista antes da triagem guardada no rascunho da sessão.
- **Ajuste durante o T029:** `analise lotes` devolvia o campo como "Triagem (15/10/2026)" (data no nome), o que atrapalharia achar os lotes já triados; agora vem `Triagem: aprovado (15/10/2026)` (e `Descartado`), com teste.
- **Etapa 3 concluída (2026-10-15):** T023–T037; 819 testes passando; rastreabilidade conferida (36 referências); `legacy-impact.md` e `regression-watch.md` (W038–W044) gerados.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-15 | Codificação concluída em três etapas (T001–T037) | `/reversa-coding` |
| 2026-10-15 | Ajustes do `/reversa-audit` (A001 a A005): critérios da RN-03 e D-111 no T023, casos novos no T024, reparos extras (T007), link do lote (T010, T011) | Claude |
| 2026-10-15 | Versão inicial gerada por `/reversa-to-do` | reversa |
