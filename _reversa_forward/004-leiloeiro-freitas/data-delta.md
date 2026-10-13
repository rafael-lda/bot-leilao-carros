# Data delta: Leiloeiro Freitas

> Feature: `004-leiloeiro-freitas`
> Resumo: **nenhum campo novo** e banco inalterado (`PRAGMA user_version` continua 1).

## 1. Campos existentes que o Freitas preenche

| Campo do `Lote` | Origem no Freitas | Etapa |
|-----------------|-------------------|-------|
| `id_canonico` | `freitas-leiloeiro:<leilaoId>-<loteNumero>` | parser (card) |
| `link` | `…/Leiloes/LoteDetalhes?leilaoId=<id>&loteNumero=<n>` | parser |
| `numero_lote` | texto do card (`003`) | parser |
| `titulo`, `marca`, `modelo` | 1ª parte da descrição (`RENAULT/DUSTER INTP CVT`; `I/NISSAN SENTRA 20S FLEX`) | parser |
| `ano_fabricacao`, `ano_modelo` | 2ª parte (`23/24`) | parser |
| `placa_parcial` | 3ª parte (`PLACA: S__-___4` → `S__-___4`) | parser |
| `lance_corrente` / `lance_inicial` | valor do card conforme o rótulo ("Maior lance" / "Lance Inicial") | parser |
| `pregao_em` | data e hora do card (Brasília) | parser |
| `tipo_leilao` | etiqueta do card (`FINANCEIRA` → `financiamento`) | parser |
| `patio` | "Visitação/Retirada: … - CIDADE/UF" | enriquecimento (detalhe) |
| `despesas_adm` | despesas operacionais + logística | enriquecimento |
| `observacoes` | selos do lote ("IPVA 2026 PAGO"); composição das despesas quando há logística | enriquecimento |
| `detalhe_lido`, `retirado` | resultado do detalhe | enriquecimento |

`quilometragem` fica `None` (o Freitas não informa km); `fipe` fica `None`.

## 2. Arquivos novos

| Arquivo | Conteúdo |
|---------|----------|
| `src/bot_leilao/coleta/certificados/globalsign-gcc-r6-alphassl-ca-2025.pem` | Intermediário oficial da GlobalSign (SHA-256 `A8:83:55:92:…:08:CA`, válido até 2027-05-21), distribuído com o pacote |

## 3. Configuração

```yaml
  - nome: Freitas Leiloeiro
    base_url: https://www.freitasleiloeiro.com.br
    ativo: true
    estrategia_acesso: publico
    nivel_coleta: script
    buscas:
      - descricao: Veículos inteiros (sem sinistro), qualquer marca
        filtros:
          categoria: 1
          condicao: inteiros
```

Id derivado do nome: `freitas-leiloeiro`.

## 4. Tabela de sinônimos

| Grafia | Canônica | Fonte |
|--------|----------|-------|
| `m.benz` | `mercedes-benz` | Freitas, 2026-10-13 |
