# Rastreabilidade: requisitos da feature 001 → testes

> Feature `001-mvp-varredura-ponta-a-ponta`. Fonte dos requisitos: `_reversa_forward/001-mvp-varredura-ponta-a-ponta/requirements.md`.
> Cada linha aponta para ao menos um teste automatizado. Nenhum teste acessa a rede.
> Conferência mecânica: todo `arquivo::teste` citado aqui existe (verificado ao gerar o arquivo).

## Requisitos funcionais

| Req. | O que exige | Testes |
|------|-------------|--------|
| RF-01 | Carregar e validar `veiculos-alvo.yaml`; inválido aborta antes da rede; sem alvo ativo é aviso | `test_config_veiculos.py::test_ano_min_maior_que_ano_max_cita_alvo_e_campo`, `test_config_veiculos.py::test_todos_inativos_geram_aviso_e_nao_erro`, `test_e2e_falhas.py::test_cenario_7_configuracao_invalida_aborta_antes_da_rede`, `test_e2e_fluxo.py::test_sem_alvo_ativo_termina_com_sucesso_sem_varrer` |
| RF-02 | Leiloeiro público com busca como filtros chave-valor; busca sem filtros rejeitada | `test_config_leiloeiros.py::test_rf02_busca_com_tres_filtros_acessiveis`, `test_config_leiloeiros.py::test_busca_sem_filtros_e_rejeitada_citando_leiloeiro_e_busca`, `test_e2e_robustez.py::test_cenario_9_cadastro_de_leiloeiro_invalido_e_rejeitado` |
| RF-03 | Sessão com cookie, timeout 30 s, até 3 redirecionamentos, cabeçalho de navegador; registro marca `script` | `test_coleta_http.py::test_cookies_persistem_na_sessao`, `test_coleta_http.py::test_redirecionamento_em_laco_vira_falha_de_rede`, `test_coleta_http.py::test_tres_redirecionamentos_ainda_sao_aceitos`, `test_coleta_http.py::test_toda_requisicao_leva_cabecalho_de_navegador`, `test_coleta_vip.py::test_preparar_sessao_faz_get_na_home`, `test_repo_execucoes.py::test_registrar_leiloeiro_e_busca` |
| RF-04 | Até 3 tentativas com espera crescente; 403/429 = bloqueio, distinto de falha de rede | `test_coleta_http.py::test_retry_com_espera_crescente_ate_dar_certo`, `test_coleta_http.py::test_403_e_429_sao_bloqueio_apos_3_tentativas`, `test_coleta_http.py::test_timeout_esgota_tentativas_como_falha_de_rede`, `test_e2e_falhas.py::test_cenario_8_bloqueio_e_distinto_de_falha_de_rede` |
| RF-05 | Lotes normalizados com todos os campos | `test_parsing_vip.py::test_um_resultado_todos_os_campos`, `test_parsing_vip.py::test_pagina_cheia_tem_12_lotes_e_total`, `test_normalizadores.py::test_preco`, `test_normalizadores.py::test_anos` |
| RF-06 | Identificador canônico estável | `test_parsing_vip.py::test_um_resultado_todos_os_campos`, `test_parsing_nucleo.py::test_lote_repetido_na_mesma_busca_fica_uma_vez` |
| RF-07 | Quebra de parser sinalizada; busca vazia legítima não é quebra | `test_parsing_nucleo.py::test_conteudo_nao_vazio_sem_lotes_e_quebra`, `test_parsing_nucleo.py::test_mais_de_30_por_cento_incompletos_e_quebra`, `test_parsing_nucleo.py::test_busca_vazia_declarada_pelo_site_nao_e_quebra`, `test_parsing_vip.py::test_layout_novo_vira_quebra_no_processamento`, `test_parsing_vip.py::test_zero_resultados_no_processamento_nao_alerta` |
| RF-08 | Candidatos por RN-01 (exemplos de R$ 41.900 e R$ 52.000) | `test_motor_criterios.py::test_exemplo_do_requirements_casa`, `test_motor_criterios.py::test_exemplo_do_requirements_acima_do_teto_nao_casa`, `test_motor_criterios.py::test_ano_de_modelo_com_extremos` |
| RF-09 | Deduplicação no SQLite; gravação só após confirmação | `test_motor_fluxo.py::test_ja_notificado_nao_volta`, `test_motor_fluxo.py::test_novos_so_sao_gravados_apos_confirmacao`, `test_e2e_fluxo.py::test_cenario_4_execucao_repetida_nao_renotifica` |
| RF-10 | Um digest por execução, com os cinco elementos; nada sem lote novo | `test_digest.py::test_digest_com_cabecalho_e_itens`, `test_digest.py::test_sem_itens_nao_ha_mensagem`, `test_digest.py::test_digest_grande_e_dividido_sem_cortar_item`, `test_e2e_fluxo.py::test_cenario_2_lote_novo_gera_digest` |
| RF-11 | Alerta operacional separado, mesmo sem lote novo | `test_e2e_falhas.py::test_cenario_5_parser_quebrado_avisa_em_vez_de_silenciar`, `test_e2e_falhas.py::test_alerta_de_quebra_no_maximo_um_por_dia`, `test_digest.py::test_alerta_de_leiloeiro` |
| RF-12 | Registro de cada execução com contagens, inclusive em falha | `test_repo_execucoes.py::test_abrir_e_fechar_com_contagens`, `test_motor_fluxo.py::test_contagens_para_o_historico`, `test_e2e_robustez.py::test_cenario_10_execucao_que_falha_por_completo_fica_registrada`, `test_e2e_robustez.py::test_trava_e_liberada_ao_fim_mesmo_com_erro` |
| RF-13 | Primeira execução semeia sem notificar | `test_motor_fluxo.py::test_primeira_execucao_de_uma_busca_semeia_sem_notificar`, `test_e2e_fluxo.py::test_cenario_1_primeira_execucao_popula_a_base_sem_notificar` |
| RF-14 | Comando de execução manual | `test_cli.py::test_varrer_com_sucesso_sai_com_zero`, `test_cli.py::test_dry_run_imprime_o_digest_e_nao_envia`, `test_cli.py::test_testar_telegram` |
| RF-15 | Trava exclusiva contra execução concorrente | `test_trava.py::test_primeira_adquire_e_segunda_e_recusada`, `test_trava.py::test_trava_com_mais_de_duas_horas_e_orfa`, `test_e2e_robustez.py::test_cenario_11_segunda_execucao_simultanea_e_recusada`, `test_cli.py::test_trava_ocupada_sai_com_tres` |
| RF-16 | `quilometragem_maxima` opcional por alvo | `test_config_veiculos.py::test_carrega_alvos_validos`, `test_motor_criterios.py::test_quilometragem_maxima_opcional`, `test_motor_criterios.py::test_quilometragem_ausente_nao_elimina` |
| RF-17 | Retirados descartados antes da filtragem, com contagem | `test_motor_criterios.py::test_retirados_sao_descartados_antes_de_filtrar`, `test_parsing_vip.py::test_retirado_pelo_texto`, `test_e2e_fluxo.py::test_retirado_nao_e_notificado` |
| RF-18 | Todas as páginas, com intervalo mínimo por host | `test_coletor.py::test_coleta_todas_as_paginas_de_uma_busca`, `test_coletor.py::test_paginas_espacadas_em_pelo_menos_5s`, `test_coleta_http.py::test_intervalo_minimo_de_5s_entre_requisicoes_ao_mesmo_host`, `test_coleta_vip.py::test_proxima_pagina_lida_da_marcacao` |

