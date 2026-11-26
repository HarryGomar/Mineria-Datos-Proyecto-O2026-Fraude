# Guion: Qué pagos revisar

Diecisiete láminas para 12 a 14 minutos, menos de un minuto cada una, y dieciocho de apéndice para preguntas. Cada
lámina dice arriba del título en qué fase de CRISP-DM está. Cada bloque indica qué se ve y qué se dice.

## 1 · Qué pagos revisar

**Ver.** Portada: los pagos de un día; en azul, los 60 que el modelo manda a revisión; en naranja, los fraudes que pasan.

**Decir.** Cada cuadro es un pago de un solo día, del tamaño de su monto. El equipo de riesgo puede revisar a mano 60 al día, alrededor de 2% de los pagos. Un fraude revisado se detiene antes del contracargo; uno que pasa se pierde completo. La pregunta del proyecto es una sola: qué 60 pagos revisar cada día para detener la mayor cantidad posible de fraude en dólares.

## 2 · Con las mismas 60 revisiones al día, el modelo detiene 45% más fraude

**Ver.** Fraude detenido en los dos meses de prueba por la práctica actual, la logística y el modelo.

**Decir.** Este es el resultado. En dos meses que apartamos hasta el final, la mejor regla, que representa la práctica actual, detiene 301 mil dólares de fraude. Una logística con la misma información, 372 mil. El modelo, 438 mil: 137 mil dólares más que la regla, 45% más, con exactamente las mismas revisiones. No hace falta más personal; solo cambia el orden de la cola. Y gana en cada mes por separado, y en 54 de los 62 días. El resto de la charla explica cómo llegamos aquí y por qué el resultado es creíble.

## 3 · Cada noche se revisan 60 de unos 3,200 pagos; el fraude que no se revisa se pierde completo

**Ver.** A la izquierda, el árbol de la decisión: cada pago se revisa o se deja pasar, con lo que cuesta cada resultado. A la derecha, lo que cuesta el fraude: el total de un día típico y el monto de cada fraude.

**Decir.** Primera fase de CRISP-DM: entender el negocio. Cada noche llegan unos 3,200 pagos y el equipo de riesgo del procesador puede revisar 60, alrededor de 2%. Para cada pago hay dos opciones. Si se revisa y era fraude, se detiene; el costo es la revisión. Si se deja pasar y era legítimo, no pasa nada; si era fraude, llega el contracargo y se pierde el monto completo. Es la matriz de confusión del curso, en dólares. Lo que está en juego: en un día típico de los primeros cuatro meses hay unos 118 fraudes que suman 17 mil dólares. Un fraude va de 29 centavos a 4,191 dólares; la mediana es 76 y el promedio 146, porque unos pocos fraudes caros pesan mucho. Hoy se decide con una regla fija; como Vesta no la publica, la representamos con la mejor de seis reglas de tasa histórica por monto. El éxito se mide en dólares de fraude detenidos con las mismas 60 revisiones.

## 4 · Se revisan los 60 pagos con mayor fraude esperado: probabilidad de fraude × monto

**Ver.** Los pagos del día 166 por probabilidad estimada y monto, en escala logarítmica; la línea marca 44 USD de fraude esperado y hay dos fraudes reales señalados.

**Decir.** Revisar conviene cuando la probabilidad por el monto supera el costo de revisar: es la regla del curso, p mayor o igual a C entre LTV, con el monto como valor en riesgo. Con un cupo fijo, se revisan los 60 pagos con mayor probabilidad por monto. Cada punto es un pago de un día, y los 60 revisados quedan arriba de la línea. Dos fraudes reales: uno de 554 dólares con 10% de probabilidad vale 56 dólares esperados y se revisa. Otro de 30 dólares con 80% es mucho más sospechoso, pero vale 24 y pasa. Un pago caro entra a la cola con menos probabilidad que uno barato.

## 5 · Ninguna variable separa sola el fraude: el modelo tiene que combinarlas

**Ver.** Matriz de dispersión de cinco variables con una muestra al azar de 300 fraudes y 300 legítimos de los días 1 a 120; en la diagonal, la distribución de cada clase completa. A la derecha, tres hallazgos.

