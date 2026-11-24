"""Prueba congelada: días 121-151 (P1) y 152-182 (P2). Se corre una vez, después de congelar docs/protocolo.md.

Repite el torneo de desarrollo con el mismo código y la selección congelada, entrenando cada periodo con los pagos
de días anteriores a su inicio menos 30. Bootstrap pareado de 1,000 réplicas que remuestrean días.
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from revisar.congelado import verificar
from revisar.datos import bloque, cargar, verificar_fuente
from revisar.evaluacion import auc, bootstrap, contraste, curva, dinero, matriz, por_dia
from revisar.politicas import FLEXIBLES, puntaje, modelos, reglas
from revisar.rutas import PROCESADOS, RESULTADOS

verificar()
verificar_fuente()
SEL = json.loads((RESULTADOS / "desarrollo_seleccion.json").read_text(encoding="utf-8"))
FINAL, REGLA, LOGIT = SEL["final"], SEL["mejor_regla"], SEL["mejor_logit"]
PUB = "PUBLICADO"
K, KS, REPLICAS = 60, (30, 60, 120), 1000
PERIODOS = {"P1": (121, 151), "P2": (152, 182)}
LIMPIOS = (121, 144)  # días que ningún estudio anterior leyó
UMBRAL = {"H1": 0.20, "H2": 0.10}
FRACCIONES = np.round(np.arange(0, 0.1001, 0.0025), 4)
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:6.0f}s]", *a, flush=True)


df = cargar(183, vesta=True)
log("datos", df.shape, "días", df["dia"].min(), df["dia"].max())
R, filas, dias_tabla, curvas = {"seleccion": {"final": FINAL, "regla": REGLA, "logit": LOGIT}}, [], [], []
for per, (ini, fin) in PERIODOS.items():
    tr, te = bloque(df, ini, fin)
    y, m, d = te["fraude"].to_numpy(), te["TransactionAmt"].to_numpy(float), te["dia"].to_numpy()
    tope = float(np.quantile(tr["TransactionAmt"], 0.99))
    P = dict(reglas(tr, te))
    for conj in ("F2", "F3"):
        cuales = ("LOGIT",) + FLEXIBLES + (("ISO",) if conj == "F3" else ())
        P.update({f"{n}|{conj}": p for n, p in modelos(tr, te, conj, cuales).items()})
        log(per, conj, "listo")
    for conj in ("F1", "F4"):
        P[f"XGB|{conj}"] = modelos(tr, te, conj, ("XGB",))["XGB"]
        log(per, conj, "listo")
    S = {n: puntaje(n.split("|")[0], p, m) for n, p in P.items()}
    S[PUB] = puntaje(FINAL.split("|")[0], P[FINAL], m, "p")
    S["oraculo"] = y * m
    pd.DataFrame({"dia": d, "fraude": y, "monto": m, **{n: np.asarray(p, float) for n, p in P.items()}}).to_parquet(
        PROCESADOS / f"prueba_puntajes_{per}.parquet", index=False)

    usd = {n: dinero(s, d, y, m, K) for n, s in S.items()}
    rep = bootstrap(S, d, y, m, K, REPLICAS, semilla=int(ini))
    rep.to_csv(RESULTADOS / f"bootstrap_{per}.csv", index=False)
    comparadores = [REGLA, LOGIT, PUB] + [n for n in S if n not in (FINAL, REGLA, LOGIT, PUB, "oraculo")]
    C = {c: contraste(rep, FINAL, c, usd) for c in comparadores}
    log(per, "bootstrap listo")

    sin = m <= tope
    m_tope = np.minimum(m, tope)
    rob = {"sin_top1": {}, "topado": {}, "K": {}}
    for c in (REGLA, LOGIT, PUB, "R_monto"):
        a = dinero(S[FINAL][sin], d[sin], y[sin], m[sin], K)
        b = dinero(S[c][sin], d[sin], y[sin], m[sin], K)
        rob["sin_top1"][c] = a / b - 1
        rob["topado"][c] = dinero(S[FINAL], d, y, m_tope, K) / dinero(S[c], d, y, m_tope, K) - 1
        rob["K"][c] = {str(k): dinero(S[FINAL], d, y, m, k) / dinero(S[c], d, y, m, k) - 1 for k in KS}
    diario = pd.DataFrame({n: por_dia(S[n], d, y, m, K) for n in (FINAL, REGLA, LOGIT, PUB, "R_monto", "oraculo")})
    diario.insert(0, "periodo", per)
    dias_tabla.append(diario.rename_axis("dia").reset_index())
    gana = {c: int((diario[FINAL] > diario[c]).sum()) for c in (REGLA, LOGIT, PUB)}

    limpio = None
    if per == "P1":
        msk = (d >= LIMPIOS[0]) & (d <= LIMPIOS[1])
        Sl = {n: S[n][msk] for n in (FINAL, REGLA, LOGIT, PUB)}
        ul = {n: dinero(s, d[msk], y[msk], m[msk], K) for n, s in Sl.items()}
        rl = bootstrap(Sl, d[msk], y[msk], m[msk], K, REPLICAS, semilla=7)
        limpio = {"dias": list(LIMPIOS), "usd": ul, "contrastes": {c: contraste(rl, FINAL, c, ul) for c in (REGLA, LOGIT, PUB)}}

    for n, s in S.items():
        base = n.split("|")[0]
        p = P.get(n, P[FINAL] if n == PUB else None)
        mx = matriz(s, d, y, m, K)
        filas.append(dict(periodo=per, politica=n, usd=usd[n], precision=mx["precision"], parte_usd_fraude=mx["parte_usd_fraude"],
                          auc=(auc(y, m) if base == "R_monto" else auc(y, p)) if p is not None else np.nan,
                          usd_K30=dinero(s, d, y, m, 30), usd_K120=dinero(s, d, y, m, 120),
                          usd_sin_top1=dinero(s[sin], d[sin], y[sin], m[sin], K), usd_topado=dinero(s, d, y, m_tope, K)))
    for n in (FINAL, REGLA, LOGIT, PUB, "R_monto", "oraculo"):
        for f, v in zip(FRACCIONES, curva(S[n], d, y, m, FRACCIONES)):
            curvas.append(dict(periodo=per, politica=n, fraccion=float(f), usd=float(v)))

    R[per] = dict(dias=[ini, fin], entrenamiento=len(tr), pagos=len(te), pagos_por_dia=float(len(te) / (fin - ini + 1)),
                  revisiones=int(K * len(np.unique(d))), pagos_fraude=int(y.sum()), usd_fraude=float((y * m).sum()),
                  tope_p99=tope, usd=usd, contrastes=C, robustez=rob, dias_que_gana=gana, n_dias=int(len(np.unique(d))),
                  matriz={n: matriz(S[n], d, y, m, K) for n in (FINAL, REGLA, LOGIT, PUB, "R_monto")},
                  azar_esperado=float(sum(K * (y * m)[d == x].sum() / (d == x).sum() for x in np.unique(d))),
                  limpio=limpio)
    log(per, "listo", {n: round(usd[n]) for n in (FINAL, REGLA, LOGIT, PUB, "oraculo")})

ve = {}
for per in PERIODOS:
    C = R[per]["contrastes"]
    ve[per] = {"H1_regla": C[REGLA]["rel"] >= UMBRAL["H1"] and C[REGLA]["rel_ic95"][0] > 0,
               "H2_logistica": C[LOGIT]["rel"] >= UMBRAL["H2"] and C[LOGIT]["rel_ic95"][0] > 0,
               "H3_publicado": C[PUB]["rel_ic95"][0] > 0}
R["veredicto"] = ve
R["exito"] = all(v for per in PERIODOS for v in ve[per].values())
R["umbrales"] = UMBRAL
(RESULTADOS / "prueba.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
pd.DataFrame(filas).to_csv(RESULTADOS / "prueba.csv", index=False)
pd.concat(dias_tabla).to_csv(RESULTADOS / "prueba_dias.csv", index=False)
pd.DataFrame(curvas).to_csv(RESULTADOS / "prueba_curvas.csv", index=False)
log("veredicto", ve, "éxito", R["exito"])
