# Requirements: Leiloeiro Copart

> Identificador: `003-leiloeiro-copart`
> Data: `2026-10-11`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Acrescenta o terceiro leiloeiro ao bot: **Copart Brasil**, o de maior volume entre os cinco da lista do Rafael. A cada varredura o bot lê todos os lotes com condição **FINANCIAMENTO** (1.506 em 2026-10-11, somando carros, SUVs, picapes e motos), aplica os mesmos veículos-alvo e avisa no mesmo resumo do Telegram, nos relatórios e na lista de monitoramento.

Junto, a feature acrescenta o **pátio** (onde o carro está) a todos os leiloeiros: o Rafael mora em Londrina-PR, e 80% dos carros de financiamento da Copart estão no Nordeste e no Centro-Oeste. Sem o pátio no aviso, um lote bom no papel pode ser inviável pelo frete.

## 2. Contexto a partir do legado

Projeto greenfield com as features 001 e 002 entregues. As fontes abaixo cumprem o papel de extração.

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/prd.md#4` | Lista-alvo de leiloeiros (Freitas, Vip, Claudio Kuss, Copart, Milan); meta de ≥ 5 | 🟢 |
| `_reversa_sdd/sdd/cadastro-leiloeiros.md#6` (v1.3) | Busca declarada como filtros chave-valor opacos; diretriz de busca ampla (§6.1.1) | 🟢 |
| `_reversa_sdd/sdd/coletor-lotes.md#6` (v1.1) | Adaptador por leiloeiro (RF-12), paginação com teto (RF-14), 5 s por host, bloqueio distinto de falha de rede | 🟢 |
| `_reversa_sdd/sdd/parser-lotes.md#6` (v1.3) | Parser por leiloeiro; id canônico único (RF-06); sinônimos de marca (RF-12); busca vazia legítima (EC-15) | 🟢 |
| `_reversa_sdd/addenda/001-mvp-varredura-ponta-a-ponta.md` | Semeadura por busca, km opcional, retirados, relatório e lista de monitoramento | 🟢 |
| `_reversa_sdd/addenda/002-leiloeiro-claudio-kuss.md` (com atualização de 2026-10-11) | Anotações por página, teto de páginas por adaptador, enriquecimento dos novos, observações no aviso (4ª linha), semeados nos documentos | 🟢 |
| `_reversa_forward/backlog.md#9` | Escada de acesso (script → Apify datacenter → residencial → IP fixo), decidida pelo Rafael em 2026-10-11 | 🟢 |
| `_reversa_forward/backlog.md#8` | Distância do pátio como fator de custo | 🟢 |
| `_reversa_forward/003-leiloeiro-copart/amostras/` | Respostas reais da busca JSON da Copart, 2026-10-11 | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Rafael, comprador em Londrina | Ver o maior estoque de carros de financiamento sem visitar a Copart | O resumo das 08:00 traz um Versa 2019 da Copart, com o pátio "CAMPO GRANDE - MS" e o FIPE ao lado do lance 🟢 |
| Rafael, comprador | Descartar logo o que está longe demais | Todo aviso, de qualquer leiloeiro, mostra onde o carro está 🟢 |
| Rafael, operador | Não ser enganado por silêncio | Se a Copart passar a barrar o robô, chega um alerta identificando a Copart, e o Vip e o Kuss seguem normalmente 🟢 |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** A busca da Copart é ampla: só `condicao: FINANCIAMENTO`, sem marca, modelo nem categoria; o recorte é feito pelos veículos-alvo (`cadastro-leiloeiros.md#6.1.1`). 🟢
   - Origem: diretriz de busca ampla; filtro nativo da Copart verificado em 2026-10-11
   - Tipo: nova
2. **RN-02:** Lotes da busca de condição FINANCIAMENTO recebem `tipo_leilao = financiamento`, por herança da busca (D-15 da 001, D-39 da 002). 🟢
   - Tipo: nova
3. **RN-03:** O identificador canônico é o número do lote da Copart (`ln`), global no site; o link é `https://www.copart.com.br/lotDetail/<ln>`. 🟢
   - Origem: CSV exportado e JSON da busca (2026-10-11)
   - Tipo: nova
4. **RN-04:** Todo lote, de qualquer leiloeiro, passa a ter o **pátio** (onde o veículo está): Copart "cidade - UF" (campo do JSON), Vip a UF do card ("Local"), Claudio Kuss o local do evento (Curitiba-PR). Pátio ausente não elimina o lote. 🟢
   - Origem: decisão do Rafael, 2026-10-11
   - Tipo: nova (vale para os três leiloeiros)
