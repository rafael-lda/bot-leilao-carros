# Legacy Impact: Skill `analisar-lotes` (triagem e custo na garagem)

> Identificador: `006-analisar-lotes`
> Atualizado em: `2026-10-15` (concluída: T001–T037, três etapas)
> Âncora greenfield: `prd.md` + specs SDD em `_reversa_sdd/sdd/`, mais os adendos vigentes das features 001 a 005. O "legado" desta feature é o código entregue por elas.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (projeto inteiro liberado pelo Rafael). Escritas restritas, por conduta, aos caminhos do `actions.md`; na lista real (`1OUTPUT/`), só pela linha de comando e com o OK do Rafael.

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/bot_leilao/analise/` (`lista.py`, `custos.py`, `distancias.py`, `fipe.py`, `pagina.py`, `cli.py`) | — | componente-novo, delta-de-contrato-externo | MEDIUM | Base determinística da skill: lista (triagem, descartados, devolução, anotação), custo na garagem, distâncias (Nominatim + OSRM), FIPE (parallelum + site oficial), leitura do lote pelo acesso do bot; subcomandos `analise` (D-104, D-110, D-112, D-114 a D-119) |
| `src/bot_leilao/config/veiculos.py` | `configuracao-veiculos-alvo` | regra-alterada | MEDIUM | Bloco `padrao`, campos `cambio`, `aceitar_*`, `triagem`, com sobrescrita e validação (D-107) |
| `src/bot_leilao/filtro/motor.py` | `motor-filtros` | regra-alterada | MEDIUM | Câmbio usado quando o lote informa, descartando só com certeza (D-108) |
| `src/bot_leilao/cli.py`, `logsetup.py`, `orquestrador.py` | `interfaces/cli.md` da 001; agendador | delta-de-contrato-externo, regra-alterada | LOW | Subcomando `analise` (logs só no arquivo); `Dependencias.transporte_analise` |
| `src/bot_leilao/notificacao/relatorio.py` | emenda E002 da 003 | regra-alterada | LOW | Texto padrão do arquivo de comentários com as regras da triagem (D-113) |
| `.claude/skills/analisar-lotes/`, `.agents/skills/analisar-lotes/` | — | componente-novo | MEDIUM | `SKILL.md` (com o `skill-creator`) e avaliações (D-105, D-106) |
| `.gitignore` | — | regra-alterada | LOW | `…/skills/*` com exceção para esta skill (D-106) |
| `config/veiculos-alvo.yaml`, `config/custos.yaml` | cadastro | regra-alterada (dados), componente-novo (dados) | LOW | Migração aprovada pelo Rafael (D-109); custos do esclarecimento (D-116) |
| `tests/apoio.py`, `tests/fixtures/analise/`, `tests/test_analise_*.py`, `tests/test_cli_analise.py`, `tests/test_skill_analisar_lotes.py` | testes | componente-novo | LOW | Simuladores da FIPE e dos mapas, `op=T` no Kuss; especificação da feature |
| `tests/test_config_veiculos.py`, `test_motor_criterios.py` | testes | regra-alterada | LOW | Testes acrescentados |
| `README.md`, `tests/RASTREABILIDADE.md`, `_reversa_forward/backlog.md` | documentação | regra-alterada | LOW | Skill, comandos, critérios e custos; rastreabilidade (36 referências); itens ★, 1 e 7 do backlog |
| `1OUTPUT/` (fora do git) | lista do Rafael | dados | — | Comentários atualizados (eram iguais ao texto antigo do bot); triagem real gravada com o OK dele; `lotes-descartados.md` criado |

## Diff conceitual por componente

**Lista de monitoramento.** Continua só por acréscimo do bot. A skill passa a escrever nela, mas só por subcomandos que pegam a trava da varredura, gravam de forma atômica e nunca mexem no número nem no comentário do lote. Reprovados mudam de arquivo, e voltam com `devolver`.

**Configuração dos alvos.** O que eram comentários (preferências do Rafael) virou regra lida: `padrao` com campos validados e `triagem` em texto livre para a skill. Um arquivo sem os campos novos continua válido e aceita tudo.

**Motor.** Ganha um critério (câmbio), aplicado só quando o lote informa e só com certeza; "automático" contra um alvo só CVT não descarta, porque o Milan escreve AUTOMATICO também para CVT.

**Análise.** Componente novo, fora da varredura: FIPE com reserva e cache por mês, distância calculada uma vez por cidade, custo e lance máximo determinísticos, leitura do lote pelo mesmo acesso do bot. O Kuss não divulga o valor final dos pregões; a leitura devolve só se houve lance e de que tipo, sem apelido.

## Preservadas

Feature greenfield, sem regras 🟢 extraídas de código por `/reversa`. Preservados por teste os comportamentos dos adendos 001 a 005: varredura, semeadura, deduplicação, lista só por acréscimo do bot, alertas, níveis de coleta. Suíte anterior (727) verde.

## Modificadas

Sem regras 🟢 extraídas. Mudanças visíveis ao Rafael: o bot descarta lote do Milan com câmbio fora do alvo; a lista ganha as linhas Triagem, Resultado do pregão e Lance máximo, e o arquivo `lotes-descartados.md`; o `veiculos-alvo.yaml` ganhou `padrao` e `triagem`.
