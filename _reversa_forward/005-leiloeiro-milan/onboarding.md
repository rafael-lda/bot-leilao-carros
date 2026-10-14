# Onboarding: Leiloeiro Milan e nível Apify

> Para: Rafael, testando a feature pela primeira vez no notebook (Windows)
> Pré-requisito: features 001 a 004 funcionando (`scripts\varrer.bat` roda sem erro)

## 1. Conferir o token do Apify

O token já está no `.env` desde 2026-10-13. Para conferir sem expor o valor:

1. Abra o `.env` na raiz do projeto.
2. Confira que existe a linha `APIFY_TOKEN=apify_api_...`.
3. Não copie o token para o chat, e-mail ou outro arquivo.

Se precisar gerar outro: https://console.apify.com → **Settings → API & Integrations** → copie o token e troque na linha do `.env`.

## 2. Ativar o Milan

Em `config\leiloeiros.yaml`, o bloco do Milan vem com `ativo: true` e `nivel_coleta: apify`. Para desligar a qualquer momento: `ativo: false`.

## 3. Primeiro teste, sem gastar o Telegram

```
venv\Scripts\python.exe -m bot_leilao varrer --dry-run
```

O que esperar no terminal e no log (`dados\logs`):

- `coleta | Milan Leilões | ... | apify | ...` nas páginas do Milan (agenda e um catálogo por leilão de financiamento).
- Uma linha de consumo: páginas pelo Apify e gasto da varredura.
- A lista de candidatos, com os do Milan (se houver alvo no leilão da vez).

Custo: US$ 0,16 a 0,40 (agenda, catálogo e as páginas dos candidatos).

## 4. Primeira varredura real (semeadura do Milan)

Dê dois cliques em `scripts\varrer-completo.bat`.

- Nada do Milan chega no Telegram nesta primeira vez (semeadura).
- Os candidatos do Milan entram no relatório `1OUTPUT\relatorio-<data>.md` e na `1OUTPUT\lotes-a-monitorar.md`, com km, lance (da página do lote), pátio, pregão, **câmbio** e observações (avisos do estado e comitente).
- Na seção "Leiloeiros" do relatório, a linha do Milan mostra quantos lotes foram lidos, as páginas e o gasto no Apify, e o gasto do ciclo.

## 5. Atalhos do dia a dia

| Atalho | O que roda | Custo |
|--------|-----------|-------|
| `scripts\varrer.bat` | Vip, Claudio Kuss, Copart e Freitas (sem os pagos) | zero |
| `scripts\varrer-completo.bat` | Os 5, com o Milan | ~US$ 0,16 a 0,40 |
| Agendamento (seg, qua e sex às 08h) | Os 5 | ~US$ 0,16 a 0,40 por varredura |

Com o `varrer.bat`, a seção "Leiloeiros" do relatório diz "Milan: não incluído nesta varredura (sem pagos)". A lista de lotes e o Telegram não mudam.

## 6. Acompanhar o gasto

- No relatório: linha do Milan na seção "Leiloeiros" ("ciclo US$ Y de 5,00 até DD/MM").
- No Apify: https://console.apify.com → **Billing / Usage**.
- Ao passar de 80% do limite do ciclo, chega um alerta no Telegram.

## 7. Se quiser espaçar o Milan

No bloco do Milan em `config\leiloeiros.yaml`, acrescente (ou tire o `#` de):

```yaml
    intervalo_horas: 72
```

O Milan passa a ser lido no máximo a cada 72 h; nas outras varreduras o relatório diz "pulado pelo intervalo". Se o bot vir um leilão anunciado com menos antecedência que o intervalo, chega um alerta sugerindo baixar o número. Para voltar a ler sempre, apague a linha.

## 8. Se o Milan parar de funcionar

| Alerta no Telegram | O que fazer |
|--------------------|-------------|
| "token do Apify inválido" | Gerar token novo (passo 1) |
| "cota do Apify esgotada" | Esperar o próximo ciclo (data no alerta) ou pagar o excedente no console |
| "o site bloqueou o acesso do bot (desafio_antibot via apify: ...)" | O ator deixou de passar pelo Cloudflare. Pedir ao Claude a troca de ator (`apify_ator`): ele cria o perfil do ator novo e testa com amostra |
| "o parser não conseguiu ler a página" | O Milan mudou o layout; pedir ao Claude o conserto do parser |
| "Apify: tempo esgotado" ou "plataforma indisponível" | Costuma passar sozinho; se repetir por dias, ver https://status.apify.com |

## 9. Teste automatizado (para quem desenvolve)

```
venv\Scripts\python.exe -m pytest
```

Os testes não usam rede: o Apify é simulado com as respostas reais guardadas em `tests/fixtures/milan/` (cópias de `_reversa_forward/005-leiloeiro-milan/amostras/`).
