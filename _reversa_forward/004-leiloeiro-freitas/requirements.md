# Requirements: Leiloeiro Freitas

> Identificador: `004-leiloeiro-freitas`
> Data: `2026-10-13`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Acrescenta o quarto leiloeiro ao bot: **Freitas Leiloeiro** (Santo André-SP), conhecido por leilões de financeiras. A cada varredura o bot lê os veículos em condição **"Inteiros"** da busca pública do site, aplica os mesmos veículos-alvo e avisa no mesmo resumo do Telegram, no relatório e na lista de monitoramento. Em 2026-10-13 eram **225 lotes "inteiros", 220 com a etiqueta FINANCEIRA**, em 3 leilões, lidos em 3 requisições.

Na triagem de 2026-10-10 o Freitas parecia bloqueado ("Acesso Bloqueado" do firewall e certificado incompleto). Em 2026-10-13, com a cadeia de certificado completada pelo intermediário oficial da GlobalSign, a busca respondeu sem bloqueio e sem login.

## 2. Contexto a partir do legado

Projeto greenfield com as features 001, 002 e 003 entregues.

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/prd.md#4` | Lista-alvo de leiloeiros (Freitas, Vip, Claudio Kuss, Copart, Milan) | 🟢 |
| `_reversa_sdd/sdd/cadastro-leiloeiros.md#6` (v1.3) | Busca declarada por filtros chave-valor; busca ampla (§6.1.1) | 🟢 |
| `_reversa_sdd/sdd/coletor-lotes.md#6` (v1.1) | Adaptador por leiloeiro, paginação, 5 s por host, bloqueio distinto de falha | 🟢 |
| `_reversa_sdd/sdd/parser-lotes.md#6` (v1.3) | Parser por leiloeiro; id canônico; sinônimos; busca vazia legítima | 🟢 |
| `_reversa_sdd/addenda/002-leiloeiro-claudio-kuss.md` | Enriquecimento pelo detalhe (novos e semeados), observações no aviso, anotações por página, ano `AA/AA` | 🟢 |
| `_reversa_sdd/addenda/003-leiloeiro-copart.md` (com atualizações de 2026-10-13) | Pátio e FIPE nos avisos; alerta de bloqueio por leiloeiro; seção "Leiloeiros" no relatório; formato numerado da lista de monitoramento | 🟢 |
| `_reversa_forward/backlog.md#9` | Escada de acesso (script → Apify) e uso estrito do Apify | 🟢 |
| `_reversa_forward/004-leiloeiro-freitas/amostras/` | Busca, página de lotes, fim da busca e detalhe de um lote, reais, de 2026-10-13 | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Rafael, comprador em Londrina | Ver os carros de financeira do Freitas sem visitar o site | O resumo traz um Duster CVT 2024 do Freitas, com lance, pregão, pátio em Santo André-SP e despesas 🟢 |
| Rafael, operador | Não ser enganado por silêncio | Se o certificado do Freitas mudar de novo ou o firewall barrar o bot, chega um alerta identificando o Freitas, e os outros leiloeiros seguem 🟢 |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** A busca do Freitas é a de veículos (`categoria` 1) com a condição **"Inteiros"**, sem marca nem modelo; o recorte é feito pelos veículos-alvo. "Inteiros" corresponde ao "conservado" já usado no Vip e à preferência do Rafael por carros sem sinistro (pequena monta adiada). 🟢
   - Origem: filtro "Condição" do site (opções: Inteiros, Sinistros e Sucatas, Pequena Monta, Média Monta, Sucatas); preferência registrada na feature 001
   - Tipo: nova
2. **RN-02:** O tipo de leilão vem da **etiqueta de origem de cada lote** (no card: "FINANCEIRA" → `financiamento`); lote sem etiqueta ou com outra fica sem tipo e não casa com alvos de financiamento. Diferente do Vip, do Kuss e da Copart, em que o tipo vem da busca. 🟢
   - Origem: censo de 2026-10-13 (220 "FINANCEIRA", 5 sem etiqueta em 225)
   - Tipo: nova
3. **RN-03:** O número do lote é por leilão; o identificador canônico combina o leilão e o lote (`leilaoId` + `loteNumero`), e o link é a página de detalhe do lote. 🟢
   - Tipo: nova
4. **RN-04:** O ano no formato `AA/AA` do card (ex.: `23/24`) segue a regra da feature 002 (ano de modelo). 🟢
   - Tipo: mantida (regra comum)
