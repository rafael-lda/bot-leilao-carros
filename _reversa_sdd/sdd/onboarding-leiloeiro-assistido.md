# Spec: Onboarding de Leiloeiro Assistido por Agente

> Selo 🟡 PLANEJADO em todos os itens. Nenhum fato aqui foi extraído de código existente.

**Versão:** 1.1
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-09-21 (emenda em 2026-10-03)
**Reviewers:** Rafael

---

## 1. Resumo

🟡 Fluxo sob demanda, executado uma vez por leiloeiro novo, em que um agente de IA navega pelo site para mapear quais dados estão disponíveis em acesso público e quais exigem login. O resultado é um relatório de campos disponíveis, do modo como o site recebe buscas e das armadilhas técnicas encontradas, e um bloco YAML pronto para ser colado em `config/leiloeiros.yaml`. O login, quando necessário, é feito pelo Rafael, com o agente pausando e aguardando.

---

## 2. Contexto e Motivação

**Problema:**
🟡 Cada leiloeiro expõe um conjunto diferente de dados sem login. A ideação registra que, na maioria dos grandes leiloeiros, fotos e vídeos são públicos, e que existem exceções em que fotos de alta resolução, laudos cautelares e número de chassi exigem autenticação. Descobrir isso site a site, na mão, é trabalho de investigação que se repete a cada leiloeiro novo e cujo resultado se perde se não for registrado.

**Evidências:**
🟡 O `ideation.md` traz a decisão explícita de "verificar leiloeiro a leiloeiro o que é público vs. restrito, para não perder dados/oportunidades". A jornada em `personas.md` inclui o passo "agente de IA navegar pelos sites (público e logado) para mapear dados disponíveis, com human-in-the-loop para login".

**Por que agora:**
🟡 A decisão de logar ou não em um leiloeiro determina o custo e o risco de toda a coleta daquele site. Tomar essa decisão com base em evidência coletada, e não em suposição, evita tanto expor credenciais sem necessidade quanto operar cego sobre dados que existiam e estavam a um login de distância.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Produzir, para cada leiloeiro novo, um registro escrito de quais campos são obtidos sem login e quais exigem autenticação.
- [ ] 🟡 G-02: Entregar um bloco YAML válido, pronto para colar no cadastro, reduzindo o onboarding a uma operação de copiar e colar.
- [ ] 🟡 G-03: Manter o login sob controle humano, sem que o agente manipule ou armazene a senha do Rafael.

**Métricas de sucesso:**

| Métrica | Baseline atual | Target | Prazo |
|---|---|---|---|
| 🟡 Tempo de onboarding de um leiloeiro novo | Investigação manual sem registro | < 30 minutos, incluindo a pausa para login | MVP |
| 🟡 Leiloeiros com mapa público/restrito documentado | 0 | 5 de 5 cadastrados | 3 meses |
| 🟡 Credenciais gravadas pelo agente em disco | Não existe | 0 | MVP |
| 🟡 Blocos YAML gerados que carregam sem erro no `cadastro-leiloeiros` | Não existe | 100% | MVP |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: **Execução automática e recorrente.** Este fluxo roda sob demanda, disparado pelo Rafael ao adicionar um leiloeiro. Não entra na varredura agendada.
- 🟡 NG-02: **Contornar proteção anti-bot.** Diante de CAPTCHA ou bloqueio, o fluxo registra o obstáculo e encerra, deixando a decisão de escalar para Apify com o Rafael. Não haverá resolução automatizada de CAPTCHA.
- 🟡 NG-03: **Criar conta no leiloeiro.** As contas já existem e pertencem ao Rafael. O fluxo apenas verifica o que a conta dele enxerga a mais.
- 🟡 NG-04: **Escrever direto no `config/leiloeiros.yaml`.** O bloco gerado é apresentado para o Rafael revisar e colar. A escrita no cadastro permanece um ato dele.
- 🟡 NG-05: **Gerar o parser do leiloeiro.** O mapa de campos alimenta a construção do parser, e a implementação em si pertence ao `parser-lotes`.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 Rafael — conduz o onboarding, faz o login quando solicitado e decide se o leiloeiro entra como público ou logado.
**Usuário secundário:** 🟡 Agente de IA gestor, que executa a navegação, compara os dois modos de acesso e redige o relatório.

