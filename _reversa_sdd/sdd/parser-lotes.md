# Spec: Parser de Lotes

> Selo 🟡 PLANEJADO em todos os itens. Nenhum fato aqui foi extraído de código existente.

**Versão:** 1.2
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-09-21 (emenda em 2026-10-03)
**Reviewers:** Rafael

---

## 1. Resumo

🟡 Componente que **traduz** o conteúdo bruto de cada leiloeiro para um formato único. Recebe do `coletor-lotes` o conteúdo de uma busca, aplica o parser específico daquele leiloeiro e devolve uma lista de lotes normalizados, com preço em número, ano em quatro dígitos e link absoluto. Detecta quando o parser deixou de funcionar e denuncia o fato em vez de devolver lista vazia em silêncio.

---

## 2. Contexto e Motivação

**Problema:**
🟡 Cada leiloeiro estrutura sua página de um jeito. Um escreve o preço como `R$ 45.000,00`, outro como `45000`. Um informa o ano como `2018`, outro como `2018/2019` separando fabricação de modelo. Um dá link absoluto, outro dá caminho relativo. Sem uma camada de tradução, o motor de filtros precisaria conhecer as particularidades dos cinco sites, e adicionar o sexto leiloeiro significaria mexer na lógica de filtro.

**Evidências:**
🟡 O `prd.md` classifica "mudança de layout dos sites quebrando parsers" como risco de probabilidade alta, e propõe como mitigação uma arquitetura modular por leiloeiro. O critério de aceite do PRD exige que, quando o parser quebrar, o sistema registre o erro e notifique, sem falhar em silêncio.

**Por que agora:**
🟡 É a camada que isola o resto do sistema da instabilidade dos sites. Sem ela, toda mudança de layout de qualquer leiloeiro se propagaria para dentro do motor de filtros e do notificador.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Produzir um objeto `Lote` de formato idêntico, qualquer que seja o leiloeiro de origem.
- [ ] 🟡 G-02: Detectar quebra de parser e sinalizá-la, em vez de devolver resultado vazio que se confunde com "nenhum lote novo".
- [ ] 🟡 G-03: Permitir adicionar o parser de um leiloeiro novo sem alterar o código dos parsers existentes.

**Métricas de sucesso:**

| Métrica | Baseline atual | Target | Prazo |
|---|---|---|---|
| 🟡 Quebras de parser detectadas contra quebras que passaram despercebidas | Não existe | 100% detectadas | 3 meses |
| 🟡 Lotes extraídos com todos os campos obrigatórios preenchidos | Não existe | ≥ 90% dos lotes de uma página | MVP |
| 🟡 Tempo de parsing por busca | Não existe | < 2 segundos para 100 lotes | MVP |
| 🟡 Esforço para adicionar parser de leiloeiro novo | Não existe | 1 arquivo novo, 0 arquivos alterados | MVP |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: **Fazer requisições de rede.** O parser recebe conteúdo já baixado. Buscar é responsabilidade do `coletor-lotes`.
- 🟡 NG-02: **Decidir se um lote interessa.** O parser extrai todos os lotes que encontrar, inclusive os que não casam com nenhum alvo. Filtrar pertence ao `motor-filtros`.
- 🟡 NG-03: **Corrigir sozinho um parser quebrado.** A detecção é automática; a correção é feita pelo agente de IA gestor em diálogo com o Rafael.
- 🟡 NG-04: **Extrair fotos, laudos e vídeos.** O MVP normaliza os campos que entram na notificação e no filtro. Anexos ficam para evolução futura, conforme o `ideation.md`.
- 🟡 NG-05: **Guardar histórico de conteúdo bruto para reprocessamento.** O conteúdo é descartado após o parsing, conforme decidido no `coletor-lotes`.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 Nenhum humano interage com este componente durante a operação normal.
**Usuário secundário:** 🟡 Agente de IA gestor, que escreve e conserta os parsers quando um site muda de layout, orientado pelos sinais de quebra que o componente emite e pelo relatório de campos do `onboarding-leiloeiro-assistido`.

**Jornada atual (sem a feature):**
1. 🟡 Rafael lê os dados de cada lote direto na tela do leiloeiro.
2. 🟡 Compara mentalmente preços escritos em formatos diferentes entre sites.
3. 🟡 Não consegue ordenar nem comparar lotes de leiloeiros distintos de forma sistemática.

