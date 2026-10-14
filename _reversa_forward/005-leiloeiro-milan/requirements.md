# Requirements: Leiloeiro Milan (e o nível Apify)

> Identificador: `005-leiloeiro-milan`
> Data: `2026-10-13`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Acrescenta o quinto e último leiloeiro da lista do Rafael: **Milan Leilões** (Rod. Raposo Tavares, km 20 - SP). O Milan faz leilões por evento; o de interesse é o de "veículos de diversos comitentes, recuperados de financiamento" (15618, pregão em 2026-10-14: 254 cards no catálogo de 2026-10-13, 243 veículos, quase todos de bancos e financeiras). Para cada leilão, o **catálogo** traz numa página só a km, o câmbio, o estado e o comitente de todos os lotes, mas não o lance atual; o lance atual é lido da **página de cada lote**, só para os lotes que casam com um alvo (RN-03).

O site inteiro está atrás do **Cloudflare "managed"**: o bot recebe 403 (desafio) até no `robots.txt` (2026-10-11 e 2026-10-13), enquanto o navegador do Rafael abre tudo, inclusive em janela anônima e sem login. Por isso esta feature implementa o **nível `apify`** previsto na spec do coletor (RF-03) e a **escada** decidida pelo Rafael em 2026-10-11 (backlog item 9): usar o Apify estritamente no necessário, subindo de degrau só quando o anterior falhar.

## 2. Contexto a partir do legado

Projeto greenfield com as features 001 a 004 entregues.

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/prd.md#4` | Lista-alvo (Freitas, Vip, Claudio Kuss, Copart, Milan); meta de ≥ 5 leiloeiros | 🟢 |
| `_reversa_sdd/ideation.md` | Começar gratuito e escalar para o Apify só quando justificado | 🟢 |
| `_reversa_sdd/sdd/coletor-lotes.md#6` (v1.1) | RF-03: níveis `apify` e `apify_residencial` delegam a requisição à Apify; EC-06 (página que só renderiza com JavaScript); EC-08 (cota esgotada com mensagem explícita); rollout gradual por nível | 🟢 |
| `_reversa_sdd/sdd/cadastro-leiloeiros.md#6` | Campo `nivel_coleta` (`script`, `apify`, `apify_residencial`); hoje só `script` está implementado (recusado como "não implementado") | 🟢 |
| `_reversa_sdd/addenda/002-leiloeiro-claudio-kuss.md` | Leilão por evento descoberto na agenda; anotações por página; observações no aviso | 🟢 |
| `_reversa_sdd/addenda/003-leiloeiro-copart.md` e `004-leiloeiro-freitas.md` | Pátio, FIPE, alerta de bloqueio e de certificado por leiloeiro, seção "Leiloeiros" no relatório, lista numerada, tipo por lote | 🟢 |
| `_reversa_forward/backlog.md#9` | Escada: script → Apify com IP de datacenter → IP residencial → IP fixo; economia (reaproveitar o cookie de liberação); regra anti-bot do Rafael (não quebrar a cabeça contornando proteção no próprio código: usar a ferramenta robusta, mesmo paga) | 🟢 |
| Prints do Rafael (2026-10-11 e 2026-10-13) e catálogo em PDF de 2026-10-11 | Agenda, página do leilão e catálogo abrem sem login; lance na página do leilão; km, câmbio, estado e comitente no catálogo | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Rafael, comprador | Ver os carros de financeira do Milan sem abrir o site | O resumo traz um Creta 2022 automático do Milan, com km, lance, pregão, pátio e "Comitente Banco Honda" 🟢 |
| Rafael, dono do orçamento | Gastar o mínimo com Apify | O Apify só é usado para leiloeiros declarados em `apify` (hoje, o Milan), com poucas páginas por varredura, fora das varreduras sem pagos, e o consumo fica visível, com alerta a 80% do limite 🟢 |
| Rafael, operador | Não ser enganado por silêncio | Se o Apify falhar, esgotar a cota ou o token estiver errado, chega alerta claro, e os outros leiloeiros seguem 🟢 |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** O bot considera os leilões da agenda de veículos do Milan (`/agenda/veiculos`) cuja descrição indica **recuperados de financiamento**; leilões judiciais e de outros tipos ficam de fora. 🟢
   - Origem: agenda de 2026-10-13 (um judicial, um "recuperados de financiamento")
   - Tipo: nova