## Cenários de aceitação (requirements.md §7)

| # | Cenário | Teste |
|---|---------|-------|
| 1 | Primeira execução popula a base sem notificar | `test_e2e_fluxo.py::test_cenario_1_primeira_execucao_popula_a_base_sem_notificar` |
| 2 | Lote novo gera digest no Telegram | `test_e2e_fluxo.py::test_cenario_2_lote_novo_gera_digest` |
| 3 | Lote acima do teto não é notificado | `test_e2e_fluxo.py::test_cenario_3_lote_acima_do_teto_nao_e_notificado` |
| 4 | Execução repetida não renotifica | `test_e2e_fluxo.py::test_cenario_4_execucao_repetida_nao_renotifica` |
| 5 | Parser quebrado avisa em vez de silenciar | `test_e2e_falhas.py::test_cenario_5_parser_quebrado_avisa_em_vez_de_silenciar` |
| 6 | Falha no envio preserva os lotes para a próxima execução | `test_e2e_falhas.py::test_cenario_6_falha_no_envio_preserva_os_lotes` |
| 7 | Configuração inválida aborta antes de tocar a rede | `test_e2e_falhas.py::test_cenario_7_configuracao_invalida_aborta_antes_da_rede` |
| 8 | Bloqueio do site é distinguido de falha de rede | `test_e2e_falhas.py::test_cenario_8_bloqueio_e_distinto_de_falha_de_rede` |
| 9 | Cadastro de leiloeiro inválido é rejeitado | `test_e2e_robustez.py::test_cenario_9_cadastro_de_leiloeiro_invalido_e_rejeitado` |
| 10 | Execução que falha por completo fica registrada | `test_e2e_robustez.py::test_cenario_10_execucao_que_falha_por_completo_fica_registrada` |
| 11 | Segunda execução simultânea é recusada | `test_e2e_robustez.py::test_cenario_11_segunda_execucao_simultanea_e_recusada` |

