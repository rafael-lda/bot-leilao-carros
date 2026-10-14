# Actions: Leiloeiro Milan (e o nível Apify)

> Identificador: `005-leiloeiro-milan`
> Data: `2026-10-13`
> Roadmap: `_reversa_forward/005-leiloeiro-milan/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 43 |
| Paralelizáveis (`[//]`) | 28 |
| Maior cadeia de dependência | 11 (T001 → T003 → T004 → T020 → T023 → T032 → T033 → T034 → T035 → T039 → T042) |

Convenções: `src/bot_leilao/` é abreviado como `src/…`. Testes antes do núcleo (TDD); a suíte anterior (608 testes) continua verde ao fim de cada etapa.

Rede e custo: só **T039** (dry-run real) acessa a rede, pelo Apify (~US$ 0,16 a 0,40). As amostras de 2026-10-13 são as fixtures; T002 só prepara o script de recaptura, sem executar. Nenhum teste acessa a rede: o Apify é simulado (`ApifySimulado`, T003).

Política de escrita: `allowLegacyEdits: true`, `allowedPaths` vazio (liberação irrestrita). Caminhos tocados: `src/**`, `tests/**`, `scripts/capturar_fixtures.py`, `scripts/varrer.bat`, `scripts/varrer-completo.bat`, `config/leiloeiros.yaml`, `.env.example`, `README.md`.

| Etapa | Ações | Conteúdo |
|-------|-------|----------|
| 1 | T001 a T017 | Fixtures, Apify simulado e todos os testes (falham até as etapas 2 e 3) |
| 2 | T018 a T031 | Núcleo: cliente Apify e roteamento, cadastro e token, adaptador e parser do Milan, enriquecimento, banco, câmbio no relatório |
| 3 | T032 a T043 | Orquestrador (Milan, `--sem-pagos`, intervalo, antecedência, consumo e alertas), linha de comando e atalhos, configuração, dry-run real e documentação |

Fora desta feature: troca automática `script` → `apify` (RF-07, Won't desde o esclarecimento de 2026-10-13; D-92), registrada no backlog pelo T043.

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Copiar as amostras para `tests/fixtures/milan/` com nomes curtos: `agenda.json`, `catalogo_15618.json`, `lote_001.json`, `lote_046.json`, `lote_209.json` (respostas do ator, já anonimizadas e sem cookies) e `erro_token.json` (401 do contrato §4) | - | `[//]` | `tests/fixtures/milan/` | 🟢 | `[X]` |
| T002 | Modo `--milan` em `scripts/capturar_fixtures.py`: recaptura agenda, catálogo do primeiro leilão de financiamento e uma página de lote pelo Apify (token do `.env`), anonimizando apelidos e removendo cookies como nas amostras; avisa o custo antes de rodar; não executar | - | `[//]` | `scripts/capturar_fixtures.py` | 🟢 | `[X]` |
| T003 | Em `tests/apoio.py`: `ApifySimulado` no host `api.apify.com` (execução síncrona que devolve a fixture pela URL pedida; `GET /v2/users/me/limits` com uso configurável; modos de falha: 401, cota 402, 408, 5xx, item com desafio, lista vazia; registro das chamadas e do cabeçalho `Authorization`); roteamento no `CenarioE2E`; `LEILOEIRO_MILAN`; verificação de que nenhuma chamada local vai a `milanleiloes.com.br` | T001 | `[//]` | `tests/apoio.py` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | (RF-01, RF-06, RF-09) `ClienteApify`: `POST …/acts/neatrat~cloudflare-scraper/run-sync-get-dataset-items?timeout=180` com `{"url": …}`, token só no cabeçalho; 201 → `OK` com o `content` e a URL do site; tabela de falhas do contrato §4 (token, cota, tempo, plataforma, desafio, 404, vazio) com no máximo 2 tentativas e nenhuma para token e cota; requisição não GET ou com corpo recusada sem chamada; cookies do item descartados; páginas contadas; consumo pela diferença de `limits` e "indisponível" se a consulta falhar; perfil de ator desconhecido recusado (D-86, D-88, D-89, D-91) | T003 | `[//]` | `tests/test_coleta_apify.py` | 🟢 (🟡 cota) | `[X]` |
| T005 | (RF-01) Roteamento: `Requisicao.nivel` padrão `script`; o `Coletor` carimba o `nivel_coleta` do leiloeiro em toda requisição (busca e preparação); `ClienteRoteado` entrega a cada cliente pelo nível e recusa nível sem cliente (D-87) | - | `[//]` | `tests/test_coleta_roteamento.py` | 🟢 | `[X]` |
| T006 | Cadastro: `apify` aceito e `apify_residencial` ainda "não implementado"; `intervalo_horas` inteiro de 1 a 720 (texto, zero, negativo e 721 recusados citando a linha); `apify_ator` só com `nivel_coleta: apify` e só com perfil conhecido; ausente = padrão (D-88, D-90, D-101) | - | `[//]` | `tests/test_config_leiloeiros.py` | 🟢 | `[X]` |
| T007 | (RF-02) Ambiente: `APIFY_TOKEN` lido do `.env` e do ambiente; exigido só quando pedido (`exigir_apify`), com mensagem que cita a variável; entra em `segredos`; vazio = ausente (D-90) | - | `[//]` | `tests/test_ambiente.py` | 🟢 | `[X]` |
| T008 | (RF-03, RF-04) Adaptador Milan: registrado como `milan-leiloes`; só o filtro `descricao_contem` (texto); página 1 = GET `/agenda/veiculos`; com a agenda real, só o 15618 escolhido (o judicial 15595 fica fora) e a página 2 = GET `/leilao/15618/catalogo` com anotações de evento, pregão e pátio; nenhum leilão escolhido encerra a busca; `teto_paginas = 10`; `requisicao_detalhe` = GET do link do lote (D-93, D-94, D-97) | T001 | `[//]` | `tests/test_coleta_milan.py` | 🟢 | `[X]` |
| T009 | (RF-04, RF-05, RN-02 a RN-04) Parser Milan com o catálogo real: 243 lotes e 11 materiais descartados no log; Creta 046 (id `milan-leiloes:15618-046`, link, `hyundai` / `creta action 1.6 flex 4p`, 2022/2022, km 99020, câmbio `automático`, observações com "IPVA 2026 PAGO" e "Comitente Banco Honda", tipo `financiamento`, pregão 14/10/2026 09:30 −03:00, pátio `São Paulo - SP`); 209 com lance inicial R$ 21.500; um lote com aviso em vermelho nas observações; `015A`; `I/I/TOYOTA` → `toyota`; `LAND ROVER`; `M-BENZ`; `(SUCATA)` → sucata; câmbio `manual`; catálogo sem cards e sem cabeçalho → exceção. Detalhe: 001 lance atual R$ 66.200 e placa `final 6`; 046 sem lance; 209 inicial R$ 21.500 e atual R$ 22.400; página sem bloco de lance e sem estado → exceção (D-95 a D-97) | T001 | `[//]` | `tests/test_parsing_milan.py` | 🟢 (🟡 pátio) | `[X]` |
| T010 | Sinônimos `m-benz` → `mercedes-benz` e `cintroen` → `citroen`; `jaguar` entre as marcas conhecidas (D-95) | - | `[//]` | `tests/test_marcas.py` | 🟢 | `[X]` |
| T011 | (RF-14) Enriquecimento: a requisição do detalhe leva o nível do leiloeiro (mapa recebido); depois do detalhe, lote que deixou de casar com o alvo (lance acima do teto) sai e conta em `acima_do_teto`; lote dentro do teto segue; leiloeiro cujo detalhe não traz preço não muda de comportamento (D-87, D-98) | - | `[//]` | `tests/test_enriquecimento.py` | 🟢 | `[X]` |
| T012 | Banco: migração da versão 1 para a 2 cria `evento_visto` (banco novo e banco existente da versão 1); `registrar_evento` com `INSERT OR IGNORE` guarda só a primeira vez e o `na_semeadura`; `ultima_coleta_ok(leiloeiro)` ignora dry-run e execuções sem busca ok (D-101, D-102) | - | `[//]` | `tests/test_repo_eventos.py` | 🟢 | `[X]` |
| T013 | (RN-04) Relatório e lista: linha "Câmbio" preenchida quando o lote traz câmbio, em branco quando não traz (D-99) | - | `[//]` | `tests/test_relatorio.py` | 🟢 | `[X]` |
| T014 | (RF-11) Linha de comando: `varrer --sem-pagos` chega ao `varrer` do orquestrador; sem a opção, valor falso (D-100) | - | `[//]` | `tests/test_cli.py` | 🟢 | `[X]` |
| T015 | (RF-01 a RF-05, RF-08) Ponta a ponta do Milan, cenários 1 a 4 do requirements: só o leilão de financiamento lido, pelo Apify, sem chamada local ao Milan e com `nivel_usado = apify` no registro; Creta com lance de R$ 50.000 (fixture 046 com o valor trocado no teste) avisado com km, câmbio, pátio, pregão e comitente; o mesmo Creta com lance acima do teto não avisado; sem `APIFY_TOKEN` aborta antes de qualquer requisição citando o Milan e a variável; cota esgotada gera alerta "cota do Apify esgotada" e Vip, Kuss, Copart e Freitas seguem. Mais: estreia do Milan semeia e lista os candidatos nos documentos | T003 | `[//]` | `tests/test_e2e_milan.py` | 🟢 | `[X]` |
| T016 | (RF-11, RF-12, cenário 5) Ritmo: com `--sem-pagos` nenhuma chamada ao Apify, token não exigido, linha "não incluído nesta varredura (sem pagos)" só na seção "Leiloeiros" (nada na lista nem no Telegram); `intervalo_horas` pula o Milan dentro do intervalo com a linha "pulado pelo intervalo … (próxima leitura a partir de …)" e lê depois dele; dry-run não conta como leitura (D-100, D-101) | T003 | `[//]` | `tests/test_e2e_ritmo.py` | 🟢 | `[X]` |
| T017 | (RF-09, RF-13) Antecedência, consumo e alertas: leilão novo gravado em `evento_visto` e citado na linha do leiloeiro com os dias de antecedência; leilões da semeadura marcados e sem alerta; alerta quando há `intervalo_horas` e a antecedência é menor; linha de consumo do Apify (páginas, gasto da varredura, ciclo); alerta a 80% do ciclo, 1 por dia; alertas de token inválido e de desafio "via apify"; o token não aparece em log, banco nem relatório (D-91, D-102, D-103) | T003 | `[//]` | `tests/test_e2e_apify_alertas.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T018 | Campo `Requisicao.nivel` (padrão `"script"`, não vai para a rede) (D-87) | T005 | `[//]` | `src/…/coleta/modelos.py` | 🟢 | `[X]` |
| T019 | Campo `Lote.cambio` (D-99) | T009 | `[//]` | `src/…/parsing/modelos.py` | 🟢 | `[X]` |
| T020 | `coleta/apify.py`: `ClienteApify` (chamada síncrona, perfis `PERFIS_ATOR`, tradução de falhas e tentativas, espaçamento por host do site, contagem de páginas, consumo por `limits`) (D-86, D-88, D-89, D-91) | T004, T018 | - | `src/…/coleta/apify.py` | 🟢 (🟡 cota) | `[X]` |
| T021 | `coleta/roteador.py`: `ClienteRoteado` (entrega pelo `Requisicao.nivel`; `cookies` e `fechar` repassados; nível sem cliente = erro claro) (D-87) | T005, T018 | - | `src/…/coleta/roteador.py` | 🟢 | `[X]` |
| T022 | `Coletor` carimba o `nivel_coleta` do leiloeiro em cada requisição antes de enviar (D-87) | T005, T018 | - | `src/…/coleta/coletor.py` | 🟢 | `[X]` |
| T023 | Cadastro: `NIVEIS_IMPLEMENTADOS = ("script", "apify")`; campos `intervalo_horas` e `apify_ator` com validação; mensagem de "não implementado" atualizada (D-88, D-90, D-101) | T006, T020 | - | `src/…/config/leiloeiros.py` | 🟢 | `[X]` |
| T024 | Ambiente: `apify_token`, parâmetro `exigir_apify`, token em `segredos` (D-90) | T007 | `[//]` | `src/…/config/ambiente.py` | 🟢 | `[X]` |
| T025 | Sinônimos `m-benz` e `cintroen`; `jaguar` nas marcas conhecidas (D-95) | T010 | `[//]` | `src/…/parsing/marcas.py` | 🟢 | `[X]` |
| T026 | `coleta/milan.py`: `AdaptadorMilan` (filtro, leitura da agenda com data sem ano, escolha dos leilões, cursor de catálogos com anotações, detalhe) e registro (D-93, D-94, D-97) | T008 | `[//]` | `src/…/coleta/milan.py` | 🟢 | `[X]` |
| T027 | `parsing/milan.py`: `ParserMilan` (catálogo: veículos, marca, modelo, anos, km, câmbio, observações, sucata, lance inicial, pregão, pátio, vazia e quebra) e `aplicar_detalhe` (lances, estado, placa, câmbio) e registro (D-95 a D-97) | T009, T019, T025 | - | `src/…/parsing/milan.py` | 🟢 (🟡 pátio, retirado) | `[X]` |
| T028 | Enriquecimento: nível no detalhe pelo mapa leiloeiro → nível; revalidação `casa(lote, alvo)` depois do detalhe com a contagem `acima_do_teto` e log do motivo (D-87, D-98) | T011, T018 | - | `src/…/coleta/enriquecimento.py` | 🟢 | `[X]` |
| T029 | Banco: esquema versão 2 (`evento_visto`) em `db/migracoes.py` e repositório `db/eventos.py` (`registrar_evento`, leitura da antecedência) (D-102) | T012 | `[//]` | `src/…/db/eventos.py` | 🟢 | `[X]` |
| T030 | `RepositorioExecucoes.ultima_coleta_ok(leiloeiro_id)` (D-101) | T012 | `[//]` | `src/…/db/execucoes.py` | 🟢 | `[X]` |
| T031 | Relatório e lista: `LoteRelatorio.cambio` e a linha "Câmbio" preenchida quando houver (D-99) | T013, T019 | - | `src/…/notificacao/relatorio.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T032 | (RF-01, RF-02, RF-08) Orquestrador: registra `coleta.milan` e `parsing.milan`; `Dependencias.transporte_apify`; monta `ClienteRoteado` com `ClienteHTTP` e, se a varredura incluir leiloeiro em `apify`, `ClienteApify` (token exigido antes da rede); passa o mapa de níveis ao enriquecimento; `acima_do_teto` no log e nas contagens (D-87, D-90, D-98) | T015, T020, T021, T022, T023, T024, T026, T027, T028, T031 | - | `src/…/orquestrador.py` | 🟢 | `[ ]` |
| T033 | Orquestrador: seleção da varredura antes da coleta: `sem_pagos` pula níveis diferentes de `script` e `intervalo_horas` pula quem leu há pouco (`ultima_coleta_ok`); linhas "não incluído nesta varredura (sem pagos)" e "pulado pelo intervalo de H h (próxima leitura a partir de DD/MM HH:MM)" só na seção "Leiloeiros"; token só exigido se sobrar leiloeiro pago (D-100, D-101) | T016, T030, T032 | - | `src/…/orquestrador.py` | 🟢 | `[ ]` |
| T034 | Orquestrador: antecedência: grava `evento_visto` pelas anotações de evento e pregão (só execução normal; `na_semeadura` quando a busca está em semeadura); linha "leilão novo X, visto N dia(s) antes do pregão"; alerta quando há `intervalo_horas` e a antecedência é menor (D-102) | T017, T029, T033 | - | `src/…/orquestrador.py` | 🟢 | `[ ]` |
| T035 | (RF-06, RF-09) Orquestrador: linha de consumo do Apify na seção "Leiloeiros"; alertas por leiloeiro de token inválido, cota esgotada, tempo esgotado e plataforma indisponível, com o que fazer; alerta a 80% do ciclo, 1 por dia; desafio "via apify" pelo alerta de bloqueio existente (D-91, D-103) | T034 | - | `src/…/orquestrador.py` | 🟢 | `[ ]` |
| T036 | Linha de comando: opção `--sem-pagos` em `varrer`, repassada ao orquestrador; texto de ajuda (D-100) | T014, T033 | - | `src/…/cli.py` | 🟢 | `[ ]` |
| T037 | Atalhos: `scripts/varrer.bat` passa `--sem-pagos` (comentário explicando); `scripts/varrer-completo.bat` novo, igual ao atual sem a opção (D-100) | T036 | - | `scripts/varrer-completo.bat` | 🟢 | `[ ]` |
| T038 | (RF-01) Bloco do Milan em `config/leiloeiros.yaml` (data-delta §3.1, contrato citado no cabeçalho, `intervalo_horas` e `apify_ator` comentados); `APIFY_TOKEN` em `.env.example` com a origem do token | T032 | - | `config/leiloeiros.yaml` | 🟢 | `[ ]` |
| T039 | (RF-10) Dry-run real no container com o Milan pelo Apify: páginas e consumo no log, nenhuma chamada local ao Milan, nenhum alerta; varredura com os 5 leiloeiros abaixo de 10 minutos. Se a agenda não tiver leilão de financiamento no dia, registrar "busca vazia" nas Notas. Se falhar, `ativo: false` e registro nas Notas | T035, T038 | - | (execução) | 🟡 | `[ ]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T040 | README: Milan na tabela de leiloeiros; nível Apify (token, custo por página, consumo no relatório, alerta de 80%); atalhos `varrer.bat` e `varrer-completo.bat`; `intervalo_horas` | T037, T038 | `[//]` | `README.md` | 🟢 | `[ ]` |
| T041 | Seção "Feature 005" em `tests/RASTREABILIDADE.md` (RF, cenários e decisões D-86 a D-103 → testes), conferida mecanicamente | T035 | `[//]` | `tests/RASTREABILIDADE.md` | 🟢 | `[ ]` |
| T042 | Ajustar `onboarding.md` com o que o dry-run real mostrou (custo, tempo, textos das linhas do relatório) | T039 | `[//]` | `_reversa_forward/005-…/onboarding.md` | 🟢 | `[ ]` |
| T043 | Backlog: item novo "troca automática `script` → `apify`" (RF-07 adiado pela D-92, com o motivo: o ator só faz GET) e Milan movido para "Feitas" ao fim | - | `[//]` | `_reversa_forward/backlog.md` | 🟢 | `[ ]` |

## Notas de execução

- **Etapa 1 concluída (2026-10-14):** T001–T017. Suíte: 608 passando; 56 falhando e 5 módulos sem coletar (`test_coleta_apify`, `test_coleta_milan`, `test_coleta_roteamento`, `test_parsing_milan`, `test_repo_eventos`), à espera das etapas 2 e 3. Os 2 testes antigos de migração passaram a esperar o esquema 2.
- **T003 (2026-10-14):** `CenarioE2E` só passa `transporte_apify` quando `Dependencias` tiver o campo (até o T032); também ganhou `varrer(**opcoes)`, `relatorio()`, `lista()` e `alertas()`.
- **T009/T015 (2026-10-14):** o cenário 2 do requirements pede câmbio no resumo; o teste fixa o câmbio na 2ª linha do digest, depois do km, só quando o leiloeiro informa (`tests/test_digest.py`). Entra no T031 junto com o relatório.
- **T008 (2026-10-14):** o ano do pregão (agenda sem ano) usa o relógio do adaptador (`agora`); o T022 faz o `Coletor` entregar o próprio relógio aos adaptadores que tiverem esse atributo, para os testes não dependerem da data real.
- **T020 (2026-10-14):** as páginas liberadas do Milan contêm `challenge-platform` (script do Cloudflare que roda depois de liberar); o `ClienteApify` reconhece o desafio só por `Just a moment`, `cf-chl` e `Performing security verification`, ou status 403/503 do item. Contrato `interfaces/apify.md` §4 atualizado.
- **T022 (2026-10-14):** a preparação de sessão também sai pelo nível do leiloeiro (cliente que carimba o nível); o `Coletor` entrega o próprio relógio aos adaptadores com atributo `agora` (Milan: datas sem ano).
- **T028 (2026-10-14):** a revalidação usa o `casa(lote, alvo)` do motor; ponta a ponta do Kuss e do Freitas seguem verdes.
- **T031 (2026-10-14):** câmbio também na 2ª linha do resumo do Telegram, depois do km (cenário 2), além do relatório e da lista.
- **Etapa 2 concluída (2026-10-14):** T018–T031; 705 testes passando; 22 falhando (orquestrador e linha de comando: `test_e2e_milan`, `test_e2e_ritmo`, `test_e2e_apify_alertas`, `test_cli`), à espera da etapa 3.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-13 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-13 | Referências aos RF-11 a RF-14 e ao cenário 5 novo, depois do esclarecimento pós-audit | `/reversa-clarify` |