**Jornada atual (sem a feature):**
1. 🟡 Rafael abre o site de um leiloeiro novo e navega à toa tentando entender o que consegue ver.
2. 🟡 Faz login e tenta perceber, de memória, o que mudou na tela.
3. 🟡 A conclusão não fica registrada em lugar nenhum e se perde até o próximo leiloeiro.

**Jornada futura (com a feature):**
1. 🟡 Rafael dispara o onboarding informando a URL base do leiloeiro.
2. 🟡 O agente navega em modo público e lista os campos que encontrou.
3. 🟡 O agente pausa e pede que o Rafael faça o login na sessão do navegador.
4. 🟡 O agente repete a navegação autenticado e apresenta a diferença entre os dois modos.
5. 🟢 O agente verifica a lista de armadilhas conhecidas (Apêndice) e propõe uma busca ampla, declarada como filtros.
6. 🟡 Rafael cola no cadastro o bloco YAML gerado.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| 🟡 RF-01 | O sistema deve oferecer um comando dedicado que inicie o onboarding recebendo o nome e a URL base de um leiloeiro. | Must | Executar o comando com a URL da Vip Leilões inicia a sessão de onboarding e gera um relatório ao final. |
| 🟡 RF-02 | O sistema deve navegar em modo público por uma página de listagem e por ao menos uma página de lote, registrando quais campos de interesse estão visíveis. | Must | O relatório lista, para cada campo do conjunto de interesse, o veredito `disponivel` ou `ausente` no modo público. |
| 🟢 RF-03 | O sistema deve verificar a presença dos campos: marca, modelo, ano (indicando se traz fabricação e modelo), lance inicial, lance corrente, quilometragem, situação do lote, link do lote, descrição, fotos, laudo e chassi, registrando para cada um se aparece **na página de listagem** ou só na página do lote. | Must | Os doze campos aparecem no relatório com veredito individual e local, sem omissão. *(Emendado em 2026-10-03: lance corrente, quilometragem e situação entraram porque o filtro de preço, o critério de km e o descarte de retirados dependem deles, e campo que só existe na página do lote custa uma requisição por lote.)* |
| 🟡 RF-04 | O sistema deve pausar e solicitar intervenção humana para o login, sem solicitar, ler ou gravar a senha do Rafael. | Must | Durante a pausa, nenhuma senha é pedida no chat nem gravada em disco; o agente apenas aguarda confirmação de que a sessão está autenticada. |
| 🟡 RF-05 | O sistema deve repetir a navegação de RF-02 em modo autenticado e apresentar a diferença entre os dois modos. | Must | O relatório contém uma tabela comparativa com uma coluna para modo público e outra para modo logado. |
| 🟢 RF-06 | O sistema deve validar que a busca proposta, declarada como conjunto de filtros chave-valor (`cadastro-leiloeiros` v1.1), retorna ao menos um lote e que o servidor de fato aplica cada filtro, comparando o total de resultados com e sem ele, antes de incluí-la no bloco YAML gerado. | Must | Uma busca que retorna zero lotes, ou um filtro que não altera o total de resultados, gera aviso e pedido de revisão, e não entra no bloco final. *(Emendado em 2026-10-03: a versão 1.0 validava uma URL filtrada; no Vip, os filtros vão no corpo de um POST e o redirecionamento descarta a query string.)* |
| 🟡 RF-07 | O sistema deve gerar um bloco YAML compatível com o esquema do `cadastro-leiloeiros`, preenchendo `estrategia_acesso` conforme a conclusão do mapeamento. | Must | O bloco gerado, colado em `config/leiloeiros.yaml`, carrega sem erro de validação. |
| 🟡 RF-08 | O sistema deve persistir o relatório de mapeamento em arquivo, nomeado pelo identificador do leiloeiro. | Must | Após o onboarding, existe um arquivo de relatório recuperável para consulta futura. |
| 🟡 RF-09 | O sistema deve recomendar um `nivel_coleta` inicial com base nos obstáculos observados durante a navegação. | Should | Um site que respondeu sem bloqueio recebe a recomendação `script`; um site que apresentou bloqueio recebe a recomendação `apify`, com a justificativa registrada. |
| 🟢 RF-10 | O sistema deve percorrer a lista de armadilhas conhecidas do Apêndice e registrar no relatório o veredito de cada uma para o leiloeiro mapeado: como o site recebe a busca (método, endpoint, onde vão os filtros), exigência de cookie ou sessão prévia, paginação, unicidade do número do lote entre eventos, grafias de marca fora da tabela de sinônimos do `parser-lotes`, presença de lotes retirados na listagem e proteção anti-bot. | Must | O relatório tem uma seção de armadilhas com veredito para cada item da lista, e cada grafia de marca nova encontrada é listada como proposta de acréscimo à tabela de sinônimos. |
| 🟢 RF-11 | O sistema deve propor a busca seguindo a diretriz de busca ampla do `cadastro-leiloeiros` (seção 6.1.1), informando o total de resultados e o número de páginas medidos. | Must | O bloco YAML proposto não filtra por marca nem modelo, e o relatório traz o total e as páginas da busca, ou a justificativa de fatiamento quando a busca ampla exceder o teto de páginas. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 Rafael dispara o comando de onboarding informando nome e URL base do leiloeiro.
2. 🟡 O agente acessa a página pública de listagem e coleta a estrutura encontrada.
3. 🟡 O agente abre uma página de lote individual e verifica os doze campos de interesse.
4. 🟡 O agente apresenta o resultado parcial do modo público e pausa, pedindo o login.
5. 🟡 Rafael autentica a sessão e confirma ao agente que pode prosseguir.
6. 🟡 O agente repete a navegação autenticado e compara os dois conjuntos de campos.
7. 🟢 O agente identifica como o site recebe a busca, propõe os filtros da busca ampla, confere que o servidor aplica cada um e que a busca retorna lotes (RF-06, RF-11), e percorre a lista de armadilhas (RF-10).
8. 🟡 O agente grava o relatório e apresenta o bloco YAML pronto.
9. 🟡 Resultado: Rafael cola o bloco no cadastro e o leiloeiro entra na próxima varredura.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Leiloeiro totalmente público:**
1. 🟡 O mapeamento em modo público encontra os doze campos de interesse.
2. 🟡 O agente informa que o login não acrescentaria dados e oferece pular a etapa autenticada.
3. 🟡 Com o aval do Rafael, o bloco é gerado com `estrategia_acesso: publico` e sem `credencial_env`.