## Regras e requisitos não funcionais

| Item | Testes |
|------|--------|
| RN-08 — nenhum segredo em log, console ou banco | `test_seguranca.py::test_erro_de_conexao_com_a_url_do_bot_nao_vaza_o_token`, `test_seguranca.py::test_excecao_inesperada_com_o_token_e_mascarada_no_rastreamento`, `test_seguranca.py::test_execucao_completa_com_digest_nao_vaza_o_token`, `test_logsetup.py::test_filtro_mascara_rastreamento_de_excecao` |
| RN-02 — ano de modelo | `test_motor_criterios.py::test_ano_de_fabricacao_dentro_da_faixa_nao_basta` |
| RN-03 — lance corrente, senão inicial | `test_motor_criterios.py::test_sem_lance_compara_o_inicial`, `test_parsing_vip.py::test_sem_lance_corrente_e_nulo` |
| RN-04 — preço ausente não elimina, ano ausente elimina | `test_motor_criterios.py::test_sem_nenhum_preco_e_candidato_a_confirmar`, `test_motor_criterios.py::test_sem_ano_de_modelo_e_descartado_por_dado_ausente` |
| RN-06 — gravar só após confirmação | `test_e2e_fluxo.py::test_cenario_2_lote_novo_gera_digest` |
| RNF desempenho — deduplicação < 1 s | `test_repo_lotes.py::test_consulta_de_deduplicacao_rapida_com_50_mil_registros` |
| RNF conduta — 5 s entre requisições ao mesmo host | `test_coleta_http.py::test_intervalo_minimo_de_5s_entre_requisicoes_ao_mesmo_host`, `test_coleta_http.py::test_429_sem_retry_after_espera_30s` |
| RNF segurança — SQLite fora do versionamento | `.gitignore` (`dados/`, `*.sqlite3`); sem teste automatizado |
| RNF desempenho — execução < 10 min | Sem teste automatizado (depende da rede); medido em 2026-10-04: 1min31s para 17 páginas |
| D-28 — sinônimos de marca | `test_parsing_vip.py::test_sinonimos_de_marca_do_vip_sao_traduzidos`, `test_motor_criterios.py::test_marca_do_alvo_tambem_passa_pela_tabela_de_sinonimos` |
| D-32 — km sentinela (0, ≥ 900.000) vale "não informada" | `test_normalizadores.py::test_quilometragem_sentinela_vale_nao_informada`, `test_parsing_vip.py::test_km_sentinela_do_site_vira_nao_informada`, `test_e2e_fluxo.py::test_km_sentinela_nao_esconde_o_carro_com_teto_de_km`, `test_e2e_fluxo.py::test_km_real_acima_do_teto_continua_eliminada` |
| D-30 — cabeçalho de navegador | `test_coleta_http.py::test_toda_requisicao_leva_cabecalho_de_navegador` |
| D-31 — busca vazia legítima | `test_parsing_vip.py::test_zero_resultados_e_busca_vazia_declarada`, `test_e2e_falhas.py::test_busca_vazia_legitima_nao_alerta` |

## Emendas

