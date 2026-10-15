# Regression Watch: Skill `analisar-lotes` (triagem e custo na garagem)

> Identificador: `006-analisar-lotes`
> Âncora greenfield: watch principal vazio até uma extração `/reversa` confirmar regras. IDs continuam a numeração das features anteriores (W001 a W037).

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------------------------|-----------------------------|---------------------|-------------------|

## Observações

| ID | Origem | Requisito | Situação |
|----|--------|-----------|----------|
| W038 | `requirements.md` RF-02 a RF-04, RN-02 | Triagem com "na dúvida, a confirmar"; reprovado só com evidência, para `lotes-descartados.md` | Implementado; avaliado pelo `skill-creator` (19/19 e 20/20) e executado na lista real em 2026-10-15 (1 aprovado, 5 reprovados, 8 a confirmar) |
| W039 | `requirements.md` RF-05, RF-06; D-108 | Critérios no `veiculos-alvo.yaml`; câmbio no motor só com certeza | Implementado e testado; conferir no próximo lote do Milan com câmbio manual |
| W040 | `requirements.md` RF-09; D-114 | FIPE pela parallelum (500 consultas/dia) com o site oficial de reserva | Funcionando em 2026-10-15; o endpoint do site oficial não é documentado: se mudar, a reserva cai e a FIPE fica "indisponível" quando a parallelum falhar |
| W041 | `requirements.md` RF-08; D-115 | Distância pelo Nominatim + OSRM públicos, com cache | Funcionando (Londrina → Curitiba 385 km); o OSRM público é de demonstração |
| W042 | `requirements.md` RN-08 | Frete a R$ 4,50/km é estimativa | **Trocar pelo orçamento real de guincho** quando o Rafael tiver um; nos pátios do Nordeste o frete estimado passa de R$ 10 mil |
| W043 | `requirements.md` RN-11, RF-13 | Pregão passado não reprova; resultado anotado; apelido nunca gravado | Kuss: só lance presencial/online, sem valor (evento 897). **Checar o que Vip, Copart, Freitas e Milan mostram depois do pregão** (backlog item 7) |
| W044 | `roadmap.md` D-106 | `.gitignore` com `…/skills/*` e exceção para a skill | Uma reinstalação do Reversa (`npx reversa install`) pode recolocar `.claude/skills/` inteiro; conferir com `git check-ignore` depois de reinstalar |

## Histórico de re-extrações

## Arquivadas