**Fluxo Alternativo B — Rafael recusa o login:**
1. 🟡 Na pausa de RF-04, Rafael opta por não autenticar naquele momento.
2. 🟡 O agente encerra registrando o mapeamento parcial, marcando o modo logado como não verificado.
3. 🟡 O bloco YAML é gerado como `publico`, e o relatório anota que a verificação autenticada ficou pendente.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|---|---|---|---|
| 🟡 RNF-01 | Duração total da sessão de onboarding | < 30 minutos por leiloeiro, incluindo a pausa humana | Fluxo raro, tolerante a lentidão. |
| 🟡 RNF-02 | Volume de requisições ao site | ≤ 10 páginas por sessão de onboarding | Exploração discreta reduz o risco de o site marcar o acesso como abusivo antes mesmo do cadastro. |
| 🟡 RNF-03 | Segurança | Zero senhas manipuladas, pedidas ou gravadas pelo agente | O login ocorre fora do alcance do agente. |
| 🟡 RNF-04 | Reprodutibilidade | O relatório registra data e URLs visitadas | Permite refazer a verificação depois que o site mudar de layout. |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Produz insumo para `cadastro-leiloeiros` (o bloco YAML) e para `parser-lotes` (o mapa de campos disponíveis). Não é chamado pela varredura agendada.

**Comportamento esperado:**
🟡 A interface é uma conversa no chat com o agente, intercalada com a navegação. O relatório final tem a forma:

```
Mapeamento: Copart
Data: 2026-09-21
Páginas visitadas: 6

Campo              Público      Logado
modelo             disponivel   disponivel
ano                disponivel   disponivel
preco              disponivel   disponivel
link               disponivel   disponivel
descricao          parcial      disponivel
fotos              baixa_res    alta_res
laudo              ausente      disponivel
chassi             ausente      disponivel

Conclusão: o login acrescenta laudo, chassi e fotos em alta resolução.
Recomendação: estrategia_acesso = logado, nivel_coleta = script.
```

