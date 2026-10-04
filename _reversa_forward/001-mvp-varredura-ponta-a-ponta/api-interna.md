# API interna: contrato entre testes (etapa 1) e núcleo (etapa 2)

> Feature `001-mvp-varredura-ponta-a-ponta`. Os testes de `tests/` são a fonte da verdade; este arquivo é o resumo para quem implementa.
> Pacote `bot_leilao`, layout `src/`. Datas sempre *aware*; gravação em UTC com sufixo `Z`.

## `texto`
- `normalizar_texto(s: str | None) -> str` — minúsculas, sem acento, espaços colapsados, sem bordas. `None` → `""`.
- `gerar_id(*partes) -> str` — cada parte normalizada; sequências não alfanuméricas viram `-`; partes unidas por `-`. `gerar_id("Vip Leilões") == "vip-leiloes"`.

## `logsetup`
- `mascarar(texto: str, segredos: Iterable[str]) -> str` — troca cada segredo (len ≥ 4) por `***`.
- `class FiltroSegredos(logging.Filter)` — `__init__(segredos=())`, `adicionar(valores)`; mascara a mensagem formatada e o texto da exceção (zera `args`, `exc_info`; põe em `exc_text`).
- `configurar_logs(pasta_logs: Path | None, segredos=(), nivel=logging.INFO) -> FiltroSegredos` — logger `bot_leilao`, console + arquivo `bot-leilao.log` rotativo (1 MB × 5) quando `pasta_logs`; o filtro fica nos handlers.

## `config.arquivos`
- `class ErroConfiguracao(Exception)`; `class ConfiguracaoAusente(ErroConfiguracao)` com `.caminho`.
- `ler_yaml(caminho: Path, timeout: float = 5.0) -> Any` — BOM → erro citando "BOM"; não UTF-8 → erro citando "UTF-8"; YAML inválido → erro citando "linha N".
- `garantir_arquivo(caminho: Path, exemplo: str) -> None` — se não existe, cria pastas, grava o exemplo e levanta `ConfiguracaoAusente`; se existe, não toca.
- `EXEMPLO_VEICULOS: str`, `EXEMPLO_LEILOEIROS: str` — conteúdo de `interfaces/arquivos-configuracao.md`, tudo `ativo: false`.

## `config.veiculos`
- `TIPOS_LEILAO = ("judicial", "extrajudicial", "financiamento", "seguradora", "recuperado")`
- `@dataclass(frozen=True) VeiculoAlvo(id, marca, modelo, ano_min, ano_max, preco_maximo: Decimal, tipos_leilao: tuple[str, ...], quilometragem_maxima: int | None, ativo: bool)`
- `@dataclass ResultadoVeiculos(ativos: list[VeiculoAlvo], inativos: int, avisos: list[str])`
- `carregar_veiculos(caminho: Path) -> ResultadoVeiculos` — ausente → cria exemplo e `ConfiguracaoAusente`; inválido → `ErroConfiguracao` com `'<Marca> <Modelo>'` e o campo na mensagem. id = `gerar_id(marca, modelo, ano_min, ano_max)`.

## `config.leiloeiros`
- `NIVEIS_COLETA`, `ESTRATEGIAS_ACESSO`, `FREQUENCIA_PADRAO = "seg-qua-sex-08h"`
- `@dataclass(frozen=True) Busca(id, leiloeiro_id, descricao, filtros: dict)`
- `@dataclass(frozen=True) Leiloeiro(id, nome, base_url, ativo, estrategia_acesso, credencial_env, nivel_coleta, frequencia, buscas: tuple[Busca, ...])`
- `@dataclass ResultadoLeiloeiros(ativos: list[Leiloeiro], inativos: int, avisos: list[str])`
- `id_busca(leiloeiro_id: str, filtros: dict) -> str` — `"<leiloeiro_id>:" + sha1(json.dumps(filtros, sort_keys=True, ensure_ascii=False))[:10]`
- `carregar_leiloeiros(caminho: Path, adaptadores: Mapping[str, Adaptador], parsers: Collection[str]) -> ResultadoLeiloeiros` — para leiloeiro **ativo**: exige adaptador e parser, chama `adaptador.validar_filtros(filtros)` (ValueError → `ErroConfiguracao`), recusa `logado` e nível ≠ `script` com "não implementado".

## `config.ambiente`
- `@dataclass Ambiente(telegram_token: str | None, telegram_chat_id: int | None)` com `.segredos -> list[str]`
- `carregar_ambiente(raiz: Path, exigir_telegram: bool = True, environ: Mapping | None = None) -> Ambiente` — lê `raiz/.env` sem sobrescrever `environ` (exportada vence); erro nunca contém o valor do token.

