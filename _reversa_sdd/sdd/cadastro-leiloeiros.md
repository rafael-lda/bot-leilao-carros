# Spec: Cadastro de Leiloeiros

> Selo 🟡 PLANEJADO em todos os itens. Nenhum fato aqui foi extraído de código existente.

**Versão:** 1.3
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-09-21 (emenda em 2026-10-03)
**Reviewers:** Rafael

---

## 1. Resumo

🟡 Componente que define **onde** o sistema procura. Mantém o registro dos leiloeiros monitorados — suas buscas, declaradas como conjuntos de filtros chave-valor, a estratégia de acesso (público ou logado), o nível de ferramenta de coleta e a frequência própria de varredura — em um arquivo YAML, com as credenciais mantidas fora dele, em variáveis de ambiente.

---

## 2. Contexto e Motivação

**Problema:**
🟡 Cada leiloeiro tem site, layout e regra de acesso diferentes. Freitas, Vip Leilões, Claudio Kuss, Copart e Milan não compartilham estrutura nem nomenclatura. Sem um registro declarativo, adicionar um sexto leiloeiro significaria mexer em código, e a informação de qual site exige login viveria apenas na memória do Rafael.

**Evidências:**
🟡 O `ideation.md` registra a decisão de "verificar leiloeiro a leiloeiro o que é público vs. restrito" e a estratégia de escalonamento progressivo de ferramenta por site. O `prd.md` fixa a meta de ≥ 5 leiloeiros monitorados em 3 meses.

**Por que agora:**
🟡 A estratégia de buscas pré-definidas, escolhida na ideação em vez de automação de cliques, só funciona se existir um lugar estável para guardar essas buscas. Este componente é esse lugar.

🟢 **Emenda de 2026-10-03:** a ideação previa guardar a URL filtrada copiada do navegador. A investigação do Vip Leilões, em 2026-09-27, mostrou que os filtros viajam no corpo de um POST e que o redirecionamento de cookie descarta os parâmetros da URL. A busca passou a ser declarada como conjunto de filtros chave-valor, e cada leiloeiro tem um adaptador no `coletor-lotes` que traduz esses filtros na requisição real, seja ela POST com corpo ou GET com query string.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Permitir adicionar um novo leiloeiro editando somente um arquivo YAML, sem tocar em código.
- [ ] 🟡 G-02: Garantir que nenhuma senha de leiloeiro seja gravada em arquivo versionado.
- [ ] 🟡 G-03: Permitir que cada leiloeiro tenha frequência de varredura e nível de ferramenta próprios, para que um site frágil não force o ritmo dos demais.

**Métricas de sucesso:**

| Métrica | Baseline atual | Target | Prazo |
|---|---|---|---|
| 🟡 Leiloeiros cadastrados e ativos | 0 | ≥ 5 | 3 meses |
| 🟡 Tempo para cadastrar uma busca nova em leiloeiro já suportado, com os filtros já em mãos | Não existe | < 5 minutos | MVP |
| 🟡 Credenciais encontradas em arquivo versionado | Não existe | 0 | MVP |
| 🟡 Execuções abortadas por credencial ausente depois do fetch iniciado | Não existe | 0 (validação sempre precede a rede) | MVP |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: **Descobrir sozinho os filtros de busca.** Os pares chave-valor são obtidos pelo Rafael, ou pelo `onboarding-leiloeiro-assistido`, observando o formulário de busca do site uma única vez. A descoberta assistida é responsabilidade do componente de onboarding.
- 🟢 NG-05: **Saber como os filtros viram requisição.** O registro trata chaves e valores como opacos: não sabe se o leiloeiro espera POST ou GET, qual o endpoint, nem o que significa `procedencia: 4`. Essa tradução é do adaptador do leiloeiro no `coletor-lotes`.
- 🟡 NG-02: **Executar o login.** Este componente apenas declara que um leiloeiro exige autenticação e aponta onde a credencial vive. Quem abre sessão é o `coletor-lotes`.
- 🟡 NG-03: **Interpretar o conteúdo das páginas.** O registro não sabe o que é um lote. Extração é responsabilidade do `parser-lotes`.
- 🟡 NG-04: **Cadastro pelo Telegram ou por interface web.** A edição é feita no arquivo YAML, em editor de texto.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 Rafael — cadastra os leiloeiros e declara os filtros de cada busca, observados no formulário do site.
**Usuário secundário:** 🟡 Agente de IA gestor, que edita o campo `nivel_coleta` de um leiloeiro ao propor a migração de script puro para Apify, e o campo `cron` ao sugerir mudança de frequência.

