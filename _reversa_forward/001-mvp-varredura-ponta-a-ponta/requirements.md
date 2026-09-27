# Requirements: MVP de Varredura Ponta a Ponta

> Identificador: `001-mvp-varredura-ponta-a-ponta`
> Data: `2026-09-25`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Entrega a primeira fatia vertical funcional do Bot Leilão Carros: um veículo-alvo configurado, um leiloeiro público monitorado, e o digest chegando no Telegram do Rafael com os lotes que casaram. Atravessa os oito componentes especificados em `_reversa_sdd/sdd/`, do carregamento do YAML até o envio da mensagem, exercitando a cadeia inteira com o menor escopo possível.

O problema que resolve é o do `prd.md#1`: hoje a busca é manual, fragmentada entre sites de layout distinto, e consome horas por semana sem garantia de cobertura. Esta feature substitui esse trabalho por uma execução verificável, em um único leiloeiro.

O valor de entregar assim, e não componente a componente, é descobrir em dias se a cadeia se sustenta. Construir os oito componentes isolados adiaria essa descoberta para o fim, quando corrigir custa caro.

## 2. Contexto a partir do legado

Este projeto é greenfield: não houve extração reversa de código. Os artefatos abaixo vieram do `/reversa-new` e cumprem o mesmo papel de fonte da verdade que `architecture.md` e `domain.md` cumpririam em um legado.

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/prd.md#4` | Escopo do MVP: configuração de alvos, cadastro de leiloeiros, scraping, parsing, notificação Telegram, execução periódica | 🟡 |
| `_reversa_sdd/prd.md#5` | Não-objetivos: sem lances automáticos, sem multi-usuário, sem interface web, sem pagamento | 🟡 |
| `_reversa_sdd/prd.md#9` | Critérios de aceite: notificar lotes que casam; registrar e avisar quando o parser quebrar; link em 1 clique | 🟡 |
| `_reversa_sdd/ideation.md#estrategia-de-mapeamento-por-url` | A coleta é fetch de URL já filtrada pelo usuário, e não automação de cliques | 🟡 |
| `_reversa_sdd/ideation.md#estrategia-de-escalonamento-progressivo` | Começar em script Python gratuito; Apify só quando justificado | 🟡 |
| `_reversa_sdd/personas.md#persona-1` | Rafael, comprador pessoa física, nível técnico intermediário, edita YAML em editor de texto | 🟡 |
| `_reversa_sdd/sdd/configuracao-veiculos-alvo.md#6` | Esquema do veículo-alvo, validação antes da rede, teto por alvo, campo `ativo` | 🟡 |
| `_reversa_sdd/sdd/cadastro-leiloeiros.md#6` | Esquema do leiloeiro, credencial por variável de ambiente, nível de coleta, frequência | 🟡 |
| `_reversa_sdd/sdd/coletor-lotes.md#6` | Fetch por nível, timeout, retry com espera crescente, isolamento de falha, classificação de bloqueio | 🟡 |
| `_reversa_sdd/sdd/parser-lotes.md#6` | Parser por leiloeiro, normalização de valores e anos, identificador canônico, sinal de quebra | 🟡 |
| `_reversa_sdd/sdd/motor-filtros.md#6` | Critérios de casamento, deduplicação em SQLite, ordem de gravação, modo de semeadura | 🟡 |
| `_reversa_sdd/sdd/notificador-telegram.md#6` | Digest único por execução, confirmação de envio, divisão por limite de tamanho | 🟡 |
| `_reversa_sdd/sdd/agendador-observabilidade.md#6` | Trava de execução, registro do histórico, registro inclusive em falha | 🟡 |
| Decisões do Rafael em 2026-09-21 e 2026-09-22 | Teto por alvo; digest por execução; YAML mais SQLite mais `.env`; ano de modelo; lance corrente; cabeçalho de navegador | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Rafael, comprador | Receber só os carros que interessam, sem abrir site nenhum | Configura um alvo e um leiloeiro no YAML, dispara a varredura, e recebe no Telegram o digest com os lotes que casaram 🟢 |
| Rafael, operador | Saber quando o sistema quebrou, para que silêncio não seja ambíguo | O parser deixa de extrair lotes, e ele recebe um alerta identificando o leiloeiro afetado em vez de um digest vazio 🟡 |
| Agente de IA gestor | Acumular evidência para propor ajustes | Lê o histórico de execuções gravado no SQLite para, mais adiante, recomendar frequência e nível de coleta 🟡 |