## `config.coerencia`
- `verificar_coerencia(alvos: Sequence[VeiculoAlvo], leiloeiros: Sequence[Leiloeiro], tipo_da_busca: Callable[[Leiloeiro, Busca], str | None]) -> list[str]` — avisos; nunca levanta.

## `db.conexao`
- `class ErroBanco(Exception)`; `conectar(caminho: Path) -> sqlite3.Connection` — cria pasta, `foreign_keys=ON`, `busy_timeout=10000`, `row_factory=sqlite3.Row`.
- `para_iso(dt: datetime) -> str` (UTC, `Z`, milissegundos); `de_iso(s: str) -> datetime`.

## `db.migracoes`
- `VERSAO_ATUAL = 1`; `migrar(con) -> int` — idempotente; `user_version` maior → `ErroBanco`.

## `db.trava`
- `class TravaOcupada(Exception)`; `class Trava(caminho: Path, orfa_apos: timedelta = 2h, agora: Callable[[], datetime] = utc_now)` com `adquirir() -> bool`, `liberar()`, `orfa_liberada: bool`, context manager (levanta `TravaOcupada`).

## `db.lotes`
- `@dataclass RegistroLote(id_canonico, leiloeiro_id, busca_id, alvo_id, origem, preco_na_notificacao: Decimal | None, lance_inicial: Decimal | None, link, registrado_em: datetime)`
- `class RepositorioLotes(con)`: `conhecidos(ids) -> set[str]`, `registrar(registros) -> int` (transação única, colisão ignorada), `busca_semeada(busca_id) -> bool`, `marcar_semeada(busca_id, execucao_id, quando)`, `total() -> int`.

## `db.execucoes`
- `@dataclass RegistroBusca(busca_id, leiloeiro_id, iniciado_em, duracao_ms, status_http, nivel_usado, tentativas, paginas, veredito, motivo=None, lotes_extraidos=None, lotes_descartados_parser=None, quebra_suspeita=False, motivo_quebra=None)`
- `class RepositorioExecucoes(con)` (expõe `.con`): `abrir(modo, iniciado_em) -> str`, `registrar_recusa(iniciado_em, motivo) -> str`, `fechar(execucao_id, veredito, finalizado_em, motivo=None, contagens: Mapping[str, int] | None = None, digest_enviado=False)`, `registrar_leiloeiro(execucao_id, leiloeiro_id, *, buscas_ok=0, buscas_bloqueadas=0, buscas_falhas=0, lotes_novos=0, quebra_suspeita=False, alerta_enviado=False)`, `registrar_busca(execucao_id, registro)`, `alerta_enviado_desde(leiloeiro_id, desde: datetime) -> bool`, `obter(execucao_id) -> sqlite3.Row | None`.

## `coleta.modelos`
- `class Veredito(StrEnum)`: `OK`, `BLOQUEADO`, `FALHA_REDE`, `FALHA_AUTENTICACAO`.
- `@dataclass Requisicao(metodo, url, dados: dict | None = None, cabecalhos: dict | None = None)`
- `@dataclass ResultadoHTTP(veredito, status_http, conteudo: bytes | None, tentativas, duracao_ms, url, motivo=None)` com `.ok`
- `@dataclass Pagina(numero, metodo, url, conteudo: bytes)`
- `@dataclass RespostaBruta(busca_id, leiloeiro_id, iniciado_em, duracao_ms, status_http, paginas: list[Pagina], nivel_usado, tentativas, veredito, motivo=None)` com `.bloqueado`
- `class Adaptador(Protocol)`: `leiloeiro_id`, `preparar_sessao(cliente) -> ResultadoHTTP | None`, `montar_requisicao(filtros, pagina) -> Requisicao`, `tem_proxima_pagina(conteudo, pagina) -> bool`, `validar_filtros(filtros) -> None`, `tipo_leilao_da_busca(filtros) -> str | None`.

## `coleta.http`
- `CABECALHOS_NAVEGADOR: dict` (User-Agent de navegador, Accept-Language pt-BR).
- `class ClienteHTTP(transporte=None, *, intervalo_minimo=5.0, tentativas=3, timeout=30.0, max_redirecionamentos=3, limite_bytes=20 MiB, esperas=(5.0, 15.0), espera_max_retry_after=60.0, relogio=time.monotonic, dormir=time.sleep)`: `requisitar(req) -> ResultadoHTTP`, `cookies`, `fechar()`, context manager.
- Motivos: `laco_redirecionamento`, `timeout`, `conexao`, `http_<status>`, `resposta_grande`, `conteudo_vazio`, `desafio_antibot`.

## `coleta.registro`
- `registrar_adaptador(a)`, `obter_adaptador(id)`, `adaptadores() -> dict`, `nomes_adaptadores() -> list[str]`.

