# Roadmap: MVP de Varredura Ponta a Ponta

> Identificador: `001-mvp-varredura-ponta-a-ponta`
> Data: `2026-10-03`
> Requirements: `_reversa_forward/001-mvp-varredura-ponta-a-ponta/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

Um único programa Python, síncrono e de processo único, executado por comando manual (`python -m bot_leilao varrer`), que atravessa em sequência os oito componentes de `_reversa_sdd/sdd/`: carrega e valida os dois YAML e o `.env`, abre o SQLite e registra o início da execução, coleta a busca do Vip Leilões por sessão HTTP com cookie e paginação, converte o HTML em lotes normalizados, descarta retirados, filtra contra os veículos-alvo, deduplica, envia o digest pelo Telegram e só então grava os lotes como notificados, encerrando o registro da execução em qualquer desfecho.

Como o projeto é greenfield, o "delta" é sobre as specs, e não sobre código: cada componente nasce aqui, implementado **só até onde a fatia vertical exige**. Apify, login, agendamento automático, recomendação de frequência e relatório de saúde ficam fora, mas o desenho reserva o lugar deles (registro de adaptadores, campo `nivel_coleta`, tabelas de histórico) para que entrem sem refatoração.

A pendência técnica que o requirements mandava resolver primeiro **foi resolvida durante este plano** (2026-10-03): o servidor do Vip aplica de fato os filtros de procedência e monta. Uma busca `Filtro.Marca=NISSAN` devolveu 9 resultados; acrescida de `Filtro.Procedencia=4` e `Filtro.Monta=1`, devolveu 1. O contrato HTTP completo está em `interfaces/vip-pesquisa.md`.

## 2. Princípios aplicados

Não existe `.reversa/principles.md` no projeto. Os princípios abaixo não são formais: são as regras estruturantes que o PRD, a ideação e as specs repetem, e foram usados aqui como critério de verificação. Para formalizá-los, use `/reversa-principles`.

| Princípio (de fato) | Como a feature se relaciona | Status |
|---------------------|-----------------------------|--------|
| Menor custo: começar gratuito, escalar só quando justificado (`ideation.md`) | Apenas o nível `script` é implementado; nenhuma dependência paga. Leiloeiro ativo com `nivel_coleta` pago aborta antes da rede (D-17) | respeita |
| Não falhar em silêncio (`prd.md#9`) | Sinal de quebra vira alerta; execução sempre registrada; config inválida aborta com mensagem citando alvo e campo | respeita |
| Nenhum segredo em arquivo versionado nem em log (RN-08) | Token e chat id só no `.env`; filtro de log mascara valores de segredos (D-20) | respeita |
| Sistema não dá lances (RN-09) | Nenhuma rota de escrita no site do leiloeiro; só GET de cookie e POST de pesquisa | respeita |
| Mudança de comportamento sob decisão humana (`ideation.md`, gestor de IA) | Nada no código altera YAML por conta própria; a única escrita em `config/` é o arquivo de exemplo quando ausente (EC-01 das duas specs de config) | respeita |
| Conduta de coleta discreta (`coletor-lotes` RNF-02) | 5 s entre requisições ao mesmo host, inclusive entre páginas e entre a obtenção do cookie e a primeira busca | respeita |

## 3. Decisões técnicas

