# Cross-check: MVP de Varredura Ponta a Ponta

> Identificador: `001-mvp-varredura-ponta-a-ponta`
> Data: `2026-10-03`
> Artefatos analisados: [`requirements.md`](../requirements.md), [`roadmap.md`](../roadmap.md), [`actions.md`](../actions.md), com apoio de [`data-delta.md`](../data-delta.md) e [`interfaces/`](../interfaces/)
> Âncora: greenfield. Não há `domain.md` nem `architecture.md`; o eixo "coerência com o legado" foi aplicado contra as specs em `_reversa_sdd/sdd/`.
> Nenhum artefato analisado foi alterado por esta auditoria.

## Resumo

| Severidade | Quantidade |
|------------|------------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 4 |
| LOW | 5 |

## Findings

| ID | Severidade | Eixo | Descrição | Onde está |
|----|------------|------|-----------|-----------|
| A001 | HIGH | Cobertura | Busca com **zero resultados legítimos** dispara falso alerta de quebra. A regra de quebra (RF-07 da feature e do `parser-lotes`) é "conteúdo não vazio e nenhum lote extraído"; a página do Vip para uma busca sem resultados é não vazia (traz `0 resultados encontrados`) e tem zero cards. Nenhuma decisão do roadmap distingue os dois casos, e a T004 captura uma fixture de 0 resultados sem que nenhuma ação diga o comportamento esperado | `requirements.md` RF-07; `roadmap.md` §3 (ausente); `actions.md` T004, T021, T022 |
| A002 | HIGH | Cobertura | O cabeçalho de navegador comum, exigido pelo RF-03 e decidido pelo Rafael em 2026-09-22 (🟢), não aparece em nenhuma decisão do roadmap nem em nenhuma ação ou teste. Só `interfaces/vip-pesquisa.md` o menciona | `requirements.md` RF-03 e §2; `actions.md` T016, T018, T040, T042 |
| A003 | MEDIUM | Consistência | `interfaces/arquivos-configuracao.md` exige que o leiloeiro tenha **adaptador e parser** registrados; o roadmap (D-17, delta do `cadastro-leiloeiros`) e as ações T010/T031 só verificam o adaptador. Leiloeiro com adaptador e sem parser passaria na validação e falharia em tempo de parsing | `interfaces/arquivos-configuracao.md` §3; `actions.md` T010, T031 |
| A004 | MEDIUM | Cobertura | O aviso de carregamento "nenhum alvo ativo aceita um tipo que alguma busca ativa produz", previsto em `interfaces/arquivos-configuracao.md` §2, não tem ação. Sem ele, um alvo sem `financiamento` em `tipos_leilao` nunca casa com o Vip, sem sinal algum | `interfaces/arquivos-configuracao.md` §2; `actions.md` (ausente) |
| A005 | MEDIUM | Cobertura | O conteúdo dos arquivos de exemplo criados quando a configuração está ausente não está amarrado ao contrato: T008 e T029 falam em "exemplo comentado" sem citar `interfaces/arquivos-configuracao.md`. A D-29 (busca ampla, sem marca) só se materializa no código por esse exemplo | `roadmap.md` D-29; `actions.md` T008, T029 |
| A006 | MEDIUM | Consistência | O RF-01 da feature diz "com ao menos um veículo-alvo ativo, abortando… quando a configuração for inválida", o que sugere abortar sem alvo ativo; a spec (`configuracao-veiculos-alvo` RF-08, EC-07) e a ação T009 tratam lista sem ativos como aviso com término bem-sucedido | `requirements.md` RF-01; `actions.md` T009 |
| A007 | LOW | Cobertura | A espera de 1 s entre blocos de um digest dividido (`interfaces/telegram-bot-api.md` §5) não está em T026 nem em T051 | `actions.md` T026, T051 |
| A008 | LOW | Cobertura | O RNF de desempenho (execução < 10 min) não tem ação que o verifique; fica sustentado pela medição do plano (17 páginas, cerca de 2 min) e pela execução real do `onboarding.md` | `requirements.md` §6; `roadmap.md` D-29 |
| A009 | LOW | Consistência | Rastreabilidade por identificador incompleta: RF-02, RF-04 e RF-09 da feature não são citados por ID no roadmap nem nas ações, e RF-03, RF-06, RF-10, RF-11, RF-13 e RF-14 não são citados nas ações. Todos estão cobertos pelo conteúdo (ver "Itens que passaram"); a T060 já prevê a matriz de rastreabilidade | `roadmap.md`; `actions.md` |
| A010 | LOW | Sanidade do actions | Marcador `[//]` ambíguo: seis ações marcadas `[//]` dependem diretamente de outra ação `[//]` da mesma fase (T003→T001, T004→T001, T005→T003, T030→T029, T031→T029, T040→T038). Não há conflito de arquivo, mas o marcador sugere paralelismo que a dependência impede | `actions.md` fases 1 e 3 |
| A011 | LOW | Coerência com as specs | A D-18 aceita `frequencia` sem validação, contrariando o RF-07 do `cadastro-leiloeiros`. Desvio documentado como premissa no roadmap §4, com risco baixo | `roadmap.md` D-18; `_reversa_sdd/sdd/cadastro-leiloeiros.md` RF-07 |

