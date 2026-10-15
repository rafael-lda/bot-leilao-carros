# Adendo: Leiloeiro Milan (e o nível Apify)

> Identificador: `005-leiloeiro-milan`
> Data: `2026-10-15`
> Cenário: `greenfield`

## Vigência

Vigente desde 2026-10-15.

## Resumo da entrega

Quinto e último leiloeiro da lista do Rafael: **Milan Leilões** (Rod. Raposo Tavares, km 20, São Paulo-SP), o primeiro **pago**. O site inteiro fica atrás do Cloudflare; as páginas vêm por um ator da loja do Apify (`neatrat/cloudflare-scraper`, ~US$ 0,08 por página), pelo nível de coleta `apify`, agora implementado. O bot lê a agenda de veículos, escolhe os leilões "recuperados de financiamento" e lê o catálogo de cada um em toda varredura (km, câmbio, avisos do estado, comitente); o lance atual vem da página do lote, só para os candidatos, e o lote que passa do teto depois desse detalhe não é avisado (regra que vale para todos os leiloeiros). Ritmo e custo: `--sem-pagos` (atalho `varrer.bat`) e `varrer-completo.bat`; `intervalo_horas` por leiloeiro; antecedência dos leilões medida pelo bot; consumo do Apify no relatório e alerta a 80% do limite do ciclo. A regra anti-bot foi corrigida pelo Rafael: proteção anti-bot (inclusive CAPTCHA) é resolvida por ferramenta robusta, mesmo paga, nunca por remendo no código. A troca automática `script` → `apify` (RF-07) ficou para o backlog (item 10).

