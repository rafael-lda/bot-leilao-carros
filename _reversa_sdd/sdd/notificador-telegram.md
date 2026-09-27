# Spec: Notificador Telegram

> Selo 🟡 PLANEJADO em todos os itens. Nenhum fato aqui foi extraído de código existente.

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-09-21
**Reviewers:** Rafael

---

## 1. Resumo

🟡 Componente que **entrega o resultado**. Monta um digest único por execução, com os lotes novos que o `motor-filtros` aprovou, e o envia ao Rafael pelo Telegram. Também envia alertas operacionais quando um parser quebra ou um leiloeiro passa a falhar. Confirma cada envio, e essa confirmação é o que autoriza o motor a gravar os lotes como notificados.

---

## 2. Contexto e Motivação

**Problema:**
🟡 Todo o trabalho de coleta, parsing e filtragem não vale nada se o resultado não chegar ao Rafael onde ele já olha. Um relatório em arquivo local exigiria que ele se lembrasse de abrir; um e-mail se perderia entre outros. O Telegram é onde a notificação chega no bolso, com link clicável para o lote.

**Evidências:**
🟡 O `prd.md` fixa o Telegram como canal e define os três campos do MVP: nome ou modelo do carro, preço e link. O critério de aceite exige que o Rafael consiga acessar o lote no site do leiloeiro pelo link em um clique. O PRD também exige que a quebra de um parser seja notificada, e não apenas registrada.

**Por que agora:**
🟡 É a única interface do sistema com o usuário. O `prd.md` declara como não-objetivo qualquer dashboard web ou aplicativo, o que torna este componente a totalidade da experiência do Rafael com o produto.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Entregar ao Rafael, em uma única mensagem por execução, todos os lotes novos que casaram com seus critérios.
- [ ] 🟡 G-02: Garantir que cada lote do digest leve ao site do leiloeiro em um clique.
- [ ] 🟡 G-03: Avisar o Rafael quando o sistema deixar de funcionar, para que silêncio nunca seja confundido com ausência de oportunidade.

**Métricas de sucesso:**

| Métrica | Baseline atual | Target | Prazo |
|---|---|---|---|
| 🟡 Digests entregues com sucesso | Não existe | ≥ 99% | 3 meses |
| 🟡 Cliques necessários da notificação até o lote no site | Não existe | 1 | MVP |
| 🟡 Tempo entre o fim da filtragem e a chegada do digest | Não existe | < 30 segundos | MVP |
| 🟡 Quebras de parser que chegaram ao Rafael como alerta | Não existe | 100% | 3 meses |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: **Receber comandos pelo Telegram.** O canal é de mão única no MVP. Configurar alvos ou leiloeiros pelo bot está fora do escopo, conforme os não-objetivos do `prd.md`.
- 🟡 NG-02: **Enviar fotos, laudos ou vídeos.** O digest traz texto e link. Anexos estão registrados como evolução futura no `ideation.md`.
- 🟡 NG-03: **Opinar sobre o lote.** Parecer de agente de IA e consulta à tabela FIPE são evolução futura declarada no PRD.
- 🟡 NG-04: **Decidir o que é relevante.** O notificador envia o que o `motor-filtros` aprovou, sem filtrar de novo nem reordenar por critério próprio.
- 🟡 NG-05: **Notificar múltiplos destinatários.** Ferramenta pessoal, com um único destino configurado.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 Rafael — recebe o digest no celular, avalia os lotes pela descrição e pelo preço, e abre no site os que merecem análise detalhada.
**Usuário secundário:** 🟡 Agente de IA gestor, destinatário indireto dos alertas operacionais, que servem de gatilho para ele investigar um parser quebrado.

**Jornada atual (sem a feature):**
1. 🟡 Rafael precisa lembrar de abrir os sites para saber se surgiu algo.
2. 🟡 Descobre um lote interessante apenas quando decide procurar.
3. 🟡 Não tem como saber se deixou de olhar em um dia em que apareceu o carro certo.

