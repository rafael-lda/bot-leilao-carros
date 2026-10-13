# Onboarding: testar o Freitas pela primeira vez

> Feature: `004-leiloeiro-freitas`
> Para: o Rafael, depois do `/reversa-coding`
> Tempo estimado: 10 minutos

## 1. Testes

No terminal do VS Code (fora do container): `venv\Scripts\activate` e `pytest -q`. Todos devem passar.

## 2. Primeira varredura (semeadura)

`varrer.bat` ou `python -m bot_leilao varrer`. O que esperar:

- no log, `Freitas Leiloeiro` com 3 páginas e `parser  | busca=freitas-leiloeiro:... | ~225 lotes | ok`, e uma linha com a quantidade de lotes "em loteamento" ignorados;
- no relatório, a seção "Leiloeiros" com "Freitas Leiloeiro | ok: N lote(s) lido(s)";
- nenhum aviso do Freitas no Telegram (estreia); os candidatos, se houver, no relatório ("Já estavam no site") e na lista numerada, com pátio (ex.: "SANTA BARBARA D OESTE - SP") e despesas.

## 3. Se aparecer alerta

| Alerta | Causa provável | O que fazer |
|--------|----------------|-------------|
| "Freitas Leiloeiro: ... certificado" | O Freitas trocou o certificado, corrigiu a cadeia ou o intermediário venceu | Seguir `src/bot_leilao/coleta/certificados/LEIA-ME.md` (o mesmo texto de `runbook-certificado.md`): diagnóstico em 5 minutos e o que fazer em cada caso. Pode pedir a um agente que siga o runbook |
| "Freitas Leiloeiro: o site bloqueou o acesso do bot" | Firewall (GoCache) voltou a barrar | Os outros seguem; degrau Apify (backlog item 9) |
| "o leitor não entendeu a página" | O Freitas mudou o HTML | Avise o Claude |
