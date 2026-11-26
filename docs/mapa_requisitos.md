# Mapa de requisitos

Dónde se cumple cada requisito del proyecto final en los cuatro entregables: el reporte
(`reporte/reporte.md`), el cuaderno ejecutado (`notebooks/que_pagos_revisar.ipynb`), la presentación
(`presentacion/que-pagos-revisar.html`, láminas 1–17 y apéndice A1–A19) y el código (`src/revisar`, `scripts/`).

## Requisitos de la decisión y la evaluación

| Requisito | Cómo se cumple | Reporte | Cuaderno | Láminas |
|---|---|---|---|---|
| Decisión: quién, cuándo, opciones y recurso | Revisión manual de pagos ya autorizados, 60 por día | 1.1 | 1.1 | 3 |
| Dinero de la decisión | Dólares de fraude dentro de la cola; matriz de confusión en dólares | 1.2, 5.3 | 1.1, 5.1 | 3, 4 |
| Mejora significativa fijada antes de la prueba | H1 ≥ 20%, H2 ≥ 10%, H3 > 0, con límite inferior del IC 95% > 0 (`docs/protocolo.md`) | 1.3, 5.2 | 1.3, 5.2 | 11, A4 |
| Mismo presupuesto para todas las políticas | 60 revisiones por día; con costo por revisión, cada política elige su cupo en desarrollo | 1.1, 5.7 | 1.1, 5.1, 5.2 | 2, A3, A6 |
| Práctica actual y reglas fuertes | Seis reglas de tasa histórica × monto; la mejor representa la práctica actual | 4.2, 4.3 | 4.1 | 10, A3 |
| Base aprendida con la misma información | Logística L2 con las mismas variables y la misma matriz de diseño | 4.2, 4.5 | 4.1, 4.3 | 10, A14, A15 |
| Comparador publicado | El enfoque de la competencia IEEE-CIS: el mismo modelo ordenado por probabilidad | 4.3, 5.4 | 5.1, 5.2 | 4, 11, 12, A8 |
| Revisar siempre los casos más claros | Cola mixta (lugares reservados para los más probables) y valor por fraude atrapado, contando el fraude evitado al bloquear la tarjeta: ninguna variante detiene más dinero | — | 5.1 | 4 |
| Elegir en desarrollo y probar en dos periodos o más | Días 61–120 para elegir; días 121–151 y 152–182 congelados, una sola corrida | 4.1, 5 | 4.1, 4.2, 5 | 9, 10, A3 |
| Sin sobreajuste a los periodos | Cuatro pliegues con origen móvil (D1, D2, P1, P2): el modelo gana a la regla, a la logística y al orden por probabilidad en los cuatro, y no cae del desarrollo a la prueba | 4.1, 5 | 5.2 | 9, 11, A19 |
| Ganancia por periodo con intervalo pareado | Bootstrap pareado de 1,000 réplicas que remuestrean días; el cuaderno las vuelve a generar | 5.2 | 5.2 | 11, A4 |
| Quitar los casos más grandes | Sin pagos sobre el percentil 99, monto topado, cupos de 30 y 120, días 121–144 | 5.8 | 3.1, 5.2 | A5 |
| Traza del dinero | Ambos, solo modelo, solo regla y ninguno suman el fraude del mes | 5.9 | 5.2 | A7 |
| Observado contra supuesto | Monto y etiqueta observados; dinero salvado supuesto; calibración | 5.6, 8 | 5.1, 7 | A9, A10 |
| Despliegue | Cola nocturna, reentrenamiento semanal, piloto aleatorio, monitoreo y respaldo | 7 | 6.1 | 15, 16, 17 |
| Mantenimiento | Monitoreo semanal con respaldo (dinero contra la regla, precisión, deriva PSI), corrido sobre la prueba; búsqueda de variables con validación cruzada temporal y bloque de confirmación | 6, 7 | 3.3, 6.2 | 14, 16, A17, A18 |
| Limitaciones | Dinero etiquetado, práctica desconocida, etiqueta propagada, margen de 30 días | 8 | 7 | A10, A11 |
| Reproducibilidad | Datos públicos con huella SHA-256, protocolo con huellas del código, scripts numerados; el cuaderno reentrena el modelo final y reproduce sus puntajes | 10 | 0, 2.1, 4.2 y todo el cuaderno | 9, A2, A13 |

## CRISP-DM

| Fase | Reporte | Cuaderno | Láminas |
|---|---|---|---|
| Comprensión del negocio | 1 | 1.1–1.3 | 3, 4, 15, A6 |
| Comprensión de los datos | 2 | 2.1–2.3 | 5–7, A10, A11 |
| Preparación de los datos | 3 | 3.1–3.3 | 8, A12–A14 |
| Modelado | 4 | 4.1–4.3 | 9, 10, A15, A17 |
| Evaluación | 5, 6 | 5.1–5.3 | 2, 11–14, A3–A5, A7–A9, A16, A18, A19 |
| Despliegue | 7 | 6.1, 6.2 | 15, 16, 17, A6 |

## Técnicas del curso

| Técnica | Reporte | Láminas |
|---|---|---|
| Matriz de confusión con costos y beneficios | 1.2, 5.3 | 3, 4 |
| Análisis exploratorio: matriz de dispersión y distribuciones por clase | 2 | 5, 6 |
| Paradoja de la exactitud; precisión, recall y F1 | 5.4 | 12, A8 |
| Curvas ROC y precisión–recall; AUC frente a dinero | 4.5, 5.4, 5.5 | 12, A8, A15 |
| Ganancia acumulada y lift | 5.5 | 7, 13 |
| Umbral de decisión con costos (p > C / LTV) y curva de beneficio | 1.2, 5.7 | 4, 15, A6 |
| Calibración y error de Brier | 5.6 | A9 |
| Ingeniería de variables (RFM, velocidad, novedad, entidades compartidas) | 3.1, 6.1 | 8, A12, A14 |
| Matriz de diseño: cuantiles, faltantes, one-hot con mínimo, frecuencia | 3.2 | A12 |
| Fuga de información | 3.3 | A13 |
| Árboles, bosque aleatorio, boosting, redes y ensambles | 4 | 10 |
| Regularización L2 | 4.5 | A15 |
| Detección de anomalías (bosque de aislamiento) | 4.6, 5.10 | 10 |
| Importancia por permutación | 4.6 | A16 |
| Validación temporal y bootstrap pareado | 4.1, 5.2 | 9, 11, A4 |
| Validación cruzada temporal, selección hacia adelante, rejilla con parada temprana | 6 | 14, A17, A18, A19 |
