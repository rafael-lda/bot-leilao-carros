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

O que esperar no log (medido no dry-run de 2026-10-10, no container):

- `coleta  | Claudio Kuss Leilões | 2 evento(s) 'Veículos - Financeiras': 897 (13/10 10:00), 898 (20/10 10:00)`;
- `pág 1` a `pág 43` do Claudio Kuss, cerca de 3,5 minutos (5 s entre páginas); a varredura inteira, com o Vip, levou **5m16s**;
- `parser  | busca=claudio-kuss-leiloes:... | 391 lotes | 0 descartados | ok`, **sem** nenhum aviso de "o site informou N lote(s) e foram lidos M";
- linhas `marca fora da tabela conhecida` para máquinas e reboques (`new holland`, `reb`, `librelato`...): são só informativas;
- na lista final de candidatos, os lotes do Claudio Kuss com link `.../lance/<evento>/0/<número>`. Em 2026-10-10 foram três: os Fluence 2013 (sinistrado) e 2015 (mecânica com problemas) e o **Kicks S CVT 2019** (sem observações).

No dry-run da primeira vez os candidatos aparecem **sem** observações: o bot só abre o detalhe dos lotes que vai avisar. Abra os links para ver o estado de cada um.

Abra os links dos candidatos no navegador e confira se é o mesmo carro.

## 4. Primeira varredura real

```powershell
python -m bot_leilao varrer
```

ou o atalho `varrer.bat`. Resultado esperado: os lotes **novos do Vip** chegam normalmente; os candidatos do Claudio Kuss que já estavam no site são registrados como conhecidos **sem aviso no Telegram**, mas aparecem no relatório de `1OUTPUT/` na seção "Já estavam no site (semeadura)" e entram em `lotes-a-monitorar.md` marcados "por semeadura" (emenda E001, de 2026-10-11).

Sucata e retirados são descartados depois de abrir o detalhe, com linhas `enriq   | novos: ...` e `enriq   | semeados: N lote(s) detalhado(s), R retirado(s), S sucata(s), F falha(s)` no log.

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