## 4. Regras de negócio novas ou alteradas

Todas as regras abaixo são **novas**: o sistema não existe ainda, então não há regra de legado sendo alterada ou removida.

1. **RN-01:** Um lote só é candidato quando satisfaz, para um mesmo veículo-alvo, todos os critérios: marca, modelo, ano de modelo dentro da faixa, lance corrente menor ou igual ao teto, e tipo de leilão aceito. 🟢
   - Origem: `_reversa_sdd/sdd/motor-filtros.md#6`, RF-06
   - Tipo: nova
2. **RN-02:** O ano comparado contra a faixa do alvo é o **ano de modelo**, e não o de fabricação. 🟢
   - Origem: decisão do Rafael em 2026-09-22, registrada em `_reversa_sdd/sdd/motor-filtros.md#15`
   - Tipo: nova
3. **RN-03:** O valor comparado contra o teto é o **lance corrente**, recorrendo ao lance inicial enquanto o lote não tiver recebido nenhum lance. 🟢
   - Origem: decisão do Rafael em 2026-09-22, registrada em `_reversa_sdd/sdd/motor-filtros.md#15`
   - Tipo: nova
4. **RN-04:** Lote sem nenhum valor monetário segue como candidato, marcado como preço a confirmar. Lote sem ano de modelo é descartado por dado insuficiente. 🟡
   - Origem: `_reversa_sdd/sdd/motor-filtros.md#6`, RF-07 e RF-08
   - Tipo: nova
5. **RN-05:** Um lote já notificado nunca é notificado de novo, qualquer que seja a variação de lance posterior. 🟡
   - Origem: `_reversa_sdd/sdd/motor-filtros.md#4`, NG-02
   - Tipo: nova
6. **RN-06:** O registro de um lote como notificado só ocorre **após** a confirmação de envio pelo Telegram. 🟢
   - Origem: `_reversa_sdd/sdd/motor-filtros.md#7`, RNF-03
   - Tipo: nova
7. **RN-07:** Na primeira execução de uma busca, os candidatos são registrados como conhecidos sem gerar notificação. 🟡
   - Origem: `_reversa_sdd/sdd/motor-filtros.md#6`, RF-13
   - Tipo: nova
8. **RN-08:** Nenhuma credencial, token ou senha pode ser gravada em arquivo versionado nem impressa em log. 🟢
   - Origem: `_reversa_sdd/sdd/cadastro-leiloeiros.md#12` e `_reversa_sdd/sdd/notificador-telegram.md#7`
   - Tipo: nova
