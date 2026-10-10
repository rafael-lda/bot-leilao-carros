# Actions: Leiloeiro Claudio Kuss

> Identificador: `002-leiloeiro-claudio-kuss`
> Data: `2026-10-10`
> Roadmap: `_reversa_forward/002-leiloeiro-claudio-kuss/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 34 |
| Paralelizáveis (`[//]`) | 22 |
| Maior cadeia de dependência | 11 (T001 → T003 → T004 → T017 → T019 → T024 → T025 → T029 → T030 → T031 → T034) |

Convenções: `src/bot_leilao/` é abreviado como `src/…`; "o Kuss" é o Claudio Kuss Leilões (`claudio-kuss-leiloes`). Como na 001, os testes vêm **antes** do núcleo (TDD) e cada ação de núcleo termina quando os testes que a especificam passam. Toda a suíte da 001 tem de continuar verde ao fim de cada etapa: o Vip é a regressão a vigiar.

Rede: só **T002** (cerca de 8 requisições ao Kuss, 5 s entre elas, **antes do pregão de 13/10/2026**, porque depois os lotes mudam) e **T031** (dry-run real, cerca de 45 requisições ao Kuss e 17 ao Vip). Nenhum teste acessa a rede.

Política de escrita: `.reversa/reversa-config.json` está com `allowLegacyEdits: true` e `allowedPaths` vazio (liberação irrestrita, decidida pelo Rafael). Caminhos tocados: `src/**`, `tests/**`, `scripts/capturar_fixtures.py`, `config/leiloeiros.yaml`, `README.md`.

Etapas do `/reversa-coding` (com resumo e commit ao fim de cada uma):

| Etapa | Ações | Conteúdo |
|-------|-------|----------|
| 1 | T001 a T016 | Fixtures e testes (falham até o núcleo existir) |
| 2 | T017 a T026 | Núcleo genérico, adaptador, parser e enriquecimento |
| 3 | T027 a T034 | Saída, orquestrador, configuração, dry-run real e documentação |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Copiar as amostras de `_reversa_forward/002-…/amostras/` para `tests/fixtures/claudio_kuss/` com nomes curtos: `agenda.html`, `lotes_897_pag1.json`, `lotes_alem_da_ultima.json`, `detalhe_282622_sinistrado.json`, `historico_nao_loteado.json` | - | `[//]` | `tests/fixtures/claudio_kuss/` | 🟢 | `[X]` |
| T002 | Acrescentar a `scripts/capturar_fixtures.py` o modo `--claudio-kuss`, que grava em `tests/fixtures/claudio_kuss/`: `op=Q` dos eventos 897 e 898, a página `op=P` que contém o seq 282622, uma página `op=P` com pelo menos um lote com `valor`, a última página (parcial) do evento 898 e o detalhe `op=D` do seq 282341 (Fluence 2015); apelidos (`usuario`) trocados por `(removido)`; 5 s entre requisições. Executar uma vez e conferir os arquivos | - | `[//]` | `scripts/capturar_fixtures.py` | 🟢 | `[X]` |
| T003 | Em `tests/apoio.py`: fábrica `lote()` aceita os sete campos novos (data-delta §1.1); `transporte_kuss(...)` responde por caminho da URL e pelo campo `op` do corpo; variações sintéticas derivadas das fixtures reais: agenda sem evento de financeiras, agenda sem nenhum bloco de evento, `op=Q` com `qtde = 0`, `op=P` com objeto no lugar de lista, detalhe com `retirado = S` | T001 | `[//]` | `tests/apoio.py` | 🟢 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Coletor: as `anotacoes` da `Requisicao` chegam à `Pagina`; `teto_paginas` declarado pelo adaptador prevalece sobre o do coletor; adaptador sem o atributo usa 50 (D-37, D-47) | T003 | `[//]` | `tests/test_coletor.py` | 🟢 | `[X]` |
| T005 | Núcleo do parsing: o parser recebe em `contexto.pagina` as anotações da página que está lendo; com `preco_obrigatorio = False`, lote sem preço não conta no limite de 30% de incompletos; sem o atributo, continua contando (Vip) (D-37, D-46) | T003 | `[//]` | `tests/test_parsing_nucleo.py` | 🟢 | `[X]` |
| T006 | Sinônimos novos: `chev` → `chevrolet`, `caoachery` → `caoa chery`, `m benz` → `mercedes-benz`, `lr` → `land rover`, sem log de "marca fora da tabela" (D-42) | - | `[//]` | `tests/test_marcas.py` | 🟢 | `[X]` |
| T007 | Anos `AA/AA`: `13/13` → (2013, 2013); `98/99` → (1998, 1999); `26/27` com ano corrente 2026 → (2026, 2027); vazio e texto inválido → (None, None) (D-44) | - | `[//]` | `tests/test_normalizadores.py` | 🟢 | `[X]` |
| T008 | Adaptador do Kuss, sequência de páginas: só a chave `categoria` é aceita (outra chave levanta citando o Kuss); `preparar_sessao` devolve `None`; página 1 é `GET /proximos-leiloes`; com a agenda real, seleciona 897 e 898 (comparação sem acento e sem caixa) e pede `op=Q` 897, `op=P` 1..`qtdePag`, `op=Q` 898, …; evento com `qtde = 0` não pede `op=P`; anotações `tipo`/`evento`/`pregao_em` corretas; cabeçalhos `X-Requested-With` e `Referer`; `tipo_leilao_da_busca` → `financiamento`; `teto_paginas = 120` (D-34, D-35, D-39, D-40, D-47) | T001 | `[//]` | `tests/test_coleta_claudio_kuss.py` | 🟢 | `[X]` |
| T009 | Adaptador do Kuss, conferência e detalhe: soma de itens diferente de `qtde` gera aviso em log com evento, esperado e lido; página `[]` antes de `qtdePag` encerra o evento com o mesmo aviso; o cursor recomeça na página 1 (duas buscas seguidas dão a mesma sequência); `requisicao_detalhe(lote)` monta o `op=D` com `leilaoID` e `le_id` (D-36, D-48) | T008 | - | `tests/test_coleta_claudio_kuss.py` | 🟡 | `[X]` |
| T010 | Parser do Kuss, páginas `agenda` e `quantidade`: agenda com blocos de evento reconhecíveis → vazia declarada (com ou sem evento da categoria; ver Notas de execução); agenda sem nenhum bloco reconhecível → não vazia (o núcleo acusa quebra); `qtde = 0` → vazia; `qtde > 0` → não vazia, com `total_informado` (D-41) | T001 | `[//]` | `tests/test_parsing_claudio_kuss.py` | 🟡 | `[X]` |
| T011 | Parser do Kuss, página `lotes`: o Fluence 282622 sai com id `claudio-kuss-leiloes:282622`, link `…/lance/897/0/282622`, marca `renault` (sem `IMP`), modelo `fluence dyn 20a`, anos 2013/2013, preço `None`, `tipo_leilao = financiamento`, `evento_id` e `pregao_em` das anotações; `CHEV/…` → `chevrolet`; lote com `valor` → `lance_corrente`; `RETIRADO` → `retirado = True`; `SUCATA …` não é devolvido e a contagem vai para o log; ano vazio → anos `None`; `[]` → vazia; corpo não JSON ou objeto no lugar de lista → exceção; campo `usuario` nunca é lido (D-38, D-42 a D-45) | T010, T002 | - | `tests/test_parsing_claudio_kuss.py` | 🟢 | `[X]` |
| T012 | Parser do Kuss, detalhe: `aplicar_detalhe` preenche `observacoes` (de `tblInformacoes`), `despesas_adm` R$ 2.750, `placa_parcial` `F**-**35`, `local_documento` `SÃO PAULO` (aparado) e `detalhe_lido = True`; `&nbsp;` e vazio → `None`; `tblTxtInfo` nunca entra; `retirado = S` → `lote.retirado = True`; JSON inválido levanta (D-50, D-52) | T011 | - | `tests/test_parsing_claudio_kuss.py` | 🟢 | `[X]` |
| T013 | Enriquecimento: só os lotes de `novos` cujo adaptador tem `requisicao_detalhe` geram requisição (Vip nenhuma); retirado sai da lista e soma em retirados; falha de rede ou JSON inválido mantém o lote com `detalhe_lido = False` e log de aviso; semeáveis não são enriquecidos (D-48, D-49) | T003 | `[//]` | `tests/test_enriquecimento.py` | 🟢 | `[X]` |
| T014 | Digest: item do Kuss com `Pregão 13/10 10:00` na segunda linha e `Obs.:` resumida em 160 caracteres com `…`; `detalhe_lido = False` → `Obs.: observações não lidas; veja o link`; texto escapado para HTML; item do Vip idêntico ao de hoje (D-51) | T003 | `[//]` | `tests/test_digest.py` | 🟢 | `[X]` |
| T015 | Relatório e lista de monitoramento: linhas `Pregão`, `Despesas admin.`, `Documento` (`Placa F**-**35, documento de SÃO PAULO`) e `Observações` completas; lote do Vip sem essas linhas; a lista continua só acrescentando (D-51) | T003 | `[//]` | `tests/test_relatorio.py` | 🟢 | `[X]` |
| T016 | Ponta a ponta do Kuss com `transporte_kuss`, os 6 cenários Gherkin do requirements §7: dois eventos lidos com total igual a `qtde`; lote que casa avisado com leiloeiro, ano e link; candidato retirado no detalhe não avisado e contado; agenda sem financeiras termina sem alerta; JSON alterado gera alerta citando o Kuss; Kuss fora do ar não impede o aviso do Vip e a execução fica `sucesso_parcial`. Mais: primeira execução semeia o Kuss sem digest (RF-09) | T003 | `[//]` | `tests/test_e2e_claudio_kuss.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T017 | `Requisicao.anotacoes` e `Pagina.anotacoes`; o coletor copia as anotações para a página e usa `getattr(adaptador, "teto_paginas", self.teto_paginas)` (D-37, D-47) | T004 | `[//]` | `src/…/coleta/coletor.py` | 🟢 | `[ ]` |
| T018 | `Lote` ganha `evento_id`, `pregao_em`, `observacoes`, `despesas_adm`, `placa_parcial`, `local_documento`, `detalhe_lido` (todos opcionais, `None`); `ContextoParsing.pagina` com padrão vazio (data-delta §1.1, §1.2) | - | `[//]` | `src/…/parsing/modelos.py` | 🟢 | `[ ]` |
| T019 | Núcleo do parsing: cópia do contexto por página com `dataclasses.replace(contexto, pagina=pagina.anotacoes)`; `_incompleto` ignora o preço quando `getattr(parser, "preco_obrigatorio", True)` é falso (D-37, D-46) | T005, T017, T018 | - | `src/…/parsing/nucleo.py` | 🟢 | `[ ]` |
| T020 | Quatro sinônimos novos na tabela comum, com a fonte em comentário (D-42) | T006 | `[//]` | `src/…/parsing/marcas.py` | 🟢 | `[ ]` |
| T021 | Normalizador `anos_dois_digitos(texto, ano_corrente)` (regra do D-44); confirmar que o normalizador de preço existente aceita `21.600,00` | T007 | `[//]` | `src/…/parsing/normalizadores.py` | 🟢 | `[ ]` |
| T022 | `coleta/claudio_kuss.py`, parte 1: `Evento(id, rotulo, pregao_em)` e `ler_agenda(html) -> list[Evento]` (blocos `div.panel`, rótulo no `.panel-heading`, data `DD/MM/AAAA - HH:MM` no `.panel-body h2`, id do link `relacao-foto/<id>`, fuso `America/Sao_Paulo`) | T017 | - | `src/…/coleta/claudio_kuss.py` | 🟡 | `[ ]` |
| T023 | `coleta/claudio_kuss.py`, parte 2: `AdaptadorClaudioKuss` com `validar_filtros`, `preparar_sessao` (`None`), `montar_requisicao` com cursor de eventos e páginas, `tem_proxima_pagina` (agenda → plano; `op=Q` → `qtdePag`; `op=P` → conferência de total), `tipo_leilao_da_busca`, `teto_paginas = 120`, `requisicao_detalhe`; registro pelo id | T022, T008, T009 | - | `src/…/coleta/claudio_kuss.py` | 🟢 | `[ ]` |
| T024 | `parsing/claudio_kuss.py`, parte 1: `ParserClaudioKuss.extrair` para `agenda` (reusa `ler_agenda`), `quantidade` e `lotes` (decodifica JSON sem olhar o `Content-Type`; `IMP`, `SUCATA`, `RETIRADO`, anos, valor, link e id); `preco_obrigatorio = False`; registro pelo id | T019, T020, T021, T022, T010, T011 | - | `src/…/parsing/claudio_kuss.py` | 🟢 | `[ ]` |
| T025 | `parsing/claudio_kuss.py`, parte 2: `aplicar_detalhe(lote, conteudo)` (entidades HTML decodificadas, espaços colapsados, `&nbsp;` → `None`, `retirado = S`) | T024, T012 | - | `src/…/parsing/claudio_kuss.py` | 🟢 | `[ ]` |
| T026 | `coleta/enriquecimento.py`: `enriquecer(novos, cliente, adaptadores, parsers) -> ResultadoEnriquecimento(novos, retirados)`; erro de um lote nunca derruba os outros (D-48, D-49) | T018, T013 | `[//]` | `src/…/coleta/enriquecimento.py` | 🟢 | `[ ]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T027 | `ItemDigest` ganha `pregao` e `observacoes`; `item_de` formata a partir do lote; `_texto_item` acrescenta o pregão na segunda linha e a linha `Obs.:` (D-51) | T018, T014 | `[//]` | `src/…/notificacao/digest.py` | 🟢 | `[ ]` |
| T028 | `LoteRelatorio` ganha `pregao`, `despesas_adm`, `documento`, `observacoes`; `montar_relatorio` e `acrescentar_monitoramento` escrevem as linhas só quando preenchidas (D-51) | T027, T015 | - | `src/…/notificacao/relatorio.py` | 🟢 | `[ ]` |
| T029 | Orquestrador: importar `coleta.claudio_kuss` e `parsing.claudio_kuss` (registro); manter o `ClienteHTTP` aberto até o fim do enriquecimento; chamar `enriquecer` entre a filtragem e o digest (também no dry-run); somar os retirados do detalhe em `descartados_retirados`; log `enriq  | N lote(s) detalhado(s), M retirado(s), K falha(s)` (D-48) | T023, T025, T026, T028, T016 | - | `src/…/orquestrador.py` | 🟢 | `[ ]` |
| T030 | Bloco do Claudio Kuss em `config/leiloeiros.yaml` (data-delta §3), com comentário apontando `interfaces/claudio-kuss.md`, e o cabeçalho do arquivo citando os dois contratos | T029 | - | `config/leiloeiros.yaml` | 🟢 | `[ ]` |
| T031 | Dry-run real no container: conferir no log o total lido por evento igual ao `qtde`, os Fluence 282622 e 282341 entre os candidatos (como semeáveis: a busca do Kuss ainda não foi semeada, então o dry-run não chama o detalhe), nenhum alerta de quebra e duração abaixo de 10 minutos. Se algo falhar, voltar o bloco para `ativo: false` e registrar nas Notas de execução | T030 | - | (execução) | 🟡 | `[ ]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T032 | README: Claudio Kuss na lista de leiloeiros, como desligar, e o aviso de semeadura (rodar `--dry-run` antes da primeira varredura real com um leiloeiro novo) | T030 | `[//]` | `README.md` | 🟢 | `[ ]` |
| T033 | Seção "Feature 002" em `tests/RASTREABILIDADE.md`: RF-01 a RF-10 e os 6 cenários → testes, conferida mecanicamente | T029 | `[//]` | `tests/RASTREABILIDADE.md` | 🟢 | `[ ]` |
| T034 | Ajustar `onboarding.md` com o que o dry-run real mostrou (número de páginas, duração, linhas de log reais) | T031 | `[//]` | `_reversa_forward/002-…/onboarding.md` | 🟢 | `[ ]` |

## Notas de execução

- **T010 (2026-10-10), ajuste do D-41:** a agenda passa a se declarar vazia sempre que a estrutura é reconhecida, tenha ou não evento da categoria. Com a regra do plano ("vazia só sem evento da categoria"), eventos de financeiras todos com `qtde = 0` virariam quebra, contra o RF-08. Quebra continua detectada por agenda sem blocos e por `qtde > 0` sem lotes lidos. Roadmap D-41 atualizado.
- **T014 (2026-10-10), conflito com spec:** o RNF-04 de `_reversa_sdd/sdd/notificador-telegram.md` limita cada item do digest a 3 linhas; o RF-07 da 002 (Must, decisão do Rafael) põe as observações no aviso. Prevalece o RF-07: só itens com observações ganham a 4ª linha (`Obs.:`); itens do Vip continuam com 3 (teste existente intacto). A spec deve ser atualizada no `/reversa-sync`.
- **T002 (2026-10-10):** a página do Fluence foi obtida com a busca do próprio endpoint (`pesq=FLUENCE`) em vez de folhear 35 páginas; mesmo formato de resposta. O segundo Fluence-alvo (282341, 2015 manual) tem observação "MECÂNICA COM PROBLEMAS" e documento de Santa Catarina.
- **T015 (2026-10-10):** lote sem nenhum preço passa a ter o rótulo "Preço" (e "Preço ao entrar" na lista), em vez de "Lance inicial (ainda sem lances): Preço a confirmar".
- **Etapa 1 concluída (2026-10-10):** 380 testes passando (375 da 001 + 5 novos que já valem), 37 falhando e 3 módulos de teste sem coletar, todos à espera do núcleo da etapa 2.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-10 | Versão inicial gerada por `/reversa-to-do` | reversa |
