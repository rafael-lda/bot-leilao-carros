# Spec: Motor de Filtros e Deduplicação

> Selo 🟡 PLANEJADO em todos os itens. Nenhum fato aqui foi extraído de código existente.

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-09-21
**Reviewers:** Rafael

---

## 1. Resumo

🟡 Componente que **decide o que interessa**. Compara cada lote normalizado contra a lista de veículos-alvo, aplicando marca, modelo, faixa de ano, teto de preço e tipo de leilão. Dos lotes que casam, elimina os que já foram notificados em execuções anteriores, consultando um banco SQLite. O que sobra é o conjunto de lotes novos e relevantes que segue para o Telegram. Também produz a contagem de lotes vistos, novos e já conhecidos que alimenta a recomendação de frequência.

---

## 2. Contexto e Motivação

**Problema:**
🟡 Uma varredura em cinco leiloeiros traz centenas de lotes, dos quais talvez dois interessem. Pior: a varredura seguinte traz os mesmos lotes de novo, porque um leilão fica aberto por dias. Sem filtro, o Telegram vira ruído; sem deduplicação, o mesmo carro é anunciado a cada execução até o pregão encerrar, e o Rafael passa a ignorar as notificações.

**Evidências:**
🟡 O `prd.md` define como valor central "receber só os carros que interessam, filtrados e prontos para avaliar". O critério de aceite exige que os lotes que casarem com os filtros sejam notificados, o que pressupõe uma definição precisa de casamento. A escolha por digest por execução, feita em 2026-09-21, torna a deduplicação ainda mais crítica, já que um digest repetido é ainda mais ignorável que uma mensagem repetida.

**Por que agora:**
🟡 É o componente que converte volume em sinal. Todo o esforço de coleta e parsing só entrega valor se esta camada acertar, e um erro aqui tem duas formas caras: deixar passar o carro certo, ou repetir tanto que o Rafael desliga as notificações.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Entregar ao notificador apenas lotes que casam com ao menos um veículo-alvo ativo.
- [ ] 🟡 G-02: Garantir que um mesmo lote nunca seja notificado duas vezes.
- [ ] 🟡 G-03: Produzir, a cada execução, a contagem de lotes vistos, novos e já conhecidos, que serve de insumo para a recomendação de frequência de varredura.

**Métricas de sucesso:**

| Métrica | Baseline atual | Target | Prazo |
|---|---|---|---|
| 🟡 Lotes notificados em duplicidade | Não existe | 0 | MVP |
| 🟡 Precisão do casamento (lotes notificados que o Rafael considera pertinentes) | Não existe | ≥ 80% | 3 meses |
| 🟡 Tempo de filtragem e deduplicação | Não existe | < 3 segundos para 500 lotes contra 20 alvos | MVP |
| 🟡 Consultas de deduplicação por execução | Não existe | < 1 segundo para base de 50.000 lotes | 3 meses |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: **Avaliar se o preço é uma boa oportunidade.** O motor compara contra o teto declarado pelo Rafael. Julgar se o valor está abaixo do mercado exigiria tabela FIPE, registrada como evolução futura no `prd.md`.
- 🟡 NG-02: **Renotificar por queda de preço.** No MVP, um lote já notificado permanece notificado, qualquer que seja a variação de lance depois. O comportamento está em aberto em OQ-02.
- 🟡 NG-03: **Ordenar ou priorizar os lotes.** O motor entrega o conjunto que casou. A apresentação pertence ao `notificador-telegram`.
- 🟡 NG-04: **Dar lance ou interagir com o leilão.** Proibido de forma explícita pelo `prd.md`, seção de não-objetivos.
- 🟡 NG-05: **Limpar a base histórica de lotes.** A retenção é tratada em OQ-03 e fica fora do MVP.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 Nenhum humano interage com o componente durante a operação. O efeito do seu trabalho chega ao Rafael pelo Telegram.
**Usuário secundário:** 🟡 Agente de IA gestor, que lê as contagens de vistos, novos e já conhecidos para propor ajuste de frequência, e que investiga quando o Rafael reclama de lote perdido ou de notificação irrelevante.

