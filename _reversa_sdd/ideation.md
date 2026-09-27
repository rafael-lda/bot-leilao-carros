# Ideation — Bot Leilão Carros

> Selo 🟡 PLANEJADO em todos os itens, sujeito a validação.

## Brief original
Uma automação para varrer sites de leilões, editais de leilões de carros, me trazendo carros dentro dos meus filtros, carros que eu possa avaliar se são candidatos a concorrer.

## Problema
🟡 O usuário (Rafael) perderia horas por semana vasculhando manualmente vários sites de leilão de carros, cada um com layout diferente, tentando encontrar veículos dentro dos seus parâmetros. Esse trabalho repetitivo e fragmentado consome tempo significativo várias vezes por semana, sem garantia de cobertura completa dos leilões disponíveis.

## Valor entregue
🟡 Receber só os carros que interessam, filtrados e prontos para avaliar, sem precisar abrir nenhum site manualmente. Notificações diretas no Telegram com nome/modelo, preço e link do lote.

## Alternativas existentes
🟡
- **Busca manual em sites de leilão** — cada site tem um layout diferente, sem padronização, o que torna o processo lento e propenso a perder oportunidades.
- **Aplicativos pagos (se existirem)** — o usuário não tem certeza se existem, mas de qualquer forma seriam pagos e não ofereceriam a personalização desejada. O objetivo é ter algo sob medida para as suas regras e filtros específicos.

## Público-alvo (bruto)
🟡 O próprio Rafael — comprador pessoa física que busca carros em leilões online para avaliar oportunidades de compra. Ferramenta de uso pessoal, a princípio sem intenção de distribuição.

## Métricas de sucesso
🟡
- Automação rodando de forma estável e autônoma, cumprindo o planejado, sem quebras (ou com falhas poucas e gerenciáveis facilmente por um agente de IA).
- Rafael apenas supervisiona/verifica o que está acontecendo, sem intervenção manual nas buscas.

## Premissas a validar
🟡
1. Que os sites-alvo de leilão permitam ou tolerem scraping automatizado (sem bloqueios anti-bot severos).
2. Que os editais/anúncios tenham estrutura suficientemente padronizada para extração automatizada de dados (marca, modelo, ano, preço, etc.).
3. Que a infraestrutura para rodar a automação periodicamente seja viável em custo e complexidade.

## Decisões estratégicas levantadas

### Modo público vs. logado
🟡 Debate sobre operar com dados públicos ou logado nas contas do usuário:
- **Na maioria dos grandes leiloeiros** (Freitas, Vip Leilões, Claudio Kuss, Copart, Milan), os vídeos e fotos detalhadas **são públicos**.
- **Exceções:** alguns leiloeiros exigem login para fotos em alta resolução, anexos, laudos cautelares, número do chassi etc.
- **Decisão:** verificar leiloeiro a leiloeiro o que é público vs. restrito, para não perder dados/oportunidades.
- O sistema **poderá logar nas contas do Rafael** quando necessário para acessar dados restritos.

### Leiloeiros-alvo identificados
🟡 Freitas, Vip Leilões, Claudio Kuss, Copart, Milan (lista inicial, expansível).

### Estratégia de mapeamento por URL
🟡 Em vez de automatizar cliques com Selenium (frágil, lento, quebradiço):
- O usuário aplica os filtros manualmente **uma vez** no site do leiloeiro.
- Copia a URL filtrada resultante (ex: `vipleiloes.com.br/busca?tipo=financiamento&marca=nissan&modelo=versa`).
- O bot faz **fetch periódico nessas URLs pré-configuradas** e parseia o HTML/JSON retornado.
- Abordagem mais robusta, rápida e simples de manter do que automação de navegador.

### Estratégia de escalonamento progressivo (custo)
🟡 Princípio: **do mais simples e barato para o mais complexo/caro**.

| Nível | Quando usar | Custo |
|---|---|---|
| Script Python puro | Site simples, URL direta, sem bloqueio | Gratuito |
| Apify (IP normal) | Site complicado ou que começou a quebrar | Baixo |
| Apify (IP residencial) | Site com bloqueio anti-bot severo | Médio |

- **Ferramenta certa no lugar certo:** cada site/feature pode ter abordagem técnica diferente.
- **Não bater cabeça:** se algo complicou, escala para Apify sem culpa.
- **Custo só quando justificado.**

### Arquitetura iterativa com agente de IA como gestor
🟡 O projeto é **iterativo e incremental**:
- Um agente de IA (Codex, Antigravity, Claude Code) age como **gestor da automação**.
- De tempos em tempos, o agente "olha" todo o sistema: onde rodou redondo, onde quebrou.
- Sugere mudanças de abordagem (ex: migrar um site de script puro para Apify).
- Implementa a mudança após debate com Rafael.
- Objetivo: chegar a uma **versão otimizada custo × benefício**.

## Notificação e infraestrutura

### Canal de notificação
🟡 **Telegram** — a automação envia notificações dos lotes encontrados.

**Dados na notificação (MVP):**
- Nome/modelo do carro
- Preço
- Link do lote

**Futuro (expansível):**
- Opinião de agente de IA sobre o lote
- Tabela FIPE
- Fotos, laudos, dados adicionais

### Filtros configuráveis
🟡 O usuário fornece uma **lista variável de veículos-alvo**, cada um com:
- Nome do veículo
- Modelo
- Faixa de ano (de–até)
- Tipo de leilão

A lista é dinâmica — Rafael adiciona/remove veículos conforme interesse.

### Infraestrutura (progressiva)
🟡
- **Início:** notebook do Rafael, execução manual ou via cron (Antigravity/Claude Code/Codex).
- **Objetivo final:** servidor caseiro ou VPS, automação periódica sem intervenção.
- **Frequência:** a definir, mas o objetivo é execução automática em intervalos regulares.

## Notas
🟡 O projeto é uma ferramenta pessoal, o que simplifica requisitos de escalabilidade, autenticação multi-usuário e compliance. O foco deve ser em robustez do scraping, flexibilidade dos filtros, facilidade de manutenção (inclusive por agentes de IA) e custo otimizado.

---
Gerado por reversa-ideator em 2026-09-19T16:45:17-03:00
Atualizado com contexto adicional em 2026-09-19T17:20:16-03:00
Fonte: newproject-brief.md + debate do usuário com outra LLM
