# Spec: Configuração de Veículos-Alvo

> Selo 🟡 PLANEJADO em todos os itens. Nenhum fato aqui foi extraído de código existente.

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-09-21
**Reviewers:** Rafael

---

## 1. Resumo

🟡 Componente que define **o que** o sistema procura. Mantém a lista de veículos-alvo do Rafael — cada um com marca, modelo, faixa de ano, teto de preço e tipos de leilão aceitos — em um arquivo YAML editável à mão, carregando e validando essa lista no início de cada varredura.

---

## 2. Contexto e Motivação

**Problema:**
🟡 Hoje os critérios de busca existem apenas na cabeça do Rafael e são reaplicados manualmente em cada site de leiloeiro, um por um. Não há uma fonte única do que está sendo procurado, então um critério pode ser aplicado em um site e esquecido em outro.

**Evidências:**
🟡 A jornada descrita em `personas.md` começa exatamente por "configurar lista de veículos-alvo". O `ideation.md` registra que a lista é dinâmica: "Rafael adiciona/remove veículos conforme interesse".

**Por que agora:**
🟡 Todo o resto do sistema depende deste componente. O `motor-filtros` não tem contra o que comparar os lotes sem uma lista de alvos carregada e validada.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Permitir que o Rafael declare N veículos-alvo em um único arquivo, sem escrever código.
- [ ] 🟡 G-02: Rejeitar configuração inválida no início da execução, antes de qualquer requisição de rede, com mensagem que aponta o campo errado.
- [ ] 🟡 G-03: Permitir desativar um alvo temporariamente sem apagar sua definição.

**Métricas de sucesso:**

| Métrica | Baseline atual | Target | Prazo |
|---|---|---|---|
| 🟡 Tempo para adicionar um novo veículo-alvo | Não existe (critério informal) | < 60 segundos editando o YAML | MVP |
| 🟡 Execuções abortadas por config inválida chegando à rede | Não existe | 0 (falha sempre antes do fetch) | MVP |
| 🟡 Veículos-alvo suportados simultaneamente | 0 | ≥ 20 sem degradação perceptível | MVP |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: **Interface gráfica ou comandos de CRUD.** A edição é feita direto no arquivo YAML, em um editor de texto. Não haverá formulário web, CLI interativo nem bot de cadastro pelo Telegram no MVP.
- 🟡 NG-02: **Múltiplos perfis de usuário.** Existe uma única lista de veículos-alvo, do Rafael. Não há separação por usuário, conta ou workspace.
- 🟡 NG-03: **Recarga a quente (hot reload).** A lista é lida uma vez no início de cada execução da varredura. Alterar o arquivo durante uma execução em andamento não afeta aquela execução.
- 🟡 NG-04: **Consulta à tabela FIPE para sugerir o teto de preço.** O teto é informado manualmente pelo Rafael. Integração com FIPE está registrada como evolução futura no `prd.md`.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 Rafael — comprador pessoa física, nível técnico intermediário, confortável editando arquivos de configuração em um editor de texto.
**Usuário secundário:** 🟡 Agente de IA gestor (Claude Code / Codex / Antigravity), que lê e edita o mesmo arquivo ao ajustar a configuração a pedido do Rafael.

**Jornada atual (sem a feature):**
1. 🟡 Rafael decide mentalmente que quer, por exemplo, um Nissan Versa 2018–2021 até R$ 45.000.
2. 🟡 Abre cada site de leiloeiro e reaplica esses filtros na mão, um por um.
3. 🟡 Ao mudar de ideia sobre o teto de preço, precisa refazer tudo em todos os sites.

