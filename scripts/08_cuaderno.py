"""Construye y ejecuta notebooks/que_pagos_revisar.ipynb: el caso completo, ordenado por las fases de CRISP-DM.

El cuaderno sigue los requisitos del proyecto final fase por fase. Corre desde los datos crudos (verifica su huella),
rehace el análisis exploratorio y la preparación con los días 1-120, vuelve a entrenar el modelo final de la prueba,
recalcula la evaluación desde el puntaje de cada pago (dólares, matriz
de confusión, métricas, bootstrap) y compara el veredicto con el protocolo congelado. El código importante se imprime
desde src/revisar/ con inspect, así que lo que se lee es lo que corre.

Requiere los scripts 00 a 07 (datos, resultados/ y puntajes en datos/procesados) y las figuras de la presentación.
Uso: python scripts/08_cuaderno.py
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "notebooks" / "que_pagos_revisar.ipynb"

M = nbf.v4.new_markdown_cell
C = nbf.v4.new_code_cell

INICIO = [
    M(r"""# Qué pagos revisar

**Minería de Datos, ITAM · Proyecto final · Metodología CRISP-DM**

Al cierre de cada día, el equipo de riesgo de un procesador de pagos puede mandar 60 pagos ya autorizados a revisión
manual. Un fraude revisado se detiene antes del contracargo; uno que no se revisa se pierde completo. La pregunta del
proyecto es **qué 60 pagos conviene revisar cada noche para detener la mayor cantidad de dólares de fraude**.

Este cuaderno es el código del proyecto, ejecutado de principio a fin:

- **Corre desde los datos crudos.** Verifica la huella del archivo público, rehace el análisis exploratorio y la
  preparación con los días 1–120 y vuelve a entrenar aquí el modelo final con el código de la prueba.
- **Recalcula la evaluación.** Los dólares, la matriz de confusión, las métricas y los intervalos se calculan aquí
  desde el puntaje de cada pago, y el veredicto se compara con el protocolo congelado (`docs/protocolo.md`).
- **Muestra el código que importa.** Las funciones del proyecto se imprimen desde `src/revisar/`: lo que se lee es
  exactamente lo que corre.

Para reproducirlo: `python scripts/00_descargar.py` baja los datos (78 MB) y `python scripts/08_cuaderno.py` ejecuta
este cuaderno. El `README.md` lista el orden completo de los scripts."""),
    M(r"""## Requisitos del proyecto y dónde se cumplen

| Fase | Lo que pide el proyecto | Sección |
|---|---|---|
| 1 · Negocio | Definición del problema | 1.1 |
| | Objetivos: qué impacto se espera | 1.2 |
| | Criterios de éxito desde el negocio | 1.3 |
| 2 · Datos | Fuentes de datos: origen y cómo se obtuvieron | 2.1 |
| | Análisis exploratorio: visualizaciones, estadísticas descriptivas y hallazgos | 2.2 |
| | Calidad: faltantes, ruido e inconsistencias | 2.3 |
| 3 · Preparación | Limpieza: nulos y valores extremos | 3.1 |
| | Ingeniería de características: variables nuevas, normalización y codificación | 3.2 |
| | Selección de variables, justificada | 3.3 |
| 4 · Modelado | Selección de algoritmos, justificada | 4.1 |
| | Entrenamiento: partición de los datos | 4.2 |
| | Optimización de hiperparámetros | 4.3 |
| 5 · Evaluación | Métricas de desempeño: matriz de confusión, F1 y otras | 5.1 |
| | Validación de negocio: ¿responde la pregunta de la fase 1? | 5.2 |
| 6 · Despliegue | Propuesta de implementación en producción | 6.1 |
| | Mantenimiento: monitoreo de la degradación del modelo | 6.2 |
| Código | Reproducible y documentado | todo el cuaderno; 0, 2.1 y 4.2 |"""),
    M(r"""## 0. Entorno

Versiones fijadas en `pyproject.toml` (Python 3.12). Las rutas de los datos salen de `src/revisar/rutas.py`. Dos
ayudas de este cuaderno: `codigo(...)` imprime el código fuente de una función del proyecto y `fig(...)` muestra una
figura del proyecto (las mismas de la presentación, dibujadas desde `resultados/`)."""),
    C(r"""import inspect, json, os, platform, sys, time, warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import sklearn, xgboost
from IPython.display import SVG, Markdown, display
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, roc_auc_score

T0 = time.time()
warnings.filterwarnings("ignore")
pd.set_option("display.width", 160); pd.set_option("display.max_columns", 30)
pd.set_option("display.max_colwidth", 220); pd.set_option("display.precision", 3)
RAIZ = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(RAIZ / "src"))
from revisar.datos import (ARCHIVO, CAT, CLAVES, CONJUNTOS, DERIVADAS, ESTADISTICAS, FUENTE, NUM, VESTA, _historial,
                           bloque, cargar, verificar_fuente)
from revisar.evaluacion import bootstrap, dinero, matriz, por_dia, seleccion
from revisar.figuras import autonomo, laminas
from revisar.politicas import CART, CS, FLEXIBLES, ISO, MLP, REGLAS, RF, XGB, Diseno, _tasa, modelos, puntaje, reglas
from revisar.rutas import PROCESADOS

AZUL, NARANJA, GRIS = "#076bb1", "#bf5128", "#8793a4"
plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#e0e5ec", "axes.edgecolor": "#a5aebc", "font.size": 10})


def codigo(*objetos):
    # Imprime el código fuente de funciones o clases del proyecto, tal como está en src/revisar/.
    for o in objetos:
        ruta = Path(os.path.relpath(inspect.getsourcefile(o), RAIZ)).as_posix()
        display(Markdown(f"`{ruta}` · `{o.__name__}`\n\n```python\n{inspect.getsource(o).rstrip()}\n```"))


def fig(*claves):
    # Figuras del proyecto (las de la presentación), dibujadas desde resultados/.
    for c in claves:
        display(SVG(autonomo(FIG[c])))


leer = lambda n: json.loads((RAIZ / "resultados" / n).read_text(encoding="utf-8"))
S, R, X, E = leer("desarrollo_seleccion.json"), leer("prueba.json"), leer("exploracion.json"), leer("eda.json")
L, CC, PJ = leer("lecciones.json"), leer("curvas_curso.json"), leer("presentacion.json")
VA, AX = leer("variables.json"), leer("anexo_prueba_variables.json")
FINAL, REGLA, LOGIT, PUB = S["final"], S["mejor_regla"], S["mejor_logit"], "PUBLICADO"
K, P = S["K"], {"P1": (121, 151), "P2": (152, 182)}
NOMBRE = {FINAL: "Modelo: XGBoost con F3", LOGIT: "Mejor logística (C = 0.003, F3)", REGLA: "Mejor regla: tasa por segmento × monto",
          PUB: "Solo probabilidad (enfoque de la competencia)", "R_monto": "Mayor monto primero", "oraculo": "Oráculo (conoce las etiquetas)"}
FIG = laminas()
mil = lambda x: round(x / 1e3, 1)
pc = lambda x: f"{x * 100:+.1f}%"
ic = lambda par: f"{par[0] * 100:+.1f}% a {par[1] * 100:+.1f}%"
print(f"Python {platform.python_version()} · numpy {np.__version__} · pandas {pd.__version__} · "
      f"scikit-learn {sklearn.__version__} · xgboost {xgboost.__version__}")
print(f"Modelo final: {FINAL} · mejor regla: {REGLA} · mejor logística: {LOGIT} · cupo: {K} revisiones por día")"""),
]

NEGOCIO = [
    M(r"""## 1. Comprensión del negocio

### 1.1 Definición del problema

| Pregunta | Respuesta |
|---|---|
| Quién decide | El equipo de riesgo del procesador de pagos (Vesta). |
| Cuándo | Al cierre de cada día, sobre los pagos ya autorizados, con la información disponible hasta ese momento. |
| Qué decide | Mandar cada pago a revisión manual o dejarlo pasar. |
| Recurso | 60 revisiones por día, cerca de 2% de los pagos; el mismo cupo para todas las políticas. |
| Qué se pierde | Un fraude que no se revisa termina en contracargo: se pierde el monto completo. |
| Práctica actual | Vesta no la publica; la representa la mejor regla del periodo de desarrollo. |

El problema no es clasificar cada pago como fraude o legítimo, sino **ordenar** los pagos del día: con un cupo fijo,
cada revisión que se va a un pago legítimo o a un fraude pequeño deja fuera un fraude más grande."""),
    C(r"""fig("arbol")"""),
    M(r"""**La matriz de confusión en dólares.** La métrica de la decisión es una sola celda:

| | El pago es fraude | El pago es legítimo |
|---|---|---|
| Se revisa | Fraude detenido: **la métrica que se maximiza** | Una revisión usada sin recuperar nada |
| No se revisa | Contracargo: se pierde el monto completo | Sin costo |

**Cómo se ordena la cola.** El modelo estima la probabilidad de fraude de cada pago y la multiplica por el monto: el
resultado es el fraude esperado en dólares. Cada noche se revisan los 60 pagos con mayor fraude esperado. La figura
muestra un día real de la prueba (día 166) con las probabilidades del modelo congelado; la sección 5.1 comprueba que
esas probabilidades están calibradas."""),
    C(r"""fig("cola_dia")"""),
    M(r"""**Cómo leer la línea.** Es el corte del día: arriba quedan los 60 pagos con mayor fraude esperado (44 USD o más).
Un fraude de 30 USD con 80% de probabilidad vale 24 USD esperados y queda abajo; uno de 554 USD con 10% vale 56 y
entra. Por eso pasan fraudes con probabilidad alta: son pagos chicos, y la cola los cambia por pagos caros de
probabilidad media. **Es la regla óptima para este objetivo**: si cada revisión cuesta lo mismo y las probabilidades
están calibradas, el fraude esperado de la cola es la suma de probabilidad × monto de sus pagos, y los 60 con mayor
producto maximizan esa suma. La sección 5.1 lo mide: en los dos meses de prueba, ordenar por fraude esperado detiene
casi el doble de dólares que ordenar solo por probabilidad."""),
    M(r"""### 1.2 Objetivos

- **Objetivo de negocio.** Detener más dólares de fraude con las mismas 60 revisiones diarias: el mismo equipo y el
  mismo cupo; solo cambia qué pagos entran a la cola.
- **Objetivo de minería de datos.** Estimar, con la información disponible al cierre del día, la probabilidad de que
  cada pago sea fraude, y ordenar la cola por probabilidad × monto.
- **Impacto esperado.** El periodo de desarrollo (días 61–120) dio la referencia antes de abrir la prueba: cuánto fraude
  detenía el modelo elegido y su ventaja contra la mejor regla y la mejor logística."""),
    C(r"""ib = S["info_bloques"]
pd.DataFrame({b: {"fraude del bloque (mil USD)": mil(ib[b]["usd_fraude"]), "modelo (mil USD)": mil(S["dolares"][FINAL][b]),
                  "mejor regla (mil USD)": mil(S["dolares"][REGLA][b]), "mejor logística (mil USD)": mil(S["dolares"][LOGIT][b]),
                  "ventaja contra la regla": pc(S["ventaja"][REGLA][b]), "ventaja contra la logística": pc(S["ventaja"][LOGIT][b])}
              for b in ("D1", "D2")}).rename(columns={"D1": "D1: días 61–90", "D2": "D2: días 91–120"})"""),
    M(r"""### 1.3 Criterios de éxito

