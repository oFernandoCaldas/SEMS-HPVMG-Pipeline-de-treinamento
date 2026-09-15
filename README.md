# PIPELINE SEMS HPVMG - TREINAMENTO DOS MODELOS E AVALIAÇÃO EXPERIMENTAL

## Gráficos de teste por modelo

O notebook inclui comparações de previsão, persistência e geração real para KRR, MLP, SVR e XGBoost. A pasta `graficos` contém 972 curvas diárias (243 dias × 4 modelos), 32 painéis mensais, quatro painéis horários completos e quatro resumos de somas diárias.

```bash
python plotar_resultados.py --todos-dias
python plotar_resultados.py --modelo KRR --dia 2024-08-01
```

Não há retreinamento: os gráficos leem `predicoes_lomo.csv` e verificam timestamps e referências contra o protocolo. Lacunas permanecem sem linha; não são preenchidas com zeros. As somas diárias representam somente os horários elegíveis, não a energia integral do dia. No notebook, altere `DIA` para comparar os quatro modelos na mesma data. LOMO com meteorologia histórica não equivale à validação operacional com boletins disponíveis às 21h.

Pacote completo com dados, fontes, candidatos congelados, modelos exportados, notebook e resultados auditados. Leia RESULTADOS.md e PROTOCOLO.md.

## VS Code / reprodução

Use Python 3.12.14 e selecione o interpretador desse ambiente no VS Code. Instale `python -m pip install -r requirements.txt`. As versões exatas são necessárias para a assinatura e para carregar os modelos serializados de forma consistente.

Abra o notebook Pipeline_SGIE_ROBUSTO_V2.ipynb com esse interpretador ou execute:

```bash
python testar_protocolo.py
python executar.py --workers 6
python auditar.py
python gerar_relatorio.py
```

O executor funciona com spawn em Windows/Linux; `--workers 1` é a alternativa sequencial. Rodadas íntegras são retomadas. Uma execução completamente nova requer copiar o pacote e alterar run_id em config.json; uma alteração de código, dados, qualidade ou ambiente não pode reutilizar resultados antigos. Importar módulos não grava resultados.

O notebook entregue contém as saídas reais da inspeção. As células foram executadas sequencialmente em processo IPython local; o ambiente desta execução não permite iniciar kernel Jupyter por sockets. O treinamento integral foi realizado pelo script executar.py.

## Previsão às 21h

```bash
python prever_21h.py --modelo MLP --entrada boletim.csv --emissao 2026-09-03T21:00:00-03:00 --saida previsoes.csv --persistencia geracao_disponivel.csv
```

O nome MLP é apenas exemplo de sintaxe, não seleção automática do vencedor. A entrada exige timestamp, issued_at, GHI, AirTemperature e WindSpeed para as 24 horas do próximo dia, em ordem. `issued_at` deve ser o horário real de emissão/disponibilidade do boletim e não pode exceder 21h. A persistência opcional exige timestamp, SystemProduction e available_at. Não relacione meteorologia histórica como se fosse boletim arquivado.

O script grava os 24 horários. Intervalos noturnos recebem zero por regra solar; intervalos parcialmente solares fora do domínio de treinamento são explicitamente marcados como extrapolação não validada. Confira a coluna status. A exclusão dos zeros nas métricas permanece. O comando não busca meteorologia na internet nem agenda uma automação; recebe o boletim arquivado pelo sistema do usuário.

## Organização

- config.json: protocolo e todos os candidatos efetivamente testados.
- resultados/robusto_v2/AAAA-MM: oito testes LOMO.
- resultados/robusto_v2/CRONO: treino até janeiro, teste fevereiro/março.
- resultados/robusto_v2/FINAL: quatro modelos finais, mais repetições de MLP/XGBoost.
- auditoria_final.json: verificação de assinaturas, períodos, previsões e convergência.
- schema_modelos_finais.json: entradas, unidades, domínios e caminhos dos modelos.
- treinamento.log: registro da execução integral.

Os arquivos .joblib exigem Python e as dependências especificadas; não são programas .exe autônomos.
