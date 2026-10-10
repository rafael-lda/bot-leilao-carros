# Investigation: Leiloeiro Claudio Kuss

> Feature: `002-leiloeiro-claudio-kuss`
> Data: 2026-10-10
> Fontes: triagem de leiloeiros (`_reversa_forward/triagem-leiloeiros-2026-10-10.md`), JavaScript do próprio site (`lance_video.js`), 9 requisições de verificação durante este plano, amostras em `amostras/`

## 1. Perguntas que o requirements deixou para o plano (§10) e respostas

| Pergunta | Resposta | Como foi verificado |
|----------|----------|---------------------|
| Quais grafias de marca o Kuss usa? | `IMP <marca>` para importados (90 lotes), `SUCATA <marca>` (17), `CHEV` e `CHEVROLET` e `GM`, `VW`, `MMC`, `M BENZ`, `CAOACHERY`, `IMP LR`; `RETIRADO` como `bem` de lote retirado; não veículos sem `/` | Censo das 391 linhas de `relacao-lista/897` e `/898` |
| Página "próximos leilões" ou página inicial para descobrir eventos? | **Agenda** (`/proximos-leiloes`): um bloco por evento com rótulo completo ("... - Veículos - Financeiras"), data e hora e link `relacao-foto/<id>` | Leitura do HTML; os dois eventos de financeiras (897 e 898) aparecem com rótulo e data |
| Quando o lance inicial (`av`) aparece? | Só no endpoint `json_lance_historico.php`, depois do loteamento; antes dele a resposta é `{"status":"Não loteado",...}` sem `av` | Leitura do `lance_video.js` (linhas 270–302) e uma chamada real para o lote 282622 |
| Lotes de um evento aparecem também em outro? | Não verificável hoje (os dois eventos são futuros). Fica como premissa (roadmap §4) | — |
| Formato do ano | `AA/AA` em 387 de 391 lotes; 4 vazios (não veículos) | Censo |
| Quantos lotes têm preço antes do pregão? | 13 de 346 no evento 897, três dias antes | `op=T` do evento 897 |
| O que vem além da última página? | `[]` | `op=P` com `pag=36` no evento 897 (35 páginas) |
| Os alvos atuais aparecem? | Sim: dois Fluence na faixa 2010–2017 (2015 `DYN 20M`, 2013 `DYN 20A`); Sentra 2008 e 2013, Duster 2013 e 2014 fora da faixa de anos | Censo filtrado pelos modelos-alvo |

## 2. Achado que confirma RN-08

O Fluence 2013 automático (seq 282622), único lote automático do Kuss que casa hoje com um alvo, tem no detalhe:

> `tblInformacoes`: "SINISTRADO - NOS DOCUMENTOS CONSTA RECUPERADO DE SINISTRO. REGULARIZAÇÃO POR CONTA DO ARREMATANTE"
> `tblTransf`: "SÃO PAULO"; `tblDespAdm`: "2.750,00"

Ou seja: evento "Financeiras", sem nenhum campo de monta, e o carro é de sinistro com documento de outro estado. Sem as observações no aviso, o Rafael receberia esse lote como se fosse conservado. Isso justifica RF-07 como Must e a inclusão da placa parcial e do estado do documento no relatório (D-50).

## 3. Alternativas de coleta avaliadas

| Alternativa | Requisições por varredura (2 eventos) | Prós | Contras | Veredito |
|-------------|----------------------------------------|------|---------|----------|
| **A. `op=Q` + `op=P` paginado (JSON)** | ~43 (~3,6 min) | JSON, cada página independente, cabe no contrato do parser, é o que a página "com fotos" do site usa | Mais requisições | **Escolhida** (D-33) |
| B. `relacao-lista/<ev>` (HTML) + `op=T` (JSON) | ~5 (~25 s) | Muito menos requisições | Preço só no `op=T`: o parser teria de juntar duas respostas (mudança de contrato no núcleo); HTML de tabela com marcação variável | Saída para quando o volume crescer (R-01) |
| C. `op=P` + detalhe `op=D` de todos os lotes | ~390 (~33 min) | Observações de tudo | Passa do limite de 10 min e é carga desnecessária no site | Descartada |
| D. Página humana `relacao-foto/<ev>` (HTML) | igual a A | — | Os lotes são carregados por JavaScript a partir do `op=P`; o HTML não tem os lotes | Descartada |

Se a alternativa B for necessária, o caminho de menor impacto é o adaptador compor uma "página" a partir das duas requisições (ex.: um método opcional `coletar_pagina(cliente, filtros, n)` no protocolo), mantendo o parser de uma resposta por vez.

## 4. Onde o evento entra no lote

O JSON de `op=P` não traz o evento. Opções avaliadas:

1. **Anotação na requisição, repassada ao parser** (escolhida, D-37): genérica, explícita, testável; o Vip ignora.
2. Parser ler a URL ou o corpo da requisição: o parser passaria a conhecer o protocolo HTTP do site.
3. Estado compartilhado entre adaptador e parser: acoplamento escondido, ruim para testes.

## 5. Padrões e armadilhas do onboarding (`onboarding-leiloeiro-assistido.md`, Apêndice)

| Armadilha | Situação no Claudio Kuss | Tratamento |
|-----------|--------------------------|------------|
| `numero_lote_por_evento` | Sim: número do lote por evento, vazio até o loteamento | Id pelo `seq` (D-38) |
| `sinonimos_marca` | Sim: `CHEV`, `CAOACHERY`, `M BENZ`, `LR`, prefixo `IMP` | D-42 |
| `km_sentinela` | Não se aplica: o Kuss não informa km | RN-06 |
| `zero_resultados` | Evento com `qtde = 0`; agenda sem evento da categoria | Busca vazia legítima (D-41) |
| `filtro_ignorado_pelo_servidor` | Não há filtro no servidor (a categoria é escolhida no cliente) | D-40 |
| `reaparicao` | Provável entre eventos (premissa) | Placa parcial na lista (D-50) |
| `paginacao` | `qtdePag` + `[]` além da última | D-35, D-36 |
| `limite_taxa` | Nenhum 429 em 9 requisições a 5–6 s | Mesmo intervalo de 5 s |
| **nova:** `preco_ausente_em_massa` | Leilão por evento: quase nenhum lote tem valor antes do pregão | `preco_obrigatorio = False` (D-46); vale registrar no Apêndice do onboarding no `/reversa-sync` |
| **nova:** `sucata_na_categoria` | Lotes `SUCATA ...` dentro do evento de financeiras | D-43; registrar no Apêndice no `/reversa-sync` |

## 6. Custos de arrematação (para o backlog "custo na garagem")

Comissão de 5% e despesas administrativas por lote no `tblDespAdm` (R$ 2.750 no Fluence). As condições de venda citam também ICMS e logística. Detalhe na triagem e na memória do projeto; esta feature só exibe a despesa no relatório.
