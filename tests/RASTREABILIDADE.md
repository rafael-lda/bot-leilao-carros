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
