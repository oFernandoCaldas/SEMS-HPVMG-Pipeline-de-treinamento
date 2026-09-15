"""Funções puras de preparação, ajuste e avaliação. Importar não grava arquivos."""
from pathlib import Path
import json,time,warnings,hashlib,platform,importlib.metadata
import numpy as np
import pandas as pd
import pvlib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import TransformedTargetRegressor
from sklearn.kernel_ridge import KernelRidge
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score
from xgboost import XGBRegressor
from threadpoolctl import threadpool_limits
from sgie_estimators import RegressorLimitado
BASE=Path(__file__).resolve().parent

def read_config():return json.loads((BASE/'config.json').read_text())
def digest(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def environment():
    return {'python':platform.python_version(),'bibliotecas':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','scikit-learn','xgboost','pvlib','joblib','threadpoolctl']}}
def signature():
    files=['config.json','sgie_pipeline.py','sgie_estimators.py','executar.py','dados/dados_geracao.csv','dados/open_meteo_convertido.csv']
    q=BASE/'dados/qualidade_geracao.csv'
    if q.exists():files.append(str(q.relative_to(BASE)))
    return {'sha256':{s:digest(BASE/s) for s in files},'qualidade_presente':q.exists(),'ambiente':environment()}
def dump(path,obj):
    path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)))
    tmp.replace(path)
def index(values,c):
    t=pd.DatetimeIndex(pd.to_datetime(values))
    return t.tz_localize(c['timezone']) if t.tz is None else t.tz_convert(c['timezone'])
def prepare(c):
    g=pd.read_csv(BASE/'dados/dados_geracao.csv');m=pd.read_csv(BASE/'dados/open_meteo_convertido.csv')
    g.index=index(pd.to_datetime(g['Date-Hour(NMT)'],format='%d.%m.%Y-%H:%M'),c)
    m.index=index(m.pop('timestamp'),c)
    if not g.index.is_unique or not m.index.is_unique:raise ValueError('Horários duplicados')
    start=pd.Timestamp(c['inicio'],tz=c['timezone']);end=pd.Timestamp(c['fim_exclusivo'],tz=c['timezone'])
    for x in [g,m]:
        if x.index.min()!=start-pd.Timedelta(days=1) or x.index.max()!=end-pd.Timedelta(hours=1):raise ValueError('Recorte dos CSVs incompatível')
        if not x.index.equals(pd.date_range(start-pd.Timedelta(days=1),end,freq='h',inclusive='left')):raise ValueError('Grade de entrada incompleta/desordenada')
    g['y']=pd.to_numeric(g.SystemProduction,errors='coerce');g['status']=''
    q=BASE/'dados/qualidade_geracao.csv'
    if q.exists():
        qd=pd.read_csv(q).fillna('');qd.index=index(qd.pop('timestamp'),c)
        if not qd.index.is_unique or not qd.index.isin(g.index).all():raise ValueError('Arquivo de qualidade inválido')
        if not qd.status.isin(['valido','suspeito','ausente','desconhecido']).all():raise ValueError('Status desconhecido')
        g.loc[qd.index,'status']=qd.status
    # Regra explícita solicitada: zero excluído inclusive como referência.
    g['valid']=np.isfinite(g.y)&g.y.gt(0)&~g.status.isin(['suspeito','ausente','desconhecido'])
    ix=pd.date_range(start,end,freq='h',inclusive='left');a=m.reindex(ix).join(g[['y','status','valid']].reindex(ix));a.index.name='timestamp'
    for f in c['features']:a[f]=pd.to_numeric(a[f],errors='coerce')
    a['zenite']=pvlib.solarposition.get_solarposition(ix-pd.Timedelta(minutes=30),latitude=c['latitude'],longitude=c['longitude'],altitude=c['altitude'])['zenith'].to_numpy()
    a['meteo_valida']=np.isfinite(a[c['features']]).all(axis=1)&a.GHI.ge(0)&a.WindSpeed.ge(0)
    a['E']=a.valid&a.meteo_valida&a.zenite.le(90)
    a['baseline_timestamp']=ix-pd.Timedelta(hours=24)
    prev=g.reindex(pd.DatetimeIndex(a.baseline_timestamp))
    a['persistencia']=prev.y.to_numpy();a['baseline_valid']=prev.valid.fillna(False).to_numpy()
    a['emissao']=ix.normalize()-pd.Timedelta(days=1)+pd.Timedelta(hours=c['emissao_hora'])
    a['baseline_disponivel_21h']=a.baseline_timestamp.le(a.emissao)
    a['M']=a.E&a.baseline_valid&a.baseline_disponivel_21h
    a['dia']=ix.normalize();a['mes']=ix.strftime('%Y-%m')
    a['positivo_excluido_solar']=a.valid&a.zenite.gt(90)
    return a

def internal_folds(train,c):
    days=pd.DatetimeIndex(train.dia.unique()).sort_values();chunks=np.array_split(np.arange(len(days)),4);out=[]
    # Referências só podem vir do período externo permitido ou do dia inicial de baseline.
    initial=pd.Timestamp(c['inicio'],tz=c['timezone'])-pd.Timedelta(days=1)
    allowed=set(train.index)|set(pd.date_range(initial,periods=24,freq='h'))
    for k in range(1,4):
        tr=train.loc[train.dia.isin(days[np.concatenate(chunks[:k])])].copy();va=train.loc[train.dia.isin(days[chunks[k]])].copy()
        for block in [tr,va]:block['M']=block.M&block.baseline_timestamp.isin(allowed)
        if not tr.index.max()<va.index.min():raise ValueError('Treino interno posterior à validação')
        if tr.loc[tr.E,'dia'].nunique()<14 or va.loc[va.M,'dia'].nunique()<7:raise ValueError('Cobertura insuficiente')
        out.append((tr,va))
    return out

