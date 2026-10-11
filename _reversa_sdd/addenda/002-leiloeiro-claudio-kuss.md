# Adendo: Leiloeiro Claudio Kuss

> Identificador: `002-leiloeiro-claudio-kuss`
> Data: `2026-10-10`
> Cenário: `greenfield`

## Vigência

Vigente desde 2026-10-10.

## Resumo da entrega

Segundo leiloeiro do bot: **Claudio Kuss Leilões** (Curitiba-PR), leilão por **evento** com data marcada. A cada varredura o bot lê os eventos "Veículos - Financeiras" publicados na agenda do site, aplica os mesmos veículos-alvo do Vip e avisa no mesmo resumo do Telegram, com a data do pregão e as observações de estado de cada lote (o Kuss não tem campo de monta e mistura financiamento e sinistro). Resolve o volume baixo de candidatos com só o Vip (`requirements.md` §1).

34 de 34 ações concluídas, em três etapas. 482 testes automatizados, sem rede (107 novos), cobrindo RF-01 a RF-10 e os 6 cenários de aceitação. Dry-run real em 2026-10-10: Vip 173 lotes em 15 páginas e Kuss 391 lotes em 43 páginas (2 eventos), sem quebra, 5m16s.

**Como ler as specs agora:** as linhas abaixo dizem o que o código entregue faz de diferente, ou a mais, do que cada spec (e o adendo da 001) descreve. Onde a spec e este adendo divergirem, vale o adendo até a próxima re-extração.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/prd.md` | §4 Escopo | componente-novo | Dois leiloeiros públicos em nível `script` (Vip e Claudio Kuss); meta de ≥ 5 leiloeiros segue aberta. Copart, Freitas e Milan bloqueiam acesso automatizado (`_reversa_forward/triagem-leiloeiros-2026-10-10.md`). |
| `_reversa_sdd/sdd/cadastro-leiloeiros.md` | §6 (RF de buscas), §6.1.1 | regra-nova | Uma busca pode ser declarada por **categoria de evento** (`categoria: Veículos - Financeiras`) em vez de filtros de formulário; continua busca ampla, sem marca nem modelo. |
| `_reversa_sdd/sdd/coletor-lotes.md` | §6 RF-12 | delta-de-contrato-externo | Adaptador `claudio-kuss-leiloes`: página 1 = agenda (`GET /proximos-leiloes`); para cada evento da categoria, `op=Q` (quantidade) e `op=P` (10 lotes por página, JSON). Contrato em `_reversa_forward/002-leiloeiro-claudio-kuss/interfaces/claudio-kuss.md`. |
| `_reversa_sdd/sdd/coletor-lotes.md` | §6 RF-14, §9 | regra-alterada | O adaptador pode declarar o próprio teto de páginas (Kuss: 120; padrão continua 50) e anotar cada requisição; as anotações seguem na `Pagina` até o parser. Total lido diferente da quantidade informada vira aviso em log, não falha. |
| `_reversa_sdd/sdd/coletor-lotes.md` | §6 (fluxo) | componente-novo | Etapa de **enriquecimento** depois da filtragem: o detalhe do lote é consultado só para os lotes novos que vão para o aviso, pelo mesmo cliente HTTP; retirados e sucata saem do aviso; falha do detalhe não bloqueia o aviso. |
| `_reversa_sdd/sdd/parser-lotes.md` | §9 `Lote`, `ContextoParsing` | delta-de-dados | `Lote` ganhou `evento_id`, `pregao_em`, `observacoes`, `despesas_adm`, `placa_parcial`, `local_documento` e `detalhe_lido` (todos opcionais); `ContextoParsing` ganhou `pagina` (anotações da página em leitura). Banco inalterado. |
| `_reversa_sdd/sdd/parser-lotes.md` | §6 RF-08 (limite de incompletos) | regra-alterada | Um parser pode declarar `preco_obrigatorio = False`: preço ausente deixa de contar no limite de 30% (antes do pregão, 333 de 346 lotes do Kuss não têm valor). Marca, modelo e ano continuam contando. |
| `_reversa_sdd/sdd/parser-lotes.md` | §6 RF-12, §11 EC-13 a EC-15 | regra-nova | Sinônimos comuns novos: `chev`, `caoachery`, `m benz`, `lr`. Ano `AA/AA` convertido (20AA até o ano corrente + 1, senão 19AA). Id canônico do Kuss pelo `seq` global, não pelo número do lote por evento. Agenda reconhecida é busca vazia; `qtde > 0` sem lotes é quebra. |
| `_reversa_sdd/sdd/notificador-telegram.md` | §7 RNF-04, §8 | regra-alterada | **Item com observações ocupa 4 linhas** (linha `Obs.:`, até 160 caracteres), contra o máximo de 3 do RNF-04, por decisão do Rafael (RF-07 da 002); itens sem observações continuam com 3. A segunda linha ganha `Pregão dd/mm hh:mm` para leilão por evento. |
| `_reversa_sdd/sdd/motor-filtros.md` | §6 RF-01 a RF-08 | regra-nova | Sem mudança no motor; lotes de **sucata** (reconhecida no detalhe: "SUCATA SEM DOCUMENTOS - BAIXADO JUNTO AO DETRAN") e retirados descobertos no detalhe são descartados no enriquecimento, antes do digest, e não gravados em `lote_conhecido`. |
| `_reversa_sdd/sdd/onboarding-leiloeiro-assistido.md` | Apêndice, "Lista de armadilhas conhecidas" | regra-nova | Duas armadilhas novas observadas no Kuss: `preco_ausente_em_massa` (leilão por evento: quase nenhum lote tem valor antes do pregão) e `sucata_na_categoria` (sucata dentro de evento de financeiras, marcada só no detalhe, não na lista JSON). Também confirmadas: `numero_lote_por_evento`, `sinonimos_marca`, `zero_resultados`. |

Emendas da 001 (relatório e lista de monitoramento) também foram estendidas: linhas `Pregão`, `Despesas admin.`, `Documento` e `Observações`, e o rótulo "Preço" para lote sem nenhum preço (ver `legacy-impact.md` da feature).

## Regras sob vigilância

W011, W012, W013, W014, W015, W016, W017, W018, todos na seção "Observações" (sem peso de regressão, por ser greenfield) de `_reversa_forward/002-leiloeiro-claudio-kuss/regression-watch.md`. W017 (link do lote depois do loteamento) depende de conferência depois do pregão de 13/10/2026.

## Fontes

- `_reversa_forward/002-leiloeiro-claudio-kuss/legacy-impact.md`
- `_reversa_forward/002-leiloeiro-claudio-kuss/regression-watch.md`
- `_reversa_forward/002-leiloeiro-claudio-kuss/requirements.md`
- `_reversa_forward/002-leiloeiro-claudio-kuss/progress.jsonl`
- `_reversa_forward/002-leiloeiro-claudio-kuss/roadmap.md` (D-33 a D-52; D-41 e D-43 revistos no coding)
- `_reversa_forward/002-leiloeiro-claudio-kuss/data-delta.md`
- `_reversa_forward/002-leiloeiro-claudio-kuss/actions.md` (notas de execução)
- `_reversa_forward/002-leiloeiro-claudio-kuss/interfaces/claudio-kuss.md`

## Atualização 2026-10-11

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/sdd/motor-filtros.md` | §6 RF-13 (semeadura) | regra-alterada | Semeadura continua sem aviso no Telegram, mas os lotes semeados passam a ser detalhados e listados no relatório da varredura ("Já estavam no site") e na lista `lotes-a-monitorar.md`, marcados "por semeadura"; retirados e sucata não aparecem. Revê a regra da E002 da feature 001. Emenda E001 da feature 002. |
