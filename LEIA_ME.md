# SGIE: pacote consolidado para revisão do artigo

## Conteúdo
1. 01_pipeline_SGIE_ROBUSTO_V2: notebook, código utilizado, dados, configurações, logs, busca de hiperparâmetros, parâmetros selecionados, modelos exportados e resultados/gráficos do treinamento.
2. 02_validacao_externa_agosto2026: código de inferência e avaliação, fontes originais, dados normalizados, modelos congelados, previsões horárias, métricas, planilha e 31 painéis diários.

## Onde localizar os resultados
Na pasta 01, resultados/robusto_v2 contém metricas_lomo_mensais.csv, metricas_lomo_agrupadas.csv, metricas_cronologicas.csv, cobertura_mensal.csv, configuracoes_todas.csv e predicoes_lomo.csv. As subpastas das rodadas contêm busca.csv, métricas internas/externas e previsões individuais. Consulte README.md e RESULTADOS.md para execução e interpretação.
Na pasta 02, consulte RELATORIO.md, metricas_gerais.csv, metricas_diarias.csv, comparacao_avaliacoes.csv, comparacao_diaria_kWh.csv e previsoes_horarias_auditoria.csv. A coluna elegivel identifica os 337 horários efetivamente avaliados. A geração observada externa está em SystemProduction; as estimativas estão nas colunas dos modelos e a referência em persistencia.

## Delimitação
Pipeline: agosto/2024 a março/2025; julho/2024 fornece a referência inicial. Abril foi excluído. Avaliação externa: 01 a 31/08/2026, com 31/07 somente para persistência, sem retreinamento. Meteorologia histórica: avaliação retrospectiva, não comprovação de acurácia de boletins day-ahead emitidos às 21h.
LOMO: SVR liderou RMSE/R² e KRR o MAE. Cronológico: MLP liderou RMSE/R² e persistência o MAE. Externo: XGBoost liderou RMSE/R² e o MAE entre os modelos; persistência apresentou menor MAE horário geral. Não se afirma superioridade universal ou estatística externa.

## Integridade e reprodução
Os arquivos existentes foram reunidos sem novo treinamento ou alteração dos resultados. Caches Python foram omitidos. MANIFEST_PACOTE_SHA256.json identifica os bytes de todos os arquivos incluídos. Os manifestos originais foram preservados nos respectivos diretórios. Utilize as dependências declaradas em cada requirements.txt.
