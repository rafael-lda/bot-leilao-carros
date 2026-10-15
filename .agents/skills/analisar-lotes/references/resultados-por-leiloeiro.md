# Resultado do pregão, por leiloeiro

O que cada site mostra depois que o pregão acaba e o que `analise pagina` devolve em `campos.resultado`. Investigado em 2026-10-15 com lotes reais. Quando um site mostrar algo diferente, conte ao Rafael e proponha atualizar este arquivo (e, se for o caso, o código em `src/bot_leilao/analise/pagina.py`).

Em nenhum caso grave o apelido de quem deu lance: Kuss, Freitas e Milan o mostram, e a leitura já o descarta.

| Leiloeiro | O que o site mostra depois do pregão | `campos.resultado` | Valor final? |
|-----------|--------------------------------------|--------------------|--------------|
| Claudio Kuss | O lote continua no evento; o último lance diz só quem deu ("PRESENCIAL" ou o apelido de quem deu online), sem valor | `último lance presencial; valor não divulgado pelo site`, `último lance online; ...` ou `sem lance` | Não. Só assistindo ao pregão (ver backlog: captura do último lance perto do fim) |
| Copart | O lote some da busca pública logo depois do leilão. A página de detalhe é barrada pelo Imperva | `saiu da busca pública da Copart (...); resultado não divulgado sem login` | Não |
| Vip | O anúncio continua no ar com a situação final (ex.: "Condicional negada") e o último lance | `condicional negada; último lance R$ 13.000` | Sim, o último lance (a venda pode estar condicional ou negada) |
| Freitas | Status do lote ("VENDIDO", "SEM LICITANTES") e o maior lance, nas mesmas chamadas públicas que a página faz | `vendido; maior lance R$ 43.500` ou `sem licitantes; sem lance` | Sim, o maior lance |
| Milan | Etiqueta de estado ("VENDIDO", "CONDICIONAL"); o lance vira "R$ ---" | `vendido; valor não divulgado pelo site` | Não (antes do fim mostra o lance; depois esconde) |

## Como ler

- **Condicional** (Vip, Milan): o lance não atingiu o mínimo do vendedor; a venda depende da aprovação dele. "Condicional negada" quer dizer que o vendedor recusou.
- **Sem lance / sem licitantes:** ninguém deu lance. É comum o carro voltar em outro evento (ver reaparições na skill).
- **Antes do fim:** enquanto o lote recebe lance, não vem `resultado`; vem `lance_corrente`, que vai para **Lance atual** na reconferência.
- **Valor do último lance × FIPE:** quando o site dá o valor (Vip, Freitas), mostre no resumo o % da FIPE do lote, se o bloco tiver FIPE. É o dado que o Rafael usa para avaliar a viabilidade.

## Evidências

- Kuss: evento 897 (13/10/2026), 179 lances presenciais, 163 online, 4 sem lance, nenhum valor.
- Copart: lote 1141180 com `total 0` na busca depois do leilão.
- Vip: anúncio 310800 (`tests/fixtures/analise/vip_anuncio_310800.html`).
- Freitas: 8103/3 vendido por R$ 43.500 e 8103/124 sem licitantes (pregão de 14/10/2026; `tests/fixtures/analise/freitas_8103_3_*`).
- Milan: 15618/001 vendido e 15618/046 condicional (`tests/fixtures/analise/milan_lote_*_apos_pregao.html`).