5. **RN-05:** O preço do card é o **maior lance** quando há lance, senão o **lance inicial**; os dois entram como já fazem no Vip (lance corrente, senão inicial). 🟢
   - Origem: card ("Maior lance" em 104 de 200, "Lance Inicial" em 96)
   - Tipo: nova
6. **RN-06:** O pátio, as despesas operacionais e as observações vêm da **página de detalhe** do lote, consultada só para os lotes que vão para o aviso ou para a lista (mesmo mecanismo do Kuss). O Freitas não informa km nem câmbio em campo próprio: km fica "a confirmar"; o câmbio aparece às vezes no título (ex.: "CVT") e é identificado lote a lote na lista. 🟢
   - Tipo: nova
7. **RN-07:** A conexão com o Freitas mantém a **verificação completa do certificado**. O site envia um certificado intermediário errado (2014) para um certificado emitido pela autoridade "GlobalSign GCC R6 AlphaSSL CA 2025"; o bot completa a cadeia com o intermediário oficial da GlobalSign, guardado no projeto. Nunca desliga a verificação. 🟢
   - Origem: diagnóstico de 2026-10-13 (`openssl s_client`; intermediário baixado do endereço indicado no próprio certificado)
   - Tipo: nova
8. **RN-08:** Acesso pelo degrau `script` da escada; sem login; sem Apify. Bloqueio vira alerta (regra da feature 003). 🟢
   - Tipo: mantida
9. **RN-09:** O sistema continua sem dar lances e sem usar a área de usuário. 🟢
   - Tipo: mantida
10. **RN-10:** Lote **"EM LOTEAMENTO"** (card com lote "X" e número provisório, 700 em diante) não entra na filtragem: fica de fora, com a contagem no log, até ganhar número definitivo. O número provisório deve mudar no loteamento, e com ele o identificador, o que geraria aviso duplicado do mesmo carro. 🟡
   - Origem: plano (D-77), auditoria de 2026-10-13 (A002)
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve aceitar o Freitas em `config/leiloeiros.yaml` como leiloeiro público, nível `script`, com busca declarada por filtros do site (`categoria: 1`, `condicao: inteiros`) | Must | Com o bloco ativo, a configuração carrega; chave desconhecida aborta antes da rede citando o Freitas | 🟢 |
| RF-02 | O sistema deve coletar todas as páginas da busca até o site indicar o fim ("Nenhum lote localizado") | Must | 225 cards lidos em 2 páginas de 200 mais a página de fim, nenhum repetido; os 21 em loteamento ficam de fora com a contagem no log (RN-10), e 204 lotes seguem para a filtragem (dados de 2026-10-13) | 🟢 |
| RF-03 | O sistema deve converter cada card (exceto os em loteamento, RN-10) em lote normalizado: id pelo leilão e lote, marca e modelo de `MARCA/MODELO VERSÃO`, anos `AA/AA`, preço (maior lance ou inicial), data e hora do pregão, placa parcial, tipo de leilão pela etiqueta e link do detalhe | Must | O card do lote 1 do leilão 8112 produz marca `renault`, modelo `duster intp cvt`, ano de modelo 2024, preço R$ 50.500, pregão 16/10/2026 10:00, tipo `financiamento` e link `…/Leiloes/LoteDetalhes?leilaoId=8112&loteNumero=1` | 🟢 |
| RF-04 | O sistema deve completar, pelo detalhe, o pátio, as despesas operacionais e as observações dos lotes que vão para o aviso ou para a lista | Must | O lote 8112/1 sai com pátio "SANTO ANDRE - SP" (como o site escreve, no mesmo formato da Copart) e despesas R$ 2.350 (as "despesas operacionais" do Freitas, mais as de logística quando houver, vão na linha "Despesas admin." do relatório e da lista) | 🟢 |
| RF-05 | O sistema deve manter a verificação completa do certificado, completando a cadeia com o intermediário oficial guardado no projeto | Must | Sem o intermediário a conexão falha como hoje; com ele, conecta; nenhum caminho do código desliga a verificação | 🟢 |
| RF-06 | O sistema deve tratar o fim da busca sem lotes como busca vazia legítima, e uma resposta fora do formato como quebra com alerta citando o Freitas | Must | Busca sem lotes não alerta; HTML alterado alerta | 🟢 |
| RF-07 | O sistema deve aplicar ao Freitas a semeadura, a deduplicação, o relatório (com a seção "Leiloeiros") e a lista de monitoramento existentes | Must | A primeira varredura não avisa os lotes do Freitas no Telegram, mas os lista no relatório e na lista numerada | 🟢 |
| RF-08 | A falha do Freitas (certificado, bloqueio, rede, quebra) não deve impedir os outros leiloeiros; bloqueio e **falha de certificado** geram alerta (1 por dia), e o alerta de certificado aponta o procedimento de correção (`src/bot_leilao/coleta/certificados/LEIA-ME.md`, o runbook) | Must | Com o Freitas fora, Vip, Kuss e Copart seguem; execução em sucesso parcial; certificado inválido gera alerta citando o LEIA-ME | 🟢 |
| RF-09 | A varredura completa (4 leiloeiros) deve ficar abaixo de 10 minutos | Should | Medida no dry-run real | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Varredura completa abaixo de 10 minutos | Freitas: 3 requisições + 1 por lote detalhado; dry-run da 003 com três leiloeiros: 5m47s | 🟡 |
| Conduta de coleta | 5 s por host; só endpoints públicos; `User-Agent` de navegador | Mesmos princípios | 🟢 |
| Segurança | Verificação de certificado nunca desligada; intermediário com data de validade conferida | RN-07 | 🟢 |
| Custo | Nível `script` | Busca respondeu sem bloqueio em 2026-10-13 | 🟢 |
| Qualidade | Testes sem rede com as amostras reais | Padrão do projeto | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Lotes inteiros do Freitas entram na varredura
  Dado o Freitas ativo no cadastro, com a busca de veículos "Inteiros"
  Quando a varredura é executada
  Então todas as páginas da busca são lidas até o site indicar o fim
  E nenhum lote vem repetido

