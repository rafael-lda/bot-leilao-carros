# Regression Watch: Leiloeiro Milan (e o nível Apify)

> Identificador: `005-leiloeiro-milan`
> Âncora greenfield: watch principal vazio até uma extração `/reversa` confirmar regras. IDs continuam a numeração das features anteriores (W001 a W029).

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-----------------------------|---------------------|-------------------|

## Observações

| ID | Origem | Requisito | Situação |
|----|--------|-----------|----------|
| W030 | `requirements.md` RF-01, RF-02, RN-06, RN-07 | Milan só pelo Apify, nada pelo IP local; token só no `.env` e no cabeçalho, nunca em log, banco ou relatório | Implementado e testado; dry-run real 2026-10-14: agenda lida pelo Apify (200) |
| W031 | `requirements.md` RF-03 a RF-05, D-94 a D-97 | Agenda → catálogo em toda varredura; lance só dos candidatos pela página do lote | Implementado e testado com as amostras de 2026-10-13; o dry-run de 2026-10-14 não tinha leilão de financiamento na agenda: **conferir no próximo leilão** (catálogo, pátio, câmbio e lance pela página do lote) |
| W032 | `requirements.md` RF-06, RN-07, D-88 | Ator `neatrat/cloudflare-scraper` passa pelo Cloudflare | Funcionando em 2026-10-13/14. Se vier alerta de bloqueio "via apify", trocar de ator (perfil novo em `coleta/apify.py`; 4 alternativas em `investigation.md` §3) |
| W033 | `requirements.md` RF-09, RN-13 | Consumo na seção "Leiloeiros" e alerta a 80% do ciclo | Implementado e testado. **O gasto da varredura sai subcontado** (o evento por item é cobrado segundos depois: US$ 0,05 lido × US$ 0,08 real); o gasto do ciclo acerta na varredura seguinte |
| W034 | `requirements.md` RF-11, RF-12, RN-09, RN-10 | `--sem-pagos` e `intervalo_horas` | Implementado e testado; o Milan começa sem intervalo |
| W035 | `requirements.md` RF-13, RN-11 | Antecedência dos leilões e alerta quando menor que o intervalo | Implementado e testado; **depois de ~1 mês de varreduras, consultar `evento_visto` para saber a antecedência real do Milan** e decidir sobre o intervalo |
| W036 | `requirements.md` RF-14, RN-12, D-98 | Lote acima do teto depois do detalhe não é avisado (todos os leiloeiros) | Implementado e testado; risco R-04 do roadmap: esse lote não é registrado e é detalhado de novo a cada varredura (US$ 0,08 por vez no Milan); rever se aparecer no consumo |
| W037 | `requirements.md` RF-10 | Varredura com 5 leiloeiros abaixo de 10 minutos | Medido: 5m49s (2026-10-14, Milan com a agenda só) |

## Histórico de re-extrações

## Arquivadas
