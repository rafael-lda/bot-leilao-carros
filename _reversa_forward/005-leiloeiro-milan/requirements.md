# Requirements: Leiloeiro Milan (e o nível Apify)

> Identificador: `005-leiloeiro-milan`
> Data: `2026-10-13`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Acrescenta o quinto e último leiloeiro da lista do Rafael: **Milan Leilões** (Rod. Raposo Tavares, km 20 - SP). O Milan faz leilões por evento; o de interesse é o de "veículos de diversos comitentes, recuperados de financiamento" (em 2026-10-14: 247 lotes, ~125 carros, quase todos de bancos e financeiras). Para cada leilão, o **catálogo** traz numa página só a km, o câmbio, o estado e o comitente de todos os lotes; a **página do leilão** traz o lance atual.

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
| `_reversa_forward/backlog.md#9` | Escada: script → Apify com IP de datacenter → IP residencial → IP fixo; economia (reaproveitar o cookie de liberação); D-30 esclarecida (subir para ferramenta robusta em vez de fabricar disfarces no código) | 🟢 |
| Prints do Rafael (2026-10-11 e 2026-10-13) e catálogo em PDF de 2026-10-11 | Agenda, página do leilão e catálogo abrem sem login; lance na página do leilão; km, câmbio, estado e comitente no catálogo | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Rafael, comprador | Ver os carros de financeira do Milan sem abrir o site | O resumo traz um Creta 2022 automático do Milan, com km, lance, pregão, pátio e "Comitente Banco Honda" 🟢 |
| Rafael, dono do orçamento | Gastar o mínimo com Apify | O Apify só é usado para o Milan (e para outro leiloeiro só se ele passar a bloquear), com poucas páginas por varredura, e o consumo fica visível 🟡 |
| Rafael, operador | Não ser enganado por silêncio | Se o Apify falhar, esgotar a cota ou o token estiver errado, chega alerta claro, e os outros leiloeiros seguem 🟢 |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** O bot considera os leilões da agenda de veículos do Milan (`/agenda/veiculos`) cuja descrição indica **recuperados de financiamento**; leilões judiciais e de outros tipos ficam de fora. 🟢
   - Origem: agenda de 2026-10-13 (um judicial, um "recuperados de financiamento")
   - Tipo: nova
2. **RN-02:** Os lotes de um leilão "recuperados de financiamento" recebem `tipo_leilao = financiamento`, por herança do leilão, e o **comitente** de cada lote (ex.: Grupo Safra, Banco Honda, Locadora Grillo) vai para as observações. [DÚVIDA: aceitar todos os lotes desses leilões, como no Claudio Kuss, ou só os de comitente banco ou financeira?] 🔴
   - Origem: catálogo de 2026-10-11 (115 de ~125 carros de banco ou financeira; locadora, montadora e comitente não informado no resto)
   - Tipo: nova
3. **RN-03:** Do catálogo vêm km, câmbio, estado (texto do lote, inclusive avisos como "VEÍCULO NÃO FUNCIONA, MOTOR VIRA MAS NÃO PEGA") e comitente; da página do leilão vem o **lance atual**. Os dois se juntam pelo número do lote. 🟢
   - Tipo: nova
4. **RN-04:** O **câmbio** informado pelo Milan é registrado no lote e mostrado (lista de monitoramento: linha "Câmbio" preenchida). Ele ainda **não filtra** (o filtro de câmbio é o item 1 do backlog). 🟢
   - Tipo: nova
5. **RN-05:** **Escada de acesso** (backlog item 9): cada leiloeiro declara o degrau em que roda (`nivel_coleta`). O Milan roda em `apify`. Um leiloeiro em `script` que for **bloqueado** pode, se o Rafael tiver habilitado a troca automática para ele, ser tentado de novo em `apify` na mesma varredura; sem essa habilitação, só alerta (comportamento atual). 🟡
   - Origem: decisão do Rafael em 2026-10-11 ("quando passar sem bloqueio segue, quando bloquear usa Apify"); spec do coletor RF-03
   - Tipo: nova
6. **RN-06:** O Apify é usado **estritamente no necessário**: só para leiloeiros em `apify` (ou na troca automática), com o menor número de páginas possível, e sem nenhum disfarce fabricado no código do bot. O token do Apify fica só no `.env` e nunca aparece em log, banco ou relatório. 🟢
   - Origem: backlog item 9; RN-08 da feature 001 (segredos)
   - Tipo: nova
7. **RN-07:** O sistema não resolve CAPTCHA, não faz login e não usa a área do cliente. Se o Cloudflare exigir interação humana mesmo pelo Apify, o Milan fica sem cobertura e o bot alerta. 🟢
   - Origem: D-30 da 001 (CAPTCHA proibido, mantido na revisão de 2026-10-11)
   - Tipo: mantida
