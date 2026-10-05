# Adendo: MVP de Varredura Ponta a Ponta

> Identificador: `001-mvp-varredura-ponta-a-ponta`
> Data: `2026-10-04`
> Cenário: `greenfield`

## Vigência

Vigente desde 2026-10-04.

## Resumo da entrega

Primeira fatia vertical do Bot Leilão Carros: um leiloeiro público (Vip Leilões) varrido por comando manual, do carregamento dos YAML até o digest no Telegram, com deduplicação em SQLite, semeadura na estreia de cada busca, alerta quando o parser quebra e histórico de toda execução. Substitui a busca manual por uma execução verificável (`prd.md` §1).

63 de 63 ações concluídas, em três etapas. 339 testes automatizados, sem rede, cobrindo RF-01 a RF-18 e os 11 cenários de aceitação. Execução real em dry-run contra o Vip em 2026-10-04: 17 páginas, 201 lotes, sem quebra, 1min31s.

**Como ler as specs agora:** as linhas abaixo dizem o que o código entregue faz de diferente, ou a mais, do que cada spec descreve. Onde a spec e este adendo divergirem, vale o adendo até a próxima re-extração.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/prd.md` | §4 Escopo | componente-novo | Escopo do MVP entregue para 1 leiloeiro (Vip), nível `script`, execução manual; agendamento automático, Apify, login e exploração assistida seguem só especificados. |
| `_reversa_sdd/sdd/configuracao-veiculos-alvo.md` | §6 RF-02, §9 `VeiculoAlvo` | componente-novo | Implementada; o alvo tem também `quilometragem_maxima` opcional (RF-16 da feature), e lista sem alvo ativo termina com aviso e sucesso. |
| `_reversa_sdd/sdd/cadastro-leiloeiros.md` | §6 RF-07 | componente-novo | Implementada conforme v1.3, exceto que `frequencia` é aceita como texto sem validação (formato ainda em aberto, OQ-04); leiloeiro ativo `logado` ou com `nivel_coleta` pago é recusado como "não implementado". |
| `_reversa_sdd/sdd/cadastro-leiloeiros.md` | §6.1.1 | regra-nova | Busca ampla aplicada no exemplo e no cadastro real do Vip: só `procedencia: 4` e `monta: 1`; o código também avisa quando um alvo nunca casa com o tipo que as buscas produzem. |
| `_reversa_sdd/sdd/coletor-lotes.md` | §6 RF-02, RF-06, RF-08 | componente-novo | Implementado só o nível `script`, com `User-Agent` de navegador em ponto único (sem rotação); espera entre tentativas de 5 s e 15 s (e não 2 s e 4 s, que ficariam abaixo do intervalo mínimo por host). |
| `_reversa_sdd/sdd/coletor-lotes.md` | §11 EC-02 / §14 OQ-02 | regra-nova | `429` sem `Retry-After` espera 30 s antes de nova tentativa; o Vip devolveu `429` na 17ª requisição a 5 s em 2026-10-04. O intervalo de 5 s foi mantido e fica sob observação. |
| `_reversa_sdd/sdd/coletor-lotes.md` | §6 RF-12 | delta-de-contrato-externo | Adaptador `vip-leiloes`: preparação por `GET /` (cookie `__CBCanal`), busca por `POST /pesquisa?handler=pesquisar` com campos `Filtro.*`, paginação reenviando o mesmo corpo. Contrato completo em `_reversa_forward/001-mvp-varredura-ponta-a-ponta/interfaces/vip-pesquisa.md`. |
| `_reversa_sdd/sdd/parser-lotes.md` | §9 `Lote` | delta-de-dados | `Lote` ganhou `quilometragem`, `situacao`, `retirado` e `titulo` (exibição); com zero lances, `lance_corrente` fica nulo e o motor usa o inicial. |
| `_reversa_sdd/sdd/parser-lotes.md` | §6 RF-12, §11 EC-13 a EC-15 | componente-novo | Implementados conforme v1.2: id canônico pelo id do anúncio, tabela comum de sinônimos de marca, e busca vazia do Vip reconhecida por `div.filter-wait` "Nenhum lote encontrado." (a página vazia não traz indicador de total). |
| `_reversa_sdd/sdd/motor-filtros.md` | §6 RF-01 a RF-08 | regra-nova | Dois critérios a mais: teto de quilometragem opcional (km ausente não elimina) e descarte prévio de lotes retirados, com contador próprio. |
| `_reversa_sdd/sdd/motor-filtros.md` | §9 `LoteNotificado`, §6 RF-13 | delta-de-dados | A tabela chama-se `lote_conhecido`, com coluna `origem` (`notificacao` ou `semeadura`) e `busca_id`; a semeadura é por busca, na tabela nova `busca_semeada`, e só acontece com coleta `ok` e sem quebra. |
| `_reversa_sdd/sdd/notificador-telegram.md` | §8, §9 | componente-novo | Implementado em `parse_mode=HTML` sem prévia de link; a segunda linha de cada item traz também a quilometragem; blocos de até 3800 caracteres com 1 s entre eles; alerta limitado a 1 por dia por leiloeiro. |
| `_reversa_sdd/sdd/agendador-observabilidade.md` | §6 RF-02 a RF-05, RF-12 | componente-novo | Implementados a trava, o histórico e os alertas; **não** implementados o disparo agendado (RF-01), o alerta de taxa de 30 dias (RF-06), as recomendações de frequência (RF-07 a RF-10) e o relatório de saúde (RF-11). |
| `_reversa_sdd/sdd/agendador-observabilidade.md` | §9 Modelo de Dados | delta-de-dados | `execucao` ganhou `motivo`, `modo` (`normal`/`dry_run`), contagens de semeadura e descartes, e o veredito `recusada`; `execucao_leiloeiro` ganhou `alerta_enviado`; nova tabela `execucao_busca` com o registro por busca exigido pelo RF-10 do coletor. Esquema em `data-delta.md` da feature. |
| `_reversa_sdd/sdd/onboarding-leiloeiro-assistido.md` | §6 | componente-novo | Não implementado nesta feature; segue só especificado (v1.1, com a lista de armadilhas conhecidas). |

## Regras sob vigilância

W001, W002, W003, W004, W005, W006, W007, W008, W009, todos na seção "Observações" (sem peso de regressão, por ser greenfield) de `_reversa_forward/001-mvp-varredura-ponta-a-ponta/regression-watch.md`.

## Fontes

- `_reversa_forward/001-mvp-varredura-ponta-a-ponta/legacy-impact.md`
- `_reversa_forward/001-mvp-varredura-ponta-a-ponta/regression-watch.md`
- `_reversa_forward/001-mvp-varredura-ponta-a-ponta/requirements.md`
- `_reversa_forward/001-mvp-varredura-ponta-a-ponta/progress.jsonl`
- `_reversa_forward/001-mvp-varredura-ponta-a-ponta/data-delta.md`
- `_reversa_forward/001-mvp-varredura-ponta-a-ponta/actions.md` (notas de execução)
- `_reversa_forward/001-mvp-varredura-ponta-a-ponta/interfaces/`

## Atualização 2026-10-05

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/sdd/parser-lotes.md` | §11 EC-16 | regra-nova | Quilometragem `0` ou a partir de `900.000` é registrada como nula ("não informada"); com isso `quilometragem_maxima` não elimina carros sem km. Já incorporada à spec na v1.3; ver roadmap D-32 da feature. |
