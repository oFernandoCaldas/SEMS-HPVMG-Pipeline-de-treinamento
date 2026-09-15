"""Verificações de integridade temporal e do contrato operacional, sem treinamento."""
import numpy as np,pandas as pd
import sgie_pipeline as p
from prever_21h import predict_day
class ModeloTeste:
    def predict(self,x):return np.full(len(x),1.0)
def main():
    c=p.read_config();a=p.prepare(c)
    assert a.E.sum()==2816 and a.M.sum()==2750
    assert a.index.min()==pd.Timestamp('2024-08-01',tz=c['timezone'])
    assert a.index.max()==pd.Timestamp('2025-03-31 23:00',tz=c['timezone'])
    assert (a.loc[a.M,'persistencia']>0).all()
    for outer in list(sorted(a.mes.unique()))+['CRONO','FINAL']:
        tr,te,folds=p.splits(a,outer,c)
        for train,val in folds:
            assert train.index.max()<val.index.min()
            if te is not None:
                assert not train.index.isin(te.index).any()
                assert not val.index.isin(te.index).any()
                assert not val.loc[val.M,'baseline_timestamp'].isin(te.index).any()
    ix=pd.date_range('2026-09-04',periods=24,freq='h',tz=c['timezone'])
    f=pd.DataFrame({'timestamp':ix,'issued_at':'2026-09-03T20:00:00-03:00','GHI':100.,'AirTemperature':20.,'WindSpeed':1.})
    out=predict_day(ModeloTeste(),f,'2026-09-03T21:00:00-03:00',c)
    assert len(out)==24 and np.isfinite(out.previsao_operacional_kWh).all()
    assert out.horizonte_horas.min()==3 and out.horizonte_horas.max()==26
    assert out.baseline_timestamp_disponivel.sum()==22
    for bad in [f.assign(issued_at='2026-09-03T22:00:00-03:00'),f.iloc[:-1],f.assign(GHI=-1.)]:
        try:predict_day(ModeloTeste(),bad,'2026-09-03T21:00:00-03:00',c)
        except ValueError:pass
        else:raise AssertionError('Entrada inválida não foi rejeitada')
    print('APROVADO: recorte, zeros, separação temporal e rejeição de boletim futuro/incompleto/inválido.')
    print('Dados meteorológicos sintéticos usados somente para teste de contrato; não são validação de previsão.')
if __name__=='__main__':main()
