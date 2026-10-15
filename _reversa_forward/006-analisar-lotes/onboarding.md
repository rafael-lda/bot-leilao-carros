# Onboarding: skill `analisar-lotes`

> Para: Rafael, usando a skill pela primeira vez (Claude Code, Antigravity ou Codex)
> Pré-requisito: o bot funcionando e a lista `1OUTPUT/lotes-a-monitorar.md` com lotes

## 1. Conferir os critérios

Abra `config/veiculos-alvo.yaml`. No topo, o bloco `padrao` vale para todos os carros (câmbio aceito, sinistro, sucata, mecânica, pequenas avarias). Em cada alvo, o texto `triagem` diz em português o que mais a skill deve exigir. Para mudar um critério, edite e salve; vale na próxima análise.

## 2. Conferir os custos

Abra `config/custos.yaml` (criado na primeira análise com os valores combinados). O frete está como estimativa (R$ 4,50/km); quando tiver um orçamento de guincho, troque o número.

## 3. Rodar a triagem

No chat do agente: `/analisar-lotes` (a lista inteira) ou `/analisar-lotes 3` (só o lote 3).

O que esperar:
- O agente lê cada lote, abre a página só quando precisa (no Milan, cada página custa ~US$ 0,08 e ele avisa).
- Antes de mover algum lote, ele mostra o resumo: aprovados, reprovados (com motivo e prova) e a confirmar.
- Os reprovados vão para `1OUTPUT/lotes-descartados.md`; os outros ganham a linha **Triagem** no bloco.

Não rode durante uma varredura: a skill recusa e explica.

O que também aparece (primeira execução real, 2026-10-15, 14 lotes, cerca de 5 a 7 minutos):
- **Pregão que já passou** não descarta o lote: o bloco ganha "Resultado do pregão". O Kuss só diz se o último lance foi presencial ou online, sem o valor.
- **Câmbio deduzido** do título é gravado no campo Câmbio, com a origem (ex.: "manual (título 'DYN 20M')").
- **Reaparições** (mesmo carro em outro evento, pelo final de placa) aparecem no resumo.
- **Reconferência dos "a confirmar"** (a cada execução): o agente relê esses lotes, atualiza Lance atual e Pregão quando mudaram e julga de novo; a linha Triagem ganha a data do dia.
- **Resultados por leiloeiro:** o resumo agrupa os pregões que já passaram por leiloeiro e diz o que cada um divulga (Vip e Freitas dão o valor; Kuss, Milan e Copart não). Detalhes em `.claude/skills/analisar-lotes/references/resultados-por-leiloeiro.md`.
- **Referência de lance máximo** para os "a confirmar", pela versão automática mais barata, só no resumo: mostra quais pátios ficam inviáveis pelo frete.

## 4. Custo na garagem

Para os aprovados, a skill consulta a FIPE e preenche FIPE, Frete, Valor estimado na garagem e Lance máximo. Se a versão do título couber em mais de uma versão da FIPE, ela lista as opções com valor em vez de escolher.

## 5. Desfazer um descarte

`/analisar-lotes devolver 2` (ou peça "devolve o lote 2"): o bloco volta para o fim da lista.

## 6. Para quem desenvolve

```
venv\Scripts\python.exe -m pytest
venv\Scripts\python.exe -m bot_leilao analise lotes
venv\Scripts\python.exe -m bot_leilao analise custo --lance 61000 --despesa 2650 --patio "Curitiba - PR" --documento-uf SC
```

A skill fica em `.claude/skills/analisar-lotes/` (cópia idêntica em `.agents/skills/analisar-lotes/`).
