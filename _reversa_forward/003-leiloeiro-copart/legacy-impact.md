# Legacy Impact: Leiloeiro Copart

> Identificador: `003-leiloeiro-copart`
> Atualizado em: `2026-10-11` (concluída: T001–T032, três etapas)
> Âncora greenfield: `prd.md` + specs SDD em `_reversa_sdd/sdd/`, mais os adendos vigentes das features 001 e 002. O "legado" desta feature é o código entregue pelas 001 e 002.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (projeto inteiro liberado pelo Rafael). Escritas restritas, por conduta, aos caminhos do `actions.md`. No `config/veiculos-alvo.yaml`, que tinha edições locais do Rafael não commitadas, só o bloco do Duster foi alterado (conferido por diff).

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/bot_leilao/coleta/copart.py` | `coletor-lotes` | componente-novo, delta-de-contrato-externo | MEDIUM | Busca JSON pública, ordenação fixa, paginação com conferência de total e de repetição (D-53 a D-59) |
| `src/bot_leilao/parsing/copart.py` | `parser-lotes` | componente-novo | MEDIUM | Lote com pátio, FIPE (`la`, nunca `fv`), data UTC → Brasília, observações, Compre Agora (D-61 a D-67) |
| `src/bot_leilao/coleta/http.py` | `coletor-lotes` RF-07 | regra-alterada | MEDIUM | Marcas do Imperva viram `bloqueado`, inclusive com status 200 em HTML (D-60) |
| `src/bot_leilao/config/veiculos.py`, `config/arquivos.py` | `configuracao-veiculos-alvo` §9 | delta-de-dados | LOW | Campo opcional `excluir`, validado; exemplo documentado (D-72) |
| `src/bot_leilao/filtro/motor.py` | `motor-filtros` RF-02 | regra-alterada | MEDIUM | Palavras a excluir pelo modelo e pelo título (D-72) |
| `src/bot_leilao/parsing/modelos.py` | `parser-lotes` §9 | delta-de-dados | LOW | `Lote.patio`, `Lote.fipe` (D-68) |
| `src/bot_leilao/parsing/vip.py` | `parser-lotes` | regra-alterada | LOW | Pátio = "Local:" do card (D-69) |
| `src/bot_leilao/coleta/claudio_kuss.py`, `parsing/claudio_kuss.py` | adendo da 002 | regra-alterada | LOW | `Evento.local` → anotação → `patio` (D-70) |
| `src/bot_leilao/notificacao/digest.py` | `notificador-telegram` §8 | regra-alterada | LOW | Pátio e FIPE na 2ª linha (D-71) |
| `src/bot_leilao/notificacao/relatorio.py` | E001/E002 da 001 | regra-alterada | LOW | Linhas Pátio e FIPE (com % do lance) (D-71) |
| `src/bot_leilao/orquestrador.py` | `agendador-observabilidade` | regra-alterada | MEDIUM | Registro da Copart; **alerta de bloqueio por leiloeiro**, 1 por dia (lacuna do RF-07 achada no coding) |
| `config/leiloeiros.yaml`, `config/veiculos-alvo.yaml` | cadastro | regra-alterada (dados) | LOW | Bloco da Copart; `excluir: [Oroch]` no Duster |
| `scripts/capturar_fixtures.py`, `tests/fixtures/copart/`, `tests/apoio.py` | testes | componente-novo | LOW | Modo `--copart`; amostras reais anonimizadas; `SiteCopart` |
| `tests/test_coleta_copart.py`, `test_parsing_copart.py`, `test_e2e_copart.py` | testes | componente-novo | LOW | Especificação da feature |
| `tests/test_coleta_http.py`, `test_config_veiculos.py`, `test_motor_criterios.py`, `test_parsing_vip.py`, `test_coleta_claudio_kuss.py`, `test_parsing_claudio_kuss.py`, `test_digest.py`, `test_relatorio.py`, `test_e2e_claudio_kuss.py` | testes | regra-alterada | LOW | Testes acrescentados; três expectativas da 002 atualizadas para incluir o pátio (evento do Kuss, anotações, 2ª linha do aviso do Kuss) |
| `README.md`, `tests/RASTREABILIDADE.md` | documentação | regra-alterada | LOW | Copart, pátio, FIPE, `excluir` |

## Diff conceitual por componente

**Coletor.** Um terceiro leiloeiro, agora com JSON paginado que exige ordenação explícita. O cliente HTTP reconhece o desafio do Imperva como bloqueio mesmo com status 200.

**Parser.** O lote ganha pátio e FIPE. A Copart entrega tudo na listagem, então não usa o enriquecimento da 002.

**Motor.** Um alvo pode excluir palavras; a exclusão vale para modelo e título.

**Orquestração.** Bloqueio de um leiloeiro, com os outros funcionando, passa a gerar alerta (antes, só registro). Vale para os três leiloeiros.

**Notificação.** Pátio em todo aviso; FIPE quando o leiloeiro informa; % do lance sobre a FIPE no relatório e na lista.

## Preservadas

Toda a suíte anterior continua verde (559 testes no total): semeadura, deduplicação, gravação após confirmação, km opcional e sentinela, retirados, enriquecimento e observações do Kuss, semeados nos documentos, alertas de quebra e de falha geral com limite diário, 5 s por host, mascaramento de segredos.

## Modificadas

| Regra | Antes | Depois |
|-------|-------|--------|
| `motor-filtros` RF-02 (casamento) | marca, modelo "contém", ano, teto, tipo | idem, mais "nenhuma palavra a excluir do alvo no modelo ou no título" |
| Alertas (`agendador-observabilidade`) | quebra de parser e falha geral | também bloqueio de um leiloeiro, 1 por dia |
| `notificador-telegram` §8 (2ª linha) | preço, leiloeiro, km, pregão | preço, leiloeiro, km, **pátio**, **FIPE**, pregão |