**Jornada atual (sem a feature):**
1. 🟡 Rafael abre cada site de leiloeiro no navegador, um a um.
2. 🟡 Reaplica os filtros manualmente em cada visita.
3. 🟡 Não tem registro de qual site exigiu login nem de qual exigiu qual conta.

**Jornada futura (com a feature):**
1. 🟡 Rafael aplica os filtros uma única vez no site e anota os pares chave-valor que o formulário envia.
2. 🟡 Declara esses pares em um bloco de busca no `config/leiloeiros.yaml`, junto da estratégia de acesso do leiloeiro.
3. 🟡 Na próxima execução agendada, aquele leiloeiro entra na varredura.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| 🟡 RF-01 | O sistema deve carregar o registro de leiloeiros de `config/leiloeiros.yaml` no início de cada execução. | Must | Um YAML com 5 leiloeiros válidos produz 5 objetos `Leiloeiro` com todos os campos acessíveis. |
| 🟢 RF-02 | O sistema deve exigir que cada leiloeiro tenha `base_url` absoluta em `https` e ao menos uma busca cadastrada, cada busca com um mapa `filtros` não vazio cujos valores sejam escalares (texto ou número) ou listas não vazias de escalares. | Must | Uma busca com `marca: NISSAN`, `procedencia: 4` e `monta: 1` carrega com os três filtros acessíveis. Um leiloeiro sem buscas, uma busca sem filtros, um filtro com valor aninhado ou uma `base_url` iniciada em `http://` são rejeitados com erro citando o nome do leiloeiro e, quando houver, a descrição da busca. |
| 🟡 RF-03 | O sistema deve aceitar `estrategia_acesso` com valor `publico` ou `logado`, e exigir o campo `credencial_env` quando o valor for `logado`. | Must | Um leiloeiro `logado` sem `credencial_env` é rejeitado; um leiloeiro `publico` sem `credencial_env` carrega sem erro. |
| 🟡 RF-04 | O sistema deve armazenar no YAML apenas o **nome** da variável de ambiente que guarda a credencial, nunca a credencial em si. | Must | Uma busca por padrões de senha no YAML de exemplo não retorna nenhuma ocorrência; o campo contém somente um identificador como `FREITAS_LOGIN`. |
| 🟡 RF-05 | O sistema deve verificar, antes de qualquer requisição de rede, que toda variável de ambiente referenciada por um leiloeiro ativo e logado existe e não está vazia. | Must | Com `FREITAS_LOGIN` ausente do ambiente, a execução aborta citando o nome da variável, sem ter feito nenhum fetch. |
| 🟡 RF-06 | O sistema deve aceitar `nivel_coleta` com valor `script`, `apify` ou `apify_residencial`, assumindo `script` quando o campo for omitido. | Must | Um leiloeiro sem `nivel_coleta` carrega com o valor `script`; um leiloeiro com valor fora do conjunto é rejeitado listando os três valores aceitos. |
| 🟡 RF-07 | O sistema deve aceitar uma expressão de frequência própria por leiloeiro, assumindo três execuções semanais quando o campo for omitido. | Must | Um leiloeiro sem o campo de frequência recebe o padrão de segunda, quarta e sexta; um leiloeiro com expressão inválida é rejeitado citando a expressão recebida. |
| 🟡 RF-08 | O sistema deve ignorar na varredura todo leiloeiro com `ativo: false`, preservando sua definição no arquivo. | Must | Com 5 leiloeiros, um inativo, a varredura processa 4 e o quinto permanece íntegro no YAML. |
| 🟡 RF-09 | O sistema deve atribuir a cada busca um identificador estável, derivado do leiloeiro e da forma canônica dos filtros, usado pelo `parser-lotes` para escolher o parser correto e pelo `agendador-observabilidade` para atribuir falhas. | Should | Dois carregamentos do mesmo arquivo produzem o mesmo identificador para a mesma busca, e reordenar as chaves de `filtros` no YAML não altera o identificador. |
| 🟢 RF-10 | O sistema deve rejeitar o leiloeiro ativo para o qual não exista adaptador de coleta registrado no `coletor-lotes` **ou** parser registrado no `parser-lotes`. | Must | Um leiloeiro ativo sem adaptador, ou com adaptador e sem parser, aborta a execução antes de qualquer fetch, citando o nome, o que falta e listando os registrados. |

