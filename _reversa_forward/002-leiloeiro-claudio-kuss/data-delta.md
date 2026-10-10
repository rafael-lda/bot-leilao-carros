# Data delta: Leiloeiro Claudio Kuss

> Feature: `002-leiloeiro-claudio-kuss`
> Base: `_reversa_sdd/sdd/parser-lotes.md` §9 e `001-mvp-varredura-ponta-a-ponta/data-delta.md`
> Resumo: só modelos em memória mudam. **Banco inalterado**, sem migração (`PRAGMA user_version` continua 1).

## 1. Modelos em memória

### 1.1 `Lote` (`src/bot_leilao/parsing/modelos.py`) — sete campos novos, todos opcionais

| Campo | Tipo | Origem no Claudio Kuss | Vip | Usado em |
|-------|------|------------------------|-----|----------|
| `evento_id` | `str \| None` | anotação da página (`leilaoID`) | `None` | requisição do detalhe |
| `pregao_em` | `datetime \| None` (com fuso) | anotação da página (agenda) | `None` | digest, relatório, lista |
| `observacoes` | `str \| None` | detalhe `tblInformacoes` | `None` | digest (resumida), relatório e lista (completa) |
| `despesas_adm` | `Decimal \| None` | detalhe `tblDespAdm` | `None` | relatório e lista |
| `placa_parcial` | `str \| None` | detalhe `tblPlaca` | `None` | relatório e lista (reaparições) |
| `local_documento` | `str \| None` | detalhe `tblTransf` | `None` | relatório e lista (custo de transferência) |
| `detalhe_lido` | `bool \| None` | enriquecimento: `True` lido, `False` falhou | `None` (não se aplica) | digest: "observações não lidas" (D-49) |

Os dois primeiros nascem no parser; os demais, no enriquecimento (D-48). Campos existentes sem mudança de significado; `quilometragem` e `lance_inicial` ficam `None` para o Kuss (RN-06, D-45).

### 1.2 `ContextoParsing` — um campo novo

| Campo | Tipo | Significado |
|-------|------|-------------|
| `pagina` | `Mapping[str, object]` (padrão: vazio) | anotações da página sendo lida (D-37). O núcleo cria uma cópia do contexto por página com `dataclasses.replace` |

### 1.3 `Requisicao` e `Pagina` (`src/bot_leilao/coleta/modelos.py`) — um campo novo em cada

| Modelo | Campo | Tipo | Significado |
|--------|-------|------|-------------|
| `Requisicao` | `anotacoes` | `dict \| None` | preenchido pelo adaptador; não vai para a rede |
| `Pagina` | `anotacoes` | `dict` (padrão vazio) | cópia feita pelo coletor |

Anotações do Claudio Kuss:

| Chave | Valores | Páginas |
|-------|---------|---------|
| `tipo` | `agenda`, `quantidade`, `lotes` | todas |
| `categoria` | texto da busca | `agenda` |
| `evento` | `"897"` | `quantidade`, `lotes` |
| `pregao_em` | `datetime` | `quantidade`, `lotes` |

### 1.4 Protocolos (atributos opcionais, lidos com `getattr`)

| Protocolo | Atributo / método | Padrão | Claudio Kuss |
|-----------|-------------------|--------|--------------|
| `Adaptador` | `teto_paginas: int` | 50 (o do coletor) | 120 |
| `Adaptador` | `requisicao_detalhe(lote) -> Requisicao \| None` | ausente (sem enriquecimento) | `op=D` |
| `Parser` | `preco_obrigatorio: bool` | `True` | `False` |
| `Parser` | `aplicar_detalhe(lote, conteudo: bytes) -> None` | ausente | preenche os campos do detalhe e `retirado` |

### 1.5 `ItemDigest` e `LoteRelatorio` (`notificacao/`)

| Modelo | Campo novo | Conteúdo |
|--------|------------|----------|
| `ItemDigest` | `pregao: str \| None` | `Pregão 13/10 10:00` |
| `ItemDigest` | `observacoes: str \| None` | até 160 caracteres, com `…` quando cortado; `observações não lidas; veja o link` quando o detalhe falhou (D-49) |
| `LoteRelatorio` | `pregao`, `despesas_adm`, `documento`, `observacoes` | textos completos; `documento` = `Placa F**-**35, documento de SÃO PAULO` |

`detalhe_lido` (§1.1) distingue "detalhe falhou" de "lote sem observações".

## 2. Banco de dados

**Sem mudança.** Justificativa por tabela:

| Tabela | Por que não muda |
|--------|------------------|
| `lote_conhecido` | Guarda id canônico, leiloeiro, busca, alvo, origem, preço na notificação (nulo já permitido, D-19 da 001) e link. Observações e pregão são de exibição, não de deduplicação |
| `busca_semeada` | A busca do Kuss é uma busca como outra; semeia na primeira execução apta |
| `execucao`, `execucao_leiloeiro`, `execucao_busca` | O número de páginas já é registrado por busca; retirados descobertos no detalhe somam no contador `descartados_retirados` existente |

Lote retirado descoberto no detalhe **não** é gravado: se continuar retirado, é conferido de novo na próxima varredura (1 requisição); se voltar, é avisado.

## 3. Configuração

`config/leiloeiros.yaml` ganha um bloco (sem mudança de esquema):

```yaml
  - nome: Claudio Kuss Leilões
    base_url: https://www.claudiokussleiloes.com.br
    ativo: true
    estrategia_acesso: publico
    nivel_coleta: script
    buscas:
      - descricao: Eventos de veículos de financeiras, qualquer marca
        filtros:
          categoria: Veículos - Financeiras
```

O id derivado do nome é `claudio-kuss-leiloes`, que é a chave de registro do adaptador e do parser.

## 4. Tabela de sinônimos (`parsing/marcas.py`)

| Grafia | Canônica | Fonte |
|--------|----------|-------|
| `chev` | `chevrolet` | Kuss, 2026-10-10 |
| `caoachery` | `caoa chery` | Kuss, 2026-10-10 |
| `m benz` | `mercedes-benz` | Kuss, 2026-10-10 |
| `lr` | `land rover` | Kuss, 2026-10-10 (`IMP LR`, depois de remover `IMP `) |

O prefixo `IMP ` é tratado no parser do Kuss (é convenção do leiloeiro, não grafia de marca).