### 3.1 Stack

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Python ≥ 3.12, programa síncrono de processo único | Ideação fixa "script Python" como nível gratuito; volume de 1 busca e poucas páginas não justifica concorrência; síncrono é mais simples de ler e consertar por agente de IA | asyncio; Node.js | 🟢 |
| D-02 | `httpx` (cliente síncrono) para HTTP: sessão com cookies, `max_redirects=3`, timeout de 30 s | Atende RF-03 da feature e RF-13 do `coletor-lotes` com configuração nativa; `httpx.MockTransport` permite testar coletor e notificador sem rede e sem biblioteca extra | `requests` + `responses` (duas dependências para o mesmo resultado); `aiohttp` (assíncrono sem necessidade) | 🟡 |
| D-03 | `beautifulsoup4` + `lxml` para HTML | API conhecida por qualquer agente de IA e por quem está aprendendo; desempenho folgado frente ao RNF-01 do `parser-lotes` (< 2 s por busca) | `selectolax` (mais rápido, menos conhecido); expressões regulares (frágeis a layout) | 🟡 |
| D-04 | `PyYAML` (`safe_load`) + validação explícita em `dataclasses` | As specs exigem mensagens que citam o alvo ou leiloeiro e o campo (RNF-04 de `configuracao-veiculos-alvo`); validação escrita à mão produz exatamente essas mensagens | `pydantic` (mensagens próprias, difíceis de moldar ao texto exigido); `ruamel.yaml` (preserva comentários, desnecessário porque o programa não reescreve o YAML) | 🟡 |
| D-05 | Telegram por chamada HTTP direta a `sendMessage`, com `parse_mode=HTML` | Só três caracteres a escapar (`<`, `>`, `&`), o que torna RF-10 do `notificador-telegram` trivial e testável; reaproveita o `httpx` | `python-telegram-bot` (assíncrona, grande, voltada a bots interativos, que são NG-01); `MarkdownV2` (18 caracteres reservados) | 🟡 |
| D-06 | `sqlite3` da biblioteca padrão, arquivo único `dados/bot-leilao.sqlite3`, migrações por `PRAGMA user_version` | Specs já fixam SQLite e arquivo único compartilhado entre `motor-filtros` e `agendador-observabilidade`; `user_version` dá migração idempotente sem dependência | ORM (SQLAlchemy); Alembic | 🟢 |
| D-07 | Trava de execução por arquivo `dados/varredura.lock` criado com abertura exclusiva, contendo PID e instante; órfã após 2 h | Portável entre o notebook Windows e um futuro Linux; atende RF-15 e EC-01 do `agendador-observabilidade` | `fcntl`/`msvcrt` (não portáveis entre si); `portalocker` (dependência para um caso simples) | 🟡 |
| D-08 | `python-dotenv` para carregar `.env` | Padrão de mercado para o arranjo que as specs já decidiram | Exigir variáveis exportadas no shell (atrito no Windows) | 🟢 |
| D-09 | `pyproject.toml` + `venv` + `pip install -e .[dev]`; testes com `pytest` | Funciona igual no Windows e no devcontainer, sem ferramenta extra a instalar | `uv`; `poetry` | 🟡 |
| D-30 | Toda requisição aos leiloeiros leva um `User-Agent` de navegador atual, constante e definido num único ponto do código, junto de `Accept-Language: pt-BR`; o programa não se autoidentifica como robô | Decisão do Rafael em 2026-09-22 (`requirements.md` §2 e RF-03; Decision Log do `coletor-lotes`). O padrão do `httpx` (`python-httpx/<versão>`) se anuncia como robô e eleva o risco de recusa pelo Cloudflare. O limite continua valendo: sem resolver CAPTCHA (NG-03 do coletor) e sem escalar para IP residencial contra recusa deliberada | `User-Agent` padrão da biblioteca; rotação de `User-Agent` (é disfarce, não cortesia, e passa do limite decidido) | 🟢 |

