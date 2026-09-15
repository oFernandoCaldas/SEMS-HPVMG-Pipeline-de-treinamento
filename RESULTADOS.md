# SGIE V2: busca ampliada, emissão às 21h e avaliação auditada

SystemProduction representa a produção de energia do sistema, conforme confirmação do usuário. Mantiveram-se os dados, as unidades declaradas no pacote, a exclusão de zeros, o filtro solar e o período de agosto/2024 a março/2025. 31/07 fornece somente a persistência inicial. Consulte PROTOCOLO.md para todas as decisões, fontes e limitações.

## Execução e auditoria

| item | valor |
| --- | --- |
| status | aprovado |
| modelos_verificados | 80 |
| horas | 5832 |
| amostras_ajuste | 2816 |
| amostras_metricas | 2750 |
| baseline_apos_emissao_nas_metricas | 0 |
| candidatos_invalidados | 0 |
| avisos_buscas_todas_tentativas | 1 |
| repeticoes_orcamento_busca | 1 |
| total_ajustes_reais | 13041 |
| selecionados_convergentes_todos_folds | True |
| nota | ICs exploratorios condicionais; estabilidade de reajuste com parametros fixos; teste cronologico nao e novo conjunto intocado. |

O total de ajustes inclui buscas, novas tentativas de convergência, reajustes e estabilidade. Candidatos interrompidos por inelegibilidade podem executar menos de três divisões. A contagem efetiva deriva dos diagnósticos.

## Cobertura e disponibilidade às 21h

| mes | horas | ajuste | metricas | positivos_excluidos_solar |
| --- | --- | --- | --- | --- |
| 2024-08 | 744 | 303 | 298 | 34 |
| 2024-09 | 720 | 298 | 277 | 35 |
| 2024-10 | 744 | 362 | 354 | 37 |
| 2024-11 | 720 | 376 | 369 | 25 |
| 2024-12 | 744 | 411 | 400 | 36 |
| 2025-01 | 744 | 390 | 383 | 36 |
| 2025-02 | 672 | 335 | 331 | 26 |
| 2025-03 | 744 | 341 | 338 | 40 |

As 2.750 referências utilizadas nas métricas têm timestamp anterior ou igual à emissão de 21h do dia anterior. A latência real da telemetria não consta no histórico fornecido. Os valores das 22h e 23h do dia de emissão ainda não seriam conhecidos; eles não são utilizados nos horários elegíveis deste recorte.

## Teste LOMO agrupado

| modelo | n | RMSE_kWh | MAE_kWh | R2 | Skill_pct |
| --- | --- | --- | --- | --- | --- |
| KRR | 2750 | 1.338358 | 1.106049 | 0.635167 | 21.723056 |
| MLP | 2750 | 1.349393 | 1.115259 | 0.629127 | 21.077691 |
| SVR | 2750 | 1.333209 | 1.115247 | 0.637969 | 22.024245 |
| XGBoost | 2750 | 1.361953 | 1.138413 | 0.622190 | 20.343100 |
| Persistencia24h | 2750 | 1.709774 | 1.180284 | 0.404576 | 0.000000 |

## Teste LOMO mensal

