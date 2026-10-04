# Legacy Impact: MVP de Varredura Ponta a Ponta

> Identificador: `001-mvp-varredura-ponta-a-ponta`
> Atualizado em: `2026-10-04` (etapa 1 de 3: T001–T026, T062)
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

## Diff conceitual por componente

Nesta etapa só existem testes e infraestrutura: nenhum comportamento de produção foi implementado. Os testes fixam o contrato descrito em `api-interna.md`, que a etapa 2 implementa.

## Preservadas

Nada a preservar: feature greenfield.

## Modificadas

Nada modificado: feature greenfield.