### 3.2 Contrato com o Vip Leilões

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-10 | Preparação de sessão: `GET https://www.vipleiloes.com.br/` seguindo até 3 redirecionamentos, guardando o cookie `__CBCanal` | Observado em 2026-10-03: a home responde 200 após 2 redirecionamentos e emite o cookie | Pedir a pesquisa direto (gera laço sem cookie, ocorrido em 2026-09-27) | 🟢 |
| D-11 | Busca: `POST /pesquisa?handler=pesquisar` com corpo `application/x-www-form-urlencoded`; os `filtros` do YAML viram campos `Filtro.<Chave>`; página N via `POST /pesquisa?SortOrder=DataInicio&pageNumber=N&handler=pesquisar` | Endpoint e nomes de campo lidos do formulário `#formPost` e dos links de paginação em 2026-10-03 | Raspar `/pesquisa/index` por GET (não carrega os filtros) | 🟢 |
| D-12 | No YAML, as chaves de filtro são escritas **sem** o prefixo (`marca`, `procedencia`, `monta`); o adaptador converte para `Filtro.Marca` etc. por tabela de mapeamento explícita, e chave desconhecida aborta antes da rede | Mantém o YAML legível e põe o conhecimento do formulário no adaptador, como decidido no `cadastro-leiloeiros` v1.1 (NG-05); falhar cedo evita busca silenciosamente mais larga que a intenção | Chave crua `Filtro.Marca` no YAML (acopla o arquivo ao HTML do site); repassar chave desconhecida (filtro ignorado pelo servidor sem erro) | 🟡 |
| D-13 | Próxima página: existe quando o `li` do link "Next" em `.main-pagination` **não** tem classe `disabled`; o total de `#resultadosEncontrados` serve de verificação cruzada. A página N reenvia o **mesmo corpo** da página 1 | Observado em 2026-10-03: a página 2 da busca `procedencia=4, monta=1` manteve o total de 201 e trouxe 12 lotes sem nenhuma repetição da página 1 | Calcular só pelo total (quebra se o tamanho da página mudar) | 🟢 |
| D-28 | Os parsers traduzem sinônimos de marca para o nome canônico antes de entregar o lote: `mmc` → `mitsubishi`, `gm` → `chevrolet`, `vw` → `volkswagen`. A tabela é **comum** a todos os parsers (RF-12 do `parser-lotes` v1.1), ampliável por leiloeiro, e marca não reconhecida passa como veio, com registro em log | O próprio `<select>` de marcas do Vip lista `MMC` e `MITSUBISHI`, `GM` e `CHEVROLET` como entradas separadas (2026-10-03), e cards reais trazem `mmc`. Pela regra de "contém" do RF-02 do `motor-filtros`, um alvo `Mitsubishi` nunca casaria com `mmc`, perdendo lote sem nenhum sinal | Exigir que o Rafael escreva a marca como o site escreve (frágil e invisível); sinônimos no YAML do alvo (complica a configuração que ele edita toda semana) | 🟢 |
| D-29 | A busca recomendada para o MVP **não filtra por marca**: só `procedencia: 4` e `monta: 1`. Os veículos-alvo fazem o recorte de marca e modelo no motor | Os alvos mudam com frequência e são editados só no `veiculos-alvo.yaml` (decisão de 2026-09-27); uma busca por marca obrigaria a editar também o `leiloeiros.yaml` a cada alvo de outra marca, e um esquecimento viraria lote perdido sem alerta. Custo medido em 2026-10-03: 201 resultados, 17 páginas, cerca de 2 minutos com o intervalo de 5 s, dentro do limite de 10 minutos | Uma busca por marca de alvo (duplica a configuração e cria falha silenciosa) | 🟢 |
| D-14 | Identificador canônico do lote Vip: `vip-leiloes:<id numérico do anúncio>`, tirado do sufixo da URL `/evento/anuncio/<slug>-<id>` | O "Lote: 21" do card é numeração **por evento** e se repete entre eventos; o id do anúncio é global. Atende RF-06 com a regra de fallback por URL do `parser-lotes` | Número do lote (colide entre eventos); hash da URL inteira (muda se o slug mudar) | 🟢 |
| D-15 | `tipo_leilao` do lote é herdado da busca: o adaptador mapeia `procedencia: 4` → `financiamento`; outros valores ficam nulos com registro em log | RN-10 manda não reavaliar procedência no motor; o motor ainda exige `tipo_leilao` (RF-05 do `motor-filtros`), então ele vem da busca, por construção. Só o valor 4 tem correspondência inequívoca no conjunto fechado | Ler o selo "Financiamento" do card (nem todo card tem selo); estender o mapa já para 1, 2, 3 e 5 (sem decisão do Rafael sobre equivalência) | 🟡 |