**Jornada futura (com a feature):**
1. 🟡 Rafael recebe no Telegram um digest quando a varredura encontra lotes novos.
2. 🟡 Lê modelo, ano e preço de cada lote na própria mensagem.
3. 🟡 Toca no link do que interessou e cai direto na página do lote no leiloeiro.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| 🟡 RF-01 | O sistema deve montar uma única mensagem de digest por execução, contendo todos os lotes novos recebidos do `motor-filtros`. | Must | Uma execução com 4 lotes novos gera uma mensagem contendo os 4, e não 4 mensagens. |
| 🟡 RF-02 | O sistema deve apresentar, para cada lote do digest, marca e modelo, ano, preço, nome do leiloeiro e link do lote. | Must | Cada item do digest exibe os cinco elementos, com o link acessível em um toque. |
| 🟡 RF-03 | O sistema deve exibir a marcação de preço a confirmar no lugar do valor quando o lote vier sem preço. | Must | Um lote com preço nulo aparece no digest com a marcação textual, e não com valor zerado ou campo em branco. |
| 🟡 RF-04 | O sistema deve enviar a mensagem via API de bot do Telegram para o destino configurado. | Must | A mensagem chega à conversa do Rafael, e a API retorna confirmação de entrega. |
| 🟡 RF-05 | O sistema deve confirmar ao `motor-filtros` o sucesso do envio, e essa confirmação é o que autoriza a gravação dos lotes como notificados. | Must | Um envio falho não produz confirmação, e nenhum lote daquele digest é gravado como notificado. |
| 🟡 RF-06 | O sistema deve dividir o digest em mensagens sucessivas quando o texto ultrapassar o limite de tamanho da plataforma, preservando a integridade de cada item. | Must | Um digest com 60 lotes é entregue em várias mensagens, sem que nenhum lote apareça cortado ao meio. |
| 🟡 RF-07 | O sistema deve deixar de enviar mensagem quando a lista de lotes novos estiver vazia. | Must | Uma execução sem lotes novos não gera nenhuma mensagem no Telegram. |
| 🟡 RF-08 | O sistema deve enviar alerta operacional, em mensagem distinta do digest, quando receber sinal de quebra de parser ou de leiloeiro em falha recorrente. | Must | Um sinal de quebra do `parser-lotes` produz mensagem de alerta identificando o leiloeiro afetado. |
| 🟡 RF-09 | O sistema deve repetir o envio até 3 tentativas, com espera crescente, antes de declarar o envio como falho. | Must | Uma indisponibilidade passageira do Telegram na primeira tentativa resulta em entrega na segunda, com o número de tentativas registrado. |
| 🟡 RF-10 | O sistema deve escapar os caracteres de formatação presentes em textos vindos dos leiloeiros, de modo que a mensagem não seja rejeitada nem exibida de forma corrompida. | Must | Um modelo contendo caractere especial de formatação é entregue com o texto íntegro. |
| 🟡 RF-11 | O sistema deve incluir no cabeçalho do digest a data e hora da execução e a contagem de lotes novos. | Should | O digest inicia com uma linha de cabeçalho contendo o instante e o total. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O notificador recebe do `motor-filtros` a lista de lotes novos.
2. 🟡 O notificador monta o cabeçalho com data, hora e contagem.
3. 🟡 Para cada lote, o notificador formata a linha com modelo, ano, preço, leiloeiro e link.
4. 🟡 O notificador escapa os caracteres de formatação do texto de origem.
5. 🟡 O notificador verifica se o texto cabe no limite da plataforma.
6. 🟡 O notificador envia a mensagem pela API do bot.
7. 🟡 A API confirma a entrega.
8. 🟡 O notificador confirma o sucesso ao motor, que grava os lotes como notificados.
9. 🟡 Resultado: Rafael recebe no celular um digest com os lotes novos e links clicáveis.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Digest extenso:**
1. 🟡 O texto montado ultrapassa o limite de tamanho da plataforma.
2. 🟡 O notificador quebra a lista em blocos, respeitando o limite de cada mensagem.
3. 🟡 Os blocos são enviados em sequência, e a confirmação só é dada após o último bloco ter sido aceito.

**Fluxo Alternativo B — Alerta operacional sem lotes novos:**
1. 🟡 A execução não encontrou lotes novos e um parser emitiu sinal de quebra.
2. 🟡 Nenhum digest é enviado (RF-07).
3. 🟡 O alerta operacional é enviado assim mesmo, pois o silêncio nesse caso significaria problema oculto.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|---|---|---|---|
| 🟡 RNF-01 | Latência de entrega | < 30 segundos após o fim da filtragem | O valor de um lote de leilão decai com o tempo. |
| 🟡 RNF-02 | Confiabilidade da confirmação | A confirmação só é emitida após aceite da plataforma | Confirmação otimista faria lotes sumirem sem nunca terem chegado. |
| 🟡 RNF-03 | Segurança | O token do bot vem de variável de ambiente e nunca aparece em log | Mesmo tratamento das credenciais de leiloeiro. |
| 🟡 RNF-04 | Legibilidade no celular | Cada lote ocupa no máximo 3 linhas na tela | Digest precisa ser varrido com o polegar, sem rolagem excessiva por item. |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Consome a lista de lotes novos do `motor-filtros` e os sinais de saúde do `agendador-observabilidade`. Integra com a API de bot do Telegram. Sua confirmação de envio é consumida de volta pelo `motor-filtros`.

**Comportamento esperado:**
🟡 A interface é a mensagem no Telegram. Formato do digest:

```
Varredura de 21/09/2026 08:03 — 2 lotes novos

1. Nissan Versa 1.6 SV — 2019
   R$ 41.900 — Vip Leilões
   https://www.vipleiloes.com.br/lote/887431

2. Toyota Corolla XEi — 2018
   Preço a confirmar — Copart
   https://www.copart.com.br/lot/55120987
```

Formato do alerta operacional:

```
Alerta do sistema — 21/09/2026 08:03

Freitas: parser não extraiu nenhum lote de uma página com conteúdo.
O site provavelmente mudou de layout e aquele leiloeiro está sem cobertura.
```

**Estados da UI:**
- 🟡 Estado vazio: nenhuma mensagem é enviada quando não há lotes novos nem alertas (RF-07).
- 🟡 Estado de carregamento: não se aplica; o envio é uma operação única, sem estado intermediário visível ao Rafael.
- 🟡 Estado de erro: falha de envio não produz mensagem ao Rafael, por motivo evidente. É registrada em log e o digest é refeito na execução seguinte.
- 🟡 Estado de sucesso: o digest entregue é a própria confirmação visível.

---

## 9. Modelo de Dados

**Entidades novas ou modificadas:**

```
Digest {                        // objeto transiente, montado e descartado
  executado_em: datetime        // instante da execução que originou o digest
  total_novos: int              // contagem exibida no cabeçalho
  itens: ItemDigest[]           // um por lote novo
}

ItemDigest {
  titulo: string                // marca e modelo, como vieram do leiloeiro
  ano: int?                     // ano de modelo
  preco_formatado: string       // valor em reais, ou a marcação de preço a confirmar
  leiloeiro: string             // nome legível, e não o identificador
  link: string                  // URL absoluta do lote
}

AlertaOperacional {             // objeto transiente
  executado_em: datetime
  severidade: enum              // aviso | critico
  leiloeiro: string?            // nulo quando o alerta é do sistema como um todo
  mensagem: string              // texto explicativo em linguagem direta
}
```

**Migrações necessárias:** 🟡 Não. O componente não persiste estado. O registro do envio vive no histórico de execuções do `agendador-observabilidade`, e o registro dos lotes notificados no banco do `motor-filtros`.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|---|---|---|
| 🟡 API de bot do Telegram | Obrigatória | Sem ela não há entrega. O envio é retentado 3 vezes; falhando, os lotes permanecem não notificados e reaparecem na execução seguinte. |
| 🟡 Token do bot em variável de ambiente | Obrigatória | Ausência ou invalidez do token impede qualquer envio; a falha é reportada em log de forma explícita. |
| 🟡 Identificador da conversa de destino | Obrigatória | Sem ele o bot não sabe para quem enviar; validado na partida junto do token. |
| 🟡 `motor-filtros` | Obrigatória | Fornece os lotes a notificar e consome a confirmação de envio. |
| 🟡 Conexão de rede | Obrigatória | Sem rede o envio falha por timeout, e os lotes seguem como não notificados. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---|---|---|
| 🟡 EC-01: Telegram indisponível ou lento | Instabilidade da plataforma | Timeout de 20 segundos por tentativa, com até 3 tentativas e espera crescente (RF-09). Esgotadas, o envio é declarado falho e nenhuma confirmação é emitida. |
| 🟡 EC-02: Token do bot inválido ou revogado | Token trocado sem atualizar o ambiente | Falha reportada de forma distinta de indisponibilidade, sem retry em laço, com mensagem em log orientando a renovar o token. |
| 🟡 EC-03: Identificador de conversa errado | Configuração incorreta | A plataforma rejeita o envio; a falha é registrada citando o destino configurado, sem expor o token. |
| 🟡 EC-04: Digest acima do limite de tamanho | Execução com dezenas de lotes novos | Dividido em mensagens sucessivas sem cortar item ao meio (RF-06). |
| 🟡 EC-05: Limite de taxa da plataforma atingido | Muitas mensagens em sequência no envio dividido | Respeita a espera indicada pela plataforma e retoma o envio dos blocos restantes. |
| 🟡 EC-06: Texto do lote com caractere de formatação | Título com caractere reservado pela sintaxe de formatação | Escapado antes do envio, preservando o texto original (RF-10). |
| 🟡 EC-07: Falha depois que parte dos blocos foi enviada | Interrupção no meio do envio dividido | A confirmação não é emitida. Os lotes voltam na execução seguinte, com duplicação parcial, que é o erro preferível à perda. |
| 🟡 EC-08: Link do lote inválido ou relativo | Parser não resolveu a URL | O item é enviado assim mesmo, com o link como veio, e a ocorrência é registrada para revisão do parser. |
| 🟡 EC-09: Execução sem lotes novos e sem alertas | Varredura silenciosa e saudável | Nenhuma mensagem é enviada. Ausência de mensagem é o estado normal de uma execução sem novidade. |
| 🟡 EC-10: Alerta operacional repetido a cada execução | Parser quebrado e ainda não consertado | O alerta é reenviado no máximo uma vez por dia por leiloeiro, evitando que o problema vire ruído diário. |

