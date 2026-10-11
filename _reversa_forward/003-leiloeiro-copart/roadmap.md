# Roadmap: Leiloeiro Copart

> Identificador: `003-leiloeiro-copart`
> Data: `2026-10-11`
> Requirements: `_reversa_forward/003-leiloeiro-copart/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA
> Numeração das decisões: continua a das features 001 e 002 (D-01 a D-52).

## 1. Resumo da abordagem

A Copart entra como terceiro par adaptador + parser (`copart`), no nível `script`, lendo a **busca pública em JSON** que a própria página de busca do site usa: `POST /public/vehicleFinder/search`, com o filtro `condicao:"FINANCIAMENTO"`, 100 lotes por página e **ordenação fixa pelo número do lote**. Sem a ordenação, a Copart repete e omite lotes entre páginas (medido: 36 de 1.506). Cada lote já traz tudo o que interessa (pátio, FIPE, lance, data do leilão, dano, documento, monta, funcionamento, comitente), então **não há etapa de detalhe**.

Junto, um campo **pátio** entra no `Lote` e é preenchido pelos três leiloeiros (Copart: cidade e UF do JSON; Vip: UF do card; Kuss: cidade e UF do local do evento na agenda). Pátio e FIPE aparecem no Telegram, no relatório e na lista; o relatório mostra também o lance em % da FIPE.

Verificação feita durante este plano (2026-10-11): duas leituras completas das 16 páginas no ritmo do bot (5 s), com o cliente HTTP do próprio bot, 77 s cada, sem nenhum desafio do Imperva; a segunda, ordenada, trouxe 1.506 lotes únicos. Com os alvos atuais, 13 lotes casam (Duster/Duster Oroch 2018–2022, Kicks 2019, Versa 2017 e 2019), quase todos no Nordeste e em Goiás, aguardando classificação.

## 2. Princípios aplicados

Não existe `.reversa/principles.md`. Princípios de fato das features anteriores.

| Princípio (de fato) | Como a feature se relaciona | Status |
|---------------------|-----------------------------|--------|
| Menor custo | Nível `script`; o degrau Apify não foi necessário (backlog item 9) | respeita |
| Não falhar em silêncio | Desafio do Imperva vira `bloqueado` com alerta (D-60); JSON fora do formato vira quebra; lote repetido entre páginas vira aviso em log (D-55) | respeita |
| Nenhum segredo em arquivo ou log | Sem login; sem credencial | respeita |
| Sistema não dá lances | Só a busca pública; área de membro (`/data/`, `/client/`) nunca é chamada | respeita |
| Conduta de coleta | 5 s por host; 17 requisições por varredura; ordenação e tamanho de página iguais aos que o site aceita | respeita |
| Automação máxima (preferência do Rafael, 2026-10-11) | Nenhum passo manual (a exportação CSV foi descartada) | respeita |

## 3. Decisões técnicas

### 3.1 Contrato com a Copart

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-53 | (RF-01, RF-02) Busca por `POST /public/vehicleFinder/search` (form), JSON, `query=*`, `filter[<chave>]=<chave>:"<valor>"`, `size=100`, `page`/`start` | Endpoint da própria página de busca (lido em `controllers.js`); responde sem login; 100 por página aceito | Raspar o HTML da página (os lotes vêm por JavaScript); exportação CSV pública `/public/exportLotSearchResults` (gerada no navegador a partir do JSON; não acrescenta nada); CSV exportado à mão (descartado: automação máxima) | 🟢 |
| D-54 | Sempre `sort=lot_number asc` | Sem ordenação, 36 lotes repetidos e 36 omitidos em 1.506; ordenado, 1.506 únicos e crescentes (duas leituras em 2026-10-11) | Ordenação padrão do site (instável) | 🟢 |
| D-55 | Próxima página enquanto `start + itens < totalElements` e a página não vier vazia; o adaptador registra os números já vistos e avisa no log se algum se repetir (sinal de paginação instável de novo) | Mesmo princípio da conferência de total do Kuss (D-36), mais a verificação que a paginação instável exige | Confiar só no total (não pega repetição) | 🟢 |
| D-56 | `preparar_sessao`: `GET /vehicleFinderSearch` antes das buscas | Obtém os cookies do Imperva como um navegador que abre a página de busca; 1 requisição | Ir direto ao JSON (funcionou nos testes, mas um navegador nunca faz isso) | 🟡 |
| D-57 | (RF-01) Filtros aceitos no YAML: as chaves de faceta do site (`condicao`, `categoria`, `marca`, `modelo`, `patioveiculo`, `patioleilao`, `anomodelo`, `classificacaodano`, `tipodocumento`, `condicaofuncionamento`, `chaves`, `blindado`, `tipovenda`, `dataleilao`); valor texto ou lista; chave desconhecida aborta antes da rede | Mesma regra do D-12 (Vip) e D-40 (Kuss) | Repassar qualquer chave (filtro ignorado sem erro) | 🟢 |
| D-58 | `tipo_leilao_da_busca`: `condicao` = `FINANCIAMENTO` → `financiamento`; outros → `None` | RN-02; mesma lógica do D-15 e D-39 | — | 🟢 |
| D-59 | `teto_paginas = 40` (4.000 lotes) | Hoje são 16 páginas; folga para o estoque de financiamento crescer sem virar falha | Teto padrão de 50 (serve, mas 40 já sinaliza crescimento anormal) | 🟡 |
| D-60 | O `ClienteHTTP` passa a reconhecer as marcas do Imperva (`_Incapsula_Resource`, `Incapsula incident`, `Request unsuccessful`) como desafio anti-robô, inclusive com status 200 quando o corpo é HTML | O Imperva pode responder o desafio com 200; sem isso, o parser receberia HTML e o alerta diria "parser quebrado" em vez de "bloqueado" | Deixar como quebra de parser (diagnóstico errado) | 🟡 |

### 3.2 Parsing

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-61 | (RF-03) Id `copart:<ln>`; link `https://www.copart.com.br/lotDetail/<ln>` | `ln` é global (coluna "Código" do CSV); formato do link igual ao "URL de Lote" do CSV | — | 🟢 |
| D-62 | Título `MARCA MODELO MOTOR` (`mkn lm eng`); marca por `marca_canonica(mkn)`; modelo `normalizar_texto(lm)`; anos `lcy` (modelo) e `manufactureYear` (fabricação) | `lm` é curto ("VERSA", "DUSTER OROCH"); o motor vai só no título | Usar `ld` ("2019 NISSAN VERSA", repete o ano) | 🟢 |
| D-63 | Preço: `hb > 0` → `lance_corrente`; Compre Agora → `lance_corrente` = `saleAmountBIN`; senão `None` (preço a confirmar). `preco_obrigatorio = False` | 1.445 de 1.506 sem lance (D-46 vale aqui também); o preço do Compre Agora é o que se paga, e precisa passar pelo teto | Tratar Compre Agora à parte (12 lotes; o teto já resolve) | 🟢 |
| D-64 | FIPE: `la` > 0 → novo campo `fipe`; **`fv` é o chassi e nunca é lido como FIPE** | Conferido com o CSV ("Valor FIPE") e com valores plausíveis (Peugeot 2008 2018 = R$ 54.676) | — | 🟢 |
| D-65 | Data do leilão: `ad` no formato `AAAA-MM-DD HH:MM:SS` é UTC → `pregao_em` em Brasília (UTC−3); vazio ou `"Copart Select"` → `None` | `13:00:00` corresponde às 10:00 BRT do print do Rafael | Ler a data como horário local (3 h adiantado) | 🟢 |
| D-66 | (RF-05) Observações montadas dos campos de estado, nesta ordem, omitindo vazios: "Compre Agora" (se for), dano (`dd`), documento (`stt`), monta (`damageClassification`, se não for "Aguardando Classificação"/"Não Aplicável"), funcionamento (`drivabilityRating`), comitente (`sellerName`). Lote aguardando classificação: "Aguardando classificação da Copart (data, FIPE e lance a definir)" no lugar de documento e monta (RN-06) | Reaproveita a linha `Obs.:` do Telegram e as observações completas do relatório e da lista (D-51), sem mudar o formato | Campos novos para cada um (formato do aviso cresceria) | 🟢 |
| D-67 | Quebra e busca vazia: `returnCode != 1`, falta de `data.results` ou lote sem `ln`/`mkn` → exceção (quebra); `totalElements = 0` → busca vazia declarada | Mesmo padrão do núcleo (EC-15) | — | 🟢 |

