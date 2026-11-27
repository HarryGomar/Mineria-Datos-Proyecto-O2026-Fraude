"""Sensibilidad del veredicto a la semilla de XGBoost. Posterior a la prueba: no cambia el protocolo ni su veredicto.

El resultado publicado sale de una corrida (semilla 0), y el bootstrap remuestrea días, no el entrenamiento. Aquí el
modelo final se reentrena con diez semillas en P1 y P2, con los mismos datos, variables e hiperparámetros, y se repiten
los tres contrastes. La regla no depende de la semilla y la logística se entrena una vez. Los dólares cambian con la
máquina: resultados/semillas.json guarda dónde se corrió y no coincide al centavo con resultados/prueba.json.
Uso: python scripts/10_semillas.py
"""
from __future__ import annotations

import json
import platform

import numpy as np
import xgboost as xgb
from sklearn.linear_model import LogisticRegression

from revisar.datos import bloque, cargar, verificar_fuente
from revisar.evaluacion import bootstrap, contraste, dinero
from revisar.politicas import XGB, Diseno, reglas
from revisar.rutas import RESULTADOS

SEL = json.loads((RESULTADOS / "desarrollo_seleccion.json").read_text(encoding="utf-8"))
PRUEBA = json.loads((RESULTADOS / "prueba.json").read_text(encoding="utf-8"))
FINAL, REGLA, LOGIT = SEL["final"], SEL["mejor_regla"], SEL["mejor_logit"]
MODELO, CONJ = FINAL.split("|")
LOGIT_C, CONJ_L = float(LOGIT.partition("|")[0].removeprefix("LOGIT_C")), LOGIT.partition("|")[2]
assert MODELO == "XGB" and CONJ_L == CONJ, "previsto para XGBoost y la logística sobre el mismo conjunto"
K, REPLICAS, SEMILLAS = 60, 1000, range(10)
PERIODOS = {"P1": (121, 151), "P2": (152, 182)}
UMBRAL = PRUEBA["umbrales"]

verificar_fuente()
df = cargar(183)
R = {"plataforma": platform.platform(), "semillas": list(SEMILLAS)}
for per, (ini, fin) in PERIODOS.items():
    tr, te = bloque(df, ini, fin)
    y, yt = tr["fraude"].to_numpy(), te["fraude"].to_numpy()
    m, d = te["TransactionAmt"].to_numpy(float), te["dia"].to_numpy()
    dis = Diseno(tr, CONJ)
    A, B = dis.matriz(tr), dis.matriz(te)
    fijos = {"regla": reglas(tr, te)[REGLA] * m,
             "logit": LogisticRegression(C=LOGIT_C, max_iter=3000).fit(A, y).predict_proba(B)[:, 1] * m}
    corridas = []
    for s in SEMILLAS:
        p = xgb.XGBClassifier(**{**XGB, "random_state": s}).fit(A, y).predict_proba(B)[:, 1]
        S = {"modelo": p * m, "pub": p, **fijos}
        usd = {n: dinero(v, d, yt, m, K) for n, v in S.items()}
        rep = bootstrap(S, d, yt, m, K, REPLICAS, semilla=ini)
        c = {n: contraste(rep, "modelo", n, usd) for n in ("regla", "logit", "pub")}
        corridas.append({"semilla": s, "usd": usd["modelo"], **{n: c[n]["rel"] for n in c},
                         **{f"{n}_inf": c[n]["rel_ic95"][0] for n in c},
                         "H1": bool(c["regla"]["rel"] >= UMBRAL["H1"] and c["regla"]["rel_ic95"][0] > 0),
                         "H2": bool(c["logit"]["rel"] >= UMBRAL["H2"] and c["logit"]["rel_ic95"][0] > 0),
                         "H3": bool(c["pub"]["rel_ic95"][0] > 0)})
        print(per, {k: round(v, 3) if isinstance(v, float) else v for k, v in corridas[-1].items()}, flush=True)
    R[per] = {"publicado": PRUEBA[per]["usd"][FINAL], "usd_regla": usd["regla"], "usd_logit": usd["logit"],
              "rango": {n: [float(f([c[n] for c in corridas])) for f in (min, np.median, max)] for n in ("usd", "regla", "logit", "pub")},
              "cumplen": {h: sum(c[h] for c in corridas) for h in ("H1", "H2", "H3")}, "corridas": corridas}
(RESULTADOS / "semillas.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
for per in PERIODOS:
    print(per, "publicado", round(R[per]["publicado"]), {n: [round(v, 3) for v in r] for n, r in R[per]["rango"].items()}, R[per]["cumplen"])
