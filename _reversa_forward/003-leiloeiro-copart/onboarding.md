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

- no log, `Copart` com cerca de 16 páginas (uns 80 segundos) e `parser  | busca=copart:... | ~1.500 lotes | ok`, sem aviso de lote repetido;
- **nenhum aviso da Copart no Telegram** (é a estreia da busca);
- no relatório de `1OUTPUT/`, a seção "Já estavam no site (semeadura)" com os candidatos da Copart (em 11/10 eram 13: Duster, Duster Oroch, Kicks e Versa), cada um com **Pátio** e, quando houver, **FIPE**;
- os mesmos lotes em `lotes-a-monitorar.md`, marcados "por semeadura".

A varredura inteira (Vip, Kuss e Copart) deve ficar abaixo de 10 minutos.

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
| Duster Oroch (picape) avisado como Duster | O alvo "Duster" casa com "Duster Oroch" | Conhecido (backlog item 4, "palavras a excluir") |