8. **RN-08:** O sistema continua sem dar lances. 🟢
   - Tipo: mantida

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve implementar o nível de coleta `apify`: a requisição é feita pela plataforma Apify, que devolve o HTML renderizado, com o token lido do `.env` | Must | Um leiloeiro com `nivel_coleta: apify` carrega sem o erro "não implementado"; a requisição não parte do IP local; o registro da busca mostra `nivel_usado: apify` | 🟡 |
| RF-02 | O sistema deve validar, antes da rede, que existe token do Apify quando algum leiloeiro ativo usa `apify` | Must | Sem `APIFY_TOKEN` no `.env`, a configuração aborta citando o leiloeiro e a variável; o token nunca aparece em log, banco ou relatório | 🟢 |
| RF-03 | O sistema deve descobrir, a cada varredura, os leilões da agenda de veículos do Milan cuja descrição indica recuperados de financiamento | Must | Com a agenda de 2026-10-13, só o leilão 15618 (14/10 09:30) é selecionado; o judicial fica de fora | 🟢 |
| RF-04 | O sistema deve ler, de cada leilão selecionado, o catálogo e a página do leilão, juntando os dados pelo número do lote | Must | Os 247 lotes do leilão 15618 saem com título, ano, km, câmbio, estado, comitente e, quando houver, lance atual | 🟡 |
| RF-05 | O sistema deve converter cada lote em lote normalizado: id único (leilão e lote), marca e modelo, ano de modelo, km, lance atual, pregão, pátio do leilão, câmbio, observações (estado e comitente) e link do lote | Must | O lote 001 do 15618 sai como Ford Ranger 2022, km 18, câmbio automático, lance R$ 47.200, observação "VEÍCULO NÃO FUNCIONA, MOTOR VIRA MAS NÃO PEGA · Comitente FORD" | 🟢 |
| RF-06 | O sistema deve distinguir as falhas do Apify (token inválido, cota esgotada, plataforma fora, desafio não resolvido) e alertar com mensagem que diga a causa | Must | Cota esgotada gera alerta "cota do Apify esgotada" (EC-08 da spec), e não "falha de rede" | 🟡 |
| RF-07 | O sistema deve permitir habilitar, por leiloeiro, a troca automática `script` → `apify` quando o `script` for bloqueado | Should | Com a troca habilitada para a Copart e a Copart respondendo desafio, a busca é refeita pelo Apify na mesma varredura; sem a habilitação, só alerta | 🟡 |
| RF-08 | O sistema deve aplicar ao Milan a semeadura, a deduplicação, o relatório, a lista de monitoramento e o alerta por leiloeiro existentes | Must | A primeira varredura não avisa os lotes do Milan, mas os lista nos documentos | 🟢 |
| RF-09 | O sistema deve registrar o consumo do Apify por varredura (requisições e, se a plataforma informar, custo) no log e no relatório | Should | O relatório da varredura mostra quantas requisições foram feitas pelo Apify | 🟡 |
| RF-10 | A varredura completa (5 leiloeiros) deve ficar abaixo de 10 minutos | Should | Medida no dry-run real | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Custo | Uso do Apify dentro do plano gratuito, se possível; custo mensal estimado antes de ativar | Milan: agenda + 2 páginas por leilão (~1 leilão de financiamento por vez) × 3 varreduras por semana | 🟡 |
| Segurança | `APIFY_TOKEN` só no `.env`; mascarado em todo texto gravado | RN-08 da 001 | 🟢 |
| Conduta de coleta | Sem CAPTCHA, sem login, sem disfarce fabricado no código; 5 s entre requisições ao mesmo host também pelo Apify | D-30 da 001; backlog item 9 | 🟢 |
| Desempenho | Varredura completa abaixo de 10 minutos | 6m43s com 4 leiloeiros (2026-10-13); o Apify leva segundos por página | 🟡 |
| Qualidade | Testes sem rede (Apify simulado), com fixtures reais do Milan obtidas pelo próprio Apify | Padrão do projeto | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Lotes de financiamento do Milan entram na varredura pelo Apify
  Dado o Milan ativo com nivel_coleta apify e o token do Apify no .env
  E a agenda com um leilão judicial e um de recuperados de financiamento
  Quando a varredura é executada
  Então só o leilão de financiamento é lido, pelo catálogo e pela página do leilão
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

Cenário: Troca automática para o Apify quando habilitada
  Dado a Copart em script com a troca automática habilitada
  E a Copart respondendo desafio ao script
  Quando a varredura é executada
  Então a busca da Copart é refeita pelo Apify e os lotes são lidos
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 a RF-06, RF-08 | Must | Sem eles o Milan não entra, ou o Apify gasta ou falha em silêncio |
| RF-07 | Should | Troca automática decidida pelo Rafael; hoje nenhum leiloeiro em `script` está bloqueado |
| RF-09, RF-10 | Should | Controle de custo e meta de tempo |
| `apify_residencial` e IP fixo | Won't (nesta feature) | Degraus seguintes da escada, só se o Apify comum não passar |

## 9. Esclarecimentos

## 10. Lacunas

- 🔴 **Verificação técnica para o plano (decide o desenho):** se o Milan busca os lotes num endereço de dados aberto (sem o desafio), o que dispensaria o Apify; qual ator do Apify usar (navegador sem cabeça para passar o desafio do Cloudflare) e o custo real por página; se o desafio "managed" passa pelo Apify com IP de datacenter ou exige IP residencial; o pátio de cada leilão (endereço na página do leilão); se o catálogo e a página do leilão mudam de formato entre leilões.
- 🟡 **Ação do Rafael antes do coding:** criar a conta no Apify (plano gratuito) e pôr o token em `APIFY_TOKEN` no `.env`.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-13 | Versão inicial gerada por `/reversa-requirements` a partir dos prints do Rafael, do catálogo de 2026-10-11, de 4 requisições de teste (todas com desafio do Cloudflare) e da spec do coletor | reversa |
