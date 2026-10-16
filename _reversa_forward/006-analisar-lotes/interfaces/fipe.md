# Contrato: FIPE (parallelum v2 e site oficial)

> Feature: `006-analisar-lotes`
> Data: 2026-10-15
> Decisão: D-114

## 1. Fonte principal: parallelum v2

Base `https://parallelum.com.br/fipe/api/v2`, sem token. **Limite: 500 consultas por dia** (cabeçalhos `x-ratelimit-limit: 500`, `x-ratelimit-remaining`, `x-ratelimit-reset` em segundos; verificado em 2026-10-15).

| Uso | Requisição | Resposta (exemplo) |
|-----|-----------|--------------------|
| Mês de referência | `GET /references` | `[{"code": "338", "month": "outubro/2026"}, …]` |
| Marcas | `GET /cars/brands` | `[{"code": "23", "name": "Nissan"}, …]` |
| Modelos da marca | `GET /cars/brands/{marca}/models` | `[{"code": "…", "name": "VERSA SL 1.6 16V FlexStart 4p Aut."}, …]` |
| Anos de um código FIPE | `GET /cars/{codigoFipe}/years` | `[{"code": "2019-5", "name": "2019 Flex"}, …]` |
| Valor | `GET /cars/{codigoFipe}/years/{ano-combustivel}` | `{"price": "R$ 62.464,00", "model": "VERSA SL 1.6 16V FlexStart 4p Aut.", "modelYear": 2019, "fuel": "Flex", "codeFipe": "023140-1", "referenceMonth": "outubro de 2026"}` |
| Erro | — | `{"error": "veículo não encontrado para a referência informada"}` |

## 2. Reserva: site oficial

Base `https://veiculos.fipe.org.br/api/veiculos`, `POST` com formulário (`application/x-www-form-urlencoded`) e `Referer: https://veiculos.fipe.org.br/`. Endpoint não documentado (é o que o site usa).

| Uso | Requisição | Resposta (exemplo) |
|-----|-----------|--------------------|
| Mês de referência | `POST /ConsultarTabelaDeReferencia` | `[{"Codigo": 338, "Mes": "outubro/2026 "}, …]` |
| Valor por código | `POST /ConsultarValorComTodosParametros` com `codigoTabelaReferencia=338&codigoTipoVeiculo=1&anoModelo=2019&codigoTipoCombustivel=5&tipoVehiculo=carro&modeloCodigoExterno=023140-1&tipoConsulta=codigo` | `{"Valor": "R$ 62.464,00", "Modelo": "VERSA SL 1.6 16V FlexStart 4p Aut.", "CodigoFipe": "023140-1", "MesReferencia": "outubro de 2026 "}` |
| Versões de um ano (D-123) | `POST /ConsultarModelosAtravesDoAno` com `codigoTabelaReferencia=338&codigoTipoVeiculo=1&codigoMarca=43&codigoModelo=&ano=2019-5&codigoTipoCombustivel=5&anoModelo=2019` | `[{"Label": "VERSA SL 1.6 16V FlexStart 4p Aut.", "Value": "7628"}, …]` (só as versões que existem naquele ano e combustível) |
| Valor por versão (D-123) | `POST /ConsultarValorComTodosParametros` com `codigoMarca`, `codigoModelo`, `anoModelo`, `codigoTipoCombustivel`, `tipoVehiculo=carro&tipoConsulta=tradicional` | mesmo formato do valor por código |
| Erro | — | `{"codigo": "0", "erro": "nadaencontrado"}` |

**Limites (verificado em 2026-10-16):** a parallelum conta cada pedido HTTP (500 em 24 h corridas; no limite responde 429 com `retry-after` de horas e sugere um token da fipe.api.br). O site oficial responde 429 a rajadas: os pedidos são espaçados de 1 s e repetidos em 5 s e 15 s. Custo de uma busca de versões: marcas (1, guardadas no mês) + 4 combustíveis + 1 por versão que casa.

Combustível: 1 gasolina, 2 álcool, 3 diesel, 5 flex (o ano da parallelum traz o mesmo código: `2019-5`).

## 3. Regras

- Mesmo valor nas duas fontes para o mesmo código, ano e mês (verificado: Versa SL 1.6 Aut. 2019 = R$ 62.464,00, out/2026).
- Ordem: cache → parallelum → site oficial. Falha nas duas: `{"erro": "FIPE indisponível"}`; a triagem segue.
- Cache em `dados/fipe-cache.json`, por mês de referência (mudou o mês, o cache daquele mês não vale).
- Toda resposta registra `fonte` (`parallelum` ou `fipe.org.br`), código e mês.
- Timeout de 20 s; uma nova tentativa só em erro de rede.