**Estados da UI:**
- 🟡 Estado vazio: `Nenhum campo de interesse encontrado na página. A URL informada aponta para uma listagem de lotes?`
- 🟡 Estado de carregamento: `Navegando em modo público, página 2 de 6...`
- 🟡 Estado de pausa: `Faça o login em COPART na janela aberta e responda PRONTO quando a sessão estiver autenticada.`
- 🟡 Estado de erro: `O site respondeu com bloqueio na terceira requisição. Mapeamento interrompido. Sugiro nivel_coleta = apify.`
- 🟡 Estado de sucesso: `Mapeamento concluído. Relatório gravado. Bloco YAML pronto para colar.`

---

## 9. Modelo de Dados

**Entidades novas ou modificadas:**

```
RelatorioMapeamento {
  leiloeiro_id: string        // identificador estável do leiloeiro
  data: datetime              // quando o mapeamento foi feito
  urls_visitadas: string[]    // rastro para reprodução futura
  campos: CampoMapeado[]      // um por campo de interesse
  modo_logado_verificado: bool // false quando o Rafael pulou o login
  obstaculos: string[]        // bloqueios, CAPTCHA ou lentidão observados
  recomendacao_acesso: enum   // publico | logado
  recomendacao_nivel: enum    // script | apify | apify_residencial
  armadilhas: Armadilha[]     // veredito por item da lista do Apêndice (RF-10)
  busca_proposta: map         // filtros da busca ampla (RF-11)
  total_resultados: int       // medido com a busca proposta
  paginas: int
}

Armadilha {
  item: string                // ex.: cookie_previo, numero_lote_por_evento, sinonimos_marca
  veredito: enum              // presente | ausente | nao_verificado
  evidencia: string           // o que foi observado, com a URL
}

CampoMapeado {
  nome: string                // um dos doze campos de interesse
  na_listagem: bool           // true se aparece no card da listagem, e não só na página do lote
  publico: enum               // disponivel | parcial | ausente
  logado: enum                // disponivel | parcial | ausente | nao_verificado
}
```

**Migrações necessárias:** 🟡 Não. O relatório é gravado como arquivo próprio, sem tabela em banco. O SQLite do projeto guarda lotes e execuções, e não mapeamentos de onboarding.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|---|---|---|
| 🟡 Site do leiloeiro sendo mapeado | Obrigatória | Sem o site no ar não há mapeamento; o fluxo encerra pedindo para tentar depois. |
| 🟡 Navegador controlável com sessão compartilhada com o Rafael | Obrigatória | Sem ele o login humano no meio do fluxo é inviável, e o mapeamento fica restrito ao modo público. |
| 🟡 Agente de IA com acesso de leitura à web | Obrigatória | É o executor do fluxo; sem ele o onboarding volta a ser manual. |
| 🟡 Esquema do `cadastro-leiloeiros` | Obrigatória | Define o formato do bloco YAML gerado; uma mudança de esquema exige atualizar o gerador. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---|---|---|
| 🟡 EC-01: Site fora do ar ou lento além do aceitável | Manutenção, instabilidade | Cada requisição tem timeout de 30 segundos. Após 2 tentativas de retry espaçadas, o fluxo encerra informando que o site não respondeu, sem gerar bloco YAML. |
| 🟡 EC-02: CAPTCHA apresentado durante a navegação pública | Proteção anti-bot do site | Registra o obstáculo, encerra o mapeamento automatizado e recomenda `nivel_coleta: apify`, deixando a decisão com o Rafael (NG-02). |
| 🟡 EC-03: Login falha ou exige segundo fator | 2FA habilitado na conta | O agente permanece na pausa até o Rafael confirmar ou desistir. Desistindo, segue o Fluxo Alternativo B. |
| 🟢 EC-04: Busca proposta retorna zero lotes, ou um filtro não altera o total | Filtro restritivo demais, nome de campo errado, ou servidor ignorando o campo | Avisa qual filtro falhou na verificação, pede revisão e não inclui a busca no bloco (RF-06). |
| 🟢 EC-09: Redirecionamento em laço na primeira requisição | Site exige cookie de sessão emitido por um endpoint próprio, como o Vip | Registra a armadilha `cookie_previo`, refaz o acesso com sessão que preserva cookies e limite de 3 redirecionamentos, e documenta no relatório qual requisição emite o cookie. |
| 🟡 EC-05: Layout do site muda no meio da sessão | Deploy do leiloeiro durante o mapeamento | A falha de extração é registrada no relatório como campo `ausente` com nota de inconsistência, e o Rafael é avisado para refazer o mapeamento. |
| 🟡 EC-06: Sessão autenticada expira antes da segunda navegação | Timeout de sessão curto no leiloeiro | Detecta a perda de sessão, retorna à pausa de RF-04 e pede novo login, sem descartar o que já foi mapeado. |
| 🟡 EC-07: O site exige login já na página de listagem | Leiloeiro sem área pública | Registra que o modo público é inexistente, vai direto para a pausa de login e gera o bloco com `estrategia_acesso: logado`. |
| 🟡 EC-08: Rafael interrompe a sessão no meio | Desistência ou imprevisto | O relatório parcial é gravado com o que foi coletado, marcado como incompleto, sem gerar bloco YAML. |