**Jornada futura (com a feature):**
1. 🟡 O coletor entrega o conteúdo de cada busca.
2. 🟡 O parser de cada leiloeiro devolve lotes no mesmo formato.
3. 🟡 Rafael recebe no Telegram lotes de cinco sites diferentes apresentados de forma uniforme.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| 🟡 RF-01 | O sistema deve selecionar o parser a aplicar com base no identificador do leiloeiro dono da busca de origem. | Must | Conteúdo vindo de uma busca da Copart é processado pelo parser da Copart, verificável pelo registro de execução. |
| 🟡 RF-02 | O sistema deve extrair de cada lote os campos: número do lote, marca, modelo, ano, lance inicial, lance corrente, link, descrição e tipo de leilão. | Must | De uma página com 20 lotes, o componente devolve 20 objetos `Lote` com os nove campos presentes ou explicitamente nulos. |
| 🟡 RF-03 | O sistema deve normalizar cada valor monetário para número decimal, descartando símbolo de moeda e separadores de milhar. | Must | O texto `R$ 45.000,00` produz o valor numérico `45000.00`, tanto para o lance inicial quanto para o corrente. |
| 🟡 RF-04 | O sistema deve normalizar o ano para quatro dígitos, registrando ano de fabricação e ano de modelo em campos separados quando a origem trouxer ambos. | Must | O texto `2018/2019` produz ano de fabricação `2018` e ano de modelo `2019`; o texto `2018` preenche ambos com `2018`. |
| 🟡 RF-05 | O sistema deve converter links relativos em URL absoluta, usando a `base_url` do leiloeiro. | Must | O caminho `/lote/12345` em um leiloeiro de base `https://exemplo.com.br` produz `https://exemplo.com.br/lote/12345`. |
| 🟢 RF-06 | O sistema deve atribuir a cada lote um identificador canônico estável, derivado do identificador do leiloeiro e de um identificador **único em todo o leiloeiro**: o número do lote quando ele for global, ou o identificador do anúncio presente na URL quando o número do lote for reiniciado a cada evento, recorrendo ao hash da URL apenas quando nenhum dos dois existir. | Must | O mesmo lote extraído em duas execuções distintas recebe o mesmo identificador canônico, e dois lotes de eventos diferentes com o mesmo número exibido ("Lote: 21") recebem identificadores distintos. |
| 🟡 RF-07 | O sistema deve sinalizar quebra de parser quando o conteúdo recebido for não vazio e nenhum lote for extraído. | Must | Uma página válida processada por um parser desatualizado produz sinal de quebra, e não lista vazia silenciosa. |
| 🟡 RF-08 | O sistema deve sinalizar quebra de parser quando mais de 30% dos lotes extraídos de uma busca estiverem sem ao menos um campo obrigatório. | Must | Uma página em que 5 de 10 lotes vêm sem preço produz sinal de quebra para aquela busca. |
| 🟡 RF-09 | O sistema deve descartar individualmente o lote que não tiver link ou identificador canônico, registrando o descarte. | Must | Um lote sem link é descartado e o contador de descartes daquela busca é incrementado. |
| 🟡 RF-10 | O sistema deve isolar falhas por busca, de modo que a exceção em um parser não impeça o processamento das demais buscas. | Must | Com 5 buscas, uma delas lançando exceção no parser, as outras 4 são processadas normalmente. |
| 🟡 RF-11 | O sistema deve registrar, por busca, quantos lotes foram extraídos, quantos descartados e se houve sinal de quebra. | Must | O `agendador-observabilidade` monta o relatório de saúde dos parsers a partir desses números. |
| 🟢 RF-12 | O sistema deve traduzir a marca extraída para um **nome canônico**, usando uma tabela de sinônimos comum a todos os parsers (ex.: `mmc` → `mitsubishi`, `gm` → `chevrolet`, `vw` → `volkswagen`), que cada parser pode ampliar com as grafias próprias do seu leiloeiro. Marca fora da tabela passa como veio, com registro em log. | Must | Um card com marca `MMC` produz `marca = mitsubishi` e casa com um alvo de marca `Mitsubishi`; uma marca desconhecida aparece no log da execução. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O parser recebe do coletor o conteúdo bruto de uma busca, junto do identificador de origem.
2. 🟡 O componente seleciona o parser registrado para aquele leiloeiro.
3. 🟡 O parser localiza no conteúdo a lista de lotes.
4. 🟡 Para cada lote, o parser extrai os oito campos de RF-02.
5. 🟡 O componente normaliza preço, ano e link (RF-03, RF-04, RF-05).
6. 🟡 O componente calcula o identificador canônico de cada lote.
7. 🟡 O componente verifica as condições de quebra de RF-07 e RF-08.
8. 🟡 Resultado: uma lista de objetos `Lote` normalizados é entregue ao `motor-filtros`.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Layout do leiloeiro mudou:**
1. 🟡 O parser processa conteúdo não vazio e não encontra nenhum lote.
2. 🟡 O componente emite sinal de quebra para aquela busca (RF-07).
3. 🟡 O `agendador-observabilidade` transforma o sinal em alerta, e o Rafael é avisado de que aquele leiloeiro parou de ser lido.

