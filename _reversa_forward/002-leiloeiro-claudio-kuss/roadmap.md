# Roadmap: Leiloeiro Claudio Kuss

> Identificador: `002-leiloeiro-claudio-kuss`
> Data: `2026-10-10`
> Requirements: `_reversa_forward/002-leiloeiro-claudio-kuss/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA
> Numeração das decisões: continua a da feature 001 (D-01 a D-32), para que "D-nn" nunca seja ambíguo.

## 1. Resumo da abordagem

O Claudio Kuss entra como **segundo par adaptador + parser**, registrado pelo id `claudio-kuss-leiloes`, sem mexer no Vip. A busca declarada no YAML é uma só (`categoria: Veículos - Financeiras`); o adaptador a transforma numa sequência de requisições: a **agenda** (`/proximos-leiloes`), e para cada evento da categoria a **quantidade** (`op=Q`) e as **páginas de lotes** (`op=P`, JSON, 10 por página). O parser lê o JSON e devolve lotes normalizados, sem preço na maioria (RN-07).

Depois da filtragem, uma etapa nova de **enriquecimento** consulta o detalhe (`op=D`) **só dos lotes novos** que vão para o aviso: descarta os retirados (RN-05) e traz observações, despesas administrativas, placa parcial e estado do documento (RF-07). O digest, o relatório e a lista de monitoramento ganham as linhas de pregão e observações.

O núcleo recebe quatro mudanças pequenas e genéricas, todas inertes para o Vip: anotações por página (o parser precisa saber de que evento veio cada página), preço opcional no teste de "lotes incompletos", teto de páginas por adaptador e o passo de enriquecimento. Nenhuma tabela nova, nenhuma migração.

Verificação feita durante este plano (2026-10-10, 9 requisições espaçadas): 391 lotes em dois eventos (13/10 e 20/10), 387 com ano `AA/AA`; dois Fluence dentro da faixa do alvo, um deles `IMP RENAULT/FLUENCE DYN 20A` 2013 com a observação **"SINISTRADO - nos documentos consta recuperado de sinistro"** e documento de São Paulo. É o caso típico que RN-08 manda mostrar.

## 2. Princípios aplicados

Não existe `.reversa/principles.md`. Usados os mesmos princípios de fato da feature 001 (`001-.../roadmap.md` §2).

| Princípio (de fato) | Como a feature se relaciona | Status |
|---------------------|-----------------------------|--------|
| Menor custo | Nível `script`, site sem proteção anti-robô, nenhuma dependência nova | respeita |
| Não falhar em silêncio | Agenda sem nenhum evento reconhecível, evento com `qtde > 0` sem lotes e JSON fora do formato viram quebra com alerta (D-41); divergência entre `qtde` e lotes lidos vai para o log (D-36) | respeita |
| Nenhum segredo em arquivo versionado nem em log | Nenhuma credencial: o Claudio Kuss é público | respeita |
| Sistema não dá lances | Só leitura: agenda, `json_edital.php` (`op=Q`, `op=P`) e `json_lance_info_lote.php` (`op=D`). Nenhuma chamada a `json_login.php`, `/portal/`, `/winleilao/`, `/contrato/` | respeita |
| Mudança de comportamento sob decisão humana | O bloco do Claudio Kuss entra no `leiloeiros.yaml` com `ativo: true` só depois do dry-run real conferido (§8) | respeita |
| Conduta de coleta discreta | 5 s entre requisições ao mesmo host (já garantido pelo `ClienteHTTP`); ~43 requisições por varredura, o mesmo que uma pessoa folheando as páginas de fotos do site | respeita |

## 3. Decisões técnicas

### 3.1 Contrato com o Claudio Kuss

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-33 | Lista de lotes pelo JSON paginado `POST /json_edital.php` `op=P` (10 lotes por página, com o lance corrente no campo `valor`) | É o endpoint que a própria página "com fotos" do site usa; JSON é menos frágil que HTML; cada página é independente e cabe no contrato atual `extrair(conteudo, contexto)` sem fundir respostas | `GET /relacao-lista/<ev>` + `op=T` (2 requisições por evento em vez de ~36, mas a lista HTML não tem preço: exigiria fundir duas respostas no parser, mudando o núcleo; e a marcação da tabela varia entre linhas, o censo quebrou na primeira tentativa). Fica registrada como saída se o volume crescer (investigation §3) | 🟢 |
| D-34 | Descoberta de eventos na **própria busca**: a página 1 é `GET /proximos-leiloes` (agenda); o adaptador lê os blocos de evento, guarda os que têm rótulo contendo a `categoria` da busca (comparação sem acento e sem caixa) e monta o plano das páginas seguintes | `preparar_sessao` não recebe os filtros da busca, e a categoria é filtro da busca (RF-01). Na busca, a agenda passa pelo coletor como qualquer página: falha de rede vira falha da busca, e o parser enxerga a página para detectar quebra (D-41) | Agenda em `preparar_sessao` (não conhece a categoria; falha derrubaria o leiloeiro inteiro sem passar pelo parser); página inicial do site (mistura destaques e banners; a agenda é a lista canônica) | 🟢 |
| D-35 | Sequência de páginas por evento: `op=Q` (quantidade) e depois `op=P` de 1 até `qtdePag`. O adaptador mantém um **cursor** (eventos e páginas) reiniciado a cada página 1 | `op=Q` dá a contagem para a conferência de RF-03 e evita a requisição vazia ao fim de cada evento. O coletor chama `montar_requisicao` e `tem_proxima_pagina` em ordem, uma busca por vez, então o estado no adaptador é seguro | Paginar até receber `[]` (sem conferência de total; observado: página além da última devolve `[]`, usado só como proteção); estado no `ContextoParsing` (mistura coleta e parsing) | 🟢 |
| D-36 | Conferência de RF-03: ao terminar um evento, se a soma dos itens das páginas `op=P` diferir de `qtde`, aviso em log com evento, esperado e lido. Se uma página vier com `[]` antes de `qtdePag`, o evento termina ali (com o mesmo aviso) | Pede-se aviso, não falha: o lote pode ser retirado da lista entre a contagem e a leitura | Tratar divergência como quebra (alarme falso em leilão vivo) | 🟡 |
| D-37 | Página com **anotações**: `Requisicao` ganha `anotacoes: dict` opcional, copiado para `Pagina.anotacoes` pelo coletor e entregue ao parser em `ContextoParsing.pagina`. O Claudio Kuss anota `tipo` (`agenda`, `quantidade`, `lotes`), `evento` e `pregao_em` | O JSON de `op=P` não diz de que evento é o lote; o parser precisa do evento para o link (`/lance/<ev>/0/<seq>`) e da data do pregão (RF-06). A anotação é genérica e o Vip simplesmente não a usa | Parser deduzir o evento pelo conteúdo (não há campo); repetir a lógica de agenda no parser; ler a URL e o corpo da requisição (o parser não os recebe e não deveria conhecer o protocolo) | 🟢 |
| D-38 | Link do lote: `https://www.claudiokussleiloes.com.br/lance/<evento>/0/<seq>`. Id canônico: `claudio-kuss-leiloes:<seq>` | `seq` é global no site (é o `le_id` do detalhe); o número do lote é por evento e fica vazio até o loteamento (RN-03). A URL `/lance/897/0/<seq>` foi aberta e responde 200 | Número do lote; `/lance/<ev>/<lote>` (só existe depois do loteamento) | 🟢 (id) 🟡 (link depois do loteamento) |
| D-39 | `tipo_leilao_da_busca`: categoria contendo "financeiras" → `financiamento`; outra categoria → `None`, com aviso de coerência já existente | RN-02; mesma lógica do D-15 do Vip | Ler um selo por lote (não existe) | 🟡 |
| D-40 | Filtro aceito no YAML: só `categoria` (texto). Qualquer outra chave aborta antes da rede citando o leiloeiro | Mesma regra do D-12 do Vip; o site não tem outros filtros úteis sem login | Repassar `pesq` (busca textual do site) — recortaria por texto, contra a busca ampla (§6.1.1 do `cadastro-leiloeiros`) | 🟢 |

