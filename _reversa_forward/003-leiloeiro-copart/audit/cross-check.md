# Cross-check: Leiloeiro Copart

> Feature: `003-leiloeiro-copart`
> Data: 2026-10-11
> Artefatos: [`requirements.md`](../requirements.md), [`roadmap.md`](../roadmap.md), [`actions.md`](../actions.md) (mais `data-delta.md`, `interfaces/copart-busca.md`)
> Auditoria leitora: nenhum artefato foi alterado.

## Resumo

| Severidade | Quantidade |
|------------|------------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 3 |
| LOW | 4 |

## Findings

| ID | Severidade | Eixo | Descrição | Onde está |
|----|------------|------|-----------|-----------|
| A001 | MEDIUM | Consistência | O critério de aceite do RF-05 espera **linhas separadas** no relatório ("FIPE: R$ 52.784", "Leilão: 13/10 20:00", "Monta: Não Aplicável", "Documento: NORMAL", "Motor dá partida e engrena"), mas o D-66 junta dano, documento, monta, funcionamento e comitente na linha **Observações**, e o D-71 mostra a data como **Pregão**. Só FIPE ganha linha própria. Um teste escrito pelo critério do RF-05 falharia contra o desenho | `requirements.md` RF-05 × `roadmap.md` D-66, D-71 |
| A002 | MEDIUM | Cobertura | A RN-06 promete o lote aguardando classificação "com a data do leilão **a definir**", mas o D-65 deixa `pregao_em = None` e o D-71 simplesmente omite o pregão; nenhuma ação mostra "a definir". O texto "Aguardando classificação da Copart" nas observações (D-66) cobre a intenção, não a redação | `requirements.md` RN-06 × `roadmap.md` D-65, D-66, D-71; nenhuma ação |
| A003 | MEDIUM | Cobertura (rastreabilidade) | RF-01, RF-03, RF-08 e RF-09 não são citados pelo identificador no roadmap nem nas ações. Estão cobertos em conteúdo (RF-01 → D-57 e T027; RF-03 → D-61 a D-67 e T008/T023; RF-08 → §8 do roadmap e T014; RF-09 → R-05, critério de pronto e T029), mas a rastreabilidade depende de leitura | `roadmap.md` §3; `actions.md` |
| A004 | LOW | Cobertura | D-73 (alvo Duster com `excluir: [Oroch]`; campo no exemplo do YAML) não é citado por nenhuma ação; T016 e T028 fazem o trabalho, mas citam só o D-72 | `actions.md` T016, T028 |
| A005 | LOW | Consistência | Pátio do Kuss escrito "Curitiba-PR" no requirements (RN-04, RF-04) e "Curitiba - PR" no roadmap, data-delta e actions (D-70, T010) | `requirements.md` RN-04, RF-04 × `roadmap.md` D-70 |
| A006 | LOW | Consistência | Na lista de regras, RN-09 aparece antes de RN-08; na tabela de requisitos, RF-10 antes de RF-09 (inserção posterior) | `requirements.md` §4, §5 |
| A007 | LOW | Consistência | "Leilão" (RF-05, cenário) e "Pregão" (D-71, onboarding) para a mesma informação | `requirements.md` RF-05 × `roadmap.md` D-71 |

## Impacto e direção

Não há CRITICAL nem HIGH. Os três MEDIUM são de redação entre documentos; nenhum muda o desenho técnico. Direção sugerida (correção humana ou por `/reversa-clarify`; esta auditoria não altera nada):

- **A001 e A007:** alinhar o critério do RF-05 ao desenho (FIPE e pátio em linha própria; dano, documento, monta, funcionamento e comitente em Observações; data como Pregão), ou mudar o desenho para linhas separadas. O desenho atual reaproveita o formato da 002 e mantém o aviso curto.
- **A002:** decidir se o aviso mostra "Pregão a definir" quando não há data (uma linha no D-71 e um item no teste T012), ou ajustar a RN-06 para "sem data, com a observação Aguardando classificação".
- **A003:** citar os RFs nas decisões e ações correspondentes, para a rastreabilidade mecânica do `tests/RASTREABILIDADE.md` (T031) sair direta.

## Itens verificados que passaram

**Cobertura**
- RF-02, RF-04, RF-05, RF-06, RF-07 e RF-10 citados em decisões do roadmap; RF-10 citado nas ações.
- Todas as 21 decisões (D-53 a D-73) existem; todas, exceto D-73, são citadas por ação (diretamente ou em intervalos "D-53 a D-59", "D-61 a D-67").
- Os 5 cenários Gherkin estão em T014; a exclusão da Oroch e a semeadura nos documentos também.

**Consistência**
- Identificadores: nenhuma ação cita decisão inexistente; "RF-12" no roadmap refere-se às specs (`coletor-lotes.md`, `parser-lotes.md`), não ao requirements.
- O contrato `interfaces/copart-busca.md` aparece no roadmap (§7) e bate com D-53 a D-67 (endpoint, ordenação, campos `la`/`fv`/`ad`).
- Termos "pátio", "FIPE", "Compre Agora", "excluir", "Imperva" e `lot_number` usados de forma uniforme.

**Coerência com o legado** (âncora greenfield: specs + adendos)
- `motor-filtros` RF-02 ("contém"): a exclusão é critério adicional, não contradiz; registrada como regra alterada no delta.
- `configuracao-veiculos-alvo` §9: campo novo opcional, registrado no data-delta.
- `notificador-telegram` RNF-04: a 4ª linha (Obs.) já foi revista pelo adendo da 002; a Copart a reaproveita.
- Semeadura sem aviso (RF-13 da 001, E001 da 002): mantida.

**Sanidade do actions**
- 32 ações, nenhuma dependência apontando para ID inexistente, nenhum ciclo; maior cadeia = 9 (confere com o resumo).
- Nenhum par de ações `[//]` compartilha arquivo alvo; 26 paralelizáveis (confere).
