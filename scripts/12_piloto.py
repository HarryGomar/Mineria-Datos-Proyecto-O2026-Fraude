"""Potencia del piloto de despliegue, con los resultados diarios de la prueba (resultados/prueba_dias.csv).

Cada simulación arma un piloto de n días remuestreando los 62 días de prueba. Dos diseños:
- días al azar: la mitad de los días usa la cola del modelo y la otra mitad la de la regla (t de Welch entre días);
- pareado: las dos colas se observan el mismo día y se compara la diferencia diaria (t pareada).
Potencia: parte de los pilotos en que el modelo sale mejor con p < 0.05. No entrena ni lee datos crudos.
Uso: python scripts/12_piloto.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats

from revisar.rutas import RESULTADOS

SEL = json.loads((RESULTADOS / "desarrollo_seleccion.json").read_text(encoding="utf-8"))
dias = pd.read_csv(RESULTADOS / "prueba_dias.csv")
mod, reg = dias[SEL["final"]].to_numpy(), dias[SEL["mejor_regla"]].to_numpy()
SIMULACIONES, ALFA = 10_000, 0.05
rng = np.random.default_rng(0)


def al_azar(n: int) -> dict:
    idx = rng.integers(0, len(mod), (SIMULACIONES, n))
    a, b = mod[idx[:, : n // 2]], reg[idx[:, n // 2:]]
    va, vb = a.var(axis=1, ddof=1) / a.shape[1], b.var(axis=1, ddof=1) / b.shape[1]
    dif = a.mean(axis=1) - b.mean(axis=1)
    gl = (va + vb) ** 2 / (va ** 2 / (a.shape[1] - 1) + vb ** 2 / (b.shape[1] - 1))
    p = 2 * stats.t.sf(np.abs(dif) / np.sqrt(va + vb), gl)
    return {"potencia": float(((p < ALFA) & (dif > 0)).mean()), "sale_al_reves": float((dif < 0).mean())}


def pareado(n: int) -> dict:
    x = (mod - reg)[rng.integers(0, len(mod), (SIMULACIONES, n))]
    dif = x.mean(axis=1)
    p = 2 * stats.t.sf(np.abs(dif) / (x.std(axis=1, ddof=1) / np.sqrt(n)), n - 1)
    return {"potencia": float(((p < ALFA) & (dif > 0)).mean()), "sale_al_reves": float((dif < 0).mean())}


R = {"dias_prueba": len(dias), "simulaciones": SIMULACIONES, "alfa": ALFA,
     "usd_por_dia": {"modelo": float(mod.mean()), "regla": float(reg.mean()), "diferencia": float((mod - reg).mean())},
     "desviacion": {"modelo": float(mod.std(ddof=1)), "regla": float(reg.std(ddof=1)), "diferencia": float((mod - reg).std(ddof=1))},
     "al_azar": {str(n): al_azar(n) for n in (30, 60, 90)},
     "pareado": {str(n): pareado(n) for n in (14, 30)}}
(RESULTADOS / "piloto.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(R, ensure_ascii=False, indent=1))
