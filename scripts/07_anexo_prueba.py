"""Anexo posterior a la prueba congelada: las variables y los hiperparámetros que eligió scripts/06_variables.py,
medidos una sola vez en los días 121–182 con el diseño de la prueba (P1: 121–151, P2: 152–182; 30 días de margen).

No cambia el veredicto de docs/protocolo.md, que se queda con F3. docs/anexo_variables.md registra, antes de correr,
las huellas de este código, de scripts/06_variables.py y de src/revisar/variables.py. Se niega a correr dos veces.
Primero reproduce el modelo congelado (XGBoost con F3) y compara sus dólares con resultados/prueba.json.

Uso: python scripts/07_anexo_prueba.py [--rapido]   (--rapido: ventanas de desarrollo en lugar de la prueba)
"""
from __future__ import annotations

import argparse
import json
import re
import time

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score

from revisar.congelado import huella
from revisar.datos import bloque, cargar, verificar_fuente
from revisar.evaluacion import auc, bootstrap, contraste, dinero, por_dia
from revisar.politicas import XGB, reglas
from revisar.rutas import PROCESADOS, RAIZ, RESULTADOS
from revisar.variables import DisenoUnion, agregar, parada_temprana

ap = argparse.ArgumentParser()
ap.add_argument("--rapido", action="store_true")
RAPIDO = ap.parse_args().rapido

ANEXO = RAIZ / "docs" / "anexo_variables.md"
HUELLAS = ["src/revisar/variables.py", "scripts/06_variables.py", "scripts/07_anexo_prueba.py"]
registradas = dict(re.findall(r"\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|", ANEXO.read_text(encoding="utf-8")))
distintas = [r for r in HUELLAS if registradas.get(r) != huella(r)]
if distintas:
    raise SystemExit(f"El código no coincide con las huellas de docs/anexo_variables.md: {distintas}")

SEL = json.loads((RESULTADOS / ("variables_rapido.json" if RAPIDO else "variables.json")).read_text(encoding="utf-8"))
assert SEL["rapido"] == RAPIDO
DES = json.loads((RESULTADOS / "desarrollo_seleccion.json").read_text(encoding="utf-8"))
FINAL, REGLA, LOGIT = DES["final"], DES["mejor_regla"], DES["mejor_logit"]
LOGIT_C = float(LOGIT.partition("|")[0].removeprefix("LOGIT_C"))
ELEGIDOS, HP = SEL["elegidos"], SEL["hiperparametros"]
SALIDA = RESULTADOS / ("anexo_prueba_variables_rapido.json" if RAPIDO else "anexo_prueba_variables.json")
if SALIDA.exists() and not RAPIDO:
    raise SystemExit("El anexo ya corrió: la prueba se lee una sola vez.")
K, REPLICAS = 60, 1000
PERIODOS, ULTIMO = {"P1": (121, 151), "P2": (152, 182)}, 183
PROTOCOLO = dict(XGB)
if RAPIDO:
    PERIODOS, ULTIMO, REPLICAS = {"P1": (91, 94), "P2": (95, 98)}, 99, 50
    PROTOCOLO["n_estimators"] = 25
CONGELADO = None if RAPIDO else json.loads((RESULTADOS / "prueba.json").read_text(encoding="utf-8"))
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:6.0f}s]", *a, flush=True)


verificar_fuente()
df = cargar(ULTIMO)
grupos = agregar(df)
grupos.pop("etiquetas")  # no compite ni se usa aquí: no se arma con etiquetas de la prueba
log("datos", df.shape, "elegidos", ELEGIDOS, "hiperparámetros", HP)
R = {"elegidos": ELEGIDOS, "hiperparametros": HP, "seleccion_06": huella(f"resultados/{'variables_rapido' if RAPIDO else 'variables'}.json")}
for per, (ini, fin) in PERIODOS.items():
    tr, te = bloque(df, ini, fin)
    dis = DisenoUnion(tr, grupos)
    Au, Bu = dis.matriz(tr), dis.matriz(te)
    y, yt = tr["fraude"].to_numpy(), te["fraude"].to_numpy()
    m, d = te["TransactionAmt"].to_numpy(float), te["dia"].to_numpy()

    def cols(e):
        idx = dis.indices(e)
        return Au[:, idx].tocsr(), Bu[:, idx].tocsr()
    A0, B0 = cols([])
    A1, B1 = cols(ELEGIDOS)
    P = {"F3": xgb.XGBClassifier(**PROTOCOLO).fit(A0, y).predict_proba(B0)[:, 1],
         "elegido": xgb.XGBClassifier(**PROTOCOLO).fit(A1, y).predict_proba(B1)[:, 1]}
    if HP["adopta"]:
        P["elegido_ajustado"] = parada_temprana(A1, y, tr["dia"].to_numpy(), B1, {**PROTOCOLO, **HP["params"]},
                                                60 if RAPIDO else 4000, 10 if RAPIDO else 150)[0]
    P["logit_F3"] = LogisticRegression(C=LOGIT_C, max_iter=3000).fit(A0, y).predict_proba(B0)[:, 1]
    P["logit_elegido"] = LogisticRegression(C=LOGIT_C, max_iter=3000).fit(A1, y).predict_proba(B1)[:, 1]
    P["regla"] = reglas(tr, te)[REGLA]
    log(per, "modelos listos")
    S = {n: p * m for n, p in P.items()}
    usd = {n: dinero(s, d, yt, m, K) for n, s in S.items()}
    rep = bootstrap(S, d, yt, m, K, REPLICAS, semilla=int(ini))
    mejor = "elegido_ajustado" if HP["adopta"] else "elegido"
    pares = [("elegido", "F3"), (mejor, "F3"), (mejor, "regla"), ("F3", "regla"), (mejor, "logit_F3"), ("logit_elegido", "logit_F3")]
    C = {f"{a}_vs_{b}": contraste(rep, a, b, usd) for a, b in dict.fromkeys(pares)}
    diario = pd.DataFrame({n: por_dia(S[n], d, yt, m, K) for n in ("F3", mejor)})
    R[per] = dict(dias=[ini, fin], usd=usd, contrastes=C, usd_fraude=float((yt * m).sum()),
                  auc={n: auc(yt, p) for n, p in P.items()}, ap={n: float(average_precision_score(yt, p)) for n, p in P.items()},
                  dias_gana=int((diario[mejor] > diario["F3"]).sum()), n_dias=int(len(diario)))
    if CONGELADO:
        cu = CONGELADO[per]["usd"]
        R[per]["reproduce"] = {"F3": [usd["F3"], cu[FINAL]], "regla": [usd["regla"], cu[REGLA]], "logit_F3": [usd["logit_F3"], cu[LOGIT]]}
    pd.DataFrame({"dia": d, "fraude": yt, "monto": m, **{n: np.asarray(p, float) for n, p in P.items()}}).to_parquet(
        PROCESADOS / f"anexo_puntajes_{per}{'_rapido' if RAPIDO else ''}.parquet", index=False)
    log(per, {n: round(u) for n, u in usd.items()}, {k: f"{v['rel']:+.3f}" for k, v in C.items()},
        R[per].get("reproduce", ""))
SALIDA.write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
log("listo", SALIDA.name)
