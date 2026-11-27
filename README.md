# Qué pagos revisar

Proyecto final de Minería de Datos (ITAM), con la metodología CRISP-DM.

Al cierre de cada día, el equipo de riesgo de un procesador de pagos puede enviar 60 pagos ya autorizados a
revisión manual. Un fraude revisado se detiene antes del contracargo; uno no revisado se pierde completo. El
proyecto construye un modelo que ordena los pagos de cada día por fraude esperado (probabilidad × monto) y lo
compara, con el mismo cupo, contra la mejor regla, una logística regularizada con la misma información y el
enfoque de la competencia de Kaggle (ordenar solo por probabilidad).

Datos públicos: IEEE-CIS Fraud Detection (Vesta), 590,540 pagos en 182 días, copia OpenML 46858.

## Resultado

Miles de dólares de fraude dentro de la cola, 60 revisiones por día, en dos meses que no se usaron para ninguna
decisión. El modelo, los comparadores y las hipótesis se congelaron antes de leerlos.

| | Días 121–151 | Días 152–182 |
|---|---:|---:|
| Mejor regla: tasa por segmento × monto | 162.6 | 138.7 |
| Mejor logística (C = 0.003) | 186.9 | 185.5 |
| Mismo modelo ordenado solo por probabilidad | 100.6 | 129.9 |
| **XGBoost, probabilidad × monto** | **211.4** | **226.7** |
| Contra la mejor regla (IC 95% pareado) | +30.1% [+16.8%, +49.8%] | +63.4% [+39.7%, +97.0%] |
| Contra la mejor logística | +13.1% [+7.0%, +21.8%] | +22.2% [+8.7%, +39.3%] |

Las tres hipótesis fijadas antes de la prueba se cumplen en los dos meses. Una búsqueda posterior de variables
con validación cruzada temporal subió 6.1% en las ventanas de búsqueda y bajó 5.3% en los días de confirmación,
así que el modelo congelado se mantiene.

## Entregables

| Entregable | Archivo |
|---|---|
| Reporte | [`reporte/reporte.md`](reporte/reporte.md) (también [`reporte.pdf`](reporte/reporte.pdf) y `reporte.html`) |
| Cuaderno ejecutado | [`notebooks/que_pagos_revisar.ipynb`](notebooks/que_pagos_revisar.ipynb) |
| Presentación | [`presentacion/que-pagos-revisar.pdf`](presentacion/que-pagos-revisar.pdf) y `que-pagos-revisar.html` |
| Guion de la presentación (10–15 min) | [`presentacion/guion.md`](presentacion/guion.md) |
| Mapa de requisitos | [`docs/mapa_requisitos.md`](docs/mapa_requisitos.md) |
| Protocolo congelado | [`docs/protocolo.md`](docs/protocolo.md) |

La presentación HTML es un solo archivo: hay que descargarlo y abrirlo en el navegador. Las flechas avanzan,
`N` muestra las notas, `O` la vista general y `F` la pantalla completa.

## Estructura

```text
datos/fuente.json        dirección y huella SHA-256 de la copia pública de los datos
docs/                    criterio de selección, protocolo congelado, diseño del anexo, mapa de requisitos
src/revisar/             datos y variables, políticas, evaluación, figuras y presentación
scripts/                 00 a 09: descarga, exploración, desarrollo, prueba, anexo y entregables
resultados/              resultados de cada paso (JSON y CSV)
notebooks/               cuaderno ejecutado
reporte/                 reporte en Markdown, HTML y PDF, con sus figuras en SVG
presentacion/            presentación HTML y PDF, guion y marco (estilos, navegación, fuentes OFL)
```

## Reproducir

Python 3.12.

```text
pip install -e ".[entregables]"
python scripts/00_descargar.py        # descarga OpenML 46858 (78 MB) y verifica la huella
python scripts/01_exploracion.py      # días 1-120
python scripts/01b_eda.py             # días 1-120: análisis exploratorio de la presentación
python scripts/02_desarrollo.py       # torneo de desarrollo y selección
python scripts/03_prueba.py           # prueba congelada: verifica las huellas del protocolo
python scripts/04_resumen.py
python scripts/04b_lecciones.py
python scripts/04c_curvas_curso.py
python scripts/06_variables.py        # anexo: búsqueda de variables con validación temporal
python scripts/07_anexo_prueba.py     # anexo: lectura posterior de la prueba
python scripts/05_presentacion.py --pdf
python scripts/08_cuaderno.py
python scripts/09_reporte.py --pdf
```

Los datos crudos y procesados no están en el repositorio. Por omisión van a `datos/crudos` y
`datos/procesados`; otras rutas se indican con las variables `REVISAR_CRUDOS` y `REVISAR_PROCESADOS` o con un
`config_local.json` (`{"crudos": "...", "procesados": "..."}`). Los scripts 02, 03 y 06 entrenan muchos modelos
y son los más lentos. Las figuras de la presentación salen de los resultados guardados; el cuaderno y el reporte
reutilizan esas mismas figuras.

### En otra máquina

Los dólares del modelo cambian con la plataforma: con el mismo código, semilla y versiones, una Mac con Apple
Silicon da 217.6 y 230.3 mil USD en la prueba, contra 211.4 y 226.7 publicados. El veredicto no cambia. Por eso
`resultados/` guarda la corrida publicada y hay dos caminos:

- **Regenerar la presentación y el reporte** desde `resultados/`, con `05_presentacion.py` y `09_reporte.py`:
  tardan segundos y dan el mismo HTML. Los pasos 04, 04b, 04c y 08 necesitan además los puntajes por pago
  (`datos/procesados`), que solo salen de correr 02, 03, 06 y 07.
- **Volver a correr el experimento** (pasos 01 a 07) en otra carpeta, sin tocar `resultados/`:

  ```text
  export REVISAR_RESULTADOS=reejecucion/resultados REVISAR_PROCESADOS=reejecucion/procesados
  ```

  Sin esto la secuencia se detiene: `03_prueba.py` exige que `resultados/desarrollo_seleccion.json` conserve su
  huella, que 02 cambia al reescribirlo, y `07_anexo_prueba.py` no corre si su salida ya existe. El veredicto
  nuevo queda en `reejecucion/resultados/prueba.json`.

En macOS, XGBoost necesita OpenMP (`brew install libomp`). `--pdf` usa Chrome, Edge o Chromium; si no está en una
ruta usual, `REVISAR_NAVEGADOR` indica cuál.

`docs/protocolo.md` registra las huellas SHA-256 de `datos.py`, `politicas.py`, `evaluacion.py`, `03_prueba.py`
y `desarrollo_seleccion.json`; `03_prueba.py` no corre si alguno cambió. `docs/protocolo.md` y
`docs/criterio_desarrollo.md` citan un estudio anterior con estos datos (`../docs/fraude-avanzado.md`) que no
forma parte de este repositorio.
