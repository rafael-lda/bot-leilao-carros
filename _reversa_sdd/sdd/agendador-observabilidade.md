# Spec: Agendador e Observabilidade

> Selo 🟡 PLANEJADO em todos os itens. Nenhum fato aqui foi extraído de código existente.

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-09-21
**Reviewers:** Rafael

---

## 1. Resumo

🟡 Componente que **roda e vigia** o sistema. Dispara a varredura na frequência declarada para cada leiloeiro, começando em três execuções por semana, e grava no SQLite o histórico de cada execução: o que foi coletado, quantos lotes foram vistos, quantos eram novos e quantos já eram conhecidos. Desse histórico saem duas coisas: os alertas de parser quebrado e de leiloeiro em falha, e uma recomendação de frequência que sugere espaçar ou adensar a varredura. A recomendação é sempre uma sugestão, e a mudança permanece decisão do Rafael.

---

## 2. Contexto e Motivação

**Problema:**
🟡 Uma automação que roda sem supervisão tem dois modos de falhar em silêncio: parar de rodar, e rodar sem encontrar nada porque quebrou. Nos dois casos o sintoma é idêntico ao de um período sem oportunidades, e o Rafael descobriria o problema apenas semanas depois, ao perceber que não recebe mensagens. Além disso, a frequência ideal de varredura é desconhecida: editais de leilão de veículos não saem todos os dias, e varrer de hora em hora gastaria recursos sem retorno, enquanto varrer uma vez por semana perderia janelas curtas.

**Evidências:**
🟡 O `prd.md` define como métricas a estabilidade de ≥ 95% de execuções sem falha e a autonomia de no máximo 1 intervenção manual por semana. Registra como pendência explícita a frequência de varredura. O `ideation.md` descreve o agente de IA gestor que "de tempos em tempos olha todo o sistema, vê onde rodou redondo e onde quebrou", e propõe mudanças após debate com o Rafael.

**Por que agora:**
🟡 É o componente que transforma o conjunto de peças em um sistema autônomo e observável. Sem ele existem scripts que alguém precisa lembrar de executar, e nenhuma base factual para decidir a frequência ou para saber se o sistema está saudável.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Executar a varredura de forma automática, na frequência declarada por leiloeiro, sem intervenção do Rafael.
- [ ] 🟡 G-02: Tornar visível toda falha do sistema, de modo que silêncio nunca seja ambíguo entre "sem oportunidades" e "quebrado".
- [ ] 🟡 G-03: Acumular a série histórica de lotes vistos, novos e já conhecidos, e dela derivar uma recomendação de frequência fundamentada em dados.

**Métricas de sucesso:**

| Métrica | Baseline atual | Target | Prazo |
|---|---|---|---|
| 🟡 Execuções concluídas sem falha | Não existe | ≥ 95% em janela de 30 dias | 3 meses |
| 🟡 Intervenções manuais por semana | Busca 100% manual | ≤ 1 | 3 meses |
| 🟡 Falhas do sistema que chegaram ao Rafael como alerta | Não existe | 100% | 3 meses |
| 🟡 Execuções com histórico gravado de forma completa | Não existe | 100% | MVP |
| 🟡 Execuções necessárias para emitir a primeira recomendação de frequência | Não existe | ≥ 10 por leiloeiro | 1 mês |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: **Alterar a frequência por conta própria.** O componente calcula e apresenta a recomendação. A edição do campo de frequência no YAML é ato do Rafael, conforme a decisão de manter mudanças sob debate registrada no `ideation.md`.
- 🟡 NG-02: **Consertar parser quebrado.** A detecção e o alerta são automáticos; a correção é trabalho do agente de IA gestor com aval do Rafael.
- 🟡 NG-03: **Escalar o nível de coleta automaticamente.** Vale a mesma regra: o componente fornece a evidência, e a mudança de `nivel_coleta` é aprovada pelo Rafael.
- 🟡 NG-04: **Painel web de métricas.** O `prd.md` declara dashboard web como não-objetivo. A observabilidade se dá por log, relatório em texto e alertas no Telegram.
- 🟡 NG-05: **Orquestrar execuções distribuídas.** Um único processo, em uma única máquina. A meta de infraestrutura é notebook e, depois, servidor caseiro ou VPS.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 Rafael — recebe os alertas, consulta o relatório de saúde quando quer entender o comportamento do sistema e decide sobre as recomendações de frequência.
**Usuário secundário:** 🟡 Agente de IA gestor, principal consumidor do histórico. É a partir dele que o agente identifica onde o sistema rodou bem e onde quebrou, e formula as propostas que levará ao Rafael.