El éxito se mide en dólares de fraude dentro de la cola, con el mismo cupo, en dos meses que no se usaron para ninguna
decisión (días 121–151 y 152–182). Las metas se fijaron antes de abrir la prueba (`docs/protocolo.md`) y se piden en
**cada** mes:"""),
    C(r"""U = R["umbrales"]
pd.DataFrame({"Comparador": ["Mejor regla (práctica actual)", "Mejor logística (misma información)", "Mismo modelo ordenado solo por probabilidad"],
              "Condición": [f"ventaja ≥ {U['H1']:.0%} y límite inferior del IC 95% > 0", f"ventaja ≥ {U['H2']:.0%} y límite inferior del IC 95% > 0",
                            "límite inferior del IC 95% > 0"]}, index=["H1", "H2", "H3"])"""),
    M(r"""**El caso tiene éxito si H1, H2 y H3 se cumplen en los dos meses.** El intervalo pareado (bootstrap de días) descarta
que la ventaja sea azar de qué días cayeron en la prueba. El criterio no es el AUC: un AUC más alto no implica más
dinero detenido (sección 5.1)."""),
]

DATOS = [
    M(r"""## 2. Comprensión de los datos

### 2.1 Fuentes de datos

- **Origen.** Pagos reales de comercio electrónico de Vesta Corporation, publicados para la competencia
  *IEEE-CIS Fraud Detection* (Kaggle, 2019). Se usa el archivo de entrenamiento, el único con etiqueta: transacciones
  e identidad unidas, 590,540 pagos en 182 días.
- **Cómo se obtuvieron.** De la copia pública en OpenML (conjunto 46858, en Parquet), que no pide cuenta de Kaggle.
  `scripts/00_descargar.py` la baja y compara su huella SHA-256 con la registrada en `datos/fuente.json`; si no
  coincide, descarta el archivo.
- **Etiqueta.** `isFraud` sigue la regla de Vesta: un pago con contracargo es fraude, y la marca se propaga a los pagos
  posteriores de la misma cuenta, dirección o correo.
- **Tiempo.** `TransactionDT` cuenta segundos desde una fecha de referencia que Vesta no publica: hay día y hora
  relativos, no fechas de calendario."""),
    C(r"""display(pd.Series(FUENTE).rename("datos/fuente.json").to_frame())
codigo(verificar_fuente)
verificar_fuente()
meta = pq.ParquetFile(ARCHIVO).metadata
print(f"Huella SHA-256 verificada: {meta.num_rows:,} pagos y {meta.num_columns} columnas.")"""),
    M(r"""**Las columnas, por grupo.** Vesta enmascara el significado de muchas: `card1–card6`, `addr`, `M1–M9` e `id_*`
tienen nombre genérico, y las columnas `C`, `D2–D15` y `V` son conteos y medidas propias de Vesta que la descripción
pública no explica."""),
    C(r"""cols = pq.read_schema(ARCHIVO).names
grupos = {"Etiqueta": ["isFraud"], "Tiempo": ["TransactionDT"], "Monto y producto": ["TransactionAmt", "ProductCD"],
          "Tarjeta": [c for c in cols if c.startswith("card")], "Dirección y distancia": ["addr1", "addr2", "dist1", "dist2"],
          "Correo": ["P_emaildomain", "R_emaildomain"], "Coincidencias M1–M9": [f"M{i}" for i in range(1, 10)],
          "Dispositivo e identidad": ["DeviceType", "DeviceInfo"] + [c for c in cols if c.startswith("id_")],
          "Antigüedad de la cuenta (D1)": ["D1"], "Opacas de Vesta (C1–C14, D2–D15, V1–V339)": VESTA,
          "Vacías en esta copia (id-01 a id-38, con guion)": [c for c in cols if c.startswith("id-")]}
vacias = pq.read_table(ARCHIVO, columns=grupos["Vacías en esta copia (id-01 a id-38, con guion)"])
assert all(vacias[c].null_count == vacias.num_rows for c in vacias.column_names), "las columnas id-xx deben estar vacías"
otras = [c for c in cols if not any(c in v for v in grupos.values())]
usa = set(NUM + CAT + ["D1"])
display(pd.DataFrame({"columnas": {g: len(v) for g, v in grupos.items()},
                      "las usa el modelo": {g: sum(c in usa for c in v) for g, v in grupos.items()},
                      "ejemplos": {g: ", ".join(v[:5]) + (" …" if len(v) > 5 else "") for g, v in grupos.items()}}))
print("Otras columnas:", otras or "ninguna")"""),
    M(r"""**Carga de los días 1 a 120.** `cargar(hasta_dia)` filtra por tiempo al leer el archivo: en las secciones 2 y 3 los
días de la prueba (121–182) ni siquiera se cargan. Su código está en la sección 3.2."""),
    C(r"""t0 = time.time()
dev = cargar(121)
assert dev["dia"].max() < 121
print(f"Días {dev['dia'].min()}–{dev['dia'].max()}: {len(dev):,} pagos y {dev.shape[1]} columnas, cargados en {time.time() - t0:.0f} s")"""),
    M(r"""### 2.2 Análisis exploratorio (días 1–120)

**Estadísticas generales.**"""),
    C(r"""uf = dev["TransactionAmt"] * dev["fraude"]          # dólares de fraude de cada pago
pagos_dia = dev.groupby("dia").size()
pd.Series({"Pagos": f"{len(dev):,}", "Días": dev["dia"].nunique(), "Pagos por día (mediana)": f"{pagos_dia.median():,.0f}",
           "Tasa de fraude": f"{dev['fraude'].mean():.2%}", "Dólares cobrados (millones)": f"{dev['TransactionAmt'].sum() / 1e6:,.1f}",
           "Dólares de fraude (miles)": f"{uf.sum() / 1e3:,.0f}", "Parte de los dólares que es fraude": f"{uf.sum() / dev['TransactionAmt'].sum():.2%}",
           "Cupo de 60 como parte de los pagos del día": f"{60 / pagos_dia.median():.1%}"}).to_frame("valor")"""),
    M(r"""**Estadísticas descriptivas por clase.** Monto, hora, antigüedad de la cuenta y el historial del cliente (que se
construye en la sección 3.2)."""),
    C(r"""variables = {"Monto (USD)": dev["TransactionAmt"], "Hora del día": dev["hora"], "Días desde el alta (D1)": dev["D1"],
             "Distancia (dist1)": dev["dist1"], "Pagos previos del cliente": dev["h_cliente_previos"],
             "Horas desde su pago anterior": dev["h_cliente_segundos_desde"] / 3600}
filas = {}
for nombre, v in variables.items():
    for clase, msk in (("fraude", dev["fraude"] == 1), ("legítimo", dev["fraude"] == 0)):
        w = v[msk].dropna()
        filas[(nombre, clase)] = {"con dato": w.size / msk.sum(), "media": w.mean(), "p10": w.quantile(.1), "p25": w.quantile(.25),
                                  "mediana": w.median(), "p75": w.quantile(.75), "p90": w.quantile(.9)}
pd.DataFrame.from_dict(filas, orient="index").round(2)"""),
    C(r"""fig("eda_matriz")"""),
    M(r"""La matriz de dispersión usa 300 fraudes y 300 legítimos al azar; la diagonal tiene el histograma de cada clase. En
cada par de variables las nubes se enciman: ningún corte simple separa el fraude.

**Tasa de fraude por categoría.**"""),
    C(r"""def por_categoria(col, n=6):
    g = pd.DataFrame({"pagos": dev.groupby(col).size(), "tasa de fraude": dev.groupby(col)["fraude"].mean(),
                      "parte del fraude en USD": uf.groupby(dev[col]).sum() / uf.sum()})
    return g.sort_values("pagos", ascending=False).head(n)


cat = pd.concat({c: por_categoria(c) for c in ("ProductCD", "card4", "card6", "DeviceType")}, names=["variable", "categoría"])
cat.assign(pagos=cat["pagos"].map("{:,}".format), **{"tasa de fraude": cat["tasa de fraude"].map("{:.1%}".format),
                                                     "parte del fraude en USD": cat["parte del fraude en USD"].map("{:.0%}".format)})"""),
    C(r"""fig("eda_clases")"""),
    M(r"""**Dónde está el dinero: deciles de monto.**"""),
    C(r"""decil = pd.qcut(dev["TransactionAmt"].rank(method="first"), 10, labels=range(1, 11))
dd = pd.DataFrame({"monto máximo (USD)": dev.groupby(decil)["TransactionAmt"].max(), "tasa de fraude": dev.groupby(decil)["fraude"].mean(),
                   "parte del fraude en USD": uf.groupby(decil).sum() / uf.sum()}).rename_axis("decil de monto")
dd.assign(**{"tasa de fraude": dd["tasa de fraude"].map("{:.1%}".format), "parte del fraude en USD": dd["parte del fraude en USD"].map("{:.0%}".format)})"""),
    C(r"""fig("deciles")"""),
    M(r"""**En el tiempo.** Pagos y tasa de fraude por día."""),
    C(r"""dia = pd.DataFrame({"pagos": pagos_dia, "tasa": dev.groupby("dia")["fraude"].mean(), "usd": uf.groupby(dev["dia"]).sum()})
f, ax = plt.subplots(1, 3, figsize=(13, 3))
ax[0].plot(dia.index, dia["pagos"], color=GRIS); ax[0].set_title("Pagos por día")
ax[1].plot(dia.index, dia["tasa"] * 100, color=NARANJA); ax[1].set_title("Tasa de fraude por día (%)")
ax[2].bar(dia.index, dia["usd"] / 1e3, color=NARANJA, width=1); ax[2].set_title("Dólares de fraude por día (miles)")
for a in ax:
    a.set_xlabel("día")
plt.tight_layout(); plt.show()
print(f"Tasa diaria de fraude: de {dia['tasa'].min():.1%} a {dia['tasa'].max():.1%}; "
      f"fraude diario: mediana {dia['usd'].median():,.0f} USD, máximo {dia['usd'].max():,.0f} USD")"""),
    C(r"""fr, lg = dev["fraude"] == 1, dev["fraude"] == 0
