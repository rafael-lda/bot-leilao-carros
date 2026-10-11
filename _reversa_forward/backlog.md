# Backlog de features — Bot Leilão Carros

> Ideias e pedidos do Rafael ainda não iniciados. Cada item vira uma feature do ciclo forward
> (`/reversa-forward` → requirements → plan → to-do → audit → coding → sync) quando for a vez dele.
> Ao iniciar um item, mova-o para "Em andamento" com o identificador da feature (`002-...`).

## Próximas

> **Ordem combinada em 2026-10-10:** 002 = Claudio Kuss (mais volume, em andamento); depois, a skill `analisar-lotes` ("Custo na garagem", itens 2, 3 e 8 unificados).

### ★ Custo na garagem em Londrina — skill `analisar-lotes` (une os itens 2, 3 e 8)

- **Pedido do Rafael (2026-10-10):** para cada lote, estimar o valor final com o carro na garagem em Londrina, e o % da FIPE desse valor.
- **Fórmula:** lance + 5% de comissão + despesa fixa do lote + frete (pátio → Londrina) + transferência; ao lado, % da FIPE (item 2).
- **Dados:** despesa fixa no JSON do lote no Kuss (`tblDespAdm`) e no PDF do edital do evento no Vip; local do pátio no card do Vip ("Local: UF") e no endereço da página do lote; o Kuss fica em Curitiba.
- **Configuração do Rafael** (ex.: `config/custos.yaml`): cidade base, R$/km de frete, custo de transferência, reserva para reparos. Valores de referência na memória do projeto (`rafael-local-e-custos`); frete ainda sem orçamento real.
- **Aviso no Telegram, exemplo:** `Na garagem: ~R$ 70.700 (71% da FIPE) — frete ~R$ 2.100`.
- Até lá: o Rafael pede e o Claude faz a conta à mão, lote a lote.
- **Abordagem escolhida (2026-10-10): skill de agente + script de apoio, e não código no bot.** O ponto difícil (casar "VERSA EXCL CVT" / "ONIX 10MT LT2" com a versão exata da FIPE) é o que um agente faz melhor que regras de código.

#### Como implementar a skill `analisar-lotes`

1. **Gatilho:** `/analisar-lotes` (ou "analisa os lotes da lista"). Escopo opcional: um lote (link) ou a lista inteira.
2. **Roteiro do agente (SKILL.md),** para cada bloco de `1OUTPUT/lotes-a-monitorar.md` com "Análise FIPE: _pendente_" (ou desatualizada):
   1. Abrir a página do lote e conferir: lance atual, situação (martelo batido, retirado), câmbio, km, local do pátio, final de placa.
   2. Aplicar as regras do topo da lista: tirar encerrados e retirados; marcar reaparições; sinalizar lance acima do teto (tirar só se o Rafael pediu).
   3. Identificar a versão na FIPE pelo título e ano; se houver mais de uma candidata plausível, listar as opções com valor em vez de escolher.
   4. Chamar o script de cálculo e escrever a análise no bloco, sem tocar nos outros blocos nem no comentário `<!-- lote: ... -->`.
3. **Script de apoio (`scripts/custo_garagem.py`),** determinístico, para o agente não errar conta:
   - `fipe <marca> <modelo/versão> <ano>`: consulta a FIPE (hoje parallelum; registrar código FIPE e mês de referência) e devolve as versões candidatas com valor.
   - `custo --lance X --despesa Y --uf-patio UF [--cidade-patio C]`: aplica `config/custos.yaml` e devolve o custo na garagem e o % da FIPE.
4. **`config/custos.yaml`** (versionado, editado pelo Rafael): cidade base (Londrina-PR), comissão (5%), frete em R$/km ou tabela por UF/cidade, transferência, reserva de reparos, margem desejada. Valores iniciais a partir da memória `rafael-local-e-custos`; frete sem orçamento real ainda.
5. **Formato da análise no bloco (exemplo):**
   ```
   - **Análise FIPE (10/10/2026):** VERSA Exclusive 1.6 Aut. 2024 — FIPE R$ 99.011 (023174-6, out/2026)
     - Lance atual R$ 61.000 = 62% da FIPE
     - Na garagem: ~R$ 70.700 = 71% da FIPE (comissão 3.050 + despesa 2.650 + frete ~2.100 + transferência ~450)
     - Lance máximo para margem de X%: R$ ...
   ```
6. **Onde guardar:** `.claude/skills/analisar-lotes/` (Claude Code) e cópia em `.agents/skills/analisar-lotes/` (Antigravity, Codex). Como `.claude/skills/` e `.agents/skills/` estão no `.gitignore` (pastas do Reversa), acrescentar exceções `!.claude/skills/analisar-lotes/` e `!.agents/skills/analisar-lotes/` para versionar só essa skill.
7. **Testes:** o script com casos fixos (FIPE simulada, custos conhecidos); a skill validada com o Versa 2023/2024 (lote 315452) como primeiro caso real.
8. **Evolução:** se o Rafael quiser o custo automático no Telegram, a skill vira o protótipo das regras e o cálculo migra para o bot (feature própria).


