# Requirements: Leiloeiro Claudio Kuss

> Identificador: `002-leiloeiro-claudio-kuss`
> Data: `2026-10-10`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Acrescenta o segundo leiloeiro ao bot: **Claudio Kuss Leilões** (Curitiba-PR). A cada varredura, o bot passa a ler também os lotes dos eventos "Veículos - Financeiras" do Claudio Kuss, aplicar os mesmos veículos-alvo e avisar no Telegram, nos relatórios e na lista de monitoramento, como já faz com o Vip.

O problema que resolve é o volume baixo: com só o Vip, as varreduras deram 0 ou 1 candidato. A triagem de 2026-10-10 mediu 391 lotes de financeiras no Claudio Kuss, contra 173 no Vip no mesmo dia (que incluem motos), com acesso livre e dados em JSON.

## 2. Contexto a partir do legado

Projeto greenfield com a feature 001 entregue. As fontes abaixo cumprem o papel de extração.

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/prd.md#4` | Cadastro de leiloeiros-alvo; meta de ≥ 5 leiloeiros em 3 meses | 🟡 |
| `_reversa_sdd/sdd/cadastro-leiloeiros.md#6` (v1.3) | Leiloeiro declarado no YAML; busca como filtros chave-valor opacos; leiloeiro ativo exige adaptador e parser registrados (RF-10); diretriz de busca ampla (§6.1.1) | 🟢 |
| `_reversa_sdd/sdd/coletor-lotes.md#6` (v1.1) | Adaptador por leiloeiro (RF-12), sessão, paginação com teto (RF-14), busca atômica (RF-15), 5 s entre requisições ao mesmo host | 🟢 |
| `_reversa_sdd/sdd/parser-lotes.md#6` (v1.3) | Parser por leiloeiro; id canônico único no leiloeiro (RF-06, EC-13); sinônimos de marca comuns (RF-12); busca vazia legítima (EC-15); km sentinela (EC-16) | 🟢 |
| `_reversa_sdd/sdd/onboarding-leiloeiro-assistido.md#Apêndice` (v1.1) | Lista de armadilhas conhecidas, a verificar para cada leiloeiro novo | 🟢 |
| `_reversa_sdd/addenda/001-mvp-varredura-ponta-a-ponta.md` | O que a feature 001 entregou de diferente das specs (lote_conhecido, semeadura por busca, km opcional, retirados, 429 com 30 s) | 🟢 |
| `_reversa_forward/triagem-leiloeiros-2026-10-10.md` | Endpoints JSON, campos, volume e robots do Claudio Kuss; custos de arrematação | 🟢 |
| `_reversa_forward/001-mvp-varredura-ponta-a-ponta/interfaces/vip-pesquisa.md` | Referência de contrato de leiloeiro já implementado | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Rafael, comprador | Ver mais oportunidades sem mudar a rotina | A varredura das 08:00 avisa, no mesmo resumo do Telegram, um Duster do Vip e um Fluence do Claudio Kuss, cada um com o leiloeiro identificado 🟢 |
| Rafael, comprador em Londrina | Saber quando é o pregão, porque o Claudio Kuss é por evento com data | O aviso do lote do Claudio Kuss mostra a data e a hora do leilão 🟡 |
| Rafael, operador | Não ser enganado por silêncio | Se o Claudio Kuss mudar o formato dos dados, chega um alerta identificando o leiloeiro 🟢 |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** O Claudio Kuss organiza os lotes em **eventos** com data e hora marcadas. O bot considera apenas os eventos rotulados **"Veículos - Financeiras"**, descobertos a cada varredura entre os próximos leilões publicados no site. 🟢
   - Origem: triagem 2026-10-10; diretriz de busca ampla, `cadastro-leiloeiros.md#6.1.1`
   - Tipo: nova
2. **RN-02:** Lotes de eventos "Veículos - Financeiras" recebem `tipo_leilao = financiamento`, por herança do evento, como os lotes da busca de procedência 4 do Vip (RN-10 da feature 001). 🟡
   - Origem: `parser-lotes.md` D-15 da 001; rótulo do evento
   - Tipo: nova
3. **RN-03:** O identificador canônico do lote é o `seq` do Claudio Kuss, e não o número do lote, que fica vazio até o lote ser "loteado" e é numeração por evento (armadilha `numero_lote_por_evento`). 🟢
   - Origem: `parser-lotes.md` RF-06 e EC-13
   - Tipo: nova
4. **RN-04:** O ano no formato `AA/AA` (ex.: `16/17`) é convertido para quatro dígitos, mantendo a regra de comparar o **ano de modelo** (RN-02 da 001). 🟢
   - Origem: JSON de lista (`ano`)
   - Tipo: nova
5. **RN-05:** Lote marcado como retirado (`retirado = S` no detalhe) é descartado antes da filtragem, como no Vip (RN-12 da 001). 🟢
   - Origem: JSON de detalhe; RN-12 da 001
   - Tipo: nova