5. **RN-05:** O pátio é **mostrado**, não filtrado: nenhum lote é descartado por distância nesta feature. O filtro ou o custo de frete fica para a skill `analisar-lotes` ou feature futura (backlog itens 8 e ★). 🟢
   - Origem: decisão do Rafael, 2026-10-11
   - Tipo: nova
6. **RN-06:** Lote da Copart ainda "Aguardando Classificação" (sem data de leilão, sem FIPE e sem lance; 656 de 692 carros de financiamento em 2026-10-11) é **avisado já**, como "preço a confirmar" e com a data do leilão "a definir", pela regra existente de que preço ausente não elimina. O aviso é único: quando a Copart classificar o lote e marcar a data, não há novo aviso; o acompanhamento é feito pela lista de monitoramento. Mesma decisão da RN-07 da feature 002 (Kuss). 🟢
   - Origem: decisão do Rafael na sessão de esclarecimento de 2026-10-11
   - Tipo: nova
7. **RN-07:** Acesso pelo degrau mais simples da escada do backlog (item 9): requisição comum, sem login, sem Apify. Se a Copart bloquear, o bot registra bloqueio e alerta (comportamento existente desde a 001); o degrau Apify com troca automática fica para a feature do Milan, que precisa dele de qualquer forma. 🟢
   - Origem: decisão do Rafael, 2026-10-11
   - Tipo: nova
8. **RN-08:** O sistema continua sem dar lances, sem login e sem usar a área de membro (`/data/...`, `/client/...`). 🟢
   - Tipo: mantida

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve aceitar a Copart em `config/leiloeiros.yaml` como leiloeiro público, nível `script`, com busca declarada por filtros chave-valor que correspondem aos filtros do site (ex.: `condicao: FINANCIAMENTO`) | Must | Com o bloco ativo, a configuração carrega; chave de filtro desconhecida aborta antes da rede citando a Copart | 🟢 |
| RF-02 | O sistema deve coletar todas as páginas da busca, conferindo o total lido com o total informado pela Copart | Must | Uma busca com 1.506 resultados resulta em 1.506 lotes lidos; divergência gera aviso em log | 🟢 |
| RF-03 | O sistema deve converter cada lote em lote normalizado: id pelo número do lote, marca e modelo (com a tabela de sinônimos), ano de modelo e de fabricação, lance atual, link da página do lote, tipo de leilão herdado e pátio | Must | O lote 1176233 (Versa 2019, Campo Grande-MS) produz marca `nissan`, modelo `versa`, ano de modelo 2019, pátio "CAMPO GRANDE - MS" e link `…/lotDetail/1176233` | 🟢 |
| RF-04 | O sistema deve mostrar o **pátio** de todo lote, de qualquer leiloeiro, no aviso do Telegram, no relatório e na lista de monitoramento | Must | Um aviso do Vip mostra "Pátio: SC"; um do Kuss, "Pátio: Curitiba-PR"; um da Copart, "Pátio: CAMPO GRANDE - MS" | 🟢 |
| RF-05 | O sistema deve incluir, para os lotes da Copart, as informações de estado que o site oferece: descrição do dano, tipo de monta, documento, condição de funcionamento, valor FIPE e data do leilão, quando informados | Must | O bloco do lote no relatório traz "FIPE: R$ 52.784", "Leilão: 13/10 20:00", "Monta: Não Aplicável", "Documento: NORMAL", "Motor dá partida e engrena" | 🟢 |
| RF-06 | O sistema deve tratar zero resultados como busca vazia legítima, e resposta fora do formato como quebra com alerta identificando a Copart | Must | Com o JSON alterado, chega alerta citando a Copart; com zero resultados, nenhum alerta | 🟢 |
| RF-07 | O sistema deve distinguir bloqueio da Copart (403/desafio do Imperva) de falha de rede, registrando e alertando, sem impedir os outros leiloeiros | Must | Com a Copart respondendo desafio, os lotes do Vip e do Kuss chegam e a execução fica como sucesso parcial com alerta da Copart | 🟢 |
| RF-08 | O sistema deve aplicar à Copart a semeadura, a deduplicação, o relatório e a lista de monitoramento existentes, incluindo os semeados nos documentos (E001 da 002) | Must | A primeira varredura com a Copart ativa não envia aviso dos lotes dela, mas os lista no relatório e na lista marcados "por semeadura" | 🟢 |
| RF-09 | O sistema deve manter a varredura completa (Vip, Kuss e Copart) abaixo de 10 minutos | Should | Medido no dry-run real do plano | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Varredura completa abaixo de 10 minutos | Copart: 1.506 lotes a 100 por página ≈ 16 requisições a 5 s ≈ 1,5 min; Kuss ≈ 3,5 min; Vip ≈ 1,5 a 2,5 min | 🟡 |
| Conduta de coleta | 5 s entre requisições ao mesmo host; `User-Agent` de navegador (D-30 da 001); só endpoints públicos de busca, nunca a área de membro | `coletor-lotes.md` RNF-02; backlog item 9 | 🟢 |
| Custo | Nível `script`, sem serviço pago | Busca JSON respondeu sem desafio em 9 requisições em 2026-10-11 | 🟢 |
| Manutenibilidade | Adaptador e parser da Copart em arquivos próprios; o campo de pátio entra no núcleo de forma genérica | `parser-lotes.md` RNF-02 | 🟢 |
| Qualidade | Testes sem rede, com fixtures reais do JSON da Copart | D-27 da 001 | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Lotes de financiamento da Copart entram na varredura
  Dado a Copart ativa no cadastro, com a busca de condição FINANCIAMENTO
  Quando a varredura é executada
  Então todas as páginas da busca são lidas
  E o total lido confere com o total informado pela Copart

