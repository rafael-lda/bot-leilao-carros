# Regression Watch: Leiloeiro Claudio Kuss

> Identificador: `002-leiloeiro-claudio-kuss`
> Âncora greenfield: não há regras 🟢 extraídas de código para vigiar. O watch principal fica vazio até uma extração `/reversa` sobre o código confirmar regras. IDs continuam a numeração da 001 (W001 a W010) para não haver ambiguidade.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-----------------------------|---------------------|-------------------|

## Observações

Requisitos especificados por teste nesta feature, sem peso de regressão até confirmação por re-extração.

| ID | Origem | Requisito | Situação |
|----|--------|-----------|----------|
| W011 | `requirements.md` RF-01 a RF-04 | Busca por categoria; eventos descobertos na agenda; todas as páginas de cada evento conferidas com a quantidade; lote normalizado | Implementado e testado; dry-run real 2026-10-10: 391 lotes em 43 páginas, sem divergência |
| W012 | `requirements.md` RF-05, roadmap D-43 revisto | Detalhe só dos lotes novos; retirados e sucata fora do aviso | Implementado e testado; observar se o Kuss passa a escrever a sucata de outro jeito no detalhe |
| W013 | `requirements.md` RF-06, RF-07 | Pregão e observações no aviso; observações completas, despesas e documento no relatório e na lista | Implementado e testado |
| W014 | `requirements.md` RF-08 | Sem eventos ou `qtde = 0` é busca vazia; agenda sem blocos ou `qtde > 0` sem lotes é quebra | Implementado e testado; observar alarme falso em período sem leilões (R-03) |
| W015 | `requirements.md` RF-09, RF-10 | Semeadura e deduplicação também no Kuss; falha de um leiloeiro não derruba o outro | Implementado e testado de ponta a ponta |
| W016 | `notificador-telegram.md` RNF-04 × RF-07 da 002 | Itens do Vip continuam com no máximo 3 linhas; só itens com observações têm a 4ª | Implementado e testado; spec a atualizar no `/reversa-sync` |
| W017 | roadmap D-38 (premissa) | Link `/lance/<ev>/0/<seq>` abre o lote também depois do loteamento | **A conferir depois do pregão de 13/10/2026** (onboarding §6) |
| W018 | `requirements.md` RNF desempenho | Varredura completa abaixo de 10 minutos | Medido: 5m16s (2026-10-10); observar quando houver mais de dois eventos de financeiras |

## Histórico de re-extrações

## Arquivadas