def splits(a,name,c):
    if name=='FINAL':return a,None,internal_folds(a,c)
    if name=='CRONO':
        cut=pd.Timestamp(c['corte_cronologico'],tz=c['timezone']);train=a.loc[a.index<cut];test=a.loc[a.index>=cut]
        # Última geração de ajuste conhecida antes da primeira emissão do teste.
        first_issuance=test.emissao.min()
        if (train.index[train.E]>first_issuance).any():raise ValueError('Treino indisponível na primeira emissão')
    else:train=a.loc[a.mes.ne(name)];test=a.loc[a.mes.eq(name)]
    if set(train.dia)&set(test.dia):raise ValueError('Dias de teste no treino')
    return train,test,internal_folds(train,c)

def factory(name,params,c,seed,cap):
    if name=='KRR':est=KernelRidge(**params)
    elif name=='SVR':est=SVR(**params,cache_size=256,tol=1e-3,max_iter=-1)
    elif name=='MLP':est=MLPRegressor(**params,solver='adam',max_iter=cap,tol=c['mlp_tol'],n_iter_no_change=c['mlp_n_iter_no_change'],early_stopping=False,shuffle=True,random_state=seed)
    else:est=XGBRegressor(**params,objective='reg:squarederror',tree_method='hist',n_jobs=1,random_state=seed,verbosity=0)
    return RegressorLimitado(TransformedTargetRegressor(regressor=Pipeline([('scaler_X',StandardScaler()),('modelo',est)]),transformer=StandardScaler()))

def fit(name,params,block,c,seed):
    tr=block.loc[block.E];attempts=[]
    for cap in (c['mlp_orcamentos_iteracoes'] if name=='MLP' else [None]):
        model=factory(name,params,c,seed,cap);tic=time.perf_counter()
        try:
            with threadpool_limits(limits=1),warnings.catch_warnings(record=True) as ws:
                warnings.simplefilter('always');model.fit(tr[c['features']],tr.y)
            est=model.regressor_.regressor_.named_steps['modelo']
            conv=any(issubclass(w.category,ConvergenceWarning) for w in ws)
            numerical=any(issubclass(w.category,(RuntimeWarning,np.exceptions.RankWarning)) or 'LinAlgWarning' in w.category.__name__ for w in ws)
            d={'max_iter':cap,'segundos':time.perf_counter()-tic,'n_iter':getattr(est,'n_iter_',None),'avisos':[str(w.message) for w in ws],'convergence_warning':conv,'numerical_warning':numerical,'loss':getattr(est,'loss_',None),'loss_curve':getattr(est,'loss_curve_',None)}
            attempts.append(d)
            if numerical:return None,{'valido':False,'tentativas':attempts,'motivo':'aviso_numerico'}
            if conv:continue
            np.testing.assert_allclose(model.regressor_.regressor_.named_steps['scaler_X'].mean_,tr[c['features']].mean(),rtol=1e-10,atol=1e-10)
            np.testing.assert_allclose(model.regressor_.transformer_.mean_,[tr.y.mean()])
            model.predict(tr[c['features']])
            return model,{'valido':True,'tentativas':attempts,'maximo_treino':model.maximo_,'parametros_efetivos':{k:v for k,v in est.get_params().items() if not (isinstance(v,float) and np.isnan(v))}}
        except (ValueError,FloatingPointError,np.linalg.LinAlgError) as exc:
            attempts.append({'erro':repr(exc),'segundos':time.perf_counter()-tic});return None,{'valido':False,'tentativas':attempts,'motivo':'erro_numerico'}
    return None,{'valido':False,'tentativas':attempts,'motivo':'sem_convergencia_no_orcamento'}

def metrics(y,p,b,c):
    y,p,b=map(lambda v:np.asarray(v,dtype=float),(y,p,b))
    if len(y)<2 or not all(np.isfinite(x).all() for x in [y,p,b]):raise ValueError('População inválida para métricas')
    rm=mean_squared_error(y,p)**.5;ma=mean_absolute_error(y,p);rb=mean_squared_error(y,b)**.5;mean=y.mean()
    return {'n':len(y),'RMSE_kWh':rm,'MAE_kWh':ma,'R2':r2_score(y,p) if np.var(y)>0 else None,'MBE_kWh':float((p-y).mean()),'Pearson':float(np.corrcoef(y,p)[0,1]) if np.std(p)>0 and np.std(y)>0 else None,'nRMSE_media_pct':100*rm/mean,'nMAE_media_pct':100*ma/mean,'nRMSE_capacidade_pct':100*rm/c['capacidade_referencia_kWh'],'nMAE_capacidade_pct':100*ma/c['capacidade_referencia_kWh'],'nMBE_pct':100*float((p-y).sum())/y.sum(),'Skill_pct':100*(1-rm/rb) if rb>0 else None,'energia_medida_recorte_kWh':float(y.sum()),'energia_prevista_recorte_kWh':float(p.sum()),'RMSE_persistencia_kWh':rb}

def evaluate(model,block,c):
    s=block.loc[block.M];raw=model.predict_raw(s[c['features']]);pred=model.predict(s[c['features']]);m=metrics(s.y,pred,s.persistencia,c)
    m.update(n_limitadas=int(np.count_nonzero(raw!=pred)),RMSE_bruta_kWh=mean_squared_error(s.y,raw)**.5)
    return m

def predictions(model,block,c):
    s=block.loc[block.M];out=s[['y','persistencia','GHI','baseline_timestamp','emissao']].copy();out['bruta']=model.predict_raw(s[c['features']]);out['prevista']=model.predict(s[c['features']]);return out