**Jornada atual (sem a feature):**
1. 🟡 Rafael percorre listagens inteiras procurando visualmente os carros que se encaixam nos seus critérios.
2. 🟡 Reencontra, a cada visita, os mesmos lotes que já tinha descartado antes.
3. 🟡 Perde tempo reavaliando o que já avaliou e corre o risco de pular um lote novo no meio dos repetidos.

**Jornada futura (com a feature):**
1. 🟡 O motor compara os lotes coletados contra os alvos configurados.
2. 🟡 Descarta os que não casam e os que já foram notificados.
3. 🟡 Rafael recebe no Telegram apenas o que é novo e pertinente.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| 🟡 RF-01 | O sistema deve comparar cada lote recebido do `parser-lotes` contra cada veículo-alvo ativo. | Must | Com 100 lotes e 5 alvos ativos, o componente avalia as 500 combinações e registra o total avaliado. |
| 🟡 RF-02 | O sistema deve considerar marca e modelo casados quando o texto normalizado do lote contiver o texto normalizado do alvo, com comparação sem distinção de maiúsculas e sem acentuação. | Must | O lote `NISSAN VERSA 1.6 SV` casa com o alvo de marca `Nissan` e modelo `Versa`. |
| 🟡 RF-03 | O sistema deve considerar o ano casado quando o **ano de modelo** do lote estiver dentro da faixa declarada no alvo, incluídos os extremos. | Must | Um lote `2017/2018` casa com um alvo de faixa 2018 a 2021, pois seu ano de modelo é 2018; um lote `2016/2017` não casa. |
| 🟡 RF-04 | O sistema deve considerar o preço casado quando o **lance corrente** do lote for menor ou igual ao teto declarado naquele alvo, adotando o lance inicial como valor de comparação enquanto o lote não tiver recebido nenhum lance. | Must | Um lote com lance corrente de R$ 45.000 casa com um alvo de teto R$ 45.000; um lote que abriu em R$ 30.000 e está com lance corrente de R$ 52.000 não casa. |
| 🟡 RF-05 | O sistema deve considerar o tipo de leilão casado quando o tipo do lote constar da lista de tipos aceitos pelo alvo. | Must | Um lote de tipo `financiamento` casa com um alvo que aceita `financiamento` e `seguradora`. |
| 🟡 RF-06 | O sistema deve declarar um lote candidato somente quando todos os critérios de RF-02 a RF-05 forem satisfeitos para um mesmo alvo. | Must | Um lote que casa marca, modelo e ano, com preço acima do teto, não é declarado candidato. |
| 🟡 RF-07 | O sistema deve tratar a ausência de lance inicial e de lance corrente como critério não eliminatório, marcando o lote como preço a confirmar e permitindo que ele siga como candidato se os demais critérios casarem. | Must | Um lote sem nenhum valor monetário, casando marca, modelo, ano e tipo, é declarado candidato com a marcação de preço a confirmar. |
| 🟡 RF-08 | O sistema deve tratar ano de modelo ausente como critério eliminatório, descartando o lote e registrando o descarte por dado insuficiente. | Must | Um lote sem ano de modelo não é declarado candidato, e o contador de descartes por dado ausente é incrementado. |
| 🟡 RF-09 | O sistema deve consultar o banco SQLite e descartar todo lote candidato cujo identificador canônico já conste como notificado. | Must | Um lote notificado na execução anterior não é entregue ao notificador na execução seguinte. |
| 🟡 RF-10 | O sistema deve registrar no SQLite, após a notificação ser confirmada pelo `notificador-telegram`, o identificador canônico, o alvo que casou, o preço no momento e o instante da notificação. | Must | Consultando o banco após a execução, cada lote notificado tem exatamente um registro. |
| 🟡 RF-11 | O sistema deve notificar uma única vez o lote que casar com mais de um veículo-alvo, registrando o primeiro alvo que casou. | Must | Um lote que casa com dois alvos gera uma única entrada no digest e um único registro no banco. |
| 🟡 RF-12 | O sistema deve produzir, ao final de cada execução, as contagens de lotes vistos, lotes candidatos, lotes novos, lotes já conhecidos e lotes descartados por filtro. | Must | O `agendador-observabilidade` recebe as cinco contagens e as persiste no histórico de execuções. |
| 🟡 RF-13 | O sistema deve oferecer um modo de semeadura em que os lotes candidatos da primeira execução de uma busca são registrados como conhecidos sem gerar notificação. | Should | Na primeira execução de uma busca nova, com o modo ativo, nenhum digest é enviado e a base fica populada. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O motor recebe a lista de lotes normalizados do `parser-lotes` e a lista de alvos ativos.
2. 🟡 Para cada lote, o motor percorre os alvos aplicando os critérios de RF-02 a RF-05.
3. 🟡 O motor marca como candidatos os lotes que satisfizeram todos os critérios de ao menos um alvo.
4. 🟡 O motor consulta o SQLite com os identificadores canônicos dos candidatos.
5. 🟡 O motor separa os candidatos em novos e já conhecidos.
6. 🟡 O motor entrega os candidatos novos ao `notificador-telegram`.
7. 🟡 Confirmado o envio, o motor grava os lotes notificados no SQLite.
8. 🟡 O motor apura as contagens de RF-12 e as entrega ao `agendador-observabilidade`.
9. 🟡 Resultado: Rafael recebe um digest contendo apenas lotes novos e pertinentes.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Execução sem nenhum lote novo:**
1. 🟡 Todos os candidatos já constam como notificados no banco.
2. 🟡 O motor entrega conjunto vazio ao notificador, que não envia digest.
3. 🟡 A contagem de lotes novos igual a zero é registrada e passa a compor a série que sustenta a recomendação de espaçar a frequência.