| mes | modelo | n | RMSE_kWh | MAE_kWh | R2 | Skill_pct |
| --- | --- | --- | --- | --- | --- | --- |
| 2024-08 | KRR | 298 | 1.201698 | 1.010989 | 0.405356 | 4.322202 |
| 2024-08 | MLP | 298 | 1.180578 | 1.001033 | 0.426074 | 6.003723 |
| 2024-08 | SVR | 298 | 1.142663 | 0.959038 | 0.462347 | 9.022523 |
| 2024-08 | XGBoost | 298 | 1.143821 | 0.973832 | 0.461256 | 8.930284 |
| 2024-09 | KRR | 277 | 1.278953 | 1.082752 | 0.546786 | 33.295483 |
| 2024-09 | MLP | 277 | 1.283971 | 1.071176 | 0.543223 | 33.033745 |
| 2024-09 | SVR | 277 | 1.266478 | 1.071088 | 0.555584 | 33.946123 |
| 2024-09 | XGBoost | 277 | 1.276088 | 1.083037 | 0.548814 | 33.444887 |
| 2024-10 | KRR | 354 | 1.202882 | 0.991725 | 0.664858 | 28.781305 |
| 2024-10 | MLP | 354 | 1.253299 | 1.022787 | 0.636175 | 25.796249 |
| 2024-10 | SVR | 354 | 1.225947 | 1.017820 | 0.651882 | 27.415691 |
| 2024-10 | XGBoost | 354 | 1.257709 | 1.035982 | 0.633610 | 25.535160 |
| 2024-11 | KRR | 369 | 1.254589 | 0.987605 | 0.639921 | 28.144330 |
| 2024-11 | MLP | 369 | 1.259922 | 1.002711 | 0.636853 | 27.838913 |
| 2024-11 | SVR | 369 | 1.246234 | 1.012044 | 0.644701 | 28.622876 |
| 2024-11 | XGBoost | 369 | 1.291522 | 1.058496 | 0.618408 | 26.029007 |
| 2024-12 | KRR | 400 | 1.531226 | 1.258086 | 0.574104 | 24.286085 |
| 2024-12 | MLP | 400 | 1.535154 | 1.276129 | 0.571917 | 24.091868 |
| 2024-12 | SVR | 400 | 1.512397 | 1.267990 | 0.584514 | 25.217129 |
| 2024-12 | XGBoost | 400 | 1.552853 | 1.299905 | 0.561989 | 23.216708 |
| 2025-01 | KRR | 383 | 1.517837 | 1.258663 | 0.555385 | 8.147944 |
| 2025-01 | MLP | 383 | 1.504061 | 1.235656 | 0.563419 | 8.981602 |
| 2025-01 | SVR | 383 | 1.512968 | 1.269433 | 0.558233 | 8.442585 |
| 2025-01 | XGBoost | 383 | 1.563897 | 1.322739 | 0.527992 | 5.360658 |
| 2025-02 | KRR | 331 | 1.310442 | 1.119080 | 0.655601 | 24.684443 |
| 2025-02 | MLP | 331 | 1.374869 | 1.186354 | 0.620904 | 20.981628 |
| 2025-02 | SVR | 331 | 1.324586 | 1.145192 | 0.648126 | 23.871564 |
| 2025-02 | XGBoost | 331 | 1.310185 | 1.112101 | 0.655736 | 24.699244 |
| 2025-03 | KRR | 338 | 1.288001 | 1.092379 | 0.582434 | 12.481934 |
| 2025-03 | MLP | 338 | 1.285776 | 1.075385 | 0.583875 | 12.633080 |
| 2025-03 | SVR | 338 | 1.306615 | 1.119066 | 0.570277 | 11.217145 |
| 2025-03 | XGBoost | 338 | 1.349046 | 1.149207 | 0.541914 | 8.333980 |

## Teste cronológico complementar

| modelo | n | RMSE_kWh | MAE_kWh | R2 | Skill_pct |
| --- | --- | --- | --- | --- | --- |
| KRR | 669 | 1.332300 | 1.140625 | 0.605098 | 17.248904 |
| MLP | 669 | 1.311333 | 1.121181 | 0.617430 | 18.551197 |
| SVR | 669 | 1.327677 | 1.147190 | 0.607834 | 17.536020 |
| XGBoost | 669 | 1.348220 | 1.163280 | 0.595604 | 16.260044 |
| Persistencia24h | 669 | 1.610009 | 1.083587 | 0.423311 | 0.000000 |

O LOMO pode usar meses posteriores ao mês testado. O teste cronológico treina até janeiro e avalia fevereiro/março, mas é exploratório porque os dados já foram inspecionados antes. Ambos usam meteorologia histórica, não boletins futuros arquivados.