43 de 43 ações concluídas, em três etapas. 727 testes automatizados, sem rede (119 novos), cobrindo RF-01 a RF-14 (RF-07 Won't) e os 5 cenários. Dry-run real em 2026-10-14: 5m49s com os 5 leiloeiros; Milan lido pelo Apify (agenda sem leilão de financiamento no dia).

**Como ler as specs agora:** as linhas abaixo dizem o que o código entregue faz de diferente, ou a mais, do que cada spec (e os adendos 001 a 004) descreve. Onde a spec e este adendo divergirem, vale o adendo até a próxima re-extração.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/prd.md` | §4 Escopo | componente-novo | Os cinco leiloeiros da lista-alvo estão ativos: Vip, Claudio Kuss, Copart e Freitas em `script`; Milan em `apify` (primeiro leiloeiro pago). |
| `_reversa_sdd/sdd/coletor-lotes.md` | §6 RF-03, §10 Integrações | componente-novo, delta-de-contrato-externo | O nível `apify` existe: cliente próprio (`coleta/apify.py`) que chama a API síncrona do Apify com um ator da loja (só GET de URL), token só no cabeçalho, até 2 tentativas (nenhuma para token ou cota), desafio reconhecido só pela tela de desafio. Cada requisição carrega o nível do leiloeiro e um roteador escolhe o cliente; nada de leiloeiro `apify` sai pelo IP local. Contrato em `_reversa_forward/005-leiloeiro-milan/interfaces/apify.md`. `apify_residencial` continua não implementado. |
| `_reversa_sdd/sdd/coletor-lotes.md` | §6 RF-12 | delta-de-contrato-externo | Adaptador `milan-leiloes`: agenda `/agenda/veiculos` → catálogo `/leilao/<id>/catalogo` dos leilões cujo card traz o filtro `descricao_contem`, lido em toda varredura; detalhe pela página do lote. Contrato em `_reversa_forward/005-leiloeiro-milan/interfaces/milan.md`. |
| `_reversa_sdd/sdd/coletor-lotes.md` | §4 NG-03; §15 decisão "escalada para Apify… termos de uso"; §14 OQ-03 | regra-alterada | **NG-03 ("Resolver CAPTCHA" fora de escopo) está superada** pela regra anti-bot do Rafael (RN-07 da 005): não se contorna proteção no código, mas resolver o desafio (inclusive CAPTCHA/Turnstile) por ferramenta robusta, mesmo paga, é permitido. **OQ-03 respondida:** alerta quando o gasto do ciclo passa de 80% do limite da conta (RN-13). §11 EC-08 (cota com mensagem explícita) atendido. |
| `_reversa_sdd/sdd/onboarding-leiloeiro-assistido.md` | §4 NG-02; §11 EC-02 | regra-alterada | Diante de CAPTCHA ou desafio anti-bot, o fluxo não deve só encerrar: recomenda subir para a ferramenta robusta (Apify, ator da loja ou serviço de desbloqueio), como na RN-07 da 005. Armadilha nova: páginas liberadas pelo Cloudflare também trazem o script `challenge-platform` (não serve como marca de bloqueio). |
| `_reversa_sdd/sdd/parser-lotes.md` | §6, §9 | regra-nova, delta-de-dados | Parser `milan-leiloes` (catálogo e página do lote; datas sem ano; marca de duas palavras; sinônimos `m-benz`, `cintroen`; `jaguar` conhecida). Campo novo `Lote.cambio` ("automático", "manual", "CVT"), que não filtra. |
| `_reversa_sdd/sdd/cadastro-leiloeiros.md` | §6, §9 | regra-alterada | `nivel_coleta: apify` implementado. Campos novos opcionais: `intervalo_horas` (1 a 720; o leiloeiro só é lido se a última coleta normal ok foi há pelo menos esse tempo) e `apify_ator` (só com `apify`, só ator com perfil no código). `frequencia` segue sem uso. |
| `_reversa_sdd/sdd/notificador-telegram.md` | §10 (`.env`), formato do resumo | regra-alterada | `APIFY_TOKEN` no `.env`, exigido só quando a varredura inclui leiloeiro pago, mascarado como segredo. O resumo traz o câmbio depois do km quando o leiloeiro informa. |
| `_reversa_sdd/sdd/agendador-observabilidade.md` | §6 (alertas, relatório), modelo de dados | regra-alterada, delta-de-dados | Varredura com `--sem-pagos` e intervalo: pulados aparecem só na seção "Leiloeiros" do relatório. A mesma seção ganha o consumo do Apify e os leilões novos com a antecedência. Alertas novos: falhas do Apify com a causa, gasto acima de 80% (1 por dia) e antecedência menor que o intervalo. Banco no esquema 2 (tabela `evento_visto`). |
| `_reversa_sdd/sdd/motor-filtros.md` | §6 (aplicação dos critérios) | regra-alterada | O alvo é conferido de novo depois do detalhe do lote: lance que passou do teto tira o lote do aviso, em qualquer leiloeiro. |

## Regras sob vigilância

W030, W031, W032, W033, W034, W035, W036, W037, todos na seção "Observações" (sem peso de regressão, por ser greenfield) de `_reversa_forward/005-leiloeiro-milan/regression-watch.md`. W031 depende do próximo leilão de financiamento do Milan (catálogo, pátio, câmbio e lance ao vivo); W035 pede uma consulta à tabela `evento_visto` depois de cerca de um mês.

## Fontes

- `_reversa_forward/005-leiloeiro-milan/legacy-impact.md`
- `_reversa_forward/005-leiloeiro-milan/regression-watch.md`
- `_reversa_forward/005-leiloeiro-milan/requirements.md`
- `_reversa_forward/005-leiloeiro-milan/progress.jsonl`
- `_reversa_forward/005-leiloeiro-milan/roadmap.md` (D-86 a D-103)
- `_reversa_forward/005-leiloeiro-milan/data-delta.md`
- `_reversa_forward/005-leiloeiro-milan/investigation.md`
- `_reversa_forward/005-leiloeiro-milan/interfaces/apify.md`
- `_reversa_forward/005-leiloeiro-milan/interfaces/milan.md`
- `_reversa_forward/005-leiloeiro-milan/audit/cross-check.md`
- `_reversa_forward/005-leiloeiro-milan/actions.md` (notas de execução)