9. **RN-09:** O sistema não dá lances e não interage com o pregão. Apenas observa, filtra e avisa. 🟢
   - Origem: `_reversa_sdd/prd.md#5`
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve carregar e validar `config/veiculos-alvo.yaml` com ao menos um veículo-alvo ativo, abortando antes de qualquer requisição quando a configuração for inválida | Must | Com um alvo válido a execução prossegue; com `ano_min` maior que `ano_max` a execução aborta citando o alvo e o campo, sem emitir log de coleta | 🟡 |
| RF-02 | O sistema deve carregar e validar `config/leiloeiros.yaml` com um leiloeiro público e uma busca de URL absoluta em `https` | Must | Um leiloeiro com acesso público e URL válida é carregado; uma URL sem TLS é rejeitada citando o leiloeiro | 🟡 |
| RF-03 | O sistema deve obter o conteúdo da URL cadastrada por requisição HTTP direta, com timeout de 30 segundos e cabeçalho de navegador comum | Must | A requisição retorna conteúdo não vazio, e o registro da execução marca o nível `script` | 🟢 |
| RF-04 | O sistema deve repetir requisição falha até 3 tentativas com espera crescente, e classificar resposta 403 ou 429 como bloqueio, distinta de falha de rede | Must | Uma resposta 429 produz veredito de bloqueio; um timeout produz veredito de falha de rede | 🟡 |
| RF-05 | O sistema deve converter o conteúdo em lotes normalizados com número do lote, marca, modelo, ano de fabricação, ano de modelo, lance inicial, lance corrente, link absoluto, descrição e tipo de leilão | Must | De uma página com N lotes visíveis no navegador, o parser devolve N lotes com os campos preenchidos ou explicitamente nulos | 🟡 |
| RF-06 | O sistema deve atribuir a cada lote um identificador canônico estável entre execuções | Must | O mesmo lote extraído em duas execuções recebe o mesmo identificador | 🟡 |
| RF-07 | O sistema deve sinalizar quebra de parser quando o conteúdo for não vazio e nenhum lote for extraído, ou quando mais de 30% dos lotes vierem sem campo obrigatório | Must | Uma página válida processada por parser desatualizado produz sinal de quebra, e não lista vazia silenciosa | 🟡 |
| RF-08 | O sistema deve declarar candidatos os lotes que satisfizerem RN-01 contra o veículo-alvo configurado | Must | Um lote `2017/2018` com lance corrente de R$ 41.900 casa com alvo de faixa 2018 a 2021 e teto R$ 45.000; um lote com lance corrente de R$ 52.000 não casa | 🟢 |
| RF-09 | O sistema deve consultar o SQLite e descartar candidatos já notificados, gravando os novos somente após a confirmação de envio | Must | Duas execuções seguidas sem lote novo no site produzem digest na primeira e nenhuma mensagem na segunda | 🟢 |
| RF-10 | O sistema deve enviar um único digest por execução com marca, modelo, ano, preço, leiloeiro e link clicável de cada lote novo, e nenhuma mensagem quando não houver lote novo | Must | O digest chega ao Telegram e cada link abre a página do lote em um toque | 🟢 |
| RF-11 | O sistema deve enviar alerta operacional, em mensagem separada do digest, ao receber sinal de quebra de parser | Must | Um sinal de quebra produz alerta identificando o leiloeiro, inclusive em execução sem lotes novos | 🟡 |
| RF-12 | O sistema deve registrar cada execução no SQLite com início, fim, duração, veredito e as contagens de lotes vistos, candidatos, novos e já conhecidos, inclusive quando falhar | Must | Após execução interrompida por ausência de rede, o histórico contém o registro com veredito de falha | 🟡 |
| RF-13 | O sistema deve registrar os candidatos da primeira execução como conhecidos, sem notificar | Must | A primeira execução de uma busca nova não envia digest, e a base fica populada | 🟡 |
| RF-14 | O sistema deve oferecer um comando de execução manual que dispare a varredura completa | Must | Executar o comando roda a cadeia inteira e encerra com o resumo em log | 🟡 |
| RF-15 | O sistema deve impedir execuções concorrentes por trava exclusiva | Should | Disparar uma segunda execução com outra em andamento resulta em recusa registrada | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Execução completa em menos de 10 minutos para 1 leiloeiro e 1 busca | `_reversa_sdd/sdd/agendador-observabilidade.md#7`, ajustado ao tamanho desta fatia | 🟡 |
| Desempenho | Consulta de deduplicação em menos de 1 segundo | `_reversa_sdd/sdd/motor-filtros.md#7`; exige índice sobre o identificador canônico | 🟡 |
| Segurança | Token do bot e credenciais em `.env`, fora do versionamento, nunca impressos em log nem em rastreamento de exceção | RN-08 | 🟢 |
| Segurança | Arquivo do banco SQLite fora do versionamento, por conter o histórico de interesse de compra | `_reversa_sdd/sdd/motor-filtros.md#12` | 🟡 |
| Custo | Zero gasto com plataforma paga nesta feature: apenas o nível `script` é exercitado | `_reversa_sdd/ideation.md#estrategia-de-escalonamento-progressivo` | 🟢 |
| Conduta de coleta | Intervalo mínimo de 5 segundos entre requisições ao mesmo host | `_reversa_sdd/sdd/coletor-lotes.md#7` | 🟢 |
| Observabilidade | Toda execução iniciada tem registro de encerramento, inclusive em falha | `_reversa_sdd/sdd/agendador-observabilidade.md#7`; sem isso a métrica de 95% fica otimista | 🟡 |
| Manutenibilidade | Parser do leiloeiro em arquivo próprio, registrado por identificador, sem acoplamento aos demais | `_reversa_sdd/sdd/parser-lotes.md#7` | 🟡 |
| Portabilidade | Execução em notebook Windows, com caminho previsto para servidor caseiro ou VPS depois | `_reversa_sdd/ideation.md#infraestrutura-progressiva` | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Primeira execução popula a base sem notificar
  Dado um veículo-alvo ativo e um leiloeiro público com uma busca cadastrada
  E o banco de deduplicação vazio
  Quando a varredura é executada pela primeira vez
  Então os lotes que casarem são gravados como conhecidos
  E nenhuma mensagem é enviada ao Telegram
  E a execução é registrada no histórico com as contagens preenchidas

