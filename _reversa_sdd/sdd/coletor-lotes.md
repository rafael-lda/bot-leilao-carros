# Spec: Coletor de Lotes

> Selo 🟡 PLANEJADO em todos os itens. Nenhum fato aqui foi extraído de código existente.

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-09-21
**Reviewers:** Rafael

---

## 1. Resumo

🟡 Componente que **busca** o conteúdo. Para cada busca cadastrada, faz a requisição à URL do leiloeiro usando o nível de ferramenta declarado para aquele site — requisição direta, Apify com IP comum ou Apify com IP residencial — abre sessão autenticada quando exigido, e entrega o conteúdo bruto ao `parser-lotes` sem interpretá-lo. A falha de uma busca nunca derruba as demais.

---

## 2. Contexto e Motivação

**Problema:**
🟡 Os cinco leiloeiros-alvo não respondem da mesma forma. Um site simples entrega HTML a uma requisição direta e gratuita; outro barra requisição automatizada e exige infraestrutura de scraping paga; um terceiro só mostra os dados relevantes para quem está logado. Tratar todos igual significa ou pagar Apify para todos sem necessidade, ou falhar nos sites difíceis.

**Evidências:**
🟡 O `ideation.md` define a estratégia de escalonamento progressivo em três níveis, com a regra "custo só quando justificado" e o princípio "ferramenta certa no lugar certo". O `prd.md` lista bloqueio anti-bot como risco de impacto alto e probabilidade média.

**Por que agora:**
🟡 É o componente onde o custo do projeto se materializa e onde o risco de bloqueio se concretiza. A meta de ≥ 95% de execuções sem falha depende quase inteiramente do comportamento deste componente diante de sites instáveis.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Obter o conteúdo de toda busca ativa usando o nível de ferramenta mais barato que funcione para aquele leiloeiro.
- [ ] 🟡 G-02: Isolar falhas por busca, de modo que um leiloeiro fora do ar não impeça a varredura dos demais.
- [ ] 🟡 G-03: Distinguir bloqueio anti-bot de falha genérica, para que o agente de IA gestor saiba quando recomendar escalar de nível.

**Métricas de sucesso:**

| Métrica | Baseline atual | Target | Prazo |
|---|---|---|---|
| 🟡 Buscas coletadas com sucesso por execução | Não existe | ≥ 95% | 3 meses |
| 🟡 Execuções interrompidas por falha de um único leiloeiro | Não existe | 0 | MVP |
| 🟡 Buscas rodando no nível `script` (gratuito) | Não existe | ≥ 60% do total | 3 meses |
| 🟡 Duração total da fase de coleta | Não existe | < 5 minutos para 10 buscas | MVP |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: **Interpretar o conteúdo recebido.** O coletor entrega bytes e metadados. Identificar o que é um lote e extrair modelo, ano e preço pertence ao `parser-lotes`.
- 🟡 NG-02: **Decidir sozinho escalar de nível.** Ao detectar bloqueio, o coletor registra o fato. A alteração de `nivel_coleta` é proposta pelo agente gestor e aprovada pelo Rafael, conforme o Fluxo Alternativo A do `cadastro-leiloeiros`.
- 🟡 NG-03: **Resolver CAPTCHA.** Um desafio anti-bot é registrado como bloqueio e encerra aquela busca.
- 🟡 NG-04: **Navegar por cliques ou paginação profunda.** A coleta é um fetch da URL já filtrada. Percorrer o site foi descartado na ideação por fragilidade.
- 🟡 NG-05: **Guardar histórico de conteúdo bruto.** O conteúdo é transiente, entregue ao parser e descartado. O que persiste é o lote normalizado e o registro de execução.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 Nenhum humano interage com este componente durante a operação normal. Ele roda sem supervisão, disparado pelo agendador.
**Usuário secundário:** 🟡 Agente de IA gestor, que lê os registros de coleta para identificar quais leiloeiros vêm falhando e propor mudança de nível.

**Jornada atual (sem a feature):**
1. 🟡 Rafael abre cada URL manualmente no navegador.
2. 🟡 Um site lento ou fora do ar interrompe a sessão de busca dele inteira.
3. 🟡 Não fica registro de qual site falhou nem com que frequência.

