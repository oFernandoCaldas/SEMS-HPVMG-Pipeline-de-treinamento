import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin, clone

class RegressorLimitado(RegressorMixin, BaseEstimator):
    def __init__(self, regressor):
        self.regressor = regressor
    def fit(self, X, y):
        self.maximo_ = float(np.max(y))
        self.regressor_ = clone(self.regressor)
        self.regressor_.fit(X,y)
        return self
    def predict_raw(self, X):
        pred = np.asarray(self.regressor_.predict(X),dtype=float).reshape(-1)
        if not np.isfinite(pred).all():
            raise FloatingPointError('Previsão não finita: não remover horários para recalcular métricas.')
        return pred
    def predict(self, X):
        return np.clip(self.predict_raw(X),0,self.maximo_)
