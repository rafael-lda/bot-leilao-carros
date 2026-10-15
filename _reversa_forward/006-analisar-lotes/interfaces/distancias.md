# Contrato: distâncias (Nominatim e OSRM)

> Feature: `006-analisar-lotes`
> Data: 2026-10-15
> Decisão: D-115

## 1. Ordem

1. Tabela `distancias` do `config/custos.yaml` (chave "Cidade - UF", sem acento e em minúsculas na comparação): vence sempre, é a correção do Rafael.
2. Cache `dados/distancias.json` (mesma chave).
3. Consulta externa abaixo, gravada no cache.
4. Falha, ou pátio só com UF: `{"frete": null, "aviso": "frete a confirmar: distância de <pátio> não encontrada"}`.

## 2. Geocodificação: Nominatim (OpenStreetMap)

`GET https://nominatim.openstreetmap.org/search?q=<Cidade>,<UF>,Brasil&format=json&limit=1`, com `User-Agent` que identifica o bot (política de uso: no máximo 1 consulta por segundo, sem uso em massa). Resposta: `[{"lat": "-23.31", "lon": "-51.16", …}]`. A origem (Londrina, PR) também vem daqui na primeira vez e fica no cache.

## 3. Rota: OSRM

`GET https://router.project-osrm.org/route/v1/driving/<lon_origem>,<lat_origem>;<lon_destino>,<lat_destino>?overview=false`. Resposta: `{"routes": [{"distance": 386123.4, …}]}` (metros). Verificado em 2026-10-15: Londrina → Curitiba = 386 km.

## 4. Regras

- Uma consulta por cidade, para sempre (cache); o servidor público do OSRM é de demonstração, sem garantia.
- Timeout de 20 s; sem nova tentativa (a falha vira "a confirmar").
- Distância em km inteiros, ida (frete = km × R$/km do `custos.yaml`).