### 1. Filtro de câmbio por veículo-alvo — prioridade do Rafael

- **Pedido (2026-10-09):** cada veículo-alvo escolhe o câmbio aceito: `automatico`, `manual` ou `ambos`. Hoje o Rafael só quer automático.
- **Por que não é ajuste:** a listagem do Vip não informa câmbio, e o filtro de câmbio do formulário é ignorado pelo servidor (testado em 2026-10-06, `interfaces/vip-pesquisa.md`). A informação confiável está na **página do lote** (campo "Câmbio: Automático", visto no Versa 315452).
- **Desenho sugerido:**
  1. Campo novo no alvo, por exemplo `cambio: automatico | manual | ambos`, com padrão `ambos` (não muda o comportamento de quem não declarar).
  2. Depois do casamento atual, **só para os candidatos**, o bot abre a página do lote e lê o câmbio, respeitando os 5 s entre requisições.
  3. Câmbio não informado na página: o lote passa, marcado "câmbio a confirmar" (mesma regra da km, D-19/D-32).
- **Evidência (2026-10-09, lote 319723, conferido pelo Rafael no celular):** a seção "Detalhes do Lote" da página traz, em pares rótulo/valor, "Câmbio: Automático", "Procedência: Recuperado Financiamento (Conservado)", "Final da placa: 1 - SC", "Funcionando na Entrada: Sim", "Comitente", "Código". Os mesmos campos servem à detecção de reaparições (item 7).
- **A investigar no plano:** estrutura da página do lote no Vip; se o título já basta em parte dos casos (CVT, AT, MT, AUT) para poupar requisições; efeito no limite de requisições do Vip (429 por volta da 13ª requisição por minuto).

### 2. Teto por ano via FIPE

- O teto hoje é "nivelado por cima": 70% da FIPE da melhor versão do ano **mais novo** da faixa, então um Sentra 2014 é julgado pela régua do 2017.
- **Caminho do meio sugerido:** teto do lote = 70% da FIPE da versão automática mais cara **do ano do lote**. Resolve o ano sem precisar casar a versão do título do Vip com a FIPE (só modelo + ano).
- Risco: depende de uma fonte da FIPE. A API não oficial parallelum funciona; o site oficial respondeu, mas a consulta por código precisa de investigação.

### 3. Custo total estimado

- Lance + comissão do leiloeiro + despesa fixa por lote + transferência, e o % da FIPE. Combina com o item 2.
- **Apurado em 2026-10-10 nos editais:**
  - **Vip:** 5% de comissão + "Reemb./Desp. Aut." por lote, listado no **PDF do edital** de cada evento (seção após o item 19, coluna `Reemb./Desp.Aut.`). No evento 091026BSSC, carros conservados: R$ 850 a R$ 2.910, mediana R$ 2.650 (inclui ATPV-e de R$ 86,20). Exemplo do edital: 20.000 + 1.000 + 1.900 = 22.900. Estadia após o prazo de retirada: R$ 100 por veículo leve + R$ 20/dia.
  - **Claudio Kuss:** 5% de comissão + "ICMS, despesas administrativas e de logística"; a despesa vem pronta no JSON do lote (`tblDespAdm`, ex.: R$ 2.750). Confirmar com o leiloeiro quando o ICMS se aplica.
  - **Regra prática:** custo ≈ lance × 1,05 + despesa fixa (≈ +12% num lance de R$ 40 mil), antes de transferência e débitos.

### 4. Palavras a excluir no veículo-alvo

- Ex.: `excluir: [Oroch]`, para que o alvo "Duster" não case com a picape "DUSTER OROCH". Pequeno; pode virar emenda (`/reversa-add`) se a Oroch começar a aparecer.

### 5. Silenciar o aviso de "marca fora da tabela"

- O log repete o aviso para marcas de implementos e caminhões (`librelato`, `massey`, `new holland`, `noma`, `facchini`, `guerra`) e para `--`, `automovel` e `outros`. Pequeno; emenda.

### 6. Lotes de pequena monta — baixa prioridade, decisão adiada pelo Rafael

- **Decisão (2026-10-09):** por enquanto só "Conservado". Pequena monta tende a somar desvalorização à passagem por leilão (que já custa 10 a 20% na revenda), o custo de funilaria ainda é desconhecido e carro batido e parado tem mais risco de problemas mecânicos.
- **Custo de incluir depois (baixo):** (1) uma busca a mais no `leiloeiros.yaml` com `monta: 2`, sem código, que semeia sozinha; (2) emenda pequena para mostrar no Telegram e nos relatórios de qual busca o lote veio; (3) a pensar: teto por busca ou "desconto por monta", porque hoje o teto é por alvo.

### 7. Reaparições detectadas pelo bot — futuro

- Um lote que não vende volta com outro número de anúncio (visto em 2026-10-09: Sentra 2.0S 2012/2013, 228.227 km, 310800 → 319723), e o bot o avisa de novo. Hoje a identificação é manual na revisão da lista (emenda E003). Futuro: o bot marcar no aviso "possível reaparição de ..." comparando modelo, ano, km e final de placa.

