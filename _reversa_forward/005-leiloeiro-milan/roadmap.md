# Roadmap: Leiloeiro Milan (e o nível Apify)

> Identificador: `005-leiloeiro-milan`
> Data: `2026-10-13`
> Requirements: `_reversa_forward/005-leiloeiro-milan/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA
> Numeração das decisões: continua a das features anteriores (D-01 a D-85).

## 1. Resumo da abordagem

O Milan entra como quinto par adaptador + parser (`milan-leiloes`), o primeiro no nível **`apify`**. Um cliente novo, `ClienteApify`, tem a mesma operação do `ClienteHTTP` (`requisitar`) e pede a página ao ator `neatrat/cloudflare-scraper`, que passa pelo desafio do Cloudflare e devolve o HTML renderizado. As requisições levam o nível do leiloeiro e um roteador escolhe o cliente; nada do Milan sai pelo IP local.

A busca segue o padrão do Kuss (cursor): agenda de veículos → catálogo de cada leilão "recuperados de financiamento". O catálogo traz todos os lotes numa página (km, câmbio, avisos, comitente), mas não o lance atual. O lance vem da página do lote, **só para os candidatos**, pelo enriquecimento existente, que passa a revalidar o alvo depois do detalhe (lance acima do teto sai do aviso).

Custo e ritmo: US$ 0,08 por página, cerca de US$ 1,90 por mês (limite de US$ 5). O consumo da varredura e do ciclo aparece no relatório, com alerta perto do limite. A opção `--sem-pagos` deixa o atalho do dia a dia sem o Milan. O campo opcional `intervalo_horas` espaça um leiloeiro pago (desligado no Milan). Uma tabela nova mede a antecedência dos anúncios.

Verificações deste plano (2026-10-13, US$ 0,39): seis caminhos de acesso testados, um passou (6 de 6 páginas com status 200); nenhum endereço de dados aberto; catálogo de 15618 com 254 cards (247 no PDF de 11/10); custo real medido pela API. Detalhe em `investigation.md`.

## 2. Princípios aplicados

Não há `.reversa/principles.md`; valem os princípios de fato das features anteriores e das decisões do Rafael.

| Princípio (de fato) | Como a feature se relaciona | Status |
|---------------------|-----------------------------|--------|
| Menor custo | Apify só para leiloeiro em `apify`; lance só dos candidatos; catálogo em uma página; `--sem-pagos`; `intervalo_horas` disponível; consumo visível com alerta a 80% | respeita |
| Regra anti-bot (RN-07, corrigida em 2026-10-13) | Nenhum disfarce no código: o desafio é resolvido pela ferramenta paga do Apify | respeita |
| Não falhar em silêncio | Falhas do Apify com causa (token, cota, tempo, plataforma, desafio) viram alerta; leiloeiro pulado aparece no relatório; catálogo relido para não perder lote inserido | respeita |
| Segurança | Token só no `.env`, só no cabeçalho, mascarado; cookies do ator descartados; ator com permissão limitada; apelidos de licitantes anonimizados nas amostras | respeita |
| Sistema não dá lances | Só leitura de páginas públicas | respeita |
| Conduta de coleta | 5 s por host mantidos; 2 a 4 páginas do Milan por varredura | respeita |
| Automação máxima | Nenhum passo manual recorrente; o bot mede a antecedência e avisa se o intervalo ficar curto | respeita |

## 3. Decisões técnicas

### 3.1 Núcleo: nível `apify`

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-86 | (RF-01, RN-07) Nível `apify` = `ClienteApify` (`src/bot_leilao/coleta/apify.py`), com `requisitar(Requisicao) -> ResultadoHTTP` como o `ClienteHTTP`. Chama `POST /v2/acts/<ator>/run-sync-get-dataset-items?timeout=180` com `{"url": …}` e devolve o `content` do item. Só GET sem corpo: outra requisição é erro interno do adaptador, antes de qualquer chamada paga (contrato `interfaces/apify.md`) | Único caminho que passou: 6 de 6 páginas com status 200 em 2026-10-13. Mesma operação = adaptador, parser e enriquecimento sem mudança de forma | Playwright Scraper oficial (4 combinações de IP e navegador, todas presas no desafio); `pamberton/cloudflare-bypass` (preso); Puppeteer/Web Scraper oficiais (permissão total da conta); Chrome no notebook (exigiria disfarce no código); `cf_clearance` reaproveitado no `httpx` | 🟢 |
| D-87 | (RF-01) Roteamento por nível: campo `Requisicao.nivel` (padrão `script`); o `Coletor` carimba o `nivel_coleta` do leiloeiro em toda requisição, e o enriquecimento também (mapa leiloeiro → nível passado pelo orquestrador); um `ClienteRoteado` entrega ao `ClienteHTTP` ou ao `ClienteApify`. Teste garante que nenhuma requisição de leiloeiro em `apify` chega ao transporte local | Um ponto só de decisão; o enriquecimento (lance do Milan) também precisa ir pelo Apify | Um `Coletor` por nível (duplica laço e falhas); o adaptador escolher o cliente (o nível é configuração, não conhecimento do site) | 🟢 |
| D-88 | Ator por leiloeiro: `apify_ator` no YAML, padrão `neatrat/cloudflare-scraper`. Cada ator tem um **perfil** no código (`PERFIS_ATOR`: como montar a entrada e ler a saída); ator sem perfil aborta a configuração antes da rede. Trocar de ator = um perfil novo (poucas linhas) + uma amostra + teste | Atores da loja têm entradas e saídas diferentes (o `pamberton` usa `start_urls` e devolve `html`; o `neatrat` usa `url` e devolve `content`). Se o `neatrat` parar, há 4 alternativas com permissão limitada (`investigation.md` §3) | Aceitar qualquer ator sem perfil (falharia em silêncio no formato); fila automática de atores reservas (sem segundo ator verificado) | 🟡 |
| D-89 | (RF-06) Falhas do Apify traduzidas com causa: 401 → `FALHA_AUTENTICACAO` "apify: token inválido" (verificado); 402/403 de cota → "apify: cota esgotada"; 408/timeout → "apify: tempo esgotado"; 5xx/conexão → "apify: plataforma indisponível"; item com desafio ou 403/503 → `BLOQUEADO` "desafio_antibot (via apify: <ator>)"; item 404 → `http_404`; lista vazia → "apify: sem resultado". No máximo 2 tentativas, e só para tempo, plataforma, desafio e resultado vazio; nunca para token ou cota (tabela completa no contrato §4) | Cada tentativa custa; token e cota não se resolvem tentando | Reaproveitar os motivos do `script` (a causa "cota" sumiria em "falha de rede", contra o EC-08 da spec) | 🟢 (401) 🟡 (formato exato do erro de cota, não observado) |
| D-90 | (RF-02, RN-06) `APIFY_TOKEN` lido por `carregar_ambiente`; exigido só quando a varredura inclui leiloeiro em `apify` (não com `--sem-pagos`, não se o único pago foi pulado pelo intervalo). Ausente → aborta antes da rede citando o leiloeiro e a variável. Entra em `Ambiente.segredos` (mascarado). Vai só no cabeçalho `Authorization`. `NIVEIS_IMPLEMENTADOS = ("script", "apify")` | RN-08 da 001 (segredos); URL aparece em log, cabeçalho não | Token na query string (é o exemplo da documentação do Apify, mas vazaria em log) | 🟢 |
| D-91 | (RF-09, RN-13) Consumo: o `ClienteApify` conta as páginas da varredura; consulta `GET /v2/users/me/limits` na primeira página paga e no fim, e a diferença é o gasto da varredura. A linha do leiloeiro na seção "Leiloeiros" do relatório ganha "Apify: N página(s), US$ X nesta varredura; ciclo US$ Y de Z até DD/MM". Alerta 1 vez por dia quando o ciclo passar de **80%** do limite (confirmado pelo Rafael em 2026-10-13; responde a OQ-03 da spec do coletor). Falha da consulta → "consumo indisponível", sem derrubar nada | O preço por página está medido, mas pode mudar; o limite da conta é a informação que importa ao Rafael | Calcular por tabela de preço fixa no código (desatualiza em silêncio); consultar o custo de cada execução (exige execução assíncrona e espera) | 🟢 |
| D-92 | (RF-07, RN-05; Won't desde o esclarecimento de 2026-10-13) Troca automática `script` → `apify` **adiada para o backlog** | O ator só faz GET de URL sem corpo nem cabeçalhos: a busca da Copart (POST JSON) e a do Kuss (POST) não passariam por ele, e o cenário 5 do requirements usa justamente a Copart. Nenhum leiloeiro em `script` está bloqueado hoje | Implementar só para buscas GET (Vip, Freitas): código sem uso hoje, e o critério do RF-07 não fecharia | 🟢 |

### 3.2 Contrato com o Milan

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-93 | (RF-03, RN-01) Adaptador `milan-leiloes` com cursor (padrão D-34 do Kuss): página 1 = agenda `/agenda/veiculos`; escolhe os cards `a[href^="/leilao/veiculos/"]` cujo texto normalizado contém o filtro `descricao_contem` (YAML: `recuperados de financiamento`); páginas seguintes = catálogo `/leilao/<id>/catalogo` de cada leilão escolhido. Nenhum escolhido = busca vazia. `teto_paginas = 10`. Filtro desconhecido aborta antes da rede | Agenda de 13/10: judicial 15595 fora, 15618 dentro. O texto do card é o único lugar que diz "recuperados de financiamento" | Filtrar pela categoria (o judicial também é "Veículos") | 🟢 |
| D-94 | (RF-04) O catálogo é lido **em toda varredura** em que o leilão está na agenda | O catálogo do 15618 passou de 247 lotes (PDF de 11/10) para 254 cards (13/10), com lotes "A" inseridos. Ler uma vez perderia lote novo em silêncio. Custo: US$ 0,08 por leilão por varredura. **Muda o que foi dito na conversa de 13/10 ("catálogo uma vez por leilão")** | Guardar o catálogo e reler só na véspera (tabela e regra a mais, ainda perde inserção entre as leituras) | 🟢 |
| D-95 | (RF-04, RF-05, RN-02 a RN-04) Parser do catálogo (regras completas no contrato §3): só veículos (título com `ANO AAAA/AAAA`; materiais contados no log); marca sem `I/` (repetido), marca de duas palavras pela tabela conhecida, senão a primeira palavra; sinônimos novos `m-benz` → `mercedes-benz` e `cintroen` → `citroen`; `jaguar` na lista de marcas conhecidas; km; câmbio; observações = avisos em vermelho + "IPVA AAAA PAGO" + "Comitente <X>" (último parêntese); `(SUCATA)` → sucata; lance inicial do card; `tipo_leilao = financiamento` por herança do leilão; id `milan-leiloes:<leilão>-<lote>`; pregão do cabeçalho ("Início: 14 OUT 09:30", ano inferido, Brasília) | Censo de 13/10: 243 veículos, comitente em 243, 102 avisos em vermelho, 54 lances iniciais, 5 lotes com sufixo A, marcas `M-BENZ` (18), `LAND` [ROVER] (4), `CINTROEN` (1), `JAGUAR` (2) | Comitente por lista de bancos (RN-02 decidiu todos os lotes) | 🟢 |
| D-96 | Pátio = "Cidade - UF" do local do leilão quando o cabeçalho trouxer; senão a cidade do endereço do Milan no rodapé ("São Paulo - SP") | O cabeçalho de 15618 diz só "Rod. Raposo Tavares - Km 20…", com visitação "no local do leilão"; nenhum lote cita outro local | Pátio vazio (o Rafael perderia a referência de frete); endereço completo (foge do formato "Cidade - UF" dos outros leiloeiros) | 🟡 |
| D-97 | (RN-03, RF-04, RF-08) **Lance pelo detalhe, só dos candidatos**: `requisicao_detalhe` = GET `/leilao/<id>/lote/<n>` (pelo Apify, D-87); `aplicar_detalhe`: lance atual → `lance_corrente` (`R$ ---` = sem lance); "LANCE INICIAL" → `lance_inicial`; estado com "RETIRADO" → retirado; "Final Placa N" → `placa_parcial`; câmbio da etiqueta se o catálogo não trouxe. Vale para novos e semeados (mecanismo D-48 e E001 da 002). O RN-03 foi alinhado a esta decisão no esclarecimento de 2026-10-13 | A página do leilão pagina por botões (20 lotes por vez, 13 páginas) e o ator só lê a primeira; ler todos os lances custaria 13 páginas por varredura (~US$ 1,04). Os candidatos são poucos (Creta 046 e os Dusters em 15618) | Página do leilão inteira; lance só na véspera do pregão (sugerido na conversa; o projeto não atualiza lance de lote já avisado, e esperar atrasaria o aviso) | 🟢 (lotes 001, 046, 209) 🟡 (texto de retirado, não observado) |
| D-98 | (RF-14, RN-12) O enriquecimento **revalida o alvo** depois do detalhe (`casa(lote, alvo)` do motor): o lote que deixou de casar (lance acima do teto) sai do aviso e entra na contagem `acima_do_teto`, e o log diz por quê. Vale para todos os leiloeiros | Sem isso, o lote do Milan entraria pelo catálogo sem preço ("preço a confirmar") e seria avisado mesmo com lance acima do teto. Nos outros leiloeiros o detalhe não traz preço nem km, então nada muda | Filtrar só no Milan (regra igual tratada em dois lugares) | 🟢 |
| D-99 | (RN-04) Campo novo `Lote.cambio` e `LoteRelatorio.cambio`; a linha "Câmbio" da lista de monitoramento e do relatório sai preenchida quando houver ("automático", "manual", "CVT"), em branco nos outros leiloeiros como hoje. Não filtra | Pedido do Rafael na lista (13/10); filtro de câmbio é o item 1 do backlog | Câmbio nas observações (misturaria dado com aviso) | 🟢 |

### 3.3 Ritmo, custo e antecedência (decisões da conversa de 13/10)

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-100 | (RF-11, RN-09) Opção `varrer --sem-pagos`: pula os leiloeiros com `nivel_coleta` diferente de `script`. A linha deles na seção "Leiloeiros" do relatório diz "não incluído nesta varredura (sem pagos)"; **nada no Telegram nem na `lotes-a-monitorar.md`**; sem alerta; token não exigido. `scripts/varrer.bat` passa a usar `--sem-pagos`; atalho novo `scripts/varrer-completo.bat` sem a opção; agendamento (seg, qua e sex) inalterado, com os 5 | Pedido do Rafael: varreduras manuais sem custo, escolhidas no clique | Pergunta interativa no atalho (passo manual a cada execução); lista de leiloeiros na linha de comando (mais do que o pedido) | 🟢 |
| D-101 | (RF-12, RN-10) Campo opcional `intervalo_horas` por leiloeiro (inteiro de 1 a 720; ausente = toda varredura). O leiloeiro é pulado quando a última coleta normal com pelo menos uma busca ok foi há menos que o intervalo (consulta em `execucao_leiloeiro` + `execucao`; dry-run não conta). Relatório: "pulado pelo intervalo de 72 h (próxima leitura a partir de DD/MM HH:MM)". **O Milan começa sem intervalo** (toda varredura) | Decisão de 13/10: a economia do intervalo é pequena (~US$ 0,40 por mês) e o risco de perder leilão anunciado em cima da hora é real; o campo fica pronto como alavanca | Reaproveitar `frequencia` (é expressão de agendamento, outra semântica, e exigiria interpretá-la) | 🟢 |
| D-102 | (RF-13, RN-11) Antecedência medida pelo bot: tabela nova `evento_visto` (versão 2 do esquema), gravada a partir das anotações de página com evento e pregão (Milan e também o Kuss) em execução normal. Leilão visto pela primeira vez na varredura aparece na linha do leiloeiro: "leilão novo 15700, visto 5 dia(s) antes do pregão". Os leilões da primeira leitura de um leiloeiro ficam com `na_semeadura = 1` e não contam. Com `intervalo_horas` ligado, antecedência menor que o intervalo gera alerta (1 por dia): "anunciou o leilão X com N dia(s) de antecedência, menos que o intervalo de H h; considere baixar `intervalo_horas` em config/leiloeiros.yaml" | Pedido do Rafael: saber a antecedência real sem vigiar; não há histórico público confiável (`investigation.md` §6) | Calcular só no relatório, sem guardar (a primeira vez que o leilão aparece se perderia) | 🟢 |
| D-103 | (RF-06) Alertas do Apify pelo mecanismo por leiloeiro (1 por dia): token inválido, cota esgotada, tempo esgotado ou plataforma fora, com a causa no texto e o que fazer (token: conferir `APIFY_TOKEN`; cota: o Milan volta no próximo ciclo, DD/MM, ou pagar o excedente); desafio não resolvido usa o alerta de bloqueio existente, citando o ator. Os outros leiloeiros seguem | Cenário 4 do requirements; hoje só bloqueio e certificado alertam | Alertar só a falha geral (o Milan ficaria sem cobertura em silêncio) | 🟢 |

## 4. Premissas

Não há `[DÚVIDA]` aberta no requirements. Premissas técnicas deste plano:

| Premissa | Origem | Risco se errada |
|----------|--------|-----------------|
| O ator `neatrat/cloudflare-scraper` continua passando pelo desafio do Milan | 6 de 6 páginas em 2026-10-13 | Alerta de bloqueio "via apify"; troca de ator com perfil novo (D-88) |
| O erro de cota esgotada vem como 402/403 com tipo ou mensagem de "usage"/"limit" | Documentação do Apify; não observado | A causa sairia genérica ("apify: http_402 (…)"), ainda com alerta |
| O número do lote não muda depois de publicado (lotes inseridos ganham sufixo "A") | 15618: 015A, 047A, 074A, 091A, 195A | Aviso duplicado do mesmo carro |
| O leilão escolhido traz a palavra "recuperados de financiamento" no card da agenda | 15618 | Leilão de financiamento não escolhido; o relatório mostraria "0 leilões escolhidos" |
| O endereço de São Paulo vale como pátio enquanto o cabeçalho não citar outra cidade | 15618 | Pátio errado num leilão fora de SP; o link do lote mostra o local |

## 5. Delta arquitetural

| Componente | Arquivo de origem | Tipo de mudança | Resumo |
|------------|-------------------|-----------------|--------|
| Cliente Apify | `coletor-lotes.md` RF-03 | componente-novo | `src/bot_leilao/coleta/apify.py`: `ClienteApify`, `PERFIS_ATOR`, consumo do ciclo (D-86, D-88, D-89, D-91) |
| Roteamento por nível | `coletor-lotes.md` RF-02, RF-03 | componente-novo | `ClienteRoteado` e `Requisicao.nivel` (D-87) |
| Coletor | `coletor-lotes.md` RF-01 | regra-alterada | Carimba o nível do leiloeiro em cada requisição (D-87) |
| Enriquecimento | adendo da 002 (D-48) | regra-alterada | Nível no detalhe; revalida o alvo depois do detalhe (D-87, D-98) |
| Adaptador Milan | `coletor-lotes.md` RF-12 | componente-novo | `src/bot_leilao/coleta/milan.py` (D-93, D-94, D-97) |
| Parser Milan | `parser-lotes.md` | componente-novo | `src/bot_leilao/parsing/milan.py` (D-95 a D-97) |
| Tabela de marcas | `parser-lotes.md` RF-12 | regra-alterada | `m-benz`, `cintroen`, `jaguar` (D-95) |
| Modelo do lote | `parser-lotes.md` §9 | regra-alterada | Campo `cambio` (D-99) |
| Cadastro de leiloeiros | `cadastro-leiloeiros.md` §6 | regra-alterada | `apify` implementado; `intervalo_horas`, `apify_ator` (D-88, D-90, D-101) |
| Ambiente | `notificador-telegram.md` §10 | regra-alterada | `APIFY_TOKEN` (D-90) |
| Banco | `agendador-observabilidade.md` | contrato-alterado | Esquema 2: `evento_visto`; consulta da última coleta (D-101, D-102) |
| Orquestrador | adendos 003 e 004 | regra-alterada | Seleção da varredura (`--sem-pagos`, intervalo), clientes por nível, consumo, antecedência, alertas do Apify (D-90, D-91, D-100 a D-103) |
| Linha de comando | `interfaces/cli.md` da 001 | contrato-alterado | `varrer --sem-pagos` (D-100) |
| Relatório e lista | emendas E001/E002 da 001, E001 da 003 | regra-alterada | Câmbio preenchido; linhas novas na seção "Leiloeiros" (D-91, D-99 a D-102) |
| Atalhos | `scripts/` | regra-alterada (dados) | `varrer.bat` com `--sem-pagos`; `varrer-completo.bat` novo (D-100) |
| Cadastro | `config/leiloeiros.yaml`, `.env.example` | regra-alterada (dados) | Bloco do Milan; `APIFY_TOKEN` |
| Spec do coletor | `_reversa_sdd/sdd/coletor-lotes.md` NG-03, decisão sobre termos de uso, OQ-03 | regra-alterada (spec) | NG-03 ("Resolver CAPTCHA" fora de escopo) superada pela regra anti-bot (RN-07); OQ-03 respondida (alerta a 80%, RN-13). Correção do texto da spec no `/reversa-sync` da 005 |
| Spec do onboarding assistido | `_reversa_sdd/sdd/onboarding-leiloeiro-assistido.md` NG-02, EC-02 | regra-alterada (spec) | Diante de desafio anti-bot, recomendar a ferramenta robusta (mesmo paga) em vez de só encerrar (RN-07). Correção do texto no `/reversa-sync` da 005 |

Fora do delta: motor de filtros (regras inalteradas; só passa a ser chamado também pelo enriquecimento), digest do Telegram, semeadura, deduplicação, alerta de certificado.

## 6. Delta no modelo de dados

- Campos novos em memória: `Lote.cambio`, `LoteRelatorio.cambio`, `Requisicao.nivel`, `Leiloeiro.intervalo_horas`, `Leiloeiro.apify_ator`, `Ambiente.apify_token`, `ResultadoEnriquecimento.acima_do_teto`.
- Banco: versão 1 → 2 com a tabela `evento_visto`; migração automática.
- Detalhe completo em: `_reversa_forward/005-leiloeiro-milan/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Apify: execução síncrona do ator e limites da conta | HTTP (API) | `_reversa_forward/005-leiloeiro-milan/interfaces/apify.md` |
| Milan: agenda, catálogo e página do lote (via Apify) | HTTP (HTML) | `_reversa_forward/005-leiloeiro-milan/interfaces/milan.md` |

