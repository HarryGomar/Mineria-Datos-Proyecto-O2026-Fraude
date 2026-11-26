# Guion: Qué pagos revisar

Quince láminas para 12 a 14 minutos, alrededor de un minuto cada una, y dieciocho de apéndice para preguntas. Cada
lámina dice arriba del título en qué fase de CRISP-DM está. Cada bloque indica qué se ve y qué se dice.

## 1 · Qué pagos revisar

**Ver.** Portada: los pagos de un día; en azul, los 60 que el modelo manda a revisión; en naranja, los fraudes que pasan.

**Decir.** Cada cuadro es un pago de un solo día, del tamaño de su monto. El equipo de riesgo puede revisar a mano 60 al día, alrededor de 2% de los pagos. Un fraude revisado se detiene antes del contracargo; uno que pasa se pierde completo. La pregunta del proyecto es una sola: qué 60 pagos revisar cada día para detener la mayor cantidad posible de fraude en dólares.

## 2 · Con las mismas 60 revisiones al día, el modelo detiene 45% más fraude

**Ver.** Fraude detenido en los dos meses de prueba por la práctica actual, la logística y el modelo.

**Decir.** Este es el resultado. En dos meses que apartamos hasta el final, la mejor regla, que representa la práctica actual, detiene 301 mil dólares de fraude. Una logística con la misma información, 372 mil. El modelo, 438 mil: 137 mil dólares más que la regla, 45% más, con exactamente las mismas revisiones. No hace falta más personal; solo cambia el orden de la cola. Y gana en cada mes por separado, y en 54 de los 62 días. El resto de la charla explica cómo llegamos aquí y por qué el resultado es creíble.

## 3 · Cada noche se revisan 60 de unos 2,800 pagos; un fraude que pasa se pierde completo

**Ver.** Árbol de la decisión: cada pago se revisa o se deja pasar, con lo que cuesta cada resultado; abajo, quién decide, la práctica actual y el criterio de éxito.

**Decir.** Primera fase de CRISP-DM: entender el negocio. Cada noche llegan unos 2,800 pagos y el equipo de riesgo del procesador puede revisar 60, el 2%. Para cada pago hay dos opciones. Si se revisa, se paga la revisión y, si era fraude, se detiene. Si se deja pasar y era legítimo, no pasa nada; si era fraude, llega el contracargo y se pierde el monto completo. Es la matriz de confusión del curso, en dólares. Hoy se decide con una regla fija; como Vesta no la publica, la representamos con la mejor de seis reglas de tasa histórica por monto. El éxito se mide en dólares de fraude detenidos con las mismas 60 revisiones.

## 4 · Se revisa el fraude esperado en dólares, no el pago más sospechoso

**Ver.** Los pagos del día 166 por probabilidad estimada y monto, en escala logarítmica; la línea marca 44 USD de fraude esperado y hay dos fraudes reales señalados.

**Decir.** Revisar conviene cuando la probabilidad por el monto supera el costo de revisar: es la regla del curso, p mayor o igual a C entre LTV, con el monto como valor en riesgo. Con un cupo fijo, se revisan los 60 pagos con mayor probabilidad por monto. Cada punto es un pago de un día, y los 60 revisados quedan arriba de la línea. Dos fraudes reales: uno de 554 dólares con 10% de probabilidad vale 56 dólares esperados y se revisa. Otro de 30 dólares con 80% es mucho más sospechoso, pero vale 24 y pasa. Un pago caro entra a la cola con menos probabilidad que uno barato.

## 5 · El 10% de los pagos más caros concentra 53% del fraude en dólares

**Ver.** Parte de los dólares de fraude por decil de monto y, debajo, la tasa de fraude de cada decil.

**Decir.** Segunda fase, los datos: 590 mil pagos de 182 días de la competencia IEEE-CIS de Vesta, de una copia pública con huella verificada. Solo 3.5% es fraude, y la tasa es parecida en todos los montos, entre 2% y 6%. Pero el dinero no se reparte igual: el 10% de los pagos más caros concentra 53% del fraude en dólares. Un modelo que solo cuente fraudes llenaría la cola de fraudes baratos. Por eso el monto entra al orden.