alta_1_7 = dev.loc[dev["D1"].between(1, 7), "fraude"].mean()
horas = dev.groupby("hora")["fraude"].mean()
Markdown(f'''**Hallazgos iniciales**

1. **El fraude es raro y caro.** {dev['fraude'].mean():.1%} de los pagos es fraude, pero suma {uf.sum() / 1e3:,.0f} mil USD en
   120 días, unos {dia['usd'].median():,.0f} USD en un día típico. El cupo de 60 revisa cerca de {60 / pagos_dia.median():.0%} de los pagos.
2. **El monto solo no separa, pero decide cuánto cuesta cada fraude.** La mediana es {dev.loc[fr, 'TransactionAmt'].median():.0f} USD en fraude
   y {dev.loc[lg, 'TransactionAmt'].median():.0f} en legítimos, y el decil de mayor monto concentra {dd['parte del fraude en USD'].iloc[-1]:.0%} del
   fraude en dólares: la cola debe ordenarse por dinero, no solo por probabilidad.
3. **El historial del cliente separa mucho.** Entre su pago anterior y el actual pasan
   {(dev.loc[fr, 'h_cliente_segundos_desde'] / 3600).median():.1f} h (mediana) en fraude y {(dev.loc[lg, 'h_cliente_segundos_desde'] / 3600).median():.0f} h en legítimos.
4. **Las cuentas nuevas son de riesgo.** Con 1 a 7 días desde el alta, {alta_1_7:.1%} de los pagos es fraude; el promedio es {dev['fraude'].mean():.1%}.
5. **Tres categorías destacan:** el producto C, la tarjeta de crédito y el celular. La tasa por hora va de {horas.min():.1%} a {horas.max():.1%}.
6. **Ninguna variable separa sola el fraude:** hace falta un modelo que combine muchas.''')"""),
    M(r"""### 2.3 Calidad de los datos

**Valores faltantes.** Son muchos en dispositivo, identidad y distancia: Vesta no siempre recibe esos campos."""),
    C(r"""falta = pd.concat([dev[NUM + ["D1"]].isna().mean(), (dev[CAT] == "NA").mean()])


def grupo(c):
    if c.startswith(("id_", "Device")):
        return "Dispositivo e identidad"
    if c.startswith("card"):
        return "Tarjeta"
    if c[0] == "M" and c[1:].isdigit():
        return "Coincidencias M1–M9"
    if c.startswith(("addr", "dist")):
        return "Dirección y distancia"
    return "Correo" if "email" in c else "Monto, producto y D1"


g = falta.groupby(falta.index.map(grupo))
display(pd.DataFrame({"columnas": g.size(), "faltante medio": g.mean().map("{:.0%}".format),
                      "columnas con más de 50% faltante": g.apply(lambda s: int((s > .5).sum()))}))
inf = {}
for c in ("DeviceType", "id_01", "dist1", "P_emaildomain", "addr1", "D1"):
    nulo = dev[c].isna() if c in NUM + ["D1"] else dev[c] == "NA"
    inf[c] = {"faltante": f"{nulo.mean():.1%}", "tasa de fraude si falta": f"{dev.loc[nulo, 'fraude'].mean():.1%}",
              "tasa de fraude con dato": f"{dev.loc[~nulo, 'fraude'].mean():.1%}"}
pd.DataFrame(inf).T"""),
    M(r"""El faltante no es al azar: la tasa de fraude cambia según falte o no el dato. Por eso se conserva como información
(sección 3.1) en vez de borrar filas o columnas.

**Ruido e inconsistencias.**"""),
    C(r"""centavos3 = (np.round(dev["TransactionAmt"] * 100, 6) % 1) > 0
mismo_seg = dev.duplicated(["card1", "addr1", "TransactionDT"], keep=False)
ck = X["cliente"]
pd.DataFrame([
    ("Filas duplicadas en todas las columnas", f"{int(dev.duplicated(NUM + CAT + ['TransactionDT', 'D1']).sum()):,}", "Se conservan: pueden ser cobros repetidos reales."),
    ("Pagos de la misma tarjeta y dirección en el mismo segundo", f"{int(mismo_seg.sum()):,}", "El historial solo cuenta segundos estrictamente anteriores: no se ven entre sí."),
    ("Montos menores o iguales a cero", f"{int((dev['TransactionAmt'] <= 0).sum()):,}", "Nada que corregir."),
    ("Montos con más de dos decimales", f"{centavos3.mean():.1%}", "Cobros convertidos de otra moneda: la variable centavos lo captura."),
    ("Categorías con un solo pago en card1 y DeviceInfo", f"{int((dev['card1'].value_counts() == 1).sum()):,} y {int((dev['DeviceInfo'].value_counts() == 1).sum()):,}",
     "Las categorías con menos de 50 casos se agrupan al codificar."),
    ("Días sin pagos entre el primero y el 120", f"{int(dev['dia'].max() - dev['dia'].min() + 1 - dev['dia'].nunique())}", "Serie diaria completa."),
    ("Fraudes que ocurren en clientes con dos o más pagos", f"{ck['fraudes_en_clientes_con_2_o_mas']:.0%}", "Etiqueta propagada: el historial del cliente pesa mucho."),
    ("Clientes con fraude en los que todos sus pagos son fraude", f"{ck['clientes_con_fraude_todo_fraude']:.0%}", "Ruido de etiqueta: se marca la cuenta, no cada pago revisado."),
], columns=["chequeo", "resultado", "qué se hace"]).set_index("chequeo")"""),
]

PREPARACION = [
    M(r"""## 3. Preparación de los datos

### 3.1 Limpieza: nulos y valores extremos

| Problema | Decisión | Por qué |
|---|---|---|
| Numéricas faltantes | Mediana del entrenamiento + una columna indicadora `falta_*` | El faltante es informativo (2.3); la mediana sale solo del entrenamiento |
| Categóricas faltantes | Categoría propia `NA` | Igual: falta el dato ≠ dato desconocido |
| Árboles de scikit-learn | Faltante = −999, fuera del rango de los datos | El árbol puede separarlo en su propia rama |
| Montos extremos | Se conservan | Ahí está el dinero (tabla de abajo); la sección 5.2 repite la evaluación sin ellos |
| Escala muy sesgada | Transformación por cuantiles a una normal | Para la logística y la red; los árboles no la necesitan |
| Categorías raras | Se agrupan si tienen menos de 50 pagos | Evita columnas de un solo caso |

**¿Qué pasaría al quitar los montos extremos?**"""),
    C(r"""monto = dev["TransactionAmt"]
q1, q3 = monto.quantile([.25, .75])
tope_iqr, p99 = q3 + 1.5 * (q3 - q1), monto.quantile(.99)
display(monto.describe(percentiles=[.25, .5, .75, .9, .99, .999]).to_frame("monto (USD)").T.round(1))
pd.DataFrame({"parte de los pagos": [f"{(monto > tope_iqr).mean():.1%}", f"{(monto > p99).mean():.1%}"],
              "parte del fraude en USD": [f"{uf[monto > tope_iqr].sum() / uf.sum():.0%}", f"{uf[monto > p99].sum() / uf.sum():.0%}"]},
             index=[f"Sobre Q3 + 1.5·IQR ({tope_iqr:,.0f} USD)", f"Sobre el percentil 99 ({p99:,.0f} USD)"])"""),
    M(r"""La regla de 1.5·IQR marcaría como atípicos los pagos que concentran una parte grande del fraude en dólares: borrarlos
quitaría justo lo que la cola debe atrapar. Se conservan, y la sección 5.2 comprueba que la ventaja del modelo no
depende de ellos.

### 3.2 Ingeniería de características

| Variable nueva | Cómo se calcula | Por qué |
|---|---|---|
| `log_monto`, `centavos` | log(1 + monto); parte decimal del monto | Escala; cobros convertidos de otra moneda |
| `hora`, `dia_semana` | Desde `TransactionDT` | El fraude cambia con la hora (2.2) |
| `alta` | Día del pago − `D1` | Fecha de alta de la cuenta: con tarjeta y dirección arma el **cliente** |
| Historial por llave, 25 variables | 5 medidas × 5 llaves, solo con pagos de segundos anteriores | Velocidad y recencia: la señal más fuerte del EDA |

Las cinco medidas por llave: pagos previos, pagos en las últimas 24 horas y en los últimos 7 días, segundos desde el
pago anterior y monto contra el promedio previo. Ninguna usa la etiqueta."""),
    C(r"""for k, v in CLAVES.items():
    print(f"llave {k:<20} {' + '.join(v)}")
print("medidas por llave:", ", ".join(ESTADISTICAS))
hist = [c for c in dev.columns if c.startswith("h_")]
print(f"{len(DERIVADAS)} derivadas ({', '.join(DERIVADAS)}) y {len(hist)} de historial, por ejemplo {hist[:3]}")"""),
    C(r"""codigo(cargar, _historial)"""),
    M(r"""**El historial, en vivo.** Cuatro pagos de un mismo cliente; los dos últimos ocurren en el mismo segundo y no se ven
entre sí."""),
    C(r"""t = np.array([0, 3_600, 90_000, 90_000])
montos = np.array([30.0, 40.0, 120.0, 10.0])
h = _historial(t, montos, np.zeros(4, int))
pd.DataFrame({"segundo": t, "monto": montos, **h}).rename(columns={"previos": "pagos previos", "ultimo_dia": "en 24 h",
    "ultima_semana": "en 7 días", "segundos_desde": "segundos desde el anterior", "razon_monto": "monto / promedio previo"})"""),
    C(r"""fig("tuberia", "cliente_armado")"""),
    M(r"""**¿Separan las variables nuevas?** Tasa de fraude por tramos del historial del cliente, días 1–120."""),
    C(r"""horas_desde = dev["h_cliente_segundos_desde"] / 3600
tramo = pd.cut(horas_desde, [-.01, 1, 24, 24 * 7, np.inf], labels=["menos de 1 h", "1 h a 1 día", "1 a 7 días", "más de 7 días"])
tramo = tramo.cat.add_categories("primer pago").fillna("primer pago")
previos = pd.cut(dev["h_cliente_previos"], [-.5, .5, 2.5, 9.5, np.inf], labels=["0", "1 o 2", "3 a 9", "10 o más"])
for nombre, tr_ in (("tiempo desde su pago anterior", tramo), ("pagos previos del cliente", previos)):
    t_ = pd.DataFrame({"pagos": dev.groupby(tr_).size(), "tasa de fraude": dev.groupby(tr_)["fraude"].mean()}).rename_axis(nombre)
    display(t_.assign(pagos=t_["pagos"].map("{:,}".format), **{"tasa de fraude": t_["tasa de fraude"].map("{:.1%}".format)}))"""),
    M(r"""**Normalización y codificación: la matriz de diseño.** La clase `Diseno` aprende todo solo del entrenamiento:
mediana para imputar, transformación por cuantiles a normal, indicadores de faltante y una columna one-hot por
categoría con al menos 50 pagos. Los árboles de scikit-learn usan otra matriz: numéricas crudas y la frecuencia de cada
categoría."""),
    C(r"""codigo(Diseno)"""),
    C(r"""tr_d2, te_d2 = bloque(dev, 91, 120)              # entrenamiento del bloque D2: días 1-60
dis = Diseno(tr_d2, "F3")
A = dis.matriz(tr_d2)
n_num = len(dis.num)
print(f"Entrenamiento de D2 (días {tr_d2['dia'].min()}–{tr_d2['dia'].max()}): {A.shape[0]:,} pagos × {A.shape[1]:,} columnas")
print(f"  {n_num} numéricas llevadas a normal + {n_num} indicadores de faltante + {A.shape[1] - 2 * n_num} columnas one-hot de {len(dis.cat)} categóricas")
print(f"  Valores faltantes en la matriz: {int(np.isnan(A.data).sum())} · celdas distintas de cero: {A.nnz / (A.shape[0] * A.shape[1]):.1%}")
i = dis.num.index("TransactionAmt")
display(pd.DataFrame({"monto original": tr_d2["TransactionAmt"].describe(),
                      "monto transformado": pd.Series(A[:, i].toarray().ravel()).describe()}).T.round(2))