**Jornada futura (com a feature):**
1. 🟡 O agendador dispara a varredura.
2. 🟡 O coletor busca todas as URLs ativas, cada uma no seu nível de ferramenta.
3. 🟡 Falhas individuais são registradas e a varredura segue com as buscas restantes.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| 🟡 RF-01 | O sistema deve executar uma requisição para cada busca ativa recebida do `cadastro-leiloeiros`, usando o `nivel_coleta` declarado no leiloeiro dono daquela busca. | Must | Com 7 buscas ativas, o componente produz 7 objetos `RespostaBruta`, cada um registrando o nível efetivamente usado. |
| 🟡 RF-02 | O sistema deve, no nível `script`, executar requisição HTTP direta com timeout de 30 segundos e cabeçalho de navegador comum. | Must | Uma busca no nível `script` contra um site que responde em 2 segundos retorna conteúdo com `nivel_usado: script`. |
| 🟡 RF-03 | O sistema deve, nos níveis `apify` e `apify_residencial`, delegar a requisição à plataforma Apify, usando IP comum ou residencial conforme o nível. | Must | Uma busca no nível `apify` retorna conteúdo com `nivel_usado: apify`, e a requisição não parte do IP local. |
| 🟡 RF-04 | O sistema deve abrir sessão autenticada antes da requisição quando o leiloeiro declarar `estrategia_acesso: logado`, usando a credencial da variável de ambiente indicada. | Must | Uma busca em leiloeiro logado retorna conteúdo que inclui campos restritos, e o log registra a autenticação sem imprimir a credencial. |
| 🟡 RF-05 | O sistema deve isolar a falha de cada busca, prosseguindo com as demais mesmo que uma lance erro. | Must | Com 5 buscas, uma apontando para host inexistente, as outras 4 são coletadas com sucesso e a execução não aborta. |
| 🟡 RF-06 | O sistema deve repetir uma requisição falha até 3 tentativas, com espera crescente entre elas, antes de marcar a busca como falha definitiva. | Must | Um site que falha duas vezes e responde na terceira produz coleta bem-sucedida, com o número de tentativas registrado. |
| 🟡 RF-07 | O sistema deve respeitar um intervalo mínimo de 5 segundos entre requisições dirigidas ao mesmo leiloeiro. | Must | Um leiloeiro com 3 buscas tem suas requisições espaçadas em pelo menos 5 segundos, verificável pelos instantes registrados. |
| 🟡 RF-08 | O sistema deve classificar a resposta como bloqueio quando receber código HTTP 403 ou 429, ou quando o conteúdo apresentar desafio anti-bot. | Must | Uma resposta 429 produz `RespostaBruta` com `bloqueado: true`, distinta de uma falha de rede comum. |
| 🟡 RF-09 | O sistema deve detectar redirecionamento para tela de login em busca autenticada e tratar como sessão expirada, tentando reautenticar uma vez. | Must | Com sessão expirada, o componente reautentica e repete a requisição; persistindo o redirecionamento, marca a busca como falha de autenticação. |
| 🟡 RF-10 | O sistema deve registrar, para cada busca, o instante de início, a duração, o código de resposta, o nível usado, o número de tentativas e o veredito final. | Must | Após a execução, o `agendador-observabilidade` consegue montar o relatório de saúde por leiloeiro a partir desses registros. |
| 🟡 RF-11 | O sistema deve entregar ao `parser-lotes` o conteúdo bruto acompanhado do identificador da busca de origem. | Must | O parser recebe, junto do conteúdo, o identificador que permite escolher o parser correto. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O coletor recebe a lista de buscas ativas do `cadastro-leiloeiros`.
2. 🟡 O coletor agrupa as buscas por leiloeiro, para aplicar o espaçamento de RF-07.
3. 🟡 Para um leiloeiro com acesso logado, o coletor abre a sessão autenticada.
4. 🟡 O coletor executa a requisição da primeira busca no nível declarado.
5. 🟡 O site responde com código 200 e conteúdo não vazio.
6. 🟡 O coletor registra duração, código e nível usado.
7. 🟡 O coletor aguarda o intervalo mínimo e segue para a busca seguinte do mesmo leiloeiro.
8. 🟡 Resultado: uma coleção de objetos `RespostaBruta` é entregue ao `parser-lotes`.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Bloqueio detectado no nível gratuito:**
1. 🟡 Uma busca no nível `script` recebe resposta 429.
2. 🟡 O coletor esgota as 3 tentativas de RF-06 e marca a busca com `bloqueado: true`.
3. 🟡 O registro alimenta o relatório de saúde, e o agente gestor passa a ter evidência para propor ao Rafael a migração daquele leiloeiro para `apify`.