**Decir.** Segunda fase, los datos: 590 mil pagos de 182 días de la competencia IEEE-CIS de Vesta, de una copia pública con huella verificada. Solo 3.5% es fraude. Antes de modelar miramos cómo se reparten fraude y legítimo. Cada panel cruza dos variables: monto, hora, días desde el alta de la cuenta, tiempo desde el pago anterior del mismo cliente y número de pagos anteriores. Hay señales: con un día o menos desde el alta, 12% de los pagos es fraude; según la hora, la tasa va de 2% a 10%. Pero en cada par de variables las nubes se enciman, y el monto solo casi no distingue: la mediana es 76 dólares en fraude y 69 en legítimos. Ningún corte simple separa las clases; por eso hace falta un modelo que combine muchas variables. Este análisis usa solo los días 1 a 120, antes de la prueba.

## 6 · El fraude se concentra en el producto C, las tarjetas de crédito y los pagos desde celular

**Ver.** Cuatro variables categóricas: qué parte de los fraudes y qué parte de los legítimos cae en cada categoría; arriba de cada panel, la categoría con la tasa de fraude más alta.

**Decir.** Las variables categóricas muestran dónde se concentra el fraude. El producto C tiene 39% de los fraudes y solo 11% de los legítimos: 11% de sus pagos son fraude. Las tarjetas de crédito llevan la mitad de los fraudes y una cuarta parte de los legítimos. Los pagos desde celular, 28% de los fraudes y 9% de los legítimos. En el correo, hotmail tiene la tasa más alta, 5.4%, pero la diferencia es menor. Son señales útiles, pero ninguna basta sola: revisar todo el producto C serían cientos de pagos al día. El modelo las combina con el monto y el historial del cliente.

## 7 · El 10% de los pagos más caros concentra 53% del fraude en dólares

**Ver.** Parte de los dólares de fraude por decil de monto y, debajo, la tasa de fraude de cada decil.

**Decir.** Lo que más importa para el negocio: la tasa de fraude es parecida en todos los montos, entre 2% y 6%, pero el dinero no se reparte igual. El 10% de los pagos más caros concentra 53% del fraude en dólares. Un modelo que solo cuente fraudes llenaría la cola de fraudes baratos. Por eso el monto entra al orden.

## 8 · Cliente = tarjeta + dirección + fecha de alta; si vuelve a pagar en menos de una hora, el fraude casi se duplica

**Ver.** A la izquierda, seis pagos reales con la misma tarjeta y la misma dirección, separados en dos clientes por su fecha de alta; a la derecha, la tasa de fraude según el tiempo desde el pago anterior del cliente y lo que agrega en dólares.

**Decir.** Tercera fase, la preparación. Los datos están anonimizados y no traen una columna de cliente, así que la construimos. Tarjeta y dirección no bastan: la misma tarjeta con la misma dirección puede ser de dos cuentas. La columna D1 cuenta los días desde el alta de la cuenta; si se resta del día del pago, queda la fecha de alta, que no cambia. En este ejemplo real, seis pagos comparten la tarjeta 16630 y la dirección 205. Al restar D1, tres dan alta el día 18 y tres el día 26: son dos clientes. Los tres pagos del cliente A son fraude y los del B son legítimos. Así, 12 mil números de tarjeta se vuelven 165 mil clientes. Con cada cliente medimos, solo con pagos anteriores y sin etiquetas, cuántos pagos lleva, cuántos en el último día y en la última semana, cuánto pasó desde el anterior y cómo se compara el monto con su promedio. Si el mismo cliente pagó hace menos de una hora, 6.8% de los pagos es fraude, casi el doble del promedio. Con este historial, el mismo modelo detiene 21 mil dólares más en desarrollo.

## 9 · Partición por tiempo: elegimos con los días 61–120 y probamos una sola vez con los días 121–182

**Ver.** Fraude diario en dólares, días 1 a 182, coloreado según su uso: entrenamiento, desarrollo y prueba.

**Decir.** Cuarta fase, el modelado, empieza por el diseño de la prueba. La partición es por tiempo, no al azar, porque en producción siempre se predice el futuro con el pasado. Los días 1 a 60 solo entrenan. En los días 61 a 120 se eligieron el modelo, las variables y los rivales. Los dos últimos meses, días 121 a 182, se congelaron con un protocolo y se evaluaron una sola vez, al final. Entre entrenar y evaluar dejamos 30 días, porque el contracargo tarda en llegar.

## 10 · XGBoost es el que más fraude detiene en desarrollo: 448 mil USD, contra 275 mil de la regla

**Ver.** Dólares en desarrollo de la mejor regla, el árbol, el bosque y XGBoost; línea punteada, la logística; en gris, los demás modelos.

