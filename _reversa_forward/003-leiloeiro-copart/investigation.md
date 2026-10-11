# Investigation: Leiloeiro Copart

> Feature: `003-leiloeiro-copart`
> Data: 2026-10-11
> Fontes: CSV exportado e prints do Rafael (janela anônima), scripts do próprio site (`controllers.js`, `serverSideDataTableJs.js`), 35 requisições à busca pública, amostras em `amostras/`

## 1. Como a busca foi encontrada

1. A página `/vehicleFinderSearch` respondeu 200 sem desafio do Imperva (na triagem de 10/10, a página inicial tinha sido barrada).
2. O HTML é só a casca de um app AngularJS; os lotes vêm por chamada de dados.
3. Em `controllers.js`: `if (url.indexOf("/vehicleFinderSearch") != -1) return "/public/vehicleFinder/search"`.
4. Em `serverSideDataTableJs.js`: o corpo é o padrão do DataTables (formulário), com `data.filter = {chave: "chave:\"valor\""}`, `data.query`, `data.sort` e campos de página.
5. Testes: corpo JSON foi ignorado; formulário com `filter[condicao]` filtrou (1.506); `size=100` aceito.
6. O botão "Exportar" gera o CSV **no navegador** (SheetJS) a partir do mesmo JSON: não há arquivo pronto a baixar com mais dados.

## 2. Teste realista pedido pelo Rafael

| Leitura | Ordenação | Páginas | Lidos | Únicos | Tempo | Desafios |
|---------|-----------|---------|-------|--------|-------|----------|
| 1 | padrão do site | 16 | 1.506 | **1.470** | 77 s | 0 |
| 2 | `lot_number asc` | 16 | 1.506 | **1.506** | 76 s | 0 |

A primeira leitura mostrou que, sem ordenação explícita, o índice de busca devolve páginas sobrepostas: 36 lotes vieram duas vezes e 36 nunca vieram, com o total "batendo". Daí D-54 e D-55.

## 3. Significado dos campos (armadilha)

| Parece | É | Como foi conferido |
|--------|---|--------------------|
| `fv` = FIPE value | **chassi** (`9BGXH80005C183447`) | 17 caracteres alfanuméricos |
| `la` | **valor FIPE** | Peugeot 2008 2018 = R$ 54.676; o CSV traz "Valor FIPE" nos mesmos lotes |
| `ad` | data do leilão em **UTC** | `2026-10-14 13:00:00` ↔ "14.10.2026 10:00 BRT" no print e no CSV |
| `stt`, `td` | documento (NORMAL, RECUPERÁVEL, IRRECUPERÁVEL) | coluna "Documento" do CSV |
| `currentHighBidder` | número de cadastro de quem deu o maior lance | dado de terceiro; não lido |

## 4. Volume e geografia (financiamento, 2026-10-11)

- 1.506 lotes: 688 automóveis, 295 motos, 148 SUVs pequenos, 108 picapes grandes, 88 caminhões...
- Só 86 com data marcada (14 a 19/10); 1.420 aguardando classificação (sem data, FIPE nem lance).
- Pátios: PE 497, CE 415, GO 286, MT 86, AM 57, SP 45, BA 34, **PR 31**, MS 31.
- Casam com os alvos atuais (ano na faixa): 13 lotes (Duster e Duster Oroch 2018–2022, Kicks 2019, Versa 2017 e 2019).

## 5. Alternativas avaliadas

| Alternativa | Veredito |
|-------------|----------|
| **Busca JSON pública, nível `script`** | Escolhida |
| CSV exportado pelo Rafael | Descartada: passo manual recorrente (preferência por automação máxima) |
| Robô logado | Desnecessário: a busca é pública |
| Apify desde já | Desnecessário hoje; vira degrau automático com o Milan (backlog item 9) |

## 6. Armadilhas para a lista do onboarding (para o `/reversa-sync`)

- `paginacao_instavel`: índice de busca sem ordenação estável repete e omite itens entre páginas com o total correto. Conferir números únicos, não só o total.
- `campo_enganoso`: nomes abreviados de campo (`fv`, `la`) que não significam o que parecem; conferir com uma fonte humana (CSV, tela).
- `data_em_utc`: datas sem fuso explícito podem estar em UTC.
