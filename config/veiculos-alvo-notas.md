# Veículos-alvo — notas de decisão

Companheiro do `veiculos-alvo.yaml`. O YAML é **o que o bot obedece**; aqui fica **o porquê** e o que
olhar na hora de dar lance. Nada neste arquivo é lido por código.

Quando uma nota virar regra que o bot deve seguir (ex.: "nunca Oroch"), ela **migra para o YAML** —
senão viram duas fontes de verdade e o código enxerga só uma.

Marcação: **[dado]** = verificado na fonte · **[aval]** = avaliação, pode estar errada.

---

## Critérios gerais

### Conforto (hérnia de disco)

O que manda, em ordem de peso **[aval]**:

| | Por quê |
|---|---|
| 1. Entre-eixos longo | Curto, o eixo traseiro bate no buraco logo depois do dianteiro e o carro cabeceia |
| 2. Curso e calibração da suspensão | Macia e de curso longo absorve; firme transmite |
| 3. Peso | Carro leve é jogado pelo buraco, pesado absorve |
| 4. Perfil do pneu | Ajuda só em impacto pequeno e seco. **Não salva o resto** |

Referência de calibragem: o CrossFox roda 205/60 R16 (pneu alto) e mesmo assim balança — entre-eixos
de ~2.465 mm e suspensão firme de hatch levantado anulam o pneu. Pneu alto sozinho não resolve.

**Regra prática:** entre duas versões do mesmo carro, **a mais barata costuma andar melhor** — roda 16
com pneu de perfil alto em vez de roda 17. Confira a roda na ficha do lote.

**Entrada e saída** também contam: teto caindo atrás obriga a curvar para entrar, e é esse movimento
que dói. Carroceria mais quadrada > carroceria estilo cupê.

### Câmbio

Todos os alvos são automáticos, mas há duas tecnologias e elas não envelhecem igual **[aval]**:

- **Convencional (conversor de torque)** — perdoa manutenção atrasada e o conserto é mais barato.
- **CVT** — confiável quando o fluido é trocado (~40 a 60 mil km), e **mais suave**, o que ajuda a
  coluna: não dá trancos de troca de marcha.

O risco do CVT em leilão não é a tecnologia, é que **num recuperado de financiamento não dá para
verificar o histórico de fluido** — o dono parou de pagar a parcela, pode ter parado a manutenção
junto. Desgaste de CVT não aparece com o carro parado. Troca custa R$ 15 a 25 mil **[aval]**.

Não é motivo para descartar CVT. É motivo para, entre dois lotes equivalentes, preferir o convencional.

### Custo: o martelo não é o preço

Em cima do lance entram **[dado]** 5% de comissão (cláusula 13 do Termo de Adesão do Vip) e
**[aval]** ~R$ 7.000 de custos que **não escalam com o preço do carro**: taxa administrativa
(~R$ 1.900, confirmar na página do lote — não está no Termo), guincho, transferência, laudo e
revisão de entrada (pneus, bateria, fluidos).

**Martelo a 70% da FIPE → custo final ~82% da FIPE.**

Como os R$ 7.000 são fixos, **punem mais o carro barato**. No mesmo martelo de 70%:

| Alvo | Custo final |
|---|---|
| Duster | 81,7% |
| Kicks | 82,1% |
| Creta | 82,3% |
| Sentra | 83,1% |
| Fluence | 83,9% |
| Versa | **84,7%** |

Revenda de carro com passagem por leilão fica em 85 a 90% da FIPE **[aval]**. Consequência prática:
**entre dois lotes no mesmo percentual de martelo, o carro mais caro deixa mais margem.**

---

## Por alvo

### Hyundai Creta (2017–2018) — o melhor dos novos

- **Prefira:** Attitude ou Pulse **1.6**, roda 16 (205/65).
- **Por quê:** câmbio **automático convencional de 6 marchas**, ~1.300 kg (o mais pesado da lista
  nova) e suspensão recalibrada pela Hyundai para estrada brasileira. Melhor revenda do grupo.
- **Cuidado:** Prestige e Sport são **2.0** e rodam 17 — andam mais firmes, e o teto do YAML não
  cobre o preço delas. O bot casa qualquer Creta, inclusive essas.

### Nissan Kicks (2018–2019) — o de estudo

- **Prefira:** versão **S**, roda 16 (205/60).
- **Contra a Creta:** ~150 kg mais leve, acerto mais firme, teto caindo atrás (mais difícil de entrar)
  e **CVT** em vez de convencional. Revenda puxada para baixo pelo volume de ex-locadora no mercado.
- **Mas:** é muito melhor que o CrossFox (155 mm a mais de entre-eixos, mais peso, suspensão de SUV).
  Resolve. A Creta resolve melhor.
- **Cuidado:** só 1.6 CVT nesta faixa. O 1.0 turbo é a geração 2021+, fora do alvo.
- **Por que manter no alvo:** aparece mais em leilão que a Creta, pelo volume de frota. Mais chances
  de observar.

### Renault Duster (2018–2022) — o melhor para a coluna

- **Por quê:** maior entre-eixos (~2.673 mm), suspensão de curso longo feita para estrada ruim,
  215/65 R16. É o mais confortável dos alvos.
- **Cuidado:** o bot casa **"DUSTER OROCH"** (picape) e também os manuais e o 1.3 turbo — descarte à mão.
- **Corte de ano:** 2018 é o primeiro ano do 1.6 SCe CVT. Em 2017 os automáticos eram 2.0, sem CVT.

### Nissan Sentra (2014–2017)

- **Por quê:** maior entre-eixos entre os sedãs (~2.700 mm), suspensão macia e banco traseiro grande.
  É o melhor dos sedãs para a coluna **[aval]**.
- **Contra:** sedã baixo — entrada e saída piores que as dos SUVs. CVT.

### Nissan Versa (2016–2019)

- **Atenção:** é o **pior alvo da lista para lucro** — custo final de 84,7% da FIPE no martelo de 70%,
  porque os R$ 7.000 fixos pesam muito num carro de FIPE baixa.
- Espaçoso e de suspensão macia para a categoria, mas sedã baixo. CVT.

### Renault Fluence (2010–2017)

- **Prefira:** 2.0 Dynamique Plus ou 2.0 Privilège — **são as únicas automáticas**.
- **Cuidado:** o bot casa qualquer Fluence, incluindo Expression 1.6 e Dynamique **manuais** e o
  GT Line. Descarte à mão.
- **Contra:** revenda fraca para sedã Renault. Confortável, mas difícil de girar.

---

## Antes de dar lance

1. Confirmar **câmbio automático** na página do lote (o filtro do site é ignorado pelo servidor).
2. Confirmar **roda 16 ou 17** e a versão — muda conforto e preço.
3. Confirmar a **taxa administrativa** do lote.
4. Calcular o custo final, não o martelo: lance + 5% + ~R$ 7.000.
5. Comparar com a FIPE **do ano e da versão do lote**, não com o teto do YAML (o teto é nivelado
   pela versão mais cara do ano mais novo da faixa).

## Pendente de validação

**[aval]** Toda a análise de conforto é por ficha técnica e reputação, não por teste. Antes de
comprar, sentar e dirigir uma Creta, um Kicks e um Duster numa loja de seminovos, 15 minutos em rua
ruim. É a única forma de saber o que a sua coluna aceita.
