"""Lectura de los pagos de Vesta (IEEE-CIS, copia de OpenML 46858) y variables conocidas al cierre del día.

Toda lectura filtra por tiempo al abrir el archivo: `cargar(hasta_dia)` no devuelve pagos del día `hasta_dia`
ni posteriores. El historial de cada pago usa solo pagos en segundos estrictamente anteriores y nunca etiquetas.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from .rutas import CRUDOS, RAIZ

FUENTE = json.loads((RAIZ / "datos" / "fuente.json").read_text(encoding="utf-8"))
ARCHIVO = CRUDOS / "openml-46858" / "openml-46858.parquet"
DIA = 86400
PRIMER_DIA_PRUEBA = 121

NUM = ["TransactionAmt", "dist1", "dist2"] + [f"id_{i:02d}" for i in range(1, 12)] + \
      ["id_13", "id_14", "id_17", "id_18", "id_19", "id_20", "id_21", "id_22", "id_24", "id_25", "id_26", "id_32"]
CAT = ["ProductCD", "card1", "card2", "card3", "card4", "card5", "card6", "addr1", "addr2",
       "P_emaildomain", "R_emaildomain"] + [f"M{i}" for i in range(1, 10)] + \
      ["DeviceType", "DeviceInfo", "id_12", "id_15", "id_16", "id_23", "id_27", "id_28", "id_29", "id_30",
       "id_31", "id_33", "id_34", "id_35", "id_36", "id_37", "id_38"]
DERIVADAS = ["log_monto", "centavos", "hora", "dia_semana"]
VESTA = [f"C{i}" for i in range(1, 15)] + [f"D{i}" for i in range(2, 16)] + [f"V{i}" for i in range(1, 340)]

CLAVES = {"tarjeta": ["card1"], "tarjeta_dir": ["card1", "addr1"], "tarjeta_dir_correo": ["card1", "addr1", "P_emaildomain"],
          "tarjeta_completa": ["card1", "card2", "card3", "card4", "card5", "card6"],
          "cliente": ["card1", "addr1", "alta"]}
ESTADISTICAS = ["previos", "ultimo_dia", "ultima_semana", "segundos_desde", "razon_monto"]


def historial(nombre: str) -> list[str]:
    return [f"h_{nombre}_{e}" for e in ESTADISTICAS]


CONJUNTOS = {
    "F1": (NUM + DERIVADAS, CAT),
    "F2": (NUM + DERIVADAS + sum((historial(k) for k in CLAVES if k != "cliente"), []), CAT),
    "F3": (NUM + DERIVADAS + sum((historial(k) for k in CLAVES), []) + ["D1"], CAT),
}
CONJUNTOS["F4"] = (CONJUNTOS["F3"][0] + VESTA, CAT)


def verificar_fuente() -> None:
    h = hashlib.sha256(ARCHIVO.read_bytes()).hexdigest()
    if h != FUENTE["sha256"]:
        raise SystemExit(f"El archivo de datos no coincide con datos/fuente.json: {h}")


def _historial(t: np.ndarray, monto: np.ndarray, codigos: np.ndarray) -> dict[str, np.ndarray]:
    """Recencia, frecuencia y desvío del monto por clave, solo con pagos en segundos estrictamente anteriores."""
    base = np.int64(1 << 25)
    orden = np.lexsort((t, codigos))
    c = codigos[orden].astype(np.int64)
    ts = t[orden]
    a = monto[orden]
    k = c * base + ts
    inicio = np.searchsorted(k, c * base, side="left")
    antes = np.searchsorted(k, k, side="left")
    previos = antes - inicio
    hay = previos > 0
    acum = np.concatenate([[0.0], np.cumsum(a)])
    media_previa = np.where(hay, (acum[antes] - acum[inicio]) / np.maximum(previos, 1), np.nan)
    salida = {
        "previos": previos.astype(float),
        "ultimo_dia": (antes - np.searchsorted(k, c * base + np.maximum(ts - DIA, 0), side="left")).astype(float),
        "ultima_semana": (antes - np.searchsorted(k, c * base + np.maximum(ts - 7 * DIA, 0), side="left")).astype(float),
        "segundos_desde": np.where(hay, ts - ts[np.maximum(antes - 1, 0)], np.nan).astype(float),
        "razon_monto": np.where(hay, a / np.where(hay, media_previa, 1.0), np.nan),
    }
    inverso = np.empty_like(orden)
    inverso[orden] = np.arange(len(orden))
    return {e: v[inverso] for e, v in salida.items()}


def cargar(hasta_dia: int, vesta: bool = False) -> pd.DataFrame:
    """Pagos de los días 1 a hasta_dia - 1, ordenados en el tiempo, con variables derivadas e historial."""
    cols = ["isFraud", "TransactionDT"] + NUM + CAT + ["D1"] + (VESTA if vesta else [])
    tabla = pq.read_table(ARCHIVO, columns=cols, filters=[("TransactionDT", "<", hasta_dia * DIA)])
    df = tabla.to_pandas()
    assert df["TransactionDT"].max() < hasta_dia * DIA
    df["fraude"] = df.pop("isFraud").astype(str).astype(float).astype(int)
    df = df.sort_values("TransactionDT", kind="stable").reset_index(drop=True)
    t = df["TransactionDT"].to_numpy(np.int64)
    monto = df["TransactionAmt"].to_numpy(float)
    df["dia"] = (t // DIA).astype(int)
    df["hora"] = ((t % DIA) // 3600).astype(float)
    df["dia_semana"] = (df["dia"] % 7).astype(float)
    df["centavos"] = np.round(monto - np.floor(monto), 3)
    df["log_monto"] = np.log1p(monto)
    df["alta"] = np.floor(df["dia"] - df["D1"])
    for c in CAT:
        df[c] = df[c].astype(str).replace({"nan": "NA", "None": "NA"})
    for nombre, campos in CLAVES.items():
        clave = df[campos[0]].astype(str)
        for c in campos[1:]:
            clave = clave + "|" + df[c].astype(str)
        codigos, _ = pd.factorize(clave)
        for e, v in _historial(t, monto, codigos).items():
            df[f"h_{nombre}_{e}"] = v
    return df


def bloque(df: pd.DataFrame, inicio: int, fin: int, margen: int = 30) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Entrenamiento (días < inicio - margen) y evaluación (días inicio a fin, inclusive)."""
    return (df[df["dia"] < inicio - margen].reset_index(drop=True),
            df[(df["dia"] >= inicio) & (df["dia"] <= fin)].reset_index(drop=True))
