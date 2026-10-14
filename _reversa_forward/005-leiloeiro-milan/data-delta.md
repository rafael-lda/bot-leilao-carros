# Delta de dados: Leiloeiro Milan e nível Apify

> Feature: `005-leiloeiro-milan`
> Data: 2026-10-13
> Base: `_reversa_sdd/sdd/*.md` mais os adendos 001 a 004

## 1. Modelos em memória

### 1.1 `Lote` (`src/bot_leilao/parsing/modelos.py`)

| Campo | Tipo | Novo/alterado | Regra |
|-------|------|---------------|-------|
| `cambio` | `str \| None` | **novo** | `"automático"`, `"manual"`, `"CVT"` ou `None`. Só o Milan preenche nesta feature; os outros parsers deixam `None`. Não filtra (RN-04) |

O Milan preenche também campos existentes: `evento_id`, `pregao_em`, `observacoes` (avisos, IPVA pago, comitente), `patio`, `placa_parcial` (pelo detalhe: `"final 6"`), `lance_inicial`, `lance_corrente` (pelo detalhe), `situacao` (`sucata`), `retirado` (pelo detalhe).

### 1.2 `LoteRelatorio` (`src/bot_leilao/notificacao/relatorio.py`)

| Campo | Tipo | Novo/alterado | Regra |
|-------|------|---------------|-------|
| `cambio` | `str \| None` | **novo** | copiado do lote; a linha "Câmbio" da lista e do relatório passa a sair preenchida quando houver (hoje sai sempre em branco) |

### 1.3 `Requisicao` (`src/bot_leilao/coleta/modelos.py`)

| Campo | Tipo | Novo/alterado | Regra |
|-------|------|---------------|-------|
| `nivel` | `str` | **novo**, padrão `"script"` | nível pelo qual a requisição sai; carimbado pelo coletor e pelo enriquecimento a partir do `nivel_coleta` do leiloeiro (D-87); não vai para a rede |

### 1.4 `Leiloeiro` (`src/bot_leilao/config/leiloeiros.py`)

| Campo | Tipo | Novo/alterado | Regra |
|-------|------|---------------|-------|
| `intervalo_horas` | `int \| None` | **novo** | opcional; inteiro de 1 a 720; ausente = lido em toda varredura (D-101) |
| `apify_ator` | `str \| None` | **novo** | opcional; só com `nivel_coleta: apify`; precisa ter perfil no código (D-88); ausente = `neatrat/cloudflare-scraper` |
| `frequencia` | `str` | inalterado | continua sem uso; semântica diferente (expressão de agendamento) |

`NIVEIS_IMPLEMENTADOS` passa de `("script",)` para `("script", "apify")`. `apify_residencial` segue recusado como "não implementado".

### 1.5 `Ambiente` (`src/bot_leilao/config/ambiente.py`)

| Campo | Tipo | Novo/alterado | Regra |
|-------|------|---------------|-------|
| `apify_token` | `str \| None` | **novo** | `APIFY_TOKEN` do `.env` (ou do ambiente); exigido só quando a varredura inclui leiloeiro em `apify`; entra em `segredos` (mascarado em log, banco e relatório) |

### 1.6 `ResultadoEnriquecimento` (`src/bot_leilao/coleta/enriquecimento.py`)

| Campo | Tipo | Novo/alterado | Regra |
|-------|------|---------------|-------|
| `acima_do_teto` | `int` | **novo** | lotes que deixaram de casar com o alvo depois do detalhe (lance acima do teto, D-98) |

## 2. Banco (`dados/bot-leilao.sqlite3`)

Esquema passa da versão **1 para a 2** (`PRAGMA user_version`), com migração automática na abertura (`db/migracoes.py`), dentro de uma transação, como a versão 1.

### 2.1 Tabela nova `evento_visto` (D-102)

```sql
CREATE TABLE IF NOT EXISTS evento_visto (
  leiloeiro_id      TEXT NOT NULL,
  evento_id         TEXT NOT NULL,
  rotulo            TEXT,
  pregao_em         TEXT,              -- ISO 8601 com offset
  visto_primeiro_em TEXT NOT NULL,     -- ISO 8601 UTC
  na_semeadura      INTEGER NOT NULL DEFAULT 0,  -- 1: já existia na primeira leitura do leiloeiro; não conta na antecedência
  PRIMARY KEY (leiloeiro_id, evento_id)
);
```

- Gravada só em execução normal (dry-run não grava), com `INSERT OR IGNORE`: a primeira vez fica.
- Fonte: anotações de página com `evento` e `pregao_em` (Milan e Claudio Kuss).
- Antecedência = `pregao_em - visto_primeiro_em`, em dias.

### 2.2 Consultas novas sobre tabelas existentes

- **Última coleta com sucesso de um leiloeiro** (D-101): `MAX(execucao.iniciado_em)` de `execucao_leiloeiro JOIN execucao` com `modo = 'normal'` e `buscas_ok > 0`.
- `execucao_busca.nivel_usado` já aceita `apify`: nenhuma mudança.

Nenhum campo removido. `lote_conhecido` inalterado (câmbio e observações não são persistidos, como hoje).

## 3. Arquivos de configuração

### 3.1 `config/leiloeiros.yaml`: bloco novo

```yaml
  - nome: Milan Leilões
    base_url: https://milanleiloes.com.br
    ativo: true
    estrategia_acesso: publico
    nivel_coleta: apify               # site inteiro atrás do Cloudflare; páginas pelo Apify
    # apify_ator: neatrat/cloudflare-scraper   # padrão; trocar só por ator com perfil no código
    # intervalo_horas: 72                       # opcional: ler o Milan no máximo a cada 72 h
    buscas:
      - descricao: Leilões recuperados de financiamento, todos os lotes
        filtros:
          descricao_contem: recuperados de financiamento
```

Filtros aceitos pelo Milan: só `descricao_contem` (texto). Chave desconhecida aborta antes da rede.

### 3.2 `.env` e `.env.example`

```
APIFY_TOKEN=          # Apify → Settings → API & Integrations. Nunca no chat nem no git.
```

O `.env` do Rafael já tem o token desde 2026-10-13.

## 4. Linha de comando e atalhos

| Item | Mudança |
|------|---------|
| `python -m bot_leilao varrer` | opção nova `--sem-pagos` (D-100) |
| `scripts/varrer.bat` | passa `--sem-pagos` (atalho do dia a dia, só os leiloeiros gratuitos) |
| `scripts/varrer-completo.bat` | **novo**: varredura com todos os leiloeiros ativos, inclusive os pagos |
| `scripts/agendar_windows.ps1` | inalterado: o agendamento roda sem `--sem-pagos` |

## 5. Migração

1. Na primeira execução da versão nova, o banco sobe de 1 para 2 sozinho (tabela `evento_visto` vazia).
2. A primeira varredura com o Milan semeia a busca: candidatos no relatório e na lista, sem Telegram (RF-08); os leilões dessa leitura entram em `evento_visto` com `na_semeadura = 1`.
3. Reversão: `ativo: false` no bloco do Milan. O banco na versão 2 continua compatível com o código desta versão; voltar para um código anterior recusaria o banco ("versão de esquema mais nova", comportamento existente).