| Emenda | Testes |
|--------|--------|
| E001 — relatório Markdown por varredura | `test_relatorio.py` (11 testes), `test_e2e_fluxo.py::test_cada_varredura_gera_um_relatorio_so_com_os_lotes_novos`, `test_e2e_fluxo.py::test_dry_run_nao_gera_relatorio`, `test_e2e_fluxo.py::test_varredura_com_falha_tambem_gera_relatorio`, `test_e2e_fluxo.py::test_relatorio_nao_contem_o_token`, `test_e2e_fluxo.py::test_falha_ao_gravar_relatorio_nao_derruba_a_varredura` |
| E002 — lista acumulada de lotes a monitorar | `test_relatorio.py::test_lista_criada_com_as_regras_num_arquivo_a_parte`, `test_relatorio.py::test_acrescenta_no_fim_sem_tocar_no_que_ja_existe`, `test_relatorio.py::test_nao_repete_lote_que_ja_esta_na_lista`, `test_relatorio.py::test_sem_lotes_novos_nao_cria_nem_altera`, `test_e2e_fluxo.py::test_lote_avisado_entra_na_lista_uma_unica_vez`, `test_e2e_fluxo.py::test_lote_semeado_entra_na_lista_marcado_como_semeadura`, `test_e2e_fluxo.py::test_lote_so_entra_depois_que_o_telegram_confirma`, `test_e2e_fluxo.py::test_lote_tirado_da_lista_nao_volta`, `test_e2e_fluxo.py::test_dry_run_nao_escreve_na_lista` |

## Feature 002: Claudio Kuss Leilões

> Fonte: `_reversa_forward/002-leiloeiro-claudio-kuss/requirements.md`. Fixtures reais de 2026-10-10 em `tests/fixtures/claudio_kuss/`; site simulado por `apoio.SiteKuss`.

| Req. | O que exige | Testes |
|------|-------------|--------|
| RF-01 | Cadastro com busca por `categoria`; chave desconhecida aborta | `test_coleta_claudio_kuss.py::test_so_aceita_o_filtro_categoria`, `test_coleta_claudio_kuss.py::test_registrado_pelo_id_do_leiloeiro`, `test_parsing_claudio_kuss.py::test_registrado_e_sem_preco_obrigatorio` |
| RF-02 | Descobrir os eventos da categoria a cada varredura | `test_coleta_claudio_kuss.py::test_ler_agenda_real`, `test_coleta_claudio_kuss.py::test_percorre_quantidade_e_paginas_de_cada_evento`, `test_coleta_claudio_kuss.py::test_sem_evento_da_categoria_para_na_agenda`, `test_coleta_claudio_kuss.py::test_categoria_comparada_sem_acento_e_sem_caixa` |
| RF-03 | Todas as páginas de cada evento, conferindo com a quantidade informada | `test_coleta_claudio_kuss.py::test_total_lido_diferente_do_informado_vai_para_o_log`, `test_coleta_claudio_kuss.py::test_total_conferido_sem_aviso`, `test_coleta_claudio_kuss.py::test_pagina_vazia_antes_do_fim_encerra_o_evento`, `test_coletor.py::test_teto_de_paginas_declarado_pelo_adaptador_prevalece`, `test_e2e_claudio_kuss.py::test_lotes_dos_dois_eventos_sao_lidos_e_conferidos` |
| RF-04 | Lote normalizado: id pelo `seq`, marca e modelo, anos `AA/AA`, lance, link, tipo | `test_parsing_claudio_kuss.py::test_fluence_real_com_todos_os_campos`, `test_parsing_claudio_kuss.py::test_sinonimo_e_valor`, `test_parsing_claudio_kuss.py::test_lote_real_com_lance`, `test_normalizadores.py::test_anos_dois_digitos_do_claudio_kuss`, `test_marcas.py::test_grafias_do_claudio_kuss` |
| RF-05 | Detalhe só dos lotes novos; retirados (e sucata) descartados | `test_enriquecimento.py::test_lote_novo_do_kuss_recebe_observacoes_e_despesas`, `test_enriquecimento.py::test_retirado_no_detalhe_sai_da_lista_e_e_contado`, `test_enriquecimento.py::test_sucata_no_detalhe_sai_da_lista_e_e_contada`, `test_e2e_claudio_kuss.py::test_candidato_retirado_no_detalhe_nao_e_avisado`, `test_e2e_claudio_kuss.py::test_primeira_varredura_semeia_o_kuss_sem_aviso_e_mostra_nos_documentos` |
| RF-06 | Data e hora do pregão no aviso e nos relatórios | `test_digest.py::test_texto_do_item_do_kuss`, `test_relatorio.py::test_relatorio_do_kuss_tem_pregao_despesas_documento_e_observacoes` |
| RF-07 | Observações (resumidas no Telegram, completas no relatório e na lista) e despesas admin. | `test_digest.py::test_observacoes_longas_sao_resumidas_em_160_caracteres`, `test_digest.py::test_detalhe_que_falhou_avisa_para_ver_o_link`, `test_relatorio.py::test_lista_de_monitoramento_do_kuss_tem_as_mesmas_linhas`, `test_parsing_claudio_kuss.py::test_detalhe_real_sinistrado`, `test_parsing_claudio_kuss.py::test_texto_padrao_de_todo_lote_nunca_entra_nas_observacoes` |
| RF-08 | Sem eventos ou `qtde = 0` é busca vazia; `qtde > 0` sem lotes é quebra | `test_parsing_claudio_kuss.py::test_no_nucleo_agenda_sem_financeiras_nao_e_quebra`, `test_parsing_claudio_kuss.py::test_no_nucleo_eventos_da_categoria_sem_lotes_nao_e_quebra`, `test_parsing_claudio_kuss.py::test_no_nucleo_evento_com_lotes_informados_e_nenhum_lido_e_quebra`, `test_parsing_claudio_kuss.py::test_no_nucleo_agenda_sem_blocos_e_quebra`, `test_parsing_claudio_kuss.py::test_no_nucleo_lotes_sem_preco_nao_sao_quebra` |
| RF-09 | Semeadura, deduplicação, relatório e lista também para o Kuss | `test_e2e_claudio_kuss.py::test_primeira_varredura_semeia_o_kuss_sem_aviso_e_mostra_nos_documentos`, `test_e2e_claudio_kuss.py::test_lote_que_casa_e_avisado_com_leiloeiro_ano_pregao_observacoes_e_link` |
| RF-10 | Falha de um leiloeiro não derruba o outro | `test_e2e_claudio_kuss.py::test_kuss_fora_do_ar_nao_impede_o_aviso_do_vip`, `test_enriquecimento.py::test_falha_num_lote_nao_impede_os_outros` |

