"""Variables candidatas para la búsqueda de variables de scripts/06_variables.py.

Reglas de cálculo, iguales a las del protocolo:
- Cada pago ve solo pagos en segundos estrictamente anteriores. Los pagos del mismo segundo no se ven entre sí.
- Ninguna variable de comportamiento usa la etiqueta. El grupo "etiquetas" (historial de contracargos) solo ve
  pagos con 30 días o más de antigüedad, el retraso de la etiqueta que supone el protocolo, y se reporta aparte.
- Lo que depende de la distribución (frecuencias, cuantiles, categorías) se ajusta con el entrenamiento de cada bloque.

No modifica los módulos congelados (datos.py, politicas.py, evaluacion.py): reproduce su matriz de diseño.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.preprocessing import OneHotEncoder, QuantileTransformer

from .datos import CONJUNTOS, DIA, _historial

BASE = np.int64(1 << 25)  # mayor que el último segundo de los datos (182 días)
RETRASO = 30 * DIA

DESCRIPCION = {
    "ventanas": "Velocidad en varias escalas: pagos en la última hora y en 6 horas; dólares en 24 horas y en 7 días (tarjeta y cliente)",
    "perfil": "Perfil del monto: desviación previa, z del monto, razón contra el máximo previo, mismo monto repetido, días desde el primer pago",
    "novedad": "Novedad y diversidad: correos, dispositivos y direcciones distintos ya vistos; si el de hoy es nuevo",
    "compartido": "Entidades compartidas: tarjetas y clientes distintos por dispositivo; tarjetas por dirección + correo",
    "texto": "Cadenas descompuestas: proveedor y país del correo, familia y versión del sistema, navegador y pantalla",
    "monto_fino": "Forma del monto: número de decimales (conversión de moneda), monto entero, terminación .95 o .99",
    "frecuencia": "Frecuencia en el entrenamiento de tarjeta, dirección, correo, dispositivo, navegador, pantalla y cliente",
    "uid_fino": "Cliente fino: tarjeta + dirección + alta + correo, con las mismas cinco medidas de historial",
    "etiquetas": "Historial de contracargos con 30 días de retraso: pagos ya etiquetados y fraudes conocidos por cliente, tarjeta y cliente fino",
}


def _llave(df: pd.DataFrame, campos: list[str]) -> np.ndarray:
    k = df[campos[0]].astype(str)
    for c in campos[1:]:
        k = k + "|" + df[c].astype(str)
    return pd.factorize(k)[0].astype(np.int64)


def _orden(cod: np.ndarray, t: np.ndarray):
    o = np.lexsort((t, cod))
    c, ts = cod[o], t[o]
    k = c * BASE + ts
    return o, c, ts, k, np.searchsorted(k, c * BASE, side="left"), np.searchsorted(k, k, side="left")


def _deshacer(o: np.ndarray, v: np.ndarray) -> np.ndarray:
    out = np.empty(len(o), dtype=float)
    out[o] = v
    return out


def ventanas(t, monto, cod) -> dict[str, np.ndarray]:
    o, c, ts, k, ini, antes = _orden(cod, t)
    acum = np.concatenate([[0.0], np.cumsum(monto[o])])
    out = {}
    for nombre, w in (("n_1h", 3600), ("n_6h", 6 * 3600), ("usd_24h", DIA), ("usd_7d", 7 * DIA)):
        lo = np.searchsorted(k, c * BASE + np.maximum(ts - w, 0), side="left")
        out[nombre] = (antes - lo).astype(float) if nombre.startswith("n_") else acum[antes] - acum[lo]
    return {n: _deshacer(o, v) for n, v in out.items()}


def perfil(t, monto, cod) -> dict[str, np.ndarray]:
    o, c, ts, k, ini, antes = _orden(cod, t)
    a = monto[o]
    s1 = np.concatenate([[0.0], np.cumsum(a)])
    s2 = np.concatenate([[0.0], np.cumsum(a * a)])
    n = antes - ini
    hay = n > 0
    media = np.where(hay, (s1[antes] - s1[ini]) / np.maximum(n, 1), np.nan)
    desv = np.where(hay, np.sqrt(np.maximum((s2[antes] - s2[ini]) / np.maximum(n, 1) - media ** 2, 0)), np.nan)
    maximo = pd.Series(a).groupby(c).cummax().to_numpy()
    previo_max = np.where(hay, maximo[np.maximum(antes - 1, 0)], np.nan)
    llave_monto = pd.factorize(pd.Series(c).astype(str) + "|" + pd.Series(np.round(a * 100).astype(np.int64)).astype(str))[0]
    o2, _, _, _, ini2, antes2 = _orden(llave_monto.astype(np.int64), ts)  # misma llave y mismo monto, estrictamente antes
    mismo = _deshacer(o2, (antes2 - ini2).astype(float))
    out = {"desv": desv, "z": (a - media) / (desv + 1.0), "razon_max": a / previo_max,
           "dias_desde_primero": np.where(hay, (ts - ts[ini]) / DIA, np.nan), "mismo_monto": np.where(hay, mismo, np.nan)}
    return {n: _deshacer(o, v) for n, v in out.items()}


def distintos(t, cod, atributo, valido=None) -> tuple[np.ndarray, np.ndarray]:
    """Valores distintos de `atributo` ya vistos para la llave (estrictamente antes) y si el valor de hoy es nuevo."""
    par = pd.factorize(pd.Series(cod).astype(str) + "|" + pd.Series(atributo).astype(str))[0]
    primero = pd.Series(t).groupby(par).transform("min").to_numpy()
    u = pd.DataFrame({"c": cod, "f": primero, "p": par}).drop_duplicates("p")
    kk = np.sort(u["c"].to_numpy(np.int64) * BASE + u["f"].to_numpy(np.int64))
    vistos = np.searchsorted(kk, cod * BASE + t, side="left") - np.searchsorted(kk, cod * BASE, side="left")
    o, c, ts, k, ini, antes = _orden(cod, t)
    previos = _deshacer(o, (antes - ini).astype(float))
    nuevo = np.where(previos > 0, (primero >= t).astype(float), np.nan)
    vistos = np.where(previos > 0, vistos.astype(float), np.nan)
    if valido is not None:
        vistos, nuevo = np.where(valido, vistos, np.nan), np.where(valido, nuevo, np.nan)
    return vistos, nuevo


def etiquetas(t, y, cod) -> dict[str, np.ndarray]:
    """Pagos de la llave con 30 días o más de antigüedad (etiqueta ya conocida) y cuántos fueron fraude."""
    o, c, ts, k, ini, antes = _orden(cod, t)
    acum = np.concatenate([[0.0], np.cumsum(y[o].astype(float))])
    hasta = np.maximum(np.searchsorted(k, c * BASE + np.maximum(ts - RETRASO, 0), side="right"), ini)
    n, f = (hasta - ini).astype(float), acum[hasta] - acum[ini]
    out = {"conocidos": n, "fraudes": f, "tasa": np.where(n > 0, f / np.maximum(n, 1), np.nan)}
    return {nombre: _deshacer(o, v) for nombre, v in out.items()}


def _version(x: str) -> float:
    """'iOS 11.2.1' → 11.02, 'Mac OS X 10_12_6' → 10.12, 'chrome 63.0' → 63.0: mayor + menor / 100."""
    m = re.search(r"(\d+)(?:[._](\d+))?", x)
    return float(m.group(1)) + min(float(m.group(2) or 0), 99) / 100 if m else np.nan


def _familia(x: str) -> str:
    if x == "NA":
        return "NA"
    m = re.match(r"[a-z]+(?: [a-z]+)?", x.lower().replace("_", " "))
    return m.group(0).strip() if m else "otro"


def _mapa(s: pd.Series, f) -> pd.Series:
    u = s.unique()
    return s.map(dict(zip(u, [f(v) for v in u])))


def agregar(df: pd.DataFrame) -> dict[str, tuple[list[str], list[str]]]:
    """Agrega a df las columnas de cada grupo candidato y devuelve {grupo: (numéricas, categóricas)}.
    df debe venir de datos.cargar(): ordenado en el tiempo, con historial y categóricas como texto."""
    t = df["TransactionDT"].to_numpy(np.int64)
    monto = df["TransactionAmt"].to_numpy(float)
    llaves = {"tarjeta": _llave(df, ["card1"]), "cliente": _llave(df, ["card1", "addr1", "alta"]),
              "uid": _llave(df, ["card1", "addr1", "alta", "P_emaildomain"])}
    grupos: dict[str, tuple[list[str], list[str]]] = {}

    def poner(grupo, nombre, v, cat=False):
        df[nombre] = v
        num, cats = grupos.setdefault(grupo, ([], []))
        (cats if cat else num).append(nombre)

    for ll in ("tarjeta", "cliente"):
        for n, v in ventanas(t, monto, llaves[ll]).items():
            poner("ventanas", f"v_{ll}_{n}", v)
        for n, v in perfil(t, monto, llaves[ll]).items():
            poner("perfil", f"p_{ll}_{n}", v)

    for ll, atributos in (("cliente", ("P_emaildomain", "DeviceInfo", "id_31")), ("tarjeta", ("addr1", "P_emaildomain", "DeviceInfo"))):
        for a in atributos:
            vistos, nuevo = distintos(t, llaves[ll], df[a].to_numpy())
            poner("novedad", f"n_{ll}_{a}_distintos", vistos)
            poner("novedad", f"n_{ll}_{a}_nuevo", nuevo)
    vistos, _ = distintos(t, llaves["tarjeta"], llaves["cliente"])
    poner("novedad", "n_tarjeta_clientes_distintos", vistos)

    con_disp = (df["DeviceInfo"] != "NA").to_numpy()
    disp = _llave(df, ["DeviceInfo", "id_30", "id_31", "id_33"])
    for nombre, cod, atributo, valido in (
            ("c_disp_tarjetas", disp, llaves["tarjeta"], con_disp),
            ("c_disp_clientes", disp, llaves["cliente"], con_disp),
            ("c_dircorreo_tarjetas", _llave(df, ["addr1", "P_emaildomain"]), llaves["tarjeta"],
             ((df["addr1"] != "NA") & (df["P_emaildomain"] != "NA")).to_numpy())):
        vistos, _ = distintos(t, cod, atributo, valido)
        poner("compartido", nombre, vistos)

    p, r = df["P_emaildomain"], df["R_emaildomain"]
    poner("texto", "t_correo_proveedor", _mapa(p, lambda x: x.split(".")[0]), cat=True)
    poner("texto", "t_correo_pais", _mapa(p, lambda x: x.rsplit(".", 1)[-1] if "." in x else "NA"), cat=True)
    poner("texto", "t_correo_igual", np.where((p != "NA") & (r != "NA"), (p == r).astype(float), np.nan))
    poner("texto", "t_disp_familia", _mapa(df["DeviceInfo"], _familia), cat=True)
    poner("texto", "t_so_familia", _mapa(df["id_30"], _familia), cat=True)
    poner("texto", "t_so_version", _mapa(df["id_30"], lambda x: np.nan if x == "NA" else _version(x)).astype(float))
    poner("texto", "t_nav_familia", _mapa(df["id_31"], _familia), cat=True)
    poner("texto", "t_nav_version", _mapa(df["id_31"], lambda x: np.nan if x == "NA" else _version(x)).astype(float))
    wh = df["id_33"].str.extract(r"^(\d+)x(\d+)$").astype(float)
    poner("texto", "t_pantalla_area", (wh[0] * wh[1]).to_numpy())
    poner("texto", "t_pantalla_razon", (wh[0] / wh[1]).to_numpy())

    cent = np.round(monto * 1000).astype(np.int64) % 1000
    poner("monto_fino", "m_decimales", np.where(cent == 0, 0, np.where(cent % 100 == 0, 1, np.where(cent % 10 == 0, 2, 3))).astype(float))
    poner("monto_fino", "m_entero", (cent == 0).astype(float))
    poner("monto_fino", "m_termina_95_99", np.isin(cent, (950, 990)).astype(float))

    df["uid_cliente"] = llaves["cliente"].astype(str)
    grupos["frecuencia"] = ([], [])  # se calculan en el diseño, con el entrenamiento de cada bloque

    for e, v in _historial(t, monto, llaves["uid"]).items():
        poner("uid_fino", f"h_uid_{e}", v)

    y = df["fraude"].to_numpy(int)
    for ll in ("cliente", "tarjeta", "uid"):
        for n, v in etiquetas(t, y, llaves[ll]).items():
            poner("etiquetas", f"e_{ll}_{n}", v)
    return grupos


FRECUENCIA = ["card1", "card2", "card5", "addr1", "P_emaildomain", "DeviceInfo", "id_31", "id_33", "uid_cliente"]


class DisenoUnion:
    """Matriz de diseño del protocolo (cuantiles → normal, indicador de faltante, one-hot con mínimo de 50) para
    F3 y todos los grupos candidatos, más la frecuencia en el entrenamiento. Cada configuración toma columnas de
    esta matriz: el resultado es idéntico a construir su propia matriz, porque cada transformación es por columna."""

    def __init__(self, tr: pd.DataFrame, grupos: dict[str, tuple[list[str], list[str]]]):
        num0, cat0 = CONJUNTOS["F3"]
        self.num = list(num0) + [c for g in grupos.values() for c in g[0]]
        self.cat = list(cat0) + [c for g in grupos.values() for c in g[1]]
        X = tr[self.num].to_numpy(float)
        self.mediana = np.nanmedian(X, axis=0)
        self.mediana = np.where(np.isnan(self.mediana), 0.0, self.mediana)
        self.qt = QuantileTransformer(n_quantiles=200, output_distribution="normal", subsample=200_000, random_state=0)
        self.qt.fit(np.where(np.isnan(X), self.mediana, X))
        self.oh = OneHotEncoder(min_frequency=50, handle_unknown="infrequent_if_exist", sparse_output=True).fit(tr[self.cat])
        self.frec = {c: tr[c].value_counts() for c in FRECUENCIA}
        cols: dict[str, list[int]] = {}
        n = len(self.num)
        for i, c in enumerate(self.num):
            cols[c] = [i, n + i]  # valor transformado e indicador de faltante
        nombres = self.oh.get_feature_names_out(self.cat)
        pos = 0
        for c in self.cat:  # el one-hot deja las columnas de cada categórica juntas y en orden
            ini = pos
            while pos < len(nombres) and nombres[pos].startswith(c + "_"):
                pos += 1
            cols[c] = list(range(2 * n + ini, 2 * n + pos))
        assert pos == len(nombres), "columnas one-hot sin asignar"
        j = 2 * n + len(nombres)
        for i, c in enumerate(FRECUENCIA):
            cols[f"f_{c}"] = [j + i]
        self.columnas = cols
        self.grupos = {g: v[0] + v[1] for g, v in grupos.items()}
        self.grupos["frecuencia"] = [f"f_{c}" for c in FRECUENCIA]
        self.base = list(num0) + list(cat0)

    def matriz(self, d: pd.DataFrame) -> sp.csc_matrix:
        X = d[self.num].to_numpy(float)
        falta = np.isnan(X)
        Z = self.qt.transform(np.where(falta, self.mediana, X))
        F = np.column_stack([np.log1p(d[c].map(self.frec[c]).fillna(0).to_numpy(float)) for c in FRECUENCIA])
        return sp.hstack([sp.csr_matrix(Z), sp.csr_matrix(falta.astype(float)), self.oh.transform(d[self.cat]),
                          sp.csr_matrix(F)]).tocsc()

    def indices(self, elegidos: list[str]) -> np.ndarray:
        variables = self.base + [v for g in elegidos for v in self.grupos[g]]
        return np.array(sorted({i for v in variables for i in self.columnas[v]}))


def parada_temprana(A, y, dias_tr, B, params: dict, tope: int = 4000, paciencia: int = 150, dias_validacion: int = 10):
    """XGBoost con parada temprana: valida con los últimos días del entrenamiento (en orden de tiempo), elige el
    número de árboles por pérdida logarítmica y reentrena con todo el entrenamiento y 10% más de árboles.
    Devuelve la probabilidad para B, el mejor número de árboles y la curva de aprendizaje."""
    import xgboost as xgb

    ajuste = dias_tr < dias_tr.max() - dias_validacion + 1
    muestra = np.random.default_rng(0).choice(np.flatnonzero(ajuste), size=min(50_000, int(ajuste.sum())), replace=False)
    mod = xgb.XGBClassifier(**{**params, "n_estimators": tope, "early_stopping_rounds": paciencia, "eval_metric": "logloss"})
    mod.fit(A[ajuste], y[ajuste], eval_set=[(A[muestra], y[muestra]), (A[~ajuste], y[~ajuste])], verbose=False)
    mejor = int(mod.best_iteration) + 1
    final = xgb.XGBClassifier(**{**params, "n_estimators": int(round(mejor * 1.1))}).fit(A, y)
    curva = mod.evals_result()
    return final.predict_proba(B)[:, 1], mejor, {"entrenamiento": curva["validation_0"]["logloss"],
                                                 "validacion": curva["validation_1"]["logloss"]}
