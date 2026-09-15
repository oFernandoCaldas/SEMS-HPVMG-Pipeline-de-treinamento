"""python executar.py --workers 6. Windows/Linux: spawn; --workers 1 sequencial."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import argparse,json,time,multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
import pandas as pd
import joblib
import sgie_pipeline as p

def complete(folder):
    f=folder/'concluido.json'
    if not f.exists():return False
    rec=json.loads(f.read_text())
    for name,h in rec['artefatos'].items():
        if not (folder/name).exists() or p.digest(folder/name)!=h:raise RuntimeError(f'Artefato alterado ou ausente: {folder/name}')
    return rec

def seal(folder,result):
    result['artefatos']={str(f.relative_to(folder)):p.digest(f) for f in folder.rglob('*') if f.is_file() and f.name!='concluido.json' and not f.name.endswith('.tmp')}
    p.dump(folder/'concluido.json',result)

def summary(block,role,fold):
    return {'fold':fold,'papel':role,'inicio':str(block.index.min()),'fim':str(block.index.max()),'dias':block.dia.nunique(),'n_ajuste':int(block.E.sum()),'n_metricas':int(block.M.sum())}

def run_task(outer,name):
    c=p.read_config();r=p.BASE/'resultados'/c['run_id'];folder=r/outer/name
    prior=complete(folder)
    if prior:return {'rodada':outer,'modelo':name,'retomado':True}
    folder.mkdir(parents=True,exist_ok=True);a=p.prepare(c);train,test,folds=p.splits(a,outer,c)
    rows=[];details=[];sd=[];dates=[]
    for k,(tr,va) in enumerate(folds,1):
        for role,block in [('treino',tr),('validacao',va)]:
            sd.append(summary(block,role,k));dates.extend({'fold':k,'papel':role,'dia':str(d)} for d in block.dia.unique())
    pd.DataFrame(sd).to_csv(folder/'divisoes_resumo.csv',index=False);pd.DataFrame(dates).to_csv(folder/'divisoes_dias.csv',index=False)
    print('INICIO',outer,name,flush=True)
    with (folder/'diagnosticos.jsonl').open('w') as log:
        for cid,params in enumerate(c['candidatos'][name]):
            score=[];valid=True
            for k,(tr,va) in enumerate(folds,1):
                model,diag=p.fit(name,params,tr,c,c['semente_principal'])
                log.write(json.dumps({'candidato':cid,'fold':k,**diag},default=str)+'\n');log.flush()
                if model is None:valid=False;break
                for role,block in [('treino',tr),('validacao',va)]:
                    met=p.evaluate(model,block,c);details.append({'candidato':cid,'fold':k,'papel':role,**met})
                    if role=='validacao':score.append(met['RMSE_kWh'])
            rows.append({'candidato':cid,'valido':valid,'RMSE_validacao':float(np.mean(score)) if valid else None,'parametros':json.dumps(params)})
            if (cid+1)%12==0:print('BUSCA',outer,name,cid+1,len(c['candidatos'][name]),flush=True)
    search=pd.DataFrame(rows);search.to_csv(folder/'busca.csv',index=False);pd.DataFrame(details).to_csv(folder/'metricas_internas.csv',index=False)
    eligible=search.loc[search.valido].sort_values(['RMSE_validacao','candidato'])
    if eligible.empty:raise RuntimeError(f'Nenhum candidato convergiu: {outer}/{name}')
    refits=[]
    # Fallback predefinido: próxima configuração por validação, nunca por teste.
    for row in eligible.itertuples():
        params=c['candidatos'][name][row.candidato];model,diag=p.fit(name,params,train,c,c['semente_principal']);refits.append({'candidato':row.candidato,**diag})
        if model is not None:break
    else:raise RuntimeError('Nenhum reajuste válido')
    p.dump(folder/'diagnosticos_reajuste.json',refits);joblib.dump(model,folder/'modelo.joblib',compress=3)
    metrics=[{'papel':'treino_reajuste',**p.evaluate(model,train,c)}]
    if test is not None:
        metrics.append({'papel':'teste',**p.evaluate(model,test,c)});p.predictions(model,test,c).to_csv(folder/'predicoes_teste.csv')
    pd.DataFrame(metrics).to_csv(folder/'metricas_externas.csv',index=False)
    stability=[]
    if name in ['MLP','XGBoost']:
        for seed in c['sementes_estabilidade']:
            sm,diag=p.fit(name,params,train,c,seed);p.dump(folder/f'diagnostico_seed_{seed}.json',diag)
            if sm is None:raise RuntimeError(f'Reajuste estabilidade sem convergência: {outer} {name} {seed}')
            joblib.dump(sm,folder/f'modelo_seed_{seed}.joblib',compress=3)
            stability.append({'semente':seed,'papel':'treino',**p.evaluate(sm,train,c)})
            if test is not None:
                stability.append({'semente':seed,'papel':'teste',**p.evaluate(sm,test,c)});p.predictions(sm,test,c).to_csv(folder/f'predicoes_seed_{seed}.csv')
        pd.DataFrame(stability).to_csv(folder/'estabilidade_metricas.csv',index=False)
    result={'rodada':outer,'modelo':name,'candidato':int(row.candidato),'parametros':params,'RMSE_validacao':float(row.RMSE_validacao),'candidatos_validos':int(search.valido.sum()),'candidatos_total':len(search),'semente_selecao':c['semente_principal'],'estabilidade':'reajuste_com_parametros_fixos_nao_reselecao' if name in ['MLP','XGBoost'] else 'deterministico'}
    seal(folder,result);print('CONCLUIDO',outer,name,json.dumps(result,ensure_ascii=False),flush=True)
    return {'rodada':outer,'modelo':name,'retomado':False}

def consolidate(c):
    r=p.BASE/'resultados'/c['run_id'];monthly=[];pieces=[];choices=[]
    for month in sorted(p.prepare(c).mes.unique()):
        for name in c['candidatos']:
            folder=r/month/name;done=complete(folder)
            if not done:raise RuntimeError(f'Rodada incompleta {folder}')
            choices.append({k:v for k,v in done.items() if k!='artefatos'})
            d=pd.read_csv(folder/'predicoes_teste.csv');d['modelo']=name;d['mes']=month;pieces.append(d)
            monthly.append({'mes':month,'modelo':name,**p.metrics(d.y,d.prevista,d.persistencia,c)})
    allpred=pd.concat(pieces);allpred.to_csv(r/'predicoes_lomo.csv',index=False)
    grouped=[]
    for name,d in allpred.groupby('modelo'):grouped.append({'modelo':name,**p.metrics(d.y,d.prevista,d.persistencia,c)})
    d=allpred.query("modelo=='KRR'");grouped.append({'modelo':'Persistencia24h',**p.metrics(d.y,d.persistencia,d.persistencia,c)})
    pd.DataFrame(grouped).to_csv(r/'metricas_lomo_agrupadas.csv',index=False);pd.DataFrame(monthly).to_csv(r/'metricas_lomo_mensais.csv',index=False);pd.DataFrame(choices).to_csv(r/'configuracoes_lomo.csv',index=False)
    stability=[]
    for name in ['MLP','XGBoost']:
        for seed in [c['semente_principal']]+c['sementes_estabilidade']:
            ds=[]
            for month in sorted(allpred.mes.unique()):
                filename='predicoes_teste.csv' if seed==c['semente_principal'] else f'predicoes_seed_{seed}.csv';ds.append(pd.read_csv(r/month/name/filename))
            d=pd.concat(ds);stability.append({'modelo':name,'semente':seed,**p.metrics(d.y,d.prevista,d.persistencia,c)})
    pd.DataFrame(stability).to_csv(r/'estabilidade_lomo.csv',index=False)
    crono=[]
    for name in c['candidatos']:
        d=pd.read_csv(r/'CRONO'/name/'predicoes_teste.csv');crono.append({'modelo':name,**p.metrics(d.y,d.prevista,d.persistencia,c)})
    crono.append({'modelo':'Persistencia24h',**p.metrics(d.y,d.persistencia,d.persistencia,c)})
    pd.DataFrame(crono).to_csv(r/'metricas_cronologicas.csv',index=False)
    daily=[];irr=[]
    allpred['dia']=allpred.timestamp.str[:10]
    for (name,day),d in allpred.groupby(['modelo','dia']):daily.append({'modelo':name,'dia':day,**p.metrics(d.y,d.prevista,d.persistencia,c)})
    allpred['faixa']=pd.cut(allpred.GHI,[-np.inf,200,500,800,np.inf],labels=['ate200','200a500','500a800','acima800'])
    for (name,band),d in allpred.groupby(['modelo','faixa'],observed=True):irr.append({'modelo':name,'faixa':str(band),**p.metrics(d.y,d.prevista,d.persistencia,c)})
    pd.DataFrame(daily).to_csv(r/'metricas_diarias.csv',index=False);pd.DataFrame(irr).to_csv(r/'metricas_faixas_GHI.csv',index=False)
    print(pd.DataFrame(grouped)[['modelo','RMSE_kWh','MAE_kWh','R2']].to_string(index=False),flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=1);args=ap.parse_args();c=p.read_config();r=p.BASE/'resultados'/c['run_id'];sig=p.signature()
    if r.exists():
        guard=r/'assinatura.json'
        if not guard.exists() or json.loads(guard.read_text())!=sig:raise RuntimeError('Dados, qualidade, configuração, código ou ambiente incompatíveis. Use novo run_id.')
    else:r.mkdir(parents=True);p.dump(r/'assinatura.json',sig)
    tic=time.time();a=p.prepare(c);a.to_csv(r/'auditoria_horaria.csv')
    a.groupby('mes').agg(horas=('E','size'),ajuste=('E','sum'),metricas=('M','sum'),positivos_excluidos_solar=('positivo_excluido_solar','sum')).to_csv(r/'cobertura_mensal.csv')
    jobs=[(month,name) for month in list(sorted(a.mes.unique()))+['CRONO','FINAL'] for name in c['candidatos']];errors=[];returned=[]
    if args.workers==1:
        for job in jobs:returned.append(run_task(*job))
    else:
        with ProcessPoolExecutor(max_workers=args.workers,mp_context=mp.get_context('spawn')) as pool:
            fs={pool.submit(run_task,*j):j for j in jobs}
            for f in as_completed(fs):
                try:returned.append(f.result())
                except Exception as e:errors.append({'rodada':fs[f],'erro':repr(e)});print('ERRO',fs[f],repr(e),flush=True)
    if errors:
        p.dump(r/'falhas.json',errors);raise RuntimeError(errors)
    consolidate(c)
    # Cada tentativa tem seu histórico; uma retomada não apaga o tempo original.
    history=r/'historico_execucoes.jsonl'
    with history.open('a') as f:f.write(json.dumps({'segundos':time.time()-tic,'tarefas':len(jobs),'retomadas':sum(x['retomado'] for x in returned)})+'\n')
    p.dump(r/'status.json',{'status':'concluido','tarefas':len(jobs),'erros':[],'consolidacao_completa':True})
    print('EXECUCAO COMPLETA',time.time()-tic,flush=True)
if __name__=='__main__':main()