| # | Cenário (requirements §7) | Teste |
|---|---------------------------|-------|
| 1 | Lotes do Claudio Kuss entram na varredura | `test_e2e_claudio_kuss.py::test_lotes_dos_dois_eventos_sao_lidos_e_conferidos` |
| 2 | Lote do Claudio Kuss que casa com um alvo é avisado | `test_e2e_claudio_kuss.py::test_lote_que_casa_e_avisado_com_leiloeiro_ano_pregao_observacoes_e_link` |
| 3 | Candidato retirado não é avisado | `test_e2e_claudio_kuss.py::test_candidato_retirado_no_detalhe_nao_e_avisado` |
| 4 | Sem eventos de financeiras não é erro | `test_e2e_claudio_kuss.py::test_sem_eventos_de_financeiras_nao_e_erro` |
| 5 | Formato alterado vira alerta | `test_e2e_claudio_kuss.py::test_formato_alterado_vira_alerta_do_kuss` |
| 6 | Um leiloeiro fora do ar não derruba o outro | `test_e2e_claudio_kuss.py::test_kuss_fora_do_ar_nao_impede_o_aviso_do_vip` |

| Item | Testes |
|------|--------|
| RN-06 — sem km, nunca eliminado pelo teto de km | `test_parsing_claudio_kuss.py::test_fluence_real_com_todos_os_campos` (km nula) e as regras da 001 (`test_motor_criterios.py::test_quilometragem_ausente_nao_elimina`) |
| RN-09 — sem lance, login nem área restrita; apelido de quem deu lance nunca lido | `test_parsing_claudio_kuss.py::test_apelido_de_quem_deu_lance_nunca_e_lido`; endpoints usados em `test_coleta_claudio_kuss.py::test_corpo_cabecalhos_e_anotacoes_das_requisicoes_json` |
| D-37 — anotações por página | `test_coletor.py::test_anotacoes_da_requisicao_chegam_a_pagina`, `test_parsing_nucleo.py::test_parser_recebe_as_anotacoes_de_cada_pagina` |
| D-43 — sucata fora do aviso | `test_parsing_claudio_kuss.py::test_detalhe_real_de_sucata`, `test_parsing_claudio_kuss.py::test_sucata_so_pelo_local_do_documento`, `test_parsing_claudio_kuss.py::test_sucata_nao_e_devolvida_e_vai_para_o_log` |
| D-46 — preço opcional no limite de incompletos | `test_parsing_nucleo.py::test_parser_sem_preco_obrigatorio_nao_conta_preco_ausente`, `test_parsing_nucleo.py::test_por_padrao_preco_ausente_continua_contando` |
| RNF desempenho — varredura < 10 min | Sem teste automatizado; dry-run real de 2026-10-10: 5m16s (Vip 15 páginas + Kuss 43 páginas) |