Cenário: Lote da Copart que casa com um alvo é avisado com pátio e FIPE
  Dado uma busca da Copart já semeada
  E um lote novo NISSAN VERSA, ano de modelo 2019, pátio "CAMPO GRANDE - MS", FIPE R$ 62.000 e lance de R$ 25.000
  E o alvo Nissan Versa 2016–2019 com teto de R$ 43.700
  Quando a varredura é executada
  Então o resumo no Telegram traz o lote, identificado como Copart, com ano 2019, o pátio e o link do lote

Cenário: Todo aviso mostra o pátio
  Dado lotes novos do Vip, do Claudio Kuss e da Copart que casam com alvos
  Quando a varredura é executada
  Então cada item do resumo, do relatório e da lista mostra onde o carro está

Cenário: Copart bloqueando não derruba os outros
  Dado a Copart respondendo com desafio do Imperva
  E um lote novo no Vip que casa com um alvo
  Quando a varredura é executada
  Então o lote do Vip é avisado
  E chega um alerta identificando a Copart
  E a execução é registrada como sucesso parcial

Cenário: Formato alterado vira alerta
  Dado uma busca da Copart com resultados informados
  Quando nenhum lote consegue ser extraído do JSON
  Então chega um alerta identificando a Copart
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 a RF-03, RF-06 a RF-08 | Must | Sem eles a Copart não entra, ou entra quebrando os outros |
| RF-04 | Must | Decisão do Rafael; com a Copart, a distância vira o primeiro critério de descarte |
| RF-05 | Must | A Copart entrega FIPE, monta e documento prontos: é o que torna o pente fino possível |
| RF-09 | Should | Meta de tempo herdada; depende da rede |
| Filtro por estado do pátio | Won't (nesta feature) | Decisão do Rafael: mostrar, não filtrar (RN-05) |
| Degrau Apify com troca automática | Won't (nesta feature) | Entra com o Milan (RN-07) |

## 9. Esclarecimentos

### Sessão 2026-10-11

- **Q:** A maioria dos carros de financiamento da Copart (656 de 692) está "Aguardando Classificação", sem data, FIPE nem lance. Avisar já, ou só quando a Copart marcar a data?
  **R:** Avisar já (recomendação aceita). O aviso antecipado dá tempo de pesquisar o carro; o lance, a data e a classificação passam a ser acompanhados pela lista de monitoramento. Registrado em RN-06.

## 10. Lacunas

- 🟡 **Verificação técnica para o plano:** campo exato do valor FIPE e da data do leilão no JSON (vazios nos lotes "Aguardando Classificação"); significado de `hb` (lance atual) versus lance inicial; lotes "Compre Agora" (84 no site) e se entram; leitura das 16 páginas no ritmo do bot sem desafio do Imperva (teste realista pedido pelo Rafael); grafias de marca da Copart frente à tabela de sinônimos.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-11 | Versão inicial gerada por `/reversa-requirements` a partir da triagem da Copart (CSV exportado, prints e 9 requisições à busca JSON) | reversa |
| 2026-10-11 | Sessão de esclarecimento: RN-06 (avisar lote aguardando classificação) resolvida | `/reversa-clarify` |