2. **RN-02:** Os lotes de um leilão "recuperados de financiamento" recebem `tipo_leilao = financiamento`, por herança do leilão, e o **comitente** de cada lote (ex.: Grupo Safra, Banco Honda, Locadora Grillo) vai para as observações. **Todos os lotes desses leilões são aceitos**, como no Claudio Kuss: o comitente aparece no aviso e na lista para o Rafael julgar (lote de locadora ou montadora não é descartado automaticamente). 🟢
   - Origem: catálogo de 2026-10-11 (115 de ~125 carros de banco ou financeira; locadora, montadora e comitente não informado no resto); decisão do Rafael na sessão de esclarecimento de 2026-10-13
   - Tipo: nova
3. **RN-03:** Do catálogo vêm km, câmbio, estado (texto do lote, inclusive avisos como "VEÍCULO NÃO FUNCIONA, MOTOR VIRA MAS NÃO PEGA"), comitente e, em alguns lotes, o lance inicial. O **lance atual** vem da **página de cada lote**, lida **só para os lotes que casam com um alvo** (candidatos novos e semeados), pelo detalhe do lote. 🟢
   - Origem: esclarecimento de 2026-10-13 (a página do leilão mostra 20 lotes por vez, trocados por botões; ler todos os lances custaria 13 páginas por varredura)
   - Tipo: nova
4. **RN-04:** O **câmbio** informado pelo Milan é registrado no lote e mostrado (lista de monitoramento: linha "Câmbio" preenchida). Ele ainda **não filtra** (o filtro de câmbio é o item 1 do backlog). 🟢
   - Tipo: nova
5. **RN-05:** **Escada de acesso** (backlog item 9): cada leiloeiro declara o degrau em que roda (`nivel_coleta`). O Milan roda em `apify`. Um leiloeiro em `script` que for **bloqueado** só alerta (comportamento atual). A troca automática `script` → `apify` fica **fora desta feature** e vai para o backlog. 🟢
   - Origem: decisão do Rafael em 2026-10-11; esclarecimento de 2026-10-13 (o ator do Apify só abre endereço simples, sem dados no pedido; Copart e Kuss enviam dados; nenhum leiloeiro em `script` está bloqueado)
   - Tipo: nova
6. **RN-06:** O Apify é usado **estritamente no necessário**: só para leiloeiros em `apify`, com o menor número de páginas possível, e sem gastar esforço contornando proteção no próprio código do bot (RN-07). O token do Apify fica só no `.env` e nunca aparece em log, banco ou relatório. 🟢
   - Origem: backlog item 9; RN-08 da feature 001 (segredos)
   - Tipo: nova
7. **RN-07:** **Regra anti-bot:** não se gasta esforço contornando proteção anti-bot (Cloudflare, Imperva, Turnstile, CAPTCHA) no próprio código nem com remendos locais. Quando o degrau atual não passar, a saída é a **ferramenta mais robusta disponível, mesmo paga** (Apify, ator da loja do Apify ou serviço de desbloqueio), que resolve o desafio do lado dela. Resolver CAPTCHA ou Turnstile **por meio dessa ferramenta é permitido**. Se nenhuma ferramenta resolver, o Milan fica sem cobertura e o bot alerta. 🟢
   - Origem: Rafael, 2026-10-11 e 2026-10-13 (correção explícita: a regra nunca foi "CAPTCHA proibido"; a leitura antiga da D-30 da 001 está superada)
   - Tipo: alterada
8. **RN-08:** O sistema continua sem dar lances. 🟢
   - Tipo: mantida
9. **RN-09:** **Varredura sem pagos:** a varredura pode ser executada sem os leiloeiros pagos (nível diferente de `script`). O atalho do dia a dia (`varrer.bat`) roda sem eles, sem custo; o atalho `varrer-completo.bat` roda com todos; o agendamento (seg, qua e sex) roda com todos. O leiloeiro deixado de fora aparece só na seção "Leiloeiros" do relatório da varredura ("não incluído nesta varredura (sem pagos)"), nunca na lista de monitoramento nem no Telegram, e não gera alerta. 🟢
   - Origem: Rafael, 2026-10-13
   - Tipo: nova
10. **RN-10:** **Intervalo por leiloeiro:** um leiloeiro pode declarar `intervalo_horas` (opcional) e só é lido se a última leitura bem-sucedida foi há pelo menos esse tempo; nas outras varreduras a seção "Leiloeiros" diz "pulado pelo intervalo". O Milan começa **sem intervalo** (lido em toda varredura em que estiver incluído). 🟢
    - Origem: Rafael, 2026-10-13 (economia de ~US$ 0,40 por mês não compensa o risco de perder leilão anunciado em cima da hora; o campo fica pronto)
    - Tipo: nova
