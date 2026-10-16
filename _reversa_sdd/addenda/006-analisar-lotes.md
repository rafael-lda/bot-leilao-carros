# Adendo: Skill `analisar-lotes` (triagem e custo na garagem)

> Identificador: `006-analisar-lotes`
> Data: `2026-10-16`
> Cenário: `greenfield`

## Vigência

Vigente desde 2026-10-16.

## Resumo da entrega

O bot filtra só o que o site informa em campo; o pente fino da lista `1OUTPUT/lotes-a-monitorar.md` agora é feito por uma **skill de agente** (`analisar-lotes`, em `.claude/skills/` e `.agents/skills/`, criada e avaliada com o `skill-creator`), apoiada numa base determinística na linha de comando do bot (`python -m bot_leilao analise …`). A skill julga; a linha de comando lê, calcula e escreve, com a trava da varredura e escrita atômica.

- **Triagem:** cada lote vira *aprovado*, *a confirmar* (com o que falta), *reprovado* (vai para `lotes-descartados.md` com motivo e evidência; volta com `devolver`) ou *encerrado* (pregão acabado: fica na lista como registro, com o resultado). Na dúvida, a confirmar. Os critérios saem do `veiculos-alvo.yaml` (bloco `padrao` e texto `triagem` de cada alvo).
- **Reconferência:** os "a confirmar" são relidos a cada execução; Lance atual e Pregão são atualizados no bloco.
- **Resultado do pregão, por leiloeiro:** Vip (situação e último lance) e Freitas (status e maior lance) dão o valor; Kuss (só presencial ou online), Milan (só o estado) e Copart (o lote some da busca) não. Com a FIPE conhecida, o resultado leva o % da FIPE. Apelido de quem deu lance nunca é gravado.
- **Custo na garagem:** FIPE (site oficial para buscar versões, parallelum para o valor por código, cache por mês), frete pela distância do pátio a Londrina (Nominatim + OSRM, cache por cidade), comissão, despesa, transferência e reserva de reparos de `config/custos.yaml`; o bloco ganha o valor na garagem, o % da FIPE e o lance máximo para a margem.

45 de 45 ações concluídas: três etapas (T001–T037) e duas emendas antes deste sync (T038–T042: reconferência e resultado por leiloeiro; T043–T045: FIPE com poucos pedidos e veredito encerrado). 838 testes automatizados, sem rede. Quatro rodadas de avaliação da skill (19/19, 20/20, 17/18 contra 16/18 da versão anterior, 10/10). Execução real na lista do Rafael em 2026-10-15, com o OK dele.

