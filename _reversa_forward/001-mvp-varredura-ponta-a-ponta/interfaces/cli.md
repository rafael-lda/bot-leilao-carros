# Interface: Linha de comando `python -m bot_leilao`

> Tipo: CLI, **exposta** ao Rafael e, numa feature futura, ao agendador do sistema operacional
> Origem: `requirements.md` RF-14 e RF-15; roadmap D-25
> Confidência: 🟢 exigido pelo requirements, 🟡 decidido neste plano

## 1. Comandos

### `varrer`

```
python -m bot_leilao varrer [--dry-run] [--raiz <pasta>]
```

Executa a cadeia completa uma vez: configuração, coleta, parsing, filtragem, notificação e registro. 🟢

| Opção | Efeito | Confidência |
|-------|--------|-------------|
| `--dry-run` | Roda tudo, inclusive a coleta real, mas não envia nada ao Telegram: imprime no console a lista de candidatos, o digest que seria enviado (vazio se a busca estiver em semeadura, com aviso explícito) e os alertas. **Não** grava `lote_conhecido` nem `busca_semeada`, e registra a execução com `modo = 'dry_run'`. Não exige variáveis do Telegram | 🟡 |
| `--raiz <pasta>` | Pasta que contém `config/`, `dados/` e `.env`. Padrão: diretório atual | 🟡 |

### `testar-telegram`

```
python -m bot_leilao testar-telegram [--raiz <pasta>]
```

Valida `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` e envia uma mensagem curta de teste. Não toca nos leiloeiros nem grava no banco. Serve para o passo 3 do `onboarding.md`. 🟡

## 2. Códigos de saída

| Código | Situação | Registro em `execucao` |
|--------|----------|------------------------|
| `0` | `sucesso` ou `sucesso_parcial` | Sim |
| `1` | `falha`: configuração inválida, banco inacessível, falha total de coleta, falha no envio do digest | Sim, quando o banco está acessível |
| `2` | Uso incorreto do comando (padrão do `argparse`) | Não |
| `3` | `recusada`: outra execução detém a trava (RF-15) | Sim |

O veredito `sucesso_parcial` sai com `0` para não fazer um agendador futuro tratar um leiloeiro fora do ar como falha do sistema; o histórico guarda a distinção. 🟡

## 3. Saída no console

Mesmo formato de log das specs, uma linha por evento, prefixada pelo componente:

```
config  | 1 veículo-alvo ativo, 1 leiloeiro ativo, 1 busca
coleta  | Vip Leilões | preparando sessão: cookie de canal obtido
coleta  | Vip Leilões | busca=vip-leiloes:3f9a1c2b7e | pág 1/17 | script | 200 | 1.4s | tentativa 1/3 | ok
…
coleta  | Vip Leilões | busca=vip-leiloes:3f9a1c2b7e | 17 páginas | ok
parser  | Vip Leilões | busca=vip-leiloes:3f9a1c2b7e | 201 lotes | 0 descartados | ok
filtro  | 201 lotes vistos, 0 retirados
filtro  | 3 candidatos | 2 já conhecidos | 1 novo
notif   | digest enviado: 1 lote, 1 mensagem
exec    | sucesso em 1m52s | registro 0b6c…
```

Na semeadura, a linha de filtro diz `busca em semeadura: 3 candidatos registrados como conhecidos, nenhum digest`. 🟡

O mesmo conteúdo vai para `dados/logs/bot-leilao.log`, com rotação de 1 MB e 5 arquivos, já com o filtro de mascaramento de segredos aplicado (roadmap D-26). 🟡
