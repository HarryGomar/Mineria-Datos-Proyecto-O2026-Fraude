# Mapa de requisitos

Dónde se cumple cada requisito del proyecto final en los cuatro entregables: el reporte
(`reporte/reporte.md`), el cuaderno ejecutado (`notebooks/que_pagos_revisar.ipynb`), la presentación
(`presentacion/que-pagos-revisar.html`, láminas 1–26 y apéndice 27–48) y el código (`src/revisar`, `scripts/`).

## Requisitos de la decisión y la evaluación

| Requisito | Cómo se cumple | Reporte | Cuaderno | Láminas |
|---|---|---|---|---|
| Decisión: quién, cuándo, opciones y recurso | Revisión manual de pagos ya autorizados, 60 por día | 1.1 | 1 | 3 |
| Dinero de la decisión | Dólares de fraude dentro de la cola; matriz de confusión en dólares | 1.2, 5.3 | 1, 5 | 4 |
| Mejora significativa fijada antes de la prueba | H1 ≥ 20%, H2 ≥ 10%, H3 > 0, con límite inferior del IC 95% > 0 (`docs/protocolo.md`) | 1.3, 5.2 | 1, 5 | 12, 27 |
| Mismo presupuesto para todas las políticas | 60 revisiones por día; con costo por revisión, cada política elige su cupo en desarrollo | 1.1, 5.7 | 5 | 2, 11, 17 |
| Práctica actual y reglas fuertes | Seis reglas de tasa histórica × monto; la mejor representa la práctica actual | 4.2, 4.3 | 4 | 10, 11 |
| Base aprendida con la misma información | Logística L2 con las mismas variables y la misma matriz de diseño | 4.2, 4.5 | 4 | 9, 12, 40 |
| Comparador publicado | El enfoque de la competencia IEEE-CIS: el mismo modelo ordenado por probabilidad | 4.3, 5.4 | 5 | 13, 14, 41, 44 |
| Elegir en desarrollo y probar en dos periodos o más | Días 61–120 para elegir; días 121–151 y 152–182 congelados, una sola corrida | 4.1, 5 | 4, 5 | 5, 10, 11 |
| Ganancia por periodo con intervalo pareado | Bootstrap pareado de 1,000 réplicas que remuestrean días; recalculado en el cuaderno | 5.2 | 5 | 12, 28 |
| Quitar los casos más grandes | Sin pagos sobre el percentil 99, monto topado, cupos de 30 y 120, días 121–144 | 5.8 | 5 | 19 |
| Traza del dinero | Ambos, solo modelo, solo regla y ninguno suman el fraude del mes | 5.9 | 5 | 20 |
| Observado contra supuesto | Monto y etiqueta observados; dinero salvado supuesto; calibración | 5.6, 8 | 5 | 18, 21, 43 |
| Despliegue | Cola nocturna, reentrenamiento semanal, piloto aleatorio, monitoreo y respaldo | 7 | 7 | 25 |
| Mantenimiento | Búsqueda de variables con validación cruzada temporal y bloque de confirmación | 6 | 6 | 22–24, 35–39 |
| Limitaciones | Dinero etiquetado, práctica desconocida, etiqueta propagada, margen de 30 días | 8 | 8 | 21 |
| Reproducibilidad | Datos públicos con huella SHA-256, protocolo con huellas del código, scripts numerados | 10 | todo el cuaderno | 48 |

## CRISP-DM

| Fase | Reporte | Cuaderno | Láminas |
|---|---|---|---|
| Comprensión del negocio | 1 | 1 | 3, 4, 16, 17 |
| Comprensión de los datos | 2 | 2 | 5, 6, 8, 32 |
| Preparación de los datos | 3 | 3 | 7, 9, 33, 34, 35 |
| Modelado | 4 | 4 | 10, 30, 36, 37, 38, 40 |
| Evaluación | 5, 6 | 5, 6 | 11–15, 18–20, 22–24, 27–29, 31, 39, 41–45 |
| Despliegue | 7 | 7 | 16, 17, 25, 46 |

## Técnicas del curso

| Técnica | Reporte | Láminas |
|---|---|---|
| Matriz de confusión con costos y beneficios | 1.2, 5.3 | 4 |
| Paradoja de la exactitud; precisión, recall y F1 | 5.4 | 13, 44 |
| Curvas ROC y precisión–recall; AUC frente a dinero | 4.5, 5.4, 5.5 | 14, 41, 42 |
| Ganancia acumulada y lift | 5.5 | 15, 43, 45 |
| Umbral de decisión con costos (p > C / LTV) y curva de beneficio | 1.2, 5.7 | 16, 17, 46 |
| Calibración y error de Brier | 5.6 | 18 |
| Ingeniería de variables (RFM, velocidad, novedad, entidades compartidas) | 3.1, 6.1 | 7, 8, 35 |
| Matriz de diseño: cuantiles, faltantes, one-hot con mínimo, frecuencia | 3.2 | 33 |
| Fuga de información | 3.3 | 31, 34 |
| Árboles, bosque aleatorio, boosting, redes y ensambles | 4 | 10, 30 |
| Regularización L2 | 4.5 | 40 |
| Detección de anomalías (bosque de aislamiento) | 4.6, 5.10 | 31 |
| Importancia por permutación | 4.6 | 29, 39 |
| Validación temporal y bootstrap pareado | 4.1, 5.2 | 5, 12, 22 |
| Validación cruzada temporal, selección hacia adelante, rejilla con parada temprana | 6 | 22, 23, 36, 37, 38 |
