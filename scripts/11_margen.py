"""Sensibilidad al margen de la etiqueta. Posterior a la prueba: no cambia el protocolo ni su veredicto.

El protocolo supone que la etiqueta madura en 30 días; Vesta la da por definitiva a los 120. Aquí el modelo final, la
mejor logística y la mejor regla se reentrenan para P1 y P2 con márgenes de 30, 45, 60 y 90 días, con la semilla del
protocolo. Con seis meses de datos, más margen también es menos entrenamiento: los dos efectos van juntos. Los dólares
cambian con la máquina, igual que en scripts/10_semillas.py.
Uso: python scripts/11_margen.py
"""
from __future__ import annotations

import json
import platform

import xgboost as xgb
from sklearn.linear_model import LogisticRegression

from revisar.datos import bloque, cargar, verificar_fuente
from revisar.evaluacion import bootstrap, contraste, dinero
from revisar.politicas import XGB, Diseno, reglas
from revisar.rutas import RESULTADOS

SEL = json.loads((RESULTADOS / "desarrollo_seleccion.json").read_text(encoding="utf-8"))
FINAL, REGLA, LOGIT = SEL["final"], SEL["mejor_regla"], SEL["mejor_logit"]
MODELO, CONJ = FINAL.split("|")
LOGIT_C, CONJ_L = float(LOGIT.partition("|")[0].removeprefix("LOGIT_C")), LOGIT.partition("|")[2]
assert MODELO == "XGB" and CONJ_L == CONJ, "previsto para XGBoost y la logística sobre el mismo conjunto"
K, REPLICAS, MARGENES = 60, 1000, (30, 45, 60, 90)
PERIODOS = {"P1": (121, 151), "P2": (152, 182)}

verificar_fuente()
df = cargar(183)
R = {"plataforma": platform.platform(), "semilla": XGB["random_state"], "margenes": list(MARGENES)}
for per, (ini, fin) in PERIODOS.items():
    R[per] = {}
    for margen in MARGENES:
        tr, te = bloque(df, ini, fin, margen=margen)
        y, yt = tr["fraude"].to_numpy(), te["fraude"].to_numpy()
        m, d = te["TransactionAmt"].to_numpy(float), te["dia"].to_numpy()
        dis = Diseno(tr, CONJ)
        A, B = dis.matriz(tr), dis.matriz(te)
        S = {"modelo": xgb.XGBClassifier(**XGB).fit(A, y).predict_proba(B)[:, 1] * m,
             "logit": LogisticRegression(C=LOGIT_C, max_iter=3000).fit(A, y).predict_proba(B)[:, 1] * m,
             "regla": reglas(tr, te)[REGLA] * m}
        usd = {n: dinero(v, d, yt, m, K) for n, v in S.items()}
        rep = bootstrap(S, d, yt, m, K, REPLICAS, semilla=ini)
        R[per][str(margen)] = {"entrenamiento": {"dias": [int(tr["dia"].min()), int(tr["dia"].max())], "pagos": len(tr)}, "usd": usd,
                               "contrastes": {n: contraste(rep, "modelo", n, usd) for n in ("regla", "logit")}}
        c = R[per][str(margen)]["contrastes"]
        print(per, "margen", margen, {n: round(v) for n, v in usd.items()},
              {n: (round(c[n]["rel"], 3), [round(x, 3) for x in c[n]["rel_ic95"]]) for n in c}, flush=True)
(RESULTADOS / "margen.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