## 8. Plano de migração

1. Banco sobe sozinho da versão 1 para a 2 na primeira execução.
2. Ordem de implementação: `Requisicao.nivel` + `ClienteApify` + roteador (com Apify simulado) → token, níveis e campos do cadastro → adaptador e parser do Milan com as amostras → detalhe e revalidação no enriquecimento → câmbio na lista → `--sem-pagos`, intervalo, antecedência, consumo e alertas → atalhos, bloco no YAML e dry-run real.
3. A primeira varredura real com o Milan semeia a busca: candidatos (com lance do detalhe) no relatório e na lista, sem Telegram.
4. Reversão: `ativo: false` no bloco do Milan (ou rodar com `--sem-pagos`).

## 9. Riscos e mitigações

| ID | Risco | Impacto | Probabilidade | Mitigação |
|----|-------|---------|---------------|-----------|
| R-01 | O ator deixa de passar pelo Cloudflare ou é abandonado | alto (Milan sem cobertura) | média | Alerta de bloqueio citando o ator; troca por outro ator da loja com perfil novo (D-88); 4 alternativas listadas |
| R-02 | Cota do ciclo esgota (varreduras manuais completas em excesso, preço do ator sobe) | médio | baixa | Alerta a 80% (D-91); `--sem-pagos` no atalho; `intervalo_horas` |
| R-03 | O Milan muda o HTML (classes do Next.js com sufixo gerado) | médio | média | Seletores por prefixo e por texto; quebra vira alerta do parser |
| R-04 | Candidato com lance acima do teto é detalhado de novo a cada varredura (não é registrado como conhecido) | baixo (US$ 0,08 por lote por varredura) | média | Poucos candidatos por leilão; registrado no regression-watch para rever se o custo aparecer |
| R-05 | Lote inserido no catálogo depois da última varredura antes do pregão | baixo | baixa | Catálogo lido em toda varredura (D-94); varredura manual completa na véspera, se o Rafael quiser |
| R-06 | A semeadura do Milan cai no dia do pregão do 15618 (14/10) e lê lotes já encerrados | baixo | alta | Sem efeito: é semeadura; os lotes ficam conhecidos |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Os cenários 1 a 5 do requirements passam em testes sem rede, com Apify simulado e as amostras reais (o cenário 5 é o da varredura sem pagos; a troca automática é Won't, D-92)
- [ ] Teste que garante que nenhuma requisição do Milan chega ao transporte local, e que o token não aparece em log, banco nem relatório
- [ ] Suíte anterior verde (608 testes)
- [ ] Dry-run real com `varrer-completo.bat`: Milan lido pelo Apify, consumo no log; varredura com os 5 leiloeiros abaixo de 10 minutos (RF-10)
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-13 | Alinhado ao esclarecimento pós-audit: decisões citam RN-09 a RN-13 e RF-08, RF-11 a RF-14; specs com regra antiga no delta (§5); cenário 5 novo no critério de pronto | `/reversa-clarify` |
| 2026-10-13 | Versão inicial gerada por `/reversa-plan`, com 6 testes de acesso pelo Apify, custo medido e 6 amostras reais | reversa |
