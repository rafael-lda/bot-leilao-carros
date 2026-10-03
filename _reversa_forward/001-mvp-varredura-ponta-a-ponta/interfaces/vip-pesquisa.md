# Interface: Pesquisa do Vip Leilões

> Tipo: HTTP, **consumido** pelo `coletor-lotes` (adaptador `vip-leiloes`) e interpretado pelo `parser-lotes` (parser `vip-leiloes`)
> Evidência: requisições reais de 2026-10-03, 6 no total, espaçadas em ≥ 5 s, com sessão de cookies e limite de 3 redirecionamentos
> Confidência: 🟢 observado, 🟡 inferido

## 1. Preparação de sessão

```
GET https://www.vipleiloes.com.br/
User-Agent: <navegador comum>
```

| Aspecto | Comportamento | Confidência |
|---------|---------------|-------------|
| Redirecionamentos | 2 até a resposta final; o limite de 3 (RF-13 do `coletor-lotes`) é suficiente | 🟢 |
| Cookie emitido | `__CBCanal` (HttpOnly, Secure, de sessão), conteúdo `{"CanalId":"<uuid>"}` | 🟢 |
| Sem cookie | Qualquer página redireciona para o emissor e volta, em laço, sem sessão que preserve cookies (investigação de 2026-09-27) | 🟢 |
| Token antifalsificação | Não existe no formulário de pesquisa em 2026-10-03 | 🟢 |

Uma preparação por execução, antes da primeira busca. Conta para o intervalo de 5 s.

## 2. Requisição de busca

```
POST https://www.vipleiloes.com.br/pesquisa?handler=pesquisar                                  (página 1)
POST https://www.vipleiloes.com.br/pesquisa?SortOrder=DataInicio&pageNumber=<N>&handler=pesquisar  (página N ≥ 2)
Content-Type: application/x-www-form-urlencoded
User-Agent: <o mesmo da preparação>
X-Requested-With: XMLHttpRequest
Referer: https://www.vipleiloes.com.br/pesquisa/index
Cookie: __CBCanal=...
```

`X-Requested-With` e `Referer` reproduzem a requisição do formulário AJAX do site. Não foi testado se são obrigatórios; mantê-los custa nada e evita uma diferença detectável. 🟡

### 2.1 Corpo

Campos fixos, sempre enviados pelo adaptador:

| Campo | Valor | Motivo |
|-------|-------|--------|
| `Filtro.OrdenarPor` | `DataInicio` | Mesmo valor do `SortOrder` da paginação, mantendo a ordem estável entre páginas |
| `Filtro.SelecaoVeiculos` | `true` | Restringe a veículos, como a aba padrão do site |

Campos vindos de `filtros` no `config/leiloeiros.yaml`. A chave do YAML é convertida pela tabela abaixo; chave fora da tabela aborta a execução antes da rede (roadmap D-12).

| Chave no YAML | Campo enviado | Valores aceitos pelo site | Confidência |
|---------------|---------------|---------------------------|-------------|
| `procedencia` | `Filtro.Procedencia` | `1` Apreensão Trânsito, `2` Patrimônio, `3` Penhorado, `4` Recuperado Financiamento, `5` Recuperado Sinistro | 🟢 |
| `monta` | `Filtro.Monta` | `1` Conservado, `2` Pequena Monta, `3` Média Monta, `4` Sinistro Recuperado, `5` Sucata Aproveitável, `6` Sucata Aproveitável com motor inservível, `7` Sucata ferrosa, `8` Sucata inservível | 🟢 |
| `marca` | `Filtro.Marca` | Texto em maiúsculas, como no `<select>`: `NISSAN`, `TOYOTA`, `CHEVROLET`… | 🟢 |
| `modelo` | `Filtro.Modelo` | Texto | 🟡 |
| `ano` | `Filtro.Ano` | Um único ano | 🟢 |
| `classificacao` | `Filtro.Classificacao` | `1` Motos, `2` Sinistrados, `3` Seminovos, `4` Diversos, `5` Usados, `6` Pesados | 🟢 |
| `quilometragem_de`, `quilometragem_ate` | `Filtro.QuilometragemDe`, `Filtro.QuilometragemAte` | Inteiro | 🟡 |
| `valor_de`, `valor_ate` | `Filtro.ValorDe`, `Filtro.ValorAte` | Número | 🟡 |
| `estado` | `Filtro.LocalEstadoId` | Identificador do estado no site | 🟡 |
| `financiavel` | `Filtro.Financiavel` | `true` | 🟢 |
| `texto` | `Filtro.Texto` | Texto livre | 🟢 |

Valor de lista no YAML vira o mesmo campo repetido no corpo. Nenhum campo do Vip observado aceita múltipla escolha, então lista é aceita pelo cadastro, mas o adaptador recusa lista para esses campos. 🟡

**Teste de aplicação dos filtros (2026-10-03):** `marca=NISSAN` → 9 resultados; `marca=NISSAN, procedencia=4, monta=1` → 1 resultado; `procedencia=4, monta=1` → 201 resultados. O servidor aplica os filtros. 🟢

## 3. Resposta

`200 OK`, `text/html; charset=utf-8`, fragmento HTML (não a página inteira) com 12 cards por página. Tamanho observado: 14 KB a 140 KB.

### 3.1 Total e paginação