### 3.2 Parsing

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-41 | Busca vazia e quebra (RF-08): página `agenda` declara `busca_vazia` sempre que reconhece **pelo menos um** bloco de evento (de qualquer categoria), porque ela nunca traz lotes (ajuste do `/reversa-coding` em 2026-10-10: com a regra anterior, eventos da categoria com `qtde = 0` virariam quebra); agenda sem nenhum bloco reconhecível **não** é vazia (vira "0 lotes de N KB" no núcleo, logo quebra). Página `quantidade` declara vazia com `qtde = 0`. Página `lotes` com `[]` é vazia; JSON inválido, objeto no lugar de lista ou item sem `seq`/`bem` levanta exceção (quebra) | Encaixa nas regras do `parser-lotes` (EC-15) e do núcleo: a busca só é vazia se **todas** as páginas declararem vazia. Um evento com `qtde > 0` sem lotes lidos fica com a página `quantidade` não vazia, e portanto vira quebra | Contar eventos no adaptador e silenciar (cego para mudança de layout da agenda) | 🟡 (agenda totalmente vazia em feriado prolongado daria alarme falso; risco R-03) |
| D-42 | `bem` = `MARCA/MODELO VERSÃO`: divide na primeira `/`. Prefixo `IMP ` (importado) é removido da marca. Novos sinônimos comuns em `parsing/marcas.py`: `chev` → `chevrolet`, `caoachery` → `caoa chery`, `m benz` → `mercedes-benz`, `lr` → `land rover` | Censo de 391 lotes (2026-10-10): `IMP NISSAN`, `IMP RENAULT`, `CHEV`, `CAOACHERY`, `M BENZ`, `IMP LR` existem; a tabela é comum, então o Vip também passa a reconhecer essas grafias (onboarding, armadilha `sinonimos_marca`) | Sinônimos só no parser do Kuss (perde-se para o próximo leiloeiro) | 🟢 |
| D-43 | `bem` igual a `RETIRADO` → lote com `retirado = True` (o motor já descarta e conta). **Sucata** fica fora do aviso. *Revisto no coding (2026-10-10):* o JSON `op=P` **não** traz o prefixo `SUCATA` (só a lista HTML traz); a sucata é reconhecida no **detalhe** (`tblInformacoes` começando com "SUCATA", ou `tblTransf` = "SUCATA"), o parser marca `situacao = "sucata"` e o enriquecimento a tira dos novos, como os retirados. O prefixo na lista continua tratado, por defesa | Censo: 1 `RETIRADO` e 17 `SUCATA ...` (inclusive `SUCATA RENAULT`, `SUCATA IMP RENAULT`). Sucata é documento baixado: o carro não volta a circular, fora de "só conservado" (preferência do Rafael). Remover o prefixo faria um Fluence sucata casar com o alvo | Manter `sucata renault` como marca (exclusão acidental, e o log de "marca fora da tabela" a cada varredura); filtrar no motor (o conceito só existe neste leiloeiro, por ora) | 🟡 |
| D-44 | Ano `AA/AA`: fabricação e modelo; `AA` vira `20AA` se `AA ≤ (ano corrente + 1) mod 100`, senão `19AA`. Campo vazio → ano ausente (o motor descarta, RN-02 da 001) | Censo: 387 de 391 no formato `AA/AA`, 4 vazios (não veículos) | Sempre `20AA` (erra carros dos anos 90) | 🟢 |
| D-45 | Valor `21.600,00` → `Decimal` no `lance_corrente`; vazio → `None` (preço a confirmar). `lance_inicial` fica `None`: o lance inicial (`av`) só existe no endpoint de histórico depois do loteamento e não é lido nesta feature | RN-07; o `av` aparece só em `json_lance_historico.php` (lido no JS do site), consultado em laço pela página; lote não loteado responde `{"status":"Não loteado"}` | Consultar o histórico de cada candidato (terceira requisição por lote, valor ausente na maior parte do tempo) | 🟢 |
| D-46 | O parser do Claudio Kuss declara `preco_obrigatorio = False`; o núcleo deixa de contar preço ausente no limite de 30% de "lotes incompletos" para parsers assim declarados | Antes do pregão, 333 de 346 lotes não têm valor (contagem do `op=T`, 2026-10-10). Com a regra atual, toda varredura do Kuss viraria "quebra suspeita" | Subir o limite para 100% (cego para quebra de marca/modelo/ano); preencher preço fictício | 🟢 |

