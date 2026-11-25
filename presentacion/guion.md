# Guion: Qué pagos revisar

Quince láminas para 12 a 14 minutos, alrededor de un minuto cada una, y dieciocho de apéndice para preguntas. Cada
lámina dice arriba del título en qué fase de CRISP-DM está. Cada bloque indica qué se ve y qué se dice.

## 1 · Qué pagos revisar

**Ver.** Portada: los 2,931 pagos de un día en orden de llegada; en azul, los 60 que manda a revisión el modelo; en naranja, los fraudes que no se revisan.

**Decir.** Cada cuadro es un pago de un solo día, del tamaño de su monto. El equipo de riesgo puede revisar a mano 60 al día, uno de cada cincuenta. Un fraude revisado se detiene antes del contracargo; uno que no se revisa se pierde completo. La pregunta del proyecto es una sola: qué 60 pagos revisar cada día para detener la mayor cantidad posible de fraude en dólares.

## 2 · Con las mismas 60 revisiones al día, el modelo atrapa 45% más fraude

**Ver.** Tres barras sobre el máximo posible con el mismo cupo: la mejor regla, la logística y el modelo, en los dos meses de prueba.

**Decir.** Este es el resultado. En dos meses que nadie tocó hasta el final, la mejor regla, que representa la práctica actual, atrapa 301 mil dólares de fraude. Una logística regularizada con la misma información atrapa 372 mil. El modelo atrapa 438 mil: 137 mil dólares más que la regla, 45% más, con exactamente las mismas revisiones. La barra completa es lo que atraparía alguien que conoce las etiquetas: el modelo llega a la mitad de ese techo y la regla a un tercio. Gana en cada uno de los dos meses, contra la regla y contra la logística, y los cuatro intervalos de 95% quedan sobre cero. El resto de la charla explica cómo llegamos aquí y por qué el resultado es creíble.

## 3 · La decisión: qué 60 pagos revisar cada día

**Ver.** Un día de la prueba: cada pago según su probabilidad estimada y su monto; los 60 revisados quedan arriba de la diagonal.

**Decir.** Primera fase, el negocio. Quién decide: el equipo de riesgo del procesador. Cuándo: al cierre del día, sobre pagos ya autorizados, con lo que se sabe hasta ese momento. Las opciones son dos: revisar o dejar pasar. El recurso escaso es el cupo de 60 revisiones. En la gráfica, el eje horizontal es la probabilidad de fraude y el vertical el monto. Se revisan los 60 pagos con mayor fraude esperado, probabilidad por monto, y por eso la frontera es una diagonal: un pago caro entra con menos probabilidad que uno barato. El umbral no se fija de antemano; lo fija el cupo.

## 4 · Un error no cuesta lo mismo en cada pago: la matriz se mide en dólares

**Ver.** Matriz de confusión del segundo mes de prueba, de la mejor regla al modelo, con dólares en las celdas de fraude.

**Decir.** La matriz de confusión del curso cuenta aciertos y errores. Aquí un error no cuesta lo mismo en cada pago: dejar pasar un fraude de mil dólares no es igual que dejar pasar uno de diez. Por eso la matriz se lee en dólares. En el segundo mes, el fraude atrapado pasa de 139 mil a 227 mil dólares y el que se escapa baja de 339 mil a 251 mil. La regla del curso dice revisar si la probabilidad supera el costo entre el valor en riesgo. Aquí el valor en riesgo es el monto, así que la regla queda probabilidad por monto mayor que el costo. De ahí sale el orden de la cola.

## 5 · El 10% de los pagos más caros concentra 53% del fraude en dólares

**Ver.** Parte de los dólares de fraude por decil de monto y, debajo, la tasa de fraude de cada decil.

**Decir.** Segunda fase, los datos. Son los de la competencia IEEE-CIS de Vesta: 590 mil pagos en 182 días, de una copia pública con huella verificada. Solo 3.5% de los pagos es fraude, uno de cada 28. El dato clave es dónde está el dinero: el 10% de los pagos más caros concentra 53% del fraude en dólares. Un modelo que solo cuente fraudes llenaría la cola de fraudes baratos. El monto tiene que entrar al orden.

