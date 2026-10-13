# Adendo: Leiloeiro Freitas

> Identificador: `004-leiloeiro-freitas`
> Data: `2026-10-13`
> Cenário: `greenfield`

## Vigência

Vigente desde 2026-10-13.

## Resumo da entrega

Quarto leiloeiro do bot: **Freitas Leiloeiro** (Santo André e Santa Bárbara d'Oeste-SP), pela busca pública de veículos "Inteiros", sem login e sem Apify. Só os lotes com a etiqueta **FINANCEIRA** casam com os alvos de financiamento. Pátio, despesas e selos do lote vêm do detalhe (lotes novos e semeados). O servidor do Freitas envia a cadeia de certificado errada: o bot passa a confiar também em intermediários oficiais guardados no pacote, sempre com verificação completa, e uma falha de certificado gera alerta que aponta o procedimento de correção (`requirements.md` §1).

20 de 20 ações concluídas, em três etapas. 608 testes automatizados, sem rede (43 novos), cobrindo RF-01 a RF-09 e os 5 cenários. Dry-run real em 2026-10-13: Freitas 255 cards em 3 páginas (21 em loteamento ignorados, 234 lotes), varredura com 4 leiloeiros em 6m43s.

**Como ler as specs agora:** as linhas abaixo dizem o que o código entregue faz de diferente, ou a mais, do que cada spec (e os adendos 001 a 003) descreve. Onde a spec e este adendo divergirem, vale o adendo até a próxima re-extração.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/prd.md` | §4 Escopo | componente-novo | Quatro leiloeiros públicos em nível `script` (Vip, Claudio Kuss, Copart, Freitas); falta o Milan (Cloudflare "managed": degrau Apify, backlog item 9). |
| `_reversa_sdd/sdd/coletor-lotes.md` | §6 RF-12 | delta-de-contrato-externo | Adaptador `freitas-leiloeiro`: `GET /Leiloes/PesquisarLotes` (HTML parcial, `TopRows=200`), paginação **até a mensagem "Nenhum lote localizado"** (nunca por página menor), aviso de lote repetido; detalhe por `GET /Leiloes/LoteDetalhes`. Contrato em `_reversa_forward/004-leiloeiro-freitas/interfaces/freitas.md`. |
| `_reversa_sdd/sdd/coletor-lotes.md` | §6 RF-07, RF-13; §12 Segurança | regra-alterada | O cliente HTTP confia nas raízes do `certifi` **mais** os intermediários oficiais de `src/bot_leilao/coleta/certificados/` (hoje: GlobalSign GCC R6 AlphaSSL CA 2025, válido até 2027-05-21), para todos os hosts; a verificação nunca é desligada (teste varre o código). Falha de verificação vira motivo `certificado: <host>`, sem novas tentativas. |
| `_reversa_sdd/sdd/agendador-observabilidade.md` | §6 (alertas) | regra-alterada | O alerta por leiloeiro (bloqueio, desde a 003) cobre também falha de certificado, 1 por dia, com o texto apontando `src/bot_leilao/coleta/certificados/LEIA-ME.md` (runbook: diagnóstico, casos A a E, troca segura do intermediário). |
| `_reversa_sdd/sdd/parser-lotes.md` | §6, §9 | regra-nova | Parser `freitas-leiloeiro`: id `<leilaoId>-<loteNumero>`; descrição em 5 partes; marca de importado sem barra (`I/NISSAN SENTRA`); "Maior lance" × "Lance Inicial"; **tipo de leilão por lote** (etiqueta FINANCEIRA), e não pela busca; lotes **"EM LOTEAMENTO"** (número provisório) não devolvidos até o loteamento; sinônimo `m.benz`. |
| `_reversa_sdd/sdd/onboarding-leiloeiro-assistido.md` | Apêndice, "Lista de armadilhas conhecidas" | regra-nova | Três armadilhas novas: `cadeia_certificado_errada` (diagnóstico com `openssl s_client -showcerts`; intermediário só do endereço "CA Issuers" da autoridade), `numero_provisorio` (lotes em montagem com número que muda) e `tipo_por_lote` (busca que mistura comitentes). |

## Regras sob vigilância

W025, W026, W027, W028, W029, todos na seção "Observações" (sem peso de regressão, por ser greenfield) de `_reversa_forward/004-leiloeiro-freitas/regression-watch.md`. W026 depende de conferência depois do loteamento do leilão 8111 (pregão 24/10/2026); W027 tem data: o intermediário vence em 2027-05-21.

## Fontes

- `_reversa_forward/004-leiloeiro-freitas/legacy-impact.md`
- `_reversa_forward/004-leiloeiro-freitas/regression-watch.md`
- `_reversa_forward/004-leiloeiro-freitas/requirements.md`
- `_reversa_forward/004-leiloeiro-freitas/progress.jsonl`
- `_reversa_forward/004-leiloeiro-freitas/roadmap.md` (D-74 a D-85)
- `_reversa_forward/004-leiloeiro-freitas/data-delta.md`
- `_reversa_forward/004-leiloeiro-freitas/investigation.md`
- `_reversa_forward/004-leiloeiro-freitas/interfaces/freitas.md`
- `_reversa_forward/004-leiloeiro-freitas/runbook-certificado.md`
- `_reversa_forward/004-leiloeiro-freitas/audit/cross-check.md`
- `_reversa_forward/004-leiloeiro-freitas/actions.md` (notas de execução)