| Emenda | Testes |
|--------|--------|
| E001 da 002 — semeados no relatório e na lista, sem aviso | `test_relatorio.py::test_relatorio_lista_os_semeados_numa_secao_propria`, `test_relatorio.py::test_lote_da_semeadura_entra_no_mesmo_formato`, `test_e2e_fluxo.py::test_lote_semeado_entra_na_lista_marcado_como_semeadura`, `test_e2e_fluxo.py::test_semeado_nao_volta_a_entrar_na_lista`, `test_e2e_claudio_kuss.py::test_primeira_varredura_semeia_o_kuss_sem_aviso_e_mostra_nos_documentos`, `test_e2e_claudio_kuss.py::test_semeado_retirado_ou_sucata_e_registrado_mas_nao_aparece`, `test_e2e_claudio_kuss.py::test_dry_run_nao_detalha_semeados` |

## Feature 003: Copart (e pátio para todos)

> Fonte: `_reversa_forward/003-leiloeiro-copart/requirements.md`. Fixtures reais de 2026-10-11 em `tests/fixtures/copart/`; site simulado por `apoio.SiteCopart`.

| Req. | O que exige | Testes |
|------|-------------|--------|
| RF-01 | Cadastro com filtros de faceta; chave desconhecida aborta | `test_coleta_copart.py::test_registrado_pelo_id_do_leiloeiro`, `test_coleta_copart.py::test_filtros_aceitos_e_chave_desconhecida`, `test_parsing_copart.py::test_registrado_e_sem_preco_obrigatorio` |
| RF-02 | Todas as páginas, total conferido, sem repetição | `test_coleta_copart.py::test_percorre_todas_as_paginas_ate_o_total`, `test_coleta_copart.py::test_pagina_vazia_antes_do_total_encerra_com_aviso`, `test_coleta_copart.py::test_lote_repetido_entre_paginas_gera_aviso`, `test_coleta_copart.py::test_requisicao_da_primeira_pagina`, `test_e2e_copart.py::test_todas_as_paginas_sao_lidas_e_conferidas` |
| RF-03 | Lote normalizado (id, marca, modelo, anos, lance, link, tipo, pátio) | `test_parsing_copart.py::test_duster_oroch_real_com_todos_os_campos`, `test_parsing_copart.py::test_versa_aguardando_classificacao`, `test_parsing_copart.py::test_compre_agora_usa_o_preco_fixo`, `test_parsing_copart.py::test_pagina_real_com_100_lotes` |
| RF-04 | Pátio de todo leiloeiro no Telegram, relatório e lista | `test_parsing_vip.py::test_patio_vem_do_local_do_card`, `test_coleta_claudio_kuss.py::test_agenda_traz_o_local_do_evento`, `test_parsing_claudio_kuss.py::test_lote_recebe_o_patio_da_anotacao`, `test_digest.py::test_segunda_linha_com_patio_e_fipe_na_ordem`, `test_relatorio.py::test_lista_traz_patio_e_fipe`, `test_e2e_copart.py::test_todo_aviso_mostra_o_patio` |
| RF-05 | FIPE, data e estado da Copart | `test_parsing_copart.py::test_chassi_nunca_vira_fipe`, `test_parsing_copart.py::test_monta_aparece_quando_classificada`, `test_parsing_copart.py::test_data_invalida_ou_ausente_e_nula`, `test_relatorio.py::test_relatorio_traz_patio_e_fipe_com_percentual` |
| RF-06 | Zero resultados = vazia; formato alterado = alerta | `test_parsing_copart.py::test_zero_resultados_e_busca_vazia`, `test_parsing_copart.py::test_formato_inesperado_levanta`, `test_e2e_copart.py::test_formato_alterado_vira_alerta_da_copart` |
| RF-07 | Bloqueio do Imperva distinto, com alerta, sem derrubar os outros | `test_coleta_http.py::test_desafio_do_imperva_e_bloqueio`, `test_e2e_copart.py::test_copart_bloqueando_nao_impede_o_vip_e_gera_alerta`, `test_e2e_copart.py::test_alerta_de_bloqueio_no_maximo_um_por_dia` |
| RF-08 | Semeadura e documentos | `test_e2e_copart.py::test_estreia_da_copart_lista_os_semeados_com_patio` |
| RF-09 | Varredura < 10 min | Sem teste automatizado; dry-run real de 2026-10-11: 5m47s (Vip 11, Kuss 43, Copart 16 páginas) |
| RF-10 | Palavras a excluir no veículo-alvo | `test_config_veiculos.py::test_excluir_como_lista`, `test_config_veiculos.py::test_excluir_invalido_cita_alvo_e_campo`, `test_motor_criterios.py::test_palavra_excluida_no_modelo_impede_o_casamento`, `test_motor_criterios.py::test_palavra_excluida_no_titulo_tambem_impede`, `test_e2e_copart.py::test_duster_oroch_excluida_pelo_alvo` |