**Fluxo Alternativo B — Alvo novo cadastrado:**
1. 🟡 Rafael adiciona um veículo-alvo ao YAML.
2. 🟡 Na execução seguinte, lotes já presentes nos sites passam a casar com o alvo novo.
3. 🟡 Esses lotes são notificados, ainda que sejam antigos nos sites, pois nunca haviam sido notificados antes.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|---|---|---|---|
| 🟡 RNF-01 | Consulta de deduplicação | < 1 segundo para base de 50.000 lotes | Exige índice sobre o identificador canônico. É a razão de o histórico viver em SQLite, e não em arquivo. |
| 🟡 RNF-02 | Atomicidade do registro | A gravação dos lotes notificados de uma execução ocorre em transação única | Evita estado parcial que renotificaria parte do digest em caso de interrupção. |
| 🟡 RNF-03 | Ordem de gravação | O registro só ocorre após a confirmação de envio pelo notificador | Registrar antes faria um lote sumir para sempre caso o envio falhasse. |
| 🟡 RNF-04 | Crescimento da base | Suportar 100.000 lotes registrados sem degradar RNF-01 | A política de retenção está em aberto em OQ-03. |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Consome `Lote` do `parser-lotes` e `VeiculoAlvo` do `configuracao-veiculos-alvo`. Produz a lista de lotes novos para o `notificador-telegram` e as contagens para o `agendador-observabilidade`. É o dono do banco SQLite de lotes notificados.

**Comportamento esperado:**
🟡 Componente sem interface visual. A saída em log tem a forma:

```
filtro | 312 lotes vistos
filtro | 9 candidatos (303 descartados: 261 sem casar, 38 ano ausente, 4 acima do teto)
filtro | 7 já notificados antes, 2 novos
filtro | novo: Nissan Versa 2019 | R$ 41.900 | Vip Leilões | alvo=nissan-versa-2018-2021
filtro | novo: Toyota Corolla 2018 | preço a confirmar | Copart | alvo=toyota-corolla-2017-2020
filtro | resumo: vistos=312 candidatos=9 novos=2 conhecidos=7
```