---

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 O agente nunca autentica sozinho. A sessão é aberta pelo próprio Rafael, no navegador, durante a pausa de RF-04.
- **Autorização:** 🟡 O agente opera com a visibilidade da conta do Rafael, e não acessa área que a conta dele já não acessasse manualmente.
- **Dados sensíveis:** 🟡 O agente não pede, não lê e não grava senha (RF-04). O relatório registra quais campos existem, e não o conteúdo dos lotes. Número de chassi, quando detectado, entra no relatório apenas como veredito de disponibilidade, sem o valor real ser transcrito.
- **Auditoria:** 🟡 O relatório guarda data e lista de URLs visitadas, permitindo reconstruir depois o que foi acessado e quando.

---

## 13. Plano de Rollout

- **Estratégia:** 🟡 Gradual e manual, um leiloeiro por vez. Começar por um leiloeiro público e de estrutura simples para validar o fluxo, e só então aplicar a um leiloeiro que exija login.
- **Como reverter (rollback):** 🟡 O fluxo não altera estado do sistema: gera um relatório e um texto para o Rafael colar. Descartar um onboarding é apagar o relatório gerado. Como NG-04 impede a escrita direta no cadastro, nenhum leiloeiro entra em operação sem ato explícito do Rafael.
- **Monitoramento pós-deploy:** 🟡 Após cada onboarding, conferir na primeira varredura real se os campos que o relatório prometeu como disponíveis foram de fato extraídos pelo `parser-lotes`. Divergência indica mapeamento otimista demais.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---|---|---|---|
| 🟡 OQ-01 | Qual ferramenta de navegação o agente usa na pausa de login, de modo que a sessão autenticada pelo Rafael continue disponível para o agente na etapa seguinte? | Alto | Rafael | Antes do primeiro leiloeiro logado |
| 🟡 OQ-02 | O mapeamento deve ser refeito periodicamente para detectar mudanças de política do site, ou basta refazer quando o parser quebrar? | Médio | Rafael | Pós-MVP |
| 🟡 OQ-03 | Os termos de uso dos leiloeiros-alvo proíbem acesso automatizado de forma explícita? O PRD pede respeito aos termos na medida do possível, e essa verificação ainda não foi feita site a site. | Alto | Rafael | Antes de ampliar para 5 leiloeiros |
| 🟡 OQ-04 | Vale reaproveitar cookie de sessão exportado do navegador em vez de manter o fluxo de pausa a cada onboarding? | Médio | Rafael | Pós-MVP |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---|---|---|
| 🟡 Login por intervenção humana, com o agente pausando | Agente autenticando com credencial do `.env` | Decidido na ideação como human-in-the-loop. Mantém a senha fora do alcance do agente e contorna 2FA sem esforço de engenharia. O custo é uma pausa em um fluxo que roda uma vez por leiloeiro. |
| 🟡 Gerar bloco YAML para o Rafael colar, sem escrever no cadastro | Escrever direto em `config/leiloeiros.yaml` | Escrita direta tornaria o agente capaz de colocar um leiloeiro em operação sem revisão. A revisão humana custa segundos e evita cadastrar uma busca errada que só apareceria como ausência silenciosa de lotes. |
| 🟢 Lista de armadilhas conhecidas, acumulada a cada leiloeiro | Investigar cada site do zero | Decidido em 2026-10-03. As armadilhas do Vip (cookie prévio, filtros no corpo do POST, número de lote por evento, sinônimos de marca) só foram descobertas por tentativa e erro, uma delas com um laço de requisições. Uma lista que cresce a cada onboarding transforma o aprendizado de um site em verificação barata nos seguintes. |
| 🟡 Mapeamento comparativo público contra logado, em vez de assumir um dos dois | Assumir tudo público; assumir tudo logado | Vem direto da ideação, que registra que a maioria dos leiloeiros é pública com exceções relevantes. Assumir qualquer um dos extremos ou desperdiçaria dados ou exporia credenciais sem necessidade. |
| 🟡 Encerrar diante de CAPTCHA em vez de contornar | Resolver CAPTCHA automaticamente | Contornar proteção anti-bot conflita com o requisito de respeitar os termos de uso registrado no PRD. A saída prevista é escalar para Apify, que é a estratégia já decidida na ideação. |

