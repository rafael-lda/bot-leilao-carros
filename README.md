# Bot Leilão Carros

Varre sites de leilão de carros, filtra os lotes pelos veículos que você procura e avisa no Telegram, com marca, modelo, ano, preço e o link do lote.

Hoje monitora dois leiloeiros. O bot só observa e avisa: ele nunca dá lance.

| Leiloeiro | O que o bot lê | Particularidades |
|---|---|---|
| **Vip Leilões** | Recuperados de financiamento, estado conservado | Leilão contínuo; informa km |
| **Claudio Kuss Leilões** (Curitiba) | Eventos "Veículos - Financeiras" | Leilão por evento com data marcada: o aviso traz a **data do pregão**. Não informa km nem monta, e o evento mistura financiamento e sinistro: o aviso traz as **observações** do lote ("SINISTRADO", "MECÂNICA COM PROBLEMAS"...) para você descartar à mão. Sucata e lotes retirados ficam de fora. Antes do pregão quase nenhum lote tem lance, então a maioria chega como "Preço a confirmar" |

## Como funciona

1. Lê os carros que você quer em `config/veiculos-alvo.yaml` e os leiloeiros em `config/leiloeiros.yaml`.
2. Busca no site do leiloeiro todas as páginas de resultado, devagar (5 s entre requisições).
3. Compara cada lote com os seus alvos: marca, modelo, **ano de modelo**, **lance corrente** contra o teto, quilometragem (opcional) e tipo de leilão.
4. Manda **um único resumo** no Telegram com os lotes novos. Lote já avisado não volta.
5. Na primeira vez que uma busca roda, ele só registra o que já existe, sem avisar (senão você receberia o catálogo inteiro). Esses lotes não vão para o Telegram, mas aparecem no relatório (seção "Já estavam no site") e entram na lista de lotes a monitorar, marcados "por semeadura".
6. Se o site mudar de layout e o bot parar de entender a página, você recebe um **alerta** em vez de silêncio.

Cada execução fica registrada em `dados/bot-leilao.sqlite3`, e o log em `dados/logs/bot-leilao.log`.

Cada varredura real também grava um relatório em Markdown em `1OUTPUT/` (por exemplo `2026-10-08_19h37_varredura.md`), com data, hora, veredito, duração e os lotes novos. Lotes já avisados não aparecem. Um relatório existente nunca é sobrescrito, então dá para anotar nele a análise de cada lote. A pasta fica fora do git.

Na mesma pasta, `1OUTPUT/lotes-a-monitorar.md` acumula os lotes avisados (e os da semeadura), para acompanhar os que ainda estão em disputa. O bot só acrescenta lotes no fim desse arquivo; quem tira (martelo batido, lote retirado, lance acima do teto) é você, à mão, ou um agente a seu pedido. As regras estão no topo do próprio arquivo.

## Instalação

Requer Python 3.12 ou mais novo.

```
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows (PowerShell)
source .venv/bin/activate         # Linux/macOS
pip install -e .[dev]
pytest                            # todos verdes, sem internet
```

Copie `.env.example` para `.env` e preencha o token do bot e o seu chat id. O passo a passo, incluindo como criar o bot no Telegram, está em [`onboarding.md`](_reversa_forward/001-mvp-varredura-ponta-a-ponta/onboarding.md).

## Comandos

| Comando | O que faz |
|---|---|
| `python -m bot_leilao varrer` | Executa uma varredura completa |
| `python -m bot_leilao varrer --dry-run` | Coleta de verdade, mas só mostra no console o que enviaria; não grava lotes |
| `python -m bot_leilao testar-telegram` | Envia uma mensagem de teste para conferir o `.env` |

Todos aceitam `--raiz <pasta>` (a pasta com `config/`, `dados/` e `.env`; padrão: a atual).

Códigos de saída: `0` sucesso (inclusive parcial), `1` falha, `2` uso incorreto, `3` outra varredura em andamento.

## Configuração

Na primeira execução, os dois arquivos de `config/` são criados como exemplo, com tudo desativado. Edite-os e troque `ativo` para `true`.

- **Veículos-alvo:** adicionar é colar um bloco, pausar é `ativo: false`. Escreva a marca por extenso (Mitsubishi, Chevrolet): as abreviações do site são traduzidas.
- **Leiloeiros:** a busca é declarada como filtros do site (no Vip, os do formulário; no Claudio Kuss, a `categoria` do evento). Não filtre por marca ou modelo ali; esse recorte é feito pelos veículos-alvo. Para desligar um leiloeiro, `ativo: false` no bloco dele.
- **Segredos:** token e credenciais ficam só no `.env`, que nunca vai para o git e nunca aparece em log.

## Estrutura

```
src/bot_leilao/
  config/        veículos-alvo, leiloeiros, .env, coerência entre alvos e buscas
  coleta/        cliente HTTP, coletor, adaptador por leiloeiro (vip.py, claudio_kuss.py), detalhe dos lotes novos
  parsing/       normalização, sinônimos de marca, parser por leiloeiro (vip.py, claudio_kuss.py)
  filtro/        critérios, deduplicação e semeadura
  notificacao/   resumo, alertas e envio ao Telegram
  db/            SQLite, migrações e trava de execução
  orquestrador.py, cli.py
tests/           testes sem rede; fixtures reais em tests/fixtures/vip/ e tests/fixtures/claudio_kuss/
scripts/         captura das fixtures (capturar_fixtures.py [--claudio-kuss])
```

## Documentação de projeto

Especificações em `_reversa_sdd/` e planos das features em `_reversa_forward/001-mvp-varredura-ponta-a-ponta/` e `_reversa_forward/002-leiloeiro-claudio-kuss/` (roadmap, contratos em `interfaces/`, rastreabilidade em `tests/RASTREABILIDADE.md`). Para adicionar um leiloeiro, siga a lista de armadilhas conhecidas da spec `onboarding-leiloeiro-assistido`.
