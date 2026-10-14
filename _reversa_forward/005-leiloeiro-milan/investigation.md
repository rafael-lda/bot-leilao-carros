# Investigação: Leiloeiro Milan e nível Apify

> Feature: `005-leiloeiro-milan`
> Data: 2026-10-13
> Gasto com Apify nesta investigação: US$ 0,39 do ciclo (limite US$ 5; ciclo de 18/09 a 17/10)

## 1. O bloqueio

- Todas as requisições do bot ao `milanleiloes.com.br` recebem **403 com o desafio do Cloudflare** ("Just a moment...", `challenge-platform`), inclusive `robots.txt`, `sitemap.xml` e `cdn.milanleiloes.com.br` (2026-10-11 e 2026-10-13). Do container, que sai pela internet da casa do Rafael, também.
- No navegador do Rafael tudo abre, inclusive em janela anônima e sem login.
- Conclusão: o Cloudflare barra **navegador automatizado ou cliente HTTP**, independentemente do IP.

## 2. Existe endereço de dados aberto? Não

| Verificação | Resultado |
|-------------|-----------|
| Subdomínios `api.`, `apiv2.`, `backend.`, `admin.` | não existem no DNS |
| `cdn.milanleiloes.com.br` | existe, também atrás do desafio |
| Wayback Machine | nenhuma cópia das páginas |
| Tráfego da página do leilão (capturado pelo navegador do Apify antes de passar o desafio) | só o desafio |
| HTML renderizado das páginas (agenda, leilão, catálogo, lote) | app Next.js com renderização no servidor; as chamadas `fetch` do código são de marketing (notificações, pop-ups, cadastro), nenhuma de lotes ou lances; sem WebSocket |

Imagens vêm de `adm.milanleiloes.com.br` e de um armazenamento R2; não há listagem de lotes fora do domínio protegido. **O Apify é necessário para o Milan.**

## 3. Escada de acesso testada (2026-10-13)

| # | Ferramenta | IP | Navegador | Resultado | Custo |
|---|------------|----|-----------|-----------|-------|
| 1 | `apify/playwright-scraper` (oficial, permissão limitada) | datacenter EUA | Chromium sem tela | preso em "Just a moment..." por 30 s; Turnstile carregado | ~US$ 0,01 |
| 2 | idem | residencial Brasil | Chromium sem tela | preso | ~US$ 0,01 |
| 3 | idem | residencial Brasil | Chromium com tela | preso | ~US$ 0,01 |
| 4 | idem | residencial Brasil | Firefox com tela | preso | ~US$ 0,01 |
| 5 | `pamberton/cloudflare-bypass` (loja, permissão limitada) | residencial Brasil | com tela, impressão digital variável | preso | centavos |
| 6 | `neatrat/cloudflare-scraper` (loja, permissão limitada) | do ator | do ator | **status 200**, página completa | US$ 0,08 |

Depois do teste 6, o mesmo ator trouxe a agenda, o catálogo do 15618 e três páginas de lote: **6 de 6 com status 200**.

Atores oficiais `apify/puppeteer-scraper`, `apify/web-scraper` e `apify/cheerio-scraper` exigem **permissão total da conta** (aprovação manual no console): descartados.

Atores da loja com "Cloudflare" no nome (consulta de 2026-10-13): `pamberton/cloudflare-bypass` (153 usuários), `macheta/universal-bypasser` (346), `neatrat/cloudflare-scraper` (149), `scrapers_lat/cloudflare-bypass-scraper` (38), `scrapers_lat/gen5-website-unblocker` (37). Todos com permissão limitada. São as alternativas se o `neatrat` parar (D-88).

## 4. Custo medido

Execuções do `neatrat/cloudflare-scraper` consultadas pela API (`GET /v2/actor-runs/<id>`):

| Página | Duração | Eventos cobrados | Custo |
|--------|---------|------------------|-------|
| catálogo 15618 (1,5 MB) | 20 s | 1 início + 1 item | US$ 0,0805 |
| lote 001 | 14 s | 1 início + 1 item | US$ 0,0804 |

O uso mensal da conta mostra `PAID_ACTORS_PER_EVENT` = US$ 0,32 para as 4 primeiras execuções, ou seja, US$ 0,08 cada, sem cobrança de computação à parte.

Estimativa mensal (13 varreduras: seg, qua e sex às 08h, `scripts/agendar_windows.ps1`):

| Item | Páginas por mês | Custo |
|------|-----------------|-------|
| Agenda, em toda varredura | 13 | US$ 1,04 |
| Catálogo, em toda varredura com leilão de financiamento na agenda (~2 leilões × 2 varreduras) | ~4 | US$ 0,32 |
| Página de lote dos candidatos novos (lance) | ~6 | US$ 0,48 |
| Varreduras manuais com `varrer-completo.bat` | ? | US$ 0,16 a 0,30 cada |
| **Total** | | **~US$ 1,90** (limite do plano gratuito: US$ 5) |

