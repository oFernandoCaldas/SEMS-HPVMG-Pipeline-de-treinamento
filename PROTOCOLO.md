# Protocolo de execução V2

## Objetivo e decisões

Prever a energia horária do sistema, representada por SystemProduction, conforme confirmação do usuário. Unidade kWh e rótulos de encerramento de intervalo mantidos conforme o pacote de origem. Sistema de referência: 10 kW. O esclarecimento do usuário identifica a grandeza como produção de energia do sistema; não fornece nova exportação original nem resolve a causa de registros positivos de madrugada. Esses registros continuam identificados e excluídos pelo filtro solar.

Dados: CSVs Open-Meteo e Huawei do pacote anterior, sem modificação dos valores. Período alvo: 01/08/2024 00:00 a 31/03/2025 23:00, UTC−3. 31/07/2024 serve apenas como baseline. Abril não participa de nenhuma etapa. Todos os zeros de geração e de referência t−24 h permanecem excluídos, por decisão explícita. A avaliação corresponde a horas com geração positiva e referência positiva; não representa todas as condições de operação.

Entradas: GHI (W/m²), AirTemperature (°C), WindSpeed (m/s). O zênite não é entrada dos modelos. Preservou-se o zênite geométrico no meio do intervalo ≤90° para conservar a população da V1. A questão dos intervalos parcialmente solares permanece explicitamente delimitada; o desempenho desses intervalos não foi avaliado nesta comparação.

## Emissão às 21h

Para o alvo no dia D, emissão no dia D−1 às 21h locais. A persistência em t−24 h só participa quando seu timestamp é menor ou igual à emissão. A base histórica não contém os horários reais de chegada da telemetria; assume-se, para esse teste de disponibilidade, que o dado do intervalo já chegou ao fim do intervalo. O script operacional exige available_at para a persistência, verificando também sua disponibilidade real.

Os dados meteorológicos desta execução são históricos. Não são apresentados como boletins day-ahead arquivados. O script prever_21h.py recebe 24 horários do dia seguinte e exige issued_at do boletim, que não pode ser posterior à emissão. O alvo tem horizonte entre 3 e 26 horas pelos rótulos horários. Zero noturno só é aplicado quando o Sol está abaixo do horizonte em toda a grade de cinco minutos; intervalos parcialmente solares fora do filtro principal recebem previsão com status de extrapolação não validada. Para uso científico de energia diária integral, essas horas necessitam validação própria.

## Seleção e comparação

Amostragem reprodutível com ParameterSampler e distribuições logarítmicas, semente 20260914; candidatos completos congelados em config.json antes da execução. Incluem configurações de referência da versão anterior. Não é uma busca exaustiva nem garantia de ótimo global. Oito rodadas externas LOMO, três validações internas por rodada, com dias inteiros e treino anterior à validação. Sem gap adicional automático. Os quatro modelos usam as mesmas divisões e amostras de métricas. O conjunto de candidatos de cada família é idêntico em todas as rodadas.

Referências t−24 h que pertencem ao mês externo de teste não podem determinar a inclusão de amostras nas métricas internas. A regra é aplicada antes da seleção em todas as famílias. Referências contidas no próprio bloco de validação são permitidas como medições anteriores à emissão diária; não são entradas dos modelos.

Orçamentos de candidatos: KRR 72, MLP 72, SVR 96, XGBoost 192. A comparação tem protocolo comum, mas não orçamento computacional igual. Os domínios e contagens são declarados para que os resultados sejam interpretados como desempenho sob essa busca, e não como superioridade irrestrita dos algoritmos.

- KRR: kernels linear, RBF e polinomial; alpha aproximadamente 1e−5 a 1e3 (polinomial começa em 1e−4); gamma de 1e−4 a 10 para RBF e 1e−3 a 1 para polinomial; graus 2 e 3; coef0 de 0 e 1. As âncoras preservam parâmetros padrão relevantes do pacote anterior.
- MLP: 10 arquiteturas, ReLU/tanh, alpha 1e−5 a 10, taxa de aprendizado 1e−4 a 1e−2, lotes auto/64/128; Adam, semente 42, sem validação aleatória de early stopping.
- SVR: RBF, C 1e−3 a 100, epsilon 0,01 a 1,5, gamma 1e−4 a 10, além das âncoras com gamma='scale'. C e epsilon são aplicados no alvo escalonado.
- XGBoost: profundidades 1 a 6, min_child_weight 1/2/4/8/16, 50/100/200/400 árvores, taxa 0,01 a 0,3, reg_lambda 0,01 a 100, reg_alpha 0/0,01/0,1/1, subsample e colsample_bytree 0,7/0,85/1.