### 3.3 Coleta, enriquecimento e saída

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-47 | O adaptador pode declarar `teto_paginas`; o coletor usa `getattr(adaptador, "teto_paginas", 50)`. Claudio Kuss: 120 | Hoje são ~43 páginas (1 + 36 + 6); um terceiro evento de financeiras passaria do teto global de 50 e a busca inteira viraria falha `teto_paginas`. 120 páginas a 5 s = 10 min, o limite do RNF | Subir o teto global (afrouxa a proteção do Vip, onde 17 páginas é o normal) | 🟢 |
| D-48 | **Enriquecimento** depois da filtragem e antes do digest: para cada lote em `novos` cujo adaptador tenha `requisicao_detalhe(lote)`, o orquestrador faz a requisição pelo mesmo `ClienteHTTP` (que passa a ser fechado só depois desta etapa) e o parser aplica `aplicar_detalhe(lote, conteudo)`. Retirado → sai de `novos` e soma em `descartados_retirados`; não é gravado em `lote_conhecido` (será conferido de novo na próxima varredura) | RF-05 pede o detalhe "apenas dos lotes que casarem"; restringir aos **novos** dá o mesmo resultado com menos requisições (os já conhecidos não serão avisados). Semeáveis não são enriquecidos (não há aviso) | Detalhe de todos os lotes (346 requisições, 29 min); detalhe de todos os candidatos, inclusive já conhecidos (requisições sem efeito) | 🟢 |
| D-49 | Falha no detalhe (rede, JSON inválido) **não** bloqueia o aviso: o lote segue com `observacoes = None` e o digest diz "observações não lidas; veja o link". Log de aviso | Avisar sem as observações é melhor que perder o lote; o link leva à mesma informação | Segurar o lote para a próxima varredura (atrasa o aviso de um carro bom por uma falha passageira) | 🟡 |
| D-50 | Novos campos opcionais no `Lote`: `evento_id`, `pregao_em`, `observacoes`, `despesas_adm`, `placa_parcial`, `local_documento` e `detalhe_lido` (distingue "detalhe falhou" de "sem observações"). Vip deixa todos `None` | Detalhe em `data-delta.md`. Placa parcial e local do documento (`tblTransf`) ajudam a regra de reaparições (E003 da 001) e o custo de transferência (backlog "custo na garagem") | Dicionário genérico `extras` (sem tipo; testes e formatação ficam frágeis) | 🟢 |
| D-51 | Digest: item do Kuss ganha o pregão na segunda linha (`Pregão 13/10 10:00`) e uma linha `Obs.:` com as observações resumidas em até 160 caracteres (com `…`). Relatório e lista de monitoramento: linhas `Pregão`, `Despesas admin.`, `Documento` (placa parcial e estado) e `Observações` completas. Lote sem esses campos (Vip) sai igual a hoje | RF-06 e RF-07; o limite de 160 mantém o resumo legível com vários lotes e longe dos 4096 caracteres por mensagem | Observações completas no Telegram (o texto padrão do Kuss tem 400+ caracteres); omitir no Telegram (RF-07 pede no aviso) | 🟢 |
| D-52 | O texto padrão de todos os lotes (`tblTxtInfo`: "vendido no estado... recuperado de financiamento ou sinistro...") **não** entra nas observações; só `tblInformacoes` (específico do lote) | Repetido em todo lote, não ajuda a separar um carro do outro e esconderia a observação específica no resumo | Concatenar os dois | 🟢 |

