# Contrato: Freitas Leiloeiro (busca pública)

> Feature: `004-leiloeiro-freitas`
> Observado em: 2026-10-13, sem login, `User-Agent` de navegador (D-30 da 001), 5 s entre requisições
> Amostras reais: `../amostras/`
> Confidência: 🟢 observado, 🟡 inferido

## 1. Visão geral

| Item | Valor |
|------|-------|
| Base | `https://www.freitasleiloeiro.com.br` 🟢 |
| Proteção | GoCache (cabeçalho `server: gocache`); em 2026-10-13, 9 requisições sem bloqueio 🟢. Em 2026-10-10 houve "Acesso Bloqueado" 🟡 |
| Certificado | **Cadeia errada no servidor:** o certificado `*.freitasleiloeiro.com.br` é emitido por "GlobalSign GCC R6 AlphaSSL CA 2025", mas o servidor envia o intermediário "AlphaSSL CA - SHA256 - G2" (de outra cadeia). Clientes sem o intermediário certo falham com `unable to get local issuer certificate`. O intermediário oficial (`http://secure.globalsign.com/cacert/gsgccr6alphasslca2025.crt`, SHA-256 `A8:83:55:92:31:F8:38:8D:AF:35:CE:41:C8:10:10:40:AE:8F:D9:B6:56:43:42:47:B9:47:5A:F5:92:CC:08:CA`, válido até 2027-05-21) completa a cadeia até a GlobalSign Root R6, que já está no pacote `certifi`. Verificado também sem `VERIFY_X509_PARTIAL_CHAIN` (comportamento do Python 3.12) 🟢 |
| `robots.txt` | inexistente (404) 🟢 |
| Login | não exigido para busca e detalhe 🟢 |
| Sessão | nenhuma 🟢 |

## 2. Busca: `GET /Leiloes/PesquisarLotes`

Chamada pela página `/Leiloes/Pesquisar?query=&categoria=1` via `$.ajax` (query string). Cabeçalhos: `X-Requested-With: XMLHttpRequest`, `Referer: <base>/Leiloes/Pesquisar?query=&categoria=1`.

| Parâmetro | Valor usado | Nota |
|-----------|-------------|------|
| `Categoria` | `1` | veículos (2 imóveis, 3 materiais) |
| `Condicao` | `inteiros` | opções do site: `0` (todos), `inteiros`, `sinistros e sucatas`, `pequena monta`, `media monta`, `sucatas` |
| `TipoLoteId`, `FaixaValor`, `PatioId`, `AnoModeloMin`, `AnoModeloMax`, `ClienteSclId` | `0` | sem filtro |
| `Nome`, `Tag`, `Estado`, `Cidade` | vazio | sem filtro |
| `ArCondicionado`, `DirecaoAssistida` | `false` | |
| `PageNumber` | `1`, `2`, ... | base 1 |
| `TopRows` | `200` | aceito (o site usa 12) 🟢 |

**Resposta:** HTML parcial (`text/html`), uma `div.cardlote` por lote. Fim da busca: `<div class="alert ...">Nenhum lote localizado com os filtros aplicados!</div>` (113 bytes). 2026-10-13: 225 lotes "inteiros" (200 + 25) e a página 3 com o fim.

### Card do lote

| Elemento | Exemplo | Uso |
|----------|---------|-----|
| `.cardLote-lote` | `003`; `<span>X</span>` em loteamento | número exibido |
| link `LoteDetalhes?leilaoId=8112&loteNumero=1` | | id e link (D-78) |
| `.cardLote-logoCliente` `LogosClientes/<n>.JPG` | `450` | logo do comitente (id numérico, sem nome) — não usado |
| `.cardLote-data` (dois `span.fw-bold`) | `16/10/2026` `10:00` | pregão (Brasília) |
| `.cardLote-descVeic span` | `RENAULT/DUSTER INTP CVT, 23/24, PLACA: S__-___4, GASOL/ALC, PRATA` | sempre 5 partes: bem, ano `AA/AA`, placa parcial, combustível, cor (225 de 225) |
| `.cardLote-vlr` + `.cardLote-lance` | `R$ 50.500,00` + `Maior lance` / `Lance Inicial` | preço (D-80) |
| `.cardLote-details span` | `FINANCEIRA` (ou vazio) | tipo de leilão do lote (D-76) |
| `.cardLote-btn` | `ABERTO PARA LANCES` / `EM LOTEAMENTO` | estado (D-77) |

Grafias de marca (censo de 225): `VW`, `I/...` (importado, às vezes sem barra entre marca e modelo: `I/NISSAN SENTRA 20S FLEX`, `I/RAM 2500`), `GM`, `CHEV`, `CHEVROLET`, `M.BENZ`, `MMC`.

## 3. Detalhe: `GET /Leiloes/LoteDetalhes?leilaoId=<id>&loteNumero=<n>`

HTML completo (~85 KB). Usado só no enriquecimento (lotes novos e semeados).

| Informação | Onde | Exemplo |
|------------|------|---------|
| Pátio | texto "Visitação/Retirada: ... - CIDADE/UF" | `AV. DOS ESTADOS, 584 - PORTÃO 2 UTINGA - SANTO ANDRE/SP` → `SANTO ANDRE - SP` |
| Despesas | "Despesas operacionais no valor de R$ 2.350,00"; às vezes "Despesas de logística no valor de R$ 350,00" | soma |
| Selos do lote | `div.small.mt-2 span.fw-bolder` | `IPVA 2026 PAGO` |
| Id interno estável | `var loteId = parseInt('797418')` | não usado nesta feature (D-77) |
| Estado | "Maior lance: ABERTO PARA LANCES" / "EM LOTEAMENTO" | |
| Comissão | "5% referente à comissão do leiloeiro" | conhecido; não lido |

O pátio e as despesas **variam por leilão** (8103 e 8111: Santa Bárbara d'Oeste-SP; 8112: Santo André-SP; 8111 com logística de R$ 350).

## 4. Erros, idempotência e conduta

- Só leitura. Página sem cards e sem a mensagem de fim → quebra (alerta).
- Falha de certificado → `falha_rede` com motivo `certificado: ...` e alerta (D-84, D-85).
- Varredura típica: 3 requisições de busca + 1 por lote detalhado; 5 s por host.