## `coleta.coletor`
- `class Coletor(cliente, adaptadores: Mapping[str, Adaptador], *, teto_paginas=50, relogio=time.monotonic, agora=utc_now)`: `coletar(leiloeiros: Sequence[Leiloeiro]) -> list[RespostaBruta]`. Motivos: `preparacao_sessao: …`, `pagina N: …`, `teto_paginas`, `erro_interno: …`.

## `coleta.vip`
- `class AdaptadorVip` (`leiloeiro_id = "vip-leiloes"`), `BASE`, `MAPA_FILTROS`, `CAMPOS_FIXOS`, `TAMANHO_PAGINA = 12`; registrado ao importar o módulo.

## `parsing.modelos`
- `@dataclass Lote(id_canonico, leiloeiro_id, busca_id, link, coletado_em, numero_lote=None, titulo=None, marca=None, modelo=None, ano_fabricacao=None, ano_modelo=None, lance_inicial=None, lance_corrente=None, quilometragem=None, descricao=None, tipo_leilao=None, situacao=None, retirado=False)`
- `@dataclass ContextoParsing(leiloeiro_id, busca_id, base_url, coletado_em, tipo_leilao=None)`
- `@dataclass ExtracaoPagina(lotes: list[Lote], busca_vazia: bool = False, total_informado: int | None = None)`
- `@dataclass ResultadoParsing(busca_id, leiloeiro_id, lotes, descartados=0, quebra_suspeita=False, motivo_quebra=None, tamanho_conteudo=0, sem_conteudo=False)`

## `parsing.normalizadores`
- `normalizar_preco(t) -> Decimal | None`, `normalizar_anos(t) -> tuple[int | None, int | None]`, `normalizar_km(t) -> int | None`, `link_absoluto(href, base_url) -> str | None`, `inteiro(t) -> int | None`.

## `parsing.marcas`
- `SINONIMOS: dict`, `MARCAS_CONHECIDAS: frozenset`, `marca_canonica(marca, extras: Mapping | None = None) -> str | None`.

## `parsing.nucleo`
- `CAMPOS_OBRIGATORIOS = ("marca", "modelo", "ano_modelo", "preco")`, `LIMITE_INCOMPLETOS = 0.30`
- `registrar_parser(leiloeiro_id, parser)`, `obter_parser(id)`, `parsers() -> dict`
- `processar(resposta: RespostaBruta, contexto: ContextoParsing, parser=None) -> ResultadoParsing`

## `parsing.vip`
- `class ParserVip` com `extrair(conteudo: bytes, contexto) -> ExtracaoPagina`; registrado ao importar.

## `filtro.motor`
- `@dataclass Candidato(lote, alvo, preco_a_confirmar: bool, km_a_confirmar: bool)` com `.preco` (corrente, senão inicial)
- `@dataclass ResultadoCriterios(candidatos, vistos, descartados_retirados, descartados_dado_ausente, descartados_sem_casar, descartados_acima_km)`
- `casa(lote, alvo) -> bool`, `avaliar(lotes, alvos) -> ResultadoCriterios`

## `filtro.fluxo`
- `@dataclass ResultadoFiltragem(vistos, candidatos, novos: list[Candidato], semeaveis: list[Candidato], ja_conhecidos, descartados_sem_casar, descartados_dado_ausente, descartados_retirados, descartados_acima_km, buscas_a_semear: list[str])` com `.contagens() -> dict`
- `class FluxoFiltragem(repo: RepositorioLotes)`: `filtrar(resultados: Sequence[ResultadoParsing], alvos, buscas_aptas: set[str]) -> ResultadoFiltragem`, `registrar_semeadura(resultado, execucao_id, agora) -> int`, `confirmar_notificacao(novos, agora) -> int`

## `notificacao.digest`
- `LIMITE_BLOCO = 3800`; `escapar_html(t)`, `formatar_preco(v: Decimal | None) -> str`, `formatar_km(km) -> str`
- `@dataclass ItemDigest(titulo, ano, preco, leiloeiro, link, km=None)`; `item_de(candidato, nome_leiloeiro) -> ItemDigest`
- `montar_digest(itens, executado_em, limite=LIMITE_BLOCO) -> list[str]`
- `@dataclass AlertaOperacional(executado_em, mensagem, leiloeiro=None, severidade="aviso")`; `montar_alerta(alerta) -> str`

## `notificacao.telegram`
- `@dataclass ResultadoEnvio(ok, blocos_enviados, erro=None, definitivo=False)`
- `class NotificadorTelegram(token, chat_id, transporte=None, *, tentativas=3, timeout=20.0, esperas=(2.0, 4.0), espera_entre_blocos=1.0, espera_max_retry_after=60.0, dormir=time.sleep)`: `enviar(blocos) -> ResultadoEnvio`, `testar() -> ResultadoEnvio`.