## 4. Premissas

| Premissa | Origem | Risco se errada |
|----------|--------|-----------------|
| O link `/lance/<ev>/0/<seq>` continua abrindo o lote depois do loteamento | requirements §10 (lacuna) | Link quebrado no aviso; mitigação: conferir no onboarding depois de 13/10 e trocar o formato se preciso (só `parsing/claudio_kuss.py`) |
| Um carro não vendido num evento reaparece em outro com **outro** `seq` | requirements §10 (lacuna) | Aviso repetido do mesmo carro; a regra de reaparições da lista (E003 da 001), agora com placa parcial, cobre a revisão manual |
| A agenda sempre tem pelo menos um evento publicado | D-41 | Alarme de quebra falso no período sem leilões; no máximo um por dia (alertas 1/dia/leiloeiro) |

## 5. Delta arquitetural

| Componente | Arquivo de origem | Tipo de mudança | Resumo |
|------------|-------------------|-----------------|--------|
| Coletor de lotes | `_reversa_sdd/sdd/coletor-lotes.md` RF-12/RF-14; `src/bot_leilao/coleta/coletor.py`, `modelos.py` | regra-alterada | `Requisicao.anotacoes` → `Pagina.anotacoes`; teto de páginas por adaptador (D-37, D-47) |
| Adaptador Claudio Kuss | `coletor-lotes.md` RF-12 | componente-novo | `src/bot_leilao/coleta/claudio_kuss.py`: agenda, cursor de eventos e páginas, `requisicao_detalhe` (D-33 a D-36, D-38 a D-40) |
| Parser de lotes (núcleo) | `_reversa_sdd/sdd/parser-lotes.md` RF-07 a RF-11; `parsing/nucleo.py`, `modelos.py` | regra-alterada | Contexto por página; preço opcional no limite de incompletos (D-37, D-46) |
| Parser Claudio Kuss | `parser-lotes.md` RF-06, RF-12 | componente-novo | `src/bot_leilao/parsing/claudio_kuss.py`: agenda, quantidade, lotes e detalhe (D-41 a D-45, D-52) |
| Tabela de sinônimos | `parser-lotes.md` RF-12; `parsing/marcas.py` | regra-alterada | Quatro grafias novas (D-42) |
| Orquestrador | `_reversa_sdd/sdd/agendador-observabilidade.md`; `orquestrador.py` | regra-alterada | Registro do novo par; etapa de enriquecimento entre filtragem e digest; cliente HTTP vive até o fim dela (D-48, D-49) |
| Notificador (digest) | `_reversa_sdd/sdd/notificador-telegram.md` RF-01; `notificacao/digest.py` | regra-alterada | Pregão e observações no item (D-51) |
| Relatório e lista de monitoramento | emendas E001/E002 da 001; `notificacao/relatorio.py` | regra-alterada | Linhas de pregão, despesas, documento e observações (D-51) |
| Cadastro de leiloeiros | `_reversa_sdd/sdd/cadastro-leiloeiros.md`; `config/leiloeiros.yaml` | regra-alterada (só dados) | Bloco do Claudio Kuss; código de validação inalterado |

