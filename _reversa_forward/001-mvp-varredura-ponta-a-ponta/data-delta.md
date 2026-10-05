# Data Delta: MVP de Varredura Ponta a Ponta

> Identificador: `001-mvp-varredura-ponta-a-ponta`
> Data: `2026-10-03`
> Base de comparação: modelos de dados das specs em `_reversa_sdd/sdd/` (seção 9 de cada uma). Projeto greenfield, sem banco preexistente.
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Objetos em memória

### 1.1 `VeiculoAlvo` (`configuracao-veiculos-alvo.md#9`)

| Campo | Situação | Tipo | Regra | Confidência |
|-------|----------|------|-------|-------------|
| `quilometragem_maxima` | **novo** | `int?` | Opcional; quando presente, inteiro > 0. Ausente ou `null` = sem limite (RN-11, RF-16) | 🟢 |
| `id` | mantido, regra concretizada | `string` | `<marca>-<modelo>-<ano_min>-<ano_max>`, normalizado em minúsculas, sem acento, espaços viram hífen | 🟡 |

Os demais campos ficam como na spec.

### 1.2 `Leiloeiro` e `Busca` (`cadastro-leiloeiros.md#9`, v1.1)

Sem campos novos: a emenda v1.1 já trouxe `Busca.filtros`. Esta feature apenas concretiza as regras de derivação:

| Campo | Regra concreta | Confidência |
|-------|----------------|-------------|
| `Leiloeiro.id` | Nome em minúsculas, sem acento, sequências de caracteres não alfanuméricos viram um hífen: `Vip Leilões` → `vip-leiloes` | 🟡 |
| `Busca.id` | `<leiloeiro_id>:<sha1(json.dumps(filtros, sort_keys=True, ensure_ascii=False))[:10]>` | 🟡 |
| `Leiloeiro.frequencia` | Texto opaco, sem validação nesta feature (roadmap D-18) | 🟡 |

### 1.3 `RespostaBruta` e `Pagina` (`coletor-lotes.md#9`, v1.1)

Sem mudança sobre a v1.1.

### 1.4 `Lote` (`parser-lotes.md#9`)

| Campo | Situação | Tipo | Regra | Confidência |
|-------|----------|------|-------|-------------|
| `quilometragem` | **novo** | `int?` | Texto `228.227 Km` → `228227`; ausente, ilegível, `0` ou a partir de `900.000` → `null` (sentinela de "não informada", roadmap D-32) | 🟢 |
| `situacao` | **novo** | `string?` | Texto do card como veio da origem (`Aberto para lances`) | 🟢 |
| `retirado` | **novo** | `bool` | `true` quando `situacao` ou a classe CSS do card contiver "retirad" (sem caixa, sem acento); padrão `false` | 🟡 |
| `id_canonico` | mantido, regra concretizada para o Vip | `string` | `vip-leiloes:<id numérico do anúncio>`, tirado do sufixo da URL `/evento/anuncio/<slug>-<id>`. O número "Lote: N" do card é por evento e **não** serve (roadmap D-14) | 🟢 |
| `numero_lote` | mantido | `string?` | No Vip, o número exibido no card ("Lote: 21"); só para exibição | 🟢 |
| `tipo_leilao` | mantido, origem redefinida | `string?` | Herdado da busca pelo adaptador (`procedencia: 4` → `financiamento`), e não lido do card (RN-10, roadmap D-15) | 🟡 |

### 1.5 `ResultadoParsing` (`parser-lotes.md#9`)

Sem mudança.

### 1.6 `ResultadoFiltragem` (`motor-filtros.md#9`)

| Campo | Situação | Tipo | Regra | Confidência |
|-------|----------|------|-------|-------------|
| `descartados_retirados` | **novo** | `int` | Lotes descartados antes da filtragem por `retirado = true` (RF-17) | 🟢 |
| `descartados_acima_km` | **novo** | `int` | Lotes que casariam, mas excedem `quilometragem_maxima` do alvo | 🟡 |
| `semeados` | **novo** | `int` | Candidatos registrados como conhecidos sem notificação, por semeadura (RN-07) | 🟡 |

## 2. Banco SQLite

Arquivo: `dados/bot-leilao.sqlite3`, fora do versionamento (`.gitignore` já cobre `*.sqlite3`; acrescentar `dados/`).
Versão de esquema controlada por `PRAGMA user_version`. Esta feature cria a **versão 1**.
Conexão com `PRAGMA foreign_keys = ON` e `busy_timeout = 10000` (EC-02 do `motor-filtros`, EC-04 do `agendador-observabilidade`).
Instantes gravados como texto ISO 8601 em UTC com sufixo `Z` (RNF-04 do `agendador-observabilidade`).