**Fluxo Alternativo B — Lote com preço sob consulta:**
1. 🟡 O parser encontra o lote e o campo de preço traz texto em vez de valor.
2. 🟡 O preço é registrado como nulo, com o texto original preservado na descrição.
3. 🟡 O lote segue para o `motor-filtros`, que decide o que fazer com preço ausente.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|---|---|---|---|
| 🟡 RNF-01 | Tempo de parsing | < 2 segundos por busca com até 100 lotes | Operação local, sem rede. |
| 🟡 RNF-02 | Modularidade | Um parser por leiloeiro, em arquivo próprio, registrado por identificador | Atende à mitigação de risco do PRD e permite ao agente de IA consertar um parser sem risco aos demais. |
| 🟡 RNF-03 | Tolerância a variação | Campo ausente em um lote individual não derruba o parsing dos outros lotes da mesma página | Páginas de leilão são irregulares por natureza. |
| 🟡 RNF-04 | Codificação | Conteúdo decodificado conforme declarado pela origem, com UTF-8 como padrão | Modelos e descrições contêm acentuação. |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Consome `RespostaBruta` do `coletor-lotes`. Produz `Lote` para o `motor-filtros`. Emite sinais de quebra para o `agendador-observabilidade`. Consome o relatório de campos produzido pelo `onboarding-leiloeiro-assistido` como referência de construção.

**Comportamento esperado:**
🟡 Componente sem interface visual. A saída em log tem a forma:

```
parser | Vip Leilões | busca=vip-versa-financiamento | 18 lotes | 0 descartados | ok
parser | Copart      | busca=copart-sedan-seguradora | 31 lotes | 2 descartados | ok
parser | Freitas     | busca=freitas-corolla | 0 lotes de conteúdo com 148 KB | QUEBRA SUSPEITA
parser | resumo: 3 buscas, 49 lotes normalizados, 1 sinal de quebra
```

**Estados da UI (saída em log):**
- 🟡 Estado vazio: `Nenhum conteúdo recebido do coletor. Fase de parsing encerrada sem trabalho.`
- 🟡 Estado de carregamento: `Processando busca 2 de 6...`
- 🟡 Estado de erro: `Freitas / freitas-corolla: 0 lotes extraídos de conteúdo não vazio. Parser provavelmente desatualizado.`
- 🟡 Estado de sucesso: `49 lotes normalizados a partir de 3 buscas.`

---

## 9. Modelo de Dados

**Entidades novas ou modificadas:**

