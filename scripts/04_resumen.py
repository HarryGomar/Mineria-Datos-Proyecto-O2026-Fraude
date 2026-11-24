"""Cifras derivadas para la presentación (resultados/presentacion.json). Solo lee resultados/ y los puntajes guardados.

- Traza del dinero de cada mes de prueba: fraude que revisan el modelo y la regla, solo uno de ellos o ninguno.
- Un día de prueba completo para la lámina de la decisión: probabilidad, monto, fraude y revisión de cada pago.
- Fraudes por día en la cola del modelo y del enfoque de la competencia.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from revisar.evaluacion import seleccion
from revisar.rutas import PROCESADOS, RESULTADOS

SEL = json.loads((RESULTADOS / "desarrollo_seleccion.json").read_text(encoding="utf-8"))
R = json.loads((RESULTADOS / "prueba.json").read_text(encoding="utf-8"))
FINAL, REGLA, LOGIT = SEL["final"], SEL["mejor_regla"], SEL["mejor_logit"]
K = 60
out = {"traza": {}, "cola": {}, "dias": {}}
dev = pd.read_csv(RESULTADOS / "exp_dias.csv")
out["dias"].update({int(r.dia): [int(r.pagos), float(r.usd_fraude)] for r in dev.itertuples()})
for per in ("P1", "P2"):
    d = pd.read_parquet(PROCESADOS / f"prueba_puntajes_{per}.parquet")
    y, m, dia = d["fraude"].to_numpy(), d["monto"].to_numpy(), d["dia"].to_numpy()
    fm = y * m
    s_mod = seleccion(d[FINAL].to_numpy() * m, dia, K)
    s_reg = seleccion(d[REGLA].to_numpy() * m, dia, K)
    s_pub = seleccion(d[FINAL].to_numpy(), dia, K)
    s_log = seleccion(d[LOGIT].to_numpy() * m, dia, K)
    out["traza"][per] = {
        "fraude_total": float(fm.sum()), "pagos_fraude": int(y.sum()),
        "ambos": float(fm[s_mod & s_reg].sum()), "solo_modelo": float(fm[s_mod & ~s_reg].sum()),
        "solo_regla": float(fm[~s_mod & s_reg].sum()), "ninguno": float(fm[~s_mod & ~s_reg].sum()),
        "pagos_solo_modelo": int((s_mod & ~s_reg).sum()), "pagos_solo_regla": int((~s_mod & s_reg).sum()),
        "fraudes_solo_modelo": int((y.astype(bool) & s_mod & ~s_reg).sum()), "fraudes_solo_regla": int((y.astype(bool) & ~s_mod & s_reg).sum()),
        "monto_medio_fraude_solo_modelo": float(m[y.astype(bool) & s_mod & ~s_reg].mean()),
        "monto_medio_fraude_solo_regla": float(m[y.astype(bool) & ~s_mod & s_reg].mean()),
    }
    g = pd.DataFrame({"dia": dia, "fm": fm}).groupby("dia")["fm"].agg(["size", "sum"])
    out["dias"].update({int(k): [int(v["size"]), float(v["sum"])] for k, v in g.iterrows()})
    n_dias = len(np.unique(dia))
    out["cola"][per] = {n: {"fraudes_por_dia": float(y[s].sum() / n_dias), "usd_por_revision": float(fm[s].sum() / s.sum()),
                            "monto_medio_fraude": float(m[s & (y == 1)].mean())}
                        for n, s in (("modelo", s_mod), ("regla", s_reg), ("publicado", s_pub), ("logistica", s_log))}

# Un día de la prueba: el de diferencia modelo menos regla más cercana a la mediana de P2
dd = pd.read_csv(RESULTADOS / "prueba_dias.csv")
p2 = dd[dd["periodo"] == "P2"].copy()
p2["dif"] = p2[FINAL] - p2[REGLA]
dia_ej = int(p2.iloc[(p2["dif"] - p2["dif"].median()).abs().argsort().iloc[0]]["dia"])
d = pd.read_parquet(PROCESADOS / "prueba_puntajes_P2.parquet")
d = d[d["dia"] == dia_ej].reset_index(drop=True)
p, m, y = d[FINAL].to_numpy(), d["monto"].to_numpy(), d["fraude"].to_numpy()
sc = p * m
corte = float(np.sort(sc)[::-1][K - 1])
rev = sc >= corte
rev_reg = seleccion(d[REGLA].to_numpy() * m, np.zeros(len(d), int), K)
out["dia"] = {"dia": dia_ej, "pagos": len(d), "corte": corte, "fraudes": int(y.sum()), "usd_fraude": float((y * m).sum()),
              "modelo_usd": float((y * m)[rev].sum()), "modelo_fraudes": int(y[rev].sum()),
              "regla_usd": float((y * m)[rev_reg].sum()), "regla_fraudes": int(y[rev_reg].sum()),
              "puntos": [[round(float(a), 5), round(float(b), 2), int(c), int(e)] for a, b, c, e in zip(p, m, y, rev)]}
(RESULTADOS / "presentacion.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k not in ("dia", "dias")}, indent=1, ensure_ascii=False)[:400])
print("días", len(out["dias"]), min(out["dias"]), max(out["dias"]))
print({k: v for k, v in out["dia"].items() if k != "puntos"})