## 6 · Una señal que no viene en los datos: reconstruimos al cliente

**Ver.** Tasa de fraude según el tiempo desde el pago anterior del mismo cliente.

**Decir.** Tercera fase, la preparación. Vesta anonimizó los datos y no trae un identificador de cliente. Pero la columna D1 cuenta los días desde el alta de la tarjeta; al restarla del día del pago sale una fecha de alta fija. Tarjeta, dirección y fecha de alta identifican al cliente. Con eso medimos su historial: cuántos pagos previos, cuánto tiempo desde el anterior, cuánto se desvía el monto. Si el mismo cliente pagó hace menos de una hora, 6.8% de los pagos es fraude, el doble del promedio. Todas las medidas usan solo pagos anteriores y ninguna etiqueta, para que no entre información del futuro. Con este historial, el mismo modelo atrapa 21 mil dólares más en desarrollo.

## 7 · Se elige con el pasado y se prueba una sola vez con el futuro

**Ver.** Fraude diario en dólares, días 1 a 182, coloreado según su uso: entrenamiento, desarrollo y prueba.

**Decir.** Cuarta fase, el modelado, empieza por el diseño de la prueba. La partición es por tiempo, no al azar, porque en producción siempre se predice el futuro con el pasado y el fraude cambia de un mes a otro. Los días 1 a 60 solo entrenan. Los días 61 a 120 son el desarrollo: ahí se eligieron modelo, variables, reglas y comparadores. Los dos últimos meses se congelaron con un protocolo y huellas SHA-256 antes de abrirlos, y se leyeron una sola vez. Entre entrenar y evaluar hay 30 días de margen, porque el contracargo tarda en llegar.

## 8 · Un árbol solo no supera a la regla; el bosque y el boosting sí

**Ver.** Dólares en desarrollo de la mejor regla, el árbol, el bosque y XGBoost; línea punteada, la logística; en gris, los demás modelos.

**Decir.** Con las mismas 93 variables y el mismo cupo, recorrimos los modelos del curso. Un solo árbol de decisión atrapa 243 mil dólares, menos que la mejor regla, con 275 mil; aun con menos variables apenas la iguala. Un árbol solo tiene demasiada varianza. El bosque aleatorio promedia muchos árboles y sube a 398 mil, al nivel de la logística. XGBoost agrega árboles que corrigen los errores de los anteriores y llega a 448 mil. La red neuronal y el bosque de aislamiento quedan muy atrás; el ensamble empata con XGBoost sin mejorarlo. El criterio se fijó antes de comparar: gana el flexible con más dólares, siempre que supere a la logística en cada bloque. XGBoost lo cumple.

## 9 · Las tres hipótesis fijadas antes de la prueba se cumplen en los dos meses

**Ver.** Ventaja del modelo con intervalos de 95% contra la regla, la logística y el orden por probabilidad, en cada mes de prueba; en naranja, la barra fijada antes.

**Decir.** Quinta fase, la evaluación. Antes de abrir la prueba registramos tres hipótesis con su barra. Contra la mejor regla, al menos 20%: el modelo gana 30% y 63%. Contra la logística, al menos 10%: gana 13% y 22%. Contra el enfoque de la competencia, que ordena solo por probabilidad, cualquier mejora: gana 110% y 75%. Los intervalos salen de un bootstrap que remuestrea días completos, con las mismas réplicas para todas las políticas. Las tres hipótesis se cumplen en los dos meses.

## 10 · Seis métricas de clasificación eligen otra cola; solo el dinero elige el modelo

**Ver.** Exactitud, precisión, recall, F1, ROC-AUC, PR-AUC y dólares de cada cola con el mismo cupo; en tono, la ganadora de cada fila.

**Decir.** Esta lámina es la lección central del curso aplicada al caso. No revisar nada tiene 96.6% de exactitud, más que cualquier cola: es la paradoja de la exactitud con un fraude de cada 28 pagos. Ordenar solo por probabilidad gana en cinco de las seis métricas de clasificación, incluido el AUC. Pero lleva 231 mil dólares a la cola, contra 438 mil del modelo. Esas métricas cuentan aciertos; no pesan el monto. Si la decisión se mide en dinero, la métrica de selección tiene que ser dinero.

