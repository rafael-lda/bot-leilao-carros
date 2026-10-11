# Actions: Leiloeiro Copart

> Identificador: `003-leiloeiro-copart`
> Data: `2026-10-11`
> Roadmap: `_reversa_forward/003-leiloeiro-copart/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 32 |
| Paralelizáveis (`[//]`) | 26 |
| Maior cadeia de dependência | 9 (T001 → T003 → T012 → T024 → T025 → T026 → T027 → T029 → T032) |

Convenções: `src/bot_leilao/` é abreviado como `src/…`. Testes antes do núcleo (TDD); cada ação de núcleo termina quando os testes que a especificam passam; a suíte das features 001 e 002 tem de continuar verde ao fim de cada etapa.

Rede: só **T029** (dry-run real: ~17 requisições à Copart, além do Vip e do Kuss). As amostras de 2026-10-11 já são as fixtures; T002 só prepara o script para recapturar no futuro. Nenhum teste acessa a rede.

Política de escrita: `allowLegacyEdits: true`, `allowedPaths` vazio (liberação irrestrita, decidida pelo Rafael). Caminhos tocados: `src/**`, `tests/**`, `scripts/capturar_fixtures.py`, `config/leiloeiros.yaml`, `config/veiculos-alvo.yaml` (só o bloco do Duster; o arquivo tem edições locais do Rafael ainda não commitadas, que não podem ser perdidas), `README.md`.

| Etapa | Ações | Conteúdo |
|-------|-------|----------|
| 1 | T001 a T014 | Fixtures, simulador da Copart e testes |
| 2 | T015 a T023 | Bloqueio do Imperva, palavras a excluir, pátio e FIPE no núcleo, adaptador e parser da Copart |
| 3 | T024 a T032 | Saída, orquestrador, configuração, dry-run real e documentação |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Copiar as amostras de `_reversa_forward/003-…/amostras/` para `tests/fixtures/copart/`: `busca_pag00.json`, `busca_ultima.json`, `busca_zero.json`, `lotes_selecionados.json` | - | `[//]` | `tests/fixtures/copart/` | 🟢 | `[X]` |
| T002 | Acrescentar a `scripts/capturar_fixtures.py` o modo `--copart`: busca de financiamento ordenada (página 0 e última) e uma busca de zero resultados, com `currentHighBidder` trocado por `999999`, 5 s entre requisições. Não executar agora | - | `[//]` | `scripts/capturar_fixtures.py` | 🟢 | `[X]` |
| T003 | Em `tests/apoio.py`: `SiteCopart` (responde `GET /vehicleFinderSearch` e `POST /public/vehicleFinder/search` por `page`/`size` a partir de uma lista de lotes, com total configurável, página de desafio do Imperva com status 200 ou 403, ou falha de rede); roteamento do host `www.copart.com.br` no `CenarioE2E`; `LEILOEIRO_COPART`; fábrica `lote_copart(**campos)` a partir de um item real | T001 | `[//]` | `tests/apoio.py` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Cliente HTTP: corpo HTML com `_Incapsula_Resource`, `Incapsula incident` ou `Request unsuccessful` é `bloqueado` com motivo `desafio_antibot`, também com status 200; JSON normal que cite a palavra num campo não é bloqueio (D-60) | - | `[//]` | `tests/test_coleta_http.py` | 🟡 | `[X]` |
| T005 | Configuração de alvos: `excluir` como lista, como texto único (vira lista de um) e ausente (vazio); item vazio ou não textual aborta citando o alvo e o campo (RF-10, D-72) | - | `[//]` | `tests/test_config_veiculos.py` | 🟢 | `[X]` |
| T006 | Motor: com `excluir: [Oroch]`, "duster oroch" não casa e "duster" casa; exclusão pelo título quando o modelo não traz a palavra; sem acento e sem caixa; o lote excluído conta em `descartados_sem_casar`; outro alvo sem exclusão ainda casa com o mesmo lote (RF-10) | - | `[//]` | `tests/test_motor_criterios.py` | 🟢 | `[X]` |
| T007 | Adaptador Copart: registrado como `copart`; chaves de filtro aceitas e chave desconhecida aborta citando a Copart; lista de valores unida por vírgula; `preparar_sessao` faz `GET /vehicleFinderSearch`; requisição com `query=*`, `filter[condicao]=condicao:"FINANCIAMENTO"`, `sort=lot_number asc`, `page`, `size=100`, `start` e cabeçalhos XHR/Origin/Referer; próxima página enquanto `start + itens < total` e a página não vier vazia; lote repetido entre páginas gera aviso em log; `tipo_leilao_da_busca` → `financiamento`; `teto_paginas = 40` (D-53 a D-59) | T003 | `[//]` | `tests/test_coleta_copart.py` | 🟢 | `[X]` |
| T008 | Parser Copart com as fixtures reais: Duster Oroch 1141180 (id `copart:1141180`, link `/lotDetail/1141180`, título `RENAULT DUSTER OROCH 1.6 16V SCE`, marca `renault`, modelo `duster oroch`, anos, lance R$ 36.000, FIPE R$ 80.266, pregão 15/10/2026 08:30 Brasília, pátio, observações na ordem do D-66, tipo financiamento); Versa 1176233 aguardando classificação (preço, FIPE e pregão nulos, "Aguardando classificação da Copart (data, FIPE e lance a definir)", pátio "CAMPO GRANDE - MS"); Compre Agora (preço = `saleAmountBIN`, pregão nulo com "Copart Select", observação começa com "Compre Agora"); "LOCAL DO VENDEDOR" como pátio; `fv` (chassi) nunca vira FIPE; `currentHighBidder` nunca lido; página 0 com 100 lotes; zero resultados = vazia; `returnCode != 1`, falta de `data.results` ou lote sem `ln` levantam; `preco_obrigatorio = False` (D-61 a D-67) | T001 | `[//]` | `tests/test_parsing_copart.py` | 🟢 | `[X]` |
| T009 | Parser Vip: o lote da fixture real traz `patio = "SC"` (D-69) | - | `[//]` | `tests/test_parsing_vip.py` | 🟢 | `[X]` |
| T010 | Adaptador Kuss: `ler_agenda` devolve `local = "Curitiba - PR"`; as anotações das páginas `quantidade` e `lotes` levam `patio` (D-70) | - | `[//]` | `tests/test_coleta_claudio_kuss.py` | 🟢 | `[X]` |
| T011 | Parser Kuss: o lote recebe `patio` da anotação da página (D-70) | - | `[//]` | `tests/test_parsing_claudio_kuss.py` | 🟢 | `[X]` |
| T012 | Digest: 2ª linha com pátio e FIPE, na ordem preço — leiloeiro — km — pátio — FIPE — pregão; item sem pátio nem FIPE igual ao de hoje (D-71) | T003 | `[//]` | `tests/test_digest.py` | 🟢 | `[X]` |
| T013 | Relatório e lista: `- **Pátio:**`; `- **FIPE:** R$ 80.266 (lance = 45% da FIPE)`; sem lance, só o valor; sem FIPE, sem a linha (D-71) | T003 | `[//]` | `tests/test_relatorio.py` | 🟢 | `[X]` |
| T014 | (RF-03, RF-08) Ponta a ponta da Copart, os 5 cenários do requirements §7: leitura completa com total conferido (várias páginas); lote que casa avisado com pátio, FIPE e link; avisos do Vip, do Kuss e da Copart com pátio; Copart com desafio do Imperva não impede o aviso do Vip (sucesso parcial, alerta da Copart); JSON alterado gera alerta da Copart. Mais: Duster Oroch excluída pelo alvo; estreia da Copart lista os semeados nos documentos | T003 | `[//]` | `tests/test_e2e_copart.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T015 | Marcas do Imperva como desafio anti-robô, inclusive com status 200 quando o corpo é HTML (D-60) | T004 | `[//]` | `src/…/coleta/http.py` | 🟡 | `[ ]` |
| T016 | `VeiculoAlvo.excluir` com validação, e o campo documentado no exemplo de `veiculos-alvo.yaml` criado na primeira execução (D-72, D-73) | T005 | `[//]` | `src/…/config/veiculos.py` | 🟢 | `[ ]` |
| T017 | Exclusão no casamento do motor, pelo modelo e pelo título normalizados (D-72) | T006, T016 | - | `src/…/filtro/motor.py` | 🟢 | `[ ]` |
| T018 | `Lote.patio` e `Lote.fipe` (D-68) | - | `[//]` | `src/…/parsing/modelos.py` | 🟢 | `[ ]` |
| T019 | Parser Vip preenche `patio` com o "Local:" do card (D-69) | T009, T018 | `[//]` | `src/…/parsing/vip.py` | 🟢 | `[ ]` |
| T020 | `Evento.local` lido da agenda; anotação `patio` nas páginas `quantidade` e `lotes` (D-70) | T010 | `[//]` | `src/…/coleta/claudio_kuss.py` | 🟢 | `[ ]` |
| T021 | Parser Kuss preenche `patio` pela anotação (D-70) | T011, T018, T020 | - | `src/…/parsing/claudio_kuss.py` | 🟢 | `[ ]` |
| T022 | `coleta/copart.py`: `AdaptadorCopart` (filtros, sessão, requisição, paginação com conferência de total e de repetição, tipo, teto) e registro (D-53 a D-59) | T007 | `[//]` | `src/…/coleta/copart.py` | 🟢 | `[ ]` |
| T023 | `parsing/copart.py`: `ParserCopart` (lote normalizado, pátio, FIPE, data UTC → Brasília, observações, Compre Agora, vazia e quebra) e registro (D-61 a D-67) | T008, T018 | `[//]` | `src/…/parsing/copart.py` | 🟢 | `[ ]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T024 | `ItemDigest.patio` e `ItemDigest.fipe`; `item_de` e `_texto_item` (D-71) | T012, T018 | `[//]` | `src/…/notificacao/digest.py` | 🟢 | `[ ]` |
| T025 | `LoteRelatorio.patio` e `.fipe` (com % do lance); linhas no relatório e na lista (D-71) | T013, T024 | - | `src/…/notificacao/relatorio.py` | 🟢 | `[ ]` |
| T026 | Orquestrador registra `coleta.copart` e `parsing.copart`, e alerta bloqueio de um leiloeiro (1 por dia; ver Notas de execução) | T022, T023, T025, T014 | - | `src/…/orquestrador.py` | 🟢 | `[ ]` |
| T027 | (RF-01) Bloco da Copart em `config/leiloeiros.yaml`, com o contrato citado no cabeçalho | T026 | - | `config/leiloeiros.yaml` | 🟢 | `[ ]` |
| T028 | `excluir: [Oroch]` no alvo Renault Duster de `config/veiculos-alvo.yaml`, atualizando o comentário "descarte à mão"; mexer só nesse bloco, preservando as edições locais do Rafael (D-73) | T017 | `[//]` | `config/veiculos-alvo.yaml` | 🟢 | `[ ]` |
| T029 | (RF-02, RF-09) Dry-run real no container: Copart com total lido igual ao informado, sem aviso de repetição, sem alerta; Duster Oroch fora dos candidatos; pátio nos candidatos; varredura completa abaixo de 10 minutos. Se falhar, `ativo: false` e registro nas Notas | T027, T028 | - | (execução) | 🟡 | `[ ]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T030 | README: Copart na tabela de leiloeiros, pátio e FIPE no aviso, campo `excluir` nos veículos-alvo | T027 | `[//]` | `README.md` | 🟢 | `[ ]` |
| T031 | Seção "Feature 003" em `tests/RASTREABILIDADE.md`, conferida mecanicamente | T026 | `[//]` | `tests/RASTREABILIDADE.md` | 🟢 | `[ ]` |
| T032 | Ajustar `onboarding.md` com o que o dry-run real mostrou | T029 | `[//]` | `_reversa_forward/003-…/onboarding.md` | 🟢 | `[ ]` |

## Notas de execução

- **T014 (2026-10-11), lacuna achada ao escrever o teste:** o RF-07 promete alerta quando a Copart bloquear, mas o orquestrador só alertava quebra de parser e falha geral (todos os leiloeiros). Bloqueio de **um** leiloeiro virava só "sucesso parcial" no banco, sem aviso no Telegram, contra o princípio de não falhar em silêncio. Resolução: T026 passa a incluir um alerta de bloqueio por leiloeiro ("acesso bloqueado pelo site"), com o mesmo limite de 1 por dia por leiloeiro. A falha geral continua tendo prioridade (alerta único). Testes: `test_e2e_copart.py::test_copart_bloqueando_nao_impede_o_vip_e_gera_alerta`, `::test_alerta_de_bloqueio_no_maximo_um_por_dia`.
- **Etapa 1 concluída (2026-10-11):** 489 testes passando (488 anteriores + 1 novo que já vale); 38 falhando e 2 módulos de teste sem coletar, todos à espera das etapas 2 e 3.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-11 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-11 | Correções do `/reversa-audit` (A003, A004): RFs e D-73 citados nas ações | Claude |