| # | Cenário (requirements §7) | Teste |
|---|---------------------------|-------|
| 1 | Lotes de financiamento da Copart entram na varredura | `test_e2e_copart.py::test_todas_as_paginas_sao_lidas_e_conferidas` |
| 2 | Lote que casa é avisado com pátio e FIPE | `test_e2e_copart.py::test_lote_que_casa_e_avisado_com_patio_fipe_e_link` |
| 3 | Todo aviso mostra o pátio | `test_e2e_copart.py::test_todo_aviso_mostra_o_patio` |
| 4 | Copart bloqueando não derruba os outros | `test_e2e_copart.py::test_copart_bloqueando_nao_impede_o_vip_e_gera_alerta` |
| 5 | Formato alterado vira alerta | `test_e2e_copart.py::test_formato_alterado_vira_alerta_da_copart` |

| Emenda | Testes |
|--------|--------|
| E001 da 003 — Copart sem a página HTML; situação dos leiloeiros no relatório | `test_coleta_copart.py::test_nao_abre_a_pagina_html_da_busca`, `test_e2e_copart.py::test_busca_nao_passa_pela_pagina_html`, `test_e2e_copart.py::test_copart_bloqueando_nao_impede_o_vip_e_gera_alerta`, `test_relatorio.py::test_relatorio_mostra_a_situacao_de_cada_leiloeiro`, `test_relatorio.py::test_sem_situacao_de_leiloeiros_nao_ha_secao` |
| E002 da 003 — novo formato da lista, numerada, regras à parte | `test_relatorio.py::test_lista_criada_com_as_regras_num_arquivo_a_parte`, `test_relatorio.py::test_formato_do_lote_definido_pelo_rafael`, `test_relatorio.py::test_numeracao_continua_do_maior_numero_mesmo_com_lotes_apagados`, `test_relatorio.py::test_arquivo_de_comentarios_nao_e_sobrescrito`, `test_relatorio.py::test_lote_da_semeadura_entra_no_mesmo_formato` |

## Feature 004: Freitas Leiloeiro (e certificados)

> Fonte: `_reversa_forward/004-leiloeiro-freitas/requirements.md`. Fixtures reais de 2026-10-13 em `tests/fixtures/freitas/`; site simulado por `apoio.SiteFreitas`.

