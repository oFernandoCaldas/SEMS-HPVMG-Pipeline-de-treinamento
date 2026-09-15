"""Gera relatório e notebook a partir da execução auditada; não retreina modelos."""
from pathlib import Path
import json
import pandas as pd
import nbformat as nb
import sgie_pipeline as p

def table(d,digits=6):
    d=d.copy()
    for col in d.columns:
        if pd.api.types.is_float_dtype(d[col]):d[col]=d[col].map(lambda v:f'{v:.{digits}f}' if pd.notna(v) else '')
    return '| '+' | '.join(d.columns)+' |\n| '+' | '.join(['---']*len(d.columns))+' |\n'+'\n'.join('| '+' | '.join(str(v).replace('|','/').replace('\n',' ') for v in row)+' |' for row in d.itertuples(index=False,name=None))

def main():
    c=p.read_config();r=p.BASE/'resultados'/c['run_id'];audit=json.loads((r/'auditoria_final.json').read_text())
    assert audit['status']=='aprovado'
    text='# SGIE V2: busca ampliada, emissão às 21h e avaliação auditada\n\n'
    text+='SystemProduction representa a produção de energia do sistema, conforme confirmação do usuário. Mantiveram-se os dados, as unidades declaradas no pacote, a exclusão de zeros, o filtro solar e o período de agosto/2024 a março/2025. 31/07 fornece somente a persistência inicial. Consulte PROTOCOLO.md para todas as decisões, fontes e limitações.\n\n'
    text+='## Execução e auditoria\n\n'+table(pd.DataFrame([{'item':k,'valor':v} for k,v in audit.items()]))+'\n\n'
    text+='O total de ajustes inclui buscas, novas tentativas de convergência, reajustes e estabilidade. Candidatos interrompidos por inelegibilidade podem executar menos de três divisões. A contagem efetiva deriva dos diagnósticos.\n\n'
    text+='## Cobertura e disponibilidade às 21h\n\n'+table(pd.read_csv(r/'cobertura_mensal.csv'))+'\n\n'
    text+='As 2.750 referências utilizadas nas métricas têm timestamp anterior ou igual à emissão de 21h do dia anterior. A latência real da telemetria não consta no histórico fornecido. Os valores das 22h e 23h do dia de emissão ainda não seriam conhecidos; eles não são utilizados nos horários elegíveis deste recorte.\n\n'
    for title,file in [('Teste LOMO agrupado','metricas_lomo_agrupadas.csv'),('Teste LOMO mensal','metricas_lomo_mensais.csv'),('Teste cronológico complementar','metricas_cronologicas.csv')]:
        d=pd.read_csv(r/file);cols=[x for x in ['mes','modelo','n','RMSE_kWh','MAE_kWh','R2','Skill_pct'] if x in d]
        text+='## '+title+'\n\n'+table(d[cols])+'\n\n'
    text+='O LOMO pode usar meses posteriores ao mês testado. O teste cronológico treina até janeiro e avalia fevereiro/março, mas é exploratório porque os dados já foram inspecionados antes. Ambos usam meteorologia histórica, não boletins futuros arquivados.\n\n'
    if (r/'comparacao_v1_v2.csv').exists():text+='## Comparação com V1 nas mesmas 2.750 amostras\n\n'+table(pd.read_csv(r/'comparacao_v1_v2.csv'))+'\n\n'
    text+='## Estabilidade com parâmetros selecionados fixos\n\n'+table(pd.read_csv(r/'estabilidade_lomo.csv')[['modelo','semente','RMSE_kWh','MAE_kWh','R2']])+'\n\n'
    text+='Não se escolheu a melhor semente. Esses resultados avaliam a inicialização/aleatoriedade dos reajustes, não a estabilidade de novas buscas completas. KRR e SVR são determinísticos neste protocolo.\n\n'
    text+='## Diferenças pareadas de RMSE\n\n'+table(pd.read_csv(r/'incerteza_pareada.csv').drop(columns=['interpretacao']))+'\n\n'
    text+='Diferença negativa favorece A. Intervalos que incluem zero não permitem uma direção consistente nesta análise. Bootstrap circular em blocos de sete dias, 2.000 réplicas; intervalos condicionais exploratórios, sem correção para múltiplas comparações nem reexecução dos ajustes.\n\n'
    text+='## Modelos finais exportados\n\n'
    finals=[];schema={}
    for name in c['candidatos']:
        f=r/'FINAL'/name;done=json.loads((f/'concluido.json').read_text());m=pd.read_csv(f/'metricas_externas.csv').iloc[0]
        finals.append({'modelo':name,'RMSE_validacao_interna':done['RMSE_validacao'],'RMSE_treino':m.RMSE_kWh,'MAE_treino':m.MAE_kWh,'R2_treino':m.R2,'parametros':json.dumps(done['parametros'])})
        schema[name]={'modelo':str((f/'modelo.joblib').relative_to(p.BASE)),'sha256':p.digest(f/'modelo.joblib'),'parametros':done['parametros'],'features':c['features'],'unidades':['W/m²','°C','m/s'],'alvo':'SystemProduction','unidade_alvo':'kWh conforme pacote de origem','inicio':c['inicio'],'fim_exclusivo':c['fim_exclusivo'],'emissao_hora_local':21,'semente':42,'dominio_avaliado':'geracao_positiva_zenite_meio_intervalo_le90_persistencia_positiva_disponivel'}
    text+=table(pd.DataFrame(finals))+'\n\n'
    text+='As métricas de treino dos modelos finais não representam teste independente. A seleção final utiliza validações internas e o reajuste usa todas as amostras elegíveis. Os modelos LOMO são diferentes dos quatro modelos finais.\n\n'
    text+='## Resultados complementares\n\n'+table(pd.read_csv(r/'metricas_faixas_GHI.csv')[['modelo','faixa','n','RMSE_kWh','MAE_kWh','R2','Skill_pct']])+'\n\n'
    daily=pd.read_csv(r/'metricas_diarias.csv');text+='### Resumo diário\n\n'+table(daily.groupby('modelo').agg(dias=('dia','size'),RMSE_min=('RMSE_kWh','min'),RMSE_max=('RMSE_kWh','max')).reset_index())+'\n\n'
    text+='As métricas completas de cada dia estão em metricas_diarias.csv. Cada pasta de rodada contém todos os candidatos, métricas internas de treino/validação, diagnósticos de convergência, datas, previsões, modelos e hashes.\n\n'
    text+='## Limites preservados\n\nNão se demonstrou ótimo global dos algoritmos. Os orçamentos de busca são distintos e explícitos. A escolha do período e a revisão das buscas ocorreram após resultados anteriores. O filtro de ponto médio continua excluindo intervalos parcialmente solares; estes não recebem validação implícita pela melhoria dos resultados. O esclarecimento de SystemProduction não resolve isoladamente a causa de valores positivos noturnos. A operação futura requer validação com boletins disponíveis às 21h e telemetria com horários reais de disponibilidade.\n'
    (p.BASE/'RESULTADOS.md').write_text(text);p.dump(p.BASE/'schema_modelos_finais.json',schema)
    readme='''# SGIE ROBUSTO V2

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
'''
    (p.BASE/'README.md').write_text(readme)
    notebook=nb.v4.new_notebook();notebook.metadata.kernelspec={'name':'python3','display_name':'Python 3','language':'python'}
    notebook.cells=[nb.v4.new_markdown_cell('# SGIE ROBUSTO V2\n\nExecução com dados Open-Meteo e Huawei, agosto/2024 a março/2025. Emissão operacional às 21h; zeros excluídos. Extraia o ZIP completo.\n\nAs células desta entrega foram executadas em processo IPython local. O treinamento real foi executado pelo script executar.py; as saídas abaixo leem os resultados auditados.'),nb.v4.new_code_cell("from pathlib import Path\nimport json, subprocess, sys\nimport pandas as pd\nfrom IPython.display import display\nimport sgie_pipeline as p\nc = p.read_config()\nR = p.BASE / 'resultados' / c['run_id']\nEXECUTAR_TREINAMENTO = False\nif EXECUTAR_TREINAMENTO:\n    subprocess.run([sys.executable, 'executar.py', '--workers', '6'], check=True)\nassert json.loads((R/'assinatura.json').read_text()) == p.signature()\nprint(json.loads((R/'auditoria_final.json').read_text()))"),nb.v4.new_code_cell("display(pd.read_csv(R/'cobertura_mensal.csv'))\ndisplay(pd.read_csv(R/'metricas_lomo_agrupadas.csv'))\ndisplay(pd.read_csv(R/'metricas_lomo_mensais.csv'))"),nb.v4.new_code_cell("display(pd.read_csv(R/'metricas_cronologicas.csv'))\ndisplay(pd.read_csv(R/'estabilidade_lomo.csv'))\ndisplay(pd.read_csv(R/'incerteza_pareada.csv'))\nif (R/'comparacao_v1_v2.csv').exists():\n    display(pd.read_csv(R/'comparacao_v1_v2.csv'))"),nb.v4.new_code_cell("for nome in c['candidatos']:\n    f = R/'FINAL'/nome\n    d = json.loads((f/'concluido.json').read_text())\n    print(nome, d['parametros'], 'RMSE de seleção interna:', d['RMSE_validacao'])\n    display(pd.read_csv(f/'metricas_externas.csv'))"),nb.v4.new_markdown_cell('O teste cronológico é exploratório, com meteorologia histórica. A estabilidade mede reajustes com parâmetros fixos. Os ICs são condicionais às previsões. Consulte PROTOCOLO.md antes de usar resultados no artigo.')]
    nb.write(notebook,p.BASE/'Pipeline_SGIE_ROBUSTO_V2.ipynb')
    from integrar_graficos import integrar
    integrar()
    print('Relatório, schema e notebook criados.')
if __name__=='__main__':main()