Critério: média aritmética do RMSE de três validações internas pareadas. Escalonadores de X e y ajustados apenas no treino de cada ajuste. Previsões limitadas a [0, máximo do treino], preservando V1; RMSE bruto também é registrado. O limite superior é empírico, não um limite físico confirmado.

## Convergência

MLP: max_iter=2000, tol=1e−4, n_iter_no_change=20. Se ocorrer ConvergenceWarning, o ajuste é reiniciado com a mesma semente e orçamento de 4000; persistindo, 8000. Essa regra é fixa e não consulta teste ou melhora de validação. Candidatos sem convergência ao final são inelegíveis. Avisos numéricos invalidam o candidato. Se o reajuste da melhor configuração falhar, tenta-se a seguinte na ordenação de validação, nunca pela métrica de teste. Todos os avisos, tentativas e tempos são preservados.

Satisfazer o critério de convergência não comprova ótimo global. Essa distinção permanece válida para todos os modelos.

## Avaliação cronológica complementar

Busca apenas em agosto/2024 a janeiro/2025; teste em fevereiro e março/2025, sem reajustar nesses meses. Verifica-se que todas as amostras efetivamente utilizadas no treino estariam disponíveis antes da emissão de 31/01/2025 às 21h. As referências de persistência avançam diariamente durante o teste; os pesos dos modelos não mudam.

Esse teste é exploratório: os meses já foram inspecionados anteriormente e algumas âncoras vieram da V1. Não é um conjunto novo, intocado, nem comprova previsão operacional com meteorologia antecipada. A confirmação final exige novos dados e boletins arquivados.

## Modelos finais e estabilidade

Busca interna sobre agosto a março seguida de reajuste integral, sem seleção pelo desempenho externo. A semente principal é 42. MLP e XGBoost são reajustados também com sementes 17 e 73 usando os hiperparâmetros já selecionados em cada rodada. As sementes não competem para escolher a melhor. A estabilidade medida é de reajuste com parâmetros fixos; não inclui variabilidade de uma nova busca inteira. KRR e SVR são determinísticos nesse protocolo e não são artificialmente repetidos.

Incerteza: bootstrap pareado circular em blocos de sete dias, 2000 réplicas, semente 20260914, sobre previsões LOMO fixas. Intervalos percentis de 95% para diferenças de RMSE. Análise exploratória condicional, sem correção de múltiplas comparações, sem reexecutar ajuste ou seleção em cada réplica. Não constitui teste definitivo de superioridade.

## Rastreabilidade

Importar os módulos não prepara dados nem escreve resultados. A assinatura é verificada antes de gravações e inclui configuração, código de treinamento, dados, presença/conteúdo do arquivo opcional de qualidade e versões do ambiente. Cada rodada concluída lista hashes dos seus artefatos. Arquivos de conclusão são escritos atomicamente após o término. Retomadas mantêm o histórico de duração da execução original.

Para execução nativa no Windows ou Linux: spawn; alternativa sequencial --workers 1. As threads das bibliotecas numéricas são limitadas a uma por processo. A reprodução bit a bit em hardware/BLAS diferentes não é garantida; o ambiente deve ser preservado, e as tolerâncias de verificação são registradas.

## Fontes técnicas consultadas

- [ParameterSampler, scikit-learn 1.8](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.ParameterSampler.html)
- [MLPRegressor, scikit-learn 1.8](https://scikit-learn.org/1.8/modules/generated/sklearn.neural_network.MLPRegressor.html)
- [Prevenção de vazamento, scikit-learn](https://scikit-learn.org/stable/common_pitfalls.html)
- [Definição das variáveis, Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api)

Essas fontes orientam a implementação. Não foram adicionadas como referências bibliográficas ao artigo.
