# Contrato: Milan Leilões

> Feature: `005-leiloeiro-milan`
> Data: 2026-10-13
> Decisões: D-93 a D-97 (`roadmap.md` §3.2)
> Base: `https://milanleiloes.com.br` (Next.js; Cloudflare "managed" no site inteiro). Todas as páginas vêm pelo Apify (`interfaces/apify.md`).
> Amostras: `../amostras/apify_*.json` (campo `content` = HTML renderizado)

## 1. Sequência por varredura

```
pág 1      GET /agenda/veiculos                 agenda: escolhe os leilões "recuperados de financiamento"
pág 2..n   GET /leilao/<id>/catalogo            um por leilão escolhido, em toda varredura (D-94)
detalhe    GET /leilao/<id>/lote/<n>            só para candidatos (novos e semeados), pelo enriquecimento (D-97)
```

Custo típico: 1 agenda + 1 catálogo por leilão + 1 página por candidato novo, a US$ 0,08 cada.

Não usado: a página do leilão `/leilao/veiculos/<id>` (lance atual de 20 lotes por vez, paginação por botões que o ator não clica; amostra guardada só como referência).

## 2. Agenda: `GET /agenda/veiculos`

- Um card por leilão: `a[href^="/leilao/veiculos/"]`; id = número final do `href` (`/leilao/veiculos/15618` → `15618`).
- Texto do card (amostra de 2026-10-13):
  - `Sexta, 09 de OUT às 14:00 Leilão Judicial - Styro-eme Comercio e Industria de Plasticos Eireli e outro 1ª PRAÇA - 09 OUT 14:00 …` → fora
  - `Quarta, 14 de OUT às 09:30 LEILÃO DE VEÍCULOS DIVS. COMITENTES - RECUPERADOS DE FINANCIAMENTO Recebendo Lances` → escolhido
- Seleção: texto normalizado (minúsculas, sem acento) contém o filtro `descricao_contem` da busca (`recuperados de financiamento`).
- Data e hora: `<dia> de <MÊS> às HH:MM`, mês em 3 letras (JAN FEV MAR ABR MAI JUN JUL AGO SET OUT NOV DEZ), **sem ano**: ano da coleta; se a data cair mais de 60 dias antes da coleta, ano seguinte. Horário de Brasília (offset fixo, como D-22).
- Nenhum leilão escolhido: busca vazia (não é quebra). Página sem nenhum card `a[href^="/leilao/veiculos/"]` e sem o texto "leilões encontrados": quebra.

## 3. Catálogo: `GET /leilao/<id>/catalogo`

Uma página com **todos os lotes** do leilão (15618: 254 cards em 2026-10-13, contra 247 lotes no PDF de 2026-10-11).

Cabeçalho: `Início: 14 OUT 09:30` (pregão; mesma regra de ano da agenda) e o local (`Rod. Raposo Tavares - Km 20, acesso pelo km 19,5 …`; visitação "no local do leilão").

Card de lote: `div.card` (classes `card mb-3`), com:

| Parte | Seletor / padrão | Exemplo |
|-------|------------------|---------|
| Número | texto `Lote <n>` no `span.badge` | `001`, `015A` |
| Título | `h5.card-title` | `I/FORD RANGER XLS 2.2 4X4 CD DIESEL 4P ANO 2021/2022` |
| Descrição | `p.card-text` | `KM: 22, COM AR, COM DIREÇÃO, COM SOM, AUTOMATICO … (FORD).` |
| Avisos do estado | elementos com `style` contendo `color:red`, dentro do card | `VEÍCULO NÃO FUNCIONA, MOTOR VIRA MAS NÃO PEGA` |
| Lance inicial | `p[id^="card_lote_lanceMinimo"]` | `LANCE INICIAL: R$ 21.500,00` (54 de 254) |

Regras de conversão (D-95):

