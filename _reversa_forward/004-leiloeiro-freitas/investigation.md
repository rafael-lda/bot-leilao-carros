# Investigation: Leiloeiro Freitas

> Feature: `004-leiloeiro-freitas`
> Data: 2026-10-13
> Fontes: prints do Rafael (janela anônima e normal), `openssl s_client`, scripts da página de busca, 9 requisições ao Freitas

## 1. Por que o Freitas "parecia bloqueado"

| Data | O que se viu | Causa |
|------|--------------|-------|
| 2026-10-10 (triagem) | "Acesso Bloqueado" do GoCache, até no `robots.txt`; certificado "incompleto" | Firewall naquele momento; e a cadeia de certificado errada |
| 2026-10-13 (Chrome normal do Rafael) | "Sua conexão não é particular" (`NET::ERR_CERT_AUTHORITY_INVALID`) | Cadeia errada: o servidor envia o intermediário "AlphaSSL CA - SHA256 - G2" para um certificado emitido pelo "GlobalSign GCC R6 AlphaSSL CA 2025" |
| 2026-10-13 (janela anônima) | Site abre | O Chrome às vezes busca sozinho o intermediário certo (endereço no próprio certificado) |
| 2026-10-13 (bot) | `CERTIFICATE_VERIFY_FAILED` sem o intermediário; 200 sem bloqueio com ele | O bot não busca intermediários; com o oficial guardado, a cadeia fecha até a Root R6 do `certifi` |

## 2. Como a busca foi encontrada

A página `/Leiloes/Pesquisar?query=&categoria=1` é uma casca; o script dela chama `$.ajax({url: "/Leiloes/PesquisarLotes", data: pesquisa})` com os campos do formulário, inclusive `Condicao` (`inteiros`, `sinistros e sucatas`, `pequena monta`, `media monta`, `sucatas`) e `TopRows` (12 no site; 200 aceito). A resposta é HTML parcial, anexado à página; o fim é a mensagem "Nenhum lote localizado com os filtros aplicados!".

## 3. Volume (2026-10-13, condição "Inteiros")

- 225 lotes: 220 "FINANCEIRA", 5 sem etiqueta (comitentes de logo 30 e 1162).
- Leilões: 8103 (188 lotes, 14/10, Santa Bárbara d'Oeste-SP), 8112 (16, 16/10, Santo André-SP), 8111 (21, 24/10, em loteamento).
- Estados: 204 "ABERTO PARA LANCES", 21 "EM LOTEAMENTO".
- Preço: 104 com "Maior lance", 96 só com "Lance Inicial" (página 1).
- Alvos atuais: Duster 2014 e Sentra 2013 (fora da faixa); Duster Intense CVT 2024 de financeira a R$ 50.500 (fora da faixa do alvo, 2018–2022).

## 4. Id do lote

O card só tem `leilaoId` e `loteNumero`. O detalhe tem um id interno estável (`var loteId = parseInt('797418')`). Lotes em loteamento aparecem com lote "X" e números 700+, provavelmente provisórios. Decisão D-77: ignorá-los até o loteamento.

## 5. Armadilhas para a lista do onboarding (para o `/reversa-sync`)

- `cadeia_certificado_errada`: o site envia intermediário de outra cadeia. Diagnóstico com `openssl s_client -showcerts`; correção com o intermediário oficial do endereço "CA Issuers" do certificado, nunca desligando a verificação.
- `numero_provisorio`: lotes em montagem com número que vai mudar.
- `tipo_por_lote`: busca que mistura comitentes; o tipo vem de uma etiqueta por lote, não da busca.
