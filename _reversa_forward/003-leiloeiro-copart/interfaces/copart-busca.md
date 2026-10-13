# Contrato: Copart Brasil (busca pública)

> Feature: `003-leiloeiro-copart`
> Observado em: 2026-10-11, sem login, `User-Agent` de navegador (D-30 da 001), 5 s entre requisições
> Amostras reais: `../amostras/` (número de cadastro do maior lance trocado por `999999`)
> Confidência: 🟢 observado, 🟡 inferido

## 1. Visão geral

| Item | Valor |
|------|-------|
| Base | `https://www.copart.com.br` 🟢 |
| Proteção | Imperva (cabeçalho `x-cdn: Imperva`); em 2026-10-11, 35 requisições (2 leituras completas) passaram sem desafio 🟢. Na triagem de 2026-10-10 a página inicial foi barrada 🟡 |
| Login | não exigido para a busca 🟢 (verificado pelo Rafael em janela anônima e pelo bot) |
| Sessão | **nenhuma** (emenda E001, 2026-10-13): a página `GET /vehicleFinderSearch` passou a receber o desafio do Imperva (status 200), enquanto a busca JSON responde sem sessão 🟢 |
| Área proibida | `/data/...`, `/client/...` (área de membro) — nunca chamar |

## 2. Busca: `POST /public/vehicleFinder/search`

- **Corpo:** `application/x-www-form-urlencoded`
- **Cabeçalhos:** `Accept: application/json, text/javascript, */*; q=0.01`, `X-Requested-With: XMLHttpRequest`, `Origin: https://www.copart.com.br`, `Referer: https://www.copart.com.br/vehicleFinderSearch`

| Campo | Valor | Nota |
|-------|-------|------|
| `query` | `*` | todos os lotes |
| `filter[<chave>]` | `<chave>:"<valor>"` | ex.: `filter[condicao]=condicao:"FINANCIAMENTO"`; vários valores da mesma chave são unidos por vírgula 🟡 |
| `sort` | `lot_number asc` | **obrigatório na prática**: sem ele a ordem muda entre páginas (2026-10-11: 1.506 lidos, só 1.470 únicos) 🟢 |
| `page` | `0`, `1`, ... | página base 0 |
| `size` | `100` | aceito; o padrão do site é 10–20 🟢 |
| `start` | `page × size` | |

Chaves de filtro (facetas devolvidas pelo próprio site): `marca`, `modelo`, `categoria`, `condicaofuncionamento`, `classificacaodano`, `tipodocumento`, `condicao`, `patioveiculo`, `patioleilao`, `anomodelo`, `dataleilao`, `chaves`, `blindado`, `tipovenda` 🟢.

### Resposta

```json
{"returnCode":1,"returnCodeDesc":"Success","data":{
  "query":{"query":["*"],"filter":{"condicao":["condicao:\"FINANCIAMENTO\""]},"sort":["lot_number asc"],"page":0,"size":100,"start":0, ...},
  "results":{"totalElements":1506,"content":[ {lote}, ... ],"facetFields":[...]}}}
```

- Zero resultados: `totalElements: 0`, `content: []` (`amostras/vehicleFinder-search_zero-resultados.json`) 🟢
- `Content-Type: application/json;charset=UTF-8`

### Campos do lote usados (de 72)

| Campo | Exemplo | Significado | Uso |
|-------|---------|-------------|-----|
| `ln` | `1141180` | número do lote (global) | id `copart:<ln>`; link `/lotDetail/<ln>` |
| `mkn` | `RENAULT` | marca | marca (sinônimos) |
| `lm` | `DUSTER OROCH` | modelo | modelo |
| `eng` | `1.6 16V SCE` | motor | título |
| `lcy` / `manufactureYear` | `2022` / `2021` | ano modelo / fabricação | anos |
| `yn` | `VITÓRIA DE SANTO ANTÃO - PE` | **pátio do veículo** ("LOCAL DO VENDEDOR" em 8 lotes) | `patio` |
| `hb` | `36000.0` | lance atual (0 = sem lance) | `lance_corrente` |
| `la` | `"80266.00"` | **valor FIPE** (0 quando aguardando classificação) | `fipe` |
| `ad` | `"2026-10-15 11:30:00"` | data do leilão em **UTC** (vazio sem data; `"Copart Select"` em Compre Agora) | `pregao_em` (convertida para Brasília) |
| `saleType` | `Leilão` / `Compre Agora` | tipo de venda | observação |
| `saleAmountBIN` | `"R$ 141.659,00"` | preço do Compre Agora | `lance_corrente` quando Compre Agora |
| `dd` | `PEQUENOS AMASSADOS` | descrição do dano | observação |
| `stt` / `td` | `NORMAL` / `Aguardando Classificação` | documento | observação |
| `damageClassification` | `Não Aplicável` | monta | observação |
| `drivabilityRating` | `Motor dá partida e engrena` | condição de funcionamento | observação |
| `sellerName` | `AYMORE CFI` | comitente (vazio sem classificação) | observação |
| `lossType` | `FINANCIAMENTO` | condição | conferência |

**Atenção:** `fv` é o **chassi**, não a FIPE. `currentHighBidder` é o número de cadastro de quem deu o maior lance: **não é lido**.

## 3. Página humana do lote

`https://www.copart.com.br/lotDetail/<ln>` 🟢 (formato da coluna "URL de Lote" do CSV exportado).

## 4. Erros, idempotência e conduta

- Só leitura; repetir não altera nada.
- `returnCode != 1`, JSON sem `data.results` ou lote sem `ln`/`mkn` → quebra (alerta).
- Desafio do Imperva (403, página HTML) → `bloqueado` pelo `ClienteHTTP` existente, com alerta; Vip e Kuss seguem.
- 1.506 lotes = 16 páginas ≈ 77 s com 5 s entre requisições (medido duas vezes em 2026-10-11).
