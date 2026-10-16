# Bot Leilão Carros

Varre sites de leilão de carros, filtra os lotes pelos veículos que você procura e avisa no Telegram, com marca, modelo, ano, preço e o link do lote.

Hoje monitora cinco leiloeiros. O bot só observa e avisa: ele nunca dá lance. Todo aviso mostra o **pátio** (onde o carro está), porque o frete até Londrina pode inviabilizar o lote.

| Leiloeiro | O que o bot lê | Particularidades |
|---|---|---|
| **Vip Leilões** | Recuperados de financiamento, estado conservado | Leilão contínuo; informa km |
| **Claudio Kuss Leilões** (Curitiba) | Eventos "Veículos - Financeiras" | Leilão por evento com data marcada: o aviso traz a **data do pregão**. Não informa km nem monta, e o evento mistura financiamento e sinistro: o aviso traz as **observações** do lote ("SINISTRADO", "MECÂNICA COM PROBLEMAS"...) para você descartar à mão. Sucata e lotes retirados ficam de fora. Antes do pregão quase nenhum lote tem lance, então a maioria chega como "Preço a confirmar" |
| **Copart** | Condição FINANCIAMENTO (~1.500 lotes, de todas as categorias) | Busca pública, sem login. O aviso traz **pátio, FIPE**, data do leilão e o estado do lote (dano, documento, monta, motor, comitente). A maioria fica no Nordeste e em Goiás, e muitos aguardam classificação (sem data, FIPE nem lance). "Compre Agora" usa o preço fixo |
| **Freitas Leiloeiro** (Santo André e Santa Bárbara d'Oeste-SP) | Veículos "Inteiros" (sem sinistro), só os lotes com a etiqueta FINANCEIRA casam com os alvos | Leilão por evento: o aviso traz o pregão, o pátio e as despesas (R$ 2.350, às vezes mais logística). Lotes "em loteamento" só entram quando ganham número definitivo. O site envia a cadeia de certificado errada: o bot a completa com o intermediário oficial guardado em `src/bot_leilao/coleta/certificados/` |
| **Milan Leilões** (Rod. Raposo Tavares, São Paulo-SP) | Leilões "recuperados de financiamento" da agenda de veículos, todos os lotes | O site inteiro está atrás do Cloudflare: as páginas vêm pelo **Apify** (pago, ver abaixo). Do catálogo saem km, **câmbio**, avisos do estado e o **comitente** (banco, financeira, locadora); o lance atual vem da página do lote, só para os carros que casam com um alvo. Lote que passa do teto depois de lido o lance não é avisado |

## Como funciona

1. Lê os carros que você quer em `config/veiculos-alvo.yaml` e os leiloeiros em `config/leiloeiros.yaml`.
2. Busca no site do leiloeiro todas as páginas de resultado, devagar (5 s entre requisições).
3. Compara cada lote com os seus alvos: marca, modelo, **ano de modelo**, **lance corrente** contra o teto, quilometragem (opcional) e tipo de leilão.
4. Manda **um único resumo** no Telegram com os lotes novos. Lote já avisado não volta.
5. Na primeira vez que uma busca roda, ele só registra o que já existe, sem avisar (senão você receberia o catálogo inteiro). Esses lotes não vão para o Telegram, mas aparecem no relatório (seção "Já estavam no site") e entram na lista de lotes a monitorar, marcados "por semeadura".
6. Se o site mudar de layout e o bot parar de entender a página, você recebe um **alerta** em vez de silêncio.

Cada execução fica registrada em `dados/bot-leilao.sqlite3`, e o log em `dados/logs/bot-leilao.log`.

Cada varredura real também grava um relatório em Markdown em `1OUTPUT/` (por exemplo `2026-10-08_19h37_varredura.md`), com data, hora, veredito, duração e os lotes novos. Lotes já avisados não aparecem. Um relatório existente nunca é sobrescrito, então dá para anotar nele a análise de cada lote. A pasta fica fora do git.

Na mesma pasta, `1OUTPUT/lotes-a-monitorar.md` acumula, numerados, os lotes avisados (e os da semeadura), com campos de custo para preencher (lance atual, frete, manutenções, valor estimado na garagem); as regras e o significado de cada campo ficam em `1OUTPUT/comentarios-lotes-a-monitorar.md`, para acompanhar os que ainda estão em disputa. O bot só acrescenta lotes no fim desse arquivo; quem tira (martelo batido, lote retirado, lance acima do teto) é você, à mão, ou um agente a seu pedido. As regras estão no topo do próprio arquivo.

## Triagem e custo na garagem (skill `analisar-lotes`)

O bot só filtra o que o site informa em campo. O pente fino fica com a skill `analisar-lotes` (Claude Code em `.claude/skills/`, Antigravity e Codex em `.agents/skills/`): no chat do agente, `/analisar-lotes` (ou "analisa os lotes", "quanto fica o lote 5 na garagem").

- **Triagem:** cada lote da lista vira *aprovado*, *a confirmar* (com o que falta) ou *reprovado* (com motivo e evidência). O reprovado vai para `1OUTPUT/lotes-descartados.md` e volta com "devolve o lote N". Na dúvida, nunca reprova.
- **Critérios:** `config/veiculos-alvo.yaml`: bloco `padrao` (câmbio aceito, sinistro, sucata, mecânica, pequenas avarias) e texto `triagem` de cada alvo, em português. O bot também usa o câmbio quando o leiloeiro informa.
- **A confirmar** é reconferido a cada execução: a skill relê o lote, atualiza Lance atual e Pregão e julga de novo.
- **Pregões que já passaram** não são descartados: o lote vira *encerrado* e ganha o resultado, informado por leiloeiro. Vip e Freitas mostram o valor; Kuss (só presencial ou online), Milan (só o estado) e Copart (o lote some da busca) não. Detalhes em `.claude/skills/analisar-lotes/references/resultados-por-leiloeiro.md`.
- **Custo na garagem:** FIPE (parallelum, com o site oficial de reserva), frete pela distância do pátio até Londrina (calculada uma vez por cidade), despesas, transferência e reserva de reparos de `config/custos.yaml`; o bloco ganha o valor na garagem, o % da FIPE e o lance máximo para a margem.
- A skill escreve só pela linha de comando do bot (`python -m bot_leilao analise …`), que não roda junto com uma varredura e nunca mexe nos números nem no comentário dos lotes.

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
| `python -m bot_leilao varrer --sem-pagos` | Varredura sem os leiloeiros pagos (hoje, o Milan): custo zero no Apify |
| `python -m bot_leilao analise …` | Base da skill `analisar-lotes`: `lotes`, `pagina`, `triar`, `devolver`, `anotar`, `fipe-candidatos`, `fipe-valor`, `custo`, `anotar-custo` (saída JSON) |
| `python -m bot_leilao testar-telegram` | Envia uma mensagem de teste para conferir o `.env` |

Todos aceitam `--raiz <pasta>` (a pasta com `config/`, `dados/` e `.env`; padrão: a atual).

Códigos de saída: `0` sucesso (inclusive parcial), `1` falha, `2` uso incorreto, `3` outra varredura em andamento.

Atalhos no Windows (duplo clique): `scripts\varrer.bat` roda **sem os pagos** (o do dia a dia); `scripts\varrer-completo.bat` roda com todos. O agendamento (seg, qua e sex às 08h, `scripts/agendar_windows.ps1`) roda com todos.

## Configuração

Na primeira execução, os dois arquivos de `config/` são criados como exemplo, com tudo desativado. Edite-os e troque `ativo` para `true`.

- **Veículos-alvo:** adicionar é colar um bloco, pausar é `ativo: false`. Escreva a marca por extenso (Mitsubishi, Chevrolet): as abreviações do site são traduzidas. Para tirar versões que o modelo pega junto, use `excluir` (ex.: `excluir: [Oroch]` no alvo Duster tira a picape Duster Oroch); prefira palavras específicas.
- **Leiloeiros:** a busca é declarada como filtros do site (no Vip, os do formulário; no Claudio Kuss, a `categoria` do evento; na Copart, as facetas da busca, como `condicao`; no Freitas, `categoria` e `condicao`). Não filtre por marca ou modelo ali; esse recorte é feito pelos veículos-alvo. Para desligar um leiloeiro, `ativo: false` no bloco dele.
- **Segredos:** token e credenciais ficam só no `.env`, que nunca vai para o git e nunca aparece em log.
- **Apify (leiloeiros pagos):** um leiloeiro com `nivel_coleta: apify` (o Milan) é lido por um ator da loja do Apify que passa pelo Cloudflare. Precisa de `APIFY_TOKEN` no `.env` (console.apify.com → Settings → API & Integrations). Cada página custa cerca de US$ 0,08 (uns US$ 1,90 por mês no ritmo atual, dentro dos US$ 5 do plano gratuito). A seção "Leiloeiros" do relatório mostra as páginas e o gasto da varredura e do mês, e chega um alerta quando o mês passa de 80% do limite. Para espaçar um leiloeiro pago, `intervalo_horas: 72` no bloco dele (lido no máximo a cada 72 h); o bot mede com quantos dias de antecedência cada leilão aparece e avisa se o intervalo ficar curto. Contrato e troca de ator: `_reversa_forward/005-leiloeiro-milan/interfaces/apify.md`.
- **Certificados:** a verificação de certificado nunca é desligada. Se chegar um alerta de certificado de algum leiloeiro, siga `src/bot_leilao/coleta/certificados/LEIA-ME.md` (diagnóstico em 5 minutos e o que fazer em cada caso).

## Estrutura

```
src/bot_leilao/
  config/        veículos-alvo, leiloeiros, .env, coerência entre alvos e buscas
  analise/       lista de monitoramento, FIPE, distâncias, custo na garagem e leitura do lote (skill analisar-lotes)
  coleta/        cliente HTTP, cliente Apify e roteamento por nível, coletor, adaptador por leiloeiro (vip.py, claudio_kuss.py, copart.py, freitas.py, milan.py), detalhe dos lotes novos, certificados/
  parsing/       normalização, sinônimos de marca, parser por leiloeiro (vip.py, claudio_kuss.py, copart.py, freitas.py, milan.py)
  filtro/        critérios, deduplicação e semeadura
  notificacao/   resumo, alertas e envio ao Telegram
  db/            SQLite, migrações, leilões vistos (antecedência) e trava de execução
  orquestrador.py, cli.py
tests/           testes sem rede; fixtures reais em tests/fixtures/ (vip, claudio_kuss, copart, freitas, milan)
scripts/         captura das fixtures (capturar_fixtures.py [--claudio-kuss | --copart | --freitas | --milan]), atalhos varrer.bat e varrer-completo.bat
```

## Documentação de projeto

Especificações em `_reversa_sdd/` e planos das features em `_reversa_forward/001-mvp-varredura-ponta-a-ponta/` `_reversa_forward/002-leiloeiro-claudio-kuss/` `_reversa_forward/003-leiloeiro-copart/` e `_reversa_forward/004-leiloeiro-freitas/` (roadmap, contratos em `interfaces/`, rastreabilidade em `tests/RASTREABILIDADE.md`). Para adicionar um leiloeiro, siga a lista de armadilhas conhecidas da spec `onboarding-leiloeiro-assistido`.