---

## Apêndice

### Referências
- `_reversa_sdd/prd.md` — seção 4, escopo "Exploração de sites por agente de IA" e "Estratégia de acesso público vs. logado"
- `_reversa_sdd/ideation.md` — seção "Modo público vs. logado"
- `_reversa_sdd/personas.md` — jornada principal, passo 3

### Lista de armadilhas conhecidas

Cada item foi encontrado num leiloeiro real e vira verificação obrigatória nos seguintes (RF-10). Ao terminar um onboarding, acrescente aqui toda armadilha nova.

| Item | O que verificar | Por que importa | Primeiro visto |
|---|---|---|---|
| `filtros_no_corpo` | A busca vai na URL (GET) ou no corpo (POST)? Qual endpoint e quais nomes de campo? | Copiar a URL do navegador não reproduz uma busca feita por POST | Vip, 2026-09-27 |
| `cookie_previo` | Alguma página exige cookie emitido por outro endpoint antes? | Sem sessão com cookies, o site redireciona em laço | Vip, 2026-09-27 |
| `redirect_descarta_query` | O redirecionamento perde os parâmetros da URL? | A busca chega ao servidor sem os filtros, mais larga que o pretendido | Vip, 2026-09-27 |
| `filtro_ignorado` | O total de resultados muda ao aplicar cada filtro? | Campo com nome errado é ignorado pelo servidor sem erro | Vip, 2026-10-03 |
| `zero_resultados` | Como o site mostra uma busca sem resultados? Existe indicador de total? | Sem indicador, página vazia legítima e layout quebrado ficam indistinguíveis e geram alerta falso (`parser-lotes` EC-15) | Vip, 2026-10-03 (`0 resultados encontrados`) |
| `paginacao` | Quantos lotes por página, como pedir a página N, como saber que acabou? | Ler só a primeira página perde lotes em silêncio | Vip, 2026-09-27 |
| `numero_lote_por_evento` | O número do lote se repete entre eventos diferentes? | Se repetir, não serve de identificador canônico (`parser-lotes` RF-06) | Vip, 2026-10-03 |
| `sinonimos_marca` | O site usa mais de uma grafia para a mesma marca? Compare a lista de marcas do site com a tabela de sinônimos do `parser-lotes` | Alvo escrito por extenso perde os lotes da grafia abreviada (`parser-lotes` RF-12) | Vip, 2026-10-03 (`MMC`, `GM`) |
| `retirados_listados` | Lotes retirados do pregão continuam na listagem? Com qual texto ou classe? | Notificaria carro que não está mais à venda | Vip, 2026-09-27 |
| `lance_corrente_na_listagem` | O card traz o lance corrente, ou só o inicial? | Sem ele, o filtro de preço exige uma requisição por lote | Vip, 2026-09-27 (traz) |
| `procedencia_fora_do_card` | Procedência e monta aparecem no card, ou só como filtro? | Se só como filtro, precisam ir na busca (busca ampla por esses atributos) | Vip, 2026-09-27 |
| `anti_bot` | Há Cloudflare ou similar? Houve desafio? | Gatilho para escalar `nivel_coleta` | Vip, 2026-09-27 (presente, sem desafio) |

### Histórico de Revisões
| Versão | Data | Autor | Mudanças |
|---|---|---|---|
| 1.0 | 2026-09-21 | reversa-spec-sdd | Criação inicial a partir do PRD |
| 1.1 | 2026-10-03 | reversa-forward | Busca passa de URL para filtros (RF-06, EC-04); campos de interesse passam de 8 para 12, com local de exibição (RF-03); novos RF-10 (armadilhas), RF-11 (busca ampla), EC-09 e lista de armadilhas conhecidas no Apêndice. Origem: investigações do Vip de 2026-09-27 e 2026-10-03 |
