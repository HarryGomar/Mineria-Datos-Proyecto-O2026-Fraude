# Protocolo congelado: qué pagos revisar

Congelado el 23 de noviembre de 2026, después del torneo de desarrollo y antes de leer cualquier pago
del día 121 en adelante. `scripts/03_prueba.py` verifica las huellas de la sección 8 y se niega a
correr si algo cambió.

## 1. Decisión

| Elemento | Definición |
|---|---|
| Quién | El equipo de riesgo de un procesador de pagos de comercio electrónico (Vesta) |
| Cuándo | Al cierre de cada día relativo, sobre los pagos ya autorizados de ese día |
| Opciones | Mandar el pago a revisión manual o dejarlo pasar |
| Recurso | K = 60 revisiones por día (cerca de 2% de los pagos), igual para todas las políticas |
| Dinero | USD (`TransactionAmt`) de los pagos etiquetados como fraude que entran a la cola |
| Práctica actual | No publicada. La representa la mejor regla del torneo de desarrollo |

## 2. Datos

IEEE-CIS Fraud Detection (Vesta), archivo de entrenamiento unido, en la copia pública OpenML 46858.
`datos/fuente.json` guarda la URL y el SHA-256, y `src/revisar/datos.py` lo verifica en cada lectura.
`TransactionDT` está en segundos desde una referencia anonimizada; el día relativo es
`TransactionDT // 86400` (días 1 a 182).

## 3. Periodos

| Uso | Días | Entrenamiento |
|---|---|---|
| Desarrollo D1 | 61–90 | días 1–30 |
| Desarrollo D2 | 91–120 | días 1–60 |
| Prueba P1 | 121–151 | días 1–90 |
| Prueba P2 | 152–182 | días 1–121 |

El margen de 30 días entre el entrenamiento y el periodo evaluado representa el tiempo en que la
etiqueta madura. Los días 121–144 se reportan aparte porque ningún estudio anterior los leyó.
`../docs/fraude-avanzado.md` usó los días 145–182 con otra decisión.

## 4. Selección de desarrollo

Regla escrita antes del torneo: `docs/criterio_desarrollo.md`. Resultado
(`resultados/desarrollo_seleccion.json`):

| Papel | Clave | Definición | USD D1 | USD D2 |
|---|---|---|---:|---:|
| Modelo final | `XGB|F3` | XGBoost sobre F3 (descriptivas + historial de tarjeta + cliente), probabilidad × monto | 183,712 | 264,173 |
| Mejor regla (práctica actual) | `R_segmento` | Tasa de fraude suavizada por producto × red × tipo de tarjeta × dispositivo, × monto | 73,313 | 201,473 |
| Mejor logística | `LOGIT_C0.003|F3` | Logística L2, C = 0.003, sobre F3, probabilidad × monto | 142,792 | 254,199 |
| Comparador publicado | `PUBLICADO` | El modelo final ordenado solo por probabilidad, como en la competencia | 100,752 | 100,508 |

Ventaja del modelo final en desarrollo:
- sobre la mejor regla: +150.6% en D1 y +31.1% en D2;
- sobre la mejor logística: +28.7% y +3.9%;
- sobre el comparador publicado: +82.3% y +162.8%.

El ensamble XGBoost + bosque quedó por debajo de XGBoost (437,612 contra 447,886 USD). XGBoost supera a
la mejor logística en los dos bloques, así que se cumple la condición 3 del criterio.

**Riesgo declarado antes de la prueba:** en D2 la ventaja sobre la logística es de solo
+3.9%, debajo del umbral de H2. H2 puede fallar; el umbral no se baja por eso.

Las columnas opacas (F4) darían 518,772 USD en desarrollo contra
447,886 de F3. Siguen fuera por la razón escrita en el criterio.

## 5. Hipótesis de la prueba

Todas las ventajas se miden en dólares de fraude dentro de la cola, con K = 60. Los intervalos son de
un bootstrap pareado de 1,000 réplicas: se remuestrean días con reemplazo, los mismos para todas las
políticas, y la cola de cada día queda como la eligió cada política.

| Hipótesis | Condición en cada periodo de prueba |
|---|---|
| H1 | El modelo final supera a la mejor regla por ≥ +20% y el límite inferior del IC 95% es > 0 |
| H2 | El modelo final supera a la mejor logística por ≥ +10% y el límite inferior del IC 95% es > 0 |
| H3 | El modelo final (probabilidad × monto) supera al enfoque de la competencia (mismo modelo, solo probabilidad); límite inferior > 0 |

**Éxito del caso:** H1, H2 y H3 en P1 y en P2.

Se reportan sin ser condición:
- la ventaja con K = 30 y K = 120;
- sin los pagos de monto mayor al percentil 99 del entrenamiento;
- con el monto topado en ese percentil;
- los días que gana el modelo;
- los días 121–144;
- el AUC y la precisión;
- el techo del oráculo;
- las columnas opacas de Vesta (F4), como diagnóstico.

## 6. Qué no cambia después de congelar

Variables, hiperparámetros, K, márgenes, la selección de la sección 4 y el código de evaluación. Si la
prueba falla, se reporta como falla.

## 7. Advertencias declaradas antes de la prueba

- La etiqueta es la de Vesta: contracargo reportado, propagado a pagos posteriores de la misma cuenta,
  dirección o correo. Parte del acierto puede ser reconocer cuentas ya marcadas.
- El dinero es exposición etiquetada que entra a la cola, no efectivo recuperado.
- La práctica actual real no se conoce; la mejor regla la representa.
- Seis meses de 2017-2018, fechas relativas.

## 8. Huellas SHA-256

| Archivo | SHA-256 (finales de línea LF) |
|---|---|
| `src/revisar/datos.py` | `90648df3a5b6fa95a5636ed31de51690f988825a22bebc9ac16cd23aa08fb69d` |
| `src/revisar/politicas.py` | `8a545716b4f00b1ceb3f71dd22b32352b76cf8dbce0153debaf85eece7ef9ec2` |
| `src/revisar/evaluacion.py` | `1976ee267ba2d96004301b89639605c460b9447b5054c973a511616c1cf7037f` |
| `scripts/03_prueba.py` | `7178b644bc2459e97f2f3f52152f1673b16da57483abd8108290d371b7960d8a` |
| `resultados/desarrollo_seleccion.json` | `af6ba98a7ea9f593e8f8039ed21557bc83a0a68b2a9b7dc9fdea6a703994c063` |