**Jornada atual (sem a feature):**
1. 🟡 Rafael decide, por impulso, quando vai procurar carros.
2. 🟡 Não tem registro de quando procurou nem do que encontrou.
3. 🟡 Não tem como saber se a frequência com que procura é adequada ao ritmo dos editais.

**Jornada futura (com a feature):**
1. 🟡 O sistema executa a varredura três vezes por semana, sem que o Rafael precise agir.
2. 🟡 Quando algo quebra, ele recebe um alerta no Telegram identificando o leiloeiro afetado.
3. 🟡 Depois de dez execuções, o sistema sugere espaçar ou adensar a frequência de cada leiloeiro, com o número que sustenta a sugestão.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| 🟡 RF-01 | O sistema deve disparar a varredura de cada leiloeiro conforme a frequência declarada no `cadastro-leiloeiros`, adotando três execuções semanais em segunda, quarta e sexta pela manhã quando nada for declarado. | Must | Um leiloeiro sem frequência declarada é varrido nos três dias previstos, verificável no histórico de execuções. |
| 🟡 RF-02 | O sistema deve impedir que duas execuções ocorram ao mesmo tempo, usando trava exclusiva. | Must | Disparar uma segunda execução com outra em andamento resulta em recusa registrada, sem processamento concorrente. |
| 🟡 RF-03 | O sistema deve registrar no SQLite, para cada execução: instante de início e de fim, duração, leiloeiros processados, buscas bem-sucedidas, bloqueadas e falhas, lotes vistos, candidatos, novos e já conhecidos, e sinais de quebra recebidos. | Must | Após uma execução, uma consulta ao banco devolve o registro completo, com os onze grupos de informação preenchidos. |
| 🟡 RF-04 | O sistema deve prosseguir com os demais leiloeiros quando um deles falhar por completo, concluindo a execução com veredito de sucesso parcial. | Must | Com 5 leiloeiros, um fora do ar, a execução termina registrando 4 processados e 1 em falha, sem abortar. |
| 🟡 RF-05 | O sistema deve solicitar ao `notificador-telegram` o envio de alerta quando receber sinal de quebra de parser em qualquer busca. | Must | Um sinal de quebra produz alerta identificando o leiloeiro e a busca afetados. |
| 🟡 RF-06 | O sistema deve solicitar alerta quando a taxa de execuções bem-sucedidas de um leiloeiro ficar abaixo de 95% em janela de 30 dias, considerando apenas leiloeiros com ao menos 10 execuções na janela. | Must | Um leiloeiro com 3 falhas em 20 execuções gera alerta; um leiloeiro com 1 falha em 4 execuções não gera, por série insuficiente. |
| 🟡 RF-07 | O sistema deve recomendar espaçar a frequência de um leiloeiro quando as 6 execuções consecutivas mais recentes dele tiverem retornado zero lotes novos. | Must | Um leiloeiro com 6 execuções seguidas sem novidade recebe recomendação de espaçar, acompanhada da contagem que a sustenta. |
| 🟡 RF-08 | O sistema deve recomendar adensar a frequência de um leiloeiro quando a média de lotes novos por execução nas 10 execuções mais recentes dele for igual ou maior que 5. | Must | Um leiloeiro com média de 7 lotes novos por execução recebe recomendação de adensar, com a média declarada. |
| 🟡 RF-09 | O sistema deve apresentar as recomendações de frequência sem alterar nenhum arquivo de configuração. | Must | Após uma recomendação ser emitida, o campo de frequência no YAML permanece com o valor anterior. |
| 🟡 RF-10 | O sistema deve permitir que os limiares de 6 execuções sem novidade, média de 5 lotes novos e janela de 10 execuções sejam ajustados por configuração. | Should | Alterar o limiar de execuções sem novidade para 4 muda o momento em que a recomendação de espaçar passa a ser emitida. |
| 🟡 RF-11 | O sistema deve oferecer um comando que produza o relatório de saúde sob demanda, com a situação por leiloeiro e as recomendações vigentes. | Must | Executar o comando produz o relatório sem disparar uma varredura. |
| 🟡 RF-12 | O sistema deve registrar a execução no histórico mesmo quando ela terminar em falha total. | Must | Uma execução interrompida por ausência de rede aparece no histórico com veredito de falha, e não fica ausente. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O agendador desperta no horário previsto para um leiloeiro.
2. 🟡 O agendador adquire a trava exclusiva de execução.
3. 🟡 O agendador registra o início da execução no histórico.
4. 🟡 O agendador aciona a cadeia de componentes: configuração, coleta, parsing, filtragem e notificação.
5. 🟡 O agendador recebe as contagens de lotes vistos, candidatos, novos e já conhecidos do `motor-filtros`.
6. 🟡 O agendador recebe os sinais de quebra do `parser-lotes` e os vereditos de coleta do `coletor-lotes`.
7. 🟡 O agendador solicita alerta ao notificador para cada sinal de quebra recebido.
8. 🟡 O agendador grava o registro completo da execução e libera a trava.
9. 🟡 O agendador recalcula as recomendações de frequência com a série atualizada.
10. 🟡 Resultado: a execução fica documentada, os problemas foram avisados e as recomendações estão atualizadas.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Recomendação de espaçar a frequência:**
1. 🟡 A sexta execução consecutiva de um leiloeiro termina com zero lotes novos.
2. 🟡 O agendador calcula a recomendação de espaçar para aquele leiloeiro.
3. 🟡 A recomendação entra no relatório de saúde com a série que a sustenta.
4. 🟡 Rafael avalia e decide se altera a frequência no YAML, sem que nada mude sozinho.