11. **RN-11:** **Antecedência dos anúncios:** o bot guarda quando viu cada leilão pela primeira vez e mostra na seção "Leiloeiros" quantos dias antes do pregão ele foi visto. Os leilões já existentes na primeira leitura de um leiloeiro não contam. Se o leiloeiro tiver `intervalo_horas` e um leilão aparecer com menos antecedência que o intervalo, chega um alerta sugerindo baixar o intervalo. 🟢
    - Origem: Rafael, 2026-10-13 (não há histórico público confiável da antecedência do Milan)
    - Tipo: nova
12. **RN-12:** **Teto conferido depois do detalhe:** quando o detalhe do lote traz o lance, o lote é conferido de novo contra o alvo; se passou do teto, não é avisado. Vale para todos os leiloeiros (nos outros o detalhe não traz preço, e nada muda). 🟢
    - Origem: esclarecimento de 2026-10-13 (consequência do RN-03)
    - Tipo: nova
13. **RN-13:** **Alerta de gasto no Apify:** quando o gasto do ciclo mensal passa de **80% do limite da conta** (hoje US$ 4 de US$ 5), chega um alerta no Telegram, no máximo 1 por dia. 🟢
    - Origem: Rafael, 2026-10-13 (responde a OQ-03 da spec do coletor)
    - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve implementar o nível de coleta `apify`: a requisição é feita pela plataforma Apify, que devolve o HTML renderizado, com o token lido do `.env` | Must | Um leiloeiro com `nivel_coleta: apify` carrega sem o erro "não implementado"; a requisição não parte do IP local; o registro da busca mostra `nivel_usado: apify` | 🟡 |
