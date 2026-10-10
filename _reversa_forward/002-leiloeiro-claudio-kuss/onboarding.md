# Onboarding: testar o Claudio Kuss pela primeira vez

> Feature: `002-leiloeiro-claudio-kuss`
> Para: o Rafael, depois do `/reversa-coding`, no notebook Windows (VS Code fora do container) ou no container
> Tempo estimado: 15 minutos

## 1. Atualizar o código

No terminal do VS Code, na pasta do projeto:

```powershell
git pull
venv\Scripts\activate
pip install -e .[dev]
pytest -q
```

Todos os testes devem passar. Se algum falhar, pare aqui e mande a saída para o Claude.

## 2. Conferir o bloco do Claudio Kuss

Abra `config/leiloeiros.yaml`. Deve haver um bloco assim:

```yaml
  - nome: Claudio Kuss Leilões
    base_url: https://www.claudiokussleiloes.com.br
    ativo: true
    ...
        filtros:
          categoria: Veículos - Financeiras
```

Para desligar o Claudio Kuss a qualquer momento: `ativo: false`.

## 3. Ver os candidatos antes da semeadura (importante)

A **primeira** varredura real com o Claudio Kuss ativo **semeia** a busca dele: os lotes que casam hoje viram "conhecidos" e **não** chegam no Telegram. Para vê-los antes, rode o modo de teste, que não grava nada e não envia nada:

```powershell
python -m bot_leilao varrer --dry-run
```

O que esperar no log:

- `coleta  | Claudio Kuss Leilões | ... pág 1 ...` até umas 43 páginas, cerca de 4 minutos (5 s entre páginas);
- uma linha por evento com o total lido igual ao informado pelo site (sem aviso de divergência);
- `parser  | ... lote(s) de sucata ignorado(s)`;
- na lista final de candidatos, os lotes do Claudio Kuss com link `.../lance/<evento>/0/<número>`.

Abra os links dos candidatos no navegador e confira se é o mesmo carro.

## 4. Primeira varredura real

```powershell
python -m bot_leilao varrer
```

ou o atalho `varrer.bat`. Resultado esperado: os lotes **novos do Vip** chegam normalmente; o Claudio Kuss aparece no relatório de `1OUTPUT/` como semeado ("N lote(s) registrados como conhecidos"), sem aviso.

## 5. Como fica um aviso do Claudio Kuss

A partir da segunda varredura, um lote novo do Kuss chega assim no Telegram:

```
1. IMP RENAULT/FLUENCE DYN 20A — 2013
   Preço a confirmar — Claudio Kuss Leilões — Pregão 13/10 10:00
   Obs.: SINISTRADO - NOS DOCUMENTOS CONSTA RECUPERADO DE SINISTRO. REGULARIZAÇÃO POR CONTA DO ARREMATANTE
   https://www.claudiokussleiloes.com.br/lance/897/0/282622
```

E no relatório e em `lotes-a-monitorar.md`, com as linhas extras:

```
- **Pregão:** 13/10/2026 10:00
- **Despesas admin.:** R$ 2.750
- **Documento:** Placa F**-**35, documento de SÃO PAULO
- **Observações:** SINISTRADO - NOS DOCUMENTOS CONSTA ...
```

## 6. Conferências depois do primeiro pregão (13/10/2026)

1. Abra um link de lote do evento 897 que já foi loteado. Se a página não abrir o lote certo, avise o Claude: o formato do link precisa mudar (premissa do roadmap §4).
2. Quando um evento novo aparecer, veja se algum carro do evento anterior voltou com outro número (reaparição). Se sim, anote na lista de monitoramento.

## 7. Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---------|----------------|-------------|
| Alerta "Claudio Kuss Leilões: o parser não conseguiu ler a página" | O site mudou o formato | Mande o log ao Claude; o Vip continua funcionando |
| Varredura passou de 10 minutos | Muitos eventos de financeiras ao mesmo tempo | Avise o Claude (risco R-01 do roadmap) |
| Aviso com "observações não lidas" | O detalhe do lote falhou naquela hora | Abra o link e leia no site |
| Nenhum lote do Kuss por semanas | Os alvos não aparecem nos eventos dele | Normal; confira no relatório se a busca do Kuss terminou com `ok` |
