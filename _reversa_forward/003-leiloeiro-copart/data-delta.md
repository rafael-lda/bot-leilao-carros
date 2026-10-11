# Data delta: Leiloeiro Copart

> Feature: `003-leiloeiro-copart`
> Base: `_reversa_forward/002-leiloeiro-claudio-kuss/data-delta.md`
> Resumo: só modelos em memória mudam. **Banco inalterado**, sem migração (`PRAGMA user_version` continua 1).

## 1. Modelos em memória

### 1.1 `Lote` (`src/bot_leilao/parsing/modelos.py`) — dois campos novos, opcionais

| Campo | Tipo | Copart | Vip | Claudio Kuss | Usado em |
|-------|------|--------|-----|--------------|----------|
| `patio` | `str \| None` | `yn` ("CAMPO GRANDE - MS"; "LOCAL DO VENDEDOR" fica como veio) | "Local:" do card ("SC") | local do evento na agenda ("Curitiba - PR") | Telegram, relatório, lista |
| `fipe` | `Decimal \| None` | `la` quando > 0 | `None` | `None` | Telegram, relatório (com % do lance), lista |

Campos existentes reaproveitados pela Copart: `pregao_em` (data do leilão, de `ad` em UTC convertida para Brasília), `observacoes` (dano, documento, monta, funcionamento, comitente, Compre Agora). `quilometragem` fica `None` (a busca da Copart não traz km), `evento_id`, `despesas_adm`, `placa_parcial`, `local_documento` e `detalhe_lido` ficam `None`.

### 1.2 `Evento` do Claudio Kuss (`coleta/claudio_kuss.py`)

| Campo | Tipo | Origem |
|-------|------|--------|
| `local` | `str \| None` | linha "Local:" do bloco da agenda; o trecho final "Cidade/UF" vira "Cidade - UF" |

Nova anotação de página `patio` nas páginas `quantidade` e `lotes`.

### 1.3 Saída

| Modelo | Campo novo | Conteúdo |
|--------|------------|----------|
| `ItemDigest` | `patio: str \| None` | texto do pátio |
| `ItemDigest` | `fipe: str \| None` | `FIPE R$ 80.266` |
| `LoteRelatorio` | `patio`, `fipe` | `Pátio: ...`; `FIPE: R$ 80.266 (lance = 45% da FIPE)`, o percentual só com lance e FIPE |

## 2. Banco de dados

**Sem mudança.** Pátio e FIPE são de exibição; `lote_conhecido` continua deduplicando por id canônico (`copart:<ln>`).

## 3. Configuração

`config/leiloeiros.yaml` ganha:

```yaml
  - nome: Copart
    base_url: https://www.copart.com.br
    ativo: true
    estrategia_acesso: publico
    nivel_coleta: script
    buscas:
      - descricao: Recuperados de financiamento, qualquer marca e categoria
        filtros:
          condicao: FINANCIAMENTO
```

Id derivado do nome: `copart`.

## 4. Tabela de sinônimos

Sem grafia nova necessária para os alvos: a Copart escreve as marcas por extenso (`NISSAN`, `RENAULT`, `MERCEDES BENZ` e `MERCEDES-BENZ`, ambas já cobertas). Marcas fora da tabela que aparecem (implementos e máquinas: `LIBRELATO`, `RANDON`, `GUERRA`, `FACCHINI`, `PASTRE`, `JCB`, `MASSEY FERGUSON`, `DIVERSOS`, `OUTROS`, `EQUIPAMENTOS`, `BAU`, `JLRP`) só geram o log informativo de sempre (backlog item 5).