| RF-02 | O sistema deve validar, antes da rede, que existe token do Apify quando a varredura **inclui** leiloeiro em `apify` (não com `--sem-pagos`, nem quando o único pago foi pulado pelo intervalo) | Must | Sem `APIFY_TOKEN` no `.env`, a varredura com o Milan incluído aborta citando o leiloeiro e a variável; com `--sem-pagos`, segue sem token; o token nunca aparece em log, banco ou relatório | 🟢 |
| RF-03 | O sistema deve descobrir, a cada varredura em que o Milan estiver incluído (RN-09, RN-10), os leilões da agenda de veículos do Milan cuja descrição indica recuperados de financiamento | Must | Com a agenda de 2026-10-13, só o leilão 15618 (14/10 09:30) é selecionado; o judicial fica de fora | 🟢 |
| RF-04 | O sistema deve ler, de cada leilão selecionado, o catálogo (em toda varredura, porque lotes são inseridos depois) e, dos lotes que casam com um alvo, a página do lote, de onde vem o lance atual (RN-03) | Must | Com o catálogo de 2026-10-13, os 243 veículos do 15618 (de 254 cards; 11 materiais descartados) saem com título, ano, km, câmbio, estado, comitente e, quando houver, lance inicial; os candidatos ganham o lance atual da página do lote | 🟢 |
| RF-05 | O sistema deve converter cada lote em lote normalizado: id único (leilão e lote), marca e modelo, ano de modelo, km, lance, pregão, pátio do leilão, câmbio, observações (estado e comitente) e link do lote | Must | O lote 046 do 15618 (amostra de 2026-10-13) sai como `milan-leiloes:15618-046`, Hyundai Creta 2022, km 99.020, câmbio automático, sem lance ainda ("preço a confirmar"), pregão 14/10/2026 09:30, pátio São Paulo - SP, observações com "IPVA 2026 PAGO" e "Comitente Banco Honda"; um lote com aviso em vermelho traz o aviso nas observações | 🟢 |
| RF-06 | O sistema deve distinguir as falhas do Apify (token inválido, cota esgotada, plataforma fora, desafio não resolvido) e alertar com mensagem que diga a causa | Must | Cota esgotada gera alerta "cota do Apify esgotada" (EC-08 da spec), e não "falha de rede" | 🟡 |
| RF-07 | ~~Troca automática `script` → `apify` quando o `script` for bloqueado~~ **Fora desta feature** (RN-05): vai para o backlog | Won't | — | 🟢 |
| RF-08 | O sistema deve aplicar ao Milan a semeadura, a deduplicação, o relatório, a lista de monitoramento e o alerta por leiloeiro existentes | Must | A primeira varredura não avisa os lotes do Milan, mas os lista nos documentos | 🟢 |
| RF-09 | O sistema deve registrar o consumo do Apify por varredura (páginas, gasto da varredura e gasto do ciclo contra o limite) no log e no relatório, e alertar a 80% do limite (RN-13) | Should | O relatório da varredura mostra as páginas e o gasto pelo Apify; com o ciclo acima de 80%, chega 1 alerta por dia | 🟢 |
| RF-10 | A varredura completa (5 leiloeiros) deve ficar abaixo de 10 minutos | Should | Medida no dry-run real | 🟡 |
| RF-11 | O sistema deve aceitar a opção `--sem-pagos` na varredura e oferecer os atalhos `varrer.bat` (sem pagos) e `varrer-completo.bat` (com todos) (RN-09) | Must | Com `--sem-pagos`, nenhuma chamada ao Apify, token não exigido e a linha "não incluído nesta varredura (sem pagos)" só na seção "Leiloeiros" | 🟢 |
| RF-12 | O sistema deve aceitar `intervalo_horas` opcional por leiloeiro (inteiro de 1 a 720) e pular o leiloeiro lido há menos tempo (RN-10) | Should | Com `intervalo_horas: 72` e leitura há 48 h, o Milan é pulado com a linha "pulado pelo intervalo" e a data da próxima leitura; dry-run não conta como leitura | 🟢 |
| RF-13 | O sistema deve guardar quando viu cada leilão pela primeira vez e mostrar a antecedência no relatório, com alerta quando ela for menor que o intervalo (RN-11) | Should | Leilão novo aparece como "visto N dia(s) antes do pregão"; os da primeira leitura não contam | 🟢 |
| RF-14 | O sistema deve conferir o lote contra o alvo de novo depois do detalhe e não avisar o que passou do teto (RN-12) | Must | O Creta com lance de R$ 70.000 no detalhe e teto de R$ 55.000 não é avisado | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Custo | Uso do Apify dentro do plano gratuito (US$ 5 por ciclo); estimativa de ~US$ 1,90 por mês | US$ 0,08 por página (medido em 2026-10-13): agenda em toda varredura, catálogo de cada leilão de financiamento, página de cada lote candidato; 13 varreduras por mês | 🟢 |
| Segurança | `APIFY_TOKEN` só no `.env`; mascarado em todo texto gravado | RN-08 da 001 | 🟢 |
| Conduta de coleta | Proteção anti-bot resolvida por ferramenta robusta (mesmo paga), nunca por remendo no código (RN-07); 5 s entre requisições ao mesmo host também pela ferramenta | Rafael, 2026-10-13; backlog item 9 | 🟢 |
| Desempenho | Varredura completa abaixo de 10 minutos | 6m43s com 4 leiloeiros (2026-10-13); o Apify leva segundos por página | 🟡 |
| Qualidade | Testes sem rede (Apify simulado), com fixtures reais do Milan obtidas pelo próprio Apify | Padrão do projeto | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Lotes de financiamento do Milan entram na varredura pelo Apify
  Dado o Milan ativo com nivel_coleta apify e o token do Apify no .env
  E a agenda com um leilão judicial e um de recuperados de financiamento
  Quando a varredura é executada
  Então só o leilão de financiamento é lido, pelo catálogo
  E o lance dos lotes que casam com um alvo vem da página de cada lote
  E nenhuma requisição ao Milan parte do IP local

Cenário: Lote do Milan que casa com um alvo é avisado com km, câmbio e comitente
  Dado uma busca do Milan já semeada
  E um lote novo "HYUNDAI CRETA ACTION 1.6 FLEX 4P ANO 2022/2022", km 99.020, automático, comitente Banco Honda, com lance de R$ 50.000
  E um alvo Hyundai Creta de 2017 a 2022 com teto de R$ 55.000
  Quando a varredura é executada
  Então o resumo traz o lote, identificado como Milan, com ano 2022, km, pátio, pregão, câmbio e comitente nas observações

Cenário: Sem token do Apify a configuração aborta antes da rede
  Dado o Milan ativo com nivel_coleta apify
  E o .env sem APIFY_TOKEN
  Quando a varredura é executada
  Então ela aborta antes de qualquer requisição, citando o Milan e a variável

Cenário: Cota do Apify esgotada vira alerta claro
  Dado o Apify respondendo cota esgotada
  Quando a varredura é executada
  Então chega um alerta dizendo que a cota do Apify acabou
  E Vip, Claudio Kuss, Copart e Freitas seguem normalmente