**Fluxo Alternativo B — Leiloeiro fora do ar:**
1. 🟡 Todas as buscas de um leiloeiro falham por timeout.
2. 🟡 O coletor registra as falhas e prossegue com os demais leiloeiros (RF-05).
3. 🟡 A execução termina com sucesso parcial, e o relatório aponta qual leiloeiro ficou sem cobertura.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|---|---|---|---|
| 🟡 RNF-01 | Timeout por requisição | 30 segundos | Acima disso o site é tratado como indisponível. |
| 🟡 RNF-02 | Intervalo entre requisições ao mesmo host | ≥ 5 segundos | Coleta discreta reduz o risco de o site classificar o acesso como abusivo. |
| 🟡 RNF-03 | Tentativas por busca | Máximo de 3, com espera crescente | Contém o custo de um site instável sem insistir a ponto de virar abuso. |
| 🟡 RNF-04 | Custo | Nenhuma requisição paga em leiloeiro cujo nível declarado seja `script` | Garante que a regra de custo da ideação seja cumprida por construção. |
| 🟡 RNF-05 | Segurança | Credenciais jamais impressas em log ou mensagem de erro | O log registra o nome da variável de ambiente usada, sem o valor. |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Consome `cadastro-leiloeiros` (lista de buscas e estratégia de acesso) e o `.env` (credenciais). Produz entrada para `parser-lotes` e registros para `agendador-observabilidade`. Integra com a plataforma Apify nos níveis pagos.

**Comportamento esperado:**
🟡 Componente sem interface visual. A observabilidade se dá pelo log de execução:

```
coleta | Vip Leilões | busca=vip-versa-financiamento | nivel=script | 200 | 1.8s | tentativa 1/3 | ok
coleta | Vip Leilões | aguardando 5s antes da próxima busca do mesmo leiloeiro
coleta | Copart      | autenticando com COPART_LOGIN
coleta | Copart      | busca=copart-sedan-seguradora | nivel=apify | 200 | 6.1s | tentativa 1/3 | ok
coleta | Freitas     | busca=freitas-corolla | nivel=script | 429 | 0.4s | tentativa 3/3 | BLOQUEADO
coleta | resumo: 6 buscas, 5 ok, 1 bloqueada, 0 falhas de rede
```

**Estados da UI (saída em log):**
- 🟡 Estado vazio: `Nenhuma busca ativa recebida. Fase de coleta encerrada sem trabalho.`
- 🟡 Estado de carregamento: `Coletando busca 3 de 7...`
- 🟡 Estado de erro: `Freitas / freitas-corolla: bloqueado após 3 tentativas (HTTP 429). Sugestão: avaliar nivel_coleta = apify.`
- 🟡 Estado de sucesso: `Coleta concluída: 6 de 7 buscas com conteúdo obtido.`

---

## 9. Modelo de Dados

**Entidades novas ou modificadas:**

```
RespostaBruta {
  busca_id: string        // identificador da busca de origem, vindo do cadastro
  leiloeiro_id: string    // para agrupar o relatório de saúde por leiloeiro
  url: string             // URL efetivamente requisitada
  iniciado_em: datetime   // instante do primeiro disparo
  duracao_ms: int         // tempo total, somadas as tentativas
  status_http: int?       // nulo quando a falha foi de rede, sem resposta
  conteudo: bytes?        // transiente, entregue ao parser e descartado
  nivel_usado: enum       // script | apify | apify_residencial
  tentativas: int         // 1 a 3
  bloqueado: bool         // true para 403, 429 ou desafio anti-bot
  veredito: enum          // ok | bloqueado | falha_rede | falha_autenticacao
}
```