| Campo do lote | Regra |
|---------------|-------|
| é veículo? | título com `ANO \d{4}/\d{4}`; senão descartado (materiais, equipamentos), contagem no log (11 em 15618) |
| `marca` | tira `I/` do começo (pode repetir: `I/I/TOYOTA`); marca de duas palavras quando as duas primeiras formam uma marca conhecida (`LAND ROVER`, `CAOA CHERY`, `ALFA ROMEO`); senão a primeira palavra; depois `marca_canonica` (sinônimos novos: `m-benz`, `cintroen`) |
| `modelo` | o resto do título até ` ANO ` |
| `ano_fabricacao`, `ano_modelo` | `ANO AAAA/AAAA` |
| `quilometragem` | `KM: 99.020` → 99020 (234 de 243 veículos; sucatas e reboques sem km) |
| `cambio` | descrição com `AUTOMATICO`/`AUTOMÁTICO` → `automático`; `CAMBIO MANUAL` ou `, MANUAL` → `manual`; `CVT` → `CVT`; senão `None` (80 / 94 / 69 em 15618) |
| `observacoes` | avisos em vermelho, na ordem; selo `IPVA AAAA PAGO` quando houver; `Comitente <X>` do **último parêntese** da descrição (`(Banco Honda).` → `Comitente Banco Honda`); separador ` · ` |
| `situacao` | `sucata` quando o título tem `(SUCATA)` |
| `lance_inicial` | o valor de `LANCE INICIAL` do card, quando houver |
| `tipo_leilao` | `financiamento` (herança do leilão escolhido, RN-02) |
| `id_canonico` | `milan-leiloes:<id do leilão>-<número do lote>` |
| `link` | `https://milanleiloes.com.br/leilao/<id>/lote/<número>` |
| `numero_lote`, `evento_id`, `pregao_em` | do card e do cabeçalho |
| `patio` | `Cidade - UF` do local quando o cabeçalho trouxer; senão a cidade do endereço do Milan no rodapé (`São Paulo - SP`) (D-96) |

Censo de 2026-10-13 (15618): 243 veículos, comitente em 243 de 243 (Grupo Safra 57, Banco Honda 54, Banco PAN 38, Locadora Grillo 17, Ford 11, …), 102 avisos em vermelho, 2 sucatas, 5 lotes com sufixo `A`.

Quebra: página sem nenhum card de lote e sem o cabeçalho `Início:`; ou card de veículo sem título.

## 4. Lote: `GET /leilao/<id>/lote/<n>` (detalhe)

| Parte | Seletor / padrão | Exemplo |
|-------|------------------|---------|
| Lance atual | `div[class^="leilao_lote_lanceAtual"]`: `label` "LANCE ATUAL", `p` (apelido mascarado, ignorado), `h4` com o valor | `R$ 66.200,00`; sem lance: `R$ ---` |
| Lance inicial | texto `LANCE INICIAL: R$ …` perto do título, quando houver | `R$ 21.500,00` (lote 209) |
| Estado | `div[id^="estado_lote_tag_estadoLote"]` | `RECEBENDO LANCES` |
| Etiquetas | `ul[class^="leilao_lote_tagsVeiculo"] li` | `2021/2022`, `Final Placa 6`, `22 KM`, `Automático` |

Regras (D-97): valor do lance atual → `lance_corrente`; `R$ ---` → sem lance (continua "preço a confirmar"); lance inicial → `lance_inicial`; estado com `RETIRADO` → `retirado` 🟡 (não observado); `Final Placa N` → `placa_parcial = "final N"`; câmbio da etiqueta preenche `cambio` se o catálogo não trouxe. Página sem o bloco de lance e sem o estado → erro do detalhe (D-49: o lote segue sem detalhe).

Classes do Next.js têm sufixo gerado (`__1nl33`); os seletores usam só o prefixo (`[class^=…]`, `[id^=…]`).

## 5. Privacidade

O site mostra o apelido de quem deu o lance, mascarado (`W*****é`). O parser ignora; as amostras trocam por `U*****1`.