## Comparação com V1 nas mesmas 2.750 amostras

| modelo | RMSE_kWh_v1 | RMSE_kWh_v2 | RMSE_kWh_delta | MAE_kWh_v1 | MAE_kWh_v2 | MAE_kWh_delta | R2_v1 | R2_v2 | R2_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| KRR | 1.340524 | 1.338358 | -0.002166 | 1.113444 | 1.106049 | -0.007394 | 0.633986 | 0.635167 | 0.001182 |
| MLP | 1.338015 | 1.349393 | 0.011378 | 1.103315 | 1.115259 | 0.011943 | 0.635355 | 0.629127 | -0.006228 |
| SVR | 1.342065 | 1.333209 | -0.008856 | 1.109026 | 1.115247 | 0.006221 | 0.633144 | 0.637969 | 0.004825 |
| XGBoost | 1.383907 | 1.361953 | -0.021954 | 1.128346 | 1.138413 | 0.010067 | 0.609912 | 0.622190 | 0.012279 |
| Persistencia24h | 1.709774 | 1.709774 | 0.000000 | 1.180284 | 1.180284 | 0.000000 | 0.404576 | 0.404576 | 0.000000 |

## Estabilidade com parâmetros selecionados fixos

| modelo | semente | RMSE_kWh | MAE_kWh | R2 |
| --- | --- | --- | --- | --- |
| MLP | 42 | 1.349393 | 1.115259 | 0.629127 |
| MLP | 17 | 1.354643 | 1.120629 | 0.626235 |
| MLP | 73 | 1.349737 | 1.110948 | 0.628937 |
| XGBoost | 42 | 1.361953 | 1.138413 | 0.622190 |
| XGBoost | 17 | 1.355090 | 1.132434 | 0.625988 |
| XGBoost | 73 | 1.360572 | 1.136982 | 0.622956 |

Não se escolheu a melhor semente. Esses resultados avaliam a inicialização/aleatoriedade dos reajustes, não a estabilidade de novas buscas completas. KRR e SVR são determinísticos neste protocolo.

## Diferenças pareadas de RMSE

| modelo_A | modelo_B | diferenca_RMSE_A_menos_B | IC95_inferior | IC95_superior | bloco_dias | replicacoes |
| --- | --- | --- | --- | --- | --- | --- |
| KRR | MLP | -0.011034 | -0.023322 | 0.001203 | 7 | 2000 |
| KRR | SVR | 0.005150 | -0.004705 | 0.015515 | 7 | 2000 |
| KRR | XGBoost | -0.023594 | -0.040371 | -0.005777 | 7 | 2000 |
| MLP | SVR | 0.016184 | 0.004736 | 0.027788 | 7 | 2000 |
| MLP | XGBoost | -0.012560 | -0.031763 | 0.006586 | 7 | 2000 |
| SVR | XGBoost | -0.028744 | -0.041532 | -0.015855 | 7 | 2000 |

Diferença negativa favorece A. Intervalos que incluem zero não permitem uma direção consistente nesta análise. Bootstrap circular em blocos de sete dias, 2.000 réplicas; intervalos condicionais exploratórios, sem correção para múltiplas comparações nem reexecução dos ajustes.

## Modelos finais exportados