Por que não usar a página do leilão para os lances: ela mostra 20 lotes por vez em 13 páginas, trocadas por botões; o ator só lê a primeira. Ler todos os lances custaria 13 páginas por varredura (~US$ 1,04 a mais por varredura).

## 5. Formatos encontrados

Detalhe em `interfaces/milan.md`. Destaques:

- **Agenda** (`/agenda/veiculos`): 2 leilões em 2026-10-13 (judicial 15595; financiamento 15618 em 14/10 09:30). Data sem ano.
- **Catálogo** (`/leilao/15618/catalogo`): 254 cards numa página; 243 veículos e 11 materiais; km, câmbio, avisos em vermelho, comitente no último parêntese; lance inicial em 54 cards; **sem lance atual**.
- **O catálogo muda**: 247 lotes no PDF de 2026-10-11, 254 cards em 2026-10-13, com lotes de sufixo `A` (015A, 047A, 074A, 091A, 195A). Por isso o catálogo é lido em toda varredura (D-94).
- **Lote** (`/leilao/15618/lote/<n>`): lance atual (`R$ 66.200,00`; ou `R$ ---` sem lance, caso do Creta 046), lance inicial quando houver (209), estado ("RECEBENDO LANCES"), final da placa, km, câmbio.
- **Marcas** no catálogo fora da tabela comum: `M-BENZ` (18), `CINTROEN` (1, erro de digitação), `LAND` (4, é "LAND ROVER"), `JAGUAR` (2); além de reboques e tratores, que não casam com alvo nenhum.
- **Pátio**: o cabeçalho traz "Rod. Raposo Tavares - Km 20 …", sem cidade; o rodapé traz o endereço do Milan em "São Paulo - SP"; nenhum lote cita outro local.

## 6. Antecedência dos anúncios

Pedido do Rafael: com quantos dias de antecedência o Milan divulga os leilões.

| Fonte | Achado |
|-------|--------|
| Agenda de 2026-10-13 | nenhum leilão de financiamento depois de 14/10 anunciado |
| Prints e PDF do Rafael | o 15618 já estava na agenda e com catálogo em 2026-10-11: **pelo menos 3 dias** |
| [IstoÉ Dinheiro, 01/06/2021](https://istoedinheiro.com.br/bancos-e-seguradoras-leiloam-45-veiculos-nesta-quarta-feira-2) | matéria da véspera de um leilão da Milan (mede a imprensa, não a agenda) |
| [Gazeta SP](https://www.gazetasp.com.br/economia/plataforma-realiza-leilao-de-veiculos-recuperados/1135500) | leitura recusada (403) |

Sem histórico confiável. Decisão: o bot mede sozinho (tabela `evento_visto`, D-102).

## 7. Alternativas de desenho avaliadas

| Alternativa | Por que não |
|-------------|-------------|
| Chrome automatizado no notebook do Rafael | O teste 3 (navegador com tela, IP residencial) mostra que o Cloudflare barra o navegador automatizado; passar exigiria disfarce no código, contra a regra anti-bot (RN-07), com manutenção a cada mudança do Cloudflare |
| Reaproveitar o `cf_clearance` devolvido pelo ator no `httpx` | O cookie fica preso ao IP e ao navegador do ator; seria também um remendo no código |
| Rafael salvar o catálogo numa pasta | Funciona, mas é passo manual recorrente (preferência por automação total) |
| Ler o catálogo uma vez por leilão | Perde lotes inseridos depois (247 → 254 em dois dias) |
| Lances pela página do leilão | 13 páginas por varredura; o ator não clica na paginação |
| Troca automática `script` → `apify` (RF-07) agora | O ator só faz GET de URL sem corpo nem cabeçalhos; Copart (POST JSON) e Kuss (POST) não passariam; nenhum leiloeiro em `script` está bloqueado. Adiada (D-92) |

## 8. Fontes

- Execuções e consultas à API do Apify em 2026-10-13 (`/v2/acts/...`, `/v2/actor-runs/...`, `/v2/users/me/limits`, `/v2/users/me/usage/monthly`, `/v2/store?search=cloudflare`)
- Amostras em `amostras/` (respostas do ator)
- [Apify API: run Actor synchronously and get dataset items](https://docs.apify.com/api/v2/act-run-sync-get-dataset-items-post)
- [Apify Store: neatrat/cloudflare-scraper](https://apify.com/neatrat/cloudflare-scraper)