**Estados da UI (saída em log):**
- 🟡 Estado vazio: `Nenhum lote recebido do parser. Nada a filtrar.`
- 🟡 Estado de carregamento: `Avaliando 312 lotes contra 5 alvos ativos...`
- 🟡 Estado de erro: `Banco de deduplicação inacessível. Execução abortada sem notificar, para não arriscar notificação duplicada.`
- 🟡 Estado de sucesso: `2 lotes novos encaminhados ao notificador.`

---

## 9. Modelo de Dados

**Entidades novas ou modificadas:**

```
LoteNotificado {                 // tabela no SQLite, propriedade deste componente
  id_canonico: string PRIMARY KEY // vem do parser-lotes
  leiloeiro_id: string            // origem, para consultas por leiloeiro
  alvo_id: string                 // qual veículo-alvo casou primeiro
  preco_na_notificacao: decimal?  // lance corrente no instante do envio, nulo se a confirmar
  lance_inicial: decimal?         // valor de abertura, base do estudo de margem em OQ-01
  link: string                    // para reconstruir o histórico sem depender do site
  notificado_em: datetime INDEX   // permite responder "quantos na última semana"
}

ResultadoFiltragem {             // objeto transiente, entregue ao agendador
  lotes_vistos: int
  lotes_candidatos: int
  lotes_novos: int
  lotes_ja_conhecidos: int
  descartados_sem_casar: int
  descartados_dado_ausente: int
  novos: Lote[]                   // o que segue para o notificador
}
```

**Migrações necessárias:** 🟡 Sim. Criação da tabela `LoteNotificado` com chave primária sobre o identificador canônico e índice sobre a data de notificação. A criação é idempotente e ocorre na primeira execução, sem passo manual.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|---|---|---|
| 🟡 Banco SQLite local | Obrigatória | Sem deduplicação confiável a execução aborta sem notificar, evitando enxurrada de repetidos (EC-01). |
| 🟡 `parser-lotes` | Obrigatória | Fornece os lotes normalizados; sem ele não há o que filtrar. |
| 🟡 `configuracao-veiculos-alvo` | Obrigatória | Fornece os critérios; sem alvos ativos a execução encerra sem notificar. |
| 🟡 `notificador-telegram` | Obrigatória | A confirmação de envio dele é o gatilho da gravação (RNF-03); falha no envio mantém os lotes como não notificados. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---|---|---|
| 🟡 EC-01: Banco SQLite inacessível ou corrompido | Arquivo apagado, disco cheio, corrupção | A execução aborta sem notificar. Notificar sem poder deduplicar geraria repetição em massa, falha mais cara que a ausência de uma execução. |
| 🟡 EC-02: Banco em lock por outro processo | Duas execuções sobrepostas | Aguarda com timeout de 10 segundos e uma tentativa de retry. Persistindo o lock, aborta registrando o conflito de concorrência. |
| 🟡 EC-03: Falha no envio do digest | Telegram indisponível | Nenhum lote é gravado como notificado, e os mesmos lotes serão candidatos na execução seguinte (RNF-03). |
| 🟡 EC-04: Falha entre o envio e a gravação | Processo interrompido no intervalo | Os lotes são renotificados na execução seguinte. A duplicação eventual é preferível à perda definitiva de um lote. |
| 🟡 EC-05: Primeira execução com base vazia | Sistema recém-instalado | Sem o modo de semeadura, todos os candidatos são novos e um digest extenso é enviado. Com o modo ativo (RF-13), a base é populada sem notificar. |
| 🟡 EC-06: Lote com preço ausente | Preço sob consulta na origem | Segue como candidato, marcado como preço a confirmar (RF-07), e o teto do alvo não é aplicado. |
| 🟡 EC-07: Lote sem ano | Parser não encontrou o campo | Descartado por dado insuficiente, com contador próprio, distinto do descarte por não casar (RF-08). |
| 🟡 EC-08: Alvo desativado após um lote já ter sido notificado por ele | Rafael desliga um alvo | O registro histórico permanece íntegro. A desativação afeta execuções futuras, sem reescrever o passado. |
| 🟡 EC-09: Dois lotes distintos com o mesmo identificador canônico | Colisão de derivação no parser | O segundo é tratado como já conhecido e não notificado. A ocorrência é registrada para que o critério de identificador do leiloeiro seja revisto. |
| 🟡 EC-10: Nenhum alvo ativo configurado | Rafael desativou tudo | O motor encerra sem avaliar nada, registrando zero lotes vistos, sem tratar a situação como falha. |