### 6.1.1 Diretriz de desenho de buscas: busca ampla

🟢 Os filtros de uma busca devem restringir apenas atributos que os veículos-alvo **não** expressam, e que o card do lote muitas vezes nem exibe: procedência, estado de conservação (monta), categoria de veículo. Marca, modelo, ano, preço e quilometragem ficam **fora** da busca e são aplicados pelo `motor-filtros` contra os veículos-alvo.

Motivo: os veículos-alvo mudam com frequência e são editados só em `config/veiculos-alvo.yaml`. Uma busca que filtra por marca obrigaria a editar também este arquivo a cada alvo de marca nova, em cada leiloeiro, e o esquecimento resultaria em lote perdido sem nenhum aviso, a falha mais cara do sistema.

Exceção aceitável: quando a busca ampla de um leiloeiro exceder o teto de páginas do `coletor-lotes` (50) ou o limite de duração da execução, a busca pode ser fatiada por um atributo do site (por exemplo, categoria ou estado), mas nunca por marca ou modelo. Medida no Vip em 2026-10-03: a busca ampla `procedencia: 4, monta: 1` trouxe 201 lotes em 17 páginas, cerca de 2 minutos.

O `onboarding-leiloeiro-assistido` aplica esta diretriz ao propor o bloco YAML de um leiloeiro novo (RF-11 daquela spec).

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O agendador dispara uma execução de varredura.
2. 🟡 O componente lê `config/leiloeiros.yaml` do disco.
3. 🟡 O componente valida cada leiloeiro contra as regras de RF-02, RF-03, RF-06, RF-07 e RF-10.
4. 🟡 O componente descarta os leiloeiros com `ativo: false`.
5. 🟡 Para cada leiloeiro ativo com `estrategia_acesso: logado`, o componente confere que a variável de ambiente declarada existe e está preenchida.
6. 🟡 O componente calcula o identificador estável de cada busca.
7. 🟡 Resultado: uma lista de objetos `Leiloeiro`, cada um com suas buscas validadas, é entregue ao `coletor-lotes`.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Escalonamento de ferramenta após quebras:**
1. 🟡 O agente de IA gestor observa no histórico que um leiloeiro vem falhando de forma recorrente.
2. 🟡 O agente propõe ao Rafael alterar `nivel_coleta` de `script` para `apify` naquele leiloeiro.
3. 🟡 Com o aval do Rafael, o campo é alterado no YAML e a execução seguinte já usa o novo nível, sem afetar os demais leiloeiros.

**Fluxo Alternativo B — Leiloeiro com várias buscas:**
1. 🟡 Rafael cadastra, para o mesmo leiloeiro, uma busca com o filtro de procedência de financiamento e outra com o de seguradora.
2. 🟡 Ambas herdam a estratégia de acesso e o nível de coleta do leiloeiro.
3. 🟡 Cada uma é coletada de forma independente, e a falha de uma não impede a coleta da outra.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|---|---|---|---|
| 🟡 RNF-01 | Tempo de carregamento e validação | < 100 ms para 20 leiloeiros | Operação local; a checagem de variáveis de ambiente não toca a rede. |
| 🟡 RNF-02 | Segurança de credenciais | Zero segredos em arquivo versionado | O `.env` fica listado no `.gitignore`. |
| 🟡 RNF-03 | Isolamento entre leiloeiros | A rejeição de um leiloeiro inválido aborta a execução inteira | Config inválida é erro do operador e deve ser corrigida, não contornada silenciosamente. |
| 🟡 RNF-04 | Codificação | UTF-8 sem BOM | Nomes de leiloeiros contêm acentuação. |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Arquivos `config/leiloeiros.yaml` e `.env`; consumidor direto é o `coletor-lotes`; consumidores indiretos são o `parser-lotes` (escolha do parser por busca) e o `agendador-observabilidade` (frequência por leiloeiro).

