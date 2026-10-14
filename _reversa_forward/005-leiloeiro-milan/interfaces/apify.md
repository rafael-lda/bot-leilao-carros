# Contrato: Apify (nível de coleta `apify`)

> Feature: `005-leiloeiro-milan`
> Data: 2026-10-13
> Decisões: D-86 a D-91 (`roadmap.md` §3.1)
> Amostras: `../amostras/apify_*.json` (respostas reais do ator, com apelidos de licitantes anonimizados e sem cookies)

## 1. Papel

O bot não fala com o site do Milan. Ele pede à plataforma Apify que um **ator** (programa hospedado na loja do Apify) abra a URL num navegador capaz de passar pelo desafio do Cloudflare e devolva o HTML renderizado. O `ClienteApify` expõe a mesma operação do `ClienteHTTP` (`requisitar(Requisicao) -> ResultadoHTTP`), então adaptador, parser e enriquecimento não sabem por onde a página veio.

Restrição do ator: **só GET de uma URL**, sem corpo e sem cabeçalhos próprios. Requisição com `metodo != "GET"` ou com `dados` é recusada pelo cliente antes da rede (erro interno do adaptador, nunca uma chamada paga).

## 2. Ator em uso

| Campo | Valor |
|-------|-------|
| Ator | `neatrat/cloudflare-scraper` (título na loja: "Cloudflare Scraper - Bypass All Captchas") |
| Permissão | `LIMITED_PERMISSIONS` (não acessa o resto da conta) |
| Modelo de preço | por evento: `apify-actor-start` US$ 0,05 + `apify-default-dataset-item` US$ 0,03 = **US$ 0,08 por página** (medido em 4 execuções de 2026-10-13; o evento `page` não foi cobrado) |
| Duração observada | 14 s a 20 s por página |
| Configuração | `apify_ator` no bloco do leiloeiro; ausente = `neatrat/cloudflare-scraper` |

Perfil do ator no código (`PERFIS_ATOR`, D-88):

| Perfil | Entrada | Saída (item 0 do dataset) |
|--------|---------|---------------------------|
| `neatrat/cloudflare-scraper` | `{"url": "<url>"}` | `content` (HTML renderizado), `status` (status HTTP que o navegador viu), `success` (bool), `url`, `timestamp`, `userAgent`, `cookies` (ignorado e nunca gravado) |

Um `apify_ator` sem perfil aborta a configuração antes da rede, citando os perfis conhecidos.

## 3. Chamada de página

```
POST https://api.apify.com/v2/acts/neatrat~cloudflare-scraper/run-sync-get-dataset-items?timeout=180
Authorization: Bearer <APIFY_TOKEN>
Content-Type: application/json

{"url": "https://milanleiloes.com.br/leilao/15618/catalogo"}
```

- O token vai **só** no cabeçalho `Authorization`, nunca na URL (a URL aparece em log).
- O `/` do nome do ator vira `~` no caminho.
- `timeout=180`: tempo máximo da execução no Apify; o `httpx` do cliente espera 200 s.
- Resposta de sucesso: **HTTP 201**, corpo JSON = lista de itens do dataset (um item por URL).

## 4. Tradução para `ResultadoHTTP`

| Situação | Veredito | Motivo | Nova tentativa? |
|----------|----------|--------|-----------------|
| 201, item com `status` 200 e sem marcas da página de desafio (`Just a moment`, `cf-chl`, `Performing security verification`) | `OK` | — | — |
| 201, item com `status` 403/503 ou marcas de desafio no `content` | `BLOQUEADO` | `desafio_antibot (via apify: <ator>)` | sim, 1 vez |
| 201, item com `status` 404 | `FALHA_REDE` | `http_404 (via apify)` | não |
| 201, lista vazia ou item sem `content` | `FALHA_REDE` | `apify: sem resultado` | sim, 1 vez |
| 401, `error.type = user-or-token-not-found` (verificado 2026-10-13) | `FALHA_AUTENTICACAO` | `apify: token inválido` | não |
| 402 ou 403 com `error.type` de cota/limite (`not-enough-usage-to-run-paid-actor`, `monthly-usage-limit-exceeded`, ou mensagem com "usage"/"limit") 🟡 | `FALHA_REDE` | `apify: cota esgotada` | não |
| 408, ou timeout do `httpx` | `FALHA_REDE` | `apify: tempo esgotado` | sim, 1 vez |
| 5xx ou erro de conexão com `api.apify.com` | `FALHA_REDE` | `apify: plataforma indisponível` | sim, 1 vez |
| Outro status | `FALHA_REDE` | `apify: http_<status> (<error.type>)` | não |

- **`challenge-platform` não é marca de desafio aqui:** as páginas liberadas do Milan também carregam esse script do Cloudflare (5 de 5 amostras de 2026-10-13). O nível `script` continua usando a marca (lá ela só aparece com 403/503).
- No máximo **2 tentativas** por página. Cada tentativa é uma execução nova e custa (US$ 0,05 a 0,08), por isso nunca se repete token inválido nem cota esgotada.
- `ResultadoHTTP.url` é a URL do site (não a da API), para o parser montar links.
- O espaçamento mínimo de 5 s por host do site continua valendo (as execuções já levam mais que isso).

## 5. Consumo do ciclo (D-91)

```
GET https://api.apify.com/v2/users/me/limits
Authorization: Bearer <APIFY_TOKEN>
```

Campos usados (verificados em 2026-10-13):

| Campo | Exemplo | Uso |
|-------|---------|-----|
| `data.current.monthlyUsageUsd` | `0.39` | gasto do ciclo |
| `data.limits.maxMonthlyUsageUsd` | `5` | limite do plano |
| `data.monthlyUsageCycle.endAt` | `2026-10-17T23:59:59.999Z` | fim do ciclo (o ciclo desta conta vai do dia 18 ao dia 17) |

Chamado na primeira página paga da varredura e no fim dela: a diferença é o gasto da varredura. **Atraso de cobrança:** o evento por item (US$ 0,03) entra no uso da conta alguns segundos depois da execução; a consulta do fim da varredura pode mostrar só o início (US$ 0,05 por página). O gasto do ciclo acerta na varredura seguinte (dry-run real de 2026-10-14). A chamada não custa. Falha nessa consulta não derruba nada: o relatório diz "consumo indisponível".

## 6. Idempotência e efeitos

- Não idempotente em custo: cada POST cria uma execução nova e cobra.
- Sem efeito no site além de uma visita de navegador.
- O ator devolve cookies do site (inclusive `cf_clearance`): o cliente descarta, sem log nem gravação.

## 7. Alternativas verificadas em 2026-10-13 (detalhe em `investigation.md`)

| Ator ou caminho | Resultado |
|-----------------|-----------|
| `apify/playwright-scraper`, IP de datacenter (EUA), sem tela | preso em "Just a moment..." 30 s |
| idem, IP residencial Brasil, sem tela / com tela / Firefox com tela | preso nas três |
| `pamberton/cloudflare-bypass`, residencial Brasil, com tela | preso |
| `neatrat/cloudflare-scraper` | **200 em 6 de 6 páginas** (agenda, leilão, catálogo, 3 lotes) |
| `apify/puppeteer-scraper`, `apify/web-scraper` | exigem permissão total da conta; não usados |
