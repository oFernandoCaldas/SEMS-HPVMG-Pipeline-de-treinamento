"""Valida resultados gravados sem alterar modelos e gera auditoria e IC exploratórios."""
import json,itertools
from pathlib import Path
import numpy as np,pandas as pd,joblib
import sgie_pipeline as p
from executar import complete

def main():
    c=p.read_config();r=p.BASE/'resultados'/c['run_id']
    if p.signature()!=json.loads((r/'assinatura.json').read_text()):raise RuntimeError('Assinatura divergente')
    a=p.prepare(c);assert len(a)==5832 and a.E.sum()==2816 and a.M.sum()==2750
    assert a.loc[a.M,'baseline_timestamp'].le(a.loc[a.M,'emissao']).all()
    valid_models=0;allchoices=[];warnings_count=0;retry_count=0;invalid=0;fit_count=0;selected_warnings=[]
    for outer in list(sorted(a.mes.unique()))+['CRONO','FINAL']:
        train,test,folds=p.splits(a,outer,c)
        if test is not None:assert set(train.dia).isdisjoint(set(test.dia))
        for tr,va in folds:
            assert tr.index.max()<va.index.min()
            assert set(tr.dia).isdisjoint(set(va.dia))
            if test is not None:
                for bl in [tr,va]:assert not bl.loc[bl.M,'baseline_timestamp'].isin(test.index).any()
        for name in c['candidatos']:
            folder=r/outer/name;done=complete(folder);assert done
            allchoices.append({k:v for k,v in done.items() if k!='artefatos'})
            selected=done['candidato']
            search=pd.read_csv(folder/'busca.csv');assert len(search)==len(c['candidatos'][name]);invalid+=int((~search.valido).sum())
            for line in (folder/'diagnosticos.jsonl').read_text().splitlines():
                diag=json.loads(line);attempts=diag['tentativas'];fit_count+=len(attempts);retry_count+=max(0,len(attempts)-1)
                warnings_count+=sum(len(x.get('avisos',[])) for x in attempts)
                if diag['candidato']==selected:
                    assert diag['valido'];assert not attempts[-1].get('convergence_warning',False)
            for diag in json.loads((folder/'diagnosticos_reajuste.json').read_text()):fit_count+=len(diag['tentativas'])
            for seed in [c['semente_principal']]+(c['sementes_estabilidade'] if name in ['MLP','XGBoost'] else []):
                file='modelo.joblib' if seed==42 else f'modelo_seed_{seed}.joblib'
                model=joblib.load(folder/file);assert np.isfinite(model.predict(train.loc[train.E,c['features']])).all()
                if seed!=42:
                    dg=json.loads((folder/f'diagnostico_seed_{seed}.json').read_text());assert dg['valido'];fit_count+=len(dg['tentativas'])
                if test is not None:
                    predfile='predicoes_teste.csv' if seed==42 else f'predicoes_seed_{seed}.csv'
                    pred=pd.read_csv(folder/predfile);ix=p.index(pred.timestamp,c);assert ix.equals(test.index[test.M])
                    np.testing.assert_allclose(model.predict(test.loc[test.M,c['features']]),pred.prevista,rtol=1e-12,atol=1e-12)
                    if seed==42:
                        stored=pd.read_csv(folder/'metricas_externas.csv').query("papel=='teste'").iloc[0];met=p.metrics(pred.y,pred.prevista,pred.persistencia,c)
                        for key in ['RMSE_kWh','MAE_kWh','R2']:np.testing.assert_allclose(met[key],stored[key],rtol=1e-12,atol=1e-12)
                valid_models+=1
    pd.DataFrame(allchoices).to_csv(r/'configuracoes_todas.csv',index=False)
    # IC condicionais às previsões já geradas; não refaz a seleção nem prova superioridade universal.
    pred=pd.read_csv(r/'predicoes_lomo.csv');pred['dia']=pred.timestamp.str[:10]
    errors={}
    for name,g in pred.groupby('modelo'):
        g=g.copy();g['sq']=(g.prevista-g.y)**2;g['ab']=abs(g.prevista-g.y)
        errors[name]=g.groupby('dia').agg(sq=('sq','sum'),ab=('ab','sum'),n=('sq','size')).sort_index()
    names=list(errors);days=len(errors[names[0]]);rng=np.random.default_rng(20260914);sample_indices=[]
    for _ in range(2000):
        starts=rng.integers(0,days,size=int(np.ceil(days/7)));sample_indices.append(np.concatenate([(s+np.arange(7))%days for s in starts])[:days])
    res=[]
    for n1,n2 in itertools.combinations(names,2):
        x,y=errors[n1],errors[n2];assert x.index.equals(y.index);np.testing.assert_array_equal(x.n,y.n)
        boot=[]
        for ix in sample_indices:
            xx=x.iloc[ix];yy=y.iloc[ix];boot.append(np.sqrt(xx.sq.sum()/xx.n.sum())-np.sqrt(yy.sq.sum()/yy.n.sum()))
        lo,hi=np.percentile(boot,[2.5,97.5]);res.append({'modelo_A':n1,'modelo_B':n2,'diferenca_RMSE_A_menos_B':np.sqrt(x.sq.sum()/x.n.sum())-np.sqrt(y.sq.sum()/y.n.sum()),'IC95_inferior':lo,'IC95_superior':hi,'bloco_dias':7,'replicacoes':2000,'interpretacao':'exploratorio_condicional_sem_correcao_multiplas_comparacoes'})
    pd.DataFrame(res).to_csv(r/'incerteza_pareada.csv',index=False)
    old=p.BASE.parent/'SGIE_FINAL_Ago2024_Mar2025/resultados/openmeteo_final_ago2024_mar2025'
    if old.exists():
        current=pd.read_csv(r/'metricas_lomo_agrupadas.csv');prior=pd.read_csv(old/'metricas_agrupadas.csv');comp=current.merge(prior,on='modelo',suffixes=('_v2','_v1'))
        priorpred=pd.read_csv(old/'predicoes_externas_agrupadas.csv')
        for name,g in pred.groupby('modelo'):
            other=priorpred.query('modelo==@name');assert set(g.timestamp)==set(other.timestamp)
            joined=g.merge(other,on='timestamp');np.testing.assert_allclose(joined.y,joined.observado)
        cols=['modelo']
        for k in ['RMSE_kWh','MAE_kWh','R2']:
            comp[k+'_delta']=comp[k+'_v2']-comp[k+'_v1'];cols += [k+'_v1',k+'_v2',k+'_delta']
        comp[cols].to_csv(r/'comparacao_v1_v2.csv',index=False)
    audit={'status':'aprovado','modelos_verificados':valid_models,'horas':len(a),'amostras_ajuste':int(a.E.sum()),'amostras_metricas':int(a.M.sum()),'baseline_apos_emissao_nas_metricas':int((a.M&~a.baseline_disponivel_21h).sum()),'candidatos_invalidados':invalid,'avisos_buscas_todas_tentativas':warnings_count,'repeticoes_orcamento_busca':retry_count,'total_ajustes_reais':fit_count,'selecionados_convergentes_todos_folds':True,'nota':'ICs exploratorios condicionais; estabilidade de reajuste com parametros fixos; teste cronologico nao e novo conjunto intocado.'}
    p.dump(r/'auditoria_final.json',audit);print(json.dumps(audit,indent=2))
if __name__=='__main__':
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):main()
