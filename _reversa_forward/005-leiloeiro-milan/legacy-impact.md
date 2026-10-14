# Legacy Impact: Leiloeiro Milan (e o nível Apify)

> Identificador: `005-leiloeiro-milan`
> Atualizado em: `2026-10-14` (concluída: T001–T043, três etapas)
> Âncora greenfield: `prd.md` + specs SDD em `_reversa_sdd/sdd/`, mais os adendos vigentes das features 001 a 004. O "legado" desta feature é o código entregue por elas.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (projeto inteiro liberado pelo Rafael). Escritas restritas, por conduta, aos caminhos do `actions.md`.

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/bot_leilao/coleta/apify.py` | `coletor-lotes` RF-03 | componente-novo, delta-de-contrato-externo | HIGH | Primeiro cliente pago: ator `neatrat/cloudflare-scraper` pela API síncrona do Apify, token só no cabeçalho, falhas com a causa, até 2 tentativas, consumo pelos limites da conta (D-86, D-88, D-89, D-91) |
| `src/bot_leilao/coleta/roteador.py`, `coleta/modelos.py` | `coletor-lotes` RF-02, RF-03 | componente-novo, regra-alterada | MEDIUM | `Requisicao.nivel` e `ClienteRoteado`: cada requisição sai pelo nível do leiloeiro (D-87) |
| `src/bot_leilao/coleta/coletor.py` | `coletor-lotes` RF-01 | regra-alterada | MEDIUM | Carimba o nível na busca e na preparação de sessão; entrega o relógio da varredura aos adaptadores com `agora` (D-87) |
| `src/bot_leilao/coleta/enriquecimento.py` | adendo da 002 (D-48) | regra-alterada | MEDIUM | Detalhe pelo nível do leiloeiro; o alvo é conferido de novo depois do detalhe (lance acima do teto sai do aviso) para **todos** os leiloeiros (D-98) |
| `src/bot_leilao/coleta/milan.py` | `coletor-lotes` RF-12 | componente-novo, delta-de-contrato-externo | MEDIUM | Agenda → catálogo de cada leilão "recuperados de financiamento", em toda varredura; detalhe pelo link do lote (D-93, D-94, D-97) |
| `src/bot_leilao/parsing/milan.py` | `parser-lotes` | componente-novo | MEDIUM | Catálogo (veículos, marca de duas palavras, km, câmbio, avisos em vermelho, IPVA pago, comitente, sucata, lance inicial, pregão sem ano, pátio) e página do lote (lances, estado, placa) (D-95 a D-97) |
| `src/bot_leilao/parsing/modelos.py` | `parser-lotes` §9 | delta-de-dados | LOW | `Lote.cambio` (D-99) |
| `src/bot_leilao/parsing/marcas.py` | `parser-lotes` RF-12 | regra-alterada | LOW | `m-benz`, `cintroen`; `jaguar` conhecida |
| `src/bot_leilao/config/leiloeiros.py` | `cadastro-leiloeiros` §6 | regra-alterada | MEDIUM | `apify` implementado; `intervalo_horas` (1 a 720) e `apify_ator` (só com perfil conhecido); `Leiloeiro.pago` (D-88, D-90, D-101) |
| `src/bot_leilao/config/ambiente.py` | `notificador-telegram` §10 | regra-alterada | MEDIUM | `APIFY_TOKEN` exigido só quando a varredura inclui pago; entra nos segredos mascarados (D-90) |
| `src/bot_leilao/db/migracoes.py`, `db/eventos.py`, `db/execucoes.py` | `agendador-observabilidade` | delta-de-dados | MEDIUM | Esquema 1 → 2 (`evento_visto`); última coleta ok por leiloeiro (D-101, D-102) |
| `src/bot_leilao/orquestrador.py` | adendos 003 e 004 | regra-alterada | HIGH | Seleção da varredura (`sem_pagos`, intervalo), clientes por nível, linha de consumo, antecedência, alertas do Apify e de gasto a 80% (D-90, D-91, D-100 a D-103) |
| `src/bot_leilao/cli.py` | `interfaces/cli.md` da 001 | delta-de-contrato-externo | LOW | `varrer --sem-pagos` (D-100) |
| `src/bot_leilao/notificacao/digest.py`, `notificacao/relatorio.py` | `notificador-telegram`, emendas E001/E002 | regra-alterada | LOW | Câmbio na 2ª linha do resumo (depois do km), no relatório e na lista, quando informado (D-99) |
| `scripts/varrer.bat`, `scripts/varrer-completo.bat` | atalhos | regra-alterada, componente-novo | LOW | O atalho do dia a dia passa a rodar sem os pagos; o novo roda com todos (D-100) |
| `config/leiloeiros.yaml`, `.env.example` | cadastro | regra-alterada (dados) | LOW | Bloco do Milan; `APIFY_TOKEN` |
| `scripts/capturar_fixtures.py`, `tests/fixtures/milan/`, `tests/apoio.py` | testes | componente-novo | LOW | Modo `--milan`; respostas reais do ator; `ApifySimulado`, auxiliares do Milan, `CenarioE2E` com Apify |
| `tests/test_coleta_apify.py`, `test_coleta_roteamento.py`, `test_coleta_milan.py`, `test_parsing_milan.py`, `test_repo_eventos.py`, `test_e2e_milan.py`, `test_e2e_ritmo.py`, `test_e2e_apify_alertas.py` | testes | componente-novo | LOW | Especificação da feature |
| `tests/test_config_leiloeiros.py`, `test_ambiente.py`, `test_marcas.py`, `test_enriquecimento.py`, `test_db_migracoes.py`, `test_relatorio.py`, `test_digest.py`, `test_cli.py` | testes | regra-alterada | LOW | Testes acrescentados; o teste antigo de `apify` "não implementado" virou o de `apify_residencial`; migração espera o esquema 2 |
| `README.md`, `tests/RASTREABILIDADE.md`, `_reversa_forward/backlog.md` | documentação | regra-alterada | LOW | Milan, Apify, atalhos e intervalo; rastreabilidade da 005 (50 referências conferidas); item 10 (troca automática) |

## Diff conceitual por componente

**Coleta.** Antes havia um só caminho de rede (o `ClienteHTTP`, pelo IP local). Agora cada requisição carrega o nível do leiloeiro e um roteador escolhe o cliente: `script` continua igual; `apify` pede a página a um ator da loja do Apify, que passa pelo Cloudflare. O ator só faz GET de uma URL, então a troca automática para buscas com corpo (Copart, Kuss) ficou para o backlog. As páginas liberadas do Milan contêm o script `challenge-platform` do Cloudflare; o cliente Apify reconhece o desafio só pela tela de desafio ("Just a moment", `cf-chl`), não por essa marca.

**Enriquecimento.** Continua detalhando só candidatos (novos e semeados), agora pelo nível do leiloeiro. Depois do detalhe, o lote é conferido de novo contra o alvo: no Milan o lance só chega pela página do lote, e um lance acima do teto deixa de ser avisado. Nos outros leiloeiros o detalhe não traz preço nem km, então o resultado não muda (testes do Kuss e do Freitas verdes).

**Orquestrador.** A varredura passa a escolher quem entra antes de exigir segredos: `--sem-pagos` tira os pagos; `intervalo_horas` tira quem foi lido há pouco (pela última execução normal com busca ok). Os pulados aparecem só na seção "Leiloeiros" do relatório. O leiloeiro pago ganha na mesma linha o consumo do Apify; leilões novos ganham a antecedência. Alertas novos: falhas do Apify com a causa, antecedência menor que o intervalo, gasto do ciclo acima de 80% (chave `apify` no limite de 1 por dia).

**Banco.** Esquema 2 com `evento_visto` (primeira vez que cada leilão aparece; os da primeira leitura de um leiloeiro ficam marcados). Migração automática e transacional.

**Resumo, relatório e lista.** Câmbio aparece quando o leiloeiro informa (hoje só o Milan); nos outros a linha fica igual.

## Preservadas

Feature greenfield, sem regras 🟢 extraídas de código por `/reversa`. Preservados por teste os comportamentos dos adendos 001 a 004: semeadura sem Telegram e com documentos, deduplicação, lista numerada só por acréscimo, pátio e FIPE no aviso, alerta por leiloeiro (bloqueio, certificado), verificação de certificado nunca desligada, 5 s por host. Suíte anterior (608) verde.

## Modificadas

Sem regras 🟢 extraídas. Mudanças de comportamento visíveis ao Rafael: `scripts/varrer.bat` passa a rodar **sem** o Milan (o `varrer-completo.bat` roda com todos); o resumo do Telegram pode trazer o câmbio depois do km; um lote que passar do teto depois do detalhe deixa de ser avisado (em qualquer leiloeiro); a seção "Leiloeiros" do relatório ganha linhas de pulado, consumo e antecedência. As specs `coletor-lotes.md` (NG-03, decisão sobre termos de uso, OQ-03) e `onboarding-leiloeiro-assistido.md` (NG-02, EC-02) ficam superadas pela regra anti-bot (RN-07) e pelo alerta de 80% (RN-13): correção no `/reversa-sync`.
