# Investigação: skill `analisar-lotes`

> Feature: `006-analisar-lotes`
> Data: 2026-10-15

## 1. O que cada leiloeiro entrega sobre um lote (verificado em 2026-10-15)

| Leiloeiro | Como o bot lê o lote | O que vem | Câmbio |
|-----------|----------------------|-----------|--------|
| Vip | `GET` da página do anúncio (link do bloco): abre para o bot, status 200 | Ficha: ano, KM, cor, combustível, **Câmbio**, chave, direção, observações ("IPVA 2026 PAGO / DOC EMITIDO EM SC"), local do lote | Sim ("Câmbio Automático") |
| Claudio Kuss | Detalhe JSON do bot (`json_lance_info_lote.php`, `op=D`) | `descLote`, `tblInformacoes` (ex.: "SINISTRADO - NOS DOCUMENTOS CONSTA RECUPERADO DE SINISTRO"), `tblDespAdm`, `retirado`, `tblTxtInfo` | Só pelo título ("DYN 20A" / "DYN 20M", "CVT") |
| Copart | Busca JSON com `query=<número do lote>`: 1 resultado (lote 1000219, Duster) | Os mesmos campos da varredura (dano, monta, documento, motor, comitente, FIPE, pátio, foto) | Não informado em campo nenhum |
| Copart | Página `/public/data/lotdetails/solr/<lote>` | **Bloqueada** pelo Imperva (desafio com status 200) | — |
| Freitas | `GET` do detalhe (`LoteDetalhes`) | Pátio, despesas, selos, checklist de vistoria (a palavra "CAMBIO" aparece como item, sem valor) | Só pelo título |
| Milan | Página do lote pelo Apify (feature 005) | Lance, estado, final da placa, km, **câmbio** | Sim (catálogo e página) |

Conclusão: o câmbio vem estruturado no Vip e no Milan; no Kuss e no Freitas, só no título; na Copart, em lugar nenhum (fica "a confirmar", salvo título com AT, AUT, CVT).

## 2. FIPE

| Verificação | Resultado |
|-------------|-----------|
| parallelum v1 e v2 | No ar; mês de referência outubro/2026 (código 338) |
| Site oficial (`veiculos.fipe.org.br/api/veiculos/ConsultarTabelaDeReferencia`) | Outubro/2026 (código 338) |
| Valor do Versa SL 1.6 Aut. 2019 (023140-1, flex) | **R$ 62.464,00 nas duas fontes** |
| Limite da parallelum | 500 consultas por dia, sem token (`x-ratelimit-limit: 500`) |

Custo por análise: ~3 a 6 consultas (marca, modelos, anos, valor); com cache por mês, a lista inteira cabe com folga no limite.

## 3. Distância

| Verificação | Resultado |
|-------------|-----------|
| Nominatim (OSM) `Londrina,PR,Brasil` | lat -23.311, lon -51.160 |
| OSRM Londrina → Curitiba | 386 km (a memória do projeto dizia ~380) |

Alternativas: tabela manual (passo manual recorrente, contra a preferência do Rafael); linha reta (subestima rota). Escolha: consulta uma vez por cidade, com cache, e tabela no `custos.yaml` só para correção.

## 4. `.gitignore`

O instalador do Reversa ignora `.claude/skills/` e `.agents/skills/` inteiros. Teste num repositório vazio: com o diretório ignorado, a exceção `!…/analisar-lotes/` não tem efeito (regra do git: não dá para reincluir arquivo de diretório excluído); com `…/skills/*` e a exceção, só a pasta da skill entra. As skills do Reversa continuam fora.

## 5. Lista atual (2026-10-15) como casos de avaliação

14 lotes, base das avaliações do `skill-creator`:

| Lote | Título | Esperado |
|------|--------|----------|
| 1 | NISSAN/KICKS S DRCT CVT — 2019 (Kuss) | Câmbio ok (CVT); sem observação de problema → aprovado (ou "a confirmar: lance", sem preço) |
| 2, 14 | IMP RENAULT/FLUENCE DYN 20M — 2015 (Kuss) | Reprovado: câmbio manual ("20M") e "MECÂNICA COM PROBLEMAS" |
| 3, 13 | IMP RENAULT/FLUENCE DYN 20A — 2013 (Kuss) | Reprovado: sinistro |
| 4, 7, 9 | RENAULT DUSTER 1.6 16V SCE (Copart) | "a confirmar: câmbio" (1.6 SCe pode ser manual ou CVT); "PEQUENOS AMASSADOS" aceito |
| 5, 8 | NISSAN KICKS 1.6 16V — 2019 (Copart) | "a confirmar: câmbio"; pequenos amassados aceitos |
| 6 | NISSAN KICKS 1.6 16V — 2019 (Copart, NÃO AVALIÁVEL) | "a confirmar: câmbio e estado" |
| 10 | NISSAN VERSA 1.6 16V — 2017 (Copart, TRASEIRO) | "a confirmar": câmbio; avaria traseira não é "pequena" (o agente explica) |
| 11 | RENAULT DUSTER 2.0 16V — 2019 (Copart) | Fora da preferência do alvo (2.0 não é 1.6 CVT) → reprovado pelo texto `triagem` |
| 12 | NISSAN VERSA 1.6 16V — 2019 (Copart, NÃO AVALIÁVEL) | "a confirmar" |

Os resultados esperados são hipóteses para as avaliações; o `skill-creator` compara e o Rafael confirma na primeira execução real.

## 6. Fontes

- Testes de acesso e de API em 2026-10-15 (Vip, Copart, parallelum, site da FIPE, Nominatim, OSRM)
- Fixtures das features 002 a 005 em `tests/fixtures/`
- `1OUTPUT/lotes-a-monitorar.md` e `1OUTPUT/comentarios-lotes-a-monitorar.md` (2026-10-15)
- [Política de uso do Nominatim](https://operations.osmfoundation.org/policies/nominatim/)
- [OSRM](https://project-osrm.org/)
- [API FIPE (parallelum)](https://deividfortuna.github.io/fipe/)
