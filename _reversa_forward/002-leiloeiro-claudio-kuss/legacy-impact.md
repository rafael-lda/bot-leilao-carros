# Legacy Impact: Leiloeiro Claudio Kuss

> Identificador: `002-leiloeiro-claudio-kuss`
> Atualizado em: `2026-10-10` (concluída: T001–T034, três etapas)
> Âncora greenfield: `prd.md` + specs SDD em `_reversa_sdd/sdd/`, mais o adendo `_reversa_sdd/addenda/001-mvp-varredura-ponta-a-ponta.md`. O "legado" desta feature é o código entregue pela 001.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (projeto inteiro liberado pelo Rafael). Escritas restritas, por conduta, aos caminhos do `actions.md`. O `config/veiculos-alvo.yaml`, com alterações locais do Rafael ainda não commitadas, não foi tocado.

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/bot_leilao/coleta/claudio_kuss.py` | `coletor-lotes` | componente-novo, delta-de-contrato-externo | MEDIUM | Adaptador: agenda, cursor de eventos e páginas, conferência de total, detalhe (D-33 a D-40, D-47) |
| `src/bot_leilao/parsing/claudio_kuss.py` | `parser-lotes` | componente-novo | MEDIUM | Parser de agenda, quantidade, lotes e detalhe; sucata reconhecida no detalhe (D-41 a D-46, D-43 revisto) |
| `src/bot_leilao/coleta/enriquecimento.py` | `coletor-lotes` / orquestração | componente-novo | MEDIUM | Detalhe só dos lotes novos; retirados e sucata saem do aviso; falha não bloqueia (D-48, D-49) |
| `src/bot_leilao/coleta/modelos.py`, `coletor.py` | `coletor-lotes` v1.1 | regra-alterada | LOW | `anotacoes` em `Requisicao` e `Pagina`; teto de páginas por adaptador (D-37, D-47). Vip: sem anotações, teto 50 como antes |
| `src/bot_leilao/parsing/modelos.py` | `parser-lotes` v1.3 | delta-de-dados | LOW | Sete campos opcionais no `Lote`; `ContextoParsing.pagina` (data-delta §1). Banco inalterado |
| `src/bot_leilao/parsing/nucleo.py` | `parser-lotes` RF-08 | regra-alterada | MEDIUM | Contexto por página; parser pode declarar preço não obrigatório no limite de 30% de incompletos (D-46). Padrão continua contando o preço |
| `src/bot_leilao/parsing/marcas.py` | `parser-lotes` RF-12 | regra-alterada | LOW | Quatro sinônimos comuns novos (`chev`, `caoachery`, `m benz`, `lr`), válidos também para o Vip |
| `src/bot_leilao/parsing/normalizadores.py` | `parser-lotes` RF-03 | regra-nova | LOW | `anos_dois_digitos` (D-44) |
| `src/bot_leilao/notificacao/digest.py` | `notificador-telegram` RF-01, RNF-04 | regra-alterada | MEDIUM | Pregão na 2ª linha e 4ª linha `Obs.:` para quem tem observações; **contraria o RNF-04** (máx. 3 linhas por item) por decisão do Rafael no RF-07 da 002. Itens do Vip continuam com 3 linhas |
| `src/bot_leilao/notificacao/relatorio.py` | emendas E001/E002 da 001 | regra-alterada | LOW | Linhas de pregão, despesas, documento e observações; rótulo "Preço" para lote sem nenhum preço |
| `src/bot_leilao/orquestrador.py` | `agendador-observabilidade` (orquestração) | regra-alterada | MEDIUM | Registro do Kuss; cliente HTTP aberto até o enriquecimento; etapa de enriquecimento entre filtragem e digest (também no dry-run) |
| `config/leiloeiros.yaml` | `cadastro-leiloeiros` | regra-alterada (dados) | LOW | Bloco do Claudio Kuss ativo, após o dry-run real |
| `scripts/capturar_fixtures.py`, `tests/fixtures/claudio_kuss/` | testes | componente-novo | LOW | Modo `--claudio-kuss`; respostas reais de 2026-10-10 sem apelidos de quem deu lance |
| `tests/apoio.py` | testes | regra-alterada | LOW | `SiteKuss` e roteamento do host do Kuss no `CenarioE2E` |
| `tests/test_coleta_claudio_kuss.py`, `test_parsing_claudio_kuss.py`, `test_enriquecimento.py`, `test_e2e_claudio_kuss.py` | testes | componente-novo | LOW | Especificação da feature |
| `tests/test_coletor.py`, `test_parsing_nucleo.py`, `test_marcas.py`, `test_normalizadores.py`, `test_digest.py`, `test_relatorio.py` | testes | regra-alterada | LOW | Testes acrescentados no fim; nenhum teste da 001 foi alterado |
| `tests/RASTREABILIDADE.md`, `README.md` | documentação | regra-alterada | LOW | Seção da feature 002; Claudio Kuss no README |

## Diff conceitual por componente

**Coletor.** Uma busca pode virar uma sequência heterogênea de requisições (GET da agenda, POSTs JSON), com anotações que o coletor só repassa. O teto de páginas deixa de ser único: o adaptador do Kuss declara 120. Nenhum comportamento do Vip mudou.

**Parser (núcleo).** O parser passa a saber de qual página está lendo (`contexto.pagina`), e um leiloeiro de leilão por evento pode dizer que preço ausente não é sinal de quebra. As regras de quebra e de busca vazia continuam as mesmas.

**Parser do Kuss.** A agenda reconhecida é sempre "vazia" (nunca traz lotes); a página de quantidade decide entre vazio legítimo (`qtde = 0`) e quebra (`qtde > 0` sem lotes). O detalhe fornece observações, despesas, placa parcial, estado do documento, retirado e sucata.

**Orquestração.** Entre a filtragem e o digest, os lotes novos dos leiloeiros que oferecem detalhe são detalhados; retirados e sucata saem do aviso. A semeadura acontece antes e não é detalhada.

**Notificação.** O item do digest ganha pregão e observações; o relatório e a lista ganham as linhas completas.

## Preservadas

Regras do adendo da 001 que continuam intactas e foram reverificadas pela suíte (482 testes): semeadura por busca, deduplicação por `lote_conhecido`, gravação só após confirmação do Telegram, km opcional e km sentinela, retirados antes da filtragem, alertas 1/dia/leiloeiro, 5 s por host, 429 com 30 s, relatório nunca sobrescrito, lista só acrescenta, mascaramento de segredos.

## Modificadas

| Regra | Antes | Depois |
|-------|-------|--------|
| `notificador-telegram` RNF-04 | Cada item do digest ocupa no máximo 3 linhas | Itens com observações ocupam 4 (RF-07 da 002); os demais, 3 |
| `parser-lotes` RF-08 (limite de incompletos) | Preço ausente sempre conta como incompleto | Conta, salvo se o parser declarar `preco_obrigatorio = False` |
| `coletor-lotes` RF-14 (teto de páginas) | Teto único do coletor (50) | Teto do coletor, ou o declarado pelo adaptador |