### 3.3 Regras de domínio que as specs deixavam em aberto

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-31 | Zero resultados legítimos não é quebra: o parser de cada leiloeiro reconhece o **marcador de busca vazia** do site (indicador de total igual a zero, ou mensagem própria de nenhum resultado) e, nesse caso, devolve lista vazia **sem** sinal de quebra. Quebra passa a ser "nenhum card extraído sem marcador de busca vazia". No Vip, o marcador é `div.filter-wait` com "Nenhum lote encontrado.", e a resposta vazia **não** traz `#resultadosEncontrados` (captura de 2026-10-04) | Achado do audit de 2026-10-03 (A001): a página de uma busca sem resultados é conteúdo não vazio sem cards, e a regra literal do RF-07 a trataria como layout quebrado, gerando alerta falso. Regra levada ao `parser-lotes` (EC-15) por valer para qualquer leiloeiro | Tratar toda página sem cards como quebra (alerta falso); tratar toda página sem cards como vazia (esconde quebra real) | 🟢 |
| D-16 | Lote retirado: o parser preenche `situacao` com o texto do card e `retirado = true` quando o texto ou a classe CSS contiver "retirad" (sem caixa, sem acento); o motor descarta antes de filtrar, com contador próprio | RN-12 e RF-17; a investigação de 2026-09-27 viu retirados na listagem, mas o texto exato não foi capturado em 2026-10-03 (todos estavam "Aberto para lances") | Descartar no parser (parser não decide relevância, NG do `parser-lotes`) | 🟡 |
| D-17 | `nivel_coleta` e `estrategia_acesso` são validados conforme o `cadastro-leiloeiros`, mas leiloeiro **ativo** com nível diferente de `script` ou acesso `logado` aborta a execução antes da rede, com mensagem "não implementado nesta versão" | Cumpre a regra de custo e a regra de "validação precede a rede" sem implementar Apify nem login | Ignorar o leiloeiro (falha silenciosa); tentar `script` mesmo assim (contraria a declaração do Rafael) | 🟢 |
| D-18 | `frequencia` é aceita como texto opaco e não validada nesta feature | O formato está em aberto (OQ-04 do `cadastro-leiloeiros`, OQ-01 do `agendador-observabilidade`) e o agendamento automático está fora da fatia | Escolher um formato agora sem decisão do Rafael | 🟡 |
| D-19 | Quilometragem ausente no lote, com teto declarado no alvo, **não elimina**: o lote segue e o log registra | Simetria com o preço ausente (não elimina) e não com o ano (elimina): km não define qual carro é. O Vip exibe km em todo card, então o caso é raro | Eliminar (perderia lote por falha de extração) | 🟡 |
| D-20 | Semeadura por busca: tabela `busca_semeada`. Uma busca só é marcada semeada quando a coleta teve veredito `ok` **e** o parser não sinalizou quebra; nessa execução, os candidatos vão para `lote_conhecido` com `origem = 'semeadura'`, sem digest | RN-07 e RF-13; marcar semeada uma busca que falhou faria a execução seguinte notificar o catálogo inteiro, exatamente o que a semeadura existe para evitar | Semeadura global por banco vazio (adicionar uma segunda busca depois notificaria tudo dela) | 🟡 |
| D-21 | O registro da execução nasce antes de tudo que pode falhar: trava → banco → `INSERT execucao` → configuração → coleta → … → `UPDATE execucao` num bloco `finally`. Configuração inválida é registrada como execução com veredito `falha` e motivo, sem nenhuma requisição | RF-12 da feature e RNF-03 do `agendador-observabilidade`; cenário "configuração inválida aborta antes de tocar a rede" continua verdadeiro, porque o SQLite é local | Validar config antes de abrir o banco (falha de config sumiria do histórico) | 🟡 |
| D-22 | Alerta de quebra limitado a 1 por dia por leiloeiro, apurado por consulta a `execucao_leiloeiro.alerta_enviado` no dia corrente | EC-10 do `notificador-telegram` sem tabela nova | Tabela própria de alertas | 🟡 |

