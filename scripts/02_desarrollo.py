"""Torneo de desarrollo: días 61-90 (D1) y 91-120 (D2). No lee ningún pago del día 121 en adelante.

Aplica la regla escrita en docs/criterio_desarrollo.md y deja la selección en resultados/desarrollo_seleccion.json.
Diagnósticos sobre D2 con la configuración elegida: importancia por grupo en dólares, etiquetas barajadas,
azar esperado y la tarjeta del árbol de profundidad 3.
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier

from revisar.datos import PRIMER_DIA_PRUEBA, bloque, cargar, verificar_fuente
from revisar.evaluacion import auc, dinero, matriz
from revisar.politicas import CART, CS, FLEXIBLES, MLP, REGLAS, RF, XGB, Diseno, modelos, puntaje, reglas
from revisar.rutas import PROCESADOS, RESULTADOS

K, KS = 60, (30, 60, 120)
BLOQUES = {"D1": (61, 90), "D2": (91, 120)}
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:6.0f}s]", *a, flush=True)


verificar_fuente()
df = cargar(PRIMER_DIA_PRUEBA, vesta=True)
assert df["dia"].max() < PRIMER_DIA_PRUEBA
log("datos", df.shape)

filas, guardados = [], {}
for b, (ini, fin) in BLOQUES.items():
    tr, te = bloque(df, ini, fin)
    y, m, d = te["fraude"].to_numpy(), te["TransactionAmt"].to_numpy(float), te["dia"].to_numpy()
    tope = float(np.quantile(tr["TransactionAmt"], 0.99))
    sin = m <= tope
    P = dict(reglas(tr, te))
    for conj in ("F2", "F3"):
        cuales = ("LOGIT",) + FLEXIBLES + (("ISO",) if conj == "F3" else ())
        P.update({f"{n}|{conj}": p for n, p in modelos(tr, te, conj, cuales).items()})
        log(b, conj, "listo")
    for conj in ("F1", "F4"):
        P[f"XGB|{conj}"] = modelos(tr, te, conj, ("XGB",))["XGB"]
        log(b, conj, "listo")
    for nombre, p in P.items():
        base = nombre.split("|")[0]
        for modo in ("p_x_monto", "p"):
            if base == "R_monto" and modo == "p":
                continue
            s = puntaje(base, p, m, modo)
            for k in KS:
                mx = matriz(s, d, y, m, k)
                filas.append(dict(bloque=b, politica=nombre, puntaje=modo, K=k, usd=mx["revisado_fraude"]["usd"],
                                  usd_sin_top1=dinero(s[sin], d[sin], y[sin], m[sin], k), precision=mx["precision"],
                                  auc=auc(y, m if base == "R_monto" else p)))
    for k in KS:
        filas.append(dict(bloque=b, politica="oraculo", puntaje="-", K=k, usd=dinero(y * m, d, y, m, k),
                          usd_sin_top1=dinero((y * m)[sin], d[sin], y[sin], m[sin], k), precision=np.nan, auc=np.nan))
    pd.DataFrame({"dia": d, "fraude": y, "monto": m, **{n: np.asarray(p, float) for n, p in P.items()}}).to_parquet(
        PROCESADOS / f"desarrollo_puntajes_{b}.parquet", index=False)
    guardados[b] = dict(entrenamiento=len(tr), evaluacion=len(te), dias=int(fin - ini + 1), tope_p99=tope,
                        usd_fraude=float((y * m).sum()), pagos_fraude=int(y.sum()),
                        azar_esperado=float(sum(K * (y * m)[d == x].sum() / (d == x).sum() for x in np.unique(d))))

res = pd.DataFrame(filas)
res.to_csv(RESULTADOS / "desarrollo.csv", index=False)

# Selección, tal como la fija docs/criterio_desarrollo.md
tab = res[(res.K == K) & (res.puntaje == "p_x_monto")].pivot_table(index="politica", columns="bloque", values="usd")
tab["total"] = tab[list(BLOQUES)].sum(axis=1)
elegibles = [f"{f}|{c}" for f in FLEXIBLES for c in ("F2", "F3")]
mejor = tab.loc[elegibles, "total"].idxmax()
nota_ens = None
if mejor.startswith("ENS"):
    unico = tab.loc[[e for e in elegibles if not e.startswith("ENS")], "total"].idxmax()
    if tab.loc[mejor, "total"] < 1.01 * tab.loc[unico, "total"]:
        nota_ens = f"{mejor} ganó por menos de 1% sobre {unico}; se elige el modelo único"
        mejor = unico
mejor_logit = tab.loc[[f"LOGIT_C{c}|{f}" for c in CS for f in ("F2", "F3")], "total"].idxmax()
supera_lineal = bool(all(tab.loc[mejor, b] > tab.loc[mejor_logit, b] for b in BLOQUES))
final = mejor if supera_lineal else mejor_logit
mejor_regla = tab.loc[list(REGLAS), "total"].idxmax()
sel = dict(final=final, mejor_flexible=mejor, supera_lineal_en_ambos=supera_lineal, nota_ensamble=nota_ens,
           mejor_logit=mejor_logit, mejor_regla=mejor_regla, publicado=f"{final} ordenado por probabilidad", K=K,
           bloques={b: dict(zip(("inicio", "fin"), v)) for b, v in BLOQUES.items()}, margen_dias=30,
           dolares={n: {b: float(tab.loc[n, b]) for b in BLOQUES} for n in tab.index},
           ventaja={c: {b: float(tab.loc[final, b] / tab.loc[c, b] - 1) for b in BLOQUES}
                    for c in (mejor_regla, mejor_logit, "R_monto")},
           info_bloques=guardados)
log("final", final, "| mejor regla", mejor_regla, "| mejor logística", mejor_logit)
(RESULTADOS / "desarrollo_seleccion.json").write_text(json.dumps(sel, ensure_ascii=False, indent=1), encoding="utf-8")

# Diagnósticos en D2 con la configuración final (solo desarrollo)
ini, fin = BLOQUES["D2"]
tr, te = bloque(df, ini, fin)
y, m, d = te["fraude"].to_numpy(), te["TransactionAmt"].to_numpy(float), te["dia"].to_numpy()
modelo, conj = final.split("|")
dis = Diseno(tr, conj)
ytr = tr["fraude"].to_numpy()


def ajustar(etiquetas):
    if modelo in ("XGB", "XGB_pond", "ENS"):
        w = tr["TransactionAmt"].to_numpy(float)
        mod = xgb.XGBClassifier(**XGB).fit(dis.matriz(tr), etiquetas, sample_weight=(w / w.mean()) if modelo == "XGB_pond" else None)
        if modelo != "ENS":
            return lambda x: mod.predict_proba(dis.matriz(x))[:, 1]
        bosque = RandomForestClassifier(**RF).fit(dis.nativa(tr), etiquetas)
        return lambda x: (mod.predict_proba(dis.matriz(x))[:, 1] + bosque.predict_proba(dis.nativa(x))[:, 1]) / 2
    if modelo == "RF":
        bosque = RandomForestClassifier(**RF).fit(dis.nativa(tr), etiquetas)
        return lambda x: bosque.predict_proba(dis.nativa(x))[:, 1]
    if modelo == "MLP":
        red = MLPClassifier(**MLP).fit(dis.matriz(tr), etiquetas)
        return lambda x: red.predict_proba(dis.matriz(x))[:, 1]
    raise SystemExit(f"Diagnóstico no previsto para {modelo}")


pred = ajustar(ytr)
base = dinero(pred(te) * m, d, y, m, K)
GRUPOS = {
    "monto y centavos": ["TransactionAmt", "log_monto", "centavos"],
    "producto": ["ProductCD"],
    "tarjeta": [f"card{i}" for i in range(1, 7)],
    "dirección y distancia": ["addr1", "addr2", "dist1", "dist2"],
    "correo": ["P_emaildomain", "R_emaildomain"],
    "dispositivo e identidad": ["DeviceType", "DeviceInfo"] + [c for c in te.columns if c.startswith("id_")],
    "coincidencias M1-M9": [f"M{i}" for i in range(1, 10)],
    "hora y día": ["hora", "dia_semana"],
    "historial de la tarjeta": [c for c in te.columns if c.startswith("h_") and not c.startswith("h_cliente")],
    "historial del cliente": [c for c in te.columns if c.startswith("h_cliente")] + ["D1"],
}
rng = np.random.default_rng(0)
perdida = {}
for g, cols in GRUPOS.items():
    cols = [c for c in cols if c in dis.num or c in dis.cat]
    if not cols:
        continue
    vals = []
    for _ in range(2):
        tp = te.copy()
        orden = rng.permutation(len(tp))
        tp[cols] = te[cols].to_numpy()[orden]
        vals.append(base - dinero(pred(tp) * m, d, y, m, K))
    perdida[g] = float(np.mean(vals))
log("importancia lista")

barajado = ajustar(rng.permutation(ytr))
cordura = dict(base=base, etiquetas_barajadas=dinero(barajado(te) * m, d, y, m, K),
               azar_esperado=guardados["D2"]["azar_esperado"])

# Árbol de profundidad 3 como tarjeta (variables nativas del conjunto final)
arbol = DecisionTreeClassifier(**CART).fit(dis.nativa(tr), ytr)
t_ = arbol.tree_
mtr = tr["TransactionAmt"].to_numpy(float)
hoja_tr = arbol.apply(dis.nativa(tr))
hojas = []


def recorrer(nodo, reglas_):
    if t_.children_left[nodo] == -1:
        msk = hoja_tr == nodo
        hojas.append(dict(reglas=reglas_, pagos=int(msk.sum()), parte=float(msk.mean()), tasa=float(ytr[msk].mean()),
                          monto_medio=float(mtr[msk].mean()), usd_fraude_por_pago=float((ytr * mtr)[msk].mean())))
        return
    v = dis.nombres_nativa[t_.feature[nodo]]
    u = float(t_.threshold[nodo])
    recorrer(t_.children_left[nodo], reglas_ + [[v, "<=", u, v in dis.cat]])
    recorrer(t_.children_right[nodo], reglas_ + [[v, ">", u, v in dis.cat]])


recorrer(0, [])
cart_d2 = dinero(arbol.predict_proba(dis.nativa(te))[:, 1] * m, d, y, m, K)
sel["diagnosticos_D2"] = dict(importancia_usd=perdida, cordura=cordura, arbol=dict(hojas=hojas, usd_D2=cart_d2))
(RESULTADOS / "desarrollo_seleccion.json").write_text(json.dumps(sel, ensure_ascii=False, indent=1), encoding="utf-8")
log("listo")
for k in KS:
    t = res[(res.K == k)].pivot_table(index=["politica", "puntaje"], columns="bloque", values="usd")
    t["total"] = t.sum(axis=1)
    print(f"\n== K={k} ==\n" + t.sort_values("total", ascending=False).head(14 if k != K else 60).round(0).to_string())
