"""Análise dos lotes da lista de monitoramento: base da skill `analisar-lotes` (feature 006).

O agente decide o veredito de cada lote; este pacote faz o que não pode errar: ler a lista e os critérios, abrir o
lote pelo acesso do bot, consultar a FIPE e as distâncias, calcular o custo na garagem e escrever na lista.
"""