---

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 O bot autentica na plataforma com token, lido de variável de ambiente.
- **Autorização:** 🟡 O bot envia para um único destino configurado. Não responde a comandos nem aceita interação de terceiros (NG-01).
- **Dados sensíveis:** 🟡 O token do bot é credencial que permite enviar mensagens em nome do bot, e é tratado como as credenciais de leiloeiro: fora do versionamento, nunca impresso em log (RNF-03). O conteúdo das mensagens revela o interesse de compra do Rafael e trafega pela infraestrutura do Telegram, o que é aceito de forma consciente ao escolher o canal.
- **Auditoria:** 🟡 Cada tentativa de envio fica registrada com instante, quantidade de itens, número de tentativas e veredito, no histórico de execuções.

---

## 13. Plano de Rollout

- **Estratégia:** 🟡 Big bang, junto do primeiro leiloeiro. O envio pode ser validado de forma isolada, com um digest de teste, antes de o pipeline completo existir.
- **Como reverter (rollback):** 🟡 O componente não persiste estado, então reverter é trocar a versão do código. Para silenciar o sistema sem desligá-lo, basta remover o token do ambiente, o que faz os envios falharem de forma controlada e mantém os lotes como não notificados. Mensagens já entregues no Telegram não são recuperáveis, o que reforça a exigência de escapar e validar o texto antes do envio.
- **Monitoramento pós-deploy:** 🟡 Na primeira semana, conferir se o digest chega dentro do prazo de 30 segundos, se os links abrem os lotes corretos e se o formato permanece legível no celular. Acompanhar também se algum digest foi dividido, e se a divisão preservou os itens.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---|---|---|---|
| 🟡 OQ-01 | O digest deve agrupar os lotes por leiloeiro ou por veículo-alvo, em vez de listá-los em sequência única? | Médio | Rafael | Após as primeiras semanas de uso |
| 🟡 OQ-02 | Os alertas operacionais devem ir para a mesma conversa do digest ou para um canal separado, de modo a não misturar oportunidade com manutenção? | Médio | Rafael | Antes do primeiro alerta real |
| 🟡 OQ-03 | Vale um resumo semanal, com o que foi varrido e o que foi encontrado, mesmo sem lotes novos, para dar sinal de vida ao sistema? | Baixo | Rafael | Pós-MVP |
| 🟡 OQ-04 | O limite de um alerta por dia por leiloeiro (EC-10) é adequado, ou um parser quebrado deve insistir mais para não ser esquecido? | Médio | Rafael | Após a primeira quebra real |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---|---|---|
| 🟡 Digest único por execução | Uma mensagem por lote; digest com limite e transbordo | Escolhido pelo Rafael em 2026-09-21. Uma mensagem por lote produziria rajadas no celular a cada varredura. O digest concentra a novidade em um ponto de leitura, ao custo de agrupar os links. |
| 🟡 Confirmação de envio como gatilho da gravação | Motor grava ao declarar o candidato | Vem do `motor-filtros`. Separar envio de gravação e ordená-los nessa direção garante que nenhum lote seja dado como avisado sem ter chegado. |
| 🟡 Alerta operacional em mensagem separada do digest | Anexar os alertas ao final do digest | Alertas precisam chegar inclusive em execuções sem lotes novos, quando nenhum digest é enviado. Anexá-los ao digest os faria desaparecer justamente quando o sistema está quebrado. |
| 🟡 Nenhuma mensagem quando não há novidade | Enviar aviso de execução sem resultado | Uma mensagem a cada varredura em um sistema que roda três vezes por semana treinaria o Rafael a ignorar o bot. O sinal de vida do sistema é tratado em OQ-03. |
| 🟡 Limite de um alerta por dia por leiloeiro | Alertar a cada execução | Um parser quebrado permanece quebrado por dias até ser consertado. Alertar a cada execução transformaria o alerta em ruído previsível. |

---

## Apêndice

### Referências
- `_reversa_sdd/prd.md` — seção 4, escopo "Notificação via Telegram"; seção 5, não-objetivos de interface; seção 9, critério de acesso ao lote em 1 clique
- `_reversa_sdd/ideation.md` — seção "Canal de notificação"
- `_reversa_sdd/sdd/motor-filtros.md` — origem dos lotes novos e consumidor da confirmação de envio

### Histórico de Revisões
| Versão | Data | Autor | Mudanças |
|---|---|---|---|
| 1.0 | 2026-09-21 | reversa-spec-sdd | Criação inicial a partir do PRD |
