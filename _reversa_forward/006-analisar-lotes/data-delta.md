# Delta de dados: skill `analisar-lotes`

> Feature: `006-analisar-lotes`
> Data: 2026-10-15

## 1. `config/veiculos-alvo.yaml` (D-107, D-109)

Bloco novo na raiz, opcional:

```yaml
padrao:
  cambio: [automatico, cvt]
  aceitar_sinistro: false
  aceitar_sucata: false
  aceitar_mecanica_com_problema: false
  aceitar_pequenas_avarias: true
veiculos:
  - marca: Renault
    modelo: Fluence
    triagem: "Só 2.0 Dynamique Plus ou Privilège, automáticos. Fora GT Line e 1.6."
    # qualquer campo do padrao pode ser repetido aqui para sobrescrever
    ...
```

| Campo | Tipo | Validação | Sem o campo |
|-------|------|-----------|-------------|
| `cambio` | lista de `automatico`, `cvt`, `manual` (sem acento) | lista não vazia, sem valores fora desses três | aceita qualquer câmbio |
| `aceitar_sinistro`, `aceitar_sucata`, `aceitar_mecanica_com_problema`, `aceitar_pequenas_avarias` | verdadeiro ou falso | só booleano | `true` (aceita) |
| `triagem` | texto | texto não vazio | sem critério em texto |

`VeiculoAlvo` (`src/bot_leilao/config/veiculos.py`) ganha `cambio: tuple[str, ...] | None`, os quatro `aceitar_*: bool` e `triagem: str | None`, já com o padrão aplicado. Só `cambio` é usado pelo bot (D-108); os demais, pela skill.

## 2. `config/custos.yaml` (novo, versionado) (D-115, D-116)

```yaml
cidade_base: Londrina - PR
comissao_percentual: 5
despesa_padrao: 2650          # quando o lote não traz a despesa fixa
frete_por_km: 4.50            # estimativa até haver orçamento de guincho
transferencia_mesmo_estado: 450
transferencia_outro_estado: 650
uf_base: PR
reparos_reserva: 2000
revenda_percentual_fipe: 85
margem_percentual: 10         # sobre o custo na garagem
distancias:                   # opcional: corrige ou completa o cálculo automático (km, ida)
  # "Curitiba - PR": 386
```

Valores do esclarecimento de 2026-10-15. Campo ausente ou inválido aborta a análise com mensagem (não a varredura).

## 3. Caches (fora do git, em `dados/`)

| Arquivo | Conteúdo | Validade |
|---------|----------|----------|
| `dados/fipe-cache.json` | `{"<mês de referência>": {"<código>|<ano-combustível>": {valor, versao, fonte}, "modelos|<marca>": [...]}}` | Mês de referência |
| `dados/distancias.json` | `{"londrina - pr": {"lat":…, "lon":…}, "curitiba - pr": {"km": 386, "fonte": "osrm"}}` | Permanente (a tabela do `custos.yaml` vence) |

## 4. Lista de monitoramento (`1OUTPUT/`, fora do git)

- Linha nova no bloco, antes de `- **Link:**`: `- **Triagem (DD/MM/AAAA):** aprovado | reprovado — <motivo> (<evidência>) | a confirmar — <o que falta>`.
- Campos preenchidos pelo `anotar-custo`: FIPE, "% da FIPE" do lance ao entrar, Despesas admin. (se vazia), Frete, Valor estimado na garagem; linha nova `- **Lance máximo (margem 10%):** R$ …`.
- Arquivo novo `1OUTPUT/lotes-descartados.md`: cabeçalho próprio e os blocos movidos, cada um com `- **Descartado em DD/MM/AAAA:** <motivo> — <evidência>`.
- `comentarios-lotes-a-monitorar.md`: regras da triagem e do arquivo de descartados (texto padrão no bot e arquivo existente atualizado).

## 5. Banco

Sem mudança. O lote descartado continua em `lote_conhecido` e não volta a ser avisado.