6. **RN-06:** O Claudio Kuss não informa quilometragem; os lotes dele são tratados como "km a confirmar" e não são eliminados pelo teto de km (D-19 da 001). 🟢
   - Origem: triagem 2026-10-10
   - Tipo: nova
7. **RN-07:** Lote sem valor antes do pregão (a maioria até perto do leilão; status "Não loteado") é **avisado já**, como "preço a confirmar", junto da data do pregão, pela regra existente de que preço ausente não elimina (RN-04 da 001). O aviso é único: quando o preço aparecer, não há novo aviso; o acompanhamento do lance é feito pela lista de monitoramento, à mão ou por agente. 🟢
   - Origem: decisão do Rafael na sessão de esclarecimento de 2026-10-10
   - Tipo: nova
8. **RN-08:** Todo lote dos eventos "Veículos - Financeiras" é aceito, sem filtro automático de estado. O Claudio Kuss não tem campo de monta e o texto padrão diz "financiamento **ou sinistro**"; as **observações** do lote (ex.: "número da caixa divergente, sem console central") são mostradas no aviso, no relatório e na lista de monitoramento para o Rafael descartar à mão. 🟢
   - Origem: decisão do Rafael na sessão de esclarecimento de 2026-10-10
   - Tipo: nova
9. **RN-09:** O sistema continua sem dar lances, sem login e sem usar a área restrita (`/portal/`, `/winleilao/`, `/contrato/`, bloqueadas no `robots.txt`). 🟢
   - Origem: `prd.md#5`; triagem
   - Tipo: mantida

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve aceitar o Claudio Kuss em `config/leiloeiros.yaml` como leiloeiro público, nível `script`, com uma busca declarada por filtros chave-valor (ex.: `categoria: Veículos - Financeiras`) | Must | Com o bloco do Claudio Kuss ativo, a configuração carrega sem erro; com uma chave de filtro desconhecida, aborta antes da rede citando o leiloeiro | 🟢 |
| RF-02 | O sistema deve descobrir, a cada varredura, os eventos futuros do Claudio Kuss cujo rótulo corresponda à categoria da busca | Must | Com dois eventos "Veículos - Financeiras" publicados, a varredura coleta os lotes dos dois; um evento de outra categoria é ignorado | 🟢 |
| RF-03 | O sistema deve coletar todos os lotes de cada evento descoberto, página a página, conferindo o total contra a quantidade informada pelo site | Must | Um evento com `qtde = 346` resulta em 346 lotes lidos; divergência gera aviso em log | 🟢 |
| RF-04 | O sistema deve converter cada lote em lote normalizado: id canônico pelo `seq`, marca e modelo a partir de `MARCA/MODELO VERSÃO` com a tabela de sinônimos, anos de fabricação e modelo a partir de `AA/AA`, lance corrente, link da página humana do lote e tipo de leilão herdado | Must | `CHEV/ONIX 10 MT LT1`, `20/21`, `21.600,00` produz marca `chevrolet`, modelo `onix 10 mt lt1`, ano de modelo 2021, lance R$ 21.600 e link `…/lance/897/0/282745` | 🟢 |
| RF-05 | O sistema deve consultar o detalhe **apenas dos lotes que casarem com algum alvo** e descartar os retirados | Must | Um candidato com `retirado = S` não é avisado e entra no contador de retirados | 🟢 |
| RF-06 | O sistema deve incluir no aviso e nos relatórios, para os lotes do Claudio Kuss, a data e a hora do pregão | Should | O resumo mostra "Pregão 13/10 10:00" no item do lote | 🟡 |
| RF-07 | O sistema deve incluir as observações do lote no aviso do Telegram (resumidas, se longas) e, completas, no relatório e na lista de monitoramento, junto das despesas administrativas, quando informadas | Must | O item do lote no resumo traz as observações; o bloco na lista traz "Despesas admin.: R$ 2.750" e o texto completo das observações | 🟢 |
| RF-08 | O sistema deve tratar como busca vazia legítima a ausência de eventos da categoria, ou um evento com `qtde = 0`, e como quebra um evento com `qtde > 0` do qual nenhum lote é extraído | Must | Sem eventos de financeiras, a varredura termina com sucesso e sem alerta; com o formato do JSON alterado, chega alerta identificando o Claudio Kuss | 🟢 |
| RF-09 | O sistema deve aplicar ao Claudio Kuss a semeadura por busca, a deduplicação, o relatório por varredura e a lista de monitoramento já existentes | Must | A primeira varredura com o Claudio Kuss ativo não envia resumo dos lotes dele; a seguinte avisa só os novos | 🟢 |
| RF-10 | A falha do Claudio Kuss (rede, bloqueio, quebra) não deve impedir a coleta e o aviso dos lotes do Vip na mesma varredura, e vice-versa | Must | Com o Claudio Kuss fora do ar, os lotes novos do Vip chegam normalmente e a execução fica como sucesso parcial | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Varredura completa (Vip + Claudio Kuss) em menos de 10 minutos | 35 + 5 páginas a 5 s ≈ 3,5 min para o Kuss, mais o Vip ≈ 2,5 min, mais o detalhe dos candidatos | 🟡 |
| Conduta de coleta | 5 s entre requisições ao mesmo host; só endpoints públicos fora das áreas bloqueadas no `robots.txt`; `User-Agent` de navegador (D-30 da 001) | `coletor-lotes.md` RNF-02; triagem | 🟢 |
| Custo | Nível `script`, sem serviço pago | Acesso livre, sem proteção anti-robô | 🟢 |
| Manutenibilidade | Adaptador e parser do Claudio Kuss em arquivos próprios, registrados pelo id do leiloeiro, sem mexer no núcleo nem no Vip | `parser-lotes.md` RNF-02 | 🟢 |
| Qualidade | Testes sem rede, com fixtures reais do JSON do Claudio Kuss | D-27 da 001 | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Lotes do Claudio Kuss entram na varredura
  Dado o Claudio Kuss ativo no cadastro, com a busca de eventos "Veículos - Financeiras"
  E dois eventos dessa categoria publicados no site
  Quando a varredura é executada
  Então os lotes dos dois eventos são lidos
  E o total lido de cada evento confere com a quantidade informada pelo site

