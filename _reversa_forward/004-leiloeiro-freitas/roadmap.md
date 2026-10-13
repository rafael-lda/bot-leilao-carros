# Roadmap: Leiloeiro Freitas

> Identificador: `004-leiloeiro-freitas`
> Data: `2026-10-13`
> Requirements: `_reversa_forward/004-leiloeiro-freitas/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA
> Numeração das decisões: continua a das features anteriores (D-01 a D-73).

## 1. Resumo da abordagem

O Freitas entra como quarto par adaptador + parser (`freitas-leiloeiro`), no nível `script`, lendo a busca pública que a própria página de veículos usa: `GET /Leiloes/PesquisarLotes`, que devolve HTML parcial com um card por lote, 200 por página, até a mensagem "Nenhum lote localizado". A busca é de veículos "Inteiros"; o tipo de leilão vem da etiqueta **FINANCEIRA** de cada card. Pátio, despesas e selos do lote (ex.: "IPVA 2026 PAGO") vêm da página de detalhe, pelo enriquecimento já existente (novos e semeados).

A peça nova no núcleo é a **cadeia de certificado**: o servidor do Freitas envia o intermediário errado; o `ClienteHTTP` passa a confiar, além do pacote `certifi`, nos intermediários oficiais guardados em `src/bot_leilao/coleta/certificados/`, sempre com verificação completa. Uma falha de certificado passa a gerar alerta, porque não se resolve sozinha.

Verificações deste plano (2026-10-13, 9 requisições): 225 lotes "inteiros" em 3 páginas, 220 com FINANCEIRA, sem bloqueio; o certificado valida até a GlobalSign Root R6 também sem `VERIFY_X509_PARTIAL_CHAIN` (comportamento do Python 3.12 do Windows); `robots.txt` inexistente; pátio e despesas mudam por leilão; lotes "EM LOTEAMENTO" aparecem com número provisório ("X", 700+).

## 2. Princípios aplicados

| Princípio (de fato) | Como a feature se relaciona | Status |
|---------------------|-----------------------------|--------|
| Menor custo | `script`, sem Apify | respeita |
| Não falhar em silêncio | Falha de certificado e bloqueio geram alerta; página sem cards e sem mensagem de fim é quebra; lote repetido entre páginas vira aviso no log | respeita |
| Segurança | Verificação de certificado nunca desligada; intermediário oficial com impressão digital registrada | respeita |
| Sistema não dá lances | Só busca e detalhe públicos | respeita |
| Conduta de coleta | 5 s por host; 3 requisições de busca por varredura | respeita |
| Automação máxima | Nenhum passo manual | respeita |

## 3. Decisões técnicas

### 3.1 Contrato com o Freitas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-74 | (RF-01, RF-02, RF-06) Busca por `GET /Leiloes/PesquisarLotes` com os parâmetros da página (contrato §2), `TopRows=200`, `PageNumber` crescente; próxima página enquanto a anterior trouxe cards; **para só na mensagem de fim** "Nenhum lote localizado"; lote repetido entre páginas gera aviso no log | É a chamada da própria página; parar só na mensagem de fim protege contra o site passar a limitar o tamanho da página sem avisar (lição da paginação da Copart) | Parar quando vier menos de 200 (falha em silêncio se o limite mudar); raspar a página `/Leiloes/Pesquisar` (os lotes não vêm nela) | 🟢 |
| D-75 | (RF-01) Filtros aceitos no YAML, com tradução para os parâmetros: `categoria` → `Categoria`, `condicao` → `Condicao`, `tipo_lote` → `TipoLoteId`, `patio` → `PatioId`, `estado` → `Estado`, `cidade` → `Cidade`, `ano_modelo_min` → `AnoModeloMin`, `ano_modelo_max` → `AnoModeloMax`; chave desconhecida aborta antes da rede | Mesma regra do D-12, D-40 e D-57 | — | 🟢 |
| D-76 | (RF-03) Tipo de leilão **por lote**: etiqueta "FINANCEIRA" → `financiamento`; vazia ou outra → `None`. `tipo_leilao_da_busca` devolve `financiamento` só para a checagem de coerência entre alvos e buscas | A busca mistura comitentes (5 de 225 sem etiqueta em 2026-10-13: logos 30 e 1162) | Herdar da busca (avisaria lote que não é de financeira) | 🟢 |
| D-77 | (RN-10) Lote "EM LOTEAMENTO" (card com lote "X" e número 700+) **não é devolvido** pelo parser; a contagem vai para o log. Ele entra quando ganhar número definitivo | O número provisório deve mudar no loteamento, e o id mudaria junto (aviso duplicado). O id interno estável (`loteId`) só existe no detalhe, e ler o detalhe de todos os lotes custaria ~225 requisições | Usar o `loteId` do detalhe para todos (19 min de varredura); id por placa parcial e descrição (frágil) | 🟡 |
| D-78 | Id `freitas-leiloeiro:<leilaoId>-<loteNumero>`; link `…/Leiloes/LoteDetalhes?leilaoId=<id>&loteNumero=<n>` | Número do lote é por leilão (RN-03) | — | 🟢 |
| D-79 | (RF-03) Descrição em 5 partes separadas por ", ": bem, ano `AA/AA`, "PLACA: …", combustível, cor. Marca: tira o prefixo `I/` (importado); se sobrar `/`, divide na barra; senão a primeira palavra é a marca. Sinônimo novo na tabela comum: `m.benz` → `mercedes-benz`. A placa parcial vai para `placa_parcial` | Censo: 225 de 225 com 5 partes; `I/NISSAN SENTRA 20S FLEX`, `I/RAM 2500 LARAMIE` (sem barra), `M.BENZ` | — | 🟢 |
| D-80 | Preço do card: rótulo "Maior lance" → `lance_corrente`; "Lance Inicial" → `lance_inicial` | RN-05; regra existente (corrente, senão inicial) | — | 🟢 |
| D-81 | Pregão: data e hora do card, horário de Brasília (offset fixo, como D-22) | Os dois `span.fw-bold` do card | — | 🟢 |
| D-82 | (RF-04) Enriquecimento pelo detalhe (`requisicao_detalhe` + `aplicar_detalhe`, mecanismo da 002): pátio = "CIDADE - UF" do trecho "Visitação/Retirada"; despesas = soma de "Despesas operacionais" e "Despesas de logística" (com a composição nas observações quando houver logística); observações = selos do lote (ex.: "IPVA 2026 PAGO"); estado com "RETIRADO" → retirado | Pátio e despesas mudam por leilão; selos são do lote | Ler uma vez por leilão (o detalhe é por lote de qualquer forma, e os selos são do lote) | 🟢 (pátio, despesas, selos) 🟡 (texto de retirado, não observado) |

### 3.2 Núcleo: certificado

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-83 | (RF-05) O `ClienteHTTP` cria o contexto TLS com o pacote `certifi` **mais** os intermediários oficiais em `src/bot_leilao/coleta/certificados/*.pem` (hoje só "GlobalSign GCC R6 AlphaSSL CA 2025", impressão digital registrada no contrato). Vale para todos os hosts. Nenhum caminho do código usa `verify=False` (teste que procura no código) | Acrescentar um intermediário legítimo não afrouxa nada: a cadeia continua terminando numa raiz do `certifi`. Verificado em 2026-10-13 sem `VERIFY_X509_PARTIAL_CHAIN` | `verify=False` para o Freitas (inaceitável); contexto só para o host do Freitas (mais código, mesmo efeito) | 🟢 |
| D-84 | Falha de verificação de certificado vira motivo `certificado: <host>`, sem novas tentativas (não se resolve sozinha) | Hoje cairia em "conexao", tentando 3 vezes | — | 🟢 |
| D-85 | (RF-08) O alerta por leiloeiro da feature 003 passa a cobrir também falha de certificado (além de bloqueio), 1 por dia. O texto do alerta aponta o procedimento de correção: `src/bot_leilao/coleta/certificados/LEIA-ME.md` (conteúdo em `runbook-certificado.md` desta feature: diagnóstico, casos A a E, como guardar um intermediário novo com segurança) | Certificado errado persiste até alguém agir (o Freitas renovar com outra cadeia, ou o intermediário vencer em 2027-05-21) | Alertar toda falha de rede (alarmes por instabilidade passageira) | 🟢 |

## 4. Premissas

| Premissa | Origem | Risco se errada |
|----------|--------|-----------------|
| O número do lote não muda depois de "ABERTO PARA LANCES" | Observação de 2026-10-13 | Aviso duplicado do mesmo carro; a lista ajuda a perceber (mesma placa parcial) |
| Lote em loteamento ganha número definitivo antes do pregão | 8111: pregão 24/10, loteamento em 13/10 | Lote avisado tarde; nunca perdido |
| O Freitas não volta a bloquear por firewall | Triagem de 10/10 × teste de 13/10 | Alerta de bloqueio; degrau Apify (backlog item 9) |

## 5. Delta arquitetural

| Componente | Arquivo de origem | Tipo de mudança | Resumo |
|------------|-------------------|-----------------|--------|
| Adaptador Freitas | `coletor-lotes.md` RF-12 | componente-novo | `src/bot_leilao/coleta/freitas.py` (D-74 a D-78, D-82) |
| Parser Freitas | `parser-lotes.md` | componente-novo | `src/bot_leilao/parsing/freitas.py` (D-76, D-77, D-79 a D-82) |
| Cliente HTTP | `coletor-lotes.md` RF-07, RF-13 | regra-alterada | Intermediários oficiais no contexto TLS; motivo `certificado` (D-83, D-84) |
| Certificados | — | componente-novo | `src/bot_leilao/coleta/certificados/globalsign-gcc-r6-alphassl-ca-2025.pem` e `LEIA-ME.md` (o runbook) |
| Tabela de sinônimos | `parser-lotes.md` RF-12 | regra-alterada | `m.benz` (D-79) |
| Orquestrador | adendo da 003 | regra-alterada | Registro do Freitas; alerta também para falha de certificado (D-85) |
| Cadastro | `config/leiloeiros.yaml` | regra-alterada (dados) | Bloco do Freitas |

Fora do delta: motor, banco, digest, relatório e lista (o Freitas usa os campos existentes: pátio, despesas, observações, placa parcial, pregão).

## 6. Delta no modelo de dados

**Nenhum campo novo.** O Freitas preenche campos que já existem (`patio`, `despesas_adm`, `observacoes`, `placa_parcial`, `pregao_em`, `lance_inicial`/`lance_corrente`). Banco inalterado. Detalhe em `data-delta.md`.

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Freitas: `GET /Leiloes/PesquisarLotes` e `GET /Leiloes/LoteDetalhes` | HTTP | `interfaces/freitas.md` |

## 8. Plano de migração

1. Sem migração. A primeira varredura com o Freitas ativo semeia a busca: os candidatos entram no relatório e na lista (com pátio e despesas do detalhe), sem aviso no Telegram.
2. Ordem: certificado no `ClienteHTTP` → adaptador e parser com amostras reais → alerta de certificado → bloco no YAML e dry-run real.
3. Reversão: `ativo: false` no bloco do Freitas.

## 9. Riscos

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|---------------|---------|-----------|
| R-01 | O Freitas renova o certificado com outra cadeia (ou corrige a dele) | média | baixo/alto | Se corrigir, nada muda (o intermediário extra não atrapalha); se trocar de autoridade, falha de certificado com alerta (D-85) e troca do PEM |
| R-02 | O intermediário vence (2027-05-21) | certa, em 2027 | médio | Item no regression-watch com a data; alerta de certificado se acontecer |
| R-03 | Firewall volta a barrar | média | médio | Alerta de bloqueio; degrau Apify |
| R-04 | Lote em loteamento muda pouco antes do pregão | baixa | baixo | Premissa §4 |

## 10. Critério de pronto

- Os 5 cenários do requirements passam em testes sem rede, com as amostras reais.
- Suíte anterior verde.
- Dry-run real: Freitas lido até a mensagem de fim, sem repetição, sem alerta; varredura com os 4 leiloeiros abaixo de 10 minutos (RF-09).