---

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 Nenhuma. Componente local, sem superfície de rede.
- **Autorização:** 🟡 Nenhuma. Ferramenta pessoal de usuário único.
- **Dados sensíveis:** 🟡 O banco guarda o histórico de interesse de compra do Rafael: quais carros ele monitora, a que preço e quando foi avisado. É informação pessoal de valor comercial. O arquivo do banco deve ficar listado no `.gitignore` e não é versionado.
- **Auditoria:** 🟡 A tabela de lotes notificados é o registro de auditoria natural do sistema: permite reconstruir o que foi enviado, quando e por qual critério, inclusive depois de o lote sumir do site de origem.

---

## 13. Plano de Rollout

- **Estratégia:** 🟡 Big bang, acompanhando o primeiro leiloeiro. O modo de semeadura de RF-13 é ativado na estreia de cada busca nova, evitando que a entrada de um leiloeiro no sistema produza um digest com dezenas de lotes preexistentes.
- **Como reverter (rollback):** 🟡 O banco é um arquivo único. Fazer cópia antes de uma mudança de esquema permite restaurar por substituição de arquivo. Apagar o banco é operação destrutiva: zera o histórico e faz todo lote voltar a ser considerado novo, provocando renotificação em massa. Essa operação exige decisão explícita do Rafael.
- **Monitoramento pós-deploy:** 🟡 Nas primeiras 2 semanas, acompanhar a razão entre lotes vistos e candidatos. Candidatos próximos de zero indicam critérios restritivos demais ou parser incompleto; candidatos muito próximos do total de vistos indicam critérios frouxos.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---|---|---|---|
| 🟡 OQ-01 | O teto deve ganhar uma margem de segurança sensível ao estágio do pregão? Um lote cujo lance corrente já está encostado no teto ainda no início do leilão tende a ultrapassá-lo antes do encerramento, e notificar nesse caso cria expectativa que o próprio pregão vai desfazer. Definir a margem exige saber quanto os lances costumam subir do início ao fim, dado que só o histórico de execuções vai revelar. | Alto | Rafael | Após as primeiras semanas de uso |
| 🟡 OQ-02 | Um lote já notificado deve voltar a ser notificado se o preço cair de forma relevante, ou se a data do pregão se aproximar? O MVP diz que não (NG-02). | Médio | Rafael | Após 1 mês de operação |
| 🟡 OQ-03 | Qual a política de retenção do histórico de lotes notificados? Guardar para sempre sustenta a auditoria e faz a base crescer sem limite. | Médio | Rafael | Quando a base passar de 50.000 registros |
| 🟡 OQ-04 | A comparação de modelo por conteúdo de texto vai gerar falso positivo entre modelos de nome parecido, como Versa e Versa Sedan? Pode ser necessário um campo de exclusão por palavra. | Alto | Rafael | Após as primeiras notificações reais |
| 🟡 OQ-05 | Existe leiloeiro que não publica o lance corrente na listagem? Onde só houver lance inicial, o filtro de preço daquele site opera sobre um valor desatualizado. Questão espelhada em OQ-04 do `parser-lotes`. | Alto | Rafael | Ao escrever o primeiro parser |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---|---|---|
| 🟡 SQLite como base de deduplicação | Arquivo JSON com os identificadores já vistos; conjunto em memória | Escolhido em 2026-09-21. A deduplicação exige busca indexada sobre uma base que cresce a cada execução: em JSON, a consulta degrada conforme o histórico aumenta. SQLite é arquivo único, sem servidor, nativo do Python, e é o que permite responder "quantos lotes novos na última semana", consulta que alimenta a recomendação de frequência. |
| 🟡 Gravar como notificado somente após confirmação de envio | Gravar ao declarar candidato | Gravar antes faria um lote desaparecer para sempre caso o Telegram falhasse, pois ele passaria a constar como já avisado sem nunca ter chegado ao Rafael. A ordem escolhida troca o risco de perda pelo risco de duplicação eventual, que é o erro menos caro. |
| 🟡 Preço ausente não elimina, ano ausente elimina | Eliminar ambos; preservar ambos | Preço sob consulta é comum em leilão e costuma esconder oportunidade, então eliminar por isso perderia exatamente o que se busca. Ano é o que define qual carro é: sem ele, o casamento seria um palpite, e notificar palpite corrói a confiança no digest. |
| 🟡 Lote que casa com vários alvos gera uma única notificação | Uma notificação por alvo casado | O Rafael quer saber do carro, e não de quantas regras suas ele satisfaz. Uma entrada por alvo produziria repetição dentro do mesmo digest. |
| 🟡 Abortar sem notificar quando o banco estiver inacessível | Notificar assumindo que nada foi visto antes | Sem deduplicação, uma execução enviaria de volta todo o histórico acumulado. Uma execução perdida é recuperada na seguinte; a confiança perdida em uma enxurrada de repetidos, não. |
| 🟡 Modo de semeadura na estreia de uma busca | Notificar tudo na primeira execução | Cadastrar um leiloeiro novo dispararia um digest com todos os lotes preexistentes que casam, o que parece falha mesmo estando correto. A semeadura alinha o sistema ao presente antes de começar a avisar. |
| 🟡 Ano de modelo como o ano comparado contra a faixa do alvo | Ano de fabricação; casar quando qualquer um dos dois entrar na faixa | Escolhido pelo Rafael em 2026-09-22. A tabela FIPE e o mercado de usados indexam por ano de modelo, então comparar por ele mantém a faixa de ano e o teto de preço na mesma referência mental. O parser preserva os dois anos, o que permite rever o critério sem reescrever parser algum. |
| 🟡 Lance corrente como valor comparado contra o teto, recorrendo ao lance inicial enquanto não houver lance | Sempre o lance inicial; filtrar pelo inicial e exibir o corrente | Escolhido pelo Rafael em 2026-09-22. O lance corrente é o valor que ele precisaria superar de fato, então filtrar pelo inicial notificaria lotes já fora do alcance, que é justamente a notificação inútil que o sistema existe para evitar. O próprio Rafael levantou o limite desta decisão, registrado em OQ-01: um lote encostado no teto no início do pregão quase certamente vai ultrapassá-lo. |

---

## Apêndice

### Referências
- `_reversa_sdd/prd.md` — seção 4, escopo "Notificação via Telegram"; seção 5, não-objetivo de lances automáticos; seção 9, critérios de aceite
- `_reversa_sdd/ideation.md` — seção "Filtros configuráveis"
- `_reversa_sdd/sdd/parser-lotes.md` — origem dos lotes normalizados e do identificador canônico
- `_reversa_sdd/sdd/configuracao-veiculos-alvo.md` — origem dos critérios

### Histórico de Revisões
| Versão | Data | Autor | Mudanças |
|---|---|---|---|
| 1.0 | 2026-09-21 | reversa-spec-sdd | Criação inicial a partir do PRD |
