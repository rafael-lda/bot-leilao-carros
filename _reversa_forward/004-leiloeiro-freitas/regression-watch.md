# Regression Watch: Leiloeiro Freitas

> Identificador: `004-leiloeiro-freitas`
> Âncora greenfield: watch principal vazio até uma extração `/reversa` confirmar regras. IDs continuam a numeração das features anteriores (W001 a W024).

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-----------------------------|---------------------|-------------------|

## Observações

| ID | Origem | Requisito | Situação |
|----|--------|-----------|----------|
| W025 | `requirements.md` RF-01 a RF-03 | Busca do Freitas até a mensagem de fim, sem repetição; lote normalizado com tipo pela etiqueta | Implementado e testado; dry-run real 2026-10-13: 255 cards, 234 lotes |
| W026 | `requirements.md` RN-10, roadmap D-77 | Lotes em loteamento ignorados até o número definitivo | Implementado e testado; **conferir depois do loteamento do leilão 8111** (pregão 24/10) se os números mudaram e se não houve aviso duplicado |
| W027 | `requirements.md` RF-05, roadmap D-83 | Verificação de certificado nunca desligada; intermediário oficial na pasta | Implementado e testado (inclui varredura do código contra `verify=False`); **o intermediário vence em 2027-05-21**: procedimento em `src/bot_leilao/coleta/certificados/LEIA-ME.md` |
| W028 | `requirements.md` RF-08, roadmap D-85 | Falha de certificado gera alerta (1 por dia) apontando o runbook | Implementado e testado |
| W029 | `requirements.md` RF-09 | Varredura com 4 leiloeiros abaixo de 10 minutos | Medido: 6m43s (2026-10-13); margem menor: observar ao entrar o Milan |

## Histórico de re-extrações

## Arquivadas