Cenário: Lote de financeira do Freitas que casa com um alvo é avisado
  Dado uma busca do Freitas já semeada
  E um lote novo "RENAULT/DUSTER INTP CVT, 23/24" com a etiqueta FINANCEIRA e maior lance de R$ 50.500
  E um alvo Renault Duster de 2018 a 2024, com teto de R$ 59.500
  Quando a varredura é executada
  Então o resumo no Telegram traz o lote, identificado como Freitas, com ano 2024, pátio, pregão e link

Cenário: Lote sem a etiqueta de financeira não é avisado
  Dado um lote que casa com um alvo em marca, modelo, ano e preço
  E o card sem a etiqueta FINANCEIRA
  Quando a varredura é executada
  Então o lote não é avisado

Cenário: Certificado com cadeia incompleta não desliga a verificação
  Dado o Freitas enviando o intermediário errado
  Quando o bot conecta usando o intermediário oficial guardado no projeto
  Então a conexão é verificada e a busca é lida

Cenário: Freitas bloqueando não derruba os outros
  Dado o Freitas respondendo bloqueio
  E um lote novo no Vip que casa com um alvo
  Quando a varredura é executada
  Então o lote do Vip é avisado
  E chega um alerta identificando o Freitas
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 a RF-08 | Must | Sem eles o Freitas não entra, ou entra avisando lote errado, ou quebra os outros |
| RF-09 | Should | Meta de tempo herdada |
| Filtro por pátio ou frete | Won't (nesta feature) | Decisão de 2026-10-11: mostrar, não filtrar |

## 9. Esclarecimentos

## 10. Lacunas

- ✅ Respondidas no plano (2026-10-13): pátio e despesas **variam por leilão** (Santa Bárbara d'Oeste-SP no 8103 e 8111; Santo André-SP no 8112; R$ 350 de logística no 8111), então o detalhe é lido por lote; a etiqueta só aparece como "FINANCEIRA" ou vazia; o card tem uma data e uma hora; a troca de certificado tem procedimento próprio (`runbook-certificado.md`).
- 🟡 Em aberto, sem impacto nesta feature: o significado do logo do comitente (id numérico, sem nome no card).

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-13 | Correções do `/reversa-audit` (A001, A002, A004 a A006): pátio no formato do site, RN-10 (lotes em loteamento), alerta de certificado no RF-08, lacunas respondidas, termo de despesas | Claude, com OK do Rafael |
| 2026-10-13 | Versão inicial gerada por `/reversa-requirements` a partir dos prints do Rafael e de 6 requisições ao Freitas (busca, 3 páginas de lotes, detalhe) | reversa |
