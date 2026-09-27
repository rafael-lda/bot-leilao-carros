# PRD: Bot Leilão Carros

> Selo 🟡 PLANEJADO. Documento gerado a partir de ideation + personas.

**Versão:** 1.0
**Data:** 2026-09-19T17:47:39-03:00
**Autor:** reversa-drafter
**Status:** rascunho

---

## 1. Problema

🟡 Encontrar carros em leilões online que atendam a critérios específicos (marca, modelo, faixa de ano, tipo de leilão) exige vasculhar manualmente vários sites de leiloeiros, cada um com layout diferente, várias vezes por semana. Esse processo é lento, repetitivo, fragmentado e propenso a perder oportunidades — lotes bons passam despercebidos por falta de cobertura ou timing.

### Quem sente
🟡 Rafael — comprador pessoa física que busca carros em leilões online para comprar abaixo do mercado, usar e revender com pequeno lucro. Sente o problema toda vez que precisa fazer a varredura manual nos sites, dedicando horas por semana a uma atividade que poderia ser automatizada.

---

## 2. Personas-alvo

🟡 Referência completa em [`personas.md`](./personas.md). Resumo:

- **Rafael — Comprador de carros em leilão**: 🟡 Pessoa física, nível técnico intermediário (estudando desenvolvimento com IAs), busca carros abaixo do mercado para uso pessoal e revenda. Dor: horas perdidas em busca manual fragmentada em múltiplos sites.

---

## 3. Métricas de sucesso

🟡

| Métrica | Unidade | Alvo | Prazo |
|---|---|---|---|
| 🟡 Estabilidade da automação | % de execuções sem falha | ≥ 95% | 3 meses |
| 🟡 Autonomia operacional | Intervenções manuais por semana | ≤ 1 | 3 meses |
| 🟡 Cobertura de leiloeiros | Leiloeiros monitorados | ≥ 5 (Freitas, Vip Leilões, Claudio Kuss, Copart, Milan) | 3 meses |
| 🟡 Tempo de busca manual eliminado | Horas/semana economizadas | Redução de horas para minutos (só avaliar notificações) | 1 mês |

---

## 4. Escopo (in)

🟡

- 🟡 **Configuração de veículos-alvo**: lista variável com nome, modelo, faixa de ano (de–até), tipo de leilão
- 🟡 **Cadastro de leiloeiros-alvo**: lista de sites a monitorar (inicial: Freitas, Vip Leilões, Claudio Kuss, Copart, Milan)
- 🟡 **Exploração de sites por agente de IA**: navegação pública e logada para mapear dados disponíveis, com human-in-the-loop para login
- 🟡 **Mapeamento por URL**: cadastro de URLs filtradas dos sites de cada leiloeiro para fetch periódico
- 🟡 **Scraping e parsing**: extração de dados dos lotes (nome/modelo, preço, link, descrição) a partir das URLs configuradas
- 🟡 **Estratégia de acesso público vs. logado**: verificação leiloeiro a leiloeiro, login quando necessário para dados restritos (fotos alta resolução, laudos, chassi)
- 🟡 **Notificação via Telegram**: envio de lotes encontrados com nome/modelo, preço e link
- 🟡 **Escalonamento progressivo de ferramentas**: script Python puro → Apify (IP normal) → Apify (IP residencial), conforme necessidade
- 🟡 **Gestão por agente de IA**: agente monitora o sistema periodicamente, identifica falhas, sugere e implementa melhorias após debate com o usuário
- 🟡 **Execução periódica automatizada**: cron/agendamento para varredura em frequência a definir

---

## 5. Não-objetivos (out)

🟡

- 🟡 **Lances automáticos**: o sistema NÃO fará lances em leilões. Apenas monitora, filtra e notifica. A decisão de participar e dar lance é exclusivamente humana.
- 🟡 **Multi-usuário**: ferramenta pessoal, sem autenticação, perfis ou gestão de múltiplos usuários.
- 🟡 **Interface web/app completa**: a interface principal é o Telegram. Não há necessidade de dashboard web, app mobile ou frontend complexo neste momento.
- 🟡 **Integração com pagamento**: sem processamento financeiro, checkout ou integração bancária.

---

## 6. Restrições

🟡

| Tipo | Descrição |
|---|---|
| 🟡 Técnica | Sem restrição de stack — usar o que fizer mais sentido para cada parte do sistema. Estratégia de escalonamento progressivo (script puro → Apify). |
| 🟡 Prazo | [INDEFINIDO, validar com usuário] |
| 🟡 Compliance | Respeitar termos de uso dos sites de leilão na medida do possível. Sem exigência regulatória formal (LGPD não se aplica — dados são do próprio usuário e de lotes públicos). |
| 🟡 Orçamento | Princípio do menor custo: começar gratuito (script Python), escalar para Apify só quando justificado. IPs residenciais apenas em último caso. |

---

## 7. Dependências externas

🟡

- 🟡 **Sites de leiloeiros** (Freitas, Vip Leilões, Claudio Kuss, Copart, Milan): fonte primária de dados, sujeitos a mudanças de layout e políticas anti-bot.
- 🟡 **API do Telegram Bot**: canal de notificação, requer token de bot.
- 🟡 **Apify** (condicional): plataforma de scraping escalável, usada quando scripts puros não bastam.
- 🟡 **Infraestrutura de execução**: notebook (início) → servidor caseiro ou VPS (objetivo final).

---

## 8. Riscos

🟡

| Risco | Impacto | Probabilidade | Mitigação proposta |
|---|---|---|---|
| 🟡 Sites bloquearem scraping (anti-bot, CAPTCHA, rate limit) | Alto | Média | Escalonamento progressivo: script → Apify → IP residencial. Rotação de headers/user-agent. |
| 🟡 Mudança de layout dos sites quebrando parsers | Médio | Alta | Agente de IA como gestor: monitora, detecta quebras e adapta parsers. Arquitetura modular por leiloeiro. |
| 🟡 Dados insuficientes em modo público (fotos, laudos só logado) | Médio | Média | Mapeamento público vs. logado por leiloeiro. Login automatizado com human-in-the-loop quando necessário. |
| 🟡 Custo de Apify/infra escalar além do esperado | Baixo | Baixa | Usar Apify apenas onde justificado. Monitorar custos. Priorizar scripts gratuitos. |

---

## 9. Critérios de aceite (alto nível)

🟡

- 🟡 **Dado** uma lista de veículos-alvo configurada e URLs de leiloeiros cadastradas, **Quando** a automação executar no horário agendado, **Então** os lotes que casarem com os filtros devem ser notificados via Telegram com nome/modelo, preço e link.
- 🟡 **Dado** que um leiloeiro muda o layout do site, **Quando** o parser quebrar, **Então** o sistema deve registrar o erro e notificar (não falhar silenciosamente).
- 🟡 **Dado** que a automação roda por uma semana, **Quando** verificar o histórico, **Então** ≥ 95% das execuções devem ter completado sem intervenção manual.
- 🟡 **Dado** um lote encontrado, **Quando** o usuário receber a notificação no Telegram, **Então** deve conseguir acessar o lote no site do leiloeiro pelo link em 1 clique.

---

## Pendências de cobertura

🟡

- Prazo do projeto (sem deadline definido)
- Frequência exata de varredura (a definir na implementação)
- Dados adicionais na notificação Telegram (futuro: opinião de IA, tabela FIPE)

---

Gerado por reversa-drafter em 2026-09-19T17:47:39-03:00
Fontes: ideation.md, personas.md