**Decir.** Con las mismas 93 variables y el mismo cupo, comparamos los modelos del curso en los días de desarrollo. La mejor regla detiene 275 mil dólares. Un solo árbol de decisión, 243 mil: queda debajo de la regla, porque un árbol solo es inestable. El bosque aleatorio promedia cientos de árboles y sube a 398 mil, al nivel de la logística. XGBoost entrena los árboles en secuencia, cada uno corrigiendo los errores de los anteriores, y llega a 448 mil: 63% más que la regla. La red neuronal y el bosque de aislamiento quedan atrás, y el ensamble no mejora a XGBoost. XGBoost supera a la logística en los dos bloques de desarrollo; por eso es el modelo que pasa a la prueba.

## 11 · El modelo cumple las dos metas en ambos meses de prueba

**Ver.** Ventaja del modelo en cada mes de prueba contra la regla y contra la logística, con su intervalo de 95% y la meta.

**Decir.** Quinta fase, la evaluación. Antes de evaluar en la prueba fijamos dos metas: detener al menos 20% más que la regla y al menos 10% más que la logística, con el intervalo de 95% por encima de cero. Contra la regla, el modelo gana 30% el primer mes y 63% el segundo. Contra la logística, 13% y 22%. Los intervalos salen de remuestrear días completos mil veces. Las cuatro barras pasan su meta. Una tercera meta, superar al mismo modelo ordenado solo por probabilidad, también se cumple; se ve en la siguiente lámina y en el apéndice.

## 12 · El orden con mejor AUC detiene 47% menos fraude: elegimos el modelo por dólares, no por AUC

**Ver.** ROC-AUC contra fraude detenido en la prueba para cuatro políticas con el mismo cupo; a la derecha, la exactitud de no revisar nada.

**Decir.** Esta es la lección central del curso aplicada al caso. Ordenar solo por probabilidad da el mejor AUC, 0.87, y también gana en precisión, recall y F1. Pero detiene 231 mil dólares, contra 438 mil del modelo: 47% menos. Es el mismo XGBoost; el modelo solo multiplica por el monto. La exactitud es peor todavía: no revisar nada acierta en 96.6% de los pagos, porque casi todos son legítimos. Estas métricas cuentan aciertos, y un fraude de 8 dólares pesa lo mismo que uno de 900. Si la decisión se mide en dinero, la métrica para elegir tiene que ser dinero.

## 13 · Revisando 2% de los pagos, el modelo captura 46% del fraude en dólares; la regla, 32%

**Ver.** Curva de ganancia acumulada en dólares del modelo y de la regla contra el azar, hasta 20% de los pagos revisados.

**Decir.** La curva de ganancia ordena los pagos de cada día y acumula el fraude en dólares. Con el cupo de 60, que es 2% de los pagos, el modelo captura 46% del fraude en dólares y la regla 32%. Revisar al azar capturaría 2%: el lift es de 22 veces. Dicho de otra forma, para detener lo mismo que la regla, al modelo le basta con 45% de las revisiones.

## 14 · Las variables nuevas mejoraban 6.1% en validación pero empeoraban 5.3% en días nuevos: no se adoptan

**Ver.** Cambio en el fraude detenido con las variables nuevas: en los días de validación donde se eligieron y en quince días que la búsqueda no vio.

**Decir.** Después de la prueba intentamos mejorar el modelo, como se haría en mantenimiento. Ocho grupos de variables nuevas compitieron con validación cruzada temporal en tres ventanas, más una rejilla de hiperparámetros. En validación, donde se eligieron, subían el resultado 6.1%. En quince días que la búsqueda no vio, lo bajaron 5.3%, con el intervalo de 95% entero bajo cero; en los dos meses de prueba quedaron en +1.5% y 0%. La ganancia venía de elegir y medir sobre los mismos datos: sobreajuste a la validación. Por eso se queda el modelo original, y ningún cambio se adopta sin confirmarlo en días nuevos.

## 15 · Si una revisión cuesta 10 USD, conviene revisar cientos de pagos al día, no 60

**Ver.** Beneficio neto en la prueba según las revisiones por día, para costos de 10, 20 y 50 dólares; puntos, el cupo elegido en desarrollo.

**Decir.** Sexta fase, el despliegue, empieza por el tamaño del cupo. Si cada revisión cuesta, el neto es el fraude detenido menos el costo de revisar: es la curva de beneficio del curso. Con 10 dólares por revisión, el desarrollo elige 450 revisiones al día y el neto en la prueba sube 112 mil dólares. En la prueba la curva es casi plana entre 200 y 450 revisiones: lo que importa es pasar de decenas a cientos. Con 50 dólares, el mejor cupo es 66, casi el actual: el cupo de 60 solo es óptimo si revisar cuesta alrededor de 50 dólares. En los doce escenarios de costo que probamos, el modelo deja más neto que la regla y que la logística.

