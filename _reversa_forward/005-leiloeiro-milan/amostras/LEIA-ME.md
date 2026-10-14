# Amostras reais do Milan (via Apify)

Capturadas em 2026-10-13, entre 19h e 22h (horário de Brasília), pelo ator `neatrat/cloudflare-scraper` (`POST /v2/acts/neatrat~cloudflare-scraper/run-sync-get-dataset-items`). Cada arquivo é a **resposta da API do Apify** (lista com um item), no formato que o `ClienteApify` recebe; o HTML da página está no campo `content`.

Tratamento antes de guardar:
- campo `cookies` removido (inclui `cf_clearance` e rastreadores do site);
- apelidos mascarados de quem deu lance (ex.: `W*****é`) trocados por `U*****1`.

| Arquivo | Página | Para que serve |
|---------|--------|----------------|
| `apify_agenda-veiculos.json` | `/agenda/veiculos` | 2 leilões: judicial 15595 (fora) e 15618 "recuperados de financiamento" (14/10 09:30) |
| `apify_catalogo-15618.json` | `/leilao/15618/catalogo` | 254 cards (243 veículos, 11 materiais); km, câmbio, avisos em vermelho, comitente, 54 lances iniciais |
| `apify_lote-15618-001_lance-atual.json` | `/leilao/15618/lote/001` | Ford Ranger com lance atual R$ 66.200,00 |
| `apify_lote-15618-046_creta-sem-lance.json` | `/leilao/15618/lote/046` | Hyundai Creta 2022 automático (Banco Honda), lance `R$ ---` (sem lance) |
| `apify_lote-15618-209_lance-inicial-e-atual.json` | `/leilao/15618/lote/209` | Renault Duster 2013 com lance inicial R$ 21.500,00 e atual R$ 22.400,00 |
| `apify_leilao-15618-pag1.json` | `/leilao/veiculos/15618` | Página do leilão (20 primeiros lotes com lance). Não usada pelo bot (D-97); só referência |

Erro de token inválido (sem custo), para o teste do `ClienteApify`:

```
HTTP 401
{"error": {"type": "user-or-token-not-found", "message": "User was not found or authentication token is not valid"}}
```
