---
name: analisar-lotes
description: Triagem e custo na garagem dos lotes de leilão da lista do Bot Leilão Carros (1OUTPUT/lotes-a-monitorar.md). Confere cada lote contra o veículo-alvo (câmbio, sinistro, sucata, mecânica, km, teto, versão), reconfere a cada execução os "a confirmar" (lance atual, data do pregão), anota e informa por leiloeiro o resultado dos pregões que já passaram e as reaparições, move os reprovados para lotes-descartados.md com motivo e evidência, e para os aprovados consulta a FIPE e calcula o custo com o carro na garagem em Londrina e o lance máximo. Use sempre que o Rafael pedir /analisar-lotes, "analisa os lotes", "triagem da lista", "quais lotes servem", "quanto fica esse carro na garagem", "vale a pena o lote 5", "FIPE do lote", "lance máximo", "devolve o lote 2", "como foram os pregões", "o que vendeu", ou quiser revisar, limpar ou avaliar a lista de monitoramento, mesmo sem dizer "skill".
---

# Analisar lotes

O bot acrescenta à lista `1OUTPUT/lotes-a-monitorar.md` todo lote que casa com um veículo-alvo, mas só filtra o que o site informa em campo: marca, modelo, ano, lance e às vezes km. O resto vem em texto livre ("SINISTRADO", "DYN 20M", "MECÂNICA COM PROBLEMAS") ou só na página do lote. Esta skill faz o pente fino que o bot não consegue: decide, lote a lote, se o carro serve, e calcula quanto ele custa na garagem.

**Divisão de trabalho:** você julga; a linha de comando do bot lê, calcula e escreve. Nunca edite a lista à mão, nem faça conta de cabeça. A lista tem um formato que o bot e o Rafael usam (números, comentário `<!-- lote: ... -->`), e os comandos escrevem sem estragar nada, com a trava da varredura.

## Comandos

Rode da raiz do projeto com o Python do projeto: `venv\Scripts\python.exe` no Windows, `.venv/bin/python` (ou `venv/bin/python`) no Linux. Todos aceitam `--raiz <pasta>` (padrão: a atual) e respondem JSON na saída padrão; erro vem como `{"erro": "..."}`.

| Comando | Para quê |
|---------|----------|
| `python -m bot_leilao analise lotes [--numero N \| --link URL]` | Lotes com os campos e o alvo (critérios e texto `triagem`) |
| `python -m bot_leilao analise pagina <número ou link>` | Lê o lote no site pelo acesso do bot: campos e texto da página |
| `python -m bot_leilao analise triar <n> --veredito aprovado` | Marca aprovado |
| `python -m bot_leilao analise triar <n> --veredito a-confirmar --falta "câmbio; lance"` | Marca a confirmar |
| `python -m bot_leilao analise triar <n> --veredito reprovado --motivo "..." --evidencia "..."` | Move para `lotes-descartados.md` |
| `python -m bot_leilao analise triar <n> --veredito encerrado --motivo "<resultado>"` | Pregão acabou: o lote fica na lista como registro |
| `python -m bot_leilao analise devolver <n>` | Traz um descartado de volta |
| `python -m bot_leilao analise anotar <n> --campo "Câmbio" --valor "..."` | Grava um campo (`Câmbio`, `Resultado do pregão`, `Lance atual` ou `Pregão`) |
| `python -m bot_leilao analise fipe-candidatos --marca M --modelo "termos" --ano A` | Versões FIPE daquele ano com valor e código |
| `python -m bot_leilao analise fipe-valor --codigo C --ano A` | Valor de um código FIPE |
| `python -m bot_leilao analise custo --lance L [--despesa D] --patio "Cidade - UF" [--documento-uf UF] [--fipe F] [--reparos-extra R --motivo-reparos "..."]` | Custo na garagem, % da FIPE, lance máximo |
| `python -m bot_leilao analise anotar-custo <n> --json -` | Grava FIPE e custo no bloco (JSON pela entrada padrão) |

Código de saída 3 significa varredura em andamento: pare, avise o Rafael e não tente de novo sozinho.

## Triagem

### 1. Ler

`analise lotes` (ou só o lote pedido). Entram na análise:

- lotes sem linha **Triagem**;
- lotes com **Triagem** "a confirmar": são reconferidos em toda execução (seção 3), porque a informação que faltava (lance, data, câmbio) costuma aparecer depois;
- lotes cujo **Pregão** já passou e que ainda não estão **encerrados** (inclusive os aprovados).

Pule os encerrados e os aprovados com pregão por vir, a menos que o Rafael peça para refazer. Lote sem alvo (`"alvo": null`) é de um alvo desativado: deixe "a confirmar — alvo desativado" e siga.

### 2. Julgar cada lote

Cada lote recebe um veredito:

- **aprovado:** nada no que se sabe contraria o alvo;
- **reprovado:** uma evidência clara contraria um critério;
- **a confirmar:** falta informação para decidir;
- **encerrado:** o pregão acabou e nada reprova o lote; ele fica na lista como registro do resultado.

**Na dúvida, a confirmar.** Um reprovado sai da lista e o Rafael pode nunca mais olhar; um "a confirmar" custa só uma olhada. Reprove só com evidência que você consegue citar (trecho do título, da observação ou da página).

Confira os critérios nesta ordem; o primeiro que reprovar decide o motivo, e os outros podem entrar na evidência:

| Critério | De onde vem | Reprova quando | A confirmar quando |
|----------|-------------|----------------|--------------------|
| Lote retirado | Observações, página | "RETIRADO" | — |
| Tipo de leilão | `alvo.tipos_leilao`; observações e comitente | Texto diz outra origem (ex.: seguradora quando o alvo só aceita financiamento) | — |
| Ano de modelo | `alvo.ano_min`/`ano_max`; título | Fora da faixa | — |
| Teto | `alvo.preco_maximo` × Lance atual (senão Lance ao entrar) | Lance acima do teto | "Preço a confirmar" não reprova |
| Km | `alvo.quilometragem_maxima`; campo Km, página | Acima do máximo | Sem km e o alvo tem máximo |
| Câmbio | `criterios.cambio`; campo Câmbio, título, página | Câmbio conhecido fora da lista | Título e página não dizem |
| Sinistro | `criterios.aceitar_sinistro` | "SINISTRADO", "RECUPERADO DE SINISTRO", média ou grande monta | — |
| Sucata | `criterios.aceitar_sucata` | "SUCATA", "BAIXA PERMANENTE" | — |
| Mecânica | `criterios.aceitar_mecanica_com_problema` | "MECÂNICA COM PROBLEMAS", "NÃO FUNCIONA", "MOTOR BATENDO", "CÂMBIO DANDO TRANCO" | — |
| Avarias | `criterios.aceitar_pequenas_avarias` | "PEQUENOS AMASSADOS" com o critério falso | Dano com local e sem tamanho ("TRASEIRO", "FRONTAL"), "NÃO AVALIÁVEL" |
| Versão preferida | `alvo.triagem` (texto do Rafael) | Título mostra claramente outra versão ou motor | Título não diz a versão |
| Documento | Observações, página | "SEM DOCUMENTO", "DOCUMENTO BAIXADO" | — |

"Motor dá partida e engrena" é bom sinal, não problema.

**Pregão que já passou não reprova.** O Rafael está investigando a viabilidade dos leilões e quer ver o resultado desses lotes. Rode `analise pagina <n>`: se vier `campos.resultado`, grave com `analise anotar <n> --campo "Resultado do pregão" --valor "<data do pregão>: <resultado>"`; se não vier, `"<data>: resultado não informado pelo site"`. Quando o resultado tem valor e você sabe a FIPE da versão (bloco ou `analise fipe-candidatos`), acrescente o percentual: `"14/10: vendido; maior lance R$ 43.500 (65% da FIPE R$ 66.872)"`; é o dado que o Rafael usa para calibrar o teto. Depois julgue pelos critérios: com evidência que reprova, reprove (anote o resultado antes, para ele ir junto para os descartados); senão, `triar <n> --veredito encerrado --motivo "<resultado curto>"`, nunca "aprovado": um carro vendido ou com o pregão fechado não está disponível. Nunca grave apelido de quem deu lance.