**Migrações necessárias:** 🟡 Sim, parcial. O campo `conteudo` é transiente e nunca persiste. Os demais campos são gravados na tabela de histórico de execuções do SQLite, cujo esquema pertence ao `agendador-observabilidade`.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|---|---|---|
| 🟡 Sites dos leiloeiros | Obrigatória | Sem resposta, a busca é marcada como falha e as demais prosseguem (RF-05). |
| 🟡 Plataforma Apify | Obrigatória para buscas nos níveis pagos | Indisponibilidade da Apify falha apenas as buscas daqueles níveis; buscas em `script` seguem normalmente. |
| 🟡 Variáveis de ambiente com credenciais | Obrigatória para leiloeiros logados | A ausência já foi validada pelo `cadastro-leiloeiros` antes do primeiro fetch, então não deveria ocorrer aqui. |
| 🟡 Conexão de rede da máquina | Obrigatória | Sem rede, todas as buscas falham por timeout e a execução termina com relatório de falha total. |
| 🟡 `cadastro-leiloeiros` | Obrigatória | Fornece a lista de buscas; sem ela o coletor não tem trabalho a fazer. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---|---|---|
| 🟡 EC-01: Timeout da requisição | Site lento ou indisponível | Após 30 segundos, a tentativa é abortada e conta para o limite de 3 de RF-06. Esgotadas, veredito `falha_rede`. |
| 🟡 EC-02: Resposta HTTP 429 | Limite de taxa atingido no leiloeiro | Espera crescente entre as tentativas; persistindo, veredito `bloqueado`, distinto de falha de rede (RF-08). |
| 🟡 EC-03: Resposta HTTP 403 | Bloqueio por IP ou por identificação do agente | Veredito `bloqueado`, sem retry adicional além do limite, e registro que alimenta a recomendação de escalar de nível. |
| 🟡 EC-04: Resposta HTTP 500 ou 502 | Falha interna do leiloeiro | Tratado como falha temporária; usa as 3 tentativas com espera crescente antes de desistir. |
| 🟡 EC-05: Redirecionamento para tela de login | Sessão expirada em leiloeiro logado | Reautentica uma vez e repete; persistindo, veredito `falha_autenticacao` (RF-09). |
| 🟡 EC-06: Resposta 200 com conteúdo vazio | Página carregada por JavaScript que o nível `script` não executa | Registra conteúdo vazio como falha de coleta, com nota sugerindo avaliar o nível `apify`, que renderiza a página. |
| 🟡 EC-07: Falha de resolução de DNS | URL cadastrada com domínio errado, ou DNS local indisponível | Veredito `falha_rede`, com a mensagem citando o host que não resolveu. As demais buscas prosseguem. |
| 🟡 EC-08: Cota da Apify esgotada | Volume acima do contratado | A busca falha com mensagem explícita sobre cota, e não como erro genérico, para que o Rafael saiba que o problema é de orçamento e não do site. |
| 🟡 EC-09: Resposta muito grande | Página com volume atípico de conteúdo | Limite de 20 MB por resposta. Acima disso, a coleta é abortada e registrada, evitando consumo de memória sem controle. |
| 🟡 EC-10: Credencial inválida ou conta bloqueada no leiloeiro | Senha alterada no site sem atualizar o `.env` | Veredito `falha_autenticacao`, sem retry em laço, e aviso explícito para o Rafael atualizar a credencial. |

---

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 O componente autentica nos leiloeiros que exigem login, usando credenciais lidas de variáveis de ambiente. Nenhuma credencial trafega por arquivo de configuração versionado.
- **Autorização:** 🟡 O coletor acessa apenas o que a conta do Rafael já acessaria manualmente. Não há escalonamento de privilégio.
- **Dados sensíveis:** 🟡 Credenciais são o ativo sensível. RNF-05 proíbe imprimi-las em log ou em mensagem de erro, inclusive em rastreamento de exceção. O conteúdo bruto coletado é transiente e descartado após o parsing (NG-05).
- **Auditoria:** 🟡 Cada requisição fica registrada com leiloeiro, busca, instante, nível usado e veredito, permitindo reconstruir depois o que foi acessado, quando e por qual caminho.

---

## 13. Plano de Rollout

