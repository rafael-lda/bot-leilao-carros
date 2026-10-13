# Actions: Leiloeiro Freitas

> Identificador: `004-leiloeiro-freitas`
> Data: `2026-10-13`
> Roadmap: `_reversa_forward/004-leiloeiro-freitas/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 20 |
| Paralelizáveis (`[//]`) | 16 |
| Maior cadeia de dependência | 8 (T001 → T004 → T006 → T012 → T014 → T016 → T017 → T020) |

Convenções: `src/bot_leilao/` é abreviado como `src/…`. Testes antes do núcleo (TDD); a suíte anterior continua verde ao fim de cada etapa.

Rede: só **T017** (dry-run real). As amostras de 2026-10-13 são as fixtures; T003 só prepara o script de recaptura. Nenhum teste acessa a rede.

Política de escrita: `allowLegacyEdits: true`, `allowedPaths` vazio (liberação irrestrita). Caminhos tocados: `src/**`, `tests/**`, `scripts/capturar_fixtures.py`, `config/leiloeiros.yaml`, `pyproject.toml`, `README.md`.

| Etapa | Ações | Conteúdo |
|-------|-------|----------|
| 1 | T001 a T009 | Fixtures, certificado e runbook no lugar, simulador do Freitas e testes |
| 2 | T010 a T013 | Certificados no cliente HTTP, sinônimo, adaptador e parser do Freitas |
| 3 | T014 a T020 | Orquestrador (registro e alerta de certificado), empacotamento, configuração, dry-run real e documentação |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Copiar as amostras para `tests/fixtures/freitas/`: `cards_selecionados.html`, `lotes_pag2.html`, `lotes_fim.html`, `detalhe_8112_1.html`, `detalhe_8103_3.html`, `detalhe_8111_700.html` | - | `[//]` | `tests/fixtures/freitas/` | 🟢 | `[ ]` |
| T002 | Criar `src/…/coleta/certificados/` com o intermediário oficial (`globalsign-gcc-r6-alphassl-ca-2025.pem`, conferindo a impressão digital do contrato) e o `LEIA-ME.md` com o texto de `runbook-certificado.md` (D-83, D-85) | - | `[//]` | `src/…/coleta/certificados/` | 🟢 | `[ ]` |
| T003 | Modo `--freitas` em `scripts/capturar_fixtures.py` (busca "inteiros" página 2 e fim, detalhe de um lote), usando o intermediário da pasta de certificados; não executar | - | `[//]` | `scripts/capturar_fixtures.py` | 🟢 | `[ ]` |
| T004 | Em `tests/apoio.py`: `SiteFreitas` (busca por `PageNumber`/`TopRows` sobre uma lista de cards, mensagem de fim, detalhe por `leilaoId`/`loteNumero`, bloqueio, e erro de certificado simulado com a mensagem `CERTIFICATE_VERIFY_FAILED`); roteamento do host no `CenarioE2E`; `LEILOEIRO_FREITAS` | T001 | `[//]` | `tests/apoio.py` | 🟢 | `[ ]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | (RF-05) Cliente HTTP: o contexto TLS carrega o pacote `certifi` e os `.pem` da pasta de certificados (o intermediário GCC R6 AlphaSSL 2025 aparece entre as autoridades); erro de verificação vira motivo `certificado: <host>` com **uma** tentativa; nenhum arquivo de `src/` contém `verify=False` (D-83, D-84) | - | `[//]` | `tests/test_coleta_http.py` | 🟢 | `[ ]` |
| T006 | (RF-01, RF-02) Adaptador Freitas: registrado como `freitas-leiloeiro`; mapa de filtros e chave desconhecida aborta citando o Freitas; `preparar_sessao` nenhuma; requisição `GET /Leiloes/PesquisarLotes` com os parâmetros do contrato, `TopRows=200`, `PageNumber` e cabeçalhos XHR/Referer; continua enquanto vierem cards e **para só na mensagem de fim** (página com menos de 200 não encerra); lote repetido entre páginas gera aviso; `tipo_leilao_da_busca` → `financiamento`; `requisicao_detalhe` = GET do link (D-74 a D-78, D-82) | T004 | `[//]` | `tests/test_coleta_freitas.py` | 🟢 | `[ ]` |
| T007 | (RF-03, RF-04, RF-06) Parser Freitas com os cards reais: Duster 8112/1 (id `freitas-leiloeiro:8112-1`, link, número `001`, título `RENAULT/DUSTER INTP CVT`, marca `renault`, modelo `duster intp cvt`, anos 2023/2024, maior lance R$ 50.500, pregão 16/10/2026 10:00, placa `S__-___4`, tipo `financiamento`); `I/NISSAN SENTRA 20S FLEX` → `nissan` / `sentra 20s flex`; `M.BENZ` → `mercedes-benz`; "Lance Inicial" → `lance_inicial`; sem etiqueta → tipo nulo; "EM LOTEAMENTO" não devolvido e contado no log; página de fim = vazia; HTML sem cards e sem fim → exceção. Detalhe: 8112/1 pátio `SANTO ANDRE - SP` e despesas R$ 2.350; 8103/3 selo "IPVA 2026 PAGO" e pátio `SANTA BARBARA D OESTE - SP`; 8111/700 despesas R$ 2.700 com a composição (operacionais + logística) nas observações (D-76 a D-82) | T001 | `[//]` | `tests/test_parsing_freitas.py` | 🟢 | `[ ]` |
| T008 | Sinônimo `m.benz` → `mercedes-benz` (D-79) | - | `[//]` | `tests/test_marcas.py` | 🟢 | `[ ]` |
| T009 | (RF-07, RF-08) Ponta a ponta do Freitas, os 5 cenários do requirements: leitura até a mensagem de fim sem repetição; lote de financeira que casa avisado com pátio, pregão e link; lote sem etiqueta não avisado; cadeia completada (o bot conecta pelo contexto com o intermediário: verificado no T005; aqui, a busca simulada é lida); Freitas bloqueando não derruba o Vip e gera alerta. Mais: falha de certificado gera alerta que cita `coleta/certificados/LEIA-ME.md`; estreia lista os semeados com pátio e despesas | T004 | `[//]` | `tests/test_e2e_freitas.py` | 🟢 | `[ ]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T010 | Contexto TLS do `ClienteHTTP` com `certifi` + `.pem` da pasta de certificados; erro `CERTIFICATE_VERIFY_FAILED` → motivo `certificado: <host>`, sem novas tentativas (D-83, D-84) | T005, T002 | `[//]` | `src/…/coleta/http.py` | 🟢 | `[ ]` |
| T011 | Sinônimo `m.benz` na tabela comum (D-79) | T008 | `[//]` | `src/…/parsing/marcas.py` | 🟢 | `[ ]` |
| T012 | `coleta/freitas.py`: `AdaptadorFreitas` (filtros, requisição, paginação até a mensagem de fim, aviso de repetição, tipo, detalhe) e registro (D-74 a D-78, D-82) | T006 | `[//]` | `src/…/coleta/freitas.py` | 🟢 | `[ ]` |
| T013 | `parsing/freitas.py`: `ParserFreitas` (cards, em loteamento ignorado, vazia e quebra) e `aplicar_detalhe` (pátio, despesas com composição, selos, retirado) e registro (D-76 a D-82) | T007, T011 | - | `src/…/parsing/freitas.py` | 🟢 | `[ ]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T014 | (RF-08) Orquestrador: registra `coleta.freitas` e `parsing.freitas`; o alerta por leiloeiro cobre também motivo `certificado`, com o texto apontando `src/bot_leilao/coleta/certificados/LEIA-ME.md`; a seção "Leiloeiros" do relatório mostra "falha de acesso (certificado: <host>)", como no runbook (D-85) | T012, T013, T009, T010 | - | `src/…/orquestrador.py` | 🟢 | `[ ]` |
| T015 | `pyproject.toml`: os `.pem` e o `LEIA-ME.md` da pasta de certificados entram como dados do pacote (instalação não editável) | T002 | `[//]` | `pyproject.toml` | 🟡 | `[ ]` |
| T016 | (RF-01) Bloco do Freitas em `config/leiloeiros.yaml` (data-delta §3), com o contrato citado no cabeçalho | T014 | - | `config/leiloeiros.yaml` | 🟢 | `[ ]` |
| T017 | (RF-02, RF-09) Dry-run real no container: Freitas lido até a mensagem de fim, sem repetição e sem alerta; contagem de lotes em loteamento no log; varredura com os 4 leiloeiros abaixo de 10 minutos. Se falhar, `ativo: false` e registro nas Notas | T016 | - | (execução) | 🟡 | `[ ]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T018 | README: Freitas na tabela de leiloeiros; pasta de certificados e o runbook | T016 | `[//]` | `README.md` | 🟢 | `[ ]` |
| T019 | Seção "Feature 004" em `tests/RASTREABILIDADE.md`, conferida mecanicamente | T014 | `[//]` | `tests/RASTREABILIDADE.md` | 🟢 | `[ ]` |
| T020 | Ajustar `onboarding.md` com o que o dry-run real mostrou | T017 | `[//]` | `_reversa_forward/004-…/onboarding.md` | 🟢 | `[ ]` |

## Notas de execução

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-13 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-10-13 | Correção do `/reversa-audit` (A007): texto da seção "Leiloeiros" alinhado ao runbook | Claude |
