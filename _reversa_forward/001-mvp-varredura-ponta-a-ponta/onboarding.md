# Onboarding: primeira execução do MVP

> Para: Rafael, testando a feature `001-mvp-varredura-ponta-a-ponta` depois que o `/reversa-coding` terminar.
> Tempo estimado: 20 a 30 minutos, a maior parte criando o bot no Telegram.
> Os comandos valem no notebook Windows (PowerShell) e no devcontainer (bash); onde diferem, as duas formas aparecem.

## Passo 0. Pré-requisitos

1. Python 3.12 ou mais novo:

   ```
   python --version
   ```

   No Windows, se aparecer versão antiga ou "não encontrado", instale pelo site oficial e marque "Add python.exe to PATH".

2. Estar na raiz do projeto (a pasta que contém `pyproject.toml`).

## Passo 1. Ambiente e dependências

```
python -m venv .venv
```

Ativar:

- PowerShell: `.venv\Scripts\Activate.ps1`
- bash: `source .venv/bin/activate`

Instalar:

```
pip install -e .[dev]
```

Conferir que os testes passam **sem internet**:

```
pytest
```

Esperado: todos verdes. Se algum falhar aqui, pare e registre com `/reversa-debugger`; não siga para a execução real.

## Passo 2. Criar o bot no Telegram

1. No Telegram, abra a conversa com **@BotFather**.
2. Envie `/newbot`, escolha um nome (ex.: "Bot Leilão Rafael") e um usuário terminado em `bot`.
3. O BotFather responde com o **token**, no formato `123456789:AA...`. Trate-o como senha.
4. Abra a conversa com o seu bot novo e envie qualquer mensagem, por exemplo `oi`. Sem isso, o bot não tem permissão de escrever para você.

## Passo 3. Configurar o `.env`

1. Copie o exemplo:

   - PowerShell: `Copy-Item .env.example .env`
   - bash: `cp .env.example .env`

2. Cole o token em `TELEGRAM_BOT_TOKEN=`.
3. Descubra o seu chat id: abra no navegador `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates` e procure `"chat":{"id":` na resposta. Cole o número em `TELEGRAM_CHAT_ID=`.
4. Teste:

   ```
   python -m bot_leilao testar-telegram
   ```

   Esperado: uma mensagem de teste chega no Telegram. Se aparecer `401`, o token está errado; `400 chat not found`, o chat id está errado ou você não mandou mensagem ao bot no passo 2.4.

## Passo 4. Configurar o que procurar

1. Rode uma vez para gerar os arquivos de exemplo:

   ```
   python -m bot_leilao varrer
   ```

   Esperado: a execução **aborta** dizendo que criou `config/veiculos-alvo.yaml` e `config/leiloeiros.yaml` de exemplo. Isso é o comportamento correto.

2. Edite `config/veiculos-alvo.yaml` com **um ou dois** carros que você de fato quer (decisão de 2026-09-27: poucos alvos para conferir à mão). Mantenha `financiamento` em `tipos_leilao`, porque a busca do Vip traz só recuperados de financiamento. Troque `ativo` para `true`.

3. Em `config/leiloeiros.yaml`, troque `ativo` do Vip Leilões para `true`. Não mexa nos filtros: `procedencia: 4` e `monta: 1` já são a escolha de 2026-09-27.

4. Para ver um erro de propósito, troque `ano_min` para um valor maior que `ano_max` e rode `python -m bot_leilao varrer`. Esperado: aborta citando o alvo e o campo, **sem** nenhuma linha `coleta |`. Desfaça a troca.

## Passo 5. Ensaio sem enviar nada

```
python -m bot_leilao varrer --dry-run
```

Esperado, em cerca de 2 minutos:

- `coleta | Vip Leilões | preparando sessão: cookie de canal obtido`
- uma linha por página, cerca de 17, com 5 s entre elas
- `parser | … | ~200 lotes | 0 descartados | ok`
- `filtro | …` com a contagem de candidatos para os seus alvos
- a lista dos candidatos impressa no console, com o aviso de que a busca ainda está em semeadura e, portanto, uma execução real os registraria como conhecidos sem enviar digest

Confira 2 ou 3 candidatos abrindo o link no navegador: o carro, o ano de modelo e o valor atual devem bater com o site.

## Passo 6. Primeira execução real: semeadura

```
python -m bot_leilao varrer
```

Esperado: `busca em semeadura: N candidatos registrados como conhecidos, nenhum digest`. **Nenhuma** mensagem no Telegram. Isso é intencional: sem semeadura, a estreia mandaria tudo o que já estava no site (RN-07).

## Passo 7. Forçar um lote "novo" e receber o digest

Para não esperar o Vip publicar um carro novo, apague um lote conhecido do banco:

```
python -c "import sqlite3; c=sqlite3.connect('dados/bot-leilao.sqlite3'); r=c.execute('SELECT id_canonico, link FROM lote_conhecido LIMIT 1').fetchone(); print(r); c.execute('DELETE FROM lote_conhecido WHERE id_canonico=?', (r[0],)); c.commit()"
```

Rode de novo:

```
python -m bot_leilao varrer
```

Esperado: um digest no Telegram com exatamente esse lote. Toque no link: deve abrir a página do lote no Vip.

Se o passo 6 não tiver registrado nenhum candidato, nenhum dos seus alvos casa com o que o Vip tem hoje. Amplie temporariamente a faixa de ano ou o teto de um alvo, rode o passo 5 até aparecer candidato, e refaça os passos 6 e 7.

## Passo 8. Execução repetida não renotifica

```
python -m bot_leilao varrer
```

Esperado: nenhuma mensagem no Telegram e `0 novos` no log.

## Passo 9. Conferir o histórico

```
python -c "import sqlite3; c=sqlite3.connect('dados/bot-leilao.sqlite3'); [print(r) for r in c.execute('SELECT iniciado_em, modo, veredito, lotes_vistos, lotes_candidatos, lotes_novos, lotes_semeados FROM execucao ORDER BY iniciado_em')]"
```

Esperado: uma linha por execução dos passos 4 a 8, inclusive a que abortou por configuração, com veredito `falha`.

## Pronto

Se os passos 5 a 8 se comportaram como descrito, a fatia vertical está funcionando. Problemas encontrados vão para `/reversa-debugger`, citando o passo e a saída do console.
