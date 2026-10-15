# Contrato: linha de comando `analise` (com o roteiro da skill)

> Feature: `006-analisar-lotes`
> Data: 2026-10-15
> Decisões: D-104, D-110, D-112, D-114 a D-117

Todos os subcomandos rodam a partir da raiz do projeto (`--raiz` como nos outros comandos), imprimem **JSON em UTF-8** na saída padrão e terminam com código `0` (ok), `1` (erro com mensagem em `{"erro": "..."}`) ou `3` (varredura em andamento, só nos que escrevem). Logs vão para `dados/logs`, nunca para a saída padrão.

## Leitura (não escrevem)

| Subcomando | Entrada | Saída (campos principais) |
|------------|---------|---------------------------|
| `analise lotes [--numero N]` | — | `lotes`: lista de `{numero, id, titulo, ano, campos: {FIPE, Lance ao entrar, Pátio, Km, Pregão, Documento, Observações, Câmbio, Link, Alvo, Triagem…}, alvo: {id, marca, modelo, ano_min, ano_max, preco_maximo, quilometragem_maxima, criterios: {cambio, aceitar_*}, triagem}}` |
| `analise pagina <numero>` | número do bloco | `{numero, leiloeiro, nivel, pago, custo_estimado_usd, campos: {lance_corrente, lance_inicial, observacoes, patio, cambio, placa_parcial, retirado…}, texto}` (texto limpo, até 8.000 caracteres); falha de acesso: `{"erro": "...", "motivo": "<motivo do cliente>"}` |
| `analise fipe-candidatos --marca M --modelo "termos" --ano A` | marca, termos do modelo, ano de modelo | `{mes_referencia, fonte, candidatas: [{codigo, versao, combustivel, valor}]}` |
| `analise fipe-valor --codigo C --ano A` | código FIPE e ano | `{codigo, versao, valor, mes_referencia, fonte}` |
| `analise custo --lance L [--despesa D] --patio "Cidade - UF" [--documento-uf UF] [--fipe F]` | valores em reais | `{parcelas: {lance, comissao, despesa, despesa_padrao, frete, frete_km, frete_estimado, transferencia, reparos}, total, percentual_fipe, lance_maximo, avisos: [...]}` |

## Escrita (pegam a trava da varredura; recusam com código 3 se ela estiver ocupada)

| Subcomando | Entrada | Efeito |
|------------|---------|--------|
| `analise triar <numero> --veredito aprovado` | — | Linha `- **Triagem (DD/MM/AAAA):** aprovado` antes de `- **Link:**` (substitui a anterior) |
| `analise triar <numero> --veredito a-confirmar --falta "câmbio; lance"` | o que falta | `- **Triagem (…):** a confirmar — câmbio; lance` |
| `analise triar <numero> --veredito reprovado --motivo "câmbio manual" --evidencia "título 'DYN 20M'"` | motivo e evidência obrigatórios | Bloco sai da lista e vai para o fim de `1OUTPUT/lotes-descartados.md` com `- **Descartado em DD/MM/AAAA:** câmbio manual — título 'DYN 20M'` |
| `analise devolver <numero>` | — | Bloco volta de `lotes-descartados.md` para o fim da lista, sem a linha de descarte |
| `analise anotar-custo <numero> --json <arquivo ou ->` | saída do `analise custo` mais a FIPE escolhida (ou as candidatas) | Preenche FIPE, "% da FIPE" do lance ao entrar, Despesas admin. (se vazia), Frete, Valor estimado na garagem; acrescenta "Lance máximo (margem X%)" |

Regras de escrita: relê o arquivo antes de alterar; grava em arquivo temporário e renomeia; nunca altera o comentário `<!-- lote: … -->`, a numeração nem outro bloco; número inexistente é erro.
