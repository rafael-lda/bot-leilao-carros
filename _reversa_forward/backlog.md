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

## Em andamento

_(nenhuma)_

## Feitas

- **001 — MVP de varredura ponta a ponta** (2026-10-04), com as emendas E001 (relatório por varredura em `1OUTPUT/`) e E002 (lista de lotes a monitorar).
- **Agendamento automático:** resolvido sem código com o Agendador de Tarefas do Windows (`scripts/agendar_windows.ps1`), em 2026-10-08.
- **Atalho de duplo clique:** `scripts/varrer.bat`, em 2026-10-08.
