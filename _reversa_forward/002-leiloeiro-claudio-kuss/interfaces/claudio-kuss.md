# Contrato: Claudio Kuss Leilões

> Feature: `002-leiloeiro-claudio-kuss`
> Observado em: 2026-10-10, sem login, `User-Agent` de navegador (D-30 da 001), 5 s ou mais entre requisições
> Amostras reais: `../amostras/`
> Confidência: 🟢 observado, 🟡 inferido

## 1. Visão geral

| Item | Valor |
|------|-------|
| Base | `https://www.claudiokussleiloes.com.br` 🟢 |
| Proteção anti-robô | nenhuma observada (sem Cloudflare challenge, sem cookie obrigatório) 🟢 |
| `robots.txt` | bloqueia só `/contrato/`, `/winleilao/`, `/portal/` e PDFs 🟢 |
| Modelo de leilão | por **evento** com data e hora; lances prévios online até o pregão presencial/online 🟢 |
| Tipo de conteúdo | os endpoints JSON respondem `Content-Type: text/html; charset=UTF-8` com corpo JSON; o parser decodifica sem olhar o cabeçalho 🟢 |
| Sessão | nenhum cookie necessário; `preparar_sessao` devolve `None` 🟢 |

Sequência de uma busca (D-34, D-35):

```
pág 1      GET  /proximos-leiloes                                  → agenda (HTML)
pág 2      POST /json_edital.php  op=Q  leilaoID=897               → {"qtde":346,"qtdePag":35}
pág 3..37  POST /json_edital.php  op=P  leilaoID=897  pag=1..35    → lista de 10 lotes
pág 38     POST /json_edital.php  op=Q  leilaoID=898               → {"qtde":45,"qtdePag":5}
pág 39..43 POST /json_edital.php  op=P  leilaoID=898  pag=1..5
depois da filtragem, por lote novo:
           POST /json_lance_info_lote.php  op=D  leilaoID  le_id    → detalhe
```

## 2. Agenda: `GET /proximos-leiloes`

- **Resposta:** HTML. Cada evento é um `div.panel` dentro de `div.container`, com:
  - rótulo em `.panel-heading h2 span`: `Leilão Presencial / Online - Veículos - Financeiras` 🟢
  - data e hora em `.panel-body h2`: `Curitiba : 13/10/2026 - 10:00 horas` 🟢 → `pregao_em` = 13/10/2026 10:00, fuso `America/Sao_Paulo` 🟡
  - link `a[href^="relacao-foto/"]`: `relacao-foto/897` → id do evento `897` 🟢
- **Seleção:** rótulo normalizado (sem acento, minúsculas) contém a `categoria` normalizada da busca.
- **Observado em 2026-10-10:** dois eventos "Veículos - Financeiras": 897 (13/10/2026 10:00) e 898 (20/10/2026 10:00).
- **Erros:** página sem nenhum bloco reconhecível → o parser não declara vazia → quebra (D-41).

## 3. Quantidade: `POST /json_edital.php` `op=Q`

- **Corpo (form):** `op=Q&leilaoID=<evento>&pesq=`
- **Resposta:** `{"qtde":346,"qtdePag":35}` 🟢 (números podem vir como texto; o parser aceita os dois 🟡)
- **Uso:** `qtdePag` define quantas páginas `op=P` pedir; `qtde` serve à conferência de RF-03 (D-36).
- `qtde = 0` → a página é declarada vazia e nenhuma página `op=P` é pedida para o evento.

## 4. Página de lotes: `POST /json_edital.php` `op=P`

- **Corpo (form):** `leilaoID=<evento>&op=P&pag=<n>&loteado=&pesq=`
- **Cabeçalhos:** `X-Requested-With: XMLHttpRequest`, `Referer: <base>/relacao-foto/<evento>` (como o navegador)
- **Resposta:** lista JSON de até 10 objetos 🟢

| Campo | Exemplo | Uso |
|-------|---------|-----|
| `seq` | `"282622"` | id canônico `claudio-kuss-leiloes:<seq>`; `le_id` do detalhe |
| `lote` | `""` ou `"119"` | `numero_lote` (vazio até o loteamento) |
| `bem` | `"IMP RENAULT/FLUENCE DYN 20A"` | título, marca e modelo (D-42, D-43) |
| `comb` | `"A/G"` | não usado |
| `ano` | `"13/13"` | fabricação e modelo (D-44) |
| `valor` | `""` ou `"74.000,00"` | `lance_corrente` (D-45) |
| `usuario` | apelido do último lance | **não lido** (dado de pessoa, sem uso) |
| `logo`, `foto`, `linkVideo` | caminhos | não usados |