j = dis.num.index("dist1")
print(f"dist1: {tr_d2['dist1'].isna().mean():.1%} faltante → indicador falta_dist1 con media {A[:, n_num + j].mean():.3f}")
print("ProductCD en one-hot:", [n for n in dis.nombres if n.startswith("ProductCD")])"""),
    M(r"""**Sin fuga de información.** Ninguna variable usa la etiqueta ni el futuro."""),
    C(r"""assert not set(VESTA) & set(CONJUNTOS["F3"][0]), "F3 no debe usar las columnas opacas de Vesta"
assert "isFraud" not in CONJUNTOS["F3"][0] + CONJUNTOS["F3"][1] and "fraude" not in CONJUNTOS["F3"][0]
assert tr_d2["dia"].max() < 91 - 30, "el entrenamiento termina 30 días antes de evaluar"
assert np.isnan(h["segundos_desde"][0]) and h["previos"][3] == 2, "el historial solo mira segundos anteriores"
print("F3 no usa columnas opacas ni la etiqueta; el historial solo mira el pasado; el entrenamiento deja 30 días de margen.")"""),
    M(r"""### 3.3 Selección de variables

Cuatro conjuntos anidados. Se elige con el torneo de desarrollo (sección 4.1) y una ablación con el mismo XGBoost."""),
    C(r"""desc = {"F1": "Descriptivas: monto, hora, producto, tarjeta, dirección, correo, dispositivo, M1–M9, id_*",
        "F2": "F1 + historial por cuatro llaves de tarjeta",
        "F3": "F2 + antigüedad (D1) e historial del cliente reconstruido",
        "F4": f"F3 + {len(VESTA)} columnas opacas de Vesta (C, D2–D15, V)"}
pd.DataFrame({c: {"numéricas": len(n), "categóricas": len(k), "contenido": desc[c]} for c, (n, k) in CONJUNTOS.items()}).T"""),
    C(r"""dv = pd.DataFrame(S["dolares"]).T
dv["total"] = dv["D1"] + dv["D2"]
pd.DataFrame({c: dv.loc[f"XGB|{c}", ["D1", "D2", "total"]] / 1e3 for c in ("F1", "F2", "F3", "F4")}).T.round(1).add_suffix(" (mil USD)")"""),
    C(r"""fig("ablacion")"""),
    M(r"""**Por qué F3.** Cada bloque de variables nuevas sube el dinero: el historial por tarjeta (F2) y el cliente
reconstruido (F3). F4 daría más, pero la descripción pública no dice en qué momento calcula Vesta sus columnas opacas:
podrían usar información posterior al pago. Quedaron fuera antes de la prueba.

**Importancia por permutación en dólares (D2).** Cuánto dinero se pierde al barajar cada grupo de variables."""),
    C(r"""dg = S["diagnosticos_D2"]
(pd.Series(dg["importancia_usd"]) / 1e3).round(1).sort_values(ascending=False).rename("mil USD que se pierden al barajar").to_frame()"""),
    C(r"""fig("importancia")"""),
    M(r"""**¿Mejores variables? Búsqueda con validación cruzada temporal.** Estudio posterior a la prueba, con los días 1–120
y un diseño registrado antes de correr (`docs/anexo_variables.md`): ocho grupos candidatos, selección hacia adelante en
tres ventanas con origen móvil (un grupo entra si sube el total al menos 1% y mejora en dos de las tres) y un bloque de
confirmación (días 106–120) que la búsqueda no usa."""),
    C(r"""fig("validacion")"""),
    C(r"""rd = pd.DataFrame([{"ronda": r["ronda"], **{g: f"{v['ganancia'] * 100:+.1f}% · {v['suben']} de 3" for g, v in r["pruebas"].items()},
                    "acepta": r["mejor"] if r["acepta"] else "ninguno"} for r in VA["rondas"]]).set_index("ronda").T
print(f"Aceptados: {', '.join(VA['elegidos'])} · ventanas de búsqueda: {VA['base_F3']['total_usd'] / 1e3:,.1f} → "
      f"{VA['final_interno']['total_usd'] / 1e3:,.1f} mil USD ({pc(VA['final_interno']['total_usd'] / VA['base_F3']['total_usd'] - 1)})")
rd.fillna("—")"""),
    C(r"""fig("escalada")"""),
    M(r"""**Confirmación, recalculada aquí** desde los puntajes guardados de los días 106–120."""),
    C(r"""cf = pd.read_parquet(PROCESADOS / "variables_confirmacion.parquet")
d_, y_, m_ = cf["dia"].to_numpy(), cf["fraude"].to_numpy(), cf["monto"].to_numpy()
usd_c = {n: dinero(cf[n].to_numpy() * m_, d_, y_, m_, K) for n in ("F3", "elegido", "con_etiquetas", "logit_F3", "logit_elegido", "regla")}
assert max(abs(usd_c[n] - VA["confirmacion_resultados"]["usd"][n]) for n in usd_c) < 0.01
cc6 = VA["confirmacion_resultados"]["contrastes"]
ETIQ = {"F3": "XGBoost con F3", "elegido": "XGBoost con variables nuevas", "con_etiquetas": "con historial de contracargos (cota)",
        "logit_F3": "logística con F3", "logit_elegido": "logística con variables nuevas", "regla": "mejor regla"}
display(pd.DataFrame({"mil USD, días 106–120": {ETIQ[n]: mil(v) for n, v in usd_c.items()}}))
pd.DataFrame({"contraste": ["variables nuevas contra F3", "logística: nuevas contra F3", "historial de contracargos contra variables nuevas"],
              "ventaja": [pc(cc6[k]["rel"]) for k in ("elegido_vs_F3", "logit_elegido_vs_logit_F3", "con_etiquetas_vs_elegido")],
              "IC 95%": [ic(cc6[k]["rel_ic95"]) for k in ("elegido_vs_F3", "logit_elegido_vs_logit_F3", "con_etiquetas_vs_elegido")]}).set_index("contraste")"""),
    C(r"""fig("espejismo")
e = cc6["elegido_vs_F3"]
Markdown(f'''**Decisión: F3 se mantiene.** En las ventanas de búsqueda, los grupos aceptados suben el dinero
{pc(VA['final_interno']['total_usd'] / VA['base_F3']['total_usd'] - 1)}, pero esas ventanas son las mismas que los eligieron. En los días de
confirmación, el modelo con variables nuevas lleva {pc(e['rel'])} contra F3 (IC 95%: {ic(e['rel_ic95'])}): la ganancia no se repite en días
nuevos. Es sobreajuste a la validación.''')"""),
]

MODELADO = [
    M(r"""## 4. Modelado

### 4.1 Selección de algoritmos

| Familia | Políticas | Por qué entra |
|---|---|---|
| Reglas de negocio | Mayor monto; tasa histórica suavizada × monto por tarjeta, segmento, correo, producto × decil de monto y velocidad | Representan la práctica actual: transparentes y sin modelo |
| Lineal | Logística L2 con cinco valores de C | Base aprendida con la misma información; interpretable |
| Árbol | CART de profundidad 3 | Reglas legibles aprendidas de los datos |
| Ensambles de árboles | Bosque aleatorio, XGBoost, XGBoost ponderado por monto, ensamble XGBoost + bosque | Interacciones no lineales, faltantes y escalas distintas sin supuestos; lo más fuerte en datos tabulares |
| Red neuronal | MLP con capas de 64 y 32 | Otra forma no lineal, para comparar |
| Anomalías | Bosque de aislamiento | No usa la etiqueta: ¿basta con buscar pagos raros? |

Todas ordenan la cola por **probabilidad × monto** y se evalúan con el mismo cupo de 60. Los hiperparámetros se
fijaron antes del torneo (`src/revisar/politicas.py`):"""),
    C(r"""hp = {"XGBoost": XGB, "Bosque aleatorio": RF, "Árbol CART": CART, "Red MLP": MLP, "Bosque de aislamiento": ISO,
      "Logística L2": {"C": CS, "max_iter": 3000}}
pd.DataFrame({"hiperparámetros": {m: ", ".join(f"{k}={v}" for k, v in d.items() if k not in ("n_jobs", "random_state"))
                                  for m, d in hp.items()}})"""),
    C(r"""codigo(_tasa, reglas, modelos, puntaje)"""),
    M(r"""**El torneo de desarrollo.** Dos bloques: D1 (días 61–90, entrena con 1–30) y D2 (días 91–120, entrena con
1–60). La regla de selección se escribió antes de correrlo (`docs/criterio_desarrollo.md`): gana el modelo flexible
con más dólares en D1 + D2 (un ensamble necesita 1% más que el mejor modelo solo), y solo si supera a la mejor
logística en los dos bloques. Aquí se recalcula desde los dólares de cada política."""),
    C(r"""display((dv / 1e3).round(1).sort_values("total", ascending=False).rename(columns=lambda c: f"{c} (mil USD)").head(15))
elegibles = [f"{f}|{c}" for f in FLEXIBLES for c in ("F2", "F3")]
mejor = dv.loc[elegibles, "total"].idxmax()
if mejor.startswith("ENS"):
    unico = dv.loc[[e for e in elegibles if not e.startswith("ENS")], "total"].idxmax()
    if dv.loc[mejor, "total"] < 1.01 * dv.loc[unico, "total"]:
        mejor = unico
logit = dv.loc[[f"LOGIT_C{c}|{f}" for c in CS for f in ("F2", "F3")], "total"].idxmax()
regla = dv.loc[list(REGLAS), "total"].idxmax()
supera = all(dv.loc[mejor, b] > dv.loc[logit, b] for b in ("D1", "D2"))
final = mejor if supera else logit
assert (final, logit, regla, supera) == (S["final"], S["mejor_logit"], S["mejor_regla"], S["supera_lineal_en_ambos"])
print(f"Regla recalculada: modelo final {final}, mejor logística {logit}, mejor regla {regla}; "
      f"supera a la logística en ambos bloques: {supera}")"""),
    C(r"""fig("torneo", "modelos")"""),
    M(r"""**Por qué XGBoost.** Es el que más dinero detiene en los dos bloques. El bosque de aislamiento, que no usa la
etiqueta, queda muy abajo: el fraude de estos datos no es solo "lo raro". **Pruebas de cordura en D2:**"""),
    C(r"""pd.Series({"Modelo": dg["cordura"]["base"], "El mismo modelo con etiquetas barajadas": dg["cordura"]["etiquetas_barajadas"],
           "Revisar al azar (esperado)": dg["cordura"]["azar_esperado"], "Árbol de profundidad 3": dg["arbol"]["usd_D2"]}).div(1e3).round(1).rename("mil USD en D2").to_frame()"""),
    M(r"""Con las etiquetas barajadas, la probabilidad queda casi constante y la cola se ordena prácticamente por monto: eso
explica lo que todavía detiene. La diferencia con el modelo real es lo que aprende de las etiquetas."""),
    M(r"""### 4.2 Entrenamiento: partición en el tiempo