## Impacto e direção dos findings HIGH

**A001, zero resultados vira alarme falso.** Com a busca ampla do Vip, zero resultados é improvável hoje, mas acontece em qualquer leiloeiro pequeno, em feriado, ou numa busca fatiada. Cada ocorrência mandaria "o site provavelmente mudou de layout" ao Telegram, o que treina o Rafael a ignorar alertas, exatamente o efeito que o PRD quer evitar. É também uma lição que vale para qualquer leiloeiro, e não só para o Vip. Direção: uma decisão nova no `roadmap.md` (o parser reconhece o indicador de total do site e trata total zero como busca vazia legítima, sem quebra; quebra continua sendo "total maior que zero e nenhum card"), uma linha no teste T021 e no T022, e, por ser regra geral, um EC no `parser-lotes` e um item na lista de armadilhas do `onboarding-leiloeiro-assistido`. Caminho: edição manual dos artefatos ou `/reversa-clarify`.

**A002, cabeçalho de navegador sem ação.** O `httpx` envia por padrão `User-Agent: python-httpx/<versão>`, que identifica o programa como robô e aumenta a chance de bloqueio pelo Cloudflare, já presente no Vip. A decisão foi tomada pelo Rafael (🟢) e está no requirements, mas pode se perder na codificação por não estar em nenhuma ação. Direção: uma decisão no `roadmap.md` §3.1 fixando o cabeçalho (um `User-Agent` de navegador atual, constante, definido num único lugar) e um item de teste em T016 verificando que toda requisição o carrega. Caminho: edição manual dos artefatos.

## Itens verificados que passaram

### Cobertura

- Os 18 RF da feature têm cobertura de conteúdo no roadmap e em ações: RF-01 (D-04, T009/T030), RF-02 (D-12, T010/T031), RF-03 (D-02, D-10, T016/T040, exceto o cabeçalho, ver A002), RF-04 (interface Vip §4, T016/T040), RF-05 (§5, T022/T047), RF-06 (D-14, T022), RF-07 (T021/T046, exceto zero resultados, ver A001), RF-08 (RN-01 no motor, T023/T048), RF-09 (D-20, T024/T049), RF-10 (D-05, T025/T050/T051), RF-11 (D-22, T052), RF-12 (D-21, T015/T037), RF-13 (D-20, T024), RF-14 (D-25, T054), RF-15 (D-07, T013/T035), RF-16 (D-19, T009/T023), RF-17 (D-16, T023), RF-18 (D-13, T017/T041).
- As 29 decisões têm ao menos uma ação: D-01 a D-09 em T001, T004 e nos módulos correspondentes; D-10 a D-15 e D-28 em T018/T042 e T022/T047; D-16, D-19 em T022/T023; D-17, D-18 em T010; D-20 em T024; D-21 em T053; D-22 em T052; D-23 na estrutura de arquivos; D-24 em T006/T010; D-25 em T054; D-26 em T007/T028; D-27 em T004/T005; D-29 em T029 (parcial, ver A005).
- Os 11 cenários Gherkin estão nas ações T055 (1 a 4), T056 (5 a 8) e T057 (9 a 11).
- O critério de pronto do roadmap tem ação correspondente: segurança do token (T059), rastreabilidade (T060); a execução real está registrada nas notas do `actions.md` como passo humano.

### Consistência

- Termos estáveis entre os três documentos: "digest", "alerta operacional", "semeadura", "veículo-alvo", "busca", "lote retirado", "veredito".
- Identificadores do roadmap que apontam para specs existem nas versões vigentes: RF-10, RF-12, RF-13, RF-14, RF-15 do `coletor-lotes` v1.1; RF-12, EC-13, EC-14 do `parser-lotes` v1.1; RF-10 e seção 6.1.1 do `cadastro-leiloeiros` v1.2.
- Os quatro contratos de `interfaces/` estão listados no roadmap §7.
- As tabelas de `data-delta.md` batem com as ações T012, T014, T015 e com os vereditos das ações T053 e T054.

### Coerência com as specs

- Nenhuma decisão contradiz uma regra 🟢 das specs. Os desvios em relação a regras 🟡 estão declarados como premissa (roadmap §4) ou como divergência para o `/reversa-sync` (roadmap §5, `data-delta.md` §5).
- Todos os componentes citados no delta arquitetural existem em `_reversa_sdd/sdd/`.

### Sanidade do actions

- 61 ações, IDs `T001` a `T061` sem lacuna.
- Todas as dependências apontam para IDs existentes e anteriores.
- Nenhum ciclo de dependência.
- Nenhum arquivo alvo repetido, inclusive entre ações `[//]`.
- Contagens do resumo (61 ações, 50 `[//]`, cadeia de 12) conferem com as tabelas.