**Fluxo Alternativo B — Máquina desligada no horário previsto:**
1. 🟡 O horário de uma execução passa com a máquina desligada.
2. 🟡 Ao ser ligada, o agendador identifica que a execução prevista não ocorreu.
3. 🟡 O agendador executa a varredura atrasada uma única vez, sem tentar recuperar todas as ocasiões perdidas.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|---|---|---|---|
| 🟡 RNF-01 | Duração total de uma execução | < 10 minutos para 5 leiloeiros e 10 buscas | Precisa terminar com folga antes da execução seguinte. |
| 🟡 RNF-02 | Consulta ao histórico para o relatório | < 2 segundos para 1.000 execuções registradas | Exige índice sobre o instante de início e sobre o identificador do leiloeiro. |
| 🟡 RNF-03 | Integridade do histórico | Toda execução iniciada tem registro de encerramento, inclusive em falha | Registro ausente tornaria a taxa de sucesso otimista e a métrica de 95% inútil. |
| 🟡 RNF-04 | Fuso horário | Horários interpretados no fuso local da máquina, com o instante gravado de forma não ambígua | Evita deslocamento de horário em mudança de horário de verão. |
| 🟡 RNF-05 | Autonomia | Nenhuma intervenção manual necessária para a execução ordinária | Atende à meta de ≤ 1 intervenção por semana do PRD. |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Aciona `configuracao-veiculos-alvo`, `cadastro-leiloeiros`, `coletor-lotes`, `parser-lotes` e `motor-filtros`. Solicita envios ao `notificador-telegram`. É o dono da tabela de histórico de execuções no SQLite.

**Comportamento esperado:**
🟡 A interface é o log de execução e o relatório de saúde sob demanda. Formato do relatório:

```
Relatório de saúde — 21/09/2026
Janela: últimos 30 dias, 13 execuções

Leiloeiro       Execuções  Sucesso  Lotes novos/exec  Situação
Vip Leilões     13         100%     2.4               saudável
Copart          13         92%      5.8               atenção: 1 bloqueio recorrente
Claudio Kuss    13         100%     0.0               saudável
Freitas          9          67%     0.1               parser quebrado desde 14/09
Milan           13         100%     1.2               saudável

Recomendações de frequência:
- Claudio Kuss: espaçar. 6 execuções consecutivas sem nenhum lote novo.
- Copart: adensar. Média de 5.8 lotes novos por execução nas últimas 10.
Nenhuma alteração foi aplicada. A decisão é sua.
```