### 3.4 Operação e organização do código

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-23 | Pacote `bot_leilao` em layout `src/`, um subpacote por componente das specs; adaptador e parser do Vip em arquivos próprios, registrados pelo id `vip-leiloes` | RNF-02 do `parser-lotes` e RF-12 do `coletor-lotes`; espelhar as specs facilita rastreabilidade SPEC↔CODE | Módulo único; organização por camada técnica | 🟢 |
| D-24 | Id do leiloeiro = nome em minúsculas, sem acento, espaços viram hífen (`Vip Leilões` → `vip-leiloes`); id da busca = `<leiloeiro_id>:<10 primeiros hex do SHA-1 do JSON canônico dos filtros>` | Estável entre execuções e insensível à ordem das chaves (RF-09 do `cadastro-leiloeiros` v1.1) | UUID gerado (não é estável); posição na lista (muda ao reordenar) | 🟡 |
| D-25 | CLI com `argparse`: `varrer` (com `--dry-run`, que imprime o digest e não grava notificados) e `testar-telegram` (envia mensagem de teste) | RF-14 exige o comando manual; `--dry-run` e `testar-telegram` tornam o `onboarding.md` executável sem disparar notificação real nem semear errado | `click`/`typer` (dependência para 2 comandos) | 🟡 |
| D-26 | Log em `logging` da biblioteca padrão, no console e em `dados/logs/bot-leilao.log` com rotação; um filtro substitui por `***` qualquer ocorrência dos valores de `TELEGRAM_BOT_TOKEN` e das variáveis de credencial | RN-08 inclui rastreamento de exceção: só um filtro no handler cobre texto que vem de exceções de terceiros | Confiar em nunca formatar o token (não cobre exceção do `httpx` com a URL do bot, que contém o token) | 🟢 |
| D-27 | Testes nunca tocam a rede: HTML real do Vip capturado uma vez em `tests/fixtures/vip/`, HTTP simulado por `httpx.MockTransport`, banco em arquivo temporário. Os 11 cenários Gherkin do requirements viram testes automatizados | Testes estáveis e repetíveis; capturar o HTML real ancora o parser em evidência, não em suposição | Testes contra o site real (frágeis, e geram tráfego desnecessário) | 🟢 |

## 4. Premissas

Nenhum marcador `[DÚVIDA]` permanece no `requirements.md`. As premissas abaixo vêm de perguntas abertas nas specs que esta feature precisou fechar provisoriamente; cada uma tem dono e momento de revisão.

| Premissa | Origem | Risco se errada |
|----------|--------|-----------------|
| O texto ou a classe de um lote retirado contém "retirad" (D-16) | `requirements.md#9`, achado "lotes retirados continuam listados"; texto exato não capturado | Lote retirado notificado como oportunidade. Mitigação: o parser registra em log toda `situacao` diferente de "Aberto para lances", e a primeira ocorrência real ajusta a regra |
| `procedencia: 4` equivale a `financiamento` no conjunto fechado de `tipos_leilao` (D-15) | `configuracao-veiculos-alvo.md` OQ-01 | Baixo: é a correspondência literal do rótulo "Recuperado Financiamento" |
| A frequência pode ficar sem validação até a feature de agendamento (D-18) | `cadastro-leiloeiros.md` RF-07 e OQ-04 | Baixo: o campo não é lido por nenhum código desta feature |
| Km ausente não elimina (D-19) | `requirements.md` RF-16 não trata ausência | Baixo: o Vip exibe km em todo card observado |

## 5. Delta arquitetural

Greenfield: não há `architecture.md` de legado, então a origem citada é a spec. Todos os componentes são **novos**; a coluna "Recorte" diz até onde cada um é implementado nesta feature.

| Componente | Arquivo de origem | Tipo de mudança | Recorte nesta feature |
|------------|-------------------|-----------------|-----------------------|
| `configuracao-veiculos-alvo` | `_reversa_sdd/sdd/configuracao-veiculos-alvo.md` | componente-novo | Completo, **mais** `quilometragem_maxima` opcional (RF-16 da feature, ainda ausente da spec) |
| `cadastro-leiloeiros` | `_reversa_sdd/sdd/cadastro-leiloeiros.md` v1.3 | componente-novo | Validação completa, incluindo adaptador **e parser** registrados para todo leiloeiro ativo (RF-10 v1.3); só `publico` + `script` são executáveis (D-17); `frequencia` opaca (D-18); aviso de coerência entre `tipos_leilao` dos alvos e o tipo que cada busca produz |
| `coletor-lotes` | `_reversa_sdd/sdd/coletor-lotes.md` v1.1 | componente-novo | Nível `script`, sessão com cookie, paginação, busca atômica, retry, classificação de bloqueio, registro de adaptadores com o adaptador `vip-leiloes`. Sem Apify, sem autenticação |
| `parser-lotes` | `_reversa_sdd/sdd/parser-lotes.md` | componente-novo | Registro de parsers, normalizadores, detecção de quebra, parser `vip-leiloes`. **Acrescenta** `quilometragem`, `situacao` e `retirado` ao `Lote` |
| `motor-filtros` | `_reversa_sdd/sdd/motor-filtros.md` | componente-novo | Completo, **mais** critério de km (RF-16), descarte de retirados (RF-17) e semeadura por busca (D-20) |
| `notificador-telegram` | `_reversa_sdd/sdd/notificador-telegram.md` | componente-novo | Completo, com alerta limitado a 1 por dia por leiloeiro (D-22) |
| `agendador-observabilidade` | `_reversa_sdd/sdd/agendador-observabilidade.md` | componente-novo | **Parcial**: trava, histórico de execução e alerta de quebra. Fora: disparo agendado (RF-01), alerta de taxa de 30 dias (RF-06), recomendações de frequência (RF-07 a RF-10), relatório de saúde (RF-11) |
| `onboarding-leiloeiro-assistido` | `_reversa_sdd/sdd/onboarding-leiloeiro-assistido.md` | — | Fora desta feature |
| CLI `bot_leilao` | `requirements.md` RF-14 | contrato-novo | Comandos `varrer` e `testar-telegram` |