La partición no es al azar. Los pagos se ordenan en el tiempo: cada bloque entrena con días anteriores y evalúa días
posteriores, como en operación. Entre el último día de entrenamiento y el primero evaluado hay **30 días de margen**:
es lo que tarda en llegar el contracargo, así que al entrenar no se conocería la etiqueta de los pagos más recientes.
Una partición al azar pondría pagos de un mismo cliente en los dos lados y sobrestimaría el desempeño."""),
    C(r"""codigo(bloque)"""),
    C(r"""t0 = time.time()
todo = cargar(183)                                 # los 182 días: la prueba ya se corrió, aquí se reproduce
print(f"Días {todo['dia'].min()}–{todo['dia'].max()}: {len(todo):,} pagos, cargados en {time.time() - t0:.0f} s")
PART = {"D1": (61, 90), "D2": (91, 120), **P}
filas = {}
for b, (ini, fin) in PART.items():
    tr, te = bloque(todo, ini, fin)
    info = S["info_bloques"][b] if b in S["info_bloques"] else R[b]
    assert len(tr) == info["entrenamiento"] and len(te) == info.get("evaluacion", info.get("pagos"))
    filas[b] = {"uso": "desarrollo: elegir" if b[0] == "D" else "prueba: una sola corrida", "entrena con días": f"{tr['dia'].min()}–{tr['dia'].max()}",
                "evalúa días": f"{ini}–{fin}", "pagos de entrenamiento": f"{len(tr):,}", "pagos evaluados": f"{len(te):,}",
                "tasa de fraude evaluada": f"{te['fraude'].mean():.2%}", "fraude evaluado (mil USD)": mil((te["fraude"] * te["TransactionAmt"]).sum())}
pd.DataFrame(filas).T"""),
    C(r"""fig("calendario")"""),
    M(r"""**¿Se usan todos los datos?** Sí, con dos límites que pone el problema y no el modelo. Al entrenar solo se puede
usar lo que ya tiene etiqueta: cada modelo usa **todos** los pagos con al menos 30 días de antigüedad, y nada más.
Y quedan fuera las columnas opacas de Vesta, porque no se sabe en qué momento se calculan."""),
    C(r"""for b, (ini, fin) in PART.items():
    tr, _ = bloque(todo, ini, fin)
    assert len(tr) == int((todo["dia"] < ini - 30).sum()), "el entrenamiento debe tener todos los pagos ya etiquetados"
tr_p2, _ = bloque(todo, *P["P2"])
f3, f4 = (dv.loc[f"XGB|{c}", "total"] for c in ("F3", "F4"))
pd.Series({"Pagos en el archivo": f"{meta.num_rows:,}",
           "Pagos con los que entrena el modelo de P2 (todos los de los días 1–121)": f"{len(tr_p2):,}",
           "Pagos evaluados en la prueba (días 121–182)": f"{sum(R[x]['pagos'] for x in P):,}",
           f"Columnas en el archivo ({vacias.num_columns} vacías)": meta.num_columns,
           "Columnas crudas que usa el modelo (con TransactionDT, de la que salen la hora y el historial)": len(usa) + 1,
           "Variables del modelo final (F3)": len(CONJUNTOS["F3"][0]) + len(CONJUNTOS["F3"][1]),
           "Columnas opacas de Vesta que no usa": len(VESTA),
           "Dinero en desarrollo si se agregaran (F4 contra F3)": pc(f4 / f3 - 1)}).to_frame("valor")"""),
    M(r"""Las columnas opacas subirían el dinero en desarrollo, pero si alguna se calcula con información posterior al pago, ese
dinero no existiría en operación. Agregarlas ahora, después de ver la prueba, además invalidaría la evaluación: es una
mejora para probar en el piloto, con días nuevos y después de preguntarle a Vesta cuándo se calculan.

**El modelo final, entrenado aquí.** El mismo código de la prueba entrena XGBoost con F3 sobre los días 1–90 y arma
la cola de P1 (días 121–151), junto con la mejor regla. Los resultados oficiales de la prueba, con sus intervalos, son
los de la sección 5."""),
    C(r"""t0 = time.time()
tr, te = bloque(todo, *P["P1"])
p_vivo = modelos(tr, te, "F3", ("XGB",))["XGB"]
r_vivo = reglas(tr, te)[REGLA]
m_, d_, y_ = te["TransactionAmt"].to_numpy(float), te["dia"].to_numpy(), te["fraude"].to_numpy()
print(f"XGBoost con F3 entrenado con {len(tr):,} pagos (días {tr['dia'].min()}–{tr['dia'].max()}) y aplicado a "
      f"{len(te):,} pagos de P1, en {time.time() - t0:.0f} s")
aqui, usd_aqui = {}, {}
for n, p in ((FINAL, p_vivo), (REGLA, r_vivo)):
    mz = matriz(p * m_, d_, y_, m_, K)
    usd_aqui[n] = mz["revisado_fraude"]["usd"]
    aqui[NOMBRE[n]] = {"fraude detenido (mil USD)": mil(usd_aqui[n]), "parte del fraude de P1": f"{mz['parte_usd_fraude']:.0%}",
                       "fraudes en la cola": f"{mz['revisado_fraude']['pagos']:,}", "precisión de la cola": f"{mz['precision']:.1%}",
                       "AUC": round(roc_auc_score(y_, p), 3)}
ventaja_aqui = usd_aqui[FINAL] / usd_aqui[REGLA] - 1
assert ventaja_aqui > 0.15, "el modelo entrenado aquí debe ganarle a la regla con holgura"
print(f"Ventaja del modelo sobre la regla en P1: {pc(ventaja_aqui)}")
pd.DataFrame(aqui).T"""),
    M(r"""### 4.3 Optimización de hiperparámetros

Los hiperparámetros se eligen **por dólares en desarrollo**, no por AUC ni por pérdida logarítmica. Tres decisiones:
la regularización de la logística, el número de árboles de XGBoost (con parada temprana) y su profundidad (rejilla
con validación cruzada temporal).

**Regularización de la logística (C).**"""),
    C(r"""rg = pd.DataFrame(L["regularizacion"])
rg.assign(usd=(rg["usd"] / 1e3).round(1)).pivot(index="C", columns="conjunto", values=["usd", "auc"]).round(3).rename(columns={"usd": "mil USD", "auc": "AUC"})"""),
    C(r"""fig("regularizacion")"""),
    M(r"""C = 0.003 da más dinero aunque no tenga el AUC más alto: el criterio de selección es el dinero.

**XGBoost: rejilla de profundidad con parada temprana.** Cuatro combinaciones, cada una con parada temprana (hasta 4,000
árboles; se detiene tras 150 sin mejorar en 10 días de validación), medidas en las tres ventanas de la búsqueda de 3.3.
Se adopta solo si supera a los hiperparámetros del protocolo por 1% y en dos de tres ventanas."""),
    C(r"""rj = pd.DataFrame([{**r["params"], "mil USD (3 ventanas)": mil(r["total_usd"]), "AUC": round(r["auc"], 3),
                    "árboles elegidos por ventana": " / ".join(str(v) for v in r["arboles"].values())} for r in VA["rejilla"]])
hpx = VA["hiperparametros"]
print(f"Protocolo: {VA['protocolo_xgb']}. Mejor combinación de la rejilla: {pc(hpx['ganancia'])} contra el protocolo, "
      f"mejora en {hpx['suben']} de 3 ventanas → {'se adopta' if hpx['adopta'] else 'se quedan los del protocolo'}.")
rj"""),
    C(r"""fig("aprendizaje")
ap = VA["aprendizaje"]
print(f"Ventana {ap['ventana']}: la pérdida de validación deja de bajar cerca del árbol {ap['mejor_iteracion']}; "
      f"el protocolo usa {ap['arboles_protocolo']} árboles con tasa de aprendizaje {ap['learning_rate']}.")"""),
    M(r"""Ninguna combinación de la rejilla supera a la del protocolo (600 árboles de profundidad 8), y la parada temprana
llega a un número de árboles parecido: el modelo congelado ya estaba cerca del óptimo. El cupo de 60 no es un
hiperparámetro: lo fija el negocio. La sección 5.2 mide la ventaja con 30 y 120 revisiones."""),
]

EVALUACION = [
    M(r"""## 5. Evaluación en los dos meses de prueba

P1: días 121–151 (entrena con 1–90). P2: días 152–182 (entrena con 1–121). Todo quedó congelado antes de leerlos y la
prueba se corrió una vez.

### 5.1 Métricas de desempeño

**Dólares de fraude en la cola, recalculados aquí.** Se toman los puntajes guardados de cada pago y se arma la cola de
60 de cada día con el código congelado de `src/revisar/evaluacion.py`:"""),
    C(r"""codigo(seleccion, dinero)"""),
    C(r"""PT, SC, vivo = {}, {}, {}
for x in P:
    PT[x] = g = pd.read_parquet(PROCESADOS / f"prueba_puntajes_{x}.parquet")
    dia_, y_, m_ = g["dia"].to_numpy(), g["fraude"].to_numpy(), g["monto"].to_numpy()
    s = {n: puntaje(n.split("|")[0], g[n].to_numpy(), m_) for n in (FINAL, LOGIT, REGLA, "R_monto")}   # probabilidad × monto
    s[PUB] = puntaje(FINAL.split("|")[0], g[FINAL].to_numpy(), m_, "p")       # el mismo modelo, ordenado solo por probabilidad
    s["oraculo"] = y_ * m_
    SC[x] = s
    vivo[x] = {n: dinero(v, dia_, y_, m_, K) for n, v in s.items()}
tab = pd.DataFrame({x: {NOMBRE[n]: v / 1e3 for n, v in vivo[x].items()} for x in P}).round(1)
tab.columns = [f"{x}: mil USD" for x in P]
for x in P:
    tab[f"{x}: parte del oráculo"] = [f"{vivo[x][n] / vivo[x]['oraculo']:.0%}" for n in vivo[x]]
dif = max(abs(vivo[x][n] - R[x]["usd"][n]) for x in P for n in vivo[x])
assert dif < 0.01, "el recálculo no reproduce resultados/prueba.json"
print(f"Diferencia máxima contra resultados/prueba.json: {dif:.6f} USD")
tab"""),
    C(r"""fig("resultado", "prueba")"""),
    M(r"""**Matriz de confusión y métricas de clasificación**, días 121–182, con el cupo de 60 por día: un pago "positivo" es
uno que entra a la cola."""),
    C(r"""T = pd.concat([PT[x].assign(periodo=x) for x in P], ignore_index=True)
y_t, m_t, d_t = T["fraude"].to_numpy(), T["monto"].to_numpy(), T["dia"].to_numpy()
colas = {"Modelo (probabilidad × monto)": T[FINAL].to_numpy() * m_t, "Solo probabilidad": T[FINAL].to_numpy(),
         "Mejor logística": T[LOGIT].to_numpy() * m_t, "Mejor regla": T[REGLA].to_numpy() * m_t, "Mayor monto primero": m_t}
