"""Exploración de los datos de desarrollo (días 1-120). No lee ningún pago del día 121 en adelante."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from revisar.datos import PRIMER_DIA_PRUEBA, cargar, verificar_fuente
from revisar.rutas import RESULTADOS

verificar_fuente()
df = cargar(PRIMER_DIA_PRUEBA)
assert df["dia"].max() < PRIMER_DIA_PRUEBA
y, m = df["fraude"].to_numpy(), df["TransactionAmt"].to_numpy(float)
fm = y * m
X = {}

por_dia = df.groupby("dia").agg(pagos=("fraude", "size"), fraudes=("fraude", "sum"))
por_dia["usd_fraude"] = pd.Series(fm).groupby(df["dia"]).sum()
por_dia.to_csv(RESULTADOS / "exp_dias.csv")
X["universo"] = dict(pagos=len(df), dias=int(df["dia"].nunique()), primer_dia=int(df["dia"].min()), ultimo_dia=int(df["dia"].max()),
                     pagos_por_dia_mediana=float(por_dia["pagos"].median()), tasa_fraude=float(y.mean()),
                     usd_total=float(m.sum()), usd_fraude=float(fm.sum()), parte_usd_fraude=float(fm.sum() / m.sum()),
                     usd_fraude_por_dia_mediana=float(por_dia["usd_fraude"].median()),
                     monto_mediano_fraude=float(np.median(m[y == 1])), monto_mediano_legitimo=float(np.median(m[y == 0])),
                     cupo_60_parte_pagos=float(60 / por_dia["pagos"].median()))

dec = pd.qcut(pd.Series(m).rank(method="first"), 10, labels=False)
t = pd.DataFrame({"dec": dec, "y": y, "m": m, "fm": fm}).groupby("dec").agg(
    monto_min=("m", "min"), monto_max=("m", "max"), tasa=("y", "mean"), usd_fraude=("fm", "sum"), pagos=("y", "size"))
t["parte_usd_fraude"] = t["usd_fraude"] / fm.sum()
t.to_csv(RESULTADOS / "exp_deciles_monto.csv")
orden = np.argsort(-m, kind="stable")
acum = np.cumsum(fm[orden]) / fm.sum()
X["concentracion"] = {f"top_{p}pct_pagos_por_monto": float(acum[int(len(m) * p / 100) - 1]) for p in (1, 5, 10)}
X["concentracion"]["top_1pct_fraudes_por_monto"] = float(np.sort(m[y == 1])[::-1][:max(1, int(y.sum() / 100))].sum() / fm.sum())
# La regla usual de valores atípicos (Q3 + 1.5 IQR) marcaría los pagos donde está el dinero: por eso no se eliminan
q1, q3 = np.quantile(m, [.25, .75])
tope = q3 + 1.5 * (q3 - q1)
X["extremos"] = dict(tope_iqr=float(tope), parte_pagos=float((m > tope).mean()), parte_usd_fraude=float(fm[m > tope].sum() / fm.sum()))

prod = pd.DataFrame({"p": df["ProductCD"], "y": y, "fm": fm}).groupby("p").agg(pagos=("y", "size"), tasa=("y", "mean"), usd_fraude=("fm", "sum"))
prod["parte_pagos"] = prod["pagos"] / len(df)
prod["parte_usd_fraude"] = prod["usd_fraude"] / fm.sum()
X["producto"] = prod.round(6).to_dict(orient="index")

# Historial del cliente reconstruido (tarjeta + dirección + día de alta): sin etiquetas, como variable
tramo = pd.cut(df["h_cliente_previos"], [-0.5, 0.5, 2.5, 9.5, 1e9], labels=["0", "1-2", "3-9", "10+"])
cl = pd.DataFrame({"t": tramo, "y": y}).groupby("t", observed=True)["y"].agg(["mean", "size"])
desde = pd.cut(df["h_cliente_segundos_desde"] / 3600, [0, 1, 24, 24 * 7, 1e9], labels=["< 1 h", "1-24 h", "1-7 días", "> 7 días"], include_lowest=True)
ds = pd.DataFrame({"t": desde.cat.add_categories("primero").fillna("primero"), "y": y}).groupby("t", observed=True)["y"].agg(["mean", "size"])
X["cliente"] = dict(
    clientes=int(pd.factorize(df["card1"] + "|" + df["addr1"] + "|" + df["alta"].astype(str))[0].max() + 1),
    tarjetas_card1=int(df["card1"].nunique()),
    tasa_por_pagos_previos={k: dict(tasa=float(v["mean"]), pagos=int(v["size"])) for k, v in cl.iterrows()},
    tasa_por_tiempo_desde_anterior={k: dict(tasa=float(v["mean"]), pagos=int(v["size"])) for k, v in ds.iterrows()},
)
# Con etiquetas, solo descriptivo: el fraude se concentra por cliente (y Vesta propaga la etiqueta a la cuenta)
cli = df["card1"] + "|" + df["addr1"] + "|" + df["alta"].astype(str)
f_cli = pd.Series(y).groupby(cli.to_numpy()).agg(["sum", "size"])
X["cliente"]["fraudes_en_clientes_con_2_o_mas"] = float(f_cli.loc[f_cli["sum"] >= 2, "sum"].sum() / y.sum())
X["cliente"]["clientes_con_fraude_todo_fraude"] = float(((f_cli["sum"] == f_cli["size"]) & (f_cli["sum"] > 0)).sum() / (f_cli["sum"] > 0).sum())

X["faltantes"] = {c: float(df[c].isna().mean()) for c in ("D1", "dist1", "id_01")}
X["faltantes"].update({c: float((df[c] == "NA").mean()) for c in ("addr1", "P_emaildomain", "DeviceType")})
(RESULTADOS / "exploracion.json").write_text(json.dumps(X, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(X, ensure_ascii=False, indent=1)[:3000])