### 2.1 `lote_conhecido` — substitui `LoteNotificado` (`motor-filtros.md#9`)

A spec chama a tabela de `LoteNotificado`. Ela passa a guardar também os lotes semeados, que nunca foram notificados, daí o nome novo e a coluna `origem`.

```sql
CREATE TABLE lote_conhecido (
  id_canonico          TEXT PRIMARY KEY,
  leiloeiro_id         TEXT NOT NULL,
  busca_id             TEXT NOT NULL,
  alvo_id              TEXT NOT NULL,           -- primeiro alvo que casou (RF-11 do motor)
  origem               TEXT NOT NULL CHECK (origem IN ('notificacao', 'semeadura')),
  preco_na_notificacao NUMERIC,                 -- lance corrente, ou inicial se sem lance; nulo se a confirmar
  lance_inicial        NUMERIC,
  link                 TEXT NOT NULL,
  registrado_em        TEXT NOT NULL            -- instante da confirmação do envio, ou da semeadura
);
CREATE INDEX ix_lote_conhecido_registrado_em ON lote_conhecido (registrado_em);
CREATE INDEX ix_lote_conhecido_leiloeiro ON lote_conhecido (leiloeiro_id);
```

| Mudança sobre a spec | Motivo | Confidência |
|----------------------|--------|-------------|
| Nome `lote_conhecido` | Semeados não foram notificados | 🟡 |
| `origem` | Distinguir semeadura de notificação real na auditoria e na métrica de "novos por semana" | 🟡 |
| `busca_id` | Permite auditar e, se preciso, refazer a semeadura de uma busca | 🟡 |
| `notificado_em` → `registrado_em` | Mesmo papel, nome coerente com `origem` | 🟡 |

Gravação dos notificados numa transação única, **depois** da confirmação do notificador (RNF-02 e RNF-03 do `motor-filtros`, RN-06).

### 2.2 `busca_semeada` — **nova**

```sql
CREATE TABLE busca_semeada (
  busca_id    TEXT PRIMARY KEY,
  semeada_em  TEXT NOT NULL,
  execucao_id TEXT NOT NULL REFERENCES execucao (id)
);
```

Uma busca é inserida aqui apenas na execução em que teve coleta `ok` e parsing sem quebra (roadmap D-20). Busca ausente desta tabela está em modo de semeadura. Mudar os filtros de uma busca muda o `busca_id` e, portanto, provoca nova semeadura daquela busca, que é o comportamento desejado: filtros novos trazem catálogo novo. 🟡

### 2.3 `execucao` (`agendador-observabilidade.md#9`)

```sql
CREATE TABLE execucao (
  id                     TEXT PRIMARY KEY,      -- UUID4
  iniciado_em            TEXT NOT NULL,
  finalizado_em          TEXT,                  -- nulo = interrompida sem encerramento
  duracao_ms             INTEGER,
  veredito               TEXT CHECK (veredito IN ('sucesso', 'sucesso_parcial', 'falha', 'recusada')),
  motivo                 TEXT,                  -- ex.: config_invalida, banco_inacessivel, falha_total_rede
  modo                   TEXT NOT NULL CHECK (modo IN ('normal', 'dry_run')),
  alvos_ativos           INTEGER,
  lotes_vistos           INTEGER,
  lotes_candidatos       INTEGER,
  lotes_novos            INTEGER,
  lotes_ja_conhecidos    INTEGER,
  lotes_semeados         INTEGER,
  descartados_sem_casar  INTEGER,
  descartados_dado_ausente INTEGER,
  descartados_retirados  INTEGER,
  digest_enviado         INTEGER NOT NULL DEFAULT 0   -- booleano
);
CREATE INDEX ix_execucao_iniciado_em ON execucao (iniciado_em);
```

| Mudança sobre a spec | Motivo | Confidência |
|----------------------|--------|-------------|
| `veredito` aceita `recusada` | Segunda execução simultânea fica registrada (cenário "Segunda execução simultânea é recusada"). Ela grava só a linha de recusa, sem processar | 🟡 |
| `motivo` | Torna legível a falha antes da coleta (config, banco, trava) | 🟡 |
| `modo` | Execuções `--dry-run` não podem entrar na série de recomendação de frequência futura | 🟡 |
| `alvos_ativos`, `lotes_semeados`, `descartados_*`, `digest_enviado` | Contagens que o RF-12 da feature e o log das specs já exigem | 🟢 |

