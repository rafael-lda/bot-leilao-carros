# Legacy Impact: MVP de Varredura Ponta a Ponta

> Identificador: `001-mvp-varredura-ponta-a-ponta`
> Atualizado em: `2026-10-04` (concluída: T001–T063, três etapas)
> Feature greenfield, sem legado pré-existente. Âncora: `prd.md` + specs SDD em `_reversa_sdd/sdd/`.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (projeto inteiro liberado pelo Rafael). Escritas restritas, por conduta, aos caminhos do `roadmap.md` §5.

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `pyproject.toml`, `README.md` | infraestrutura | componente-novo | LOW | Pacote `bot_leilao`, dependências (D-01 a D-09) |
| `.gitignore`, `.env.example` | infraestrutura | componente-novo | LOW | `dados/` fora do versionamento; variáveis do Telegram documentadas |
| `src/bot_leilao/__init__.py`, `__main__.py` | infraestrutura | componente-novo | LOW | Esqueleto do pacote |
| `scripts/capturar_fixtures.py`, `tests/fixtures/vip/` | `coletor-lotes`, `parser-lotes` | componente-novo | LOW | Evidência real do Vip para os testes (D-27) |
| `tests/conftest.py`, `tests/apoio.py` | testes | componente-novo | LOW | Fixtures sem rede |
| `tests/test_texto.py`, `tests/test_logsetup.py` | transversal | componente-novo | LOW | Especificação de normalização e mascaramento (RN-08) |
| `tests/test_config_*.py`, `tests/test_ambiente.py` | `configuracao-veiculos-alvo`, `cadastro-leiloeiros` | componente-novo | LOW | Especificação da configuração |
| `tests/test_db_migracoes.py`, `tests/test_trava.py`, `tests/test_repo_*.py` | `motor-filtros`, `agendador-observabilidade` | componente-novo | LOW | Especificação do SQLite e da trava |
| `tests/test_coleta_*.py`, `tests/test_coletor.py` | `coletor-lotes` | componente-novo | LOW | Especificação do cliente HTTP, coletor e adaptador Vip |
| `tests/test_normalizadores.py`, `tests/test_marcas.py`, `tests/test_parsing_*.py` | `parser-lotes` | componente-novo | LOW | Especificação do parsing |
| `tests/test_motor_*.py` | `motor-filtros` | componente-novo | LOW | Especificação dos critérios, semeadura e deduplicação |
| `tests/test_digest.py`, `tests/test_telegram.py` | `notificador-telegram` | componente-novo | LOW | Especificação do digest e do envio |
| `src/bot_leilao/texto.py`, `src/bot_leilao/logsetup.py` | transversal | componente-novo | LOW | Normalização e ids estáveis (D-24); log com mascaramento de segredos (D-26, RN-08) |
| `src/bot_leilao/config/arquivos.py`, `veiculos.py`, `leiloeiros.py`, `ambiente.py`, `coerencia.py` | `configuracao-veiculos-alvo`, `cadastro-leiloeiros` v1.3 | componente-novo | MEDIUM | Validação antes da rede; `quilometragem_maxima` (delta sobre a spec); adaptador e parser exigidos; aviso alvos × buscas |
| `src/bot_leilao/db/conexao.py`, `migracoes.py`, `trava.py`, `lotes.py`, `execucoes.py` | `motor-filtros`, `agendador-observabilidade` | delta-de-dados | MEDIUM | Esquema v1 com cinco tabelas (data-delta.md §2), duas delas novas sobre as specs |
| `src/bot_leilao/coleta/modelos.py`, `registro.py`, `http.py`, `coletor.py`, `vip.py` | `coletor-lotes` v1.1 | componente-novo, delta-de-contrato-externo | MEDIUM | Nível `script`; cabeçalho de navegador (D-30); sessão, paginação, busca atômica; contrato do Vip |
| `src/bot_leilao/parsing/modelos.py`, `normalizadores.py`, `marcas.py`, `nucleo.py`, `vip.py` | `parser-lotes` v1.2 | componente-novo | MEDIUM | Campos novos no `Lote`; sinônimos de marca; busca vazia legítima (D-31) |
| `src/bot_leilao/filtro/motor.py`, `fluxo.py` | `motor-filtros` | componente-novo | MEDIUM | Km opcional, retirados, semeadura por busca (D-20); `lote_conhecido` no lugar de `LoteNotificado` |
| `src/bot_leilao/notificacao/digest.py`, `telegram.py` | `notificador-telegram` | componente-novo, delta-de-contrato-externo | LOW | Digest em HTML, divisão em blocos, envio com confirmação |
| `src/bot_leilao/notificacao/alertas.py` | `notificador-telegram`, `agendador-observabilidade` | componente-novo | LOW | Alerta de quebra limitado a 1 por dia por leiloeiro (D-22); alerta único de falha geral |
| `src/bot_leilao/orquestrador.py`, `src/bot_leilao/cli.py` | `agendador-observabilidade` (parcial) | componente-novo | MEDIUM | Pipeline com registro garantido em `finally`, trava, dry-run; comandos `varrer` e `testar-telegram`. Sem agendamento automático, recomendações de frequência nem relatório de saúde |
| `tests/test_e2e_*.py`, `tests/test_cli.py`, `tests/test_seguranca.py`, `tests/RASTREABILIDADE.md` | testes | componente-novo | LOW | 11 cenários de aceitação, CLI, segurança do token e matriz RF → teste |

| `src/bot_leilao/notificacao/relatorio.py`, `src/bot_leilao/orquestrador.py`, `.gitignore` | `notificador-telegram`, `agendador-observabilidade` | regra-nova | LOW | Emenda E001: relatório Markdown por varredura real em `1OUTPUT/`, fora do git, nunca sobrescrito |
| `src/bot_leilao/notificacao/relatorio.py`, `src/bot_leilao/orquestrador.py` | `notificador-telegram` | regra-nova | LOW | Emenda E002: lista acumulada de lotes a monitorar em `1OUTPUT/`, só acréscimo, mantida pelo Rafael e por agentes a pedido |
| `src/bot_leilao/notificacao/relatorio.py` | `notificador-telegram` | regra-nova | LOW | Emenda E003: regras da lista de monitoramento passam a cobrir reaparições de lotes |

## Diff conceitual por componente

Todos os componentes do recorte da feature existem e passam em 339 testes, incluindo os 11 cenários de aceitação de ponta a ponta. Uma execução real em dry-run contra o Vip leu 17 páginas e 201 lotes sem quebra. Deltas sobre as specs, a convergir pelo `/reversa-sync`: `quilometragem_maxima`; campos `quilometragem`, `situacao` e `retirado` no `Lote`; critério de km e descarte de retirados no motor; tabelas `lote_conhecido` (com `origem`), `busca_semeada` e `execucao_busca`.

## Preservadas

Nada a preservar: feature greenfield.

## Modificadas

Nada modificado: feature greenfield.
