"""Lecciones del curso con los puntajes ya guardados (resultados/lecciones.json). No entrena ni lee datos crudos.

- Curva de beneficio: dólares de fraude en la cola para cada cupo diario K, y el valor de la revisión marginal.
- Costo por revisión: el cupo que maximiza el valor neto se elige en desarrollo y se mide en la prueba.
- Calibración: probabilidad estimada contra tasa observada, y dinero esperado contra dinero observado en la cola.
- Regularización de la logística y AUC contra dinero en desarrollo (de resultados/desarrollo.csv).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from revisar.evaluacion import seleccion
from revisar.rutas import PROCESADOS, RESULTADOS

SEL = json.loads((RESULTADOS / "desarrollo_seleccion.json").read_text(encoding="utf-8"))
FINAL, REGLA, LOGIT = SEL["final"], SEL["mejor_regla"], SEL["mejor_logit"]
KMAX, TRAMO = 1500, 20
COSTOS = (1, 2, 5, 10, 20, 50, 100)
RECUPERA = (1.0, 0.5)
POL = {"modelo": (FINAL, "p_x_monto"), "logistica": (LOGIT, "p_x_monto"), "regla": (REGLA, "p_x_monto"),
       "publicado": (FINAL, "p")}


def leer(nombres):
    return pd.concat([pd.read_parquet(PROCESADOS / f"{n}.parquet") for n in nombres], ignore_index=True)


def acumulada(d, col, modo):
    """F[K]: dólares de fraude en la cola sumados sobre los días, para K = 0..KMAX revisiones por día."""
    s = d[col].to_numpy(float) * (d["monto"].to_numpy(float) if modo == "p_x_monto" else 1.0)
    fm = (d["fraude"] * d["monto"]).to_numpy(float)
    F = np.zeros(KMAX + 1)
    for _, idx in d.groupby("dia").indices.items():
        v = np.cumsum(fm[idx][np.argsort(-s[idx], kind="stable")])
        v = np.concatenate([[0.0], v, np.full(max(KMAX - len(v), 0), v[-1])])[: KMAX + 1]
        F += v
    return F


dev, test = leer(["desarrollo_puntajes_D1", "desarrollo_puntajes_D2"]), leer(["prueba_puntajes_P1", "prueba_puntajes_P2"])
nd, nt = dev["dia"].nunique(), test["dia"].nunique()
Fd = {k: acumulada(dev, c, m) for k, (c, m) in POL.items()}
Ft = {k: acumulada(test, c, m) for k, (c, m) in POL.items()}
# control: la curva reproduce los dólares de la prueba con K = 60
chk = {k: float(Ft[k][60]) for k in Ft}
ref = sum(float((test["fraude"] * test["monto"])[seleccion(test[FINAL] * test["monto"], test["dia"].to_numpy(), 60)].sum()) for _ in [0])
assert abs(chk["modelo"] - ref) < 1e-6 * ref, (chk["modelo"], ref)

out = {"dias_dev": int(nd), "dias_prueba": int(nt), "tramo": TRAMO, "kmax": KMAX}
# valor de la revisión marginal: USD de fraude por revisión en cada tramo de 20 posiciones de la cola diaria
out["marginal"] = {k: [float((F[i + TRAMO] - F[i]) / (TRAMO * nt)) for i in range(0, KMAX, TRAMO)] for k, F in Ft.items()}
out["marginal_dev"] = {k: [float((F[i + TRAMO] - F[i]) / (TRAMO * nd)) for i in range(0, KMAX, TRAMO)] for k, F in Fd.items()}
out["acumulada"] = {k: [float(F[i]) for i in range(0, KMAX + 1, 10)] for k, F in Ft.items()}

# costo por revisión: K* elegido en desarrollo, valor neto medido en la prueba
K = np.arange(KMAX + 1)
costos = []
for r in RECUPERA:
    for c in COSTOS:
        fila = {"costo": c, "recupera": r}
        for k in ("modelo", "logistica", "regla"):
            kstar = int(np.argmax(r * Fd[k] - c * K * nd))
            fila[k] = {"K": kstar, "neto_prueba": float(r * Ft[k][kstar] - c * kstar * nt),
                       "neto_60": float(r * Ft[k][60] - c * 60 * nt),
                       "kstar_prueba": int(np.argmax(r * Ft[k] - c * K * nt))}
        costos.append(fila)
out["costos"] = costos

# calibración en la prueba
bordes = [0, .005, .01, .02, .05, .1, .2, .5, 1.0001]
cal = {}
for k, col in (("modelo", FINAL), ("logistica", LOGIT)):
    p, y = test[col].to_numpy(float), test["fraude"].to_numpy(float)
    b = np.digitize(p, bordes) - 1
    cal[k] = {"bins": [{"desde": bordes[i], "hasta": min(bordes[i + 1], 1.0), "n": int((b == i).sum()),
                        "p_media": float(p[b == i].mean()), "tasa": float(y[b == i].mean())} for i in range(len(bordes) - 1) if (b == i).sum()],
              "brier": float(np.mean((p - y) ** 2)), "p_media": float(p.mean()), "tasa": float(y.mean())}
    cola = {}
    for per, ds in (("P1", test[test["dia"] <= 151]), ("P2", test[test["dia"] >= 152])):
        sel = seleccion(ds[col].to_numpy(float) * ds["monto"].to_numpy(float), ds["dia"].to_numpy(), 60)
        cola[per] = {"esperado": float((ds[col] * ds["monto"]).to_numpy()[sel].sum()),
                     "observado": float((ds["fraude"] * ds["monto"]).to_numpy()[sel].sum())}
    cal[k]["cola"] = cola
out["calibracion"] = cal
out["brier_base"] = float(test["fraude"].mean() * (1 - test["fraude"].mean()))

# regularización y AUC contra dinero (desarrollo)
dc = pd.read_csv(RESULTADOS / "desarrollo.csv")
d60 = dc[dc["K"] == 60]
reg = []
for conj in ("F2", "F3"):
    for c in (0.001, 0.003, 0.01, 0.03, 0.1):
        g = d60[(d60["politica"] == f"LOGIT_C{c}|{conj}") & (d60["puntaje"] == "p_x_monto")]
        reg.append({"conjunto": conj, "C": c, "usd": float(g["usd"].sum()), "auc": float(g["auc"].mean())})
out["regularizacion"] = reg
d2 = d60[(d60["bloque"] == "D2") & (d60["politica"] != "oraculo")]
out["auc_dinero"] = [{"politica": r.politica, "puntaje": r.puntaje, "usd": float(r.usd), "auc": float(r.auc)} for r in d2.itertuples()]

(RESULTADOS / "lecciones.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
print("K=60 prueba:", {k: round(v) for k, v in chk.items()})
print("marginal en K=40-60 (USD/rev):", {k: round(v[2], 1) for k, v in out["marginal"].items()})
for f in costos:
    print(f["recupera"], f["costo"], {k: (f[k]["K"], f[k]["kstar_prueba"], round(f[k]["neto_prueba"]), round(f[k]["neto_60"])) for k in ("modelo", "logistica", "regla")})
for k in cal:
    print(k, "brier", round(cal[k]["brier"], 5), "p media", round(cal[k]["p_media"], 4), "tasa", round(cal[k]["tasa"], 4), cal[k]["cola"])
    print("  ", [(b["desde"], b["n"], round(b["p_media"], 4), round(b["tasa"], 4)) for b in cal[k]["bins"]])
print("brier base", round(out["brier_base"], 5))
