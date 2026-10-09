# Actions: MVP de Varredura Ponta a Ponta

> Identificador: `001-mvp-varredura-ponta-a-ponta`
> Data: `2026-10-03`
> Roadmap: `_reversa_forward/001-mvp-varredura-ponta-a-ponta/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 63 |
| Paralelizáveis (`[//]`) | 52 |
| Maior cadeia de dependência | 12 |

Convenções: `src/bot_leilao/` é abreviado como `src/…` nas descrições. A fase de testes vem **antes** do núcleo (TDD): cada módulo do núcleo depende do teste que o especifica. Cada ação de núcleo termina quando o teste correspondente passa. Nenhuma ação desta lista acessa a rede, **exceto T004**, que faz 4 requisições ao Vip, espaçadas em 5 s.

Antes da primeira ação que escreve fora das pastas do Reversa, o `.reversa/reversa-config.json` precisa ter sido liberado pelo Rafael (ver `roadmap.md` §5). Caminhos tocados: `src/**`, `tests/**`, `scripts/**`, `config/**` (criado em tempo de execução pelo programa, mas liberado para os arquivos de exemplo usados nos testes), `pyproject.toml`, `.env.example`, `.gitignore`, `README.md`.


## Fase 1, Preparação

<!-- Setup, scaffolding e evidência real do Vip. -->

Setup, scaffolding e evidência real do Vip.

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar `pyproject.toml`: pacote `bot_leilao` em layout `src/`, `requires-python >=3.12`, dependências `httpx`, `beautifulsoup4`, `lxml`, `PyYAML`, `python-dotenv`, extra `dev` com `pytest`; configuração do pytest | - | `[//]` | `pyproject.toml` | 🟢 | `[X]` |
| T002 | Acrescentar `dados/` ao `.gitignore` e criar `.env.example` com `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` sem valores e com comentários | - | `[//]` | `.env.example` | 🟢 | `[X]` |
| T003 | Criar o esqueleto do pacote: `src/bot_leilao/__init__.py` com a versão e `__main__.py` mínimo que chama `cli.principal()` | T001 | `[//]` | `src/bot_leilao/__init__.py` | 🟢 | `[X]` |
| T004 | Criar `scripts/capturar_fixtures.py` que, com sessão de cookies, limite de 3 redirecionamentos e 5 s entre requisições, grava em `tests/fixtures/vip/` a pesquisa filtrada (`procedencia=4`, `monta=1`) páginas 1 e última, uma busca de 1 resultado e uma busca de 0 resultados; executar uma vez e conferir os arquivos | T001 | `[//]` | `scripts/capturar_fixtures.py` | 🟢 | `[X]` |
| T005 | Criar `tests/conftest.py` com fixtures: raiz temporária com `config/` e `dados/`, banco SQLite temporário, leitor das fixtures HTML e fábrica de `httpx.MockTransport` | T003 | `[//]` | `tests/conftest.py` | 🟢 | `[X]` |

## Fase 2, Testes

<!-- Testes escritos antes do núcleo, um arquivo por componente, contra o contrato das specs e das interfaces. Falham até o núcleo existir. -->

Testes escritos antes do núcleo, um arquivo por componente, contra o contrato das specs e das interfaces. Falham até o núcleo existir.

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T006 | Testes de `normalizar_texto` e `gerar_id` (minúsculas, sem acento, hífens, estabilidade): `Vip Leilões` → `vip-leiloes`; `Citroën` → `citroen` | T005 | `[//]` | `tests/test_texto.py` | 🟢 | `[X]` |
| T007 | Testes do filtro de mascaramento: token e credenciais substituídos por `***` em mensagem, argumentos e rastreamento de exceção | T005 | `[//]` | `tests/test_logsetup.py` | 🟢 | `[X]` |
| T008 | Testes de leitura de YAML: UTF-8 com e sem BOM, CRLF, sintaxe inválida citando a linha, arquivo ausente criando exemplo comentado com tudo `ativo: false` e abortando, arquivo existente nunca reescrito; conteúdo dos exemplos conforme `interfaces/arquivos-configuracao.md` §2 e §3, com a busca ampla do Vip sem filtro de marca (D-29) | T005 | `[//]` | `tests/test_config_arquivos.py` | 🟢 | `[X]` |
| T009 | Testes de `veiculos-alvo.yaml`: RF-01 e RF-16 da feature (`quilometragem_maxima` opcional), `ano_min > ano_max`, preço ≤ 0, `tipos_leilao` inválido listando os cinco aceitos, duplicata com aviso, `ativo` omitido, todos os alvos inativos geram aviso e término com sucesso, e não erro (RF-01, A006), id estável; toda mensagem cita alvo e campo | T005 | `[//]` | `tests/test_config_veiculos.py` | 🟢 | `[X]` |
| T010 | Testes de `leiloeiros.yaml`: filtros não vazios e escalares, `base_url` `http` rejeitada, sem buscas, chave de filtro desconhecida, leiloeiro ativo sem adaptador ou sem parser registrado (EC-11, RF-10 v1.3), ativo `logado` ou `nivel_coleta` pago abortando (D-17), `frequencia` opaca, ids de leiloeiro e de busca estáveis e insensíveis à ordem das chaves, duplicata com aviso | T005 | `[//]` | `tests/test_config_leiloeiros.py` | 🟢 | `[X]` |
| T011 | Testes do `.env`: token e chat id ausentes, vazios ou malformados abortam antes da rede; variável exportada vence o `.env`; `--dry-run` dispensa as variáveis do Telegram | T005 | `[//]` | `tests/test_ambiente.py` | 🟢 | `[X]` |
| T012 | Testes de conexão e migrações: pragmas (`foreign_keys`, `busy_timeout`), criação das cinco tabelas e índices em `user_version = 1`, idempotência, `user_version` maior que o conhecido aborta | T005 | `[//]` | `tests/test_db_migracoes.py` | 🟡 | `[X]` |
| T013 | Testes da trava: aquisição exclusiva, segunda aquisição recusada, trava com mais de 2 h tratada como órfã e liberada com registro, liberação no `finally` | T005 | `[//]` | `tests/test_trava.py` | 🟡 | `[X]` |
| T014 | Testes do repositório de lotes: consulta por `id_canonico`, gravação em transação única, `origem` notificacao/semeadura, `busca_semeada`, colisão de id tratada como já conhecido (EC-09 do motor), consulta de dedup < 1 s com 50.000 registros | T005 | `[//]` | `tests/test_repo_lotes.py` | 🟢 | `[X]` |
| T015 | Testes do repositório de execuções: abrir, fechar com contagens, registro de execução recusada e de falha, `execucao_leiloeiro`, `execucao_busca`, consulta de alerta já enviado no dia (D-22) | T005 | `[//]` | `tests/test_repo_execucoes.py` | 🟡 | `[X]` |
| T016 | Testes do cliente HTTP com `MockTransport`: timeout de 30 s, limite de 3 redirecionamentos (`laco_redirecionamento`), 3 tentativas com espera crescente, `429` com `Retry-After`, 403/429/desafio Cloudflare = `bloqueado`, 5xx e timeout = `falha_rede`, intervalo mínimo de 5 s entre requisições ao mesmo host, resposta acima de 20 MB abortada; toda requisição leva o `User-Agent` de navegador e `Accept-Language: pt-BR`, nunca o padrão `python-httpx` (D-30) | T005 | `[//]` | `tests/test_coleta_http.py` | 🟢 | `[X]` |
| T017 | Testes do coletor: sessão preparada uma vez por leiloeiro, paginação até o adaptador indicar fim, teto de 50 páginas (`teto_paginas`), busca atômica (falha na página 2 entrega nada, RF-15), isolamento entre buscas, leiloeiro sem adaptador, registro por busca com `nivel_usado = script` | T005 | `[//]` | `tests/test_coletor.py` | 🟢 | `[X]` |
| T018 | Testes do adaptador `vip-leiloes`: tradução de `procedencia`, `monta`, `marca` etc. em campos `Filtro.*`, campos fixos, página 1 e N, chave desconhecida recusada, lista recusada, próxima página lida da marcação das fixtures, verificação cruzada do total; `tipo_leilao_da_busca` traduz `procedencia: 4` em `financiamento` e devolve nulo para os demais (D-15) | T005, T004 | `[//]` | `tests/test_coleta_vip.py` | 🟢 | `[X]` |
| T019 | Testes dos normalizadores: `R$ 45.000,00` → `45000.00`, `2018/2019` → fabricação 2018 e modelo 2019, ano único preenche os dois, `228.227 Km` → `228227`, ano `0000` → nulo, preço `Sob consulta` → nulo com texto preservado, link relativo → absoluto | T005 | `[//]` | `tests/test_normalizadores.py` | 🟢 | `[X]` |
| T020 | Testes da tabela comum de sinônimos de marca: `mmc` → `mitsubishi`, `gm` → `chevrolet`, `vw` → `volkswagen`, ampliação por parser, marca desconhecida passa como veio com registro em log | T005 | `[//]` | `tests/test_marcas.py` | 🟢 | `[X]` |
| T021 | Testes do núcleo de parsing: seleção de parser por leiloeiro, sinal de quebra com conteúdo não vazio e zero lotes (RF-07), quebra acima de 30% de lotes incompletos (RF-08), descarte de lote sem link ou id, exceção isolada por busca, duplicata na mesma busca mantida uma vez, conteúdo vazio não é quebra; página com marcador de busca vazia não é quebra, e página sem cards e sem o marcador é quebra (D-31) | T005 | `[//]` | `tests/test_parsing_nucleo.py` | 🟢 | `[X]` |
| T022 | Testes do parser `vip-leiloes` contra as fixtures reais: 12 lotes por página, todos os campos de RF-05, id `vip-leiloes:<id do anúncio>`, `tipo_leilao` herdado da busca, marca traduzida, `retirado` por HTML sintético com "Retirado", `situacao` desconhecida registrada em log; fixture de 0 resultados devolve lista vazia sem sinal de quebra (D-31) | T005, T004 | `[//]` | `tests/test_parsing_vip.py` | 🟢 | `[X]` |
| T023 | Testes dos critérios do motor: ano de modelo com extremos, lance corrente com recurso ao inicial, preço ausente não elimina, ano ausente elimina, teto de km opcional (RF-16), km ausente não elimina (D-19), tipo de leilão, marca e modelo por conteúdo sem acento, descarte de retirados antes da filtragem (RF-17), lote casando dois alvos gera um candidato; exemplos de 41.900 e 52.000 do requirements | T005 | `[//]` | `tests/test_motor_criterios.py` | 🟢 | `[X]` |
| T024 | Testes do fluxo do motor: deduplicação, semeadura por busca só com coleta `ok` e sem quebra (D-20), busca nova após mudar filtros semeia de novo, contagens de RF-12, lotes notificados gravados só após confirmação e em transação única | T005 | `[//]` | `tests/test_motor_fluxo.py` | 🟢 | `[X]` |
| T025 | Testes do digest e do alerta: cabeçalho com data e contagem, itens com marca, modelo, ano de modelo, preço, km, leiloeiro e link, "Preço a confirmar", escape de `<`, `>` e `&`, divisão em blocos de 3800 caracteres sem cortar item, formato do alerta | T005 | `[//]` | `tests/test_digest.py` | 🟢 | `[X]` |
| T026 | Testes do envio ao Telegram com `MockTransport`: sucesso só com `ok: true`, 3 tentativas com espera crescente, `429` com `retry_after`, `401`/`400`/`403` sem retry e com mensagem distinta, confirmação só após o último bloco, token ausente do log em falha, espera de 1 s entre blocos do mesmo digest | T005 | `[//]` | `tests/test_telegram.py` | 🟢 | `[X]` |
| T062 | Testes do aviso de coerência entre alvos e buscas: alvo ativo cujo `tipos_leilao` não contém nenhum tipo produzido pelas buscas ativas gera aviso citando o alvo, os tipos aceitos e os produzidos; busca de tipo nulo não entra na conta; o aviso nunca aborta (A004) | T005 | `[//]` | `tests/test_config_coerencia.py` | 🟡 | `[X]` |

## Fase 3, Núcleo

<!-- Lógica de cada componente, ordenada pela dependência. -->

Lógica de cada componente, ordenada pela dependência.

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T027 | Implementar `normalizar_texto` e `gerar_id` | T006 | - | `src/bot_leilao/texto.py` | 🟢 | `[X]` |
| T028 | Implementar `logsetup`: log em console e `dados/logs/bot-leilao.log` com rotação de 1 MB e 5 arquivos, e filtro que mascara valores de segredos, inclusive em exceções | T007 | `[//]` | `src/bot_leilao/logsetup.py` | 🟢 | `[X]` |
| T029 | Implementar leitura segura de YAML e criação dos arquivos de exemplo comentados, com o conteúdo de `interfaces/arquivos-configuracao.md` | T008 | `[//]` | `src/bot_leilao/config/arquivos.py` | 🟢 | `[X]` |
| T030 | Implementar o carregamento e a validação de `veiculos-alvo.yaml` com `VeiculoAlvo`, id estável e avisos | T009, T029, T027 | `[//]` | `src/bot_leilao/config/veiculos.py` | 🟢 | `[X]` |
| T031 | Implementar o carregamento e a validação de `leiloeiros.yaml` com `Leiloeiro`, `Busca`, ids estáveis e consulta aos registros de adaptadores e de parsers recebidos como parâmetro | T010, T029, T027 | `[//]` | `src/bot_leilao/config/leiloeiros.py` | 🟢 | `[X]` |
| T032 | Implementar o carregamento do `.env` e a validação de `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`, expondo a lista de valores a mascarar | T011 | `[//]` | `src/bot_leilao/config/ambiente.py` | 🟢 | `[X]` |
| T033 | Implementar a conexão SQLite com os pragmas e o timeout de bloqueio | T012 | `[//]` | `src/bot_leilao/db/conexao.py` | 🟢 | `[X]` |
| T034 | Implementar as migrações por `user_version`, versão 1 com as cinco tabelas e índices de `data-delta.md` | T012, T033 | - | `src/bot_leilao/db/migracoes.py` | 🟢 | `[X]` |
| T035 | Implementar a trava de execução por arquivo exclusivo com PID, instante e regra de órfã de 2 h | T013 | `[//]` | `src/bot_leilao/db/trava.py` | 🟡 | `[X]` |
| T036 | Implementar o repositório de `lote_conhecido` e `busca_semeada` | T014, T034 | `[//]` | `src/bot_leilao/db/lotes.py` | 🟢 | `[X]` |
| T037 | Implementar o repositório de `execucao`, `execucao_leiloeiro` e `execucao_busca`, com a consulta de alerta já enviado no dia | T015, T034 | `[//]` | `src/bot_leilao/db/execucoes.py` | 🟡 | `[X]` |
| T038 | Implementar os modelos do coletor: `RespostaBruta`, `Pagina`, `Veredito` e o protocolo `Adaptador` | T016 | `[//]` | `src/bot_leilao/coleta/modelos.py` | 🟢 | `[X]` |
| T039 | Implementar o registro de adaptadores por `leiloeiro_id`, com listagem dos nomes disponíveis | T038 | - | `src/bot_leilao/coleta/registro.py` | 🟢 | `[X]` |
| T040 | Implementar o cliente HTTP: sessão com cookies, redirecionamentos, timeout, retry com espera crescente, classificação de veredito, espaçamento entre requisições e limite de tamanho, com os cabeçalhos de navegador definidos num único ponto (D-30) | T016, T038 | `[//]` | `src/bot_leilao/coleta/http.py` | 🟢 | `[X]` |
| T041 | Implementar o coletor: preparação de sessão por leiloeiro, paginação com teto, busca atômica, isolamento entre buscas e registro por busca | T017, T040, T039 | - | `src/bot_leilao/coleta/coletor.py` | 🟢 | `[X]` |
| T042 | Implementar o adaptador `vip-leiloes` conforme `interfaces/vip-pesquisa.md` e registrá-lo | T018, T039 | `[//]` | `src/bot_leilao/coleta/vip.py` | 🟢 | `[X]` |
| T043 | Implementar os modelos de parsing: `Lote` com `quilometragem`, `situacao`, `retirado` e `ResultadoParsing` | T021 | `[//]` | `src/bot_leilao/parsing/modelos.py` | 🟢 | `[X]` |
| T044 | Implementar os normalizadores de preço, ano, quilometragem e link | T019, T027 | `[//]` | `src/bot_leilao/parsing/normalizadores.py` | 🟢 | `[X]` |
| T045 | Implementar a tabela comum de sinônimos de marca e a função de tradução | T020, T027 | `[//]` | `src/bot_leilao/parsing/marcas.py` | 🟢 | `[X]` |
| T046 | Implementar o núcleo de parsing: registro de parsers, detecção de quebra, descartes, isolamento de falha e deduplicação por busca, com a regra de zero resultados legítimos (D-31) | T021, T043 | - | `src/bot_leilao/parsing/nucleo.py` | 🟢 | `[X]` |
| T047 | Implementar o parser `vip-leiloes` e registrá-lo | T022, T044, T045, T043, T046 | - | `src/bot_leilao/parsing/vip.py` | 🟢 | `[X]` |
| T048 | Implementar os critérios do motor de filtros, incluindo km opcional, retirados e preço ou km ausentes | T023, T043, T030, T027 | `[//]` | `src/bot_leilao/filtro/motor.py` | 🟢 | `[X]` |
| T049 | Implementar o fluxo do motor: deduplicação, semeadura, contagens e gravação pós-confirmação | T024, T048, T036 | - | `src/bot_leilao/filtro/fluxo.py` | 🟢 | `[X]` |
| T050 | Implementar a formatação do digest e do alerta, com escape HTML e divisão em blocos | T025, T043 | `[//]` | `src/bot_leilao/notificacao/digest.py` | 🟢 | `[X]` |
| T051 | Implementar o envio ao Telegram com retry, tratamento por código de resposta e confirmação e espera de 1 s entre blocos | T026, T050, T032 | - | `src/bot_leilao/notificacao/telegram.py` | 🟢 | `[X]` |
| T063 | Implementar o aviso de coerência entre alvos e buscas, recebendo a função de tipo da busca de cada adaptador como parâmetro | T030, T031, T062 | `[//]` | `src/bot_leilao/config/coerencia.py` | 🟡 | `[X]` |

## Fase 4, Integração

<!-- Cola dos componentes, CLI e os cenários de aceitação ponta a ponta. -->

Cola dos componentes, CLI e os cenários de aceitação ponta a ponta.

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T052 | Implementar o alerta operacional com limite de 1 por dia por leiloeiro e o alerta único de falha geral, consultando `execucao_leiloeiro.alerta_enviado` | T050, T051, T037 | `[//]` | `src/bot_leilao/notificacao/alertas.py` | 🟡 | `[X]` |
| T053 | Implementar o orquestrador: trava, banco, `INSERT execucao`, configuração, coleta, parsing, filtragem, notificação e `UPDATE execucao` em `finally`; modo `dry_run`; vereditos `sucesso`, `sucesso_parcial`, `falha` e `recusada` | T028, T030, T031, T032, T035, T037, T041, T042, T046, T047, T049, T051, T052, T063 | - | `src/bot_leilao/orquestrador.py` | 🟡 | `[X]` |
| T054 | Implementar a CLI com `varrer [--dry-run] [--raiz]` e `testar-telegram [--raiz]` e os códigos de saída de `interfaces/cli.md` | T053 | - | `src/bot_leilao/cli.py` | 🟢 | `[X]` |
| T055 | Testes de ponta a ponta dos cenários 1 a 4 do requirements: semeadura sem notificar, lote novo gera digest, lote acima do teto, execução repetida não renotifica | T053 | `[//]` | `tests/test_e2e_fluxo.py` | 🟢 | `[X]` |
| T056 | Testes de ponta a ponta dos cenários 5 a 8: parser quebrado avisa, falha no envio preserva lotes, configuração inválida aborta antes da rede, bloqueio distinto de falha de rede | T053 | `[//]` | `tests/test_e2e_falhas.py` | 🟢 | `[X]` |
| T057 | Testes de ponta a ponta dos cenários 9 a 11: cadastro de leiloeiro inválido, falha total de rede registrada com encerramento, segunda execução recusada | T053 | `[//]` | `tests/test_e2e_robustez.py` | 🟢 | `[X]` |
| T058 | Testes da CLI: códigos de saída 0, 1, 2 e 3, `--dry-run` sem envio e sem gravar `lote_conhecido`, `testar-telegram` | T054 | `[//]` | `tests/test_cli.py` | 🟢 | `[X]` |

## Fase 5, Polimento

<!-- Segurança comprovada, rastreabilidade e documentação curta. -->

Segurança comprovada, rastreabilidade e documentação curta.

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T059 | Teste de segurança: forçar exceção do `httpx` com a URL do bot no rastreamento e verificar que o token não aparece no log nem na saída; varrer o log de uma execução completa em busca de valores do `.env` | T053, T028 | `[//]` | `tests/test_seguranca.py` | 🟢 | `[X]` |
| T060 | Criar a matriz de rastreabilidade RF-01 a RF-18 e dos 11 cenários para os arquivos de teste, e conferir que nenhum requisito ficou sem teste | T055, T056, T057, T058, T059 | - | `tests/RASTREABILIDADE.md` | 🟢 | `[X]` |
| T061 | Criar `README.md` curto: o que é, instalação, os comandos, estrutura de pastas e ponteiro para `onboarding.md` | T054 | `[//]` | `README.md` | 🟢 | `[X]` |

## Emendas

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| E001 | Relatório Markdown por varredura real em `1OUTPUT/` (data, hora, veredito, duração, lotes novos com alvo e teto); nunca sobrescreve; fora do git; falha ao gravar não derruba a varredura | - | - | `src/bot_leilao/notificacao/relatorio.py` | 🟢 | `[X]` |
| E002 | Lista acumulada `1OUTPUT/lotes-a-monitorar.md`: o bot só acrescenta os lotes avisados (após confirmação do Telegram), sem repetir; regras de manutenção no topo para o Rafael e os agentes | E001 | - | `src/bot_leilao/notificacao/relatorio.py` | 🟢 | `[X]` |
| E003 | Regras da lista de monitoramento orientam a identificar e anotar reaparições (mesmo carro, outro número de anúncio) por modelo, ano, km e final de placa | E002 | - | `src/bot_leilao/notificacao/relatorio.py` | 🟢 | `[X]` |

## Notas de execução

- **Etapa 9 do roadmap (execução real contra o Vip, com o Telegram do Rafael) não é uma ação de código.** É o passo a passo de `onboarding.md`, conduzido pelo Rafael depois que todas as ações estiverem `[X]`. Depende de o Rafael preencher os valores do primeiro veículo-alvo (`requirements.md` §10).
- `[//]` indica ações que não compartilham arquivo alvo nem dependência entre si **dentro da mesma leva**. Na fase 2, todos os testes são paralelizáveis entre si depois de T005; na fase 3, o paralelismo existe entre módulos de componentes diferentes.
- Revisão futura que remover uma ação não reaproveita o ID.

### Registro da codificação

- **Etapa 1 (2026-10-04):** T001–T026 e T062 concluídas. Os testes da fase 2 falhavam na coleta por `ModuleNotFoundError` até o núcleo existir, como esperado em TDD. O contrato entre testes e núcleo está resumido em `api-interna.md`.
- **Achado na captura das fixtures (T004):** a busca sem resultados do Vip devolve `div.filter-wait` com "Nenhum lote encontrado." e **sem** `#resultadosEncontrados`. A D-31 foi ajustada antes dos testes (roadmap, `vip-pesquisa.md`, `parser-lotes` EC-15).
- **Ajuste de desenho (T016):** espera entre tentativas de 5 s e 15 s para leiloeiros, porque 2 s e 4 s ficariam abaixo do intervalo mínimo de 5 s por host. O Telegram mantém 2 s e 4 s.
- **`data=` do httpx** exige dicionário: `Requisicao.dados` é `dict`, e o Vip não usa múltipla escolha.
- **Etapa 2 (2026-10-04):** T027–T051 e T063 concluídas; 302 testes passando, sem acesso à rede.
- **Ajuste (T036):** `INSERT OR IGNORE` do SQLite engole também violações de CHECK; o repositório usa `ON CONFLICT (...) DO NOTHING`, que só ignora a chave duplicada (o teste de atomicidade pegou isso).
- **Ajuste (T048):** o motor traduz sinônimos de marca sem registrar em log, para não repetir o aviso de marca desconhecida a cada combinação lote × alvo; o registro fica no parser.
- **Etapa 3 (2026-10-04):** T052–T061 concluídas; 339 testes passando, sem acesso à rede. Os 11 cenários do requirements passam de ponta a ponta.
- **Vazamento corrigido (T059):** o motivo de um erro inesperado ia para `execucao.motivo` com o texto da exceção; se contivesse o token, ele ficaria no SQLite. Todo texto gravado no banco passa pelo mascaramento de segredos, e o teste de segurança cobre console, arquivo de log e banco.
- **Execução real em `--dry-run` contra o Vip (2026-10-04):** 17 páginas, 201 lotes, 0 descartados, sem quebra, 1min31s. O Vip devolveu um `429` sem `Retry-After` na 17ª requisição a 5 s de intervalo; resolvido na tentativa seguinte. Decisão: em `429` sem `Retry-After`, esperar 30 s (`ClienteHTTP.espera_429`), mantendo o intervalo de 5 s. Responde em parte à OQ-02 do `coletor-lotes`; acompanhar a frequência de `429` nas primeiras semanas.
- **Mensagem do dry-run (T053):** o log dizia "registrado(s) como conhecido(s)" mesmo sem gravar; agora diz "seriam registrados (dry-run)".
- **Ajuste pós-entrega (2026-10-05, D-32):** km `0` ou ≥ 900.000 passa a valer "não informada" (`parsing/normalizadores.py`), para que o teto `quilometragem_maxima` não esconda carros sem km. 349 testes passando. Registrado fora das ações T001–T063, que seguem todas `[X]`.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-03 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-04 | Codificação concluída em três etapas: 63 ações `[X]` | reversa-coding |
| 2026-10-05 | Notas de execução das três etapas registradas; ajuste D-32 (km sentinela) | reversa-coding |
| 2026-10-03 | Correções do `audit/cross-check.md`: T062 e T063 novas (A004); descrições de T008, T009, T010, T016, T018, T021, T022, T026, T029, T031, T040, T046, T051 ajustadas (A001, A002, A003, A005, A006, A007); T053 passa a depender de T063 | reversa-forward |
