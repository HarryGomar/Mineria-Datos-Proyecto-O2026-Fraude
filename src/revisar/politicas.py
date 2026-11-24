"""Políticas de la cola de revisión. Hiperparámetros fijos, escritos antes del torneo de desarrollo."""
from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.sparse as sp
import xgboost as xgb
from joblib import Parallel, delayed
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import OneHotEncoder, QuantileTransformer
from sklearn.tree import DecisionTreeClassifier

from .datos import CONJUNTOS

HILOS = 16
XGB = dict(n_estimators=600, max_depth=8, learning_rate=0.05, subsample=0.8, colsample_bytree=0.5, tree_method="hist",
           eval_metric="logloss", random_state=0, n_jobs=HILOS)
RF = dict(n_estimators=300, min_samples_leaf=5, max_features=0.3, n_jobs=HILOS, random_state=0)
CART = dict(max_depth=3, min_samples_leaf=200, random_state=0)
MLP = dict(hidden_layer_sizes=(64, 32), alpha=1e-4, batch_size=512, learning_rate_init=1e-3, max_iter=30,
           early_stopping=True, validation_fraction=0.1, n_iter_no_change=4, random_state=0)
ISO = dict(n_estimators=200, random_state=0, n_jobs=HILOS)
CS = (0.001, 0.003, 0.01, 0.03, 0.1)
SUAVIZADO = 50
FLEXIBLES = ("CART", "RF", "XGB", "XGB_pond", "MLP", "ENS")
REGLAS = ("R_monto", "R_tarjeta", "R_segmento", "R_correo", "R_tabla", "R_velocidad")


class Diseno:
    """Matriz única para logística, XGBoost y red (cuantiles + faltantes + una columna por categoría con al
    menos 50 casos) y matriz nativa para árboles de sklearn (numéricas crudas + frecuencia de cada categoría)."""

    def __init__(self, tr: pd.DataFrame, conjunto: str):
        self.num, self.cat = CONJUNTOS[conjunto]
        X = tr[self.num].to_numpy(float)
        self.mediana = np.nanmedian(X, axis=0)
        self.mediana = np.where(np.isnan(self.mediana), 0.0, self.mediana)
        self.qt = QuantileTransformer(n_quantiles=200, output_distribution="normal", subsample=200_000, random_state=0)
        self.qt.fit(np.where(np.isnan(X), self.mediana, X))
        self.oh = OneHotEncoder(min_frequency=50, handle_unknown="infrequent_if_exist", sparse_output=True).fit(tr[self.cat])
        self.frec = {c: tr[c].value_counts() for c in self.cat}
        self.nombres = self.num + [f"falta_{c}" for c in self.num] + list(self.oh.get_feature_names_out(self.cat))
        self.nombres_nativa = self.num + self.cat

    def matriz(self, d: pd.DataFrame) -> sp.csr_matrix:
        X = d[self.num].to_numpy(float)
        falta = np.isnan(X)
        Z = self.qt.transform(np.where(falta, self.mediana, X))
        return sp.hstack([sp.csr_matrix(Z), sp.csr_matrix(falta.astype(float)), self.oh.transform(d[self.cat])]).tocsr()

    def nativa(self, d: pd.DataFrame) -> np.ndarray:
        partes = [d[self.num].to_numpy(float)] + [d[c].map(self.frec[c]).fillna(0).to_numpy(float)[:, None] for c in self.cat]
        return np.nan_to_num(np.hstack(partes), nan=-999.0)


def _clave(d: pd.DataFrame, campos: list[str]) -> pd.Series:
    k = d[campos[0]].astype(str)
    for c in campos[1:]:
        k = k + "|" + d[c].astype(str)
    return k


def _tasa(ktr: pd.Series, ytr: np.ndarray, kte: pd.Series) -> np.ndarray:
    prior = ytr.mean()
    g = pd.DataFrame({"k": ktr.to_numpy(), "y": ytr}).groupby("k")["y"].agg(["sum", "count"])
    tasa = (g["sum"] + SUAVIZADO * prior) / (g["count"] + SUAVIZADO)
    return kte.map(tasa).fillna(prior).to_numpy(float)


def _tramos(x: pd.Series, cortes: list[float]) -> pd.Series:
    return pd.Series(np.searchsorted(cortes, x.fillna(0).to_numpy(), side="right"), index=x.index).astype(str)