## 6 · Reconstruimos al cliente: si volvió a pagar en menos de una hora, el fraude casi se duplica

**Ver.** Tres pasos: los tres campos que forman al cliente; el historial de un pago de ejemplo, solo hacia atrás, con sus cinco medidas; y la tasa de fraude según el tiempo desde el pago anterior, con lo que agrega en dólares.

**Decir.** Tercera fase, la preparación. Los datos están anonimizados y no traen un identificador de cliente. Pero la columna D1 cuenta los días desde el alta de la tarjeta; al restarla del día del pago sale una fecha de alta fija. Tarjeta, dirección y fecha de alta identifican al cliente: 12 mil números de tarjeta se vuelven 165 mil clientes. Para cada pago medimos su historial, recencia, frecuencia y monto, como en RFM: cuántos pagos lleva, cuántos en el último día y en la última semana, cuánto pasó desde el anterior y cómo se compara el monto con su promedio. En el ejemplo, el cliente pagó hace 43 minutos y hoy paga 3.4 veces su promedio. Todas las medidas usan solo pagos anteriores y ninguna etiqueta, para que no se cuele información del futuro. Lo que revela: si el mismo cliente pagó hace menos de una hora, 6.8% de los pagos es fraude, casi el doble del promedio. Con este historial, el mismo modelo detiene 21 mil dólares más en desarrollo.

## 7 · Se decide con el pasado y se prueba una sola vez con el futuro

**Ver.** Fraude diario en dólares, días 1 a 182, coloreado según su uso: entrenamiento, desarrollo y prueba.

**Decir.** Cuarta fase, el modelado, empieza por el diseño de la prueba. La partición es por tiempo, no al azar, porque en producción siempre se predice el futuro con el pasado. Los días 1 a 60 solo entrenan. En los días 61 a 120 se eligieron modelo, variables y rivales. Los dos últimos meses se congelaron con un protocolo antes de abrirlos y se leyeron una sola vez. Entre entrenar y evaluar dejamos 30 días, porque el contracargo tarda en llegar.

## 8 · Un árbol solo no supera a la regla; el bosque y el boosting sí

**Ver.** Dólares en desarrollo de la mejor regla, el árbol, el bosque y XGBoost; línea punteada, la logística; en gris, los demás modelos.

**Decir.** Con las mismas 93 variables y el mismo cupo, recorrimos los modelos del curso. Un solo árbol detiene 243 mil dólares, menos que la mejor regla, con 275 mil: un árbol solo cambia mucho con los datos. El bosque aleatorio promedia cientos de árboles y sube a 398 mil, al nivel de la logística. XGBoost agrega árboles que corrigen los errores de los anteriores y llega a 448 mil. La red neuronal y el bosque de aislamiento quedan atrás, y el ensamble no mejora a XGBoost. XGBoost supera a la logística en los dos bloques de desarrollo y es el que pasa a la prueba.

## 9 · En los dos meses de prueba, el modelo supera las metas fijadas antes de abrirla

**Ver.** Ventaja del modelo en cada mes de prueba contra la regla y contra la logística, con su intervalo de 95% y la meta fijada antes.

**Decir.** Quinta fase, la evaluación. Antes de abrir la prueba registramos las metas: al menos 20% más que la regla y 10% más que la logística, con el intervalo de 95% entero sobre cero. Contra la regla, el modelo gana 30% el primer mes y 63% el segundo. Contra la logística, 13% y 22%. Los intervalos salen de remuestrear días completos mil veces. Las cuatro barras pasan su meta. La tercera meta, superar al mismo modelo ordenado solo por probabilidad, también se cumple; se ve en la siguiente lámina y en el apéndice.

## 10 · El mejor AUC detiene 47% menos fraude: el modelo se elige por dólares