## 16 · Cada noche, el modelo entrega al equipo de riesgo la lista de 60 pagos a revisar

**Ver.** Ejemplo de la lista de la noche del día 166: los primeros pagos con su monto, probabilidad, fraude esperado y resultado real, y el fraude detenido esa noche por el modelo y por la regla; a la derecha, el ritmo de operación.

**Decir.** Así funcionaría en operación. Cada noche, el modelo calcula para cada pago del día la probabilidad de fraude por el monto y entrega al equipo los 60 con el valor más alto. El equipo, el cupo y la revisión no cambian: cada caso lo sigue decidiendo una persona. Esta es la lista de la noche del día 166, un día típico del segundo mes. Arriba van pagos caros con probabilidad media: la mayoría resulta legítima, pero es donde un fraude cuesta más. Esa noche, la lista del modelo detuvo 10 fraudes y 4 mil dólares; la de la regla, 2 fraudes y 1,800. Cada semana se reentrena con los pagos de más de 30 días, que ya tienen etiqueta. El primer mes es un piloto: en días elegidos al azar se usa la lista actual o la del modelo, y se compara lo recuperado. Si dos semanas seguidas el modelo detiene menos que la regla, se vuelve a la regla.

## 17 · Recomendamos adoptar el modelo: 137 mil USD más de fraude detenido en dos meses, con el mismo equipo

**Ver.** Fraude detenido acumulado día a día en los dos meses de prueba: modelo, logística, regla y revisión al azar; a la derecha, los tres pasos.

**Decir.** Recomendamos adoptar el modelo para ordenar la lista de revisión. En los dos meses de prueba acumuló 438 mil dólares de fraude detenido; la logística, 372 mil; la regla, 301 mil; y revisar 60 pagos al azar, unos 20 mil. Son 137 mil dólares más que la regla, y la brecha se abre de forma pareja: el modelo gana en 54 de los 62 días. Tres pasos. Primero, adoptarlo con el cupo actual, desde la próxima noche y sin más personal. Segundo, confirmarlo con un piloto de un mes con días al azar, para medir el efectivo recuperado. Tercero, medir lo que cuesta una revisión: si cuesta 10 dólares, revisar cientos de pagos al día deja 112 mil dólares más de neto. Los límites están en el apéndice: medimos exposición, no efectivo; la etiqueta de Vesta se propaga a la cuenta; y los datos son de 2017 y 2018. Gracias.

## 18 · Las seis fases de CRISP-DM

**Ver.** Apéndice. Cada fase de CRISP-DM con lo que se hizo, las técnicas del curso y sus láminas.

**Decir.** Si preguntan por la metodología: cada fase tiene sus láminas en la charla y en el apéndice, y cada lámina dice su fase arriba del título.

## 19 · Mapa de requisitos

**Ver.** Apéndice. Cada requisito del proyecto con cómo se cumple y en qué lámina.

**Decir.** Si preguntan por un requisito: aquí está dónde se cumple cada uno; el reporte tiene el detalle completo.

## 20 · La prueba confirma el orden del desarrollo

**Ver.** Apéndice. Cada política frente al techo del oráculo en cada mes de prueba.

**Decir.** El orden de desarrollo se repite en la prueba: modelo, logística, regla, solo probabilidad y mayor monto. El modelo captura 49% y 52% del techo; la regla, 38% y 32%.

## 21 · El modelo supera a las reglas y a la logística; con el ensamble empata

**Ver.** Apéndice. Ventaja del modelo con IC 95% contra seis comparadores.

**Decir.** Además de las tres hipótesis, el modelo supera al bosque y empata con el ensamble, que es más complejo. Las columnas opacas de Vesta darían más, pero no se puede saber cuándo se calculan y se excluyeron por diseño.

## 22 · La ventaja se mantiene en todos los escenarios

**Ver.** Apéndice. Ventaja contra la regla y la logística con medio cupo, doble cupo, sin los pagos más caros, con el monto topado y por días.

**Decir.** La ventaja no depende de unos pocos pagos grandes: sin los pagos sobre el percentil 99 sigue en al menos 21% contra la regla y 9% contra la logística, y el modelo gana en 24 a 28 de los 31 días de cada mes.

## 23 · Con cualquier costo por revisión, el modelo deja más neto

