# Interface: Arquivos de configuração

> Tipo: arquivo, **fornecido pelo Rafael** e lido no início de cada execução
> Specs de origem: `configuracao-veiculos-alvo.md`, `cadastro-leiloeiros.md` v1.1, `notificador-telegram.md`
> Confidência: 🟢 decidido em spec ou esclarecimento, 🟡 inferido

## 1. Regras comuns

| Regra | Confidência |
|-------|-------------|
| UTF-8; BOM detectado aborta com mensagem dizendo o encoding esperado (EC-08 de `configuracao-veiculos-alvo`) | 🟢 |
| Fim de linha CRLF ou LF aceitos indistintamente (arquivo editado no Windows) | 🟡 |
| Leitura com `yaml.safe_load`; erro de sintaxe aborta citando a linha informada pelo parser | 🟢 |
| Arquivo ausente: cria um exemplo comentado no caminho esperado, com tudo `ativo: false`, e aborta orientando a edição (EC-01 das duas specs) | 🟢 |
| Toda rejeição cita o alvo ou leiloeiro, o campo e o valor recebido, e acontece antes de qualquer requisição de rede | 🟢 |
| O programa nunca reescreve um arquivo existente | 🟢 |
| Os dois YAML são versionados em git; o `.env` não | 🟢 |

## 2. `config/veiculos-alvo.yaml`

```yaml
# Veículos que quero encontrar.
# Desative um alvo com `ativo: false` em vez de apagar o bloco.
# ano_min e ano_max referem-se ao ANO DE MODELO (o segundo número em 2018/2019).
# preco_maximo é comparado contra o LANCE CORRENTE do lote.
# quilometragem_maxima é opcional: sem ela, qualquer quilometragem serve.
# Escreva a marca por extenso (Mitsubishi, Chevrolet): o sistema traduz as abreviações do site.
veiculos:
  - marca: Nissan
    modelo: Versa
    ano_min: 2018
    ano_max: 2021
    preco_maximo: 45000
    quilometragem_maxima: 120000
    tipos_leilao:
      - financiamento
    ativo: true
```

| Campo | Tipo | Obrigatório | Regra |
|-------|------|-------------|-------|
| `marca`, `modelo` | texto | sim | Não vazios |
| `ano_min`, `ano_max` | inteiro | sim | 4 dígitos; `ano_min` ≤ `ano_max` |
| `preco_maximo` | número | sim | > 0, em reais |
| `quilometragem_maxima` | inteiro | **não** | > 0 quando presente; ausente ou `null` = sem limite (RN-11) |
| `tipos_leilao` | lista de texto | sim | ≥ 1 valor de `judicial`, `extrajudicial`, `financiamento`, `seguradora`, `recuperado` |
| `ativo` | booleano | não | Padrão `true` |

Com a busca do Vip filtrando procedência 4, só lotes com `tipo_leilao = financiamento` chegam ao motor (roadmap D-15). Um alvo sem `financiamento` na lista não casará com nada do Vip, e o carregamento emite um aviso quando nenhum alvo ativo aceita um tipo que alguma busca ativa produz. 🟡

## 3. `config/leiloeiros.yaml`

```yaml
# Leiloeiros monitorados.
# A senha nunca entra aqui: credencial_env aponta para uma variável no .env.
# Os filtros são os do formulário de busca do site; veja os valores aceitos
# em _reversa_forward/001-mvp-varredura-ponta-a-ponta/interfaces/vip-pesquisa.md
leiloeiros:
  - nome: Vip Leilões
    base_url: https://www.vipleiloes.com.br
    ativo: true
    estrategia_acesso: publico
    nivel_coleta: script
    frequencia: seg-qua-sex-08h      # ainda não usada; o agendamento automático vem em feature futura
    buscas:
      - descricao: Recuperados de financiamento, conservados, qualquer marca
        filtros:
          procedencia: 4   # Recuperado Financiamento
          monta: 1         # Conservado
```

| Campo | Regra nesta feature |
|-------|---------------------|
| `nome` | Não vazio; gera o id (`vip-leiloes`), que precisa ter adaptador e parser registrados (RF-10 do `cadastro-leiloeiros`) |
| `base_url` | Absoluta, `https` |
| `estrategia_acesso` | `publico` ou `logado`; `logado` exige `credencial_env`. Leiloeiro **ativo** `logado` aborta: não implementado nesta feature (roadmap D-17) |
| `nivel_coleta` | `script`, `apify` ou `apify_residencial`, padrão `script`. Leiloeiro **ativo** fora de `script` aborta: não implementado nesta feature (roadmap D-17) |
| `frequencia` | Texto livre, não validado nesta feature (roadmap D-18) |
| `buscas[].filtros` | Mapa não vazio; chaves aceitas pelo adaptador do leiloeiro (tabela em `vip-pesquisa.md#2.1`), senão aborta antes da rede |

A busca recomendada não filtra por marca: o recorte de marca e modelo fica com os veículos-alvo, que o Rafael edita com frequência (roadmap D-29).

## 4. `.env` e `.env.example`

`.env.example`, versionado, documenta as variáveis sem valores:

```dotenv
# Copie para .env e preencha. O .env nunca vai para o git.
# Token do bot, emitido pelo @BotFather no Telegram
TELEGRAM_BOT_TOKEN=
# Id da sua conversa com o bot (veja onboarding.md, passo 3)
TELEGRAM_CHAT_ID=
```

| Variável | Obrigatória quando | Validação |
|----------|--------------------|-----------|
| `TELEGRAM_BOT_TOKEN` | Sempre, exceto em `varrer --dry-run` | Ver `telegram-bot-api.md#1` |
| `TELEGRAM_CHAT_ID` | Idem | Inteiro |
| `<credencial_env>` de cada leiloeiro | Leiloeiro ativo `logado` (não ocorre nesta feature) | Presente e não vazia (RF-05 do `cadastro-leiloeiros`) |

Precedência: variável já exportada no ambiente vence o `.env`. 🟡
