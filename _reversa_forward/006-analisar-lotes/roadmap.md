# Roadmap: Skill `analisar-lotes` (triagem e custo na garagem)

> Identificador: `006-analisar-lotes`
> Data: `2026-10-15`
> Requirements: `_reversa_forward/006-analisar-lotes/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA
> Numeração das decisões: continua a das features anteriores (D-01 a D-103).

## 1. Resumo da abordagem

A skill tem duas metades. O **roteiro** (`SKILL.md`, redigido e avaliado com o `skill-creator`) diz ao agente como julgar cada lote. Uma **linha de comando determinística** do próprio bot (`python -m bot_leilao analise …`) faz tudo o que não pode errar: ler a lista e os critérios, abrir a página do lote pelo acesso do bot, consultar a FIPE, calcular o custo e escrever na lista e no arquivo de descartados. O agente decide; o código escreve. Toda escrita pega a trava da varredura. O roteiro lista todos os critérios da RN-03 e diz de onde vem cada um: dos campos que o alvo já tem (`tipos_leilao`, `ano_min`/`ano_max`, `preco_maximo`, `quilometragem_maxima`), dos campos novos (`cambio`, `aceitar_*`), do texto `triagem` (versão preferida) e do estado do lote (encerrado, retirado, documento).

Os critérios entram no `veiculos-alvo.yaml`: bloco `padrao` com campos fixos validados, sobrescrevíveis por alvo, e texto livre `triagem` para o agente. O bot passa a usar o câmbio quando o lote já o traz (Milan), descartando só quando há certeza.

Verificações deste plano (2026-10-15): página de anúncio do Vip abre e traz "Câmbio Automático"; detalhe do Kuss traz as observações; busca JSON da Copart aceita o número do lote (o detalhe HTML segue barrado pelo Imperva); FIPE pela parallelum (500 consultas/dia) igual ao site oficial (R$ 62.464 no Versa SL 2019, out/2026); rota Londrina → Curitiba de 386 km pelo OSRM; exceção no `.gitignore` para versionar só esta skill funciona.

## 2. Princípios aplicados

Não há `.reversa/principles.md`; valem os princípios de fato das features anteriores e das decisões do Rafael.

| Princípio (de fato) | Como a feature se relaciona | Status |
|---------------------|-----------------------------|--------|
| Menor custo | Página paga (Milan) só quando o bloco não basta, com o total informado; cache de FIPE e de distâncias | respeita |
| Não falhar em silêncio | Na dúvida, "a confirmar" com o que falta; FIPE ou distância indisponíveis aparecem como tal, nunca como número inventado | respeita |
| Segurança | Nenhum segredo no `SKILL.md`; token só do `.env`, pela linha de comando; nada de login | respeita |
| Sistema não dá lances | Só leitura e anotação | respeita |
| Regra anti-bot (RN-07 da 005) | Páginas protegidas só pelo acesso do bot (Apify no Milan); o agente não abre o site direto | respeita |
| Automação máxima | Distância calculada e guardada sozinha; o Rafael só corrige se quiser | respeita |
| Lista só por acréscimo do bot | A skill escreve só no bloco do lote, pela linha de comando; comentário `<!-- lote -->` e numeração intactos | respeita |

## 3. Decisões técnicas

### 3.1 Forma da skill

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-104 | (RF-01, RF-02, RN-03, RN-06) Skill = roteiro (`SKILL.md`) + subcomandos `python -m bot_leilao analise …` com saída JSON (contrato em `interfaces/cli-analise.md`). **O agente nunca edita a lista à mão:** triagem, descarte e anotação de custo são subcomandos que pegam a trava da varredura (`dados/varredura.lock`) e gravam de forma atômica | Escrita em markdown por agente erra numeração e comentário; o código é testável e repete o mesmo resultado. A trava resolve o RF-11 e o conflito com a varredura que acrescenta blocos | Agente editando o arquivo (frágil); script solto em `scripts/` (sem os clientes, a config e os testes do pacote) | 🟢 |
| D-105 | (RF-01, RNF Qualidade) O `SKILL.md` é redigido com o `skill-creator`: rascunho → avaliações com uma cópia da lista de 2026-10-15 e o resultado esperado de cada lote → ajuste até acertar. Gatilhos: `/analisar-lotes`, "analisa os lotes", "triagem da lista" | Decisão de 2026-10-15: Reversa registra e testa o código; o `skill-creator` cuida da qualidade da instrução | Escrever o roteiro sem avaliação | 🟢 |
| D-106 | (RF-01) A skill fica em `.claude/skills/analisar-lotes/` e uma cópia idêntica em `.agents/skills/analisar-lotes/` (um teste falha se divergirem). `.gitignore`: `.claude/skills/` e `.agents/skills/` viram `…/skills/*` com a exceção `!…/skills/analisar-lotes/` | Verificado em 2026-10-15: com `skills/` inteiro ignorado a exceção não funciona; com `skills/*` funciona e o Reversa continua fora do git | Link simbólico (Windows sem privilégio não cria); versionar todas as skills do Reversa | 🟢 |

### 3.2 Critérios

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-107 | (RN-04, RF-05) `veiculos-alvo.yaml` aceita, na raiz, um bloco `padrao` e, em cada alvo, os campos `cambio` (lista entre `automatico`, `cvt`, `manual`), `aceitar_sinistro`, `aceitar_sucata`, `aceitar_mecanica_com_problema`, `aceitar_pequenas_avarias` (verdadeiro ou falso) e `triagem` (texto). O alvo sobrescreve o padrão campo a campo. Valor inválido aborta antes da rede, citando o alvo e o campo. Sem `padrao` e sem os campos, nada muda (compatível com o arquivo atual) | Uma fonte só, que o bot e a skill leem (clarify de 2026-10-15) | Arquivo de critérios separado (duas fontes) | 🟢 |
| D-108 | (RF-06) O motor usa o câmbio quando o lote o traz, descartando **só com certeza**: lote "manual" e alvo sem `manual`; lote "automático" ou "CVT" e alvo só `[manual]`. Lote "automático" com alvo só `[cvt]` **não** é descartado (o Milan escreve AUTOMATICO também para CVT, ex.: HR-V EXL CVT). Lote sem câmbio passa como hoje. Os descartados por câmbio somam em `descartados_sem_casar` e aparecem no log | Evita perder carro bom por texto ambíguo; RN-02 (na dúvida, não reprova) | Descartar "automático" contra `[cvt]` | 🟢 |
| D-109 | O `veiculos-alvo.yaml` do Rafael ganha o `padrao` (`cambio: [automatico, cvt]`, sem sinistro, sem sucata, sem mecânica com problema, pequenas avarias aceitas) e o texto `triagem` em cada alvo, a partir dos comentários de hoje (Fluence: só 2.0 Dynamique Plus ou Privilège; Kicks: só 1.6 CVT, preferir S; Creta: preferir Attitude ou Pulse 1.6; Duster: 1.6 CVT de 2018 em diante, fora 1.3 turbo e manual). As notas de conforto continuam em `veiculos-alvo-notas.md` | O que hoje é comentário não é lido por ninguém | Deixar os comentários e repetir tudo no `SKILL.md` | 🟡 |

### 3.3 Leitura do lote

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-110 | (RF-07, RN-01, RN-07) `analise pagina <número ou link>` (o link é convertido no número do bloco) lê o lote pelo acesso do bot, com o cliente e o nível do leiloeiro (5 s por host; token do `.env`). Por leiloeiro: **Vip** GET da página do anúncio (link do bloco); **Kuss** o detalhe JSON do bot (evento e sequência tirados do link `/lance/<evento>/0/<seq>`); **Copart** a busca JSON com `query=<número do lote>` (a página de detalhe é barrada pelo Imperva); **Freitas** GET do detalhe; **Milan** GET da página do lote pelo Apify. Saída: campos que o parser do leiloeiro já extrai, o texto limpo da página (até 8.000 caracteres) e `pago` (verdadeiro no Milan, com o custo estimado) | Mesmo caminho e mesma conduta do bot; o agente lê o texto e julga | Agente abrir o link no navegador (Milan e Copart barram; contornaria a regra anti-bot) | 🟢 (Vip, Kuss, Copart, Freitas verificados em 2026-10-15; Milan pelas amostras da 005) |
| D-111 | (RN-07) Ordem da evidência no roteiro: primeiro o bloco (título, observações, câmbio, km); a página só se faltar algo que decida o veredito. Na Copart, sem câmbio no título nem na busca, o lote fica "a confirmar: câmbio" (fotos não entram nesta versão) | Custo e tempo; a Copart não informa câmbio em dado nenhum | Ler fotos com visão (fica para depois, se o Rafael pedir) | 🟢 |

### 3.4 Escrita na lista

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-112 | (RF-03, RF-04, RN-05, RN-06) Triagem: uma linha por bloco, `- **Triagem (DD/MM/AAAA):** aprovado`, `… reprovado — <motivo> (<evidência>)` ou `… a confirmar — <o que falta>`, inserida antes da linha `- **Link:**`; uma nova triagem substitui a anterior. Reprovado: o bloco sai da lista (do `---` até antes do próximo) e vai para o fim de `1OUTPUT/lotes-descartados.md` com a linha `- **Descartado em DD/MM/AAAA:** <motivo> — <evidência>`; número e comentário do lote não mudam. `analise devolver <número>` traz o bloco de volta para o fim da lista | Reversível (clarify) e sem tocar nos outros blocos | Apagar o bloco; marcar sem mover | 🟢 |
| D-113 | As regras do arquivo `comentarios-lotes-a-monitorar.md` ganham a linha de triagem e o arquivo de descartados: o texto padrão do bot (`notificacao/relatorio.py`) e o arquivo que já existe em `1OUTPUT/` (atualizado uma vez; a pasta fica fora do git) | O bot só cria o arquivo de comentários quando ele não existe | Deixar a regra só no `SKILL.md` | 🟢 |

### 3.5 FIPE, distância e custo

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-114 | (RF-09, RN-09) FIPE pela API parallelum v2 (gratuita, 500 consultas por dia, verificado) com reserva no endpoint do site oficial (`veiculos.fipe.org.br/api/veiculos/…`, mesmo valor verificado). Cache por mês de referência em `dados/fipe-cache.json`. `analise fipe-candidatos --marca --modelo --ano` devolve as versões daquele ano cujo nome contém os termos, com valor, código, mês e fonte; `analise fipe-valor --codigo --ano` devolve uma. A escolha entre candidatas é do agente; se houver mais de uma plausível, ele lista em vez de escolher | Valores idênticos às duas fontes; a reserva e o cache protegem do limite e de queda | Só a parallelum (ponto único de falha); só o site oficial (endpoint não documentado, sem garantia) | 🟢 (fontes e limite) 🟡 (estabilidade das duas) |
| D-115 | (RN-08, RF-08) Distância do pátio até Londrina: a tabela `distancias` do `custos.yaml` vence; senão o cache `dados/distancias.json`; senão geocodificação da cidade pelo Nominatim (OpenStreetMap) e rota pelo OSRM, com identificação do bot e no máximo 1 consulta por segundo, gravada no cache. Falha ou pátio só com UF: frete "a confirmar". Londrina → Curitiba deu 386 km | Os pátios se repetem: cada cidade é consultada uma vez só, sem trabalho manual | Tabela feita à mão (passo manual recorrente); distância em linha reta (subestima) | 🟢 |
| D-116 | (RN-08, RF-08, RF-10) `config/custos.yaml` (versionado; criado com os valores do clarify se não existir; validado). `analise custo --lance --despesa --patio "Cidade - UF" --documento-uf --fipe` devolve as parcelas, o total na garagem, o % da FIPE e o lance máximo. Lance máximo = (revenda ÷ (1 + margem) − despesa − frete − transferência − reparos) ÷ (1 + comissão), com revenda = 85% da FIPE e margem = 10% sobre o custo na garagem. Despesa ausente usa o padrão e é marcada "(padrão)"; frete marcado "(estimativa)". Reparos além da reserva (RN-08), quando as observações citam avaria: `--reparos-extra <valor> --motivo-reparos "<texto>"`, somados e mostrados com o motivo | Contas determinísticas, testadas com o exemplo do requirements (R$ 71.060 com 380 km) | Calcular no roteiro do agente | 🟢 |
| D-117 | (RF-08) `analise anotar-custo <número>` preenche os campos que o bloco já tem: FIPE (valor, código, mês e versão, ou "_a escolher_" com as candidatas), o "% da FIPE" do lance ao entrar, Despesas admin. (se vazia), Frete, Valor estimado na garagem; e acrescenta "Lance máximo (margem 10%)". Só para lotes aprovados | Formato definido pelo Rafael na emenda E002 da 003 | Seção nova "Análise FIPE" no bloco | 🟢 |

### 3.6 Ajustes depois da primeira rodada de avaliações (2026-10-15)

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-118 | (RN-11, RN-12, RF-12) Subcomando `analise anotar <lote> --campo {Câmbio, Resultado do pregão} --valor …`, com a trava da varredura: substitui a linha se existe, senão insere antes do Link. A skill grava o câmbio deduzido e o resultado do pregão por ele | Mesma proteção das outras escritas; só campos conhecidos | Agente editando o bloco à mão (o baseline fez isso) | 🟢 |
| D-119 | (RF-13) `analise pagina` do Kuss consulta `json_edital.php op=T` do evento e devolve `resultado`: "último lance presencial/online; valor não divulgado pelo site" ou "sem lance". O apelido nunca sai | Verificado no evento 897 (13/10): 179 presenciais, 163 online, 4 sem lance, nenhum valor | Ler o histórico `json_lance_historico.php` (devolve "Não loteado") | 🟢 |

## 4. Premissas

| Premissa | Origem | Risco se errada |
|----------|--------|-----------------|
| A busca JSON da Copart continua aceitando o número do lote | Teste de 2026-10-15 | Copart sem leitura de página: fica com o que está no bloco |
| A página de anúncio do Vip continua aberta | Teste de 2026-10-15 | Vip "a confirmar" quando o título não basta |
| Os endpoints da FIPE (parallelum e site oficial) seguem no ar e com o mesmo formato | Teste de 2026-10-15 | FIPE "indisponível"; triagem não depende dela |
| OSRM e Nominatim públicos aceitam uso esporádico | Teste de 2026-10-15 | Frete "a confirmar" até o Rafael pôr a distância na tabela |

## 5. Delta arquitetural

| Componente | Arquivo de origem | Tipo de mudança | Resumo |
|------------|-------------------|-----------------|--------|
| Análise de lotes | — | componente-novo | `src/bot_leilao/analise/` (`lista.py`, `pagina.py`, `fipe.py`, `custos.py`, `distancias.py`) (D-104, D-110, D-112, D-114 a D-117) |
| Linha de comando | `interfaces/cli.md` da 001 | contrato-alterado | Subcomandos `analise lotes`, `pagina`, `triar`, `devolver`, `fipe-candidatos`, `fipe-valor`, `custo`, `anotar-custo` (D-104) |
| Configuração de alvos | `configuracao-veiculos-alvo.md` | regra-alterada | Bloco `padrao`, campos de critério e `triagem` (D-107) |
| Motor de filtros | `motor-filtros.md` | regra-alterada | Câmbio quando conhecido, só com certeza (D-108) |
| Relatório e lista | emendas E002 da 003 | regra-alterada | Texto do arquivo de comentários (D-113) |
| Skill | — | componente-novo | `.claude/skills/analisar-lotes/` e `.agents/skills/analisar-lotes/` (D-105, D-106) |
| Configuração | `config/` | componente-novo (dados) | `config/custos.yaml`; `config/veiculos-alvo.yaml` migrado (D-109, D-116) |
| `.gitignore` | — | regra-alterada | Exceção para versionar só esta skill (D-106) |

Fora do delta: coleta, parsers (reaproveitados pela leitura do lote), semeadura, digest do Telegram, banco (sem tabela nova).

## 6. Delta no modelo de dados

- Campos novos no alvo (`padrao` e por alvo), `config/custos.yaml`, caches `dados/fipe-cache.json` e `dados/distancias.json`, linha de triagem nos blocos e arquivo `1OUTPUT/lotes-descartados.md`. Banco inalterado.
- Detalhe completo em: `_reversa_forward/006-analisar-lotes/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| FIPE: parallelum v2 e site oficial | HTTP (API) | `_reversa_forward/006-analisar-lotes/interfaces/fipe.md` |
| Distâncias: Nominatim e OSRM | HTTP (API) | `_reversa_forward/006-analisar-lotes/interfaces/distancias.md` |
| Linha de comando `analise` (contrato com o roteiro da skill) | CLI (JSON) | `_reversa_forward/006-analisar-lotes/interfaces/cli-analise.md` |

## 8. Plano de migração

1. `veiculos-alvo.yaml` atual continua válido (campos novos opcionais); a migração do arquivo do Rafael (D-109) é uma ação própria, com o diff mostrado a ele.
2. `config/custos.yaml` é criado com os valores do clarify na primeira execução da análise, se não existir.
3. `.gitignore` muda para versionar só esta skill; as skills do Reversa continuam fora.
4. Ordem: critérios no YAML e câmbio no motor → leitura e escrita da lista → leitura do lote → FIPE, distância e custo → linha de comando → `SKILL.md` com o `skill-creator` → arquivo de comentários, YAML do Rafael, README.
5. Reversão: apagar a pasta da skill; os campos novos do YAML podem ficar (ou sair) sem efeito no bot além do câmbio.

## 9. Riscos e mitigações

| ID | Risco | Impacto | Probabilidade | Mitigação |
|----|-------|---------|---------------|-----------|
| R-01 | O agente julga errado (reprova o que servia) | alto | média | "Na dúvida, a confirmar" (RN-02); evidência obrigatória; avaliações do `skill-creator` com a lista real; descarte reversível (`devolver`) |
| R-02 | Limite de 500 consultas/dia ou queda da parallelum | baixo | média | Cache por mês; reserva no site oficial |
| R-03 | Endpoint do site oficial da FIPE muda | baixo | baixa | Só é usado na falha da parallelum; FIPE "indisponível" sem bloquear a triagem |
| R-04 | O Rafael edita a lista ao mesmo tempo que a skill | médio | baixa | Escrita atômica, janela curta; a skill relê o arquivo antes de cada escrita |
| R-05 | Página do Milan custa a cada leitura | baixo | média | Leitura só quando necessária; total informado no resumo |
| R-06 | Cópias da skill em `.claude` e `.agents` divergem | baixo | média | Teste de igualdade |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Os 5 cenários do requirements passam: os 4 de triagem e FIPE nas avaliações do `skill-creator` com a cópia da lista de 2026-10-15; o da varredura em andamento em teste automatizado
- [ ] Linha de comando `analise` com testes sem rede (FIPE, distâncias e sites simulados); suíte anterior (727) verde
- [ ] Exemplo do requirements reproduzido pelo `analise custo` (R$ 71.060)
- [ ] Execução real da skill sobre a lista atual, com o resumo mostrado ao Rafael antes de mover qualquer lote
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-15 | Ajustes do `/reversa-audit` (A001 a A005): RF-02 e RN-03 no D-104 com a origem de cada critério; link aceito (D-110); reparos extras no custo (D-116) | Claude |
| 2026-10-15 | Versão inicial gerada por `/reversa-plan`, com verificações de acesso por leiloeiro, FIPE, distâncias e `.gitignore` | reversa |