Cenário: Varredura sem pagos não usa o Apify
  Dado o Milan ativo com nivel_coleta apify
  Quando a varredura é executada com --sem-pagos
  Então nenhuma chamada ao Apify é feita e o token não é exigido
  E a seção "Leiloeiros" do relatório diz que o Milan não foi incluído nesta varredura
  E a lista de monitoramento e o Telegram não citam o Milan
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 a RF-06, RF-08, RF-11, RF-14 | Must | Sem eles o Milan não entra, o Apify gasta sem controle ou falha em silêncio, ou um lote acima do teto é avisado |
| RF-09, RF-10, RF-12, RF-13 | Should | Controle de custo, meta de tempo e ritmo |
| RF-07 (troca automática) | Won't (nesta feature) | O ator só abre endereço simples; Copart e Kuss enviam dados no pedido; nenhum leiloeiro em `script` bloqueado (backlog) |
| `apify_residencial` e IP fixo | Won't (nesta feature) | Degraus seguintes da escada, só se o ator atual deixar de passar |

## 9. Esclarecimentos

### Sessão 2026-10-13

- **Q:** Os leilões "recuperados de financiamento" do Milan misturam comitentes (bancos e financeiras na maioria; locadora, montadora e comitente não informado no resto). Considerar todos os lotes, ou só os de banco ou financeira?
  **R:** Todos, com o comitente nas observações (recomendação aceita). Regra igual à do Claudio Kuss, sem lista de bancos para manter, sem perder carro bom de locadora. Registrado em RN-02.

### Sessão 2026-10-13 (depois do plano e do `/reversa-audit`)

- **Q:** Troca automática `script` → `apify` (RF-07, cenário 5, segunda metade do RN-05): implementar agora ou adiar?
  **R:** Fica fora desta feature e vai para o backlog (recomendação aceita). O ator do Apify só abre endereço simples; Copart e Kuss enviam dados no pedido; nenhum leiloeiro em `script` está bloqueado. Registrado em RN-05, RF-07 e §8; o cenário 5 passou a ser o da varredura sem pagos.
- **Q:** De onde vem o lance atual (RN-03, RF-04, cenário 1)?
  **R:** Da página de cada lote, só para os lotes que casam com um alvo (recomendação aceita), a US$ 0,08 por candidato, em vez de 13 páginas do leilão por varredura. Registrado em RN-03, RF-04 e cenário 1.
- **Q:** Qual lote de exemplo no critério do RF-05, já que o lote 001 da amostra de hoje mudou (km 22, sem aviso)?
  **R:** Creta 046 (recomendação aceita). Registrado no RF-05.
- **Q:** A partir de quanto do limite do mês (US$ 5) o bot avisa sobre o gasto no Apify?
  **R:** 80%, US$ 4 (recomendação aceita). Registrado em RN-13 e RF-09.
- **Q:** Registrar no requirements as decisões da conversa de 13/10 (`--sem-pagos` e atalhos, `intervalo_horas` desligado no Milan, antecedência com alerta, teto conferido depois do detalhe)?
  **R:** Registrar tudo como decidido (recomendação aceita). Registrado em RN-09 a RN-12, RF-03 ("a cada varredura em que o Milan estiver incluído") e RF-11 a RF-14.

## 10. Lacunas

- Nenhuma em aberto. A verificação técnica foi respondida pelo plano em 2026-10-13 (`investigation.md`: não há endereço de dados aberto; o ator `neatrat/cloudflare-scraper` passa pelo Cloudflare a US$ 0,08 por página; o navegador do Apify com IP de datacenter ou residencial não passa; pátio em São Paulo - SP; formatos de agenda, catálogo e lote documentados em `interfaces/milan.md`). O token do Apify está no `.env` desde 2026-10-13.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-14 | Correções da segunda auditoria (A001 a A003): RF-02 alinhado ao `--sem-pagos`; troca automática retirada do RN-06 e da persona; resumo com os números e a origem do lance de 2026-10-13 | Claude |
| 2026-10-13 | Segunda sessão de esclarecimento, depois do `/reversa-audit`: RN-03, RN-05, RF-03 a RF-05, RF-07 (Won't), RF-09, cenários 1 e 5, custo e lacunas atualizados; RN-09 a RN-13 e RF-11 a RF-14 novos | `/reversa-clarify` |
| 2026-10-13 | Regra anti-bot corrigida pelo Rafael (RN-06, RN-07, conduta de coleta) | Claude |
| 2026-10-13 | Sessão de esclarecimento: RN-02 (todos os lotes, comitente nas observações) | `/reversa-clarify` |
| 2026-10-13 | Versão inicial gerada por `/reversa-requirements` a partir dos prints do Rafael, do catálogo de 2026-10-11, de 4 requisições de teste (todas com desafio do Cloudflare) e da spec do coletor | reversa |
