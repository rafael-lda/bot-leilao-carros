# Regression Watch: Leiloeiro Copart

> Identificador: `003-leiloeiro-copart`
> Âncora greenfield: o watch principal fica vazio até uma extração `/reversa` confirmar regras. IDs continuam a numeração das features 001 e 002.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-----------------------------|---------------------|-------------------|

## Observações

| ID | Origem | Requisito | Situação |
|----|--------|-----------|----------|
| W019 | `requirements.md` RF-01 a RF-03 | Busca pública da Copart ordenada por número do lote, total conferido, sem repetição | Implementado e testado; dry-run real 2026-10-11: 1.506 lotes, 16 páginas |
| W020 | `requirements.md` RF-04 | Pátio em todo aviso, relatório e lista, dos três leiloeiros | Implementado e testado de ponta a ponta |
| W021 | `requirements.md` RF-05, roadmap D-64, D-65 | FIPE de `la` (nunca `fv`, o chassi); data `ad` em UTC convertida para Brasília | Implementado e testado; observar se a Copart muda o significado dos campos |
| W022 | `requirements.md` RF-07 | Bloqueio do Imperva vira alerta por leiloeiro, 1 por dia, sem derrubar os outros | Implementado e testado; observar a frequência de bloqueios nas varreduras reais (degrau Apify: backlog item 9) |
| W023 | `requirements.md` RF-10 | Palavras a excluir pelo modelo e pelo título | Implementado e testado; Duster Oroch fora no dry-run real |
| W024 | `requirements.md` RF-09 | Varredura completa abaixo de 10 minutos | Medido: 5m47s (2026-10-11); observar se o estoque de financiamento crescer |

## Histórico de re-extrações

## Arquivadas