| Elemento | Seletor | Exemplo | Confidência |
|----------|---------|---------|-------------|
| Total | `#resultadosEncontrados` | `201 resultados encontrados` | 🟢 |
| Página atual | `input#CurrentPage` | `value="2"` | 🟢 |
| Existe próxima | `.main-pagination li.page-go` que contém `a[aria-label="Next"]`, **sem** a classe `disabled` | — | 🟢 |

Verificação cruzada: `ceil(total / 12)` deve bater com a última página alcançada; divergência gera aviso em log, sem abortar. 🟡

### 3.2 Card de lote

Um `div.card-anuncio` por lote. Exemplo real, resumido:

```html
<div class="card card-lel card-anuncio h-100 evento-Aberto anuncio-AbertoParaOfertas">
  <a class="crd-status" href="/evento/anuncio/nissan-sentra-20s-flex-310800">
    <span class="situacao">Aberto para lances</span></a>
  …
  <div class="anc-title">
    <h1>SENTRA 20S FLEX - 2012/2013</h1>
    <div class="anc-info"><span>nissan</span><span>228.227 Km</span><span>placa final 1</span></div>
  </div>
  <span class="valor-atual">R$ 12.500,00</span>
  <span class="anc-lel">Valor inicial: <b>R$ 12.500,00</b></span>
  <strong>Lote:</strong> 21 … <strong>Local:</strong> SC
  <span class="anc-lanc"><span>1 Lance</span></span>
  <span class="anc-start">Início:  05/10/2026</span><span class="anc-hour">19:00</span>
</div>
```

| Campo do `Lote` | Origem no card | Normalização | Confidência |
|-----------------|----------------|--------------|-------------|
| `link` | `href` de `a.crd-status` | Absoluto com a `base_url` | 🟢 |
| `id_canonico` | Sufixo numérico do `href` (`310800`) | `vip-leiloes:310800` | 🟢 |
| `modelo` | `h1`, trecho antes de ` - ` | Minúsculas, sem acento | 🟢 |
| `ano_fabricacao`, `ano_modelo` | `h1`, trecho `AAAA/AAAA` depois de ` - ` | Inteiros; um único ano preenche os dois (RF-04 do `parser-lotes`) | 🟢 |
| `marca` | Primeiro `span` de `.anc-info` | Minúsculas, sem acento, depois tradução pela tabela comum de sinônimos (`parser-lotes` RF-12): `mmc` → `mitsubishi`, `gm` → `chevrolet` (roadmap D-28). O formulário do site lista as duas grafias como marcas separadas | 🟢 |
| `quilometragem` | `span` de `.anc-info` terminado em `Km` | `228.227 Km` → `228227` | 🟢 |
| `lance_corrente` | `.valor-atual` | `R$ 12.500,00` → `12500.00` | 🟢 |
| `lance_inicial` | `b` dentro de `.anc-lel` com texto "Valor inicial" | Idem | 🟢 |
| `numero_lote` | Texto depois de `<strong>Lote:</strong>` | Texto | 🟢 |
| `situacao` | `.crd-status .situacao` | Texto como veio | 🟢 |
| `retirado` | `situacao` ou classes `evento-*`/`anuncio-*` contendo "retirad" | Booleano | 🟡 |
| `tipo_leilao` | Não vem do card: herdado da busca (`procedencia: 4` → `financiamento`) | — | 🟡 |
| `descricao` | `h1` completo + local + número de lances + início do pregão | Texto livre, preservando o que não tem campo próprio | 🟡 |

Sem nenhum lance, `valor-atual` e `Valor inicial` coincidem (`requirements.md#9`); a quantidade de lances diz se houve lance.

## 4. Erros e classificação

| Situação | Detecção | Veredito no coletor | Retry |
|----------|----------|---------------------|-------|
| Timeout de 30 s | Exceção de timeout | `falha_rede` | Sim, até 3 tentativas com espera de 2 s e 4 s |
| DNS ou conexão recusada | Exceção de conexão | `falha_rede` | Sim |
| Mais de 3 redirecionamentos | Exceção de excesso de redirecionamentos | `falha_rede`, `motivo: laco_redirecionamento` | Sim |
| `403` ou `429` | Status | `bloqueado` | Sim; em `429`, respeita `Retry-After` até 60 s |
| Desafio do Cloudflare | Status `403`/`503` com marcas `cf-chl` ou `Just a moment` no corpo | `bloqueado` | Sim |
| `5xx` | Status | `falha_rede` | Sim |
| `200` com corpo vazio | Tamanho zero | Falha de coleta (EC-06 do `coletor-lotes`) | Não |
| `200` sem `#resultadosEncontrados` e sem cards | — | `ok` no coletor; o parser sinaliza quebra (RF-07 do `parser-lotes`) | Não |

## 5. Idempotência, ritmo e limites

- Somente leitura: repetir a requisição não altera nada no site.
- Intervalo mínimo de 5 s entre quaisquer duas requisições ao host, incluindo a preparação de sessão.
- `robots.txt`: `User-agent: *`, `Allow: /`, sem `Crawl-delay` (2026-09-27).
- Teto de 50 páginas por busca (RF-14 do `coletor-lotes`); a busca recomendada usa 17.
- Limite de 20 MB por resposta (EC-09 do `coletor-lotes`).
