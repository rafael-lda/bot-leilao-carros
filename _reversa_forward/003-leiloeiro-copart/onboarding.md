# Onboarding: testar a Copart pela primeira vez

> Feature: `003-leiloeiro-copart`
> Para: o Rafael, depois do `/reversa-coding`, no notebook Windows
> Tempo estimado: 10 minutos

## 1. Atualizar e testar

A pasta é a mesma do container, então o código já está lá. No terminal do VS Code (fora do container):

```powershell
venv\Scripts\activate
pytest -q
```

Todos os testes devem passar.

## 2. Conferir o bloco da Copart

Em `config/leiloeiros.yaml` deve haver o bloco `nome: Copart`, com `condicao: FINANCIAMENTO` e `ativo: true`. Para desligar: `ativo: false`.

## 3. Primeira varredura (semeadura)

```powershell
python -m bot_leilao varrer
```

ou `varrer.bat`. O que esperar:

- no log (dry-run de 2026-10-11 no container): `Copart | preparando sessão: ok (8 cookie(s))`, `Copart | busca=copart:... | 16 página(s) | ok` (cerca de 80 segundos) e `parser  | busca=copart:... | 1506 lotes | 0 descartados | ok`, sem aviso de lote repetido nem de total divergente;
- **nenhum aviso da Copart no Telegram** (é a estreia da busca);
- no relatório de `1OUTPUT/`, a seção "Já estavam no site (semeadura)" com os candidatos da Copart (em 11/10 eram 9: Duster 2019 a 2022, três Kicks 2019 e Versa 2017 e 2019; as 4 Duster Oroch ficaram de fora pelo `excluir`), cada um com **Pátio** e, quando houver, **FIPE**;
- os mesmos lotes em `lotes-a-monitorar.md`, marcados "por semeadura".

A varredura inteira (Vip, Kuss e Copart) levou **5m47s** no dry-run de 2026-10-11 (Vip 11 páginas, Kuss 43, Copart 16).

## 4. Como fica um aviso da Copart

A partir da segunda varredura, um lote novo chega assim:

```
1. RENAULT DUSTER OROCH 1.6 16V SCE — 2022
   R$ 36.000 — Copart — VITÓRIA DE SANTO ANTÃO - PE — FIPE R$ 80.266 — Pregão 15/10 08:30
   Obs.: PEQUENOS AMASSADOS · Documento NORMAL · Motor dá partida e engrena · Comitente AYMORE CFI
   https://www.copart.com.br/lotDetail/1141180
```

Lote ainda sem classificação chega como "Preço a confirmar", sem FIPE nem data, com "Aguardando classificação da Copart (data, FIPE e lance a definir)" nas observações.

Os avisos do Vip e do Kuss também passam a mostrar o pátio ("SC", "Curitiba - PR").

## 5. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---------|----------------|-------------|
| Alerta "Copart: bloqueado" | O Imperva passou a barrar o robô | Vip e Kuss seguem; avise o Claude (degrau Apify, backlog item 9) |
| Aviso no log "lote repetido entre páginas" | A Copart mudou a ordenação | Avise o Claude |
| Muitos avisos de carros no Nordeste | Estoque da Copart concentrado lá | Normal; o pátio no aviso serve para descartar; filtro por estado pode vir depois |
| Alerta "o site bloqueou o acesso do bot" de outro leiloeiro | Vale para todos os leiloeiros desde a feature 003 | No máximo 1 por dia por leiloeiro; os outros seguem |