Fora do delta: motor de filtros, deduplicação, semeadura, banco, alertas, trava, CLI, agendamento do Windows.

## 6. Delta no modelo de dados

- Sete campos opcionais novos no `Lote` (em memória), campo `pagina` no `ContextoParsing`, `anotacoes` em `Requisicao` e `Pagina`. **Banco inalterado** (`user_version` continua 1).
- Detalhe completo em: `_reversa_forward/002-leiloeiro-claudio-kuss/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Claudio Kuss: agenda, `json_edital.php` (`op=Q`, `op=P`), `json_lance_info_lote.php` (`op=D`), página humana do lote | HTTP | `_reversa_forward/002-leiloeiro-claudio-kuss/interfaces/claudio-kuss.md` |
| Telegram `sendMessage` | HTTP | inalterado (só o texto do item muda; `001-.../interfaces/telegram-bot-api.md`) |

## 8. Plano de migração

1. Nenhuma migração de banco. A primeira varredura com o Claudio Kuss ativo **semeia** a busca dele (RF-09): os candidatos de hoje entram como conhecidos e **não** são avisados. Para vê-los antes, o onboarding manda rodar `--dry-run`, que lista os candidatos sem gravar nada.
2. Ordem de entrega: núcleo genérico (anotações, teto, preço opcional, campos do `Lote`) com o Vip passando igual → adaptador e parser do Kuss com fixtures reais → enriquecimento e saída → bloco no YAML e dry-run real.
3. Reversão: `ativo: false` no bloco do Claudio Kuss. Nada no banco depende dele.

## 9. Riscos

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|---------------|---------|-----------|
| R-01 | Varredura passa de 10 min com mais eventos (cada evento de ~350 lotes custa ~3 min) | média | médio | Teto de 120 páginas (D-47); se virar rotina, trocar para `relacao-lista` + `op=T` (2 requisições por evento, investigation §3) |
| R-02 | Muitas observações de sinistro no aviso, tornando o resumo longo | média | baixo | Resumo de 160 caracteres (D-51); o Rafael descarta à mão (RN-08); filtro por palavras fica no backlog |
| R-03 | Agenda sem eventos em feriado prolongado vira alarme de quebra | baixa | baixo | Alerta limitado a 1/dia; ajustar D-41 se acontecer, com a página real como fixture |
| R-04 | Lote de sucata sem o prefixo `SUCATA` (só nas observações) | média | médio | Observação aparece no aviso (RN-08); o Rafael descarta |
| R-05 | Mudança no JSON (`op=P`) sem aviso | baixa | alto | Quebra detectada pelo núcleo e alerta por leiloeiro (D-41); fixtures reais nos testes |

## 10. Critério de pronto

- Os 6 cenários Gherkin do requirements passam em testes sem rede, com as amostras reais de `amostras/` (transformadas em fixtures).
- Todos os testes da 001 continuam verdes sem alteração de comportamento (o Vip é a regressão a vigiar).
- Um dry-run real no container lista os lotes dos eventos de financeiras abertos, com o total por evento igual ao `qtde`, e os Fluence da faixa aparecem como candidatos.
- Uma varredura real com o Kuss ativo termina em menos de 10 minutos.