**Comportamento esperado:**
🟡 A interface é o arquivo YAML. Exemplo válido:

```yaml
# Leiloeiros monitorados.
# A senha nunca entra aqui: o campo credencial_env aponta para uma variável no .env
leiloeiros:
  - nome: Vip Leilões
    base_url: https://www.vipleiloes.com.br
    ativo: true
    estrategia_acesso: publico
    nivel_coleta: script
    frequencia: seg-qua-sex-08h
    buscas:
      - descricao: Recuperados de financiamento, conservados, qualquer marca
        filtros:
          procedencia: 4      # Recuperado de Financiamento
          monta: 1            # Conservado
          # sem marca: o recorte de marca e modelo é feito pelos veículos-alvo (seção 6.1.1)

  - nome: Copart
    base_url: https://www.copart.com.br
    ativo: true
    estrategia_acesso: logado
    credencial_env: COPART_LOGIN
    nivel_coleta: apify
    frequencia: seg-qua-sex-08h
    buscas:
      - descricao: Sedãs recuperados de seguradora
        filtros:
          tipo: seguradora
          carroceria: [sedan, hatch]   # lista = múltipla escolha no formulário
```

**Estados da UI (saída em log):**
- 🟡 Estado vazio: `Nenhum leiloeiro ativo cadastrado. Nada a varrer nesta execução.`
- 🟡 Estado de carregamento: `Carregando leiloeiros de config/leiloeiros.yaml...`
- 🟡 Estado de erro: `Leiloeiro 'Copart' declara estrategia_acesso: logado, e a variável COPART_LOGIN não está definida no ambiente. Execução abortada.`
- 🟡 Estado de sucesso: `4 leiloeiros ativos, 7 buscas cadastradas (1 leiloeiro inativo ignorado).`

---

## 9. Modelo de Dados

**Entidades novas ou modificadas:**

```
Leiloeiro {
  id: string                // derivado do nome, estável entre execuções
  nome: string              // obrigatório, não vazio
  base_url: string          // obrigatório, https
  ativo: bool               // padrão true quando omitido
  estrategia_acesso: enum   // publico | logado
  credencial_env: string?   // obrigatório quando estrategia_acesso = logado
  nivel_coleta: enum        // script | apify | apify_residencial, padrão script
  frequencia: string        // expressão de agendamento, padrão três vezes por semana
  buscas: Busca[]           // >= 1 item
}

Busca {
  id: string                // derivado de leiloeiro.id + forma canônica dos filtros (chaves ordenadas), estável
  descricao: string         // texto livre, para o Rafael se localizar
  filtros: map<string, Escalar | Escalar[]>   // >= 1 par; chaves e valores opacos ao registro
}

Escalar = string | int | float   // listas não podem ser vazias nem conter mapas
```