| Req. | O que exige | Testes |
|------|-------------|--------|
| RF-01 | Cadastro com filtros do site; chave desconhecida aborta | `test_coleta_freitas.py::test_registrado_pelo_id_do_leiloeiro`, `test_coleta_freitas.py::test_filtros_aceitos_e_chave_desconhecida`, `test_coleta_freitas.py::test_filtros_viram_os_parametros_do_site`, `test_parsing_freitas.py::test_registrado` |
| RF-02 | Todas as páginas até a mensagem de fim, sem repetição | `test_coleta_freitas.py::test_percorre_ate_a_mensagem_de_fim`, `test_coleta_freitas.py::test_pagina_com_menos_de_200_nao_encerra_a_busca`, `test_coleta_freitas.py::test_lote_repetido_entre_paginas_gera_aviso`, `test_e2e_freitas.py::test_le_ate_a_mensagem_de_fim_sem_repeticao` |
| RF-03 | Card em lote normalizado (exceto em loteamento) | `test_parsing_freitas.py::test_duster_real_com_todos_os_campos`, `test_parsing_freitas.py::test_importado_sem_barra_entre_marca_e_modelo`, `test_parsing_freitas.py::test_lance_inicial_quando_ainda_sem_lances`, `test_parsing_freitas.py::test_em_loteamento_nao_e_devolvido_e_vai_para_o_log`, `test_marcas.py::test_grafias_do_claudio_kuss` |
| RF-04 | Pátio, despesas e observações pelo detalhe | `test_parsing_freitas.py::test_detalhe_real_do_duster`, `test_parsing_freitas.py::test_detalhe_real_em_santa_barbara`, `test_parsing_freitas.py::test_despesas_de_logistica_somadas_com_a_composicao_nas_observacoes`, `test_e2e_freitas.py::test_estreia_lista_os_semeados_com_patio_e_despesas` |
| RF-05 | Verificação completa com o intermediário oficial | `test_coleta_http.py::test_contexto_tls_confia_no_certifi_e_nos_intermediarios_da_pasta`, `test_coleta_http.py::test_cliente_usa_o_contexto_com_verificacao`, `test_coleta_http.py::test_nenhum_codigo_desliga_a_verificacao` |
| RF-06 | Fim sem lotes = vazia; formato alterado = quebra | `test_parsing_freitas.py::test_mensagem_de_fim_e_busca_vazia`, `test_parsing_freitas.py::test_sem_cards_e_sem_mensagem_de_fim_levanta`, `test_parsing_freitas.py::test_card_com_descricao_fora_do_formato_levanta` |
| RF-07 | Semeadura, relatório e lista | `test_e2e_freitas.py::test_estreia_lista_os_semeados_com_patio_e_despesas` |
| RF-08 | Falha não derruba os outros; bloqueio e certificado geram alerta | `test_e2e_freitas.py::test_freitas_bloqueando_nao_derruba_o_vip_e_gera_alerta`, `test_e2e_freitas.py::test_falha_de_certificado_gera_alerta_que_aponta_o_runbook`, `test_e2e_freitas.py::test_alerta_de_certificado_no_maximo_um_por_dia`, `test_coleta_http.py::test_falha_de_certificado_vira_motivo_proprio_sem_novas_tentativas` |
| RF-09 | Varredura < 10 min | Sem teste automatizado; dry-run real de 2026-10-13: 6m43s (Vip 13, Kuss 45, Copart 16, Freitas 3 páginas) |

| # | Cenário (requirements §7) | Teste |
|---|---------------------------|-------|
| 1 | Lotes inteiros do Freitas entram na varredura | `test_e2e_freitas.py::test_le_ate_a_mensagem_de_fim_sem_repeticao` |
| 2 | Lote de financeira que casa é avisado | `test_e2e_freitas.py::test_lote_de_financeira_que_casa_e_avisado_com_patio_pregao_e_link` |
| 3 | Lote sem etiqueta de financeira não é avisado | `test_e2e_freitas.py::test_lote_sem_etiqueta_de_financeira_nao_e_avisado` |
| 4 | Cadeia incompleta não desliga a verificação | `test_coleta_http.py::test_contexto_tls_confia_no_certifi_e_nos_intermediarios_da_pasta`, `test_coleta_http.py::test_nenhum_codigo_desliga_a_verificacao` |
| 5 | Freitas bloqueando não derruba os outros | `test_e2e_freitas.py::test_freitas_bloqueando_nao_derruba_o_vip_e_gera_alerta` |