**Ver.** Apéndice. Neto del modelo, la logística y la regla con seis costos por revisión y dos tasas de recuperación.

**Decir.** Cada política elige su cupo en desarrollo y se mide en la prueba. En los doce escenarios, el modelo deja más neto; con 100 dólares por revisión, la regla deja de revisar.

## 24 · Cada dólar de fraude cae en una caja: ambos, solo modelo, solo regla o ninguno

**Ver.** Apéndice. Traza del fraude de cada mes: lo que revisan ambas políticas, solo el modelo, solo la regla o ninguna.

**Decir.** Modelo y regla difieren en 1,200 a 1,300 revisiones por mes. El modelo encuentra cientos de fraudes que la regla no ve; la regla encuentra pocas decenas que el modelo no ve, más caros pero muchos menos.

## 25 · Precisión–recall muestra mejor el punto de operación que la ROC

**Ver.** Apéndice. Curvas ROC y precisión–recall con la cola real de 60 por día marcada.

**Decir.** En la ROC la cola queda pegada al eje, con 1.5% de falsos positivos; en precisión–recall se ve que 70% de las revisiones van a legítimos. Las dos curvas ignoran el monto.

## 26 · Las probabilidades subestiman un poco el fraude

**Ver.** Apéndice. Curva de calibración del modelo y de la logística, con el fraude esperado contra el observado en la cola.

**Decir.** El modelo reduce el error de Brier 18% contra la tasa media y la logística 7%. Las probabilidades subestiman un poco, por eso el umbral óptimo de beneficio queda algo por debajo del costo.

## 27 · Qué se observa y qué se supone

**Ver.** Apéndice. Tabla de cantidades observadas y supuestos.

**Decir.** Monto y etiqueta son observados. El dinero salvado por revisión, el retraso de la etiqueta y la práctica actual son supuestos, iguales para todas las políticas.

## 28 · Calidad de los datos: faltantes, fechas relativas y etiqueta propagada

**Ver.** Apéndice. Hallazgos de calidad de datos y su tratamiento.

**Decir.** Hay muchos faltantes informativos, fechas relativas y una etiqueta que Vesta propaga a la cuenta: 62% de los clientes con algún fraude tienen todos sus pagos marcados.

## 29 · 93 variables en cinco grupos

**Ver.** Apéndice. Catálogo de variables y cómo entran a la matriz de diseño.

**Decir.** Monto y reloj, distancias e identidad, categóricas, historial de tarjeta y cliente reconstruido. Las 367 columnas opacas quedan fuera; no se repondera el desbalance para no deformar la probabilidad.

## 30 · Seis controles contra la fuga de información

**Ver.** Apéndice. Riesgos de fuga, control y comprobación.

**Decir.** Con las etiquetas barajadas, el modelo cae a 117 mil dólares, debajo de ordenar por monto: no hay señal que venga de una fuga.

## 31 · El historial del cliente agrega 21 mil USD en desarrollo

**Ver.** Apéndice. Dólares de XGBoost con cada conjunto de variables; rombos, la logística.

**Decir.** Con el mismo XGBoost, el historial del cliente agrega 21 mil dólares. Las columnas opacas agregarían 71 mil, pero no se pueden fechar y se excluyeron antes de la prueba.

## 32 · La penalización con más dólares no coincide con la de mayor AUC

**Ver.** Apéndice. Dólares y AUC de la logística según la penalización L2.

**Decir.** El dinero toca techo en C igual a 0.003 y el AUC en 0.01: elegir por AUC habría dado otra logística.

## 33 · Importancia por permutación: monto y centavos es el grupo principal

**Ver.** Apéndice. Dólares que pierde la cola al permutar cada grupo de variables.

**Decir.** El monto es el grupo más importante; sin el historial del cliente se pierden 35 mil dólares. El historial de la tarjeta aporta casi cero porque el del cliente ya lo contiene.

## 34 · Parada temprana en 618 árboles

**Ver.** Apéndice. Pérdida logarítmica en entrenamiento y validación según el número de árboles.

**Decir.** La validación deja de mejorar cerca de 600 árboles, el mismo número que fijó el protocolo; después, el entrenamiento sigue bajando y eso es sobreajuste.

## 35 · Validación cruzada temporal para buscar variables nuevas

**Ver.** Apéndice. Ventanas de búsqueda, días de confirmación y prueba, con su entrenamiento y margen.

**Decir.** Tres ventanas de quince días eligen variables; los días 106 a 120 confirman; la prueba se lee una sola vez. Es el diseño detrás de la lámina 14.