Cenário: Lote novo gera digest no Telegram
  Dado uma base já semeada e um lote novo publicado no leiloeiro
  E o lote é um Nissan Versa 2017/2018 com lance corrente de R$ 41.900
  E o veículo-alvo é Versa, faixa 2018 a 2021, teto R$ 45.000
  Quando a varredura é executada
  Então o Rafael recebe um digest contendo esse lote
  E o digest exibe marca, modelo, ano, preço, leiloeiro e link
  E o lote é gravado como notificado somente após a confirmação de envio

Cenário: Lote acima do teto não é notificado
  Dado um lote que abriu em R$ 30.000 e está com lance corrente de R$ 52.000
  E o veículo-alvo tem teto de R$ 45.000
  Quando a varredura é executada
  Então o lote não é declarado candidato
  E nenhuma mensagem sobre ele é enviada

Cenário: Execução repetida não renotifica
  Dado um lote já notificado na execução anterior
  Quando a varredura é executada de novo sem lote novo no site
  Então nenhuma mensagem é enviada ao Telegram
  E o histórico registra lotes novos igual a zero

Cenário: Parser quebrado avisa em vez de silenciar
  Dado que o leiloeiro mudou o layout da página
  Quando a varredura recebe conteúdo não vazio e nenhum lote é extraído
  Então um alerta operacional é enviado identificando o leiloeiro
  E o alerta é enviado mesmo não havendo lotes novos
  E a execução é registrada com o sinal de quebra

Cenário: Falha no envio preserva os lotes para a próxima execução
  Dado lotes novos prontos para notificação
  Quando o envio ao Telegram falha nas 3 tentativas
  Então nenhum lote é gravado como notificado
  E os mesmos lotes voltam a ser candidatos na execução seguinte

Cenário: Configuração inválida aborta antes de tocar a rede
  Dado um arquivo de veículos-alvo com ano mínimo maior que o ano máximo
  Quando a varredura é disparada
  Então a execução aborta citando o alvo e o campo
  E nenhuma requisição HTTP é realizada

Cenário: Bloqueio do site é distinguido de falha de rede
  Dado que o leiloeiro responde com HTTP 429
  Quando a varredura esgota as 3 tentativas
  Então o veredito registrado é bloqueio
  E o registro fica disponível para sustentar a proposta de escalar o nível de coleta