Cada leiloeiro mostra uma coisa diferente depois do pregão (o Kuss não divulga valor; a Copart tira o lote da busca; Vip, Freitas e Milan mostram a situação final). O que cada um mostra, e como ler, está em `references/resultados-por-leiloeiro.md`: leia esse arquivo quando houver pregão passado. Se a página mostrar algo que o arquivo não prevê (situação nova, valor que antes não aparecia), conte ao Rafael no resumo e proponha atualizar o arquivo.

**Lendo câmbio pelo título:** "CVT", "AT", "AUT", "AUTOM", "AUTOMÁTICO" → automático ou CVT; "MT", "MEC", "MANUAL" → manual. Na Renault e em importados do Kuss, o sufixo da motorização diz o câmbio: "DYN 20A" é 2.0 automático, "DYN 20M" é 2.0 manual. "1.6 16V" sozinho não diz nada: o mesmo motor tem versões manuais e CVT. A Copart não informa câmbio em lugar nenhum; sem pista no título, fica a confirmar.

**Câmbio deduzido:** quando o título ou a página diz o câmbio e o campo Câmbio do bloco está vazio, grave com `analise anotar <n> --campo "Câmbio" --valor "automático (título 'DYN 20A')"`, citando de onde veio. Assim o Rafael não precisa deduzir de novo.

**Reaparições:** um carro que não vendeu volta em outro evento com outro número. Compare os lotes entre si: mesmo modelo e versão, mesmo ano e o mesmo final de placa (campo Documento), ou a mesma km, indicam o mesmo carro. Cite no resumo ("13 é o mesmo carro do 3, placa O\*\*-\*\*35"); isso conta para a investigação do Rafael (o carro não vendeu da primeira vez).

### 3. Reconferir os "a confirmar"

Para cada lote "a confirmar", rode `analise pagina <n>` e compare com o bloco:

- **Lance:** se `campos.lance_corrente` veio e difere do **Lance atual** do bloco, grave `analise anotar <n> --campo "Lance atual" --valor "R$ <valor> (lido em <dd/mm/aaaa>)"`. Na Copart, "Aguardando classificação" ainda não tem lance: não grave nada.
- **Pregão:** se `campos.pregao_em` veio e o bloco não tem **Pregão** ou tem outro, grave `analise anotar <n> --campo "Pregão" --valor "<dd/mm/aaaa hh:mm>"`.
- **Resultado:** se veio `campos.resultado`, o pregão acabou: siga a regra do pregão passado acima.
- **Julgue de novo** com o que chegou: o lote pode virar aprovado, reprovado (ex.: lance passou do teto) ou continuar a confirmar com outra pendência. Grave sempre com `analise triar`: a linha Triagem nova substitui a antiga e leva a data de hoje, para o Rafael ver que foi reconferido.

Leia todos os "a confirmar", mesmo os da Copart e do Milan; no Milan, avise o custo (~US$ 0,08 por página) no resumo. Se a página não trouxe nada novo, mantenha o veredito e diga "sem novidade" no resumo; regrave a triagem só se a pendência mudou.

### 4. Ler a página dos outros só quando ela pode decidir

Se o bloco não basta (ex.: câmbio desconhecido num lote do Vip, cuja página traz "Câmbio Automático"), rode `analise pagina <n>`. Não abra o site no navegador: Milan (Cloudflare) e Copart (Imperva) barram robô, e a regra do projeto é passar só pelo acesso do bot. No Milan cada página custa cerca de US$ 0,08 (`"pago": true`): leia só quando a página pode mudar o veredito, e some no resumo. Na Copart a "página" é a busca pelo número do lote, sem câmbio. Erro de acesso não reprova: o lote fica a confirmar.

### 5. Mostrar o resumo antes de mover

Antes de gravar, mostre ao Rafael:

```
Triagem de <data>: <N> lotes
Aprovados (<n>): 1 Kicks S CVT 2019 ...
Reprovados (<n>), vão para lotes-descartados.md:
  2 Fluence DYN 20M 2015: câmbio manual (título "DYN 20M"); também "MECÂNICA COM PROBLEMAS"
A confirmar (<n>):
  5 Kicks 1.6 16V 2019 (Copart): câmbio; data e lance
Reconferidos (<n>): 4 Duster 2022 (Copart): pregão 22/10 10:00, lance R$ 21.000 → continua a confirmar (câmbio)
Encerrados (<n>): 15 HB20 Limited 2023 (Freitas): vendido em 14/10 por R$ 43.500 (65% da FIPE)
Resultados dos pregões, por leiloeiro:
  Claudio Kuss: 1 Kicks S CVT 2019, 13/10: último lance presencial; valor não divulgado pelo site
  Freitas: ...
Páginas lidas: <n> (<n> pagas, ~US$ <total>)
```