met, mc = {}, {}
for n, s in colas.items():
    sel = seleccion(s, d_t, K)
    tn, fp, fn, tp = confusion_matrix(y_t, sel).ravel()
    mc[n] = pd.DataFrame([[tp, fp], [fn, tn]], index=["revisado", "no revisado"], columns=["fraude", "legítimo"])
    met[n] = {"exactitud": (tp + tn) / len(y_t), "precisión": tp / (tp + fp), "recall": tp / (tp + fn), "F1": 2 * tp / (2 * tp + fp + fn),
              "AUC-ROC del puntaje": roc_auc_score(y_t, s), "AUC-PR del puntaje": average_precision_score(y_t, s),
              "mil USD en la cola": mil((y_t * m_t)[sel].sum()), "parte del fraude en USD": (y_t * m_t)[sel].sum() / (y_t * m_t).sum()}
met["No revisar nada"] = {"exactitud": 1 - y_t.mean(), "precisión": np.nan, "recall": 0.0, "F1": 0.0, "AUC-ROC del puntaje": 0.5,
                          "AUC-PR del puntaje": y_t.mean(), "mil USD en la cola": 0.0, "parte del fraude en USD": 0.0}
op = CC["operacion"]["modelo"]
assert (mc["Modelo (probabilidad × monto)"].loc["revisado", "fraude"], mc["Modelo (probabilidad × monto)"].loc["revisado", "legítimo"]) == (op["TP"], op["FP"])
print("Matriz de confusión del modelo, en pagos:")
display(mc["Modelo (probabilidad × monto)"])
pd.DataFrame(met).T.round(3)"""),
    M(r"""**Las métricas de conteo engañan aquí.** No revisar nada tiene la mayor exactitud, porque 96.5% de los pagos es
legítimo. Ordenar solo por probabilidad tiene mejor precisión, recall, F1 y AUC: atrapa más fraudes, pero pequeños. En
dólares, que es lo que el negocio pierde, gana el modelo ordenado por probabilidad × monto.

**Matriz de confusión en dólares**, por mes:"""),
    C(r"""filas = {}
for x in P:
    g, s = PT[x], SC[x]
    for n in (FINAL, LOGIT, REGLA):
        v = matriz(s[n], g["dia"].to_numpy(), g["fraude"].to_numpy(), g["monto"].to_numpy(), K)
        filas[(x, NOMBRE[n])] = {"fraude revisado (mil USD)": mil(v["revisado_fraude"]["usd"]), "fraude que pasa (mil USD)": mil(v["no_revisado_fraude"]["usd"]),
                                 "fraudes revisados": v["revisado_fraude"]["pagos"], "revisiones a legítimos": v["revisado_legitimo"]["pagos"],
                                 "precisión de la cola": f"{v['precision']:.0%}", "parte del fraude del mes": f"{v['parte_usd_fraude']:.0%}"}
pd.DataFrame(filas).T"""),
    C(r"""fig("exactitud", "roc", "ganancia")"""),
    M(r"""**¿Las probabilidades son confiables? Calibración.** Por decil de probabilidad estimada, días 121–182."""),
    C(r"""p_t = T[FINAL]
dec_p = pd.qcut(p_t, 10, labels=range(1, 11))
cal = pd.DataFrame({"pagos": p_t.groupby(dec_p).size(), "probabilidad media estimada": p_t.groupby(dec_p).mean(),
                    "tasa de fraude observada": T["fraude"].groupby(dec_p).mean()}).rename_axis("decil de probabilidad")
display(cal.round(3))
br = {"Modelo": brier_score_loss(y_t, p_t), "Mejor logística": brier_score_loss(y_t, T[LOGIT]),
      "Asignar a todos la tasa media": brier_score_loss(y_t, np.full(len(y_t), y_t.mean()))}
display(pd.Series(br).round(4).rename("error de Brier").to_frame())
print(f"Fraudes con probabilidad estimada menor a 10%: {(p_t[y_t == 1] < .1).mean():.0%}; "
      f"con 50% o más: {(p_t[y_t == 1] >= .5).mean():.0%}")"""),
    C(r"""fig("calibracion")"""),
    M(r"""Las probabilidades están calibradas: en cada decil, la probabilidad media estimada se parece a la tasa observada.
Que la mitad de los fraudes tenga probabilidad baja no es un error del modelo: esos fraudes se parecen a pagos
legítimos en todo lo que se observa. Con 60 revisiones por día no hacen falta probabilidades altas, sino un buen
**orden**: el decil más alto tiene una tasa de fraude varias veces el promedio.

**¿Por qué no se revisan primero los pagos con probabilidad más alta?** Se comparan, pago por pago, la cola por fraude
esperado y la cola del mismo modelo ordenada solo por probabilidad."""),
    C(r"""p_np, uft = T[FINAL].to_numpy(), y_t * m_t
sel_e, sel_p = seleccion(p_np * m_t, d_t, K), seleccion(p_np, d_t, K)
partes = {"en las dos colas": sel_e & sel_p, "solo en la cola por probabilidad": sel_p & ~sel_e, "solo en la cola por fraude esperado": sel_e & ~sel_p}
cambio = pd.DataFrame({n: {"pagos": int(k.sum()), "fraudes": int(y_t[k].sum()), "fraude detenido (mil USD)": mil(uft[k].sum()),
                           "fraude esperado (mil USD)": mil((p_np * m_t)[k].sum()), "monto mediano (USD)": round(float(np.median(m_t[k]))),
                           "probabilidad mediana": f"{np.median(p_np[k]):.0%}"} for n, k in partes.items()}).T
display(cambio)
n_dias = len(np.unique(d_t))
alta = {f"probabilidad ≥ {u:.0%}": {"pagos por día": round((p_np >= u).sum() / n_dias, 1),
                                     "entran a la cola": f"{((p_np >= u) & sel_e).sum() / (p_np >= u).sum():.0%}",
                                     "monto mediano de los que quedan fuera (USD)": round(float(np.median(m_t[(p_np >= u) & ~sel_e]))),
                                     "fraude que dejan pasar (mil USD)": mil(uft[(p_np >= u) & ~sel_e].sum())} for u in (.3, .5, .8)}
display(pd.DataFrame(alta).T)
a_, b_ = cambio.loc["solo en la cola por probabilidad"], cambio.loc["solo en la cola por fraude esperado"]
Markdown(f'''Las dos colas comparten {(sel_e & sel_p).sum() / sel_e.sum():.0%} de los pagos. En el resto, ordenar por probabilidad elige
{a_['fraudes']:,} fraudes que suman {a_['fraude detenido (mil USD)']:,.1f} mil USD (pagos de {a_['monto mediano (USD)']} USD en mediana);
ordenar por fraude esperado elige {b_['fraudes']:,} fraudes que suman {b_['fraude detenido (mil USD)']:,.1f} mil USD (pagos de
{b_['monto mediano (USD)']} USD en mediana). Menos fraudes, pero {b_['fraude detenido (mil USD)'] / a_['fraude detenido (mil USD)']:.0f} veces
más dinero.''')"""),
    M(r"""**¿Y una cola mixta, que revise siempre los casos más claros?** Dos refinamientos posibles:

- **Reservar lugares:** los primeros N lugares de cada día para los pagos con mayor probabilidad, y el resto por fraude
  esperado.
- **Dar valor a cada fraude atrapado:** ordenar por probabilidad × (monto + V), donde V es lo que vale atrapar un fraude
  aparte de su monto (una comisión de contracargo, por ejemplo).

Además del fraude de la cola, se cuenta el **fraude posterior del mismo cliente** que se evita si un fraude revisado
lleva a bloquear la tarjeta: es el argumento a favor de revisar los fraudes chicos pero obvios, que a veces son pruebas
de una tarjeta robada. Cada variante se mide en desarrollo (días 61–120) y en la prueba. Es un análisis posterior: no
cambia el veredicto del protocolo."""),
    C(r"""todo["cliente"] = pd.factorize(todo["card1"] + "|" + todo["addr1"] + "|" + todo["alta"].astype(str))[0]


def cola_mixta(p, m, d, reserva=0, V=0.0):
    # Los primeros `reserva` lugares de cada día van a los pagos más probables; el resto, por probabilidad × (monto + V).
    arriba = seleccion(p, d, reserva) if reserva else np.zeros(len(p), bool)
    return seleccion(np.where(arriba, np.inf, p * (m + V)), d, K)


def detenido(sel, y, m, d, c):
    # Fraude de la cola, y fraude posterior del mismo cliente si el primer fraude revisado lleva a bloquear su tarjeta.
    rev = sel & (y == 1)
    dia_bloqueo = pd.Series(c).map(pd.Series(d[rev]).groupby(c[rev]).min()).to_numpy(dtype=float)
    despues = (y == 1) & ~sel & (d > dia_bloqueo)
    return (y * m)[sel].sum(), (y * m)[despues].sum(), int(y[sel].sum())


VARIANTES = {"actual: fraude esperado": (0, 0), "reserva 5 lugares": (5, 0), "reserva 10 lugares": (10, 0), "reserva 20 lugares": (20, 0),
             "probabilidad × (monto + 25)": (0, 25), "probabilidad × (monto + 100)": (0, 100), "solo probabilidad": (K, 0)}
ARCH = {"D1": "desarrollo_puntajes_D1", "D2": "desarrollo_puntajes_D2", "P1": "prueba_puntajes_P1", "P2": "prueba_puntajes_P2"}
acum = {}
for b, arch in ARCH.items():
    _, te = bloque(todo, *PART[b])
    g = pd.read_parquet(PROCESADOS / f"{arch}.parquet")
    assert np.array_equal(g["monto"].to_numpy(), te["TransactionAmt"].to_numpy())
    p, m, d, y, c = g[FINAL].to_numpy(), g["monto"].to_numpy(), g["dia"].to_numpy(), g["fraude"].to_numpy(), te["cliente"].to_numpy()
    for n, (r, V) in VARIANTES.items():
        x = acum.setdefault(("desarrollo" if b[0] == "D" else "prueba", n), np.zeros(3))
        x += detenido(cola_mixta(p, m, d, r, V), y, m, d, c)
mx = pd.DataFrame(acum, index=["en la cola", "evitado al bloquear", "fraudes"]).T
mx["total"] = mx["en la cola"] + mx["evitado al bloquear"]
base = mx.xs("actual: fraude esperado", level=1)
tabla = {}
for (etapa, n), v in mx.iterrows():
    tabla.setdefault(n, {})
    tabla[n][(etapa, "mil USD con bloqueo")] = mil(v["total"])
    tabla[n][(etapa, "contra la actual")] = pc(v["total"] / base.loc[etapa, "total"] - 1)
    tabla[n][(etapa, "fraudes atrapados")] = int(v["fraudes"])
mixta = pd.DataFrame(tabla).T
mejor_dev = mx.xs("desarrollo")["total"].idxmax()
r5 = mx.loc[("prueba", "reserva 5 lugares")] / mx.loc[("prueba", "actual: fraude esperado")] - 1
print(f"Mejor variante en desarrollo: {mejor_dev}. En la prueba, reservar 5 lugares cambia el dinero {pc(r5['total'])} "
      f"y los fraudes atrapados {pc(r5['fraudes'])}.")
mixta"""),
    M(r"""**No hace falta cambiar la cola.** Con o sin el efecto de bloquear la tarjeta, ordenar por fraude esperado es lo que