### 3.3 Pátio e saída (vale para os três leiloeiros)

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-68 | Campos novos no `Lote`: `patio: str \| None` e `fipe: Decimal \| None` | RF-04 e RF-05; detalhe em `data-delta.md` | Pátio dentro das observações (não daria para filtrar nem calcular frete depois) | 🟢 |
| D-69 | Vip: `patio` = texto de "Local:" do card (hoje a UF, ex.: "SC"; antes ia só para a descrição) | Já era lido pelo parser (`_local`) | — | 🟢 |
| D-70 | Kuss: `Evento` ganha `local`, lido da linha "Local:" da agenda ("... - Curitiba/PR" → "Curitiba - PR"); vai nas anotações da página e para `lote.patio` | O pátio do Kuss é o local do evento (pregão presencial) | Fixar "Curitiba - PR" no código (quebra se houver evento em outra cidade) | 🟢 |
| D-71 | Telegram: a 2ª linha do item ganha o pátio e a FIPE: `R$ 36.000 — Copart — VITÓRIA DE SANTO ANTÃO - PE — FIPE R$ 80.266 — Pregão 15/10 08:30`. Relatório e lista: `- **Pátio:**` e `- **FIPE:** R$ 80.266 (lance = 45% da FIPE)` | RF-04/RF-05; o % da FIPE é a primeira conta que o Rafael faz e sai de graça | Linha própria para o pátio no Telegram (item com 5 linhas) | 🟢 |