**Jornada futura (com a feature):**
1. 🟡 Rafael abre `config/veiculos-alvo.yaml` e adiciona um bloco com marca, modelo, faixa de ano, teto e tipos de leilão.
2. 🟡 Salva o arquivo.
3. 🟡 Na próxima execução agendada, o novo alvo já entra na varredura de todos os leiloeiros cadastrados.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| 🟡 RF-01 | O sistema deve carregar a lista de veículos-alvo de um arquivo YAML em caminho fixo (`config/veiculos-alvo.yaml`) no início de cada execução. | Must | Com um YAML contendo 3 alvos válidos, o componente retorna exatamente 3 objetos `VeiculoAlvo` com todos os campos preenchidos. |
| 🟡 RF-02 | O sistema deve aceitar, para cada veículo-alvo, os campos: `marca`, `modelo`, `ano_min`, `ano_max`, `preco_maximo`, `tipos_leilao` e `ativo`. | Must | Um alvo com os 7 campos preenchidos é carregado sem erro e todos os valores são acessíveis no objeto resultante. |
| 🟡 RF-03 | O sistema deve validar que `ano_min` ≤ `ano_max` e que `preco_maximo` é um número maior que zero. | Must | Um alvo com `ano_min: 2020` e `ano_max: 2018` faz o carregamento falhar com erro citando o nome do alvo e o campo `ano_min`. |
| 🟡 RF-04 | O sistema deve abortar a execução inteira quando o arquivo de configuração for inválido, antes de realizar qualquer requisição HTTP. | Must | Com um YAML malformado, nenhum log de fetch é emitido e o processo encerra com código de saída diferente de zero. |
| 🟡 RF-05 | O sistema deve ignorar, na varredura, todo veículo-alvo cujo campo `ativo` seja `false`, mantendo sua definição no arquivo. | Must | Com 3 alvos, um deles `ativo: false`, o componente retorna 2 alvos ativos e a definição do terceiro permanece intacta no YAML. |
| 🟡 RF-06 | O sistema deve aceitar `tipos_leilao` como lista de um ou mais valores do conjunto fechado: `judicial`, `extrajudicial`, `financiamento`, `seguradora`, `recuperado`. | Must | Um alvo com os valores `financiamento` e `seguradora` carrega sem erro; um alvo com o valor `inexistente` é rejeitado com erro citando o valor inválido e os cinco valores aceitos. |
| 🟡 RF-07 | O sistema deve atribuir a cada veículo-alvo um identificador estável derivado de `marca`, `modelo` e faixa de ano, usado pelos demais componentes para rastrear qual alvo originou uma notificação. | Should | Dois carregamentos sucessivos do mesmo arquivo produzem o mesmo `id` para o mesmo alvo. |
| 🟡 RF-08 | O sistema deve emitir aviso (sem abortar) quando a lista de alvos ativos estiver vazia. | Should | Com todos os alvos `ativo: false`, o log contém um aviso explícito e a execução termina sem erro, sem notificar nada. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O agendador dispara uma execução de varredura.
2. 🟡 O componente lê o arquivo `config/veiculos-alvo.yaml` do disco.
3. 🟡 O componente faz o parse do YAML em uma lista de estruturas brutas.
4. 🟡 O componente valida cada entrada contra as regras de RF-03 e RF-06.
5. 🟡 O componente descarta as entradas com `ativo: false`.
6. 🟡 O componente calcula o `id` estável de cada alvo restante (RF-07).
7. 🟡 Resultado: uma lista de objetos `VeiculoAlvo` validados é entregue ao `motor-filtros`.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Arquivo de configuração ausente na primeira execução:**
1. 🟡 O componente não encontra `config/veiculos-alvo.yaml`.
2. 🟡 O componente cria um arquivo de exemplo comentado no caminho esperado, com um alvo fictício e `ativo: false`.
3. 🟡 O componente aborta a execução com mensagem orientando o Rafael a editar o arquivo recém-criado.

**Fluxo Alternativo B — Ajuste de teto de preço entre execuções:**
1. 🟡 Rafael altera `preco_maximo` de um alvo já existente.
2. 🟡 Na execução seguinte, o novo teto é aplicado.
3. 🟡 Lotes que já haviam sido notificados não são renotificados por causa da mudança, pois a deduplicação é responsabilidade do `motor-filtros`.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|---|---|---|---|
| 🟡 RNF-01 | Tempo de carregamento e validação | < 100 ms para 50 alvos | Operação puramente local, sem rede ou banco. |
| 🟡 RNF-02 | Legibilidade por humano | Arquivo aceita comentários e mantém a ordem escrita pelo Rafael | Motivo central da escolha de YAML sobre banco de dados. |
| 🟡 RNF-03 | Codificação | UTF-8 sem BOM | Marcas e modelos podem conter acentuação (ex.: "Citroën"). |
| 🟡 RNF-04 | Mensagens de erro | Toda falha de validação cita o nome do alvo e o campo problemático | O Rafael precisa corrigir sem ler o código-fonte. |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Arquivo `config/veiculos-alvo.yaml`; consumidor direto é o `motor-filtros`; consumidor indireto é o `agendador-observabilidade`, que registra quantos alvos estavam ativos em cada execução.

**Comportamento esperado:**
🟡 A "interface" deste componente é o próprio arquivo YAML. Um exemplo válido:

```yaml
# Lista de veículos que quero monitorar nos leilões.
# Desative um alvo com `ativo: false` em vez de apagar o bloco.
# ano_min e ano_max referem-se ao ANO DE MODELO (o segundo número em 2018/2019).
# preco_maximo é comparado contra o LANCE CORRENTE do lote, e não contra o inicial.
veiculos:
  - marca: Nissan
    modelo: Versa
    ano_min: 2018
    ano_max: 2021
    preco_maximo: 45000
    tipos_leilao:
      - financiamento
      - seguradora
    ativo: true

  - marca: Toyota
    modelo: Corolla
    ano_min: 2017
    ano_max: 2020
    preco_maximo: 62000
    tipos_leilao:
      - judicial
      - extrajudicial
      - financiamento
    ativo: true
```

**Estados da UI (saída em log):**
- 🟡 Estado vazio: `Nenhum veículo-alvo ativo. Nada a procurar nesta execução.`
- 🟡 Estado de carregamento: `Carregando veículos-alvo de config/veiculos-alvo.yaml...`
- 🟡 Estado de erro: `Configuração inválida em 'Nissan Versa': ano_min (2020) é maior que ano_max (2018). Execução abortada.`
- 🟡 Estado de sucesso: `7 veículos-alvo ativos carregados (2 inativos ignorados).`

---

## 9. Modelo de Dados

**Entidades novas ou modificadas:**

```
VeiculoAlvo {
  id: string           // derivado de marca+modelo+faixa de ano, estável entre execuções
  marca: string        // obrigatório, não vazio
  modelo: string       // obrigatório, não vazio
  ano_min: int         // obrigatório, <= ano_max
  ano_max: int         // obrigatório, >= ano_min
  preco_maximo: decimal // obrigatório, > 0, em reais
  tipos_leilao: string[] // >= 1 item, valores do conjunto fechado de RF-06
  ativo: bool          // padrão true quando omitido
}
```

**Migrações necessárias:** 🟡 Não. O componente não escreve em banco; apenas lê um arquivo YAML. A única escrita possível é a criação do arquivo de exemplo descrito no Fluxo Alternativo A.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|---|---|---|
| 🟡 Arquivo `config/veiculos-alvo.yaml` | Obrigatória | Execução abortada; arquivo de exemplo é criado para orientar a correção (Fluxo Alternativo A). |
| 🟡 Biblioteca de parsing YAML | Obrigatória | Falha de import encerra o processo; sem fallback, é dependência de instalação. |
| 🟡 Sistema de arquivos local com permissão de leitura | Obrigatória | Erro de permissão é reportado com o caminho absoluto tentado. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---|---|---|
| 🟡 EC-01: Arquivo ausente | Primeira execução, ou arquivo apagado | Cria arquivo de exemplo comentado, aborta com mensagem orientando a edição. |
| 🟡 EC-02: YAML sintaticamente malformado | Indentação errada, aspas não fechadas | Aborta antes de qualquer fetch, citando a linha reportada pelo parser. |
| 🟡 EC-03: `ano_min` maior que `ano_max` | Erro de digitação do Rafael | Aborta citando nome do alvo e ambos os valores. |
| 🟡 EC-04: `preco_maximo` ausente, zero ou negativo | Campo esquecido ou digitado errado | Aborta citando o alvo e o campo. Não assume teto infinito. |
| 🟡 EC-05: `tipos_leilao` com valor fora do conjunto fechado | Rafael escreve "leilao judicial" em vez de "judicial" | Aborta listando o valor inválido e os 5 valores aceitos. |
| 🟡 EC-06: Dois alvos idênticos (mesma marca, modelo e faixa de ano) | Duplicação por copiar e colar | Emite aviso, mantém apenas a primeira ocorrência, prossegue a execução. |
| 🟡 EC-07: Lista `veiculos` declarada sem nenhum item, ou todos inativos | Rafael desativou tudo temporariamente | Aviso explícito no log, execução termina com sucesso sem notificar nada (RF-08). |
| 🟡 EC-08: Arquivo com BOM ou codificação diferente de UTF-8 | Editor do Windows salvando como ANSI | Aborta com mensagem indicando o problema de codificação e o encoding esperado. |
| 🟡 EC-09: Campo `ativo` omitido | Bloco escrito sem a chave | Assume `true` (padrão declarado no modelo de dados), sem aviso. |
| 🟡 EC-10: Arquivo inacessível ou leitura travada | Arquivo em lock por outro processo, ou em pasta de nuvem sincronizando | A leitura tem timeout de 5 segundos. Estourado o limite, a falha é reportada com o caminho absoluto e a execução aborta, sem retry silencioso que mascararia o problema. |