más dinero detiene, en desarrollo y en la prueba. El fraude evitado al bloquear es chico y parecido entre variantes:
los fraudes obvios que quedan fuera son de pocos dólares, y bloquear su tarjeta evita poco fraude posterior. Si el equipo valora
además el número de fraudes atrapados, reservar 5 de los 60 lugares para los casos más claros cuesta alrededor de 1%
del dinero y atrapa cerca de 5% más fraudes: es una decisión de operación, no del modelo.

### 5.2 Validación de negocio

La pregunta de la fase 1: **con las mismas 60 revisiones diarias, ¿el modelo detiene más dólares de fraude que la
práctica actual, por el margen fijado antes de la prueba?**

**Intervalos pareados, recalculados aquí.** Cada réplica remuestrea días con reemplazo, los mismos para todas las
políticas. Se vuelven a generar las 1,000 réplicas con la misma semilla y se comparan con las guardadas."""),
    C(r"""codigo(bootstrap)"""),
    C(r"""filas, veredicto = [], {}
for x, (ini, fin) in P.items():
    g = PT[x]
    b = bootstrap(SC[x], g["dia"].to_numpy(), g["fraude"].to_numpy(), g["monto"].to_numpy(), K, 1000, semilla=ini)
    guardadas = pd.read_csv(RAIZ / "resultados" / f"bootstrap_{x}.csv")
    assert all(np.allclose(b[c], guardadas[c]) for c in b.columns), "las réplicas no coinciden con las guardadas"
    cx = {}
    for c in (REGLA, LOGIT, PUB):
        rel = b[FINAL] / b[c] - 1
        lo, hi = rel.quantile(0.025), rel.quantile(0.975)
        assert abs(lo - R[x]["contrastes"][c]["rel_ic95"][0]) < 1e-9 and abs(hi - R[x]["contrastes"][c]["rel_ic95"][1]) < 1e-9
        cx[c] = (vivo[x][FINAL] / vivo[x][c] - 1, lo)
        filas.append({"periodo": x, "contra": NOMBRE[c], "ventaja": pc(cx[c][0]), "IC 95%": ic((lo, hi))})
    veredicto[x] = {"H1_regla": cx[REGLA][0] >= U["H1"] and cx[REGLA][1] > 0,
                    "H2_logistica": cx[LOGIT][0] >= U["H2"] and cx[LOGIT][1] > 0, "H3_publicado": cx[PUB][1] > 0}
assert veredicto == R["veredicto"]
display(pd.DataFrame(filas).set_index(["periodo", "contra"]))
display(pd.DataFrame(veredicto).rename(index={"H1_regla": "H1 · mejor regla", "H2_logistica": "H2 · mejor logística", "H3_publicado": "H3 · solo probabilidad"}))
print("Éxito del caso (H1, H2 y H3 en los dos meses):", all(all(v.values()) for v in veredicto.values()))"""),
    C(r"""fig("hipotesis", "intervalos")"""),
    M(r"""**Robustez.** Ventaja del modelo con otros cupos, sin los pagos más caros, con el monto topado y en los días 121–144,
que ningún estudio anterior había leído."""),
    C(r"""rb = {}
for x in P:
    r = R[x]["robustez"]
    for c, nom in ((REGLA, "regla"), (LOGIT, "logística")):
        rb[f"{nom} · {x}"] = {"principal (60 por día)": pc(R[x]["contrastes"][c]["rel"]), "30 por día": pc(r["K"][c]["30"]),
                              "120 por día": pc(r["K"][c]["120"]), "sin pagos sobre el p99": pc(r["sin_top1"][c]),
                              "monto topado en el p99": pc(r["topado"][c]), "días que gana": f"{R[x]['dias_que_gana'][c]} de {R[x]['n_dias']}",
                              "días 121–144": pc(R[x]["limpio"]["contrastes"][c]["rel"]) if x == "P1" else "—"}
pd.DataFrame(rb)"""),
    M(r"""**¿Sobreajuste a los periodos? Validación cruzada en el tiempo.** Los cuatro bloques son los pliegues de una
validación con origen móvil: cada uno entrena solo con días anteriores, con 30 de margen, y se evalúa en un mes que su
modelo no vio. D1 y D2 se usaron para elegir; P1 y P2 no. Si la elección estuviera sobreajustada a D1 y D2, el modelo
caería en P1 y P2. Las políticas elegibles son las reglas, las logísticas y los modelos flexibles con F2 o F3."""),
    C(r"""filas = {}
for b, arch in ARCH.items():
    g = pd.read_parquet(PROCESADOS / f"{arch}.parquet")
    d_, y_, m_ = g["dia"].to_numpy(), g["fraude"].to_numpy(), g["monto"].to_numpy()
    eleg = [c for c in g.columns if c not in ("dia", "fraude", "monto") and not c.startswith("ISO") and not c.endswith(("F1", "F4"))]
    usd = {c: dinero(puntaje(c.split("|")[0], g[c].to_numpy(), m_), d_, y_, m_, K) for c in eleg}
    solo_p, orac = dinero(g[FINAL].to_numpy(), d_, y_, m_, K), dinero(y_ * m_, d_, y_, m_, K)
    dm, dr = (por_dia(puntaje(n.split("|")[0], g[n].to_numpy(), m_), d_, y_, m_, K) for n in (FINAL, REGLA))
    orden = sorted(eleg, key=lambda c: -usd[c])
    filas[b] = {"uso": "elegir" if b[0] == "D" else "prueba", "días": f"{PART[b][0]}–{PART[b][1]}",
                "contra la regla": pc(usd[FINAL] / usd[REGLA] - 1), "contra la logística": pc(usd[FINAL] / usd[LOGIT] - 1),
                "contra solo probabilidad": pc(usd[FINAL] / solo_p - 1), "parte del oráculo": f"{usd[FINAL] / orac:.0%}",
                "lugar del modelo": f"{orden.index(FINAL) + 1} de {len(eleg)}",
                "quién le gana": ", ".join(f"{c} ({pc(usd[c] / usd[FINAL] - 1)})" for c in orden[:orden.index(FINAL)]) or "nadie",
                "días que gana a la regla": f"{int((dm > dr).sum())} de {len(dm)}"}
pliegues = pd.DataFrame(filas).T
assert all(v.startswith("+") for c in ("contra la regla", "contra la logística", "contra solo probabilidad") for v in pliegues[c])
pliegues"""),
    M(r"""El modelo gana a la regla, a la logística y al orden por probabilidad en los cuatro pliegues, y su parte del oráculo
no cae al pasar de los pliegues que lo eligieron a los de prueba: no hay señal de que la elección se sobreajustara a D1 y
D2. Solo el ensamble XGBoost + bosque le gana en algún pliegue, por pocos puntos; perdió mucho en D1, y la regla de
selección, escrita antes del torneo, pedía ganar en el total. Además, los hiperparámetros no se ajustaron con estos
periodos (4.3), y la única búsqueda que sí ajustó, la de variables, mostró sobreajuste en la confirmación y se
descartó (3.3).

**Costo por revisión.** Si revisar cuesta, cada política elige su cupo en desarrollo para cada costo; el neto
(recuperado − costo) se mide en la prueba."""),
    C(r"""ct = pd.DataFrame([{"costo por revisión": e["costo"], "recupera": f"{e['recupera']:.0%}",
                    **{f"{k}: cupo": e[k]["K"] for k in ("modelo", "logistica", "regla")},
                    **{f"{k}: neto (mil USD)": mil(e[k]["neto_prueba"]) for k in ("modelo", "logistica", "regla")}} for e in L["costos"]])
gana = sum(e["modelo"]["neto_prueba"] > max(e["logistica"]["neto_prueba"], e["regla"]["neto_prueba"]) for e in L["costos"])
print(f"El modelo deja más neto que la regla y que la logística en {gana} de {len(L['costos'])} escenarios")
ct"""),
    C(r"""fig("montana")"""),
    M(r"""**Traza del dinero.** Cada dólar de fraude del mes cae en una sola categoría y las cuatro suman el fraude total."""),
    C(r"""tr_ = pd.DataFrame(PJ["traza"]).T
for x in P:
    assert abs(tr_.loc[x, ["ambos", "solo_modelo", "solo_regla", "ninguno"]].sum() - tr_.loc[x, "fraude_total"]) < 0.01
(tr_[["fraude_total", "ambos", "solo_modelo", "solo_regla", "ninguno"]] / 1e3).round(1).rename(columns=lambda c: f"{c} (mil USD)")"""),
    C(r"""fig("traza", "diario")"""),
    C(r"""tot = lambda n: sum(vivo[x][n] for x in P)
Markdown(f'''**Respuesta a la pregunta de negocio: sí.** Con las mismas 60 revisiones diarias, en los días 121–182 el modelo lleva
{tot(FINAL) / 1e3:,.0f} mil USD de fraude a la cola, contra {tot(REGLA) / 1e3:,.0f} mil de la mejor regla y {tot(LOGIT) / 1e3:,.0f} mil de la
logística: {(tot(FINAL) - tot(REGLA)) / 1e3:,.0f} mil USD más que la práctica actual. Las tres metas fijadas antes de la prueba se
cumplen en los dos meses, la ventaja resiste sin los pagos más caros y con otros cupos, y el modelo gana en la mayoría de
los días.''')"""),
    M(r"""### 5.3 Lectura posterior: ¿las variables nuevas habrían ayudado en la prueba?

Una sola lectura de los días 121–182 con las variables de la búsqueda de 3.3, recalculada aquí. F3 reconstruido debe
reproducir la corrida congelada."""),
    C(r"""lec = {}
for x in P:
    a = pd.read_parquet(PROCESADOS / f"anexo_puntajes_{x}.parquet")
    d_, y_, m_ = a["dia"].to_numpy(), a["fraude"].to_numpy(), a["monto"].to_numpy()
    lec[x] = {n: dinero(a[n].to_numpy() * m_, d_, y_, m_, K) for n in ("F3", "elegido", "logit_F3", "logit_elegido")}
    assert abs(lec[x]["F3"] - R[x]["usd"][FINAL]) < 0.01, "F3 no reproduce la prueba congelada"
pd.DataFrame({x: {"F3 (mil USD)": mil(lec[x]["F3"]), "variables nuevas (mil USD)": mil(lec[x]["elegido"]),
                  "variables nuevas contra F3": f"{pc(AX[x]['contrastes']['elegido_vs_F3']['rel'])} ({ic(AX[x]['contrastes']['elegido_vs_F3']['rel_ic95'])})",
                  "logística: nuevas contra F3": f"{pc(AX[x]['contrastes']['logit_elegido_vs_logit_F3']['rel'])} ({ic(AX[x]['contrastes']['logit_elegido_vs_logit_F3']['rel_ic95'])})"}
              for x in P})"""),
    C(r"""fig("confirmacion")"""),
]

DESPLIEGUE = [
    M(r"""## 6. Despliegue

### 6.1 Propuesta de implementación