### 3.4 Palavras a excluir no veículo-alvo (RF-10)

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-72 | `VeiculoAlvo.excluir: tuple[str, ...]` (padrão vazio), lido de `excluir:` no YAML (lista de textos não vazios; texto único aceito como lista de um). O motor (`_casa_sem_km`) recusa o lote quando alguma palavra, normalizada, aparece no modelo **ou** no título normalizados. Lote recusado por exclusão conta em `descartados_sem_casar` | O título do Vip ("Renault Duster Oroch...") e o modelo da Copart ("duster oroch") cobrem os leiloeiros; normalização igual à do casamento de modelo | Regex (exagero para o caso); excluir só pelo modelo (o Vip às vezes põe a versão só no título) | 🟢 |
| D-73 | `config/veiculos-alvo.yaml`: o alvo Renault Duster ganha `excluir: [Oroch]`, e o comentário "descarte à mão" é atualizado; o exemplo criado na primeira execução documenta o campo | Pedido do Rafael | — | 🟢 |

## 4. Premissas

| Premissa | Origem | Risco se errada |
|----------|--------|-----------------|
| O Imperva continua deixando a busca passar no ritmo do bot | Teste de 2026-10-11 (35 requisições) | Copart bloqueada com alerta; Vip e Kuss seguem; resposta: degrau Apify (feature do Milan) |
| `sort=lot_number asc` continua estável | Teste de 2026-10-11 | Repetição detectada e avisada em log (D-55) |
| `la` continua sendo a FIPE e `ad` continua em UTC | CSV e print de 2026-10-11 | FIPE ou horário errados no aviso; testes com amostras reais pegam mudança de formato, não de significado |

## 5. Delta arquitetural

