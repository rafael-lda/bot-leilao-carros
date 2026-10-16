- Milan: 
  
  [https://www.milanleiloes.com.br](https://www.milanleiloes.com.br/)

- Copart:
  
   [https://www.copart.com.br](https://www.copart.com.br/)

- Freitas:
  
  [https://www.freitasleiloeiro.com.br](https://www.freitasleiloeiro.com.br/)

- VIP:
  
   [https://www.vipleiloes.com.br/](https://www.vipleiloes.com.br/)

- Claudio Kuss:
  
  [[https://www.claudiokussleiloes.com.br/](https://www.claudiokussleiloes.com.br/))


## A verificar (candidatos, levantados em 16/10/2026)

Fonte: lista oficial de leiloeiros parceiros da Santander Financiamentos (https://www.santander.com.br/hotsite/santanderfinanciamentos/leilao-de-veiculos.html), datas de outubro/2026. Distância até Londrina pelo cálculo da skill (frete estimado a R$ 4,50/km).

O que conferir em cada um: quantos carros de financeira aparecem por evento; se aparecem os modelos-alvo (Kicks, Versa, Sentra, Duster, Fluence, Creta); se o site deixa o robô ler sem bloqueio.

- Loop Leilões (recomendado 1º: pregão quase 2x por semana):

  [https://www.loopleiloes.com.br](https://www.loopleiloes.com.br/)

  Pátio: Mogi das Cruzes-SP, 589 km (frete ~R$ 2.650). 8 pregões em outubro.

- Guariglia (recomendado 2º):

  [https://www.guariglialeiloes.com.br](https://www.guariglialeiloes.com.br/)

  Pátio: Caçapava-SP, 641 km (frete ~R$ 2.880); outro pátio em Candeias-BA (longe). Pregão semanal.

- Depois desses (frete de R$ 4 a 5 mil já pesa na margem):

  - Leilomaster, Goiânia-GO, 896 km: [https://www.leilomaster.com.br](https://www.leilomaster.com.br/)
  - Win Leilões, Goiânia-GO, 896 km (também MT, CE, PE): [https://www.winleiloes.com.br](https://www.winleiloes.com.br/)
  - Bolsa de Leilões, Belo Horizonte-MG, 973 km: [https://www.bolsadeleiloes.com.br](https://www.bolsadeleiloes.com.br/)
  - Pestana, Nova Santa Rita-RS, 1.036 km: [https://www.pestanaleiloes.com.br](https://www.pestanaleiloes.com.br/)
  - Parque dos Leilões, Brasília-DF, 1.085 km: [https://www.parquedosleiloes.com.br](https://www.parquedosleiloes.com.br/)

- Não compensam pela distância: Pacto (AM, PA, CE), Norte Leilões (PA), Rogério Menezes (RJ).

- Já olhado: Sodré Santoro (MS), só 2 veículos de financeira.

Observação: a lista é só do Santander; outros bancos (Itaú, Bradesco, BV, Pan) têm parceiros próprios (o Vip vende para o Banco Pan).


## Outros bancos (levantado em 16/10/2026)

### Bradesco: vitrine oficial (a melhor fonte achada)

[https://vitrinebradesco.com.br](https://vitrinebradesco.com.br/), ligada à página de leilões do banco (https://banco.bradesco/html/classic/produtos-servicos/leiloes/index.shtm). Reúne os veículos do grupo Bradesco de 13 leiloeiros, atualizados várias vezes ao dia. Em 16/10/2026: 100 retomados de financiamento, 119 sinistrados e 4 sucatas. Tem uma API pública (api.vitrinebradesco.com.br), que no futuro poderia virar uma fonte só para o bot; ela bloqueia (429) depois de poucas consultas seguidas.

Leiloeiros da vitrine que ainda não estão no bot (data da última atualização na vitrine):

- Mega Leilões, ativo (16/10): [https://www.megaleiloes.com.br](https://www.megaleiloes.com.br/)
- Pestana, ativo (16/10); também está na lista do Santander: [https://www.leiloes.com.br](https://www.leiloes.com.br/)
- AJ Leilões, ativo (16/10): [https://www.ajleiloes.com.br](https://www.ajleiloes.com.br/)
- Palácio dos Leilões, 30/09: [https://www.palaciodosleiloes.com.br](https://www.palaciodosleiloes.com.br/)
- Sodré Santoro, 06/08: [https://www.sodresantoro.com.br](https://www.sodresantoro.com.br/)
- Guariglia, 14/04 (parado na vitrine; ativo na lista do Santander): [https://www.guariglialeiloes.com.br](https://www.guariglialeiloes.com.br/)
- ZUK, ativo, mas é mais de imóveis: [https://www.zukerman.com.br](https://www.zukerman.com.br/)
- Parados há mais de um ano: Leilão Santos (2025), Favareto (2024).

Também na vitrine e já no bot: Milan, Freitas, Vip e Copart.

Cidades de pátio com veículos na vitrine (a vitrine não diz de qual leiloeiro), com a distância até Londrina:
Curitiba-PR 385 km, Osasco-SP 516 km, Ilhota-SC 599 km (pátio do Vip), Caçapava-SP 641 km, Passo Fundo-RS 770 km, Goiânia-GO 896 km, Betim-MG 941 km; o resto (AM, BA, CE, DF, MA, MT, PA, PE, RO) é longe.

### BV, Itaú e Pan

- BV: não achei página oficial de leilões. Notícias citam Rogério Menezes (RJ), Freitas (2021), Sodré Santoro (2023) e Vardana Leilões (2025).
- Itaú: não achei página oficial de leilões de veículos. Em 2022 o Itaú vendeu retomados num feirão direto, sem anotação de leilão no documento: se voltar a acontecer, é outro canal (carro sem a marca de leilão revende melhor).
- Pan: vende pelo Milan e pelo Vip (já no bot).

### Resumo para decidir a próxima feature

1. Loop Leilões e Guariglia (lista do Santander, pátios em SP a ~600 km).
2. Mega Leilões e Pestana (ativos na vitrine do Bradesco; o Pestana também é parceiro do Santander).
3. Vitrine do Bradesco como fonte única de vários leiloeiros (um adaptador só, em vez de um por leiloeiro).


## Análise dos leiloeiros da vitrine do Bradesco (16/10/2026)

Como foi feita: lista de veículos da vitrine (330 veículos do grupo Bradesco no dia), site de cada leiloeiro aberto pelo mesmo acesso do bot (sem login, sem lance, sem Apify) e distância até Londrina pelo cálculo da skill (frete estimado a R$ 4,50/km).

### Vale uma feature

1. Pestana Leilões: [https://www.leiloes.com.br](https://www.leiloes.com.br/)
   - Pátios: Suzano-SP 577 km (frete ~R$ 2.600), Tijucas-SC 634 km (~R$ 2.850); também Nova Santa Rita-RS 1.036 km, RO e MT.
   - Volume: 56 veículos do Bradesco na vitrine, com Duster ICO TCE 2022/23, Sentra 2.0 SV CVT 2014/15 e Versa 1.6 SL 2016. No site, cada lote de financiamento vem marcado "Retomado".
   - Parceiro do Santander e do Bradesco.
   - Acesso: sem bloqueio; a página já traz os lotes em dados estruturados e há API pública (api.pestanaleiloes.com.br). Leitura por script, de graça.

2. Guariglia: [https://www.guariglialeiloes.com.br](https://www.guariglialeiloes.com.br/)
   - Pátio: Caçapava-SP 641 km (frete ~R$ 2.880).
   - Volume: leilão de veículos em 19/11/2026 (online e presencial, em loteamento); o filtro de modelos do evento lista Creta, Duster, Fluence, Kicks e Versa. Pregão semanal pela agenda do Santander.
   - Acesso: HTML simples, sem bloqueio.
   - Ressalvas: a vitrine parou de atualizá-lo em abril, mas o site está ativo. Falta abrir os lotes para ver quais são de financeira.

### Depende de conferir

3. Sodré Santoro: [https://www.sodresantoro.com.br](https://www.sodresantoro.com.br/)
   - Base em SP; o site tem página de "carros recuperados de financeira" e uma só do Bradesco (no MS havia só 2 de financeira; o volume pode estar em SP).
   - Acesso: os lotes vêm de uma API fora do HTML; há reCAPTCHA (provavelmente só no login). Mais trabalho para o bot.

4. Palácio dos Leilões: [https://www.palaciodosleiloes.com.br](https://www.palaciodosleiloes.com.br/)
   - A página de eventos cita muitos bancos (Pan, Bradesco, BMG, Banco do Brasil, BV, Honda): provavelmente o maior volume de financeira entre os novos.
   - Contra: Belo Horizonte/Contagem-MG, ~960 km (frete ~R$ 4.300). Site aberto.

### Não compensa agora

- Mega Leilões: quase tudo judicial e imóvel; os bancos aparecem só nos imóveis; nenhum carro do Bradesco na vitrine.
- AJ Leilões: 1 veículo na vitrine (caminhão em Cuiabá-MT); site em JavaScript.
- ZUK: imóveis; o link de veículos cai na página de imóveis.
- Leilão Santos: vitrine parada desde 2025; busca de veículos quase vazia.
- Favareto: vitrine parada desde 2024; reCAPTCHA e nenhum lote visível.

### Os que já estão no bot, na vitrine do dia

Vip 150 veículos (Creta 2021, Sentra; pátios BA, SC, PE, MA); Copart 105 (maioria sinistro ou sucata); Freitas 18; Milan 0.

Loop Leilões (lista do Santander, fora da vitrine): a agenda é carregada por JavaScript; falta investigar para ver os lotes.

### Sugestão de ordem para a próxima feature

Pestana, depois Guariglia (pátios a ~600 km, modelos-alvo presentes, leitura gratuita). Sodré e Palácio só depois de conferir o volume.