**Migrações necessárias:** 🟡 Não. O componente apenas lê arquivos. O identificador da busca é derivado, não persistido em banco por este componente.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|---|---|---|
| 🟡 Arquivo `config/leiloeiros.yaml` | Obrigatória | Execução abortada; arquivo de exemplo comentado é criado para orientar o cadastro. |
| 🟡 Arquivo `.env` com as credenciais referenciadas | Obrigatória quando há leiloeiro logado ativo | Execução abortada citando a variável faltante, antes de qualquer requisição. |
| 🟡 Biblioteca de parsing YAML | Obrigatória | Falha de import encerra o processo. |
| 🟡 Sites dos leiloeiros | Obrigatória em tempo de coleta, não em tempo de cadastro | Este componente valida apenas o formato da `base_url` e a forma dos filtros, e não se o site os aceita. A checagem de resposta é do `coletor-lotes`. |
| 🟢 Registro de adaptadores do `coletor-lotes` | Obrigatória | Consultado apenas para listar os nomes disponíveis (RF-10); sem adaptador, o leiloeiro ativo é rejeitado. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---|---|---|
| 🟡 EC-01: Arquivo de leiloeiros ausente | Primeira execução | Cria arquivo de exemplo comentado e aborta com mensagem orientando o cadastro. |
| 🟢 EC-02: Busca sem filtros, com filtro de valor aninhado ou lista vazia, ou `base_url` relativa ou em `http` | Bloco de busca incompleto, ou URL colada pela metade | Rejeita citando o leiloeiro, a descrição da busca e o campo ou valor recebido. |
| 🟡 EC-03: Leiloeiro `logado` com variável de ambiente inexistente ou vazia | `.env` não carregado, ou nome digitado errado | Aborta antes do primeiro fetch, citando o nome exato da variável esperada (RF-05). |
| 🟡 EC-04: Credencial escrita direto no YAML | Rafael cola a senha no campo em vez do nome da variável | O carregamento é rejeitado com aviso de segurança, orientando a mover o valor para o `.env`. |
| 🟡 EC-05: Leiloeiro declarado sem nenhuma busca | Bloco criado e esquecido pela metade | Rejeita citando o nome do leiloeiro (RF-02). |
| 🟡 EC-06: Duas buscas com os mesmos filtros, em qualquer ordem de chaves | Duplicação por copiar e colar | Emite aviso, mantém a primeira ocorrência e prossegue. |
| 🟢 EC-11: Leiloeiro ativo sem adaptador de coleta | Leiloeiro novo cadastrado antes de o adaptador ser implementado | Rejeita citando o nome e listando os adaptadores disponíveis (RF-10). Com `ativo: false`, carrega sem erro, permitindo cadastrar antes de implementar. |
| 🟡 EC-07: Expressão de frequência inválida | Erro de digitação no campo | Rejeita citando a expressão recebida e o formato esperado. |
| 🟡 EC-08: `nivel_coleta` fora do conjunto aceito | Rafael escreve `apify-residencial` com hífen | Rejeita listando os três valores válidos. |
| 🟡 EC-09: Arquivo inacessível ou leitura travada | Arquivo em lock, ou pasta de nuvem sincronizando | A leitura tem timeout de 5 segundos. Estourado o limite, a falha é reportada com o caminho absoluto e a execução aborta, sem retry silencioso. |
| 🟡 EC-10: Todos os leiloeiros inativos | Rafael pausou o sistema temporariamente | Aviso explícito no log e término com sucesso, sem varrer nem notificar. |

---

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 Nenhuma para acessar o registro em si. Ferramenta pessoal de usuário único.
- **Autorização:** 🟡 Nenhuma. Quem acessa o sistema de arquivos acessa o cadastro.
- **Dados sensíveis:** 🟡 Este é o componente mais sensível da configuração. As credenciais dos leiloeiros são de contas reais do Rafael. A regra é absoluta: o YAML guarda apenas o **nome** da variável de ambiente (RF-04), e o valor vive no `.env`, que é listado no `.gitignore`. A violação dessa regra é tratada como erro de carregamento, e não como aviso (EC-04).
- **Auditoria:** 🟡 O log registra quais leiloeiros estavam ativos e quantas buscas cada um tinha. O log nunca imprime o valor de uma credencial, apenas o nome da variável.

---

## 13. Plano de Rollout