- **Estratégia:** 🟡 Gradual por nível. Implementar primeiro o nível `script` e validar contra um leiloeiro público simples. Só então adicionar o caminho Apify, e por último a autenticação. Cada nível entra em operação depois que o anterior estiver estável.
- **Como reverter (rollback):** 🟡 Rebaixar o `nivel_coleta` de um leiloeiro no YAML reverte aquele site ao caminho anterior sem tocar em código. Para desligar um leiloeiro problemático por completo, `ativo: false`. Como o componente não persiste conteúdo bruto, não há dado a limpar em um rollback.
- **Monitoramento pós-deploy:** 🟡 Nas primeiras 2 semanas, acompanhar a proporção de vereditos `bloqueado` por leiloeiro. Um site que bloqueia de forma recorrente no nível `script` é candidato a escalar. Acompanhar também o custo acumulado na Apify contra o previsto.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---|---|---|---|
| 🟡 OQ-01 | O coletor deve respeitar o `robots.txt` de cada leiloeiro, ainda que se apresente com cabeçalho de navegador? São decisões independentes, e respeitar o arquivo é a convenção padrão da web. | Alto | Rafael | Antes da primeira coleta real |
| 🟡 OQ-02 | O intervalo de 5 segundos entre requisições ao mesmo leiloeiro é adequado, ou algum dos cinco sites exige espaçamento maior? | Médio | Rafael | Após as primeiras execuções |
| 🟡 OQ-03 | Qual o teto de gasto mensal aceitável na Apify antes de o sistema avisar? O PRD registra o princípio do menor custo sem fixar um valor. | Médio | Rafael | Antes de ativar o primeiro leiloeiro em Apify |
| 🟡 OQ-04 | Sites que renderizam a listagem por JavaScript devem ir direto para `apify`, ou vale um nível intermediário com renderização local? | Médio | Rafael | Quando o primeiro site com essa característica aparecer |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---|---|---|
| 🟡 Nível de ferramenta declarado por leiloeiro, e não escolhido em tempo de execução | Tentar `script` e cair para `apify` automaticamente ao falhar | O fallback automático gastaria dinheiro sem decisão humana, contrariando o princípio de custo da ideação. A escolha declarativa mantém o gasto previsível, e a evidência coletada alimenta a proposta de mudança. |
| 🟡 Isolamento de falha por busca | Abortar a execução inteira ao primeiro erro | Um leiloeiro fora do ar é evento comum e esperado. Abortar tudo transformaria uma indisponibilidade de terceiro em falha total do sistema, inviabilizando a meta de 95%. |
| 🟡 Bloqueio classificado à parte de falha de rede | Tratar todo erro como falha genérica | São problemas com respostas opostas: falha de rede pede nova tentativa depois; bloqueio pede mudança de estratégia. Sem essa distinção, o agente gestor não teria como saber quando recomendar escalar. |
| 🟡 Conteúdo bruto transiente, sem histórico | Guardar o HTML de cada coleta | Guardar tudo cresceria sem limite e traria pouco retorno: o que importa depois é o lote normalizado e o registro de saúde. Reprocessar um HTML antigo não é caso de uso previsto. |
| 🟡 Limite de 3 tentativas com espera crescente | Retry indefinido; tentativa única | Tentativa única desperdiçaria coletas em falhas passageiras. Retry indefinido transformaria instabilidade do site em varredura que nunca termina, e se aproximaria de abuso. |
| 🟡 Cabeçalho de navegador comum, sem autoidentificação como bot | Cabeçalho declarando o bot de forma explícita | Escolhido pelo Rafael em 2026-09-22. Não constitui quebra de proteção técnica, é prática padrão de bibliotecas de coleta, e reduz recusa automática por política. O contrapeso que sustenta a escolha continua valendo por construção: intervalo de 5 segundos entre requisições ao mesmo host (RNF-02), três varreduras por semana e conteúdo restrito a anúncio público. |
| 🟡 Escalada para Apify por dificuldade técnica, com os termos de uso como limite | Escalar sempre que houver bloqueio, sem distinção de causa | Um site que só renderiza a listagem por JavaScript é obstáculo técnico, e usar uma plataforma de coleta para isso é uso corrente dela. Situação distinta é a do site que bloqueia depois de o coletor já ter respeitado o ritmo dele: ali o bloqueio é uma recusa deliberada, e escalar para IP residencial para derrubá-la é onde os termos de uso pesam. Por isso a leitura dos termos dos cinco leiloeiros continua pendente em `onboarding-leiloeiro-assistido` OQ-03, e a resolução de CAPTCHA segue fora de escopo em NG-03. |

---

## Apêndice

### Referências
- `_reversa_sdd/prd.md` — seção 4, escopo "Scraping e parsing" e "Escalonamento progressivo de ferramentas"; seção 8, riscos de bloqueio
- `_reversa_sdd/ideation.md` — seção "Estratégia de escalonamento progressivo (custo)"
- `_reversa_sdd/sdd/cadastro-leiloeiros.md` — origem das buscas e da estratégia de acesso

### Histórico de Revisões
| Versão | Data | Autor | Mudanças |
|---|---|---|---|
| 1.0 | 2026-09-21 | reversa-spec-sdd | Criação inicial a partir do PRD |
