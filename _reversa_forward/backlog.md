# Backlog de features — Bot Leilão Carros

> Ideias e pedidos do Rafael ainda não iniciados. Cada item vira uma feature do ciclo forward
> (`/reversa-forward` → requirements → plan → to-do → audit → coding → sync) quando for a vez dele.
> Ao iniciar um item, mova-o para "Em andamento" com o identificador da feature (`002-...`).

## Próximas

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

- Lance + comissão do leiloeiro (~5%, confirmar no Termo de Adesão do Vip) + taxas administrativas e de pátio + transferência, e o % da FIPE. Combina com o item 2.

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

## Em andamento

_(nenhuma)_

## Feitas

- **001 — MVP de varredura ponta a ponta** (2026-10-04), com as emendas E001 (relatório por varredura em `1OUTPUT/`) e E002 (lista de lotes a monitorar).
- **Agendamento automático:** resolvido sem código com o Agendador de Tarefas do Windows (`scripts/agendar_windows.ps1`), em 2026-10-08.
- **Atalho de duplo clique:** `scripts/varrer.bat`, em 2026-10-08.