### 7. Registro do martelo final — base para calibrar o teto com dado próprio

- **Pedido (2026-10-09):** anotar por quanto cada lote acompanhado foi efetivamente arrematado, para montar a distribuição real de % da FIPE. Vale para **todos os leiloeiros ativos**, não só o Vip: a lista-alvo do brainstorm é Freitas, Vip Leilões, Claudio Kuss, Copart e Milan (`_reversa_sdd/prd.md#47`).
- **Por que importa:** hoje o teto de 70% é uma estimativa. Com dois ou três meses de martelo registrado, o Rafael responde com dado se 60% da FIPE existe ou é fantasia, e calibra o teto por leiloeiro — cada um tem público, avaria e disputa diferentes.
- **Desenho sugerido:**
  1. Campos novos por lote acompanhado: `martelo_final`, `data_do_martelo`, `fipe_do_lote` (ano e versão) e `pct_fipe` calculado. O `1OUTPUT/lotes-a-monitorar.md` já acumula os lotes avisados e é o lugar natural.
  2. Preenchimento é manual, como já é a retirada de lotes desse arquivo. O bot não sabe o resultado do pregão.
  3. Quando houver série, um resumo por leiloeiro e por modelo: mediana, p25 e p75 do % da FIPE.
- **Depende de / combina com:** item 2 (teto por ano via FIPE) para ter a FIPE do lote sem preencher à mão, e item 3 (custo total) para a distribuição sair em custo final, não só em martelo.
- **A investigar no plano:** comissão e taxas variam por leiloeiro (no Vip são 5% confirmados na cláusula 13 do Termo de Adesão, mais taxa administrativa a confirmar na página do lote), então o % final precisa ser calculado com a tabela do leiloeiro de origem, não com um número único.

### 8. Distância do pátio — ideia

- O Rafael mora em Londrina-PR; frete de carro de outro estado pode inviabilizar a margem. O Vip tem filtro de estado (`estado` → `Filtro.LocalEstadoId`). Opções: busca só com pátios do PR e vizinhos, ou mostrar o estado/cidade do pátio no aviso (o card do Vip traz "Local: SC"; o lote do Kuss, cidade de transferência).

### 9. Acesso a sites protegidos e com login — decisões de 2026-10-11 (para futura implementação)

- **Leitura correta da D-30 (esclarecida pelo Rafael):** a regra existe para **não gastar esforço fabricando disfarces no código**. Quando o acesso simples (`script`) não bastar, a saída é subir para uma ferramenta robusta (Apify), e não remendar o código com truques.
- **Escada do Apify, usada estritamente no necessário:** (1) `script` atual; (2) navegador do Apify com IP de datacenter; (3) navegador com IP residencial; (4) IP residencial com sessão fixa ("sticky") ou estático ("ISP"), restrito ao Brasil. Subir um degrau só quando o anterior falhar, e registrar por leiloeiro qual degrau foi preciso.
- **Economia de Apify:** usar o navegador só para passar o desafio (Cloudflare/Imperva) e reaproveitar o cookie de liberação nas páginas seguintes.
- **Sites que exigem login:** o risco principal é a **conta de arrematar** do Rafael (ligada ao CPF), não o IP. Com login, IP que muda (Apify residencial rotativo) parece conta invadida. Caminhos, em ordem de preferência:
  1. **Importar a exportação oficial** do site (ex.: CSV da Copart), feita pelo Rafael: risco zero, custo zero, ~2 min por exportação.
  2. **Robô logado rodando no notebook do Rafael** (IP e navegador dele, sem Apify), em ritmo baixo, de preferência com **conta secundária** só de consulta.
  3. Robô logado no Apify com IP fixo: só se 1 e 2 não servirem.
- **Comportamento humano simulado** (variar horários e intervalos) é possível, mas o Imperva também examina a impressão digital do navegador; tratar como reforço, não como garantia.
- **Triagem de 2026-10-11:** Milan (Cloudflare "managed" no site inteiro, inclusive `robots.txt` e catálogo; leilão de 14/10 com 247 lotes, ~125 carros, km, câmbio e comitente no catálogo) e Copart (exportação CSV com 692 carros de financiamento, FIPE, monta, documento e pátio; 80% dos pátios no NE/CO). Freitas fora (bloqueio deliberado).

## Em andamento

- **002 — Leiloeiro Claudio Kuss** (aberta em 2026-10-10). Base: `_reversa_forward/triagem-leiloeiros-2026-10-10.md`.

## Feitas

- **001 — MVP de varredura ponta a ponta** (2026-10-04), com as emendas E001 (relatório por varredura em `1OUTPUT/`) e E002 (lista de lotes a monitorar).
- **Agendamento automático:** resolvido sem código com o Agendador de Tarefas do Windows (`scripts/agendar_windows.ps1`), em 2026-10-08.
- **Atalho de duplo clique:** `scripts/varrer.bat`, em 2026-10-08.
