# Amostras reais da Copart (2026-10-11)

Respostas de `POST https://www.copart.com.br/public/vehicleFinder/search` (sem login), capturadas no `/reversa-plan` da feature 003.

| Arquivo | Busca |
|---|---|
| `vehicleFinder-search_financiamento_ordenado_pag00.json` | `condicao:"FINANCIAMENTO"`, `sort=lot_number asc`, página 0, 100 lotes (total 1.506) |
| `vehicleFinder-search_financiamento_ordenado_pag15-ultima.json` | mesma busca, página 15 (última, 6 lotes) |
| `vehicleFinder-search_zero-resultados.json` | `condicao:"INEXISTENTE"` (0 resultados) |

O número de cadastro de quem deu o maior lance (`currentHighBidder`) foi trocado por `999999`: o bot não lê esse campo. Contrato em `../interfaces/copart-busca.md`.
| `vehicleFinder-search_lotes-selecionados.json` | **Composta:** lotes reais escolhidos da leitura completa (Duster Oroch 2022 com FIPE, lance e data; Versa 2019 de Campo Grande-MS aguardando classificação; Creta 2021 com data; Versa 2017; um "Compre Agora"; um "LOCAL DO VENDEDOR"), no envelope da página 0, com `totalElements` ajustado |