| Componente | Arquivo de origem | Tipo de mudança | Resumo |
|------------|-------------------|-----------------|--------|
| Adaptador Copart | `coletor-lotes.md` RF-12 | componente-novo | `src/bot_leilao/coleta/copart.py` (D-53 a D-59) |
| Parser Copart | `parser-lotes.md` RF-06, RF-12 | componente-novo | `src/bot_leilao/parsing/copart.py` (D-61 a D-67) |
| Cliente HTTP | `coletor-lotes.md` RF-07 | regra-alterada | Marcas do Imperva como desafio (D-60) |
| Modelo `Lote` | `parser-lotes.md` §9 | delta-de-dados | `patio` e `fipe` (D-68) |
| Parser Vip | `parser-lotes.md` | regra-alterada | Preenche `patio` (D-69) |
| Adaptador e parser Kuss | adendo da 002 | regra-alterada | `Evento.local` → anotação → `patio` (D-70) |
| Digest, relatório e lista | `notificador-telegram.md`; E001/E002 da 001 | regra-alterada | Pátio e FIPE (D-71) |
| Orquestrador | `agendador-observabilidade.md` | regra-alterada | Registro do par Copart |
| Cadastro | `config/leiloeiros.yaml` | regra-alterada (dados) | Bloco da Copart |
| Configuração de veículos-alvo | `configuracao-veiculos-alvo.md` §9 | delta-de-dados | Campo opcional `excluir` (D-72) |
| Motor de filtros | `motor-filtros.md` RF-02 | regra-alterada | Palavras a excluir no casamento (D-72) |

Fora do delta: banco, alertas, enriquecimento, semeadura (a E001 da 002 já põe os semeados nos documentos).

## 6. Delta no modelo de dados

- Dois campos opcionais no `Lote` (`patio`, `fipe`), `local` no `Evento` do Kuss, campos de exibição no `ItemDigest` e no `LoteRelatorio`. **Banco inalterado**.
- Detalhe em: `_reversa_forward/003-leiloeiro-copart/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Copart: página de busca e `POST /public/vehicleFinder/search` | HTTP | `interfaces/copart-busca.md` |
| Telegram `sendMessage` | HTTP | inalterado (só o texto da 2ª linha) |

## 8. Plano de migração

1. Sem migração de banco. A primeira varredura com a Copart ativa (RF-08) **semeia** a busca dela: os ~13 candidatos de hoje vão para o relatório e para `lotes-a-monitorar.md` marcados "por semeadura", sem aviso no Telegram (E001 da 002).
2. Ordem de entrega: pátio e FIPE no núcleo e na saída (Vip e Kuss passam a mostrar pátio) → adaptador e parser da Copart com amostras reais → bloco no YAML e dry-run real.
3. Reversão: `ativo: false` no bloco da Copart.

## 9. Riscos

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|---------------|---------|-----------|
| R-01 | Imperva passa a barrar o robô | média | médio | Alerta de bloqueio (D-60); degrau Apify na feature do Milan, com troca automática |
| R-02 | Paginação volta a ficar instável | baixa | médio | Ordenação fixa (D-54) e aviso de repetição (D-55) |
| R-03 | Muitos avisos de lotes longe de Londrina | alta | baixo | Pátio no aviso (RN-04); filtro por UF ou custo de frete na skill `analisar-lotes` |
| R-04 | Palavra a excluir curta demais esconde carro bom (ex.: "SE" casaria com muitos títulos) | baixa | médio | A comparação é por trecho de texto; documentar no exemplo do YAML que a palavra deve ser específica |
| R-05 | (RF-09) Volume de financiamento cresce muito | baixa | baixo | Teto de 40 páginas (D-59); a 5 s por página, 40 páginas ≈ 3,5 min |

## 10. Critério de pronto

- Os 5 cenários Gherkin do requirements passam em testes sem rede, com as amostras reais.
- Todos os testes das features 001 e 002 continuam verdes; Vip e Kuss passam a mostrar o pátio.
- Dry-run real no container: total lido igual ao informado, sem lote repetido, sem alerta, varredura completa abaixo de 10 minutos.