Cenário: Cadastro de leiloeiro inválido é rejeitado
  Dado um leiloeiro cadastrado com URL de busca sem TLS
  Quando a varredura é disparada
  Então a execução aborta citando o nome do leiloeiro e a URL recebida
  E nenhuma requisição HTTP é realizada

Cenário: Execução que falha por completo fica registrada
  Dado que a máquina está sem conexão de rede
  Quando a varredura é executada
  Então todas as buscas terminam com veredito de falha de rede
  E a execução é registrada no histórico com veredito de falha
  E o registro tem instante de encerramento preenchido

Cenário: Segunda execução simultânea é recusada
  Dado uma varredura em andamento que já adquiriu a trava
  Quando uma segunda varredura é disparada
  Então a segunda é recusada sem processar nada
  E a recusa é registrada em log
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02 | Must | Sem configuração carregada e validada não há o que buscar nem onde |
| RF-03, RF-04 | Must | A coleta é o elo que prova a viabilidade técnica da fatia |
| RF-05, RF-06 | Must | Sem lote normalizado e com identificador estável não há filtro nem deduplicação |
| RF-07 | Must | Critério de aceite do `prd.md#9`: não falhar em silêncio |
| RF-08, RF-09 | Must | É o núcleo do valor: só o que interessa, e só uma vez |
| RF-10 | Must | É a única interface do sistema com o usuário |
| RF-11 | Must | Sem alerta, o silêncio vira ambíguo e o sistema perde confiabilidade percebida |
| RF-12 | Must | Sem histórico não há observabilidade nem série para a recomendação de frequência futura |
| RF-13 | Must | Sem semeadura, a estreia dispara um digest com todo o catálogo que casa |
| RF-14 | Must | Sem disparo manual não há como exercitar a fatia |
| RF-15 | Should | Relevante quando o agendamento automático entrar; com disparo manual o risco é baixo |
| RNF de desempenho | Should | A fatia tem volume pequeno; os limites importam de verdade com 5 leiloeiros |
| RNF de segurança | Must | Credencial vazada em repositório é dano que não se desfaz |
| RNF de custo | Must | O princípio do menor custo é decisão estruturante da ideação |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

## 10. Lacunas

- 🔴 [DÚVIDA] **Qual leiloeiro é o primeiro?** A fatia exige um leiloeiro público e de estrutura simples. Os cinco candidatos são Freitas, Vip Leilões, Claudio Kuss, Copart e Milan, e nenhum foi inspecionado. A escolha determina qual parser será escrito e qual URL filtrada precisa ser capturada. Categoria: escopo.
- 🔴 [DÚVIDA] **O leiloeiro escolhido exibe o lance corrente na página de listagem?** RN-03 fixa o lance corrente como valor de comparação. Se o site só revelar esse valor ao abrir o lote, o filtro de preço exigiria uma requisição por lote, o que contraria a estratégia de fetch de URL única registrada em `_reversa_sdd/ideation.md` e muda o desenho da coleta. Espelha `_reversa_sdd/sdd/parser-lotes.md#14`, OQ-04. Categoria: escopo e técnico.
- 🔴 [DÚVIDA] **Os termos de uso e o `robots.txt` do leiloeiro escolhido permitem acesso automatizado?** O `prd.md#6` assume o compromisso de respeitar os termos na medida do possível, e a verificação nunca foi feita site a site. A resposta pode vetar o leiloeiro escolhido ou impor restrição de caminho e de ritmo. Espelha `_reversa_sdd/sdd/onboarding-leiloeiro-assistido.md#14`, OQ-03, e `_reversa_sdd/sdd/coletor-lotes.md#14`, OQ-01. Categoria: segurança e conformidade.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-09-25 | Versão inicial gerada por `/reversa-requirements` | reversa |