| modelo | RMSE_validacao_interna | RMSE_treino | MAE_treino | R2_treino | parametros |
| --- | --- | --- | --- | --- | --- |
| KRR | 1.449289 | 1.309332 | 1.079147 | 0.650820 | {"alpha": 2.568386730418734, "coef0": 1.0, "degree": 3, "gamma": 0.05718030235668149, "kernel": "polynomial"} |
| MLP | 1.426615 | 1.306944 | 1.077948 | 0.652093 | {"hidden_layer_sizes": [5, 5], "alpha": 0.1, "learning_rate_init": 0.001, "batch_size": "auto", "activation": "relu"} |
| SVR | 1.431339 | 1.319717 | 1.106678 | 0.645259 | {"C": 34.82675727581821, "epsilon": 0.6973941757037488, "gamma": 0.015062483652633225, "kernel": "rbf"} |
| XGBoost | 1.468538 | 1.251727 | 1.031796 | 0.680870 | {"colsample_bytree": 0.85, "learning_rate": 0.031950211734973935, "max_depth": 3, "min_child_weight": 16, "n_estimators": 200, "reg_alpha": 1.0, "reg_lambda": 0.849051908330512, "subsample": 0.7} |

As métricas de treino dos modelos finais não representam teste independente. A seleção final utiliza validações internas e o reajuste usa todas as amostras elegíveis. Os modelos LOMO são diferentes dos quatro modelos finais.

## Resultados complementares

| modelo | faixa | n | RMSE_kWh | MAE_kWh | R2 | Skill_pct |
| --- | --- | --- | --- | --- | --- | --- |
| KRR | ate200 | 634 | 0.987734 | 0.852880 | -0.026195 | 24.133800 |
| KRR | 200a500 | 893 | 1.492570 | 1.282774 | 0.142938 | 13.595924 |
| KRR | 500a800 | 806 | 1.437396 | 1.199949 | 0.190591 | 22.573832 |
| KRR | acima800 | 417 | 1.250987 | 0.931016 | 0.139530 | 34.516823 |
| MLP | ate200 | 634 | 1.015252 | 0.875015 | -0.084171 | 22.020170 |
| MLP | 200a500 | 893 | 1.498311 | 1.281483 | 0.136333 | 13.263603 |
| MLP | 500a800 | 806 | 1.444249 | 1.207327 | 0.182853 | 22.204655 |
| MLP | acima800 | 417 | 1.265625 | 0.946602 | 0.119275 | 33.750571 |
| SVR | ate200 | 634 | 0.944140 | 0.818384 | 0.062388 | 27.482153 |
| SVR | 200a500 | 893 | 1.497224 | 1.314093 | 0.137585 | 13.326515 |
| SVR | 500a800 | 806 | 1.433895 | 1.206163 | 0.194528 | 22.762399 |
| SVR | acima800 | 417 | 1.261711 | 0.965038 | 0.124714 | 33.955466 |
| XGBoost | ate200 | 634 | 0.992184 | 0.848015 | -0.035462 | 23.792016 |
| XGBoost | 200a500 | 893 | 1.518914 | 1.324632 | 0.112416 | 12.070877 |
| XGBoost | 500a800 | 806 | 1.468667 | 1.239402 | 0.154989 | 20.889372 |
| XGBoost | acima800 | 417 | 1.275220 | 0.985945 | 0.105870 | 33.248327 |

### Resumo diário

| modelo | dias | RMSE_min | RMSE_max |
| --- | --- | --- | --- |
| KRR | 243 | 0.561866 | 2.715645 |
| MLP | 243 | 0.589352 | 2.660356 |
| SVR | 243 | 0.584457 | 2.557772 |
| XGBoost | 243 | 0.536903 | 2.579959 |

As métricas completas de cada dia estão em metricas_diarias.csv. Cada pasta de rodada contém todos os candidatos, métricas internas de treino/validação, diagnósticos de convergência, datas, previsões, modelos e hashes.

## Limites preservados

Não se demonstrou ótimo global dos algoritmos. Os orçamentos de busca são distintos e explícitos. A escolha do período e a revisão das buscas ocorreram após resultados anteriores. O filtro de ponto médio continua excluindo intervalos parcialmente solares; estes não recebem validação implícita pela melhoria dos resultados. O esclarecimento de SystemProduction não resolve isoladamente a causa de valores positivos noturnos. A operação futura requer validação com boletins disponíveis às 21h e telemetria com horários reais de disponibilidade.
