"""Evaluación con el mismo cupo diario: dólares de fraude que entran a la cola, intervalos pareados y curvas."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def seleccion(score: np.ndarray, dia: np.ndarray, k: int) -> np.ndarray:
    """Marca los k pagos de mayor puntaje de cada día. Empates: gana el pago anterior en el tiempo."""
    s = np.nan_to_num(np.asarray(score, float), nan=-np.inf)
    orden = np.lexsort((-s, dia))
    d = dia[orden]
    rango = np.arange(len(d)) - np.searchsorted(d, d, side="left")
    marca = np.zeros(len(d), bool)
    marca[orden[rango < k]] = True
    return marca


def por_dia(score, dia, y, monto, k) -> pd.Series:
    sel = seleccion(score, dia, k)
    return pd.Series(np.where(sel, y * monto, 0.0)).groupby(dia).sum()


def dinero(score, dia, y, monto, k) -> float:
    return float(por_dia(score, dia, y, monto, k).sum())


def matriz(score, dia, y, monto, k) -> dict:
    """Matriz de confusión en pagos y en dólares: revisado o no × fraude o legítimo."""
    sel = seleccion(score, dia, k)
    out = {}
    for s_nombre, s in (("revisado", sel), ("no_revisado", ~sel)):
        for y_nombre, yy in (("fraude", y == 1), ("legitimo", y == 0)):
            m = s & yy
            out[f"{s_nombre}_{y_nombre}"] = {"pagos": int(m.sum()), "usd": float(monto[m].sum())}
    out["precision"] = out["revisado_fraude"]["pagos"] / max(int(sel.sum()), 1)
    out["parte_usd_fraude"] = out["revisado_fraude"]["usd"] / max(float((y * monto).sum()), 1e-9)
    return out


def auc(y, p) -> float:
    return float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else float("nan")


def bootstrap(scores: dict[str, np.ndarray], dia, y, monto, k, replicas=1000, semilla=0) -> pd.DataFrame:
    """Réplicas pareadas por día: se remuestrean días con reemplazo, los mismos para todas las políticas. Dentro de
    cada día, la cola de cada política queda como se eligió. Devuelve el total de cada réplica."""
    dias = np.unique(dia)
    total = {n: por_dia(s, dia, y, monto, k).reindex(dias, fill_value=0.0).to_numpy() for n, s in scores.items()}
    idx = np.random.default_rng(semilla).integers(0, len(dias), size=(replicas, len(dias)))
    return pd.DataFrame({n: v[idx].sum(axis=1) for n, v in total.items()})


def contraste(rep: pd.DataFrame, a: str, b: str, puntual: dict[str, float]) -> dict:
    rel = rep[a] / rep[b] - 1
    dif = rep[a] - rep[b]
    return {"rel": puntual[a] / puntual[b] - 1, "dif": puntual[a] - puntual[b],
            "rel_ic95": [float(rel.quantile(0.025)), float(rel.quantile(0.975))],
            "dif_ic95": [float(dif.quantile(0.025)), float(dif.quantile(0.975))]}


def curva(score, dia, y, monto, fracciones) -> np.ndarray:
    """Dólares de fraude acumulados al revisar la fracción f de los pagos de cada día, en orden de puntaje."""
    s = np.nan_to_num(np.asarray(score, float), nan=-np.inf)
    out = np.zeros(len(fracciones))
    for d in np.unique(dia):
        m = dia == d
        v = (y * monto)[m][np.argsort(-s[m], kind="stable")]
        acum = np.concatenate([[0.0], np.cumsum(v)])
        out += acum[np.ceil(np.asarray(fracciones) * m.sum()).astype(int)]
    return out
