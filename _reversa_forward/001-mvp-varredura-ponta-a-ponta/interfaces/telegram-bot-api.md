# Interface: Telegram Bot API, `sendMessage`

> Tipo: HTTP, **consumido** pelo `notificador-telegram`
> Fonte: documentação pública da Bot API; parâmetros de comportamento vêm de `_reversa_sdd/sdd/notificador-telegram.md`
> Confidência: 🟢 documentado ou decidido em spec, 🟡 inferido

## 1. Configuração

| Variável no `.env` | Conteúdo | Validação na partida (antes de qualquer rede) |
|--------------------|----------|-----------------------------------------------|
| `TELEGRAM_BOT_TOKEN` | Token emitido pelo @BotFather, formato `<número>:<texto>` | Presente, não vazio, casa com `^\d+:[A-Za-z0-9_-]{30,}$` |
| `TELEGRAM_CHAT_ID` | Id da conversa do Rafael com o bot (inteiro, pode ser negativo em grupo) | Presente, inteiro |

O token **nunca** aparece em log, mensagem de erro ou rastreamento de exceção (RN-08). Como ele faz parte da URL, o filtro de mascaramento do log (roadmap D-26) é obrigatório, e não opcional. 🟢

## 2. Requisição

```
POST https://api.telegram.org/bot<TOKEN>/sendMessage
Content-Type: application/json

{
  "chat_id": <TELEGRAM_CHAT_ID>,
  "text": "<mensagem em HTML restrito>",
  "parse_mode": "HTML",
  "link_preview_options": { "is_disabled": true }
}
```

| Campo | Decisão | Confidência |
|-------|---------|-------------|
| `parse_mode: HTML` | Só `<`, `>` e `&` precisam de escape em texto vindo do leiloeiro (RF-10 do `notificador-telegram`; roadmap D-05) | 🟢 |
| `link_preview_options.is_disabled` | Sem prévia de página: mantém cada lote em até 3 linhas (RNF-04 do `notificador-telegram`). O link continua clicável, porque a URL em texto puro é reconhecida pelo cliente | 🟡 |
| Negrito no cabeçalho | `<b>…</b>` apenas no cabeçalho do digest e do alerta | 🟡 |

## 3. Formato das mensagens

Digest (RF-01 a RF-03 e RF-11 do `notificador-telegram`):

```
<b>Varredura de 05/10/2026 08:03 — 2 lotes novos</b>

1. Nissan Sentra 20S Flex — 2013
   R$ 12.500 — Vip Leilões — 228.227 km
   https://www.vipleiloes.com.br/evento/anuncio/nissan-sentra-20s-flex-310800

2. Toyota Corolla XEi — 2018
   Preço a confirmar — Vip Leilões
   https://www.vipleiloes.com.br/evento/anuncio/...
```

- O ano exibido é o **ano de modelo** (RN-02).
- O preço exibido é o lance corrente, ou o inicial sem lance (RN-03), sem centavos quando inteiros.
- A quilometragem entra na segunda linha quando conhecida: custa poucos caracteres e é critério da busca (RF-16). 🟡

Alerta operacional (RF-08 do `notificador-telegram`; RF-11 da feature), sempre em mensagem separada:

```
<b>Alerta do sistema — 05/10/2026 08:03</b>

Vip Leilões: o parser não extraiu nenhum lote de uma página com conteúdo (148 KB).
O site provavelmente mudou de layout e este leiloeiro está sem cobertura.
```

## 4. Resposta e erros

Sucesso: `200` com `{"ok": true, "result": {"message_id": …}}`. Só isso conta como confirmação (RNF-02 do `notificador-telegram`). 🟢

| Resposta | Significado | Tratamento | Retry |
|----------|-------------|------------|-------|
| `200`, `ok: true` | Entregue | Confirma o bloco | — |
| `400` | `chat not found`, ou `can't parse entities` (escape falhou) | Falha definitiva do envio, com a `description` da API no log (EC-03) | Não |
| `401` | Token inválido ou revogado | Falha definitiva, mensagem orientando renovar o token (EC-02) | Não |
| `403` | Bot bloqueado pelo usuário | Falha definitiva, mensagem orientando desbloquear o bot | Não |
| `429` | Limite de taxa | Espera `parameters.retry_after` segundos, até 60 s, e tenta de novo (EC-05) | Sim |
| `5xx`, timeout de 20 s, erro de conexão | Indisponibilidade | Espera crescente de 2 s e 4 s (EC-01) | Sim, até 3 tentativas |

## 5. Tamanho e divisão

- Limite da plataforma: 4096 caracteres por mensagem, após a interpretação do HTML. O notificador usa **3800** como limite próprio, deixando margem para entidades. 🟡
- A divisão acontece entre itens, nunca dentro de um item (RF-06). O cabeçalho vai só na primeira mensagem; as seguintes começam com `(continuação 2/3)`. 🟡
- Espera de 1 s entre blocos do mesmo digest, abaixo do ritmo que dispara `429` em conversa privada. 🟡
- A confirmação ao `motor-filtros` só ocorre depois do aceite do **último** bloco. Falha no meio não confirma nada, e os lotes voltam na execução seguinte, com duplicação parcial aceita (EC-07). 🟢

## 6. Idempotência

`sendMessage` não é idempotente: repetir após timeout pode entregar duas vezes. A duplicação eventual é o erro preferido à perda, como decidido no `motor-filtros` (EC-04). 🟢