```
Lote {
  id_canonico: string       // leiloeiro_id + numero_lote, ou leiloeiro_id + hash da URL
  leiloeiro_id: string      // origem
  busca_id: string          // qual busca trouxe este lote
  numero_lote: string?      // identificação do lote no site de origem
  marca: string?            // normalizada em minúsculas, sem acento, para comparação
  modelo: string?           // normalizado em minúsculas, sem acento
  ano_fabricacao: int?      // quatro dígitos
  ano_modelo: int?          // quatro dígitos
  lance_inicial: decimal?   // valor de abertura do lote, nulo quando não divulgado
  lance_corrente: decimal?  // valor atual do pregão, nulo enquanto não houver lance
  link: string              // obrigatório, absoluto
  descricao: string?        // texto livre da origem
  tipo_leilao: string?      // mapeado para o conjunto fechado quando reconhecível
  coletado_em: datetime     // instante da coleta que originou este lote
}

ResultadoParsing {
  busca_id: string
  lotes: Lote[]
  descartados: int          // lotes sem link ou sem identificador
  quebra_suspeita: bool     // resultado de RF-07 ou RF-08
  motivo_quebra: string?    // texto explicativo quando quebra_suspeita for true
}
```

**Migrações necessárias:** 🟡 Sim. A entidade `Lote` é a que o `motor-filtros` persiste no SQLite para deduplicação. O esquema da tabela pertence ao `motor-filtros`, e este componente define a forma do objeto.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|---|---|---|
| 🟡 `coletor-lotes` | Obrigatória | Fornece o conteúdo a ser interpretado; sem ele o parser não tem entrada. |
| 🟡 `cadastro-leiloeiros` | Obrigatória | Fornece `base_url` para resolver links relativos e o identificador que seleciona o parser. |
| 🟡 Biblioteca de parsing de HTML | Obrigatória | Falha de import encerra o processo; é dependência de instalação. |
| 🟡 Relatório do `onboarding-leiloeiro-assistido` | Opcional | Orienta quais campos esperar em cada leiloeiro. Sua ausência torna a escrita do parser mais lenta, sem impedi-la. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---|---|---|
| 🟡 EC-01: Layout mudou e nenhum lote é encontrado | Deploy do leiloeiro | Sinal de quebra para aquela busca, com o tamanho do conteúdo registrado como evidência de que havia o que ler (RF-07). |
| 🟡 EC-02: Parser lança exceção | Estrutura inesperada no conteúdo | A falha é capturada, registrada com a busca de origem, e as demais buscas prosseguem (RF-10). |
| 🟡 EC-03: Preço como `Sob consulta` ou `A combinar` | Lote sem valor divulgado | Lance inicial e lance corrente registrados como nulos, com o texto original preservado na descrição. O lote não é descartado. |
| 🟡 EC-04: Ano ausente ou fora de faixa plausível | Campo vazio, ou valor como `0000` | Ano registrado como nulo. O lote segue, e o `motor-filtros` decide se ano nulo pode casar com um alvo. |
| 🟡 EC-05: Lote sem link | Estrutura parcial na página | Lote descartado individualmente, com incremento do contador de descartes (RF-09). |
| 🟡 EC-06: Mesmo lote aparecendo duas vezes na mesma página | Paginação sobreposta, ou destaque duplicado | Mantida uma única ocorrência por identificador canônico dentro da mesma busca. |
| 🟡 EC-07: Conteúdo em codificação divergente da declarada | Servidor declarando ISO e servindo UTF-8 | Tentativa de decodificação com o encoding declarado; falhando, recorre a UTF-8 e registra a divergência. |
| 🟡 EC-08: Maioria dos lotes sem preço | Site passou a carregar preço por requisição adicional | Sinal de quebra ao ultrapassar 30% de lotes incompletos (RF-08), com sugestão de reavaliar o nível de coleta. |
| 🟡 EC-09: Tipo de leilão com nomenclatura desconhecida | Site usa termo fora do conjunto fechado | Campo registrado como nulo, com o texto original na descrição, e registro para que o Rafael avalie ampliar o conjunto. |
| 🟡 EC-10: Conteúdo recebido vazio | Coletor entregou resposta sem corpo | Não é quebra de parser. Registrado como busca sem conteúdo, atribuído ao coletor, sem falso alarme de parser desatualizado. |
| 🟡 EC-11: Lote sem nenhum lance ainda | Pregão recém-aberto | Lance corrente registrado como nulo e lance inicial preenchido. O `motor-filtros` adota o inicial como valor de comparação nesse caso. |
| 🟢 EC-15: Busca sem nenhum resultado | Filtro restritivo, leiloeiro pequeno, período sem pregões | O parser lê o indicador de total do site. Total zero devolve lista vazia **sem** sinal de quebra. Quebra é total maior que zero sem cards extraídos, ou indicador ausente sem cards (layout desconhecido). Sem essa distinção, toda busca vazia viraria alerta falso de layout quebrado. |
| 🟢 EC-13: Número do lote reiniciado a cada evento | Leiloeiro numera lotes por pregão, como o Vip ("Lote: 21" em vários eventos) | O número fica em `numero_lote` só para exibição, e o identificador canônico usa o identificador do anúncio (RF-06). Usar o número causaria colisão: o lote novo seria tratado como já notificado e nunca chegaria ao Rafael. |
| 🟢 EC-14: Mesma marca com grafias diferentes no mesmo site | Cadastro do leiloeiro mistura `MMC` e `MITSUBISHI`, `GM` e `CHEVROLET` | Tradução para o nome canônico (RF-12). Sem ela, o alvo escrito por extenso perderia em silêncio os lotes da grafia abreviada. |
| 🟡 EC-12: Site exibe apenas o lance inicial na listagem | Leiloeiro que só mostra o valor corrente ao abrir o lote | Lance corrente registrado como nulo com nota de indisponibilidade na origem, para que a limitação fique visível no relatório e não seja confundida com pregão sem lance. |