**Divergências entre a feature e as specs que o `/reversa-sync` deverá convergir depois da entrega:** `quilometragem_maxima` no `VeiculoAlvo`; `quilometragem`, `situacao` e `retirado` no `Lote`; critério de km e descarte de retirados no `motor-filtros`; tabelas `busca_semeada` e `execucao_busca` (ver `data-delta.md`).

**Lições já levadas às specs em 2026-10-03, por valerem para qualquer leiloeiro:** identificador único no leiloeiro e sinônimos de marca (`parser-lotes` v1.1), busca ampla (`cadastro-leiloeiros` v1.2), lista de armadilhas conhecidas para o onboarding de cada leiloeiro novo (`onboarding-leiloeiro-assistido` v1.1).

### Caminhos que a codificação vai tocar

Use esta lista para liberar `.reversa/reversa-config.json` (ação exclusiva do Rafael), caso prefira restringir em vez de liberar o projeto inteiro:

```json
{
  "version": 1,
  "allowLegacyEdits": true,
  "allowedPaths": ["src/**", "tests/**", "scripts/**", "config/**", "pyproject.toml", ".env.example", ".gitignore", "README.md"]
}
```

`dados/` é criado pelo próprio programa em tempo de execução e não precisa estar na lista.

## 6. Delta no modelo de dados

