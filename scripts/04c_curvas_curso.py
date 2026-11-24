"""Curvas del capítulo 4 del curso ("La evaluación de modelos como herramienta financiera") con los puntajes ya guardados.

No entrena ni lee datos crudos: usa procesados/{desarrollo,prueba}_puntajes_*.parquet y escribe resultados/curvas_curso.json.
- ROC y precisión–recall de cada puntaje, con el punto de operación real: 60 revisiones por día.
- Paradoja de la exactitud: exactitud, precisión, recall, especificidad y F1 de cada cola, y de no revisar nada.
- Tabla de deciles con el orden de cada día: fraudes, dólares, lift y dólares esperados contra observados.
- Ganancia acumulada (cumulative gains) en fraudes y en dólares.
- Distribución de la probabilidad por clase (el "duelo" que mide el AUC).
- Curva de beneficio contra el umbral t de fraude esperado (p × monto): t se elige en desarrollo y se mide en la prueba.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from revisar.evaluacion import seleccion
from revisar.rutas import PROCESADOS, RESULTADOS

SEL = json.loads((RESULTADOS / "desarrollo_seleccion.json").read_text(encoding="utf-8"))
FINAL, REGLA, LOGIT = SEL["final"], SEL["mejor_regla"], SEL["mejor_logit"]
K = 60
POL = {"modelo": (FINAL, True), "solo_p": (FINAL, False), "logistica": (LOGIT, True), "regla": (REGLA, True), "monto": ("R_monto", True)}
COSTOS = (5, 10, 20, 50, 100)


def leer(nombres):
    return pd.concat([pd.read_parquet(PROCESADOS / f"{n}.parquet") for n in nombres], ignore_index=True)


def puntaje(d, pol):
    col, por_monto = POL[pol]
    p = d[col].to_numpy(float)
    return p * d["monto"].to_numpy(float) if por_monto else p


def rango_diario(s, dia):
    """Lugar de cada pago en la cola de su día (0 = primero) y tamaño del día. Empates: gana el anterior, como en seleccion()."""
    orden = np.lexsort((-np.nan_to_num(s, nan=-np.inf), dia))
    d = dia[orden]
    r = np.empty(len(s), int)
    r[orden] = np.arange(len(d)) - np.searchsorted(d, d, side="left")
    n = pd.Series(dia).map(pd.Series(dia).value_counts()).to_numpy()
    return r, n


def metricas(y, m, marca):
    tp, fp = int((marca & (y == 1)).sum()), int((marca & (y == 0)).sum())
    fn, tn = int((~marca & (y == 1)).sum()), int((~marca & (y == 0)).sum())
    prec = tp / (tp + fp) if tp + fp else None
    rec = tp / (tp + fn)
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn, "exactitud": (tp + tn) / len(y), "precision": prec, "recall": rec,
            "especificidad": tn / (tn + fp), "fpr": fp / (fp + tn), "f1": 2 * tp / (2 * tp + fp + fn),
            "usd": float((m * y)[marca].sum()), "revisiones": int(marca.sum())}


test, dev = leer(["prueba_puntajes_P1", "prueba_puntajes_P2"]), leer(["desarrollo_puntajes_D1", "desarrollo_puntajes_D2"])
y, m, dia = test["fraude"].to_numpy(int), test["monto"].to_numpy(float), test["dia"].to_numpy()
P, N = int(y.sum()), int((1 - y).sum())
out = {"dias": [int(dia.min()), int(dia.max())], "n_dias": int(len(np.unique(dia))), "pagos": int(len(y)), "fraudes": P,
       "prevalencia": P / len(y), "usd_fraude": float((y * m).sum())}

# ROC y precisión–recall sobre el orden global del periodo, más el punto de operación de 60 por día
grid = np.unique(np.concatenate([np.geomspace(1e-4, 1, 160), [1.0]]))
curvas, puntos, tabla = {}, {}, {}
for pol in POL:
    s = puntaje(test, pol)
    o = np.argsort(-s, kind="stable")
    tp = np.cumsum(y[o])
    idx = np.maximum(np.ceil(grid * len(y)).astype(int), 1) - 1
    TP, FP = tp[idx], idx + 1 - tp[idx]
    curvas[pol] = {"fpr": (FP / N).tolist(), "tpr": (TP / P).tolist(), "precision": (TP / (TP + FP)).tolist(),
                   "auc": float(roc_auc_score(y, s)), "ap": float(average_precision_score(y, s))}
    tabla[pol] = metricas(y, m, seleccion(s, dia, K))
tabla["nunca"] = metricas(y, m, np.zeros(len(y), bool))
out["curvas"], out["operacion"] = curvas, tabla
out["auc_por_periodo"] = {per: {pol: float(roc_auc_score(test["fraude"][f], puntaje(test[f], pol))) for pol in POL}
                          for per, f in (("P1", test["dia"] <= 151), ("P2", test["dia"] >= 152))}

# Ganancia acumulada con el orden de cada día: % de fraudes y % de dólares de fraude capturados
fr = np.unique(np.concatenate([np.arange(0, .05, .0025), np.arange(.05, .2, .01), np.arange(.2, 1.0001, .05)]).round(4))
ganancia = {}
for pol in ("modelo", "solo_p", "logistica", "regla", "monto"):
    r, n = rango_diario(puntaje(test, pol), dia)
    ganancia[pol] = {"fraccion": fr.tolist(),
                     "fraudes": [float(y[r < f * n].sum() / P) for f in fr],
                     "usd": [float((y * m)[r < f * n].sum() / out["usd_fraude"]) for f in fr]}
out["ganancia"] = ganancia
out["cupo_fraccion"] = K / (len(y) / out["n_dias"])

# Tabla de deciles del modelo, con el orden de cada día
s = puntaje(test, "modelo")
r, n = rango_diario(s, dia)
decil = np.minimum(r * 10 // n, 9) + 1
filas, acum_f, acum_u, acum_n = [], 0, 0.0, 0
for d in range(1, 11):
    f = decil == d
    nf, fu, nn = int(y[f].sum()), float((y * m)[f].sum()), int(f.sum())
    acum_f, acum_u, acum_n = acum_f + nf, acum_u + fu, acum_n + nn
    filas.append({"decil": d, "pagos": nn, "fraudes": nf, "tasa": nf / nn, "fraudes_acum": acum_f / P, "lift": (nf / nn) / out["prevalencia"],
                  "lift_acum": (acum_f / acum_n) / out["prevalencia"], "usd": fu, "usd_acum": acum_u / out["usd_fraude"],
                  "lift_usd": (fu / out["usd_fraude"]) / (nn / len(y)), "usd_esperado": float(s[f].sum()),
                  "esperado_medio": float(np.median(s[f]))})
out["deciles"] = filas

# Distribución de la probabilidad del modelo por clase, en escala logarítmica
p = test[FINAL].to_numpy(float)
bordes = np.linspace(-4, 0, 41)
lp = np.clip(np.log10(np.maximum(p, 1e-6)), -4, -1e-9)
out["distribucion"] = {"bordes": bordes.tolist(),
                       "fraude": (np.histogram(lp[y == 1], bordes)[0] / P).tolist(),
                       "legitimo": (np.histogram(lp[y == 0], bordes)[0] / N).tolist(),
                       "mediana_fraude": float(np.median(p[y == 1])), "mediana_legitimo": float(np.median(p[y == 0]))}

# Curva de beneficio contra el umbral t: revisar todo pago con fraude esperado p × monto ≥ t (sin cupo, como en el curso)
ts = np.geomspace(0.5, 5000, 181)
nd, nt = dev["dia"].nunique(), test["dia"].nunique()


def beneficio(d, pol, c):
    s = puntaje(d, pol)
    o = np.argsort(-s, kind="stable")
    fu = np.concatenate([[0.0], np.cumsum((d["fraude"] * d["monto"]).to_numpy(float)[o])])
    k = np.searchsorted(-s[o], -ts, side="right")  # pagos con s >= t
    return fu[k] - c * k, k


ben = {}
for pol in ("modelo", "logistica", "regla"):
    ben[pol] = {}
    for c in COSTOS:
        bd, _ = beneficio(dev, pol, c)
        bt, kt = beneficio(test, pol, c)
        i_dev, i_test = int(np.argmax(bd)), int(np.argmax(bt))
        ben[pol][str(c)] = {"t_dev": float(ts[i_dev]), "neto_prueba": float(bt[i_dev]), "revisiones_dia": float(kt[i_dev] / nt),
                            "t_prueba": float(ts[i_test]), "neto_max_prueba": float(bt[i_test]),
                            "curva": bt.tolist() if pol == "modelo" or c == 20 else None}
out["umbral"] = {"t": ts.tolist(), "costos": list(COSTOS), "politicas": ben}
cortes = pd.Series(s).groupby(dia).apply(lambda v: np.sort(v.to_numpy())[::-1][K - 1])
out["corte_60"] = {"mediana": float(cortes.median()), "p25": float(cortes.quantile(.25)), "p75": float(cortes.quantile(.75))}

(RESULTADOS / "curvas_curso.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
print("prueba", out["pagos"], "pagos", P, "fraudes", round(out["prevalencia"], 4), "días", out["n_dias"])
for pol in POL:
    t = tabla[pol]
    print(f"{pol:10s} AUC {curvas[pol]['auc']:.3f} AP {curvas[pol]['ap']:.3f} | 60/día: exact {t['exactitud']:.4f} prec {t['precision']:.3f} "
          f"rec {t['recall']:.3f} fpr {t['fpr']:.4f} f1 {t['f1']:.3f} usd {t['usd']:,.0f}")
print("nunca revisar: exactitud", round(tabla["nunca"]["exactitud"], 4))
print("deciles:", [(f["decil"], round(f["fraudes_acum"], 3), round(f["usd_acum"], 3), round(f["lift"], 1), round(f["lift_usd"], 1)) for f in filas])
print("corte diario de 60:", out["corte_60"])
for pol in ben:
    print(pol, {c: (round(v["t_dev"], 1), round(v["revisiones_dia"]), round(v["neto_prueba"]), round(v["t_prueba"], 1), round(v["neto_max_prueba"]))
                for c, v in ben[pol].items()})