| Etapa | Cuándo | Qué se hace |
|---|---|---|
| Operación | Cada noche | Se puntúan los pagos del día y los 60 con mayor fraude esperado pasan a la cola. La decisión sobre cada pago sigue siendo del equipo. |
| Etiquetas | A los 30 días | Llega el contracargo y cada pago queda etiquetado. |
| Reentrenamiento | Cada semana | Con los pagos de más de 30 días, que ya tienen etiqueta, con el mismo código (`Diseno` + XGBoost). |
| Piloto | Primer mes | Los días se asignan al azar a la cola actual o a la del modelo, para medir el efectivo recuperado. |
| Respaldo | Si el modelo falla | Si dos semanas seguidas detiene menos que la regla, se vuelve a la tabla por segmento. |

El proceso nocturno es corto: `cargar` arma el historial con los pagos hasta el cierre, el modelo de la semana puntúa,
`puntaje` multiplica por el monto y `seleccion` toma los 60 primeros. **La lista de una noche**, día 166, con los puntajes
del modelo congelado:"""),
    C(r"""x, noche = "P2", PJ["dia"]["dia"]
_, te2 = bloque(todo, *P[x])
g = PT[x].assign(producto=te2["ProductCD"].to_numpy(), tarjeta=te2["card4"].to_numpy() + " " + te2["card6"].to_numpy())
h = g[g["dia"] == noche].copy()
h["fraude esperado"] = h[FINAL] * h["monto"]
h["en la cola"] = seleccion(h["fraude esperado"].to_numpy(), h["dia"].to_numpy(), K)
cola = h[h["en la cola"]].sort_values("fraude esperado", ascending=False)
assert abs((cola["fraude"] * cola["monto"]).sum() - PJ["dia"]["modelo_usd"]) < 0.01
print(f"Día {noche}: {len(h):,} pagos; la cola tiene {len(cola)}. A los 30 días: {int(cola['fraude'].sum())} fraudes y "
      f"{(cola['fraude'] * cola['monto']).sum():,.0f} USD detenidos, de {(h['fraude'] * h['monto']).sum():,.0f} USD de fraude del día.")
top = cola.head(12)
top.assign(probabilidad=top[FINAL].map("{:.1%}".format), resultado=np.where(top["fraude"] == 1, "fraude", "legítimo"))[
    ["producto", "tarjeta", "monto", "probabilidad", "fraude esperado", "resultado"]].round(1).reset_index(drop=True).rename(index=lambda i: i + 1)"""),
    C(r"""fig("cola_noche", "operacion")"""),
    M(r"""### 6.2 Mantenimiento: monitoreo de la degradación

| Qué se mide | Cada cuándo | Señal de alarma | Qué se hace |
|---|---|---|---|
| Dólares detenidos: modelo contra la regla, en días del piloto | Semana | Dos semanas seguidas por debajo de la regla | Volver a la regla y revisar |
| Dólares por revisión y precisión de la cola | Semana | Caída sostenida frente a las semanas anteriores | Revisar datos y reentrenar |
| Deriva de los datos (PSI del monto y de la probabilidad) | Semana | PSI > 0.25 | Revisar qué cambió antes de confiar en la cola |
| Mezcla de la cola (producto, monto medio) | Semana | Cambio brusco | Revisar con el equipo |

Para ver cómo se comporta ese tablero, se corre aquí sobre los dos meses de prueba, por semana (la última semana de
cada mes junta 10 días). La edad del modelo cuenta los días desde su último día de entrenamiento."""),
    C(r"""def psi(referencia, actual, cubetas=10):
    # Índice de estabilidad poblacional: cuánto cambió la distribución de actual frente a referencia.
    cortes = np.quantile(referencia, np.linspace(0, 1, cubetas + 1)[1:-1])
    a = np.bincount(np.searchsorted(cortes, referencia), minlength=cubetas) / len(referencia)
    b = np.bincount(np.searchsorted(cortes, actual), minlength=cubetas) / len(actual)
    a, b = np.clip(a, 1e-6, None), np.clip(b, 1e-6, None)
    return float(((b - a) * np.log(b / a)).sum())


filas = []
for x, (ini, fin) in P.items():
    tr, te = bloque(todo, ini, fin)
    g = PT[x]
    d_, y_, m_ = g["dia"].to_numpy(), g["fraude"].to_numpy(), g["monto"].to_numpy()
    sel_m, sel_r = seleccion(SC[x][FINAL], d_, K), seleccion(SC[x][REGLA], d_, K)
    semana = np.minimum((d_ - ini) // 7, 3)
    ultimo = tr["dia"].max()
    p_ref = g[FINAL].to_numpy()[semana == 0]
    for w in range(4):
        k = semana == w
        km, kr = k & sel_m, k & sel_r
        filas.append({"mes": x, "semana": w + 1, "días": f"{d_[k].min()}–{d_[k].max()}", "edad del modelo (días)": f"{d_[k].min() - ultimo}–{d_[k].max() - ultimo}",
                      "modelo (mil USD)": mil((y_ * m_)[km].sum()), "regla (mil USD)": mil((y_ * m_)[kr].sum()),
                      "parte del fraude que detiene": (y_ * m_)[km].sum() / (y_ * m_)[k].sum(),
                      "USD por revisión": (y_ * m_)[km].sum() / km.sum(), "precisión de la cola": y_[km].mean(),
                      "monto medio en la cola": m_[km].mean(), "producto C en la cola": (te["ProductCD"].to_numpy()[km] == "C").mean(),
                      "PSI del monto": psi(np.log1p(tr["TransactionAmt"].to_numpy()), np.log1p(m_[k])),
                      "PSI de la probabilidad": psi(p_ref, g[FINAL].to_numpy()[k])})
mon = pd.DataFrame(filas)
mon["modelo debajo de la regla"] = mon["modelo (mil USD)"] < mon["regla (mil USD)"]
alarma = any(mon.groupby("mes")["modelo debajo de la regla"].apply(lambda s: (s & s.shift(fill_value=False)).any()))
print("¿Se habría activado el respaldo (dos semanas seguidas debajo de la regla)?", "sí" if alarma else "no")
formato = {"parte del fraude que detiene": "{:.0%}", "USD por revisión": "{:,.0f}", "precisión de la cola": "{:.0%}",
           "monto medio en la cola": "{:,.0f}", "producto C en la cola": "{:.0%}", "PSI del monto": "{:.3f}", "PSI de la probabilidad": "{:.3f}"}
mon.assign(**{c: mon[c].map(f.format) for c, f in formato.items()}).drop(columns="modelo debajo de la regla").set_index(["mes", "semana"])"""),
    C(r"""f, ax = plt.subplots(1, 2, figsize=(12, 3.4))
etq = mon["mes"] + " · s" + mon["semana"].astype(str)
ax[0].plot(etq, mon["modelo (mil USD)"], "o-", color=AZUL, label="modelo")
ax[0].plot(etq, mon["regla (mil USD)"], "o-", color=GRIS, label="mejor regla")
ax[0].set_title("Fraude detenido por semana (mil USD)"); ax[0].legend(frameon=False)
ax[1].plot(etq, mon["PSI del monto"], "o-", color=NARANJA, label="monto contra el entrenamiento")
ax[1].plot(etq, mon["PSI de la probabilidad"], "o-", color=AZUL, label="probabilidad contra la semana 1")
ax[1].axhline(0.25, color=NARANJA, ls="--", lw=1); ax[1].set_title("Deriva de los datos (PSI)"); ax[1].legend(frameon=False)
for a in ax:
    a.tick_params(axis="x", rotation=45)
plt.tight_layout(); plt.show()
edad = mon.groupby("semana")["parte del fraude que detiene"].mean()
print("Parte del fraude que detiene el modelo según la semana del mes (promedio de P1 y P2):",
      ", ".join(f"semana {w}: {v:.0%}" for w, v in edad.items()))"""),
    M(r"""En los dos meses el modelo supera a la regla todas las semanas, la deriva del monto y de la probabilidad queda lejos
del umbral y la parte del fraude que detiene no cae de forma clara entre la semana 1 y la 4, con modelos de 31 a 61
días de edad. El reentrenamiento semanal es una precaución: el monitoreo es lo que dice cuándo hace falta.

## 7. Conclusiones"""),
    C(r"""Markdown(f'''Con las mismas 60 revisiones diarias, en los días 121–182 la mejor regla lleva {tot(REGLA) / 1e3:,.0f} mil USD de fraude a la cola,
la logística {tot(LOGIT) / 1e3:,.0f} mil y el modelo {tot(FINAL) / 1e3:,.0f} mil. Contra la regla, la ventaja es de
{pc(R['P1']['contrastes'][REGLA]['rel'])} y {pc(R['P2']['contrastes'][REGLA]['rel'])}; contra la logística, de
{pc(R['P1']['contrastes'][LOGIT]['rel'])} y {pc(R['P2']['contrastes'][LOGIT]['rel'])}. Las tres hipótesis fijadas antes de la prueba
se cumplen en los dos meses.

**Por qué confiar en el resultado**

- La partición es en el tiempo, con 30 días de margen, y ninguna variable usa el futuro ni la etiqueta (3.2, 4.2).
- El modelo, los comparadores y las metas se congelaron antes de la prueba, que se corrió una sola vez (1.3, 4.1).
- Cada modelo entrena con todos los pagos ya etiquetados; el modelo final, entrenado de nuevo aquí, vuelve a ganarle a la regla (4.2).
- Con las etiquetas barajadas, el mismo modelo detiene menos de la mitad: su ventaja viene de lo que aprende (4.1).
- La ventaja se repite en los cuatro pliegues de la validación en el tiempo, y no cae del desarrollo a la prueba (5.2).
- Las probabilidades están calibradas y la ventaja resiste otros cupos, sin los pagos más caros y semana a semana (5.1, 5.2, 6.2).
- Una mejora que no se confirmó en días nuevos no se adoptó (3.3).

**Lo que se aprendió**

- Con un cupo fijo, la pregunta es de orden, no de clasificación: ordenar por probabilidad × monto vale más que mejorar el AUC.
- De las variables nuevas, la que más dinero agrega es el historial del cliente reconstruido (tarjeta + dirección + fecha de alta).
- Una mejora que solo aparece en las ventanas que la eligieron no es mejora: la confirmación en días nuevos la descartó.

**Limitaciones**

- El dinero es el monto de los pagos etiquetados como fraude que entran a la cola, no el efectivo recuperado.
- La práctica real de Vesta no es pública; la representa la mejor de seis reglas.
- La etiqueta se propaga por cuenta, así que parte del fraude es fácil de ver una vez que la cuenta ya tuvo uno.
- El margen de 30 días supone que todo contracargo llega en ese plazo.

Un piloto con asignación aleatoria de días mide lo que estos datos no pueden: cuánto efectivo se recupera y cómo se compara
el modelo con la práctica actual de Vesta.

*Cuaderno ejecutado completo en {(time.time() - T0) / 60:.1f} minutos.*''')"""),
]

CELDAS = INICIO + NEGOCIO + DATOS + PREPARACION + MODELADO + EVALUACION + DESPLIEGUE


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb["cells"] = CELDAS
    nb["metadata"] = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                      "language_info": {"name": "python"}}
    SALIDA.parent.mkdir(exist_ok=True)
    NotebookClient(nb, timeout=1800, kernel_name="python3", resources={"metadata": {"path": str(SALIDA.parent)}}).execute()
    nbf.write(nb, SALIDA)
    print("cuaderno:", SALIDA.relative_to(RAIZ))


if __name__ == "__main__":
    main()