**Ver.** ROC-AUC contra fraude detenido en la prueba para cuatro políticas con el mismo cupo; a la derecha, la exactitud de no revisar nada.

**Decir.** Esta es la lección central del curso aplicada al caso. Ordenar solo por probabilidad da el mejor AUC, 0.87, y también gana en precisión, recall y F1. Pero detiene 231 mil dólares, contra 438 mil del modelo: 47% menos. Es el mismo XGBoost; el modelo solo multiplica por el monto. La exactitud es peor todavía: no revisar nada acierta en 96.6% de los pagos, porque casi todos son legítimos. Estas métricas cuentan aciertos, y un fraude de 8 dólares pesa lo mismo que uno de 900. Si la decisión se mide en dinero, la métrica para elegir tiene que ser dinero.

## 11 · Revisando 2% de los pagos, el modelo captura 46% del fraude en dólares; la regla, 32%

**Ver.** Curva de ganancia acumulada en dólares del modelo y de la regla contra el azar, hasta 20% de los pagos revisados.

**Decir.** La curva de ganancia ordena los pagos de cada día y acumula el fraude en dólares. Con el cupo de 60, que es 2% de los pagos, el modelo captura 46% del fraude en dólares y la regla 32%. Revisar al azar capturaría 2%: el lift es de 22 veces. Dicho de otra forma, para detener lo mismo que la regla, al modelo le basta con 45% de las revisiones.

## 12 · Las variables nuevas ganaban 6.1% donde se eligieron y perdían 5.3% en días nuevos

**Ver.** Cambio en el fraude detenido con las variables nuevas: en los días donde se eligieron y en quince días que la búsqueda no vio.

**Decir.** Después de la prueba intentamos mejorar el modelo, como se haría en mantenimiento. Ocho grupos de variables nuevas compitieron con validación cruzada temporal en tres ventanas, más una rejilla de hiperparámetros. Donde se eligieron, subían el resultado 6.1%. En quince días que la búsqueda no vio, lo bajaron 5.3%, con el intervalo de 95% entero bajo cero; en los dos meses de prueba quedaron en +1.5% y 0%. La ganancia venía de elegir y medir sobre los mismos datos: sobreajuste a la validación. Por eso se queda el modelo original, y ningún cambio se adopta sin confirmarlo en días nuevos.

## 13 · Si una revisión cuesta 10 USD, conviene revisar cientos de pagos al día, no 60

**Ver.** Beneficio neto en la prueba según las revisiones por día, para costos de 10, 20 y 50 dólares; puntos, el cupo elegido en desarrollo.

**Decir.** Sexta fase, el despliegue, empieza por el tamaño del cupo. Si cada revisión cuesta, el neto es el fraude detenido menos el costo de revisar: es la curva de beneficio del curso. Con 10 dólares por revisión, el desarrollo elige 450 revisiones al día y el neto en la prueba sube 112 mil dólares. En la prueba la curva es casi plana entre 200 y 450 revisiones: lo que importa es pasar de decenas a cientos. Con 50 dólares, el mejor cupo es 66, casi el actual: el cupo de 60 solo es óptimo si revisar cuesta alrededor de 50 dólares. En los doce escenarios de costo que probamos, el modelo deja más neto que la regla y que la logística.

## 14 · En operación cambia una sola cosa: qué 60 pagos llegan cada noche al equipo

**Ver.** La cola de 60 de la noche del día 166, un día típico de la prueba, con su resultado a los 30 días y lo que detuvo cada cola; a la derecha, el ritmo de operación.