- **Página além da última:** `[]` (2 bytes) 🟢
- **Grafias de `bem` (censo de 391 lotes na lista HTML):** marcas com prefixo `IMP ` (importados), `SUCATA ` (17 lotes, **só na lista HTML**: no `op=P` o mesmo lote vem sem o prefixo, ex.: seq 282327 `IMP RENAULT/CLIO EXP 10 16V H`), `CHEV`, `GM`, `CHEVROLET`, `VW`, `MMC`, `M BENZ`, `CAOACHERY`, `IMP LR`; `RETIRADO` sozinho para lote retirado; não veículos sem `/` (`MODULOS FOTOVOLTAICOS`) 🟢
- **Erros:** corpo que não é lista JSON, ou item sem `seq` ou `bem` → exceção no parser → quebra.

## 5. Detalhe do lote: `POST /json_lance_info_lote.php` `op=D`

- **Corpo (form):** `op=D&leilaoID=<evento>&le_id=<seq>&loteado=N`
- **Cabeçalhos:** `X-Requested-With: XMLHttpRequest`, `Referer: <base>/lance/<evento>/0/<seq>`
- **Resposta (amostra `detalhe-op-D_282622-fluence-sinistrado.json`):**

| Campo | Exemplo | Uso |
|-------|---------|-----|
| `retirado` | `"N"` / `"S"` | `S` → lote descartado (RN-05) |
| `tblInformacoes` | `"SINISTRADO - NOS DOCUMENTOS CONSTA RECUPERADO DE SINISTRO. ..."` | `observacoes` (RF-07); vazio ou `&nbsp;` → `None`; começando com `"SUCATA SEM DOCUMENTOS - BAIXADO JUNTO AO DETRAN"` → sucata (D-43) |
| `tblDespAdm` | `"2.750,00"` | `despesas_adm` |
| `tblPlaca` | `"F**-**35"` | `placa_parcial` |
| `tblTransf` | `" SÃO PAULO"` | `local_documento` (aparado); `"SUCATA"` em lote de sucata |
| `tblTxtInfo` | texto padrão de todo lote | **não usado** (D-52) |
| `descLote`, `tblAno`, `tblCor`, `tblComb`, `tblCRLV`, `tblDUT`, `tblIPVA`, `incr`, `sequencia` | | não usados nesta feature |

- Entidades HTML (`&nbsp;`) e escapes Unicode são decodificados; espaços colapsados.
- **Erros:** falha de rede ou JSON inválido → lote segue sem observações (D-49).

## 6. Página humana do lote

- `GET /lance/<evento>/0/<seq>` → 200, página com fotos e o detalhe acima carregado por JavaScript 🟢
- Depois do loteamento, o próprio site usa `/lance/<evento>/<lote>`; se `/0/<seq>` deixar de abrir, trocar o formato (premissa do roadmap §4) 🟡

## 7. Endpoints conhecidos e não usados

| Endpoint | Por que não |
|----------|-------------|
| `GET /relacao-lista/<evento>` | Todos os lotes do evento num HTML, **sem** preço; alternativa para volume alto junto com `op=T` (investigation §3) |
| `POST /json_edital.php` `op=T&loteado=S` | Todos os lances do evento: `{"qtde":346,"atual":"0","0":{"Q":seq,"U":usuario,"V":"74.000,00"},...}` |
| `POST /json_lance_historico.php` | Status e lance inicial (`av`), consultado em laço pela página; `{"status":"Não loteado",...}` antes do loteamento (D-45) |
| `json_login.php`, `/portal/`, `/winleilao/`, `/contrato/` | Área de usuário / bloqueados no `robots.txt` (RN-09) |

## 8. Idempotência, timeouts e conduta

- Todas as chamadas são leituras; repetir não altera nada no site.
- Timeout de 30 s e retentativas do `ClienteHTTP` (5 s e 15 s); 429 sem `Retry-After` espera 30 s (D-30 e emendas da 001).
- 5 s entre requisições ao mesmo host. Varredura típica: 43 requisições de lista (~3,6 min) + 1 por lote novo.