## 11 · Revisar 2.1% de los pagos captura 46% del fraude en dólares

**Ver.** Curva de ganancia acumulada: parte del fraude capturado según la parte de los pagos revisados, en dólares y en número.

**Decir.** La curva de ganancia ordena los pagos de cada día por el modelo. Con el cupo de 60, que es 2.1% de los pagos, se captura 46% del fraude en dólares. Revisar al azar capturaría 2.1%: el lift en dólares es de 22 veces. La línea punteada muestra el número de fraudes, que crece más despacio: el modelo prioriza los fraudes caros. Para atrapar los mismos dólares que la mejor regla, al modelo le bastan 55% menos revisiones.

## 12 · Si una revisión cuesta 10 USD, conviene revisar cientos de pagos al día, no 60

**Ver.** Beneficio neto en la prueba según las revisiones por día, para costos de 10, 20 y 50 dólares por revisión; puntos, el cupo elegido en desarrollo.

**Decir.** Sexta fase, el despliegue, empieza por el tamaño del cupo. Si cada revisión tiene un costo, el neto es el fraude detenido menos el costo de revisar. Con 10 dólares por revisión, el desarrollo elige 450 revisiones al día y el neto en la prueba pasa de 401 mil a 513 mil dólares. Con 50 dólares, el mejor cupo es 66, casi el actual. Es decir, el cupo de 60 solo es óptimo si revisar cuesta alrededor de 50 dólares. En los doce escenarios de costo que probamos, el modelo deja más neto que la regla y que la logística.

## 13 · Optimizar sobre la misma validación engaña: +6.1% donde se eligió, −5.3% en días nuevos

**Ver.** Ventaja de las variables nuevas contra el modelo congelado: en las ventanas donde se eligieron, en días apartados y en los dos meses de prueba.

**Decir.** Después de la prueba intentamos mejorar el modelo, como se haría en mantenimiento. Ocho grupos de variables nuevas compitieron con validación cruzada temporal, con selección hacia adelante y una rejilla de hiperparámetros con parada temprana. En las ventanas de búsqueda, dos grupos subieron el resultado 6.1%. En quince días que la búsqueda no vio, la misma mejora bajó 5.3%, con un intervalo entero bajo cero; en la prueba quedó cerca de cero. La ganancia venía de elegir y medir sobre los mismos datos: sobreajuste a la validación. Por eso se queda el modelo congelado, y ningún cambio se adopta sin confirmarlo en días nuevos.

## 14 · Despliegue: la misma cola, otro orden y un piloto

**Ver.** Etapas del despliegue: operación, reentrenamiento, piloto, monitoreo, respaldo y regla para adoptar cambios.

**Decir.** El despliegue no cambia el proceso del equipo: el cupo sigue siendo 60 y cambia qué pagos entran. Cada noche se puntúan los pagos del día y los 60 con mayor fraude esperado pasan a la cola. Cada semana se reentrena con los pagos que ya tienen etiqueta. El primer mes es un piloto: los días se asignan al azar a la cola actual o a la del modelo, para medir el efectivo recuperado, que los datos no traen. Se vigilan los dólares por revisión y la mezcla de productos; si el modelo queda dos semanas por debajo de la regla, se regresa a la regla.

## 15 · Ordenar la cola de revisión por fraude esperado

**Ver.** Tres recomendaciones y los límites del análisis.

**Decir.** Recomendamos tres cosas. Primero, ordenar la cola con el modelo y el cupo actual: con las mismas revisiones, 137 mil dólares más de fraude detenido en dos meses, 45% más que la mejor regla. Segundo, un mes de piloto con días al azar para medir el efectivo recuperado contra la cola actual. Tercero, fijar el cupo con el costo real de revisar: si cuesta 10 dólares, conviene revisar cientos de pagos al día. Los límites: medimos exposición, no efectivo; la etiqueta de Vesta se propaga a toda la cuenta; y los datos son de 2017 y 2018. Gracias.

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

**Decir.** Tres ventanas de quince días eligen variables; los días 106 a 120 confirman; la prueba se lee una sola vez. Es el diseño detrás de la lámina 13.