**Decir.** Así se vería el despliegue. Cada noche se puntúan los pagos del día y el equipo recibe 60, ordenados por fraude esperado; no cambia el equipo ni el cupo, y cada caso lo sigue decidiendo una persona. Esta es la cola de la noche del día 166, un día típico del segundo mes. Arriba van pagos caros con probabilidad media: la mayoría resulta legítima, pero es donde un fraude cuesta más. Esa noche la cola del modelo tuvo 10 fraudes y 4 mil dólares; la de la regla, 2 fraudes y 1,800. Cada semana se reentrena con los pagos de más de 30 días, que ya tienen etiqueta, y se vigilan los dólares por revisión. El primer mes es un piloto con días al azar, y si el modelo queda dos semanas por debajo de la regla, se vuelve a ella.

## 15 · Ordenar la cola por fraude esperado: 137 mil USD más en dos meses, con el mismo equipo

**Ver.** Fraude detenido acumulado día a día en los dos meses de prueba, modelo contra regla; a la derecha, los tres pasos.

**Decir.** Recomendamos ordenar la cola de revisión por fraude esperado. En los dos meses de prueba, el modelo acumuló 438 mil dólares de fraude detenido y la regla 301 mil: 137 mil más, y la brecha se abre de forma pareja; el modelo gana en 54 de los 62 días. Tres pasos. Primero, adoptarlo con el cupo actual, desde la próxima noche y sin más personal. Segundo, confirmarlo con un piloto de un mes con días al azar, para medir el efectivo recuperado. Tercero, medir lo que cuesta una revisión: si cuesta 10 dólares, revisar cientos de pagos al día deja 112 mil dólares más de neto. Los límites están en el apéndice: medimos exposición, no efectivo; la etiqueta de Vesta se propaga a la cuenta; y los datos son de 2017 y 2018. Gracias.

## 16 · Las seis fases de CRISP-DM

**Ver.** Apéndice. Cada fase de CRISP-DM con lo que se hizo, las técnicas del curso y sus láminas.

**Decir.** Si preguntan por la metodología: cada fase tiene sus láminas en la charla y en el apéndice, y cada lámina dice su fase arriba del título.

## 17 · Mapa de requisitos

**Ver.** Apéndice. Cada requisito del proyecto con cómo se cumple y en qué lámina.

**Decir.** Si preguntan por un requisito: aquí está dónde se cumple cada uno; el reporte tiene el detalle completo.

## 18 · La prueba confirma el orden del desarrollo

**Ver.** Apéndice. Cada política frente al techo del oráculo en cada mes de prueba.

**Decir.** El orden de desarrollo se repite en la prueba: modelo, logística, regla, solo probabilidad y mayor monto. El modelo captura 49% y 52% del techo; la regla, 38% y 32%.

## 19 · El modelo supera a las reglas y a la logística; con el ensamble empata

**Ver.** Apéndice. Ventaja del modelo con IC 95% contra seis comparadores.

**Decir.** Además de las tres hipótesis, el modelo supera al bosque y empata con el ensamble, que es más complejo. Las columnas opacas de Vesta darían más, pero no se puede saber cuándo se calculan y se excluyeron por diseño.

## 20 · La ventaja se mantiene en todos los escenarios

**Ver.** Apéndice. Ventaja contra la regla y la logística con medio cupo, doble cupo, sin los pagos más caros, con el monto topado y por días.

**Decir.** La ventaja no depende de unos pocos pagos grandes: sin los pagos sobre el percentil 99 sigue en al menos 21% contra la regla y 9% contra la logística, y el modelo gana en 24 a 28 de los 31 días de cada mes.

## 21 · Con cualquier costo por revisión, el modelo deja más neto

**Ver.** Apéndice. Neto del modelo, la logística y la regla con seis costos por revisión y dos tasas de recuperación.

**Decir.** Cada política elige su cupo en desarrollo y se mide en la prueba. En los doce escenarios, el modelo deja más neto; con 100 dólares por revisión, la regla deja de revisar.

## 22 · Cada dólar de fraude cae en una caja: ambos, solo modelo, solo regla o ninguno

**Ver.** Apéndice. Traza del fraude de cada mes: lo que revisan ambas políticas, solo el modelo, solo la regla o ninguna.

