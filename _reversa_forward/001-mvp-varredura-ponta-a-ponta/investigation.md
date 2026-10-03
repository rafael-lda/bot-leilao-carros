# Investigation: MVP de Varredura Ponta a Ponta

> Identificador: `001-mvp-varredura-ponta-a-ponta`
> Data: `2026-10-03`
> Confidência: 🟢 observado ou documentado, 🟡 inferido

## 1. Verificação técnica do Vip Leilões (2026-10-03)

O `requirements.md#10` deixou como "primeira ação técnica do plano" confirmar que o servidor do Vip aplica os filtros de procedência e monta. A verificação foi feita durante este plano, com 6 requisições reais, espaçadas em ≥ 5 s, por sessão de cookies (`curl -c/-b`), limite de 3 redirecionamentos e `User-Agent` de navegador.

| # | Requisição | Resultado | O que estabeleceu |
|---|------------|-----------|-------------------|
| 1 | `GET /` | `200` após 2 redirecionamentos; cookie `__CBCanal` emitido | Preparação de sessão (roadmap D-10) |
| 2 | `GET /pesquisa/index` | `200`; formulário `#formPost`, `POST /pesquisa`, `data-ajax="true"`, 50+ campos `Filtro.*`; nenhum token antifalsificação | Nomes de campo e opções dos `<select>` |
| 3 | `POST /pesquisa?handler=pesquisar` com `Filtro.Marca=NISSAN` | 9 resultados | Endpoint de busca responde HTML parcial |
| 4 | Idem + `Filtro.Procedencia=4` + `Filtro.Monta=1` | 1 resultado | **Servidor aplica os filtros** — pendência fechada 🟢 |
| 5 | `Filtro.Procedencia=4` + `Filtro.Monta=1`, sem marca | 201 resultados, 12 por página, paginação até a 17 | Custo da busca recomendada (roadmap D-29) |
| 6 | Mesmo corpo da #5 em `…&pageNumber=2&handler=pesquisar` | 201 resultados, `CurrentPage=2`, 12 lotes, 0 em comum com a página 1 | Contrato de paginação (roadmap D-13) |

Achados que mudaram o desenho:

- **"Lote: 21" não é identificador global.** É a numeração do lote dentro do evento. O identificador estável é o sufixo numérico da URL do anúncio (`…-310800`), que já tinha sido apontado em `requirements.md#9` (roadmap D-14). 🟢
- **Sinônimos de marca.** O `<select>` de marcas tem `MMC` e `MITSUBISHI`, `GM` e `CHEVROLET` como opções distintas, e cards reais trazem `mmc` (roadmap D-28). 🟢
- **Busca sem marca é viável.** 17 páginas a 5 s cabem com folga no limite de 10 minutos, o que permite manter marca e modelo só nos veículos-alvo (roadmap D-29). 🟢
- **Nenhum lote retirado foi visto** nas 3 páginas lidas: todos "Aberto para lances". A regra de detecção de retirado fica como premissa (roadmap D-16). 🟡
- **O card não informa procedência nem monta**, confirmando `requirements.md#9`; só um selo de imagem com `alt="Financiamento"`, que não aparece em todo card. Daí `tipo_leilao` herdado da busca (roadmap D-15). 🟢
- **O card informa início do pregão** (`Início: 05/10/2026 19:00`) e número de lances. Não há requisito para esses dados; vão para `descricao` sem campo próprio. 🟡

Os HTML obtidos ficaram fora do repositório. A primeira etapa da construção recaptura as mesmas páginas como fixtures de teste (roadmap §8, etapa 1), para que o parser seja escrito contra conteúdo real e atual.

## 2. Alternativas avaliadas

### 2.1 Cliente HTTP

| Opção | A favor | Contra | Veredito |
|-------|---------|--------|----------|
| `httpx` síncrono | `max_redirects` e timeouts por fase nativos; `MockTransport` embutido para testes; mesma biblioteca serve ao Telegram | Uma dependência a mais que `urllib` | **Escolhido** (D-02) |
| `requests` | O mais conhecido | Testes exigem `responses` ou `requests-mock`; limite de redirecionamento por atributo da sessão, menos explícito | Descartado |
| `urllib.request` | Sem dependência | Cookies, redirecionamento limitado e retry à mão; código mais longo para o agente de IA manter | Descartado |
| Navegador automatizado (Playwright) | Executa JavaScript | Pesado; o Vip entrega HTML pronto por POST, sem necessidade de JavaScript | Descartado; reservado ao nível `apify` |