- Resumo das mudanças: quatro objetos de configuração e domínio ganham campos que a feature exige e as specs ainda não têm (`VeiculoAlvo.quilometragem_maxima`, `Lote.quilometragem`, `Lote.situacao`, `Lote.retirado`); o SQLite nasce com cinco tabelas — as três das specs (`lote_conhecido`, `execucao`, `execucao_leiloeiro`) e duas novas (`execucao_busca`, para o registro por busca exigido pelo RF-10 do `coletor-lotes`, e `busca_semeada`, para a semeadura). `LoteNotificado` da spec vira `lote_conhecido` com coluna `origem`, porque guarda também os lotes semeados, que nunca foram notificados.
- Detalhe completo em: `_reversa_forward/001-mvp-varredura-ponta-a-ponta/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Pesquisa do Vip Leilões | HTTP (consumido) | `_reversa_forward/001-mvp-varredura-ponta-a-ponta/interfaces/vip-pesquisa.md` |
| Telegram Bot API, `sendMessage` | HTTP (consumido) | `_reversa_forward/001-mvp-varredura-ponta-a-ponta/interfaces/telegram-bot-api.md` |
| `config/veiculos-alvo.yaml`, `config/leiloeiros.yaml`, `.env` | arquivo (fornecido pelo Rafael) | `_reversa_forward/001-mvp-varredura-ponta-a-ponta/interfaces/arquivos-configuracao.md` |
| Linha de comando `python -m bot_leilao` | CLI (exposto) | `_reversa_forward/001-mvp-varredura-ponta-a-ponta/interfaces/cli.md` |

## 8. Plano de migração e sequência de construção

Migração: n/a. Não há sistema anterior nem dado a converter; o banco é criado na primeira execução.

Sequência de construção sugerida ao `/reversa-to-do`. Cada etapa termina com testes verdes e não depende de rede, exceto a primeira e a última:

1. **Fundação e evidência:** `pyproject.toml`, layout `src/`, `.env.example`, `.gitignore` com `dados/`; captura única do HTML real do Vip (home, pesquisa sem filtro com mais de uma página, pesquisa filtrada) para `tests/fixtures/vip/`.
2. **Configuração:** `configuracao-veiculos-alvo`, `cadastro-leiloeiros` e validação do `.env`, com arquivos de exemplo e todas as rejeições citando alvo, leiloeiro e campo.
3. **Persistência:** conexão, migrações por `user_version`, repositórios das cinco tabelas, trava de execução.
4. **Coleta:** núcleo do coletor (sessão, espaçamento, retry, veredito, busca atômica, teto de páginas) e adaptador `vip-leiloes`, testados com `MockTransport`.
5. **Parsing:** normalizadores, detecção de quebra e parser `vip-leiloes` contra as fixtures.
6. **Filtragem:** critérios de RN-01, retirados, deduplicação, semeadura e contagens.
7. **Notificação:** formatação do digest e do alerta, escape HTML, divisão em 4096 caracteres, envio com retry e confirmação.
8. **Orquestração e CLI:** pipeline com registro garantido em `finally`, `varrer`, `--dry-run` e `testar-telegram`; os 11 cenários Gherkin como testes de ponta a ponta.
9. **Execução real:** onboarding com o Rafael, seguindo `onboarding.md` (semeadura e depois digest real).

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| O Vip muda o HTML do card ou da paginação | médio | alta | Parser isolado em arquivo próprio; RF-07 e RF-08 do `parser-lotes` transformam a mudança em alerta, não em silêncio; fixtures reais tornam o conserto verificável |
| Cloudflare passa a desafiar o acesso automatizado | alto | média | Classificado como `bloqueado` (RF-08 do `coletor-lotes`), registrado em `execucao_busca` como evidência para escalar `nivel_coleta`; não há contorno de desafio (NG-03) |
| O Vip passa a exigir token antifalsificação no POST | médio | baixa | Não exigido hoje (nenhum `__RequestVerificationToken` no formulário em 2026-10-03). Se surgir, `preparar_sessao` do adaptador passa a extraí-lo do HTML de `/pesquisa/index`, sem tocar no núcleo |
| Token do bot vazar em log por exceção do `httpx` (a URL da API contém o token) | alto | média | Filtro de mascaramento no handler de log (D-26) e teste automatizado que força uma exceção e verifica a ausência do token |
| Texto de "retirado" diferente do previsto (D-16) | médio | média | Log de toda `situacao` não reconhecida; ajuste na primeira ocorrência real |
| Outra grafia de marca no Vip, além de `mmc` e `gm`, deixa um alvo sem casar (D-28) | médio | baixa | O parser registra em log toda marca fora da lista de marcas do formulário do site; o Rafael confere no passo 5 do `onboarding.md` se os candidatos esperados aparecem |
| Encoding ou fim de linha do Windows no YAML | baixo | média | Leitura em UTF-8 com detecção explícita de BOM (EC-08 de `configuracao-veiculos-alvo`) e teste com arquivo CRLF |
| Python antigo no notebook do Rafael | baixo | média | `requires-python = ">=3.12"` no `pyproject.toml`; `onboarding.md` começa verificando a versão |
| Trava órfã após queda da máquina | baixo | baixa | Trava registra o instante e é liberada após 2 h, com registro em log (EC-01 do `agendador-observabilidade`) |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Os 11 cenários de aceitação do `requirements.md#7` passam como testes automatizados, sem acesso à rede
- [ ] RF-01 a RF-18 com ao menos um teste rastreável cada
- [ ] Teste automatizado comprova que o token do bot não aparece no log nem em rastreamento de exceção
- [ ] Uma execução real contra o Vip semeia a base sem notificar, e uma segunda execução, após apagar um lote conhecido, entrega o digest no Telegram do Rafael com link que abre o lote em um toque
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-03 | Versão inicial gerada por `/reversa-plan`, incluindo a verificação dos filtros do Vip que o requirements deixou como primeira ação técnica | reversa |
| 2026-10-03 | Correções do `audit/cross-check.md`: D-30 (cabeçalho de navegador, A002), D-31 (zero resultados legítimos, A001), validação de parser registrado (A003) e aviso de coerência alvos × buscas (A004) | reversa-forward |