**Decir.** Modelo y regla difieren en 1,200 a 1,300 revisiones por mes. El modelo encuentra cientos de fraudes que la regla no ve; la regla encuentra pocas decenas que el modelo no ve, más caros pero muchos menos.

## 23 · Precisión–recall muestra mejor el punto de operación que la ROC

**Ver.** Apéndice. Curvas ROC y precisión–recall con la cola real de 60 por día marcada.

**Decir.** En la ROC la cola queda pegada al eje, con 1.5% de falsos positivos; en precisión–recall se ve que 70% de las revisiones van a legítimos. Las dos curvas ignoran el monto.

## 24 · Las probabilidades subestiman un poco el fraude

**Ver.** Apéndice. Curva de calibración del modelo y de la logística, con el fraude esperado contra el observado en la cola.

**Decir.** El modelo reduce el error de Brier 18% contra la tasa media y la logística 7%. Las probabilidades subestiman un poco, por eso el umbral óptimo de beneficio queda algo por debajo del costo.

## 25 · Qué se observa y qué se supone

**Ver.** Apéndice. Tabla de cantidades observadas y supuestos.

**Decir.** Monto y etiqueta son observados. El dinero salvado por revisión, el retraso de la etiqueta y la práctica actual son supuestos, iguales para todas las políticas.

## 26 · Calidad de los datos: faltantes, fechas relativas y etiqueta propagada

**Ver.** Apéndice. Hallazgos de calidad de datos y su tratamiento.

**Decir.** Hay muchos faltantes informativos, fechas relativas y una etiqueta que Vesta propaga a la cuenta: 62% de los clientes con algún fraude tienen todos sus pagos marcados.

## 27 · 93 variables en cinco grupos

**Ver.** Apéndice. Catálogo de variables y cómo entran a la matriz de diseño.

**Decir.** Monto y reloj, distancias e identidad, categóricas, historial de tarjeta y cliente reconstruido. Las 367 columnas opacas quedan fuera; no se repondera el desbalance para no deformar la probabilidad.

## 28 · Seis controles contra la fuga de información

**Ver.** Apéndice. Riesgos de fuga, control y comprobación.

**Decir.** Con las etiquetas barajadas, el modelo cae a 117 mil dólares, debajo de ordenar por monto: no hay señal que venga de una fuga.

## 29 · El historial del cliente agrega 21 mil USD en desarrollo

**Ver.** Apéndice. Dólares de XGBoost con cada conjunto de variables; rombos, la logística.

**Decir.** Con el mismo XGBoost, el historial del cliente agrega 21 mil dólares. Las columnas opacas agregarían 71 mil, pero no se pueden fechar y se excluyeron antes de la prueba.

## 30 · La penalización con más dólares no coincide con la de mayor AUC

**Ver.** Apéndice. Dólares y AUC de la logística según la penalización L2.

**Decir.** El dinero toca techo en C igual a 0.003 y el AUC en 0.01: elegir por AUC habría dado otra logística.

## 31 · Importancia por permutación: monto y centavos es el grupo principal

**Ver.** Apéndice. Dólares que pierde la cola al permutar cada grupo de variables.

**Decir.** El monto es el grupo más importante; sin el historial del cliente se pierden 35 mil dólares. El historial de la tarjeta aporta casi cero porque el del cliente ya lo contiene.

## 32 · Parada temprana en 618 árboles

**Ver.** Apéndice. Pérdida logarítmica en entrenamiento y validación según el número de árboles.

**Decir.** La validación deja de mejorar cerca de 600 árboles, el mismo número que fijó el protocolo; después, el entrenamiento sigue bajando y eso es sobreajuste.

## 33 · Validación cruzada temporal para buscar variables nuevas

**Ver.** Apéndice. Ventanas de búsqueda, días de confirmación y prueba, con su entrenamiento y margen.

**Decir.** Tres ventanas de quince días eligen variables; los días 106 a 120 confirman; la prueba se lee una sola vez. Es el diseño detrás de la lámina 12.