---

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 Nenhuma. Ferramenta pessoal de usuário único, rodando na máquina do próprio Rafael.
- **Autorização:** 🟡 Nenhuma. Quem tem acesso ao sistema de arquivos tem acesso à configuração.
- **Dados sensíveis:** 🟡 Este arquivo não contém credenciais, dados pessoais nem informação financeira de terceiros. Contém apenas preferências de compra. Credenciais de leiloeiros são responsabilidade exclusiva do componente `cadastro-leiloeiros`, em `.env`, e nunca devem aparecer neste YAML.
- **Auditoria:** 🟡 Cada execução registra no log quantos alvos estavam ativos e o `id` de cada um, permitindo reconstruir depois qual configuração gerou qual notificação.

---

## 13. Plano de Rollout

- **Estratégia:** 🟡 Big bang. É componente fundacional do MVP, sem versão anterior em produção para conviver.
- **Como reverter (rollback):** 🟡 O arquivo YAML é versionado no git. Reverter uma configuração problemática é um `git checkout` do arquivo. Como o componente não escreve estado em banco, não há migração a desfazer.
- **Monitoramento pós-deploy:** 🟡 Nas primeiras 3 execuções, conferir no log se a contagem de alvos ativos bate com o que o Rafael espera, e se nenhum alvo foi silenciosamente descartado como duplicado (EC-06).

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---|---|---|---|
| 🟡 OQ-01 | O conjunto fechado de `tipos_leilao` (judicial, extrajudicial, financiamento, seguradora, recuperado) cobre a nomenclatura real dos 5 leiloeiros-alvo? A terminologia varia entre sites. | Alto | Rafael | Antes de cadastrar o segundo leiloeiro |
| 🟡 OQ-02 | Faz sentido um campo opcional de quilometragem máxima? Não foi levantado na ideação, ainda que seja critério comum na compra de carro usado. | Médio | Rafael | Pós-MVP |
| 🟡 OQ-03 | O teto de preço deve admitir uma margem de segurança configurável, para não notificar lote que já abriu encostado no limite? A decisão sobre a margem pertence ao `motor-filtros` OQ-01, e pode exigir um campo novo aqui. | Médio | Rafael | Após as primeiras semanas de uso |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---|---|---|
| 🟡 Teto de preço por veículo-alvo, não global | Teto global único; nenhum filtro de preço | Escolhido pelo Rafael em 2026-09-21. Um Versa 2018 e um Corolla 2020 têm faixas de mercado diferentes; um teto único ou seria alto demais para um ou baixo demais para o outro. |
| 🟡 YAML como formato de configuração | SQLite; JSON | Escolhido em 2026-09-21. YAML aceita comentários, é editável à mão sem ferramenta e versiona bem em git — requisitos que vêm do fato de o Rafael e um agente de IA editarem o mesmo arquivo. JSON não aceita comentários; SQLite exigiria ferramenta para uma edição trivial. |
| 🟡 `tipos_leilao` como conjunto fechado e validado | Texto livre | Texto livre transferiria o erro de digitação para o `motor-filtros`, onde ele falharia silenciosamente como "nenhum lote casou". Validar na entrada torna o erro imediato e explícito. |
| 🟡 Desativar via campo `ativo` em vez de apagar o bloco | Comentar o bloco no YAML; remover e reescrever depois | Preserva a definição (teto, faixa de ano) que custou tempo para calibrar, e mantém o histórico legível no git. |
| 🟡 `ano_min` e `ano_max` referem-se ao ano de modelo | Ano de fabricação | Escolhido pelo Rafael em 2026-09-22. Alinha a faixa declarada aqui com o critério aplicado no `motor-filtros` RF-03 e com a referência de preço da FIPE. Um comentário no YAML de exemplo deixa isso explícito para quem editar o arquivo. |
| 🟡 `preco_maximo` é comparado contra o lance corrente do lote | Lance inicial | Escolhido pelo Rafael em 2026-09-22. O teto passa a significar "quanto eu aceito pagar agora", e não "de quanto o pregão partiu". Detalhamento e limites em `motor-filtros` RF-04 e OQ-01. |

---

## Apêndice

### Referências
- `_reversa_sdd/prd.md` — seção 4, escopo "Configuração de veículos-alvo"
- `_reversa_sdd/ideation.md` — seção "Filtros configuráveis"
- `_reversa_sdd/personas.md` — jornada principal, passo 1

### Histórico de Revisões
| Versão | Data | Autor | Mudanças |
|---|---|---|---|
| 1.0 | 2026-09-21 | reversa-spec-sdd | Criação inicial a partir do PRD |