### 2.2 Parsing de HTML

| Opção | A favor | Contra | Veredito |
|-------|---------|--------|----------|
| `beautifulsoup4` + `lxml` | Seletores CSS via `select()`, tolerante a HTML irregular, amplamente conhecido | Mais lento que alternativas em C | **Escolhido** (D-03); 12 cards por página tornam a velocidade irrelevante |
| `selectolax` | Muito rápido | Menos exemplos e menos familiar | Descartado |

### 2.3 Validação de configuração

| Opção | A favor | Contra | Veredito |
|-------|---------|--------|----------|
| `dataclasses` + funções de validação | Mensagem exatamente como a spec pede ("Configuração inválida em 'Nissan Versa': ano_min (2020) é maior que ano_max (2018)") | Mais linhas | **Escolhido** (D-04) |
| `pydantic` v2 | Declarativo, conversão de tipos | Mensagens em formato próprio; traduzir para o texto exigido custa tanto quanto escrever a validação | Descartado |

### 2.4 Envio ao Telegram

| Opção | A favor | Contra | Veredito |
|-------|---------|--------|----------|
| HTTP direto em `sendMessage` | Uma chamada; controle total de retry e confirmação | Escrever o tratamento de erros (pequeno) | **Escolhido** (D-05) |
| `python-telegram-bot` | Abstrações prontas | Assíncrona, voltada a bots que recebem comandos (NG-01 do notificador), esconde a resposta exata que serve de confirmação | Descartado |

Entre os modos de formatação, `HTML` exige escapar 3 caracteres; `MarkdownV2`, 18. Títulos de lote do Vip trazem `-`, `.`, `(` e `/`, todos reservados no `MarkdownV2`.

### 2.5 Trava de execução

| Opção | A favor | Contra | Veredito |
|-------|---------|--------|----------|
| Arquivo criado com `O_CREAT \| O_EXCL`, com PID e instante | Portável, sem dependência, permite a regra de órfã de 2 h | Não é liberado pelo sistema operacional se o processo morrer, daí a regra de órfã | **Escolhido** (D-07) |
| `fcntl.flock` / `msvcrt.locking` | Liberação automática | Um código por sistema operacional | Descartado |
| Linha de trava no SQLite | Mesmo arquivo do histórico | Mistura controle de concorrência com dado; recuperação de órfã fica mais difícil de inspecionar | Descartado |

## 3. Padrões aplicáveis

- **Registro por identificador (registry):** adaptadores de coleta e parsers indexados pelo `leiloeiro_id`. É o que permite ao `cadastro-leiloeiros` recusar leiloeiro sem adaptador (RF-10) e ao agente de IA consertar um site sem tocar nos outros.
- **Unidade de trabalho com confirmação externa:** os lotes notificados só são gravados depois da confirmação do Telegram, numa transação única (RN-06; RNF-02 do `motor-filtros`).
- **Registro garantido em `finally`:** a linha de `execucao` é criada no início e fechada em qualquer desfecho (RF-12; RNF-03 do `agendador-observabilidade`).
- **Falhar cedo, antes da rede:** toda validação de configuração e de ambiente roda antes da primeira requisição.
- **Testes com fixtures reais e transporte simulado:** o parser é testado contra HTML capturado do site, e coletor e notificador contra `httpx.MockTransport`.

## 4. Fontes

- Vip Leilões, home, formulário e endpoint de pesquisa: `https://www.vipleiloes.com.br/`, `/pesquisa/index`, `POST /pesquisa?handler=pesquisar`, observados em 2026-10-03.
- Vip Leilões, `robots.txt` e Termo de Adesão: `requirements.md#9`, sessão de 2026-09-27.
- Telegram Bot API, `sendMessage`, formatação HTML e limites: `https://core.telegram.org/bots/api#sendmessage` e `#formatting-options`.
- HTTPX, clientes, transporte simulado e limites de redirecionamento: `https://www.python-httpx.org/advanced/clients/` e `/advanced/transports/`.
- SQLite, `PRAGMA user_version` e `busy_timeout`: `https://www.sqlite.org/pragma.html`.