def reglas(tr: pd.DataFrame, te: pd.DataFrame) -> dict[str, np.ndarray]:
    """Tasa de fraude histórica (suavizada) de cada regla; el puntaje es tasa × monto. R_monto: tasa constante."""
    ytr = tr["fraude"].to_numpy()
    out = {"R_monto": np.ones(len(te))}
    for nombre, campos in (("R_tarjeta", ["card1"]), ("R_segmento", ["ProductCD", "card4", "card6", "DeviceType"]),
                           ("R_correo", ["P_emaildomain", "ProductCD"])):
        out[nombre] = _tasa(_clave(tr, campos), ytr, _clave(te, campos))
    cortes = list(np.quantile(tr["TransactionAmt"], np.linspace(0, 1, 11)[1:-1]))
    dec = lambda d: d["ProductCD"] + "|" + _tramos(d["TransactionAmt"], cortes)  # noqa: E731
    out["R_tabla"] = _tasa(dec(tr), ytr, dec(te))
    vel = lambda d: (d["ProductCD"] + "|" + _tramos(d["h_tarjeta_dir_previos"], [0.5, 2.5, 9.5])  # noqa: E731
                     + "|" + _tramos(d["h_tarjeta_dir_ultimo_dia"], [0.5, 1.5]))
    out["R_velocidad"] = _tasa(vel(tr), ytr, vel(te))
    return out


def _logit(C, A, y, B):
    return LogisticRegression(C=C, max_iter=3000).fit(A, y).predict_proba(B)[:, 1]


def _mlp(A, y, B):
    return MLPClassifier(**MLP).fit(A, y).predict_proba(B)[:, 1]


def modelos(tr: pd.DataFrame, te: pd.DataFrame, conjunto: str, cuales: tuple[str, ...]) -> dict[str, np.ndarray]:
    """Probabilidad de fraude de cada pago de te. ISO devuelve el percentil de rareza (no es probabilidad)."""
    dis = Diseno(tr, conjunto)
    y = tr["fraude"].to_numpy()
    A, B = dis.matriz(tr), dis.matriz(te)
    out = {}
    lentos = [(f"LOGIT_C{c}", delayed(_logit)(c, A, y, B)) for c in CS if "LOGIT" in cuales]
    if "MLP" in cuales:
        lentos.append(("MLP", delayed(_mlp)(A, y, B)))
    if lentos:
        res = Parallel(n_jobs=len(lentos), backend="loky")(t for _, t in lentos)
        out.update({n: p for (n, _), p in zip(lentos, res)})
    if {"XGB", "ENS"} & set(cuales):
        out["XGB"] = xgb.XGBClassifier(**XGB).fit(A, y).predict_proba(B)[:, 1]
    if "XGB_pond" in cuales:
        w = tr["TransactionAmt"].to_numpy(float)
        out["XGB_pond"] = xgb.XGBClassifier(**XGB).fit(A, y, sample_weight=w / w.mean()).predict_proba(B)[:, 1]
    if {"RF", "CART", "ISO", "ENS"} & set(cuales):
        Na, Nb = dis.nativa(tr), dis.nativa(te)
        if {"RF", "ENS"} & set(cuales):
            out["RF"] = RandomForestClassifier(**RF).fit(Na, y).predict_proba(Nb)[:, 1]
        if "CART" in cuales:
            out["CART"] = DecisionTreeClassifier(**CART).fit(Na, y).predict_proba(Nb)[:, 1]
        if "ISO" in cuales:
            rareza = -IsolationForest(**ISO).fit(Na).score_samples(Nb)
            out["ISO"] = pd.Series(rareza).rank(pct=True).to_numpy()
    if "ENS" in cuales:
        out["ENS"] = (out["XGB"] + out["RF"]) / 2
    return {k: v for k, v in out.items() if k in cuales or k.startswith("LOGIT")}


def puntaje(nombre: str, p: np.ndarray, monto: np.ndarray, modo: str = "p_x_monto") -> np.ndarray:
    """Orden de la cola: probabilidad × monto (por defecto) o solo probabilidad. R_monto ordena por monto."""
    if nombre == "R_monto":
        return monto.copy()
    return p * monto if modo == "p_x_monto" else p.copy()