### 2.4 `execucao_leiloeiro` (`agendador-observabilidade.md#9`)

```sql
CREATE TABLE execucao_leiloeiro (
  execucao_id       TEXT NOT NULL REFERENCES execucao (id),
  leiloeiro_id      TEXT NOT NULL,
  buscas_ok         INTEGER NOT NULL DEFAULT 0,
  buscas_bloqueadas INTEGER NOT NULL DEFAULT 0,
  buscas_falhas     INTEGER NOT NULL DEFAULT 0,
  lotes_novos       INTEGER NOT NULL DEFAULT 0,
  quebra_suspeita   INTEGER NOT NULL DEFAULT 0,   -- booleano
  alerta_enviado    INTEGER NOT NULL DEFAULT 0,   -- booleano; base do limite de 1 alerta por dia (D-22)
  PRIMARY KEY (execucao_id, leiloeiro_id)
);
CREATE INDEX ix_execucao_leiloeiro_leiloeiro ON execucao_leiloeiro (leiloeiro_id);
```

Mudança sobre a spec: `alerta_enviado` (roadmap D-22). 🟡

### 2.5 `execucao_busca` — **nova**

O RF-10 do `coletor-lotes` exige registrar, por busca, início, duração, código de resposta, nível, tentativas e veredito, e o RF-03 da feature exige que "o registro da execução marque o nível `script`". As tabelas da spec do agendador só agregam por leiloeiro, então falta o nível de detalhe por busca.

```sql
CREATE TABLE execucao_busca (
  execucao_id      TEXT NOT NULL REFERENCES execucao (id),
  busca_id         TEXT NOT NULL,
  leiloeiro_id     TEXT NOT NULL,
  iniciado_em      TEXT NOT NULL,
  duracao_ms       INTEGER NOT NULL,
  status_http      INTEGER,
  nivel_usado      TEXT NOT NULL CHECK (nivel_usado IN ('script', 'apify', 'apify_residencial')),
  tentativas       INTEGER NOT NULL,
  paginas          INTEGER NOT NULL DEFAULT 0,
  veredito         TEXT NOT NULL CHECK (veredito IN ('ok', 'bloqueado', 'falha_rede', 'falha_autenticacao')),
  motivo           TEXT,
  lotes_extraidos  INTEGER,
  lotes_descartados_parser INTEGER,
  quebra_suspeita  INTEGER NOT NULL DEFAULT 0,
  motivo_quebra    TEXT,
  PRIMARY KEY (execucao_id, busca_id)
);
```

🟡

## 3. Migrações

| Versão | Conteúdo | Quando roda |
|--------|----------|-------------|
| 0 → 1 | Cria as cinco tabelas e os índices acima | Na primeira execução, de forma idempotente, dentro de uma transação; `user_version` passa a 1 no mesmo commit |

Não há dado a migrar. Banco com `user_version` maior que o conhecido pelo código aborta a execução com mensagem, em vez de operar sobre esquema desconhecido. 🟡

## 4. Arquivos de configuração

Formato detalhado em `interfaces/arquivos-configuracao.md`. Delta resumido:

| Arquivo | Mudança sobre as specs |
|---------|------------------------|
| `config/veiculos-alvo.yaml` | Campo opcional `quilometragem_maxima` por alvo |
| `config/leiloeiros.yaml` | Nenhuma além da v1.1 do `cadastro-leiloeiros`; chaves de filtro do Vip documentadas |
| `.env` | Variáveis `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`, já previstas pelo `notificador-telegram`, agora com nome fixado |

## 5. Pendências de convergência nas specs

Após a entrega, o `/reversa-sync` deve levar para `_reversa_sdd/` estes deltas, que hoje só existem na feature:

1. `configuracao-veiculos-alvo.md#9`: `quilometragem_maxima`.
2. `parser-lotes.md#9`: `quilometragem`, `situacao`, `retirado`. (A regra de identificador único e a tabela de sinônimos de marca já foram levadas à spec na v1.1, em 2026-10-03, por valerem para qualquer leiloeiro.)
3. `motor-filtros.md#6` e `#9`: critério de km, descarte de retirados, tabela renomeada para `lote_conhecido` com `origem`, `busca_semeada`.
4. `agendador-observabilidade.md#9`: `execucao_busca`, colunas novas de `execucao` e `execucao_leiloeiro`.
5. `coletor-lotes.md`: endpoint, cookie `__CBCanal` e contrato de paginação do Vip, hoje só em `interfaces/vip-pesquisa.md`, como referência do adaptador `vip-leiloes`.
