# Regression Watch: MVP de Varredura Ponta a Ponta

> Identificador: `001-mvp-varredura-ponta-a-ponta`
> Feature greenfield: não há regras 🟢 extraídas de código para vigiar. O watch principal fica vazio até uma extração `/reversa` sobre o código novo confirmar regras.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-----------------------------|---------------------|-------------------|

## Observações

Requisitos especificados por teste nesta feature, sem peso de regressão até confirmação por re-extração. Atualizado ao fim de cada etapa da codificação.

| ID | Origem | Requisito | Situação |
|----|--------|-----------|----------|
| W001 | `requirements.md` RF-01, RF-02, RF-16 | Configuração validada antes da rede | Implementado e testado, inclusive de ponta a ponta |
| W002 | `requirements.md` RF-03, RF-04, RF-18 | Sessão com cookie, retry, bloqueio, paginação espaçada | Implementado e testado, inclusive de ponta a ponta |
| W003 | `requirements.md` RF-05 a RF-07 | Lote normalizado, id estável, quebra sinalizada sem falso alarme de busca vazia | Implementado e testado, inclusive de ponta a ponta |
| W004 | `requirements.md` RF-08, RF-09, RF-13, RF-17 | Critérios, deduplicação, semeadura, retirados | Implementado e testado, inclusive de ponta a ponta |
| W005 | `requirements.md` RF-10, RF-11 | Digest e alerta | Implementado e testado, inclusive de ponta a ponta |
| W006 | `requirements.md` RF-12, RF-15 | Histórico e trava | Implementado e testado, inclusive de ponta a ponta |
| W007 | `requirements.md` RN-08 | Nenhum segredo em log, console ou banco | Implementado e testado, inclusive de ponta a ponta |
| W008 | `requirements.md` RF-14, RF-15 | CLI `varrer`/`testar-telegram`, códigos de saída, trava | Implementado e testado, inclusive de ponta a ponta |
| W010 | `parser-lotes.md` EC-16, roadmap D-32 | Km 0 ou ≥ 900.000 vale "não informada" e não elimina por teto de km | Implementado e testado |
| W009 | `interfaces/vip-pesquisa.md` §4 | `429` sem `Retry-After` espera 30 s | Implementado e testado; observar a frequência de `429` nas execuções reais |

## Histórico de re-extrações

## Arquivadas