Agrupe os resultados por leiloeiro, na ordem da lista, e diga em uma linha o que aquele leiloeiro divulga (ex.: "Kuss: só o tipo do último lance"; "Copart: lote some da busca, sem resultado público"). Inclua também, quando houver: as reaparições e o câmbio deduzido que vai ser gravado.

**Referência para os "a confirmar":** quando um lote está "a confirmar" só por falta de câmbio, versão ou lance, dê ao Rafael uma referência de viabilidade, sem gravar no bloco: a FIPE da versão automática mais barata daquele ano (`analise fipe-candidatos`) e o lance máximo para ela (`analise custo --lance 0 --patio ... --fipe <valor>`: com lance 0, só o `lance_maximo` interessa). Diga que é referência, com a versão suposta. Isso mostra quais pátios ficam inviáveis pelo frete antes de qualquer lance.

Pergunte se pode gravar. Se o Rafael já disse para aplicar direto, grave sem perguntar. Depois grave com `analise anotar` (câmbio, resultado, lance atual, pregão) e `analise triar`, um lote por vez, e confirme no fim quantos foram gravados.

## Custo na garagem (aprovados)

Lote encerrado não tem custo: o pregão acabou. Para ele, só o % da FIPE do resultado (seção "Pregão que já passou").

Faça quando o Rafael pedir, ou logo após a triagem se ele pediu "triagem e custo".

1. **FIPE:** `analise fipe-candidatos --marca <marca por extenso> --modelo "<termos>" --ano <ano de modelo>`. Termos: modelo e versão do título, sem "IMP", "I/", marca, ano ou códigos do leiloeiro (ex.: "NISSAN/KICKS S DRCT CVT" → `--marca Nissan --modelo "kicks s"`). Comece específico e vá tirando termos se não vier nada. Use o câmbio que você já sabe para eliminar versões. Ficou **uma** plausível: use-a. Ficaram **várias**: não escolha; anote as candidatas e não calcule custo (o Rafael escolhe).
2. **Custo:** `analise custo` com:
   - `--lance`: Lance atual; se vazio, o valor do Lance ao entrar; "Preço a confirmar" → não calcule e diga isso;
   - `--despesa`: Despesas admin., se houver (sem ela o padrão entra marcado);
   - `--patio`: o campo Pátio como está;
   - `--documento-uf`: a UF do documento (campo Documento ou página: "documento de SANTA CATARINA" → SC); sem pista, omita;
   - `--fipe`: o valor escolhido;
   - `--reparos-extra` e `--motivo-reparos`: só quando as observações citam avaria ou defeito, com estimativa conservadora e o motivo (ex.: 800, "pequenos amassados"). A reserva padrão já cobre o imprevisto comum.
3. **Gravar:** passe pela entrada padrão para `analise anotar-custo <n> --json -` o JSON `{"fipe": <saída do fipe-valor ou a candidata escolhida>, "custo": <saída do custo>}`; com várias candidatas, `{"fipe": null, "candidatas": <saída do fipe-candidatos>, "custo": null}`.

A FIPE vem sempre da linha de comando, nunca de memória. A busca de versões custa uns 5 a 20 pedidos (menos com termos específicos, como "hb20 limited" em vez de "hb20"), e os pedidos ao site oficial são espaçados de 1 s: espere alguns segundos por busca. Se vier `FIPE indisponível`, diga e siga sem custo.

## Devolver um lote

`analise devolver <n>` quando o Rafael discordar de um descarte. O bloco volta para o fim da lista, sem a linha de descarte.

## Limites

Esta skill só lê e anota. Não dá lance, não faz login e não contorna proteção de site. Os critérios vivem em `config/veiculos-alvo.yaml` (bloco `padrao` e texto `triagem` de cada alvo) e os custos em `config/custos.yaml`: se o Rafael quiser mudar uma regra, aponte o arquivo em vez de aplicar a regra só nesta conversa.
