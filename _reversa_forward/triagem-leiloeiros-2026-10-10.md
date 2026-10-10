# Triagem de leiloeiros — 2026-10-10

> Objetivo: escolher, por dados, o próximo leiloeiro a entrar no bot depois do Vip.
> Método: poucas requisições por site (2 a 6), mesmo `User-Agent` de navegador do bot, saindo da internet do Rafael (Docker Desktop no notebook), sem login e sem contornar nenhuma proteção.

## Resumo

| Leiloeiro | Acesso automatizado | Tecnologia dos dados | Financiamento | Volume hoje | Veredito |
|---|---|---|---|---|---|
| **Claudio Kuss** (`claudiokussleiloes.com.br`) | ✅ Livre, sem proteção | **API interna em JSON** (lista e detalhe) | ✅ Eventos "Veículos - Financeiras" | **391 lotes** em 2 eventos (346 + 45) | **Próximo a entrar** |
| **Copart** (`copart.com.br`) | ❌ Imperva/Incapsula na página inicial | Desconhecida (sitemap de lotes vazio) | Minoria do catálogo, mas leiloeiro grande | Desconhecido sem navegador | Só com navegador automatizado (Apify) |
| **Freitas** (`freitasleiloeiro.com.br`) | ❌ "Acesso Bloqueado" pelo firewall da GoCache, até no `robots.txt`; certificado TLS incompleto | Desconhecida | Desconhecido | Desconhecido | Só com navegador automatizado |
| **Milan** (`milanleiloes.com.br`) | ❌ Desafio do Cloudflare ("Just a moment...") | Desconhecida | Desconhecido | Desconhecido | Só com navegador automatizado |

Para comparação, o Vip tinha 173 lotes de financiamento + conservado (incluindo motos) no mesmo dia.

## Claudio Kuss em detalhe

- **`robots.txt`:** só bloqueia `/contrato/`, `/winleilao/`, `/portal/` e PDFs. Os endpoints usados abaixo ficam fora disso.
- **Modelo de leilão:** por **eventos** com data marcada ("Leilão Presencial / Online", por exemplo 13/10/2026 às 10:00), com lances prévios online até o pregão. Diferente do Vip, que é contínuo.
- **Descoberta de eventos:** a página inicial lista os próximos leilões. Os de interesse têm o rótulo **"Veículos - Financeiras"** e o link `relacao-foto/<id do evento>`.
- **Quantidade por evento:** `POST /json_edital.php` com `op=Q&leilaoID=<evento>&pesq=` devolve `{"qtde":346,"qtdePag":35}`.
- **Lista de lotes:** `POST /json_edital.php` com `leilaoID=<evento>&op=P&pag=<n>&loteado=&pesq=` devolve 10 lotes por página, com os campos `seq` (id), `lote`, `bem` (`CHEV/ONIX 10 MT LT1`: marca/modelo e versão, frequentemente com `MT`/`AT`), `comb`, `ano` (`20/21`), `valor` (lance atual; vazio sem lance), `usuario` (último lance), `foto`, `linkVideo`.
- **Detalhe do lote:** `POST /json_lance_info_lote.php` com `op=D&leilaoID=<evento>&le_id=<seq>&loteado=N` devolve `tblAno`, `tblCor`, `tblComb`, `tblPlaca` (parcial), `tblTransf`, `tblCRLV`, `tblDUT`, `tblIPVA`, **`tblDespAdm` (despesas administrativas, ex.: R$ 2.750,00)**, **`tblInformacoes` (observações do estado, ex.: "NÚMERO DA CAIXA DIVERGENTE - SEM CONSOLE CENTRAL / ALAVANCA DE CAMBIO")**, **`retirado` (S/N)** e `incr` (incremento). Página humana do lote: `lance/<evento>/0/<seq>`.
- **Não há:** quilometragem (em nenhum lugar), campo de monta, campo de câmbio. O texto padrão diz "recuperado de financiamento **ou sinistro**", então o estado só aparece nas observações.

### Encaixe na arquitetura atual

- **Parser:** recebe JSON em vez de HTML; o contrato (`extrair(conteudo, contexto)`) já aceita bytes. Sem mudança no núcleo.
- **Adaptador:** é o ponto de desenho. O Vip é "uma busca com páginas"; aqui é "vários eventos, cada um com páginas". O adaptador precisa descobrir os eventos de financeiras na preparação da sessão e mapear as páginas da busca para (evento, página). Isso vai para o plano da feature.
- **Km ausente:** já tratado (D-19): o teto de km não elimina, o lote passa como "km a confirmar".
- **Volume de requisições:** 35 + 5 páginas a 5 s ≈ 3,5 min, mais a página inicial. Cabe no limite de 10 min.
- **Ganhos extras:** câmbio no título (`MT`/`AT`) dá uma primeira pista para o filtro de câmbio; despesas administrativas alimentam o custo total; observações ajudam a separar o que é "bomba".

## O que falta saber e só o Rafael consegue ver (no navegador)

O navegador de verdade passa pelas proteções. Uma olhada rápida em cada site responde se vale pagar Apify por ele:

1. **Copart:** existe filtro ou categoria de **financiamento / recuperado**? Quantos lotes aparecem nele hoje?
2. **Freitas:** idem. O Freitas é conhecido por leilões de financeiras.
3. **Milan:** idem.

Se algum tiver muito mais volume que o Claudio Kuss, entra na conta do nível `apify` (custo mensal), decisão do Rafael.

## Recomendação

1. **Claudio Kuss como feature 002**, pelo ciclo do Reversa (requirements → plan → código). Dados em JSON, acesso livre e volume maior que o do Vip.
2. Copart, Freitas e Milan **dependem da sua olhada no navegador** e da decisão sobre custo do Apify.