**Estados da UI (saída em log):**
- 🟡 Estado vazio: `Nenhuma execução registrada ainda. O relatório de saúde precisa de ao menos 1 execução.`
- 🟡 Estado de carregamento: `Execução em andamento: etapa 3 de 5 (parsing)...`
- 🟡 Estado de erro: `Execução abortada: banco de histórico inacessível. Nada foi varrido.`
- 🟡 Estado de sucesso: `Execução concluída em 4m12s. 5 leiloeiros, 312 lotes vistos, 2 novos notificados.`

---

## 9. Modelo de Dados

**Entidades novas ou modificadas:**

```
Execucao {                        // tabela no SQLite, propriedade deste componente
  id: string PRIMARY KEY          // identificador da execução
  iniciado_em: datetime INDEX     // base das janelas de 30 dias
  finalizado_em: datetime?        // nulo indica execução interrompida sem encerramento
  duracao_ms: int?
  veredito: enum                  // sucesso | sucesso_parcial | falha
  lotes_vistos: int
  lotes_candidatos: int
  lotes_novos: int
  lotes_ja_conhecidos: int
}

ExecucaoLeiloeiro {               // uma linha por leiloeiro por execução
  execucao_id: string INDEX
  leiloeiro_id: string INDEX
  buscas_ok: int
  buscas_bloqueadas: int
  buscas_falhas: int
  lotes_novos: int                // base do cálculo de recomendação de frequência
  quebra_suspeita: bool           // sinal vindo do parser-lotes
}

RecomendacaoFrequencia {          // objeto transiente, recalculado a cada execução
  leiloeiro_id: string
  acao: enum                      // espacar | adensar | manter
  justificativa: string           // a série numérica que sustenta a sugestão
  frequencia_atual: string        // o valor declarado hoje no YAML
}
```

**Migrações necessárias:** 🟡 Sim. Criação das tabelas `Execucao` e `ExecucaoLeiloeiro`, com índices sobre o instante de início e sobre o identificador do leiloeiro. A criação é idempotente e ocorre na primeira execução. O banco é o mesmo arquivo usado pelo `motor-filtros` para a tabela de lotes notificados.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|---|---|---|
| 🟡 Banco SQLite local | Obrigatória | Sem histórico não há observabilidade nem recomendação. A execução aborta antes de varrer, para não rodar sem deixar registro (EC-03). |
| 🟡 Mecanismo de agendamento do sistema operacional | Obrigatória | Sem ele as execuções dependem de disparo manual, o que anula a autonomia de RNF-05. |
| 🟡 `notificador-telegram` | Obrigatória | Canal dos alertas. Indisponível, os alertas ficam apenas no log, e o problema pode passar despercebido. |
| 🟡 `motor-filtros` | Obrigatória | Fornece as contagens de vistos, novos e já conhecidos, que são a matéria-prima da recomendação de frequência. |
| 🟡 `coletor-lotes` e `parser-lotes` | Obrigatórias | Fornecem os vereditos de coleta e os sinais de quebra que alimentam os alertas. |
| 🟡 Máquina ligada no horário previsto | Obrigatória | Execução perdida é executada com atraso, uma única vez (Fluxo Alternativo B). |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---|---|---|
| 🟡 EC-01: Execução anterior travada deixou trava órfã | Processo encerrado sem liberar a trava | A trava carrega o instante de aquisição. Passadas 2 horas, é considerada órfã, liberada com registro, e a execução prossegue. |
| 🟡 EC-02: Duas execuções disparadas ao mesmo tempo | Sobreposição de horários, ou disparo manual durante execução agendada | A segunda é recusada e o fato é registrado, sem processamento concorrente (RF-02). |
| 🟡 EC-03: Banco de histórico inacessível | Disco cheio, arquivo apagado, corrupção | A execução aborta antes de varrer. Varrer sem registrar produziria notificação sem rastro e corromperia a métrica de 95%. |
| 🟡 EC-04: Banco em lock durante a gravação final | Concorrência com o `motor-filtros` no mesmo arquivo | Aguarda com timeout de 10 segundos e uma tentativa de retry. Persistindo, registra a falha de gravação em log. |
| 🟡 EC-05: Máquina desligada no horário previsto | Notebook fechado | Executa com atraso uma única vez ao ser ligada, sem acumular as ocasiões perdidas (Fluxo Alternativo B). |
| 🟡 EC-06: Execução excede o intervalo até a próxima | Leiloeiro muito lento, ou volume atípico | A execução em andamento é preservada e a seguinte é recusada pela trava. O fato é registrado como sinal de que o intervalo é curto demais. |
| 🟡 EC-07: Leiloeiro recém-cadastrado, sem série histórica | Primeiras execuções após o cadastro | Nenhuma recomendação de frequência é emitida até haver 10 execuções, e nenhum alerta de taxa de sucesso até haver 10 na janela (RF-06). |
| 🟡 EC-08: Todos os leiloeiros falham na mesma execução | Queda de rede na máquina | Veredito de falha total, registrado no histórico (RF-12), com alerta único informando falha geral, sem um alerta por leiloeiro. |
| 🟡 EC-09: Sinal de quebra persistente por dias | Parser quebrado sem conserto | O alerta respeita o limite de um envio por dia por leiloeiro definido no notificador, e o relatório de saúde passa a exibir desde quando a quebra dura. |
| 🟡 EC-10: Recomendações contraditórias entre leiloeiros | Um leiloeiro sem novidade e outro com volume alto | As recomendações são por leiloeiro, e não globais, então convivem sem conflito. Cada uma cita o leiloeiro a que se aplica. |
| 🟡 EC-11: Mudança de horário de verão | Ajuste de fuso no sistema operacional | O instante é gravado de forma não ambígua (RNF-04), e a execução do dia da mudança pode ocorrer uma hora deslocada, sem duplicar nem ser omitida. |