- **Estratégia:** 🟡 Incremental por leiloeiro. Começar com um único leiloeiro público e de estrutura simples, validar o ciclo completo até a notificação, e só então cadastrar os demais. Leiloeiros que exigem login entram por último, após o `onboarding-leiloeiro-assistido` ter mapeado o que o login acrescenta.
- **Como reverter (rollback):** 🟡 O YAML é versionado em git, e reverter um cadastro problemático é um `git checkout` do arquivo. Para desligar um leiloeiro sem reverter histórico, basta `ativo: false`. O `.env` não é versionado e é responsabilidade manual do Rafael.
- **Monitoramento pós-deploy:** 🟡 Nas primeiras execuções de cada leiloeiro novo, conferir se a busca retornou lotes, e se o nível de coleta `script` foi suficiente ou se já surgiram sinais de bloqueio.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---|---|---|---|
| 🟢 OQ-01 | ~~As URLs filtradas dos leiloeiros expiram?~~ **Resolvida em 2026-10-03:** a busca deixou de ser URL. Filtros declarados não expiram; o estado de sessão, como o cookie de canal do Vip, é obtido pelo `coletor-lotes` a cada execução. | — | Rafael | Fechada |
| 🟡 OQ-02 | Uma credencial pode servir a mais de um leiloeiro do mesmo grupo econômico? O modelo atual assume uma variável de ambiente por leiloeiro. | Baixo | Rafael | Pós-MVP |
| 🟡 OQ-03 | O acesso logado deve usar login e senha ou é viável reaproveitar um cookie de sessão exportado do navegador? A segunda opção evitaria lidar com 2FA. | Alto | Rafael | Antes de cadastrar o primeiro leiloeiro logado |
| 🟡 OQ-04 | Qual o formato exato da expressão de frequência: cron padrão de cinco campos ou um vocabulário simplificado? A decisão pertence ao `agendador-observabilidade` e é apenas consumida aqui. | Médio | Rafael | Antes de implementar o agendador |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---|---|---|
| 🟢 Busca ampla: filtros só sobre o que os alvos não expressam (seção 6.1.1) | Uma busca por marca de cada alvo; uma busca por alvo | Decidido em 2026-10-03. Configuração duplicada entre alvos e buscas cria falha silenciosa a cada alvo novo. O custo da busca ampla foi medido e cabe no limite de duração. |
| 🟡 Credencial por referência a variável de ambiente | Senha no YAML; cofre de segredos dedicado | Escolhido em 2026-09-21. Senha no YAML seria versionada em git, o que é inaceitável. Um cofre dedicado é complexidade desproporcional para ferramenta pessoal de usuário único. |
| 🟡 ~~URL filtrada cadastrada à mão~~ (substituída em 2026-10-03, ver linha seguinte) | Automação de navegador percorrendo os filtros | Decidido na ideação. Automação de cliques é frágil, lenta e quebra a cada mudança de layout. |
| 🟢 Busca como conjunto de filtros chave-valor, opacos ao registro, traduzidos por adaptador por leiloeiro | Manter URL; guardar o corpo HTTP bruto; aceitar URL ou filtros como formas alternativas | Decidido em 2026-09-27 e incorporado em 2026-10-03. O Vip envia filtros no corpo de um POST e o redirecionamento de cookie descarta a query string, então a URL não reproduz a busca. Guardar o corpo bruto acoplaria o YAML ao formato HTTP. Duas formas alternativas dobrariam a validação; um leiloeiro que filtra por query string é atendido pelo adaptador montando a URL a partir dos mesmos filtros. Mantém o espírito da ideação: a busca é definida uma vez, à mão, sem automação de cliques. |
| 🟡 `nivel_coleta` e frequência declarados por leiloeiro | Configuração global única | Vem direto da estratégia de escalonamento progressivo da ideação: um site que exige Apify não deve forçar todos os outros a pagar esse custo, e um site frágil não deve ditar o ritmo dos demais. |
| 🟡 Config inválida aborta a execução inteira | Ignorar o leiloeiro inválido e seguir com os demais | Ignorar em silêncio criaria a falha mais cara do sistema: o Rafael acreditando que monitora 5 leiloeiros enquanto monitora 4. O PRD exige explicitamente que o sistema não falhe em silêncio. |

---

## Apêndice

### Referências
- `_reversa_sdd/prd.md` — seção 4, escopo "Cadastro de leiloeiros-alvo" e "Mapeamento por URL"
- `_reversa_sdd/ideation.md` — seções "Estratégia de mapeamento por URL" e "Modo público vs. logado"
- `_reversa_sdd/personas.md` — jornada principal, passos 2 e 4

### Histórico de Revisões
| Versão | Data | Autor | Mudanças |
|---|---|---|---|
| 1.0 | 2026-09-21 | reversa-spec-sdd | Criação inicial a partir do PRD |
| 1.1 | 2026-10-03 | reversa-forward | Emenda: busca passa de URL absoluta para mapa `filtros` (RF-02, RF-09, modelo de dados, exemplo, EC-02, EC-06); `https` passa a valer para `base_url`; novos NG-05, RF-10 e EC-11 (adaptador por leiloeiro); OQ-01 fechada. Origem: esclarecimento de 2026-09-27 em `_reversa_forward/001-mvp-varredura-ponta-a-ponta/requirements.md#9` |
| 1.2 | 2026-10-03 | reversa-forward | Diretriz de busca ampla (seção 6.1.1) e exemplo do Vip sem filtro de marca. Origem: decisão D-29 de `_reversa_forward/001-mvp-varredura-ponta-a-ponta/roadmap.md` |
| 1.3 | 2026-10-03 | reversa-forward | RF-10 passa a exigir também parser registrado. Origem: audit da feature 001 (A003) |
