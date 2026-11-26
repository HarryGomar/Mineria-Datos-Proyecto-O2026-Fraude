"""Análisis exploratorio para la presentación (días 1-120): lo que cuesta un fraude, la matriz de dispersión por clase,
las distribuciones de fraude y legítimo por categoría, y un ejemplo real de cómo se arma el cliente.
No lee ningún pago del día 121 en adelante."""
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
E = {}

# Lo que cuesta un fraude: monto de cada fraude y totales de un día típico
mf = m[y == 1]
por_dia = df.groupby("dia").agg(pagos=("fraude", "size"), fraudes=("fraude", "sum"))
por_dia["usd"] = pd.Series(y * m).groupby(df["dia"]).sum()
bordes = np.logspace(-1, 4, 31)
E["costo_fraude"] = dict(promedio=float(mf.mean()), mediana=float(np.median(mf)), minimo=float(mf.min()), maximo=float(mf.max()),
                         p90=float(np.quantile(mf, .9)), pagos_dia=float(por_dia["pagos"].median()),
                         fraudes_dia=float(por_dia["fraudes"].median()), usd_dia=float(por_dia["usd"].median()),
                         bordes=[float(b) for b in bordes], fraudes=[int(c) for c in np.histogram(mf, bordes)[0]])

# Matriz de dispersión: cinco variables numéricas, en escala logarítmica cuando el rango lo pide
horas = df["h_cliente_segundos_desde"].to_numpy(float) / 3600
VARS = [
    ("Monto, USD", np.log10(np.clip(m, 1, 5000)), (0, np.log10(5000)), [(1, "10"), (3, "1,000")]),
    ("Hora del día", df["hora"].to_numpy(float) + .5, (0, 24), [(6, "6"), (12, "12"), (18, "18")]),
    ("Días desde el alta", np.log10(1 + np.clip(df["D1"].to_numpy(float), 0, 640)), (0, np.log10(641)),
     [(np.log10(11), "10"), (np.log10(101), "100")]),
    ("Desde su pago anterior", np.log10(np.clip(horas, .01, 3000)), (-2, np.log10(3000)),
     [(0, "1 h"), (np.log10(720), "1 mes")]),
    ("Pagos anteriores", np.log10(1 + np.clip(df["h_cliente_previos"].to_numpy(float), 0, 999)), (0, 3),
     [(np.log10(11), "10"), (np.log10(101), "100")]),
]
rng = np.random.default_rng(7)
muestra = {c: np.sort(rng.choice(np.flatnonzero(y == v), 300, replace=False)) for c, v in (("fraude", 1), ("legitimo", 0))}
E["matriz"] = dict(variables=[], muestra={c: [[None if np.isnan(v[i]) else round(float(v[i]), 3) for _, v, _, _ in VARS] for i in idx]
                                          for c, idx in muestra.items()})
for nombre, v, (lo, hi), marcas in VARS:
    b = np.linspace(lo, hi, 25)
    dens = {c: np.histogram(v[(y == k) & ~np.isnan(v)], b)[0] for c, k in (("fraude", 1), ("legitimo", 0))}
    E["matriz"]["variables"].append(dict(nombre=nombre, rango=[float(lo), float(hi)], marcas=[[float(a), t] for a, t in marcas],
                                         bordes=[float(x) for x in b], **{c: [float(x) for x in d / d.sum()] for c, d in dens.items()}))

# Tasas que la presentación cita junto a la matriz
d1, hora = df["D1"].to_numpy(float), df["hora"].to_numpy(float)
por_hora = pd.Series(y).groupby(hora).mean()
E["tasas"] = dict(promedio=float(y.mean()), alta_0_1=float(y[(d1 > 0) & (d1 <= 1)].mean()), alta_1_7=float(y[(d1 > 1) & (d1 <= 7)].mean()),
                  hora_min=float(por_hora.min()), hora_max=float(por_hora.max()),
                  mediana_fraude=float(np.median(m[y == 1])), mediana_legitimo=float(np.median(m[y == 0])))

# Fraude contra legítimo en cuatro variables categóricas: qué parte de cada clase cae en cada categoría
CATS = [("Producto", df["ProductCD"], {"W": "W", "C": "C", "R": "R", "H": "H", "S": "S"}),
        ("Tipo de tarjeta", df["card6"], {"debit": "Débito", "credit": "Crédito"}),
        ("Dispositivo", df["DeviceType"], {"NA": "Sin dato", "desktop": "Computadora", "mobile": "Celular"}),
        ("Correo del comprador", df["P_emaildomain"], {"gmail.com": "gmail.com", "yahoo.com": "yahoo.com", "hotmail.com": "hotmail.com",
                                                       "anonymous.com": "anonymous.com", "NA": "Sin dato"})]
E["clases"] = []
for nombre, serie, etiquetas in CATS:
    s = serie.map(etiquetas).fillna("Otro")
    t = pd.DataFrame({"c": s, "y": y}).groupby("c")["y"].agg(["sum", "size"])
    orden = list(etiquetas.values()) + (["Otro"] if "Otro" in t.index else [])
    E["clases"].append(dict(nombre=nombre, filas=[dict(nombre=c, fraude=float(t.loc[c, "sum"] / y.sum()),
                                                        legitimo=float((t.loc[c, "size"] - t.loc[c, "sum"]) / (len(y) - y.sum())),
                                                        tasa=float(t.loc[c, "sum"] / t.loc[c, "size"]), pagos=int(t.loc[c, "size"]))
                                                   for c in orden]))

# Un ejemplo real: misma tarjeta y misma dirección, dos fechas de alta, dos clientes
c1, a1 = "16630", "205.0"
ej = df[(df["card1"] == c1) & (df["addr1"] == a1)]
assert ej["alta"].nunique() == 2 and len(ej) == 6
E["cliente_ejemplo"] = dict(card1=c1, addr1=a1.removesuffix(".0"), filas=[
    [int(r.dia), float(r.TransactionAmt), int(r.D1), int(r.alta), int(r.fraude)] for r in ej.itertuples()])

(RESULTADOS / "eda.json").write_text(json.dumps(E, ensure_ascii=False, indent=1), encoding="utf-8")
print("eda.json:", ", ".join(E))