Cenário: Lote do Claudio Kuss que casa com um alvo é avisado
  Dado uma busca do Claudio Kuss já semeada
  E um lote novo "RENAULT/DUSTER ICONIC 1.6 CVT", ano "21/22", com lance de R$ 45.000
  E o alvo Renault Duster 2018–2022 com teto de R$ 59.500
  Quando a varredura é executada
  Então o resumo no Telegram traz o lote, identificado como Claudio Kuss, com ano 2022 e o link da página do lote

Cenário: Candidato retirado não é avisado
  Dado um lote que casa com um alvo
  E o detalhe do lote indica retirado
  Quando a varredura é executada
  Então o lote não é avisado
  E entra no contador de retirados

Cenário: Sem eventos de financeiras não é erro
  Dado que o site não tem nenhum evento "Veículos - Financeiras" publicado
  Quando a varredura é executada
  Então a busca do Claudio Kuss termina sem lotes e sem alerta de quebra

Cenário: Formato alterado vira alerta
  Dado um evento com quantidade de lotes maior que zero
  Quando nenhum lote consegue ser extraído do JSON
  Então chega um alerta identificando o Claudio Kuss

Cenário: Um leiloeiro fora do ar não derruba o outro
  Dado o Claudio Kuss inacessível
  E um lote novo no Vip que casa com um alvo
  Quando a varredura é executada
  Então o lote do Vip é avisado
  E a execução é registrada como sucesso parcial
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 a RF-05, RF-08 a RF-10 | Must | Sem eles o Claudio Kuss não entra, ou entra quebrando o Vip, ou avisa lote retirado |
| RF-06 | Should | Leilão por evento: a data do pregão muda a decisão, mas o link já leva a ela |
| RF-07 | Must | Com RN-08, as observações são a única forma de o Rafael separar o carro conservado do problemático |
| RNF de conduta e custo | Must | Mesmos princípios da 001 |

## 9. Esclarecimentos

### Sessão 2026-10-10

- **Q:** Antes do pregão, a maioria dos lotes do Claudio Kuss não tem valor. Avisar já como "preço a confirmar", ou esperar o lote ter valor?
  **R:** Avisar já (opção a). O aviso antecipado dá tempo de pesquisar, ver fotos e FIPE e visitar o pátio; esperar o valor pode significar avisar só no dia do pregão, ou nunca. O preço passa a ser acompanhado pela lista de monitoramento. Registrado em RN-07.
- **Q:** Os eventos "Financeiras" misturam recuperado de financiamento e de sinistro, sem campo de monta. Aceitar todos e mostrar as observações, ou filtrar automaticamente pelas observações?
  **R:** Aceitar todos e mostrar as observações no aviso, no relatório e na lista (opção a); filtro por palavras em texto livre erraria nos dois sentidos. Registrado em RN-08 e RF-07 (promovido a Must).

## 10. Lacunas

- 🟡 **Verificação técnica para o plano:** grafias de marca do Claudio Kuss (`CHEV/`, `CAOACHERY/`, `VW/`, possíveis prefixos `I/` de importados) frente à tabela de sinônimos; página "próximos leilões" versus página inicial para descobrir eventos; quando o lance inicial (`av`) passa a aparecer no detalhe; se lotes de um evento aparecem também em outro (reaparição).

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-10 | Versão inicial gerada por `/reversa-requirements` a partir da triagem de leiloeiros | reversa |
| 2026-10-10 | Sessão de esclarecimento: RN-07 (avisar lote sem preço) e RN-08 (aceitar todos, mostrar observações) resolvidas; RF-07 vira Must | `/reversa-clarify` |