---

## 12. Segurança e Privacidade

- **Autenticação:** 🟡 Nenhuma. O componente opera sobre conteúdo já obtido, sem tocar a rede.
- **Autorização:** 🟡 Nenhuma.
- **Dados sensíveis:** 🟡 O conteúdo processado pode incluir número de chassi em leiloeiros acessados com login. O MVP não extrai chassi (NG-04). Caso venha a extrair, o campo deve ser tratado como dado identificável de veículo de terceiro e não deve ser replicado em log.
- **Auditoria:** 🟡 Por busca, ficam registrados quantos lotes foram extraídos, quantos descartados e se houve sinal de quebra, permitindo reconstruir o comportamento do parser ao longo do tempo.

---

## 13. Plano de Rollout

- **Estratégia:** 🟡 Um parser por vez, acompanhando o cadastro de leiloeiros. O primeiro parser é escrito para o leiloeiro público de estrutura mais simples, validado ponta a ponta até a notificação, e serve de modelo para os demais.
- **Como reverter (rollback):** 🟡 Parsers são arquivos independentes, versionados em git. Reverter um parser problemático é um `git checkout` daquele arquivo, sem afetar os outros leiloeiros. Para desligar um leiloeiro cujo parser quebrou e ainda não foi consertado, `ativo: false` no cadastro.
- **Monitoramento pós-deploy:** 🟡 Acompanhar, nas primeiras execuções de cada parser novo, a contagem de lotes extraídos contra o que a página mostra no navegador, e a taxa de descartes. Descarte alto indica parser incompleto, e não site irregular.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---|---|---|---|
| 🟡 OQ-01 | O limiar de 30% de lotes incompletos para sinalizar quebra é adequado, ou vai gerar alarme falso em sites naturalmente irregulares? | Médio | Rafael | Após as primeiras execuções reais |
| 🟡 OQ-02 | A marca e o modelo devem ser extraídos de campos próprios do site ou inferidos do título do lote? Nem todo leiloeiro separa esses campos. | Alto | Rafael | Ao escrever o segundo parser |
| 🟡 OQ-03 | Vale gravar o conteúdo bruto apenas quando houver sinal de quebra, para facilitar o conserto do parser? Isso conflita de forma parcial com a decisão de conteúdo transiente. | Médio | Rafael | Após a primeira quebra real |
| 🟡 OQ-04 | Os cinco leiloeiros-alvo exibem o lance corrente já na página de listagem, ou algum deles só revela esse valor ao abrir o lote? Onde o corrente não estiver na listagem, o filtro por lance corrente fica inviável naquele site sem uma requisição por lote. | Alto | Rafael | Ao escrever o primeiro parser |
| 🟡 OQ-05 | Todos os leiloeiros informam os dois anos no padrão `fabricação/modelo`, ou algum publica um único ano sem dizer qual dos dois é? | Médio | Rafael | Ao escrever o segundo parser |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---|---|---|
| 🟡 Um parser por leiloeiro, em arquivo próprio | Um parser genérico configurável por seletores | É a mitigação que o PRD indica para o risco de mudança de layout. Cinco sites sem padronização entre si não se acomodam bem em um parser único, e um genérico concentraria todo o risco em um só arquivo. |
| 🟡 Quebra sinalizada de forma ativa, e não inferida do silêncio | Devolver lista vazia e deixar o resto do sistema concluir | Atende ao critério de aceite do PRD de não falhar em silêncio. Lista vazia é ambígua: pode significar site sem novidade ou parser morto, e confundir os dois é a falha mais cara do sistema. |
| 🟡 Lote com preço nulo é preservado, e não descartado | Descartar lote sem preço | Descartar perderia oportunidade real: preço sob consulta é comum em leilão e não significa lote irrelevante. A decisão sobre preço ausente pertence ao filtro, com o contexto do teto do alvo. |
| 🟢 Identificador canônico derivado de identificador **único no leiloeiro**: número do lote se global, senão id do anúncio na URL, senão hash da URL | Usar sempre o número do lote; usar sempre a URL; usar posição na página | A posição muda a cada execução, o que geraria notificação repetida. Emendado em 2026-10-03: a versão 1.0 preferia o número do lote, mas o Vip reinicia a numeração a cada evento, e o número colidiria entre eventos. Antes de escolher a fonte do identificador num leiloeiro novo, é preciso confirmar se o número se repete (`onboarding-leiloeiro-assistido` RF-10). |
| 🟢 Tabela de sinônimos de marca comum a todos os parsers, ampliável por leiloeiro | Exigir que o Rafael escreva a marca como cada site escreve; sinônimos no YAML do alvo | Decidido em 2026-10-03, ao encontrar `MMC`/`MITSUBISHI` e `GM`/`CHEVROLET` como marcas distintas no formulário do Vip. Uma tabela comum faz o conhecimento de um leiloeiro valer para os outros, e mantém o YAML dos alvos simples. A regra de casamento por conteúdo do `motor-filtros` (RF-02) não resolve isso: `mmc` não contém `mitsubishi`. |
| 🟡 Normalização de marca e modelo em minúsculas e sem acento | Comparar o texto como veio da origem | A comparação contra o veículo-alvo acontece no `motor-filtros`. Normalizar na tradução evita que cada leiloeiro imponha sua grafia ao filtro. |
| 🟡 Extrair lance inicial e lance corrente como campos separados | Um único campo de preço | Decidido em 2026-09-22, junto da escolha de filtrar pelo lance corrente. Os dois valores divergem ao longo do pregão e respondem a perguntas diferentes: o corrente diz quanto custaria levar o carro agora, e o inicial diz de onde o pregão partiu, informação necessária para a margem de segurança em estudo no `motor-filtros`. |
| 🟡 Extrair os dois anos, deixando ao filtro a escolha de qual comparar | Extrair apenas o ano de modelo | O Rafael escolheu comparar pelo ano de modelo em 2026-09-22. Preservar também o ano de fabricação custa um campo e permite rever o critério depois sem reescrever nenhum parser. |

---

## Apêndice

### Referências
- `_reversa_sdd/prd.md` — seção 4, escopo "Scraping e parsing"; seção 8, risco de mudança de layout; seção 9, critério de não falhar em silêncio
- `_reversa_sdd/ideation.md` — seção "Arquitetura iterativa com agente de IA como gestor"
- `_reversa_sdd/sdd/coletor-lotes.md` — origem do conteúdo bruto

### Histórico de Revisões
| Versão | Data | Autor | Mudanças |
|---|---|---|---|
| 1.0 | 2026-09-21 | reversa-spec-sdd | Criação inicial a partir do PRD |
| 1.1 | 2026-10-03 | reversa-forward | Emenda com lições do Vip válidas para qualquer leiloeiro: RF-06 passa a exigir identificador único no leiloeiro (número do lote pode ser por evento); RF-12 e tabela comum de sinônimos de marca; EC-13 e EC-14. Origem: `_reversa_forward/001-mvp-varredura-ponta-a-ponta/investigation.md#1` |
| 1.2 | 2026-10-03 | reversa-forward | EC-15: zero resultados legítimos não é quebra; o parser deve ler o indicador de total do site. Origem: audit da feature 001 (A001) |