**Como ler as specs agora:** as linhas abaixo dizem o que o código entregue faz de diferente, ou a mais, do que cada spec (e os adendos 001 a 005) descreve. Onde a spec e este adendo divergirem, vale o adendo até a próxima re-extração.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/prd.md` | §4 Escopo; Pendências de cobertura ("tabela FIPE") | componente-novo | Existe uma camada de análise feita por agente de IA sobre a lista (skill `analisar-lotes`): triagem, resultado dos pregões e custo na garagem com FIPE. A FIPE entra na lista, não no aviso do Telegram. §5 continua valendo: o lance máximo é referência para o Rafael, nenhum lance é dado. |
| `_reversa_sdd/prd.md` | §7 Dependências externas | delta-de-contrato-externo | Dependências novas, todas sem token: FIPE (site oficial `veiculos.fipe.org.br`, não documentado, e parallelum v2, 500 pedidos em 24 h), Nominatim e OSRM públicos. Contratos em `_reversa_forward/006-analisar-lotes/interfaces/fipe.md` e `distancias.md`. |
| `_reversa_sdd/sdd/configuracao-veiculos-alvo.md` | §6.1, §9 Modelo de Dados | regra-alterada, delta-de-dados | `VeiculoAlvo` ganha `cambio` (automatico, cvt, manual), `aceitar_sinistro`, `aceitar_sucata`, `aceitar_mecanica_com_problema`, `aceitar_pequenas_avarias` e `triagem` (texto livre lido só pela skill). Bloco `padrao` no topo do YAML vale para todos os alvos; cada alvo sobrescreve. Arquivo sem os campos novos continua válido e aceita tudo. |
| `_reversa_sdd/sdd/motor-filtros.md` | §6.1 (RF-02 a RF-06) | regra-alterada | Critério novo: câmbio, aplicado só quando o lote informa (hoje, o Milan) e só com certeza; "automático" contra alvo só CVT não descarta (o Milan escreve AUTOMATICO também para CVT). O descarte soma em `descartados_sem_casar`. |
| `_reversa_sdd/sdd/coletor-lotes.md` | §10 Integrações e Dependências | delta-de-contrato-externo | A leitura de um lote fora da varredura (`analise pagina`) usa o mesmo cliente, nível e conduta: Vip pela página do anúncio, Kuss pelo detalhe e por `json_edital.php op=T`, Copart pela busca com o número do lote, Freitas pelo detalhe e por `RetornarLoteStatus`/`RetornarMaiorLanceLote`, Milan pela página do lote via Apify (~US$ 0,08). Devolve o resultado do pregão quando o site mostra o fim. Contrato em `_reversa_forward/006-analisar-lotes/interfaces/cli-analise.md`; o que cada site mostra, em `.claude/skills/analisar-lotes/references/resultados-por-leiloeiro.md`. |
| `_reversa_forward/001-mvp-varredura-ponta-a-ponta/requirements.md` | Emenda E002 (lista de lotes a monitorar) | regra-alterada, delta-de-dados | A lista deixa de ser só por acréscimo do bot: a skill escreve nela pela linha de comando (linhas Triagem, Resultado do pregão, Lance atual, Pregão, Câmbio deduzido, FIPE, Frete, Manutenções, Valor estimado na garagem, Lance máximo), sem tocar nos números nem no comentário `<!-- lote: … -->`. Arquivo novo `1OUTPUT/lotes-descartados.md`. O texto padrão de `comentarios-lotes-a-monitorar.md` explica a triagem. |
| `_reversa_sdd/sdd/agendador-observabilidade.md` | §8 Design e Interface | componente-novo | Subcomando `analise` (`lotes`, `pagina`, `triar`, `devolver`, `anotar`, `fipe-candidatos`, `fipe-valor`, `custo`, `anotar-custo`), com saída JSON e logs só no arquivo; código 3 quando a varredura está em andamento. Configuração nova `config/custos.yaml` (criada na primeira análise) e caches `dados/fipe-cache.json` e `dados/distancias.json`. |

## Regras sob vigilância

W038, W039, W040, W041, W042, W043, W044, W045, W046, W047, todos na seção "Observações" (sem peso de regressão, por ser greenfield) de `_reversa_forward/006-analisar-lotes/regression-watch.md`. W042 pede a troca do frete estimado pelo orçamento real de guincho; W046 e W047 se confirmam na próxima execução real (reconferência da Copart; lote 1 encerrado).

## Fontes

- `_reversa_forward/006-analisar-lotes/legacy-impact.md`
- `_reversa_forward/006-analisar-lotes/regression-watch.md`
- `_reversa_forward/006-analisar-lotes/requirements.md` (RN-01 a RN-14, RF-01 a RF-16)
- `_reversa_forward/006-analisar-lotes/progress.jsonl`
- `_reversa_forward/006-analisar-lotes/roadmap.md` (D-104 a D-124)
- `_reversa_forward/006-analisar-lotes/data-delta.md`
- `_reversa_forward/006-analisar-lotes/investigation.md`
- `_reversa_forward/006-analisar-lotes/interfaces/cli-analise.md`, `fipe.md`, `distancias.md`
- `_reversa_forward/006-analisar-lotes/audit/cross-check.md`
- `_reversa_forward/006-analisar-lotes/actions.md` (notas de execução)
