"""Búsqueda de variables con validación cruzada temporal. Solo desarrollo: no lee ningún pago del día 121 en adelante.

Diseño, fijado en docs/anexo_variables.md antes de correr:
- Tres ventanas internas con origen móvil: días 61–75, 76–90 y 91–105. Cada una entrena con los pagos de días
  anteriores a su inicio menos 30, el margen de madurez de la etiqueta del protocolo.
- Selección hacia adelante por grupos, desde F3: en cada ronda se agrega cada grupo restante y se acepta el mejor si
  sube el dinero total de las tres ventanas al menos 1% y sube en al menos dos de ellas. Después, una pasada hacia
  atrás quita los grupos aceptados que no restan dinero.
- Hiperparámetros de XGBoost sobre las mismas ventanas, con parada temprana en los últimos 10 días de cada
  entrenamiento; se adoptan con la misma regla del 1% y dos ventanas.
- Confirmación en los días 106–120, que la búsqueda nunca usa.
- El historial de contracargos (grupo "etiquetas") no compite: aprende la regla con que Vesta propaga la etiqueta a
  la cuenta. Se mide aparte.
Métrica: dólares de fraude en la cola de 60 por día, ordenada por probabilidad × monto.

Uso: python scripts/06_variables.py [--rapido]   (--rapido: ventanas cortas y pocos árboles, para probar el código)
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd
import scipy.sparse as sp
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss

from revisar.datos import PRIMER_DIA_PRUEBA, bloque, cargar, verificar_fuente
from revisar.evaluacion import auc, bootstrap, contraste, dinero, por_dia
from revisar.politicas import XGB, reglas
from revisar.rutas import PROCESADOS, RESULTADOS
from revisar.variables import DESCRIPCION, DisenoUnion, agregar, parada_temprana

ap = argparse.ArgumentParser()
ap.add_argument("--rapido", action="store_true")
RAPIDO = ap.parse_args().rapido

K = 60
INTERNAS = {"V1": (61, 75), "V2": (76, 90), "V3": (91, 105)}
CONFIRMA = (106, 120)
CANDIDATOS = ["ventanas", "perfil", "novedad", "compartido", "texto", "monto_fino", "frecuencia", "uid_fino"]
APARTE = "etiquetas"
MIN_GANANCIA, MIN_VENTANAS = 0.01, 2
PROTOCOLO = dict(XGB)
REJILLA = [dict(max_depth=6, min_child_weight=1), dict(max_depth=8, min_child_weight=1),
           dict(max_depth=8, min_child_weight=10), dict(max_depth=10, min_child_weight=10)]
VALIDACION_DIAS, PACIENCIA, TOPE_ARBOLES = 10, 150, 4000
LOGIT_C = 0.003
REPLICAS = 1000
ULTIMO_DIA = PRIMER_DIA_PRUEBA
if RAPIDO:
    INTERNAS, CONFIRMA, ULTIMO_DIA = {"V1": (61, 64), "V2": (65, 68)}, (69, 72), 73
    PROTOCOLO["n_estimators"] = 25
    REJILLA, TOPE_ARBOLES, PACIENCIA, REPLICAS = REJILLA[:2], 60, 10, 50
SALIDA = RESULTADOS / ("variables_rapido.json" if RAPIDO else "variables.json")
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:6.0f}s]", *a, flush=True)


verificar_fuente()
df = cargar(ULTIMO_DIA)
assert df["dia"].max() < PRIMER_DIA_PRUEBA
grupos = agregar(df)
log("datos", df.shape, {g: len(v[0]) + len(v[1]) for g, v in grupos.items()})


class Ventana:
    def __init__(self, ini, fin):
        tr, te = bloque(df, ini, fin)
        self.tr, self.te = tr, te
        self.dis = DisenoUnion(tr, grupos)
        self.A, self.B = self.dis.matriz(tr), self.dis.matriz(te)
        self.y, self.dias_tr = tr["fraude"].to_numpy(), tr["dia"].to_numpy()
        self.yt, self.m, self.d = te["fraude"].to_numpy(), te["TransactionAmt"].to_numpy(float), te["dia"].to_numpy()

    def columnas(self, elegidos):
        idx = self.dis.indices(elegidos)
        return self.A[:, idx].tocsr(), self.B[:, idx].tocsr(), len(idx)

    def medir(self, p):
        p = np.clip(p, 1e-6, 1 - 1e-6)
        return dict(usd=dinero(p * self.m, self.d, self.yt, self.m, K), auc=auc(self.yt, p),
                    ap=float(average_precision_score(self.yt, p)), logloss=float(log_loss(self.yt, p)),
                    brier=float(brier_score_loss(self.yt, p)))


def xgb_fijo(A, y, B, params):
    return xgb.XGBClassifier(**params).fit(A, y).predict_proba(B)[:, 1]


def xgb_temprano(v: Ventana, A, B, params):
    return parada_temprana(A, v.y, v.dias_tr, B, {**PROTOCOLO, **params}, TOPE_ARBOLES, PACIENCIA, VALIDACION_DIAS)


V = {n: Ventana(*r) for n, r in INTERNAS.items()}
log("ventanas internas", {n: (len(v.tr), len(v.te)) for n, v in V.items()})
cache: dict[tuple, dict] = {}


def evaluar(elegidos, params=None):
    clave = (tuple(sorted(elegidos)), json.dumps(params, sort_keys=True))
    if clave not in cache:
        out = {}
        for n, v in V.items():
            A, B, ncol = v.columnas(elegidos)
            if params is None:
                out[n] = v.medir(xgb_fijo(A, v.y, B, PROTOCOLO))
            else:
                p, arboles, _ = xgb_temprano(v, A, B, params)
                out[n] = {**v.medir(p), "arboles": arboles}
            out[n]["columnas"] = ncol
        cache[clave] = out
        log("evaluado", "+".join(elegidos) or "F3", params or "", round(total(out)))
    return cache[clave]


def total(r):
    return sum(r[n]["usd"] for n in INTERNAS)


def resumen(r):
    return {"total_usd": total(r), "ventanas": {n: r[n] for n in INTERNAS},
            "auc": float(np.mean([r[n]["auc"] for n in INTERNAS])), "ap": float(np.mean([r[n]["ap"] for n in INTERNAS])),
            "logloss": float(np.mean([r[n]["logloss"] for n in INTERNAS]))}


# 1 · Selección hacia adelante por grupos
actual, r_actual = [], evaluar([])
base_F3 = resumen(r_actual)
rondas = []
while True:
    restantes = [g for g in CANDIDATOS if g not in actual]
    if not restantes:
        break
    prueba = {g: evaluar(actual + [g]) for g in restantes}
    mejor = max(prueba, key=lambda g: total(prueba[g]))
    ganancia = total(prueba[mejor]) / total(r_actual) - 1
    suben = int(sum(prueba[mejor][n]["usd"] > r_actual[n]["usd"] for n in INTERNAS))
    acepta = bool(ganancia >= MIN_GANANCIA and suben >= MIN_VENTANAS)
    rondas.append(dict(ronda=len(rondas) + 1, partida=list(actual), partida_usd=total(r_actual),
                       pruebas={g: {**resumen(prueba[g]), "ganancia": total(prueba[g]) / total(r_actual) - 1,
                                    "suben": int(sum(prueba[g][n]["usd"] > r_actual[n]["usd"] for n in INTERNAS))} for g in restantes},
                       mejor=mejor, ganancia=ganancia, suben=suben, acepta=acepta))
    log("ronda", len(rondas), mejor, f"{ganancia:+.3f}", suben, "acepta" if acepta else "para")
    if not acepta:
        break
    actual.append(mejor)
    r_actual = prueba[mejor]

# 2 · Pasada hacia atrás: se quita un grupo aceptado si sin él el dinero no baja
atras = []
for g in list(actual):
    if len(actual) < 2:
        break
    sin = [x for x in actual if x != g]
    r = evaluar(sin)
    quita = bool(total(r) >= total(r_actual))
    atras.append(dict(grupo=g, sin_usd=total(r), con_usd=total(r_actual), quita=quita))
    if quita:
        actual, r_actual = sin, r
elegidos = list(actual)
log("elegidos", elegidos)

# 3 · Hiperparámetros con parada temprana, sobre las variables elegidas
rejilla = []
for params in REJILLA:
    r = evaluar(elegidos, params)
    rejilla.append(dict(params=params, **resumen(r), arboles={n: r[n]["arboles"] for n in INTERNAS}))
mejor_p = max(rejilla, key=lambda f: f["total_usd"])
gan_p = mejor_p["total_usd"] / total(r_actual) - 1
suben_p = int(sum(mejor_p["ventanas"][n]["usd"] > r_actual[n]["usd"] for n in INTERNAS))
adopta_p = bool(gan_p >= MIN_GANANCIA and suben_p >= MIN_VENTANAS)
params_final = mejor_p["params"] if adopta_p else None
arboles_final = int(np.median([mejor_p["arboles"][n] for n in INTERNAS])) if adopta_p else None
log("hiperparámetros", mejor_p["params"], f"{gan_p:+.3f}", suben_p, "adopta" if adopta_p else "se queda el protocolo")

# Curva de aprendizaje (capítulo 7): pérdida logarítmica en entrenamiento y validación, última ventana interna
vu = V[list(INTERNAS)[-1]]
A_u, B_u, _ = vu.columnas(elegidos)
_, mejor_it, curva = xgb_temprano(vu, A_u, B_u, params_final or {})
paso = max(1, len(curva["validacion"]) // 200)
aprendizaje = {"ventana": list(INTERNAS)[-1], "mejor_iteracion": mejor_it, "paso": paso,
               "entrenamiento": curva["entrenamiento"][::paso], "validacion": curva["validacion"][::paso],
               "arboles_protocolo": PROTOCOLO["n_estimators"], "learning_rate": PROTOCOLO["learning_rate"]}

# 4 · Historial de contracargos, medido aparte
r_etq = evaluar(elegidos + [APARTE])
etiquetas_internas = {**resumen(r_etq), "ganancia": total(r_etq) / total(r_actual) - 1}

# 5 · Confirmación en días que la búsqueda no usó
for v in V.values():
    v.A = v.B = None
C = Ventana(*CONFIRMA)
log("confirmación", len(C.tr), len(C.te))
P, filas_c = {}, {}
A0, B0, _ = C.columnas([])
A1, B1, _ = C.columnas(elegidos)
A2, B2, _ = C.columnas(elegidos + [APARTE])
P["F3"] = xgb_fijo(A0, C.y, B0, PROTOCOLO)
P["elegido"] = xgb_fijo(A1, C.y, B1, PROTOCOLO)
P["elegido_ajustado"] = xgb_temprano(C, A1, B1, params_final)[0] if params_final else P["elegido"]
P["con_etiquetas"] = xgb_fijo(A2, C.y, B2, PROTOCOLO)
P["logit_F3"] = LogisticRegression(C=LOGIT_C, max_iter=3000).fit(A0, C.y).predict_proba(B0)[:, 1]
P["logit_elegido"] = LogisticRegression(C=LOGIT_C, max_iter=3000).fit(A1, C.y).predict_proba(B1)[:, 1]
P["regla"] = reglas(C.tr, C.te)["R_segmento"]
S = {n: p * C.m for n, p in P.items()}
usd = {n: dinero(s, C.d, C.yt, C.m, K) for n, s in S.items()}
rep = bootstrap(S, C.d, C.yt, C.m, K, REPLICAS, semilla=CONFIRMA[0])
contrastes = {f"{a}_vs_{b}": contraste(rep, a, b, usd) for a, b in
              (("elegido", "F3"), ("elegido_ajustado", "F3"), ("elegido_ajustado", "elegido"), ("con_etiquetas", "elegido"),
               ("logit_elegido", "logit_F3"), ("elegido", "regla"), ("F3", "regla"))}
metricas_c = {n: ({**C.medir(p), "usd": usd[n]} if n != "regla" else {"usd": usd[n]}) for n, p in P.items()}
diario = pd.DataFrame({n: por_dia(S[n], C.d, C.yt, C.m, K) for n in ("F3", "elegido", "elegido_ajustado")})
gana = {"elegido": int((diario["elegido"] > diario["F3"]).sum()), "elegido_ajustado": int((diario["elegido_ajustado"] > diario["F3"]).sum()),
        "dias": int(len(diario))}
log("confirmación", {n: round(u) for n, u in usd.items()})

# Importancia por grupo en la confirmación: dólares que pierde la cola al barajar juntas las columnas de cada grupo.
# Se baraja la matriz densa y se vuelve a dispersa igual que en el entrenamiento (los ceros quedan como ausentes).
mod_e = xgb.XGBClassifier(**PROTOCOLO).fit(A1, C.y)
sel = C.dis.indices(elegidos)
pos = {c: i for i, c in enumerate(sel)}
Bd = B1.toarray()
rng = np.random.default_rng(1)
importancia = {}
for g in ["base"] + elegidos:
    variables = C.dis.base if g == "base" else C.dis.grupos[g]
    gcols = [pos[i] for v in variables for i in C.dis.columnas[v]]
    vals = []
    for _ in range(3):
        Bp = Bd.copy()
        Bp[:, gcols] = Bd[rng.permutation(len(Bd))][:, gcols]
        pp = mod_e.predict_proba(sp.csr_matrix(Bp))[:, 1]
        vals.append(usd["elegido"] - dinero(pp * C.m, C.d, C.yt, C.m, K))
    importancia["F3" if g == "base" else g] = float(np.mean(vals))
log("importancia", importancia)

pd.DataFrame({"dia": C.d, "fraude": C.yt, "monto": C.m, **{n: np.asarray(p, float) for n, p in P.items()}}).to_parquet(
    PROCESADOS / ("variables_confirmacion_rapido.parquet" if RAPIDO else "variables_confirmacion.parquet"), index=False)
out = dict(rapido=RAPIDO, internas=INTERNAS, confirmacion=CONFIRMA, regla=dict(min_ganancia=MIN_GANANCIA, min_ventanas=MIN_VENTANAS),
           candidatos=CANDIDATOS, descripcion=DESCRIPCION, variables_por_grupo={g: C.dis.grupos[g] for g in CANDIDATOS + [APARTE]},
           columnas_F3=len(C.dis.indices([])), columnas_elegido=len(C.dis.indices(elegidos)),
           base_F3=base_F3, rondas=rondas, atras=atras, elegidos=elegidos, final_interno=resumen(r_actual),
           rejilla=rejilla, hiperparametros=dict(adopta=adopta_p, params=params_final, arboles=arboles_final, ganancia=gan_p, suben=suben_p),
           aprendizaje=aprendizaje, etiquetas_internas=etiquetas_internas,
           confirmacion_resultados=dict(usd=usd, metricas=metricas_c, contrastes=contrastes, dias_gana=gana,
                                        usd_fraude=float((C.yt * C.m).sum()), pagos=len(C.te), entrenamiento=len(C.tr)),
           importancia_confirmacion=importancia, protocolo_xgb={k: PROTOCOLO[k] for k in ("n_estimators", "max_depth", "learning_rate")})
SALIDA.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
log("listo", SALIDA.name, elegidos, {k: f"{v['rel']:+.3f} [{v['rel_ic95'][0]:+.3f}, {v['rel_ic95'][1]:+.3f}]" for k, v in contrastes.items()})
