# Amostras reais do Freitas Leiloeiro (2026-10-13)

Capturadas no `/reversa-requirements` e no `/reversa-plan` da feature 004, sem login, com a cadeia de certificado completada pelo intermediário oficial (`globalsign-gcc-r6-alphassl-ca-2025.pem`).

| Arquivo | O que é |
|---|---|
| `Pesquisar_categoria1.html` | Página de busca de veículos (casca; os lotes vêm por `PesquisarLotes`) |
| `PesquisarLotes_inteiros_pag2_25-lotes.html` | `GET /Leiloes/PesquisarLotes` com `Condicao=inteiros`, `TopRows=200`, página 2 (25 lotes) |
| `PesquisarLotes_inteiros_pag3_fim.html` | Página 3: "Nenhum lote localizado com os filtros aplicados!" |
| `PesquisarLotes_cards-selecionados.html` | **Composta:** cards reais escolhidos das páginas 1 e 2 (Duster CVT com maior lance; Sentra importado "I/NISSAN SENTRA"; HB20; lote sem etiqueta FINANCEIRA; lote "EM LOTEAMENTO"; grafia "M.BENZ"; lote só com lance inicial) |
| `LoteDetalhes_8112_1_duster-cvt.html` | Detalhe do Duster CVT 2024 (pátio Santo André-SP, despesas R$ 2.350) |
| `LoteDetalhes_8103_3_hb20-ipva-pago.html` | Detalhe com selo "IPVA 2026 PAGO" (pátio Santa Bárbara d'Oeste-SP) |
| `LoteDetalhes_8111_700_em-loteamento.html` | Detalhe de lote em loteamento ("Lote x"; despesas de logística a mais) |
| `globalsign-gcc-r6-alphassl-ca-2025.pem` | Intermediário oficial da GlobalSign (SHA-256 A8:83:55:92…:08:CA; válido até 2027-05-21) |