---

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 Nenhuma. Processo local, disparado pelo agendador do sistema operacional.
- **Autorização:** 🟡 Nenhuma. Roda com as permissões do usuário da máquina.
- **Dados sensíveis:** 🟡 O histórico revela a rotina de busca do Rafael e o que ele encontrou ao longo do tempo. O arquivo do banco fica fora do versionamento, listado no `.gitignore`, junto da regra já estabelecida para o banco de lotes notificados. Nenhuma credencial é registrada no histórico, apenas o nome do leiloeiro e os vereditos.
- **Auditoria:** 🟡 Este componente é o registro de auditoria do sistema. O histórico de execuções permite responder, depois, o que rodou, quando, com que resultado e o que falhou.

---

## 13. Plano de Rollout

- **Estratégia:** 🟡 Em duas etapas. Primeiro a execução manual com histórico sendo gravado, o que permite validar toda a cadeia observando os registros. Só depois o agendamento automático é ativado, quando as execuções manuais já estiverem consistentes. A recomendação de frequência entra em operação por último, pois depende de dez execuções acumuladas por leiloeiro.
- **Como reverter (rollback):** 🟡 Desativar a entrada no agendador do sistema operacional interrompe as execuções automáticas sem apagar nada, e a execução manual continua disponível. O histórico é preservado. Apagar o banco é operação destrutiva: zeraria o histórico, as métricas e as recomendações, e faria o `motor-filtros` renotificar tudo, já que o arquivo é compartilhado. Exige decisão explícita do Rafael.
- **Monitoramento pós-deploy:** 🟡 Na primeira semana, conferir se as execuções ocorreram nos horários previstos, se toda execução iniciada tem registro de encerramento (RNF-03) e se a duração está com folga em relação ao intervalo. Após um mês, avaliar se as recomendações de frequência fazem sentido contra a percepção do Rafael sobre o ritmo real dos editais.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---|---|---|---|
| 🟡 OQ-01 | Qual o formato da expressão de frequência no YAML: cron padrão de cinco campos ou um vocabulário simplificado como o usado nos exemplos? Questão espelhada em OQ-04 do `cadastro-leiloeiros`. | Médio | Rafael | Antes de implementar o agendador |
| 🟡 OQ-02 | Os limiares de 6 execuções sem novidade e de média 5 para adensar são adequados ao ritmo real dos editais de veículo? Foram definidos por estimativa, sem dado observado. | Alto | Rafael | Após 1 mês de operação |
| 🟡 OQ-03 | O horário de três execuções por semana deve ser pela manhã, ou existe um momento do dia em que os leiloeiros costumam publicar editais novos? | Médio | Rafael | Antes de ativar o agendamento |
| 🟡 OQ-04 | O agendamento deve usar o mecanismo do sistema operacional ou um processo residente próprio? A escolha muda o comportamento em caso de máquina desligada. | Alto | Rafael | Antes de implementar o agendador |
| 🟡 OQ-05 | Quando o sistema migrar do notebook para servidor caseiro ou VPS, o histórico acumulado deve ser transferido, ou a série reinicia? | Baixo | Rafael | Na migração de infraestrutura |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---|---|---|
| 🟡 Três execuções por semana como padrão inicial, configurável por leiloeiro | Uma vez ao dia; de hora em hora; intervalo global único | Escolhido em diálogo com o Rafael em 2026-09-21, partindo da avaliação dele de que editais de leilão de veículo não são publicados diariamente. Começar espaçado e adensar com base em dado observado é mais barato que o contrário, e reduz o risco de bloqueio anti-bot na estreia. |
| 🟡 Recomendação de frequência calculada pelo sistema, aplicada pelo Rafael | Ajuste automático da frequência; frequência fixa sem revisão | Ajuste automático removeria o Rafael de uma decisão que afeta custo e risco de bloqueio, contrariando o modelo de debate do `ideation.md`. Frequência fixa desperdiçaria o histórico que o sistema acumula de graça. |
| 🟡 Séries de lotes novos por execução como base da recomendação | Contagem de lotes vistos; volume total coletado | Lotes vistos variam com o tamanho do catálogo do leiloeiro, e não com a chegada de novidade. Lote novo é o único número que mede o que a varredura acrescentou, que é exatamente o que a frequência deveria otimizar. |
| 🟡 Exigir 10 execuções antes de recomendar, e 10 na janela antes de alertar por taxa | Recomendar desde a primeira execução | Uma série curta produziria recomendação instável, oscilando a cada execução. Exigir base mínima evita sugerir mudança por causa de uma semana atípica. |
| 🟡 Abortar a execução quando o histórico não puder ser gravado | Varrer e notificar mesmo sem registrar | Uma execução sem registro corromperia a métrica de 95% e produziria notificação sem rastro. A observabilidade é o propósito deste componente, então operar sem ela contradiz sua razão de existir. |
| 🟡 Execução perdida é recuperada uma única vez | Ignorar execuções perdidas; recuperar todas as perdidas | Recuperar todas faria uma máquina desligada por uma semana disparar várias varreduras em sequência ao ligar. Ignorar por completo deixaria um notebook de uso intermitente sem nenhuma varredura. |
| 🟡 Histórico no mesmo arquivo SQLite dos lotes notificados | Banco separado por componente | Um arquivo único simplifica backup e permite consultar em conjunto quais execuções geraram quais notificações. O custo é a contenção de escrita, tratada em EC-04. |

---

## Apêndice

### Referências
- `_reversa_sdd/prd.md` — seção 3, métricas de estabilidade e autonomia; seção 4, escopo "Execução periódica automatizada" e "Gestão por agente de IA"; seção 9, critério de não falhar em silêncio; seção "Pendências de cobertura", frequência de varredura
- `_reversa_sdd/ideation.md` — seções "Arquitetura iterativa com agente de IA como gestor" e "Infraestrutura (progressiva)"
- `_reversa_sdd/sdd/motor-filtros.md` — origem das contagens de lotes vistos, novos e já conhecidos
- `_reversa_sdd/sdd/cadastro-leiloeiros.md` — origem da frequência declarada por leiloeiro

### Histórico de Revisões
| Versão | Data | Autor | Mudanças |
|---|---|---|---|
| 1.0 | 2026-09-21 | reversa-spec-sdd | Criação inicial a partir do PRD |
