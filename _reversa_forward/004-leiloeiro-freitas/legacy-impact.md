# Legacy Impact: Leiloeiro Freitas

> Identificador: `004-leiloeiro-freitas`
> Atualizado em: `2026-10-13` (concluída: T001–T020, três etapas)
> Âncora greenfield: `prd.md` + specs SDD em `_reversa_sdd/sdd/`, mais os adendos vigentes das features 001 a 003. O "legado" desta feature é o código entregue por elas.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (projeto inteiro liberado pelo Rafael). Escritas restritas, por conduta, aos caminhos do `actions.md`.

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/bot_leilao/coleta/freitas.py` | `coletor-lotes` | componente-novo, delta-de-contrato-externo | MEDIUM | Busca pública em HTML até a mensagem de fim, aviso de repetição, filtros do site, detalhe pelo link (D-74 a D-78, D-82) |
| `src/bot_leilao/parsing/freitas.py` | `parser-lotes` | componente-novo | MEDIUM | Cards (marca de importado sem barra, anos `AA/AA`, maior lance × lance inicial, pregão, placa, etiqueta FINANCEIRA), em loteamento ignorado, detalhe (pátio, despesas, selos) (D-76 a D-82) |
| `src/bot_leilao/coleta/http.py` | `coletor-lotes` RF-07, RF-13 | regra-alterada | HIGH | Contexto TLS com `certifi` + intermediários da pasta `certificados/`, para **todos** os hosts; falha de certificado com motivo próprio e sem novas tentativas (D-83, D-84) |
| `src/bot_leilao/coleta/certificados/` | — | componente-novo | MEDIUM | Intermediário oficial GlobalSign GCC R6 AlphaSSL CA 2025 e o `LEIA-ME.md` (runbook do alerta de certificado) |
| `src/bot_leilao/parsing/marcas.py` | `parser-lotes` RF-12 | regra-alterada | LOW | `m.benz` |
| `src/bot_leilao/orquestrador.py` | `agendador-observabilidade` | regra-alterada | MEDIUM | Registro do Freitas; alerta de falha de certificado por leiloeiro, 1 por dia, apontando o runbook (D-85) |
| `pyproject.toml` | empacotamento | regra-alterada | LOW | `certifi` declarado; certificados e LEIA-ME como dados do pacote |
| `config/leiloeiros.yaml` | cadastro | regra-alterada (dados) | LOW | Bloco do Freitas |
| `scripts/capturar_fixtures.py`, `tests/fixtures/freitas/`, `tests/apoio.py` | testes | componente-novo | LOW | Modo `--freitas` (com o intermediário); amostras reais; `SiteFreitas` |
| `tests/test_coleta_freitas.py`, `test_parsing_freitas.py`, `test_e2e_freitas.py` | testes | componente-novo | LOW | Especificação da feature |
| `tests/test_coleta_http.py`, `test_marcas.py` | testes | regra-alterada | LOW | Testes acrescentados, inclusive a varredura do código contra `verify=False` |
| `README.md`, `tests/RASTREABILIDADE.md` | documentação | regra-alterada | LOW | Freitas, certificados; duas referências antigas da 003 corrigidas |

## Diff conceitual por componente

**Cliente HTTP.** Antes confiava só nas raízes padrão; agora acrescenta os intermediários oficiais da pasta, o que não afrouxa a verificação (a cadeia continua terminando numa raiz do `certifi`). Falha de verificação deixa de ser "falha de conexão com 3 tentativas" e vira "certificado", sem repetir.

**Coletor e parser.** Quarto leiloeiro, com tipo de leilão por lote (etiqueta) e não pela busca, e com lotes de número provisório deixados de fora.

**Orquestração.** O alerta por leiloeiro cobre bloqueio (003) e agora certificado.

## Preservadas

Toda a suíte anterior continua verde (608 testes no total): semeadura, deduplicação, enriquecimento, semeados nos documentos, lista numerada, pátio e FIPE nos avisos, alertas de quebra, falha geral e bloqueio com limite diário, 5 s por host, mascaramento de segredos.

## Modificadas

| Regra | Antes | Depois |
|-------|-------|--------|
| Confiança TLS (`coletor-lotes`) | Raízes padrão | Raízes padrão + intermediários oficiais guardados |
| Falha de certificado | "conexão", 3 tentativas, sem alerta | "certificado", 1 tentativa, alerta por leiloeiro apontando o runbook |
| Tipo de leilão | Sempre herdado da busca | Herdado da busca, ou da etiqueta do lote (Freitas) |
