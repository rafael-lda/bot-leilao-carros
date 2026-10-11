# Adendo: Leiloeiro Copart

> Identificador: `003-leiloeiro-copart`
> Data: `2026-10-11`
> Cenário: `greenfield`

## Vigência

Vigente desde 2026-10-11.

## Resumo da entrega

Terceiro leiloeiro do bot: **Copart Brasil**, o de maior volume (1.506 lotes de condição FINANCIAMENTO em 2026-10-11, de todas as categorias), lido pela busca pública em JSON, sem login e sem Apify. Junto, todo aviso, relatório e lista passa a mostrar o **pátio** (onde o carro está) dos três leiloeiros e a **FIPE** quando o leiloeiro informa; os veículos-alvo ganham **palavras a excluir** (ex.: Oroch no alvo Duster); e o bloqueio de um leiloeiro passa a gerar alerta (`requirements.md` §1).

32 de 32 ações concluídas, em três etapas. 559 testes automatizados, sem rede (71 novos), cobrindo RF-01 a RF-10 e os 5 cenários de aceitação. Dry-run real em 2026-10-11: Vip 11 páginas, Kuss 43, Copart 16 (1.506 lotes, sem repetição), sem alerta, 5m47s.

**Como ler as specs agora:** as linhas abaixo dizem o que o código entregue faz de diferente, ou a mais, do que cada spec (e os adendos da 001 e da 002) descreve. Onde a spec e este adendo divergirem, vale o adendo até a próxima re-extração.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/prd.md` | §4 Escopo | componente-novo | Três leiloeiros públicos em nível `script` (Vip, Claudio Kuss, Copart); Milan e Freitas seguem na lista, com acesso via escada do Apify registrada no backlog (item 9). |
| `_reversa_sdd/sdd/cadastro-leiloeiros.md` | §6, §6.1.1 | regra-nova | Na Copart, a busca é declarada pelas facetas do site (`condicao: FINANCIAMENTO`); continua busca ampla. |
| `_reversa_sdd/sdd/coletor-lotes.md` | §6 RF-12, RF-14 | delta-de-contrato-externo | Adaptador `copart`: `GET /vehicleFinderSearch` (cookies do Imperva) e `POST /public/vehicleFinder/search` em formulário, JSON, 100 por página, **sempre `sort=lot_number asc`** (sem ordenação o site repete e omite lotes entre páginas com o total certo); lote repetido gera aviso em log; teto de 40 páginas. Contrato em `_reversa_forward/003-leiloeiro-copart/interfaces/copart-busca.md`. |
| `_reversa_sdd/sdd/coletor-lotes.md` | §6 RF-07, §11 | regra-alterada | Página de desafio do Imperva/Incapsula (`_Incapsula_Resource`, `Incapsula incident`, `Request unsuccessful`) é `bloqueado`, inclusive com status 200 em HTML. |
| `_reversa_sdd/sdd/agendador-observabilidade.md` | §6 (alertas) | regra-alterada | Além de quebra de parser e falha geral, **bloqueio de um leiloeiro** (com os outros funcionando) gera alerta, no máximo 1 por dia por leiloeiro. Antes ficava só no registro. |
| `_reversa_sdd/sdd/parser-lotes.md` | §9 `Lote` | delta-de-dados | `Lote` ganhou `patio` (Vip: UF do "Local:" do card; Kuss: "Cidade - UF" do local do evento; Copart: "CIDADE - UF" do JSON) e `fipe` (Copart). Banco inalterado. |
| `_reversa_sdd/sdd/parser-lotes.md` | §6, §11 | regra-nova | Parser `copart`: id `copart:<ln>`; FIPE do campo `la` (o campo `fv` é o chassi); data do leilão `ad` em UTC convertida para Brasília; "Compre Agora" usa o preço fixo; estado (dano, documento, monta, funcionamento, comitente) nas observações; lote aguardando classificação com "Aguardando classificação da Copart (data, FIPE e lance a definir)". |
| `_reversa_sdd/sdd/configuracao-veiculos-alvo.md` | §9 `VeiculoAlvo` | delta-de-dados | Campo opcional `excluir` (palavra ou lista de palavras não vazias). |
| `_reversa_sdd/sdd/motor-filtros.md` | §6 RF-02 | regra-alterada | O alvo não casa com lote cujo modelo ou título (normalizados) contenha alguma palavra de `excluir`; o lote conta como "sem casar". |
| `_reversa_sdd/sdd/notificador-telegram.md` | §8 | regra-alterada | A 2ª linha do item fica: preço — leiloeiro — km — **pátio** — **FIPE** — pregão (cada parte só quando existe). Relatório e lista ganham "Pátio" e "FIPE" com o lance em % da FIPE. |
| `_reversa_sdd/sdd/onboarding-leiloeiro-assistido.md` | Apêndice, "Lista de armadilhas conhecidas" | regra-nova | Três armadilhas novas observadas na Copart: `paginacao_instavel` (conferir números únicos, não só o total), `campo_enganoso` (nomes abreviados como `fv`/`la`; conferir com CSV ou tela) e `data_em_utc` (datas sem fuso podem estar em UTC). |

## Regras sob vigilância

W019, W020, W021, W022, W023, W024, todos na seção "Observações" (sem peso de regressão, por ser greenfield) de `_reversa_forward/003-leiloeiro-copart/regression-watch.md`.

## Fontes

- `_reversa_forward/003-leiloeiro-copart/legacy-impact.md`
- `_reversa_forward/003-leiloeiro-copart/regression-watch.md`
- `_reversa_forward/003-leiloeiro-copart/requirements.md`
- `_reversa_forward/003-leiloeiro-copart/progress.jsonl`
- `_reversa_forward/003-leiloeiro-copart/roadmap.md` (D-53 a D-73)
- `_reversa_forward/003-leiloeiro-copart/data-delta.md`
- `_reversa_forward/003-leiloeiro-copart/investigation.md`
- `_reversa_forward/003-leiloeiro-copart/actions.md` (notas de execução, incluindo o alerta de bloqueio)
- `_reversa_forward/003-leiloeiro-copart/interfaces/copart-busca.md`
- `_reversa_forward/003-leiloeiro-copart/audit/cross-check.md`
