# Guion: Qué pagos revisar

Veintiséis láminas para 14 a 15 minutos y veintidós de apéndice para preguntas. Cada bloque indica qué se ve y qué se dice.

## 1 · Qué pagos revisar

**Ver.** Portada: los pagos de un día en orden de llegada; en azul, los 60 que selecciona el modelo; en naranja, los fraudes no revisados.

**Decir.** La imagen muestra un día de pagos con tarjeta en línea: 2,931 pagos, cada uno con un tamaño proporcional a su monto. El equipo de riesgo puede revisar 60 al día. En azul están los que selecciona el modelo y en naranja los fraudes que no se revisaron. La pregunta del proyecto es qué 60 pagos conviene revisar cada día para detener la mayor cantidad posible de fraude en dólares.

## 2 · El modelo lleva a revisión 137 mil USD más de fraude

**Ver.** Marcas de 5 mil USD para la mejor regla y el modelo en cada mes de prueba.

**Decir.** Cada marca equivale a 5 mil dólares de fraude dentro de la cola. En el primer mes de prueba, la mejor regla captura 163 mil dólares y el modelo 211 mil, 30% más. En el segundo, 139 mil contra 227 mil, 63% más. En total son 137 mil dólares adicionales con el mismo número de revisiones, y las tres hipótesis fijadas antes de la prueba se cumplen en ambos meses.

## 3 · Qué 60 pagos revisar cada día

**Ver.** Un día de prueba: cada pago según su probabilidad estimada y su monto; los 60 revisados quedan sobre la diagonal.

**Decir.** Al cierre de cada día, el equipo de riesgo tiene alrededor de 3 mil pagos autorizados y puede enviar 60 a revisión manual, menos del 2%. Un fraude revisado se detiene antes del contracargo; uno no revisado se pierde completo. En la gráfica, el eje horizontal es la probabilidad de fraude y el vertical el monto. Se revisan los 60 pagos con mayor fraude esperado, probabilidad por monto, y por eso la frontera es una diagonal. El umbral no se fija de antemano: lo determina el cupo.

## 4 · Matriz de confusión en dólares

**Ver.** Matriz de confusión del segundo mes de prueba, en dólares, de la mejor regla al modelo.

**Decir.** Con un cupo fijo, la matriz de confusión puede leerse en dólares. El fraude dentro de la cola pasa de 139 mil a 227 mil dólares, y el fraude no revisado baja de 339 mil a 251 mil. Como el número de revisiones es el mismo, cada revisión asignada a un pago legítimo o a un fraude pequeño deja fuera un fraude más grande. Por eso la métrica del proyecto es una sola celda: dólares de fraude dentro de la cola.

## 5 · Los dos últimos meses se reservan para la prueba

**Ver.** Fraude diario en dólares, días 1 a 182, según su uso: entrenamiento, desarrollo y prueba.

**Decir.** Los datos son los de la competencia IEEE-CIS de Vesta: 590 mil pagos en seis meses, de una copia pública verificada, en orden temporal. Los primeros 60 días solo entrenan; los días 61 a 120 son el desarrollo, donde se tomaron todas las decisiones; los dos últimos meses son la prueba, evaluada una sola vez con el protocolo congelado. Entre entrenamiento y evaluación hay 30 días de margen por el retraso de la etiqueta.

## 6 · El fraude se concentra en los montos altos

**Ver.** Parte de los dólares de fraude por decil de monto y, debajo, la tasa de fraude de cada decil.

**Decir.** Solo 3.5% de los pagos es fraude, y la mediana del monto es parecida en ambas clases: 76 dólares en fraudes y 69 en legítimos. Sin embargo, el 10% de pagos de mayor monto concentra 53% del fraude en dólares. Ordenar solo por probabilidad llenaría la cola de fraudes pequeños; por eso todas las políticas ordenan por probabilidad por monto.

## 7 · Preparación de datos sin información futura

**Ver.** El historial de un cliente visto desde el pago de hoy y, a la derecha, las cinco medidas que se calculan con él.

**Decir.** Los pagos se ordenan por segundo y se definen cinco llaves: cuatro de tarjeta y una de cliente. Para cada llave se calculan cinco medidas: pagos previos, pagos del último día y de la última semana, tiempo desde el pago anterior y desviación del monto respecto de su promedio. En el ejemplo llega un pago de 120 dólares de un cliente que pagó hace 43 minutos y suele gastar 35, una razón de 3.4. Todas las medidas usan solo segundos anteriores y ninguna etiqueta, y cada transformación se ajusta solo con el entrenamiento de su bloque.

## 8 · Reconstrucción del identificador de cliente

**Ver.** Tasa de fraude según el tiempo desde el pago anterior del mismo cliente.

**Decir.** Vesta anonimizó los datos, pero la columna D1 registra los días desde el alta de la tarjeta. Al restarla del día del pago se obtiene una fecha de alta fija. Tarjeta, dirección y fecha de alta identifican unos 165 mil clientes, en lugar de 12 mil tarjetas. Si el mismo cliente pagó hace menos de una hora, 6.8% de los pagos es fraude; si pagó hace más de una semana, 1.2%.

## 9 · El historial del cliente agrega 21 mil USD en desarrollo

**Ver.** Dólares en desarrollo de XGBoost al agregar conjuntos de variables; los rombos verdes corresponden a la logística.

**Decir.** Con el mismo XGBoost se mide el aporte de cada conjunto de variables. El historial por tarjeta agrega poco; el del cliente agrega 21 mil dólares en desarrollo. Las columnas opacas de Vesta agregarían 71 mil más, pero no se sabe en qué momento se calculan, y una variable que podría contener información futura no es defendible en producción. Se excluyeron antes de la prueba y la decisión quedó registrada en el protocolo.

## 10 · En desarrollo, el mejor modelo es XGBoost con F3

**Ver.** Dólares de fraude en la cola por política, días 61 a 120.

**Decir.** En desarrollo compitieron seis reglas de tasa histórica por monto, que representan la práctica actual, una logística regularizada con la misma información y siete modelos flexibles, todos con hiperparámetros fijos. El criterio se fijó antes: el modelo flexible con más dólares, siempre que superara a la logística en cada bloque. El elegido fue XGBoost con F3. En el segundo bloque superó a la logística por solo 3.9%, y eso se registró como riesgo, porque la hipótesis 2 pedía 10%.

## 11 · La prueba confirma el orden del desarrollo

**Ver.** Dólares de fraude por política en los dos meses de prueba; la barra gris es lo que capturaría un oráculo.

**Decir.** Con todo congelado, la prueba se corrió una vez. El orden se mantiene en ambos meses: primero el modelo, después la logística y luego la mejor regla; ordenar solo por probabilidad o solo por monto queda muy por debajo. Un oráculo que conociera las etiquetas capturaría unos 435 mil dólares al mes con el mismo cupo. El modelo alcanza 49 y 52% de ese máximo; la regla, 38 y 32%.

## 12 · Las tres hipótesis se cumplen en los dos meses

**Ver.** Ventaja del modelo contra cada comparador con intervalos de 95%, un punto por mes; las líneas naranjas son las barras fijadas antes.

**Decir.** Cada intervalo proviene de mil réplicas bootstrap que remuestrean días, las mismas para todas las políticas. Contra la regla, la barra era 20% y el modelo obtiene 30 y 63%, con intervalos por encima de cero. Contra la logística, la barra era 10% y obtiene 13 y 22%, también con límite inferior positivo; es la comparación más exigente porque usa la misma información. Contra ordenar solo por probabilidad, la ventaja es de 110 y 75%. El ensamble queda empatado, así que su complejidad no se justifica.

## 13 · Seis métricas de clasificación prefieren otra cola

**Ver.** Tabla de la prueba con 60 revisiones por día: exactitud, precisión, recall, F1, ROC-AUC, PR-AUC y dólares de cinco colas; el tono marca la mejor de cada fila.

**Decir.** Esta tabla aplica las métricas del capítulo 4 del curso. No revisar ningún pago da 96.6% de exactitud, más que cualquier cola, porque solo 3.4% de los pagos es fraude. Las otras cinco métricas favorecen ordenar solo por probabilidad, que lleva 231 mil dólares a la cola; el modelo lleva 438 mil. Estas métricas cuentan aciertos sin ponderar el monto, mientras que la decisión se mide en dólares.

## 14 · Precisión–recall muestra mejor el punto de operación

**Ver.** Curvas ROC y precisión–recall del modelo, de solo probabilidad y de la regla, con el punto de la cola de 60 por día.

**Decir.** Con clases desbalanceadas, la curva ROC da una impresión demasiado favorable. El punto de operación del modelo revisa solo 1.5% de los pagos legítimos y aparece junto al eje vertical. En la curva precisión–recall, el mismo punto muestra que 70% de las revisiones van a pagos legítimos, y la referencia del azar es la tasa de fraude, 3.4%. Ninguna de las dos áreas considera el monto: ordenar solo por probabilidad tiene mejores áreas y lleva 47% menos dinero a la cola.

## 15 · Revisar 2% de los pagos captura 46% del fraude en USD

**Ver.** Ganancia acumulada: parte del fraude capturado al revisar más pagos de cada día, en dólares y en número, frente a la diagonal del azar.

**Decir.** Una revisión al azar seguiría la diagonal. Con el cupo, 2% de los pagos, el modelo captura 46% del fraude en dólares, un lift de 22. El primer decil de cada día reúne 77% del dinero y 48% de los fraudes; la curva en dólares queda por encima de la de conteo porque el orden prioriza montos. Para igualar los dólares de la regla, el modelo necesita 55% menos revisiones.

## 16 · El beneficio neto es máximo cerca del costo

**Ver.** Beneficio neto en la prueba según el umbral de fraude esperado, para costos de 10, 20 y 50 dólares por revisión, con el umbral equivalente a 60 por día.

**Decir.** El curso indica actuar cuando la probabilidad supera el costo dividido entre el valor en riesgo. Aquí el valor en riesgo es el monto, así que se revisa si probabilidad por monto supera el costo; por eso la cola se ordena por fraude esperado. Con un umbral bajo se revisa todo y domina el costo; con uno alto casi no se revisa. Los máximos están en 9, 17 y 33 dólares, un poco por debajo de cada costo. Revisar 60 pagos al día equivale a un umbral de 36 dólares.

## 17 · Con cualquier costo, el modelo deja más neto

**Ver.** Neto del modelo en la prueba para seis costos por revisión y dos supuestos de recuperación, con su cupo y el neto de la logística y la regla.

**Decir.** Para cada costo, y suponiendo que se recupera todo o la mitad del fraude revisado, cada política elige su cupo en desarrollo y el neto se mide en la prueba: lo recuperado menos el costo de revisar. El cupo varía de más de mil a 14 revisiones diarias, y el modelo deja más neto que la regla y que la logística en los 12 escenarios. Con 100 dólares por revisión la regla deja de revisar, y el modelo todavía obtiene 128 mil.

## 18 · Las probabilidades subestiman un poco el fraude

**Ver.** Diagrama de calibración de la prueba: probabilidad estimada contra tasa de fraude observada, para el modelo y la logística.

**Decir.** La regla del umbral supone probabilidades calibradas. Sobre la diagonal, lo estimado coincide con lo observado. El modelo queda cerca, aunque subestima entre 2 y 20%, y por eso los máximos de la curva anterior quedan un poco por debajo del costo. La logística sobreestima en el tramo alto: estima 32% y se observa 19%. El error de Brier del modelo es 18% menor que el de asignar la tasa media; el de la logística, 7%.

## 19 · La ventaja se mantiene en todos los escenarios

**Ver.** Ventaja del modelo en cada escenario de robustez, contra la regla y la logística, en los dos meses.

**Decir.** Como el fraude en dólares depende de pocos pagos grandes, la comparación se repitió sin ellos. Sin pagos sobre el percentil 99, con el monto topado, con la mitad o el doble del cupo y en los días 121 a 144, que ningún estudio previo había revisado, la ventaja contra la regla nunca baja de 20%, y el modelo gana 26 y 28 de 31 días. Contra la logística el margen es menor: el peor caso es 8.8%, sin los pagos más caros en el primer mes.

## 20 · Origen de la diferencia en dólares

**Ver.** Fraude de cada mes dividido en lo que revisan ambas políticas, solo el modelo, solo la regla o ninguna.

**Decir.** Cada dólar de fraude del mes cae en una sola categoría, y las categorías suman el fraude total. Unos 120 mil dólares al mes los revisan ambas. En las cerca de 1,200 revisiones mensuales en que difieren, el modelo encuentra 436 y 355 fraudes, y la regla 49 y 34. La regla prioriza pagos muy grandes en segmentos riesgosos, con baja precisión; el modelo encuentra fraudes medianos de clientes con historial sospechoso. Más de 220 mil dólares al mes no los revisa ninguna.

## 21 · Cantidades observadas y supuestos

**Ver.** Tabla de cantidades observadas y supuestas, con su efecto sobre el resultado.

**Decir.** El monto y la etiqueta son observados, pero la etiqueta sigue la regla de Vesta: un contracargo se propaga a los demás pagos de la misma cuenta. Como 77% de los fraudes está en clientes con dos o más, parte del acierto proviene de reconocer cuentas ya marcadas. Hay tres supuestos: que revisar un fraude evita su monto completo, lo que mide exposición y no efectivo recuperado; el margen de 30 días; y que la mejor regla representa la práctica actual. Afectan igual a todas las políticas, así que la comparación es válida.

## 22 · Validación cruzada temporal para mejorar las variables

**Ver.** Diseño de validación: tres ventanas internas con origen móvil, un bloque de confirmación y la prueba, cada uno con 30 días de margen.

**Decir.** Después de la prueba revisamos si mejores variables agregan dinero, con un diseño registrado antes de correr. Se probaron ocho grupos nuevos, todos calculados con pagos anteriores. La búsqueda usa tres ventanas de 15 días con origen móvil; los días 106 a 120 quedan apartados para confirmar, y la prueba se lee una sola vez al final. Cada bloque deja 30 días de margen con su entrenamiento.

## 23 · Tres grupos nuevos suben 6.1% en validación

**Ver.** Selección hacia adelante: dólares en las tres ventanas internas en cada ronda; en gris, cada grupo probado; en naranja, la barra de 1%.

**Decir.** En cada ronda se prueba cada grupo restante y se acepta el mejor solo si sube el total al menos 1% y mejora en dos de las tres ventanas. Entran perfil del monto (+2.5%), novedad y diversidad (+1.9%), y cliente fino (+1.6%). En la ronda 4 ningún grupo cumple y la búsqueda se detiene. La rejilla de hiperparámetros no supera la barra y se mantienen los del protocolo. En las ventanas internas, el dinero pasa de 296 a 314 mil dólares, +6.1%; son las mismas ventanas que eligieron los grupos.

## 24 · En días no usados, la ganancia no se repite

**Ver.** Ventaja de las variables nuevas con intervalos de 95% en los días de confirmación y en los dos meses de prueba.

**Decir.** En los días 106 a 120, que la búsqueda no usó, el modelo con variables nuevas lleva 5.3% menos dinero que F3; el intervalo va de −9.6% a −1.1% y gana solo 6 de 15 días. La ganancia interna venía de elegir y medir con las mismas ventanas; para detectar eso existe el bloque de confirmación. En la prueba, leída después, la diferencia es de +1.5% y 0.0%. En la logística, las mismas variables suman +1.0% en la confirmación y +5.1% y +2.2% en la prueba. El historial de contracargos daría 12.2% más que las variables nuevas, pero aprende cómo Vesta propaga la etiqueta a la cuenta, así que no se usa. F3 se mantiene y el veredicto del protocolo no cambia.

## 25 · Despliegue y monitoreo

**Ver.** Tabla del despliegue: operación, reentrenamiento, piloto, monitoreo y respaldo.

**Decir.** Cada noche se puntúan los pagos del día y los 60 con mayor fraude esperado pasan a la cola; la decisión final sigue siendo del equipo. Cada semana se reentrena con los pagos que ya tienen etiqueta. El primer mes sería un piloto que asigna días al azar a la cola actual o a la del modelo, para medir el efectivo recuperado. Se vigilan los dólares por revisión y la composición de la cola; si durante dos semanas el modelo queda por debajo de la regla, se vuelve a la tabla por segmento.

## 26 · Recomendación: ordenar la cola con el modelo

**Ver.** Cierre: dólares de fraude en la cola en los dos meses de prueba para la regla, la logística y el modelo.

**Decir.** La recomendación es ordenar la cola con el modelo. En los dos meses de prueba, con las mismas revisiones, la mejor regla captura 301 mil dólares, la logística 372 mil y el modelo 438 mil. Las tres hipótesis fijadas antes se cumplen en ambos meses, y la ventaja se mantiene en todos los costos por revisión evaluados. Quedan dos preguntas abiertas: cuánto efectivo se recupera y cómo se compara con la práctica actual de Vesta. Un piloto con asignación aleatoria de días permite responder ambas. Gracias.

## 27 · Veredicto del protocolo congelado

**Ver.** Apéndice: las tres hipótesis con su resultado, ventaja e intervalo en cada mes.

**Decir.** Estas son las tres hipótesis como se escribieron en el protocolo, con la ventaja y el intervalo de cada mes. Las seis celdas superan su barra y tienen límite inferior positivo.

## 28 · El modelo supera a la regla en 54 de 62 días

**Ver.** Apéndice: diferencia diaria en dólares entre el modelo y la regla en los 62 días de prueba.

**Decir.** Si la ventaja dependiera de unos pocos días con fraudes grandes, se vería aquí. El modelo supera a la regla en 54 de 62 días, y en los días que pierde la diferencia es menor que en los que gana.

## 29 · Importancia por permutación

**Ver.** Apéndice: dólares que pierde la cola al permutar cada grupo de variables.

**Decir.** Al permutar el monto se pierden 75 mil dólares; le siguen las coincidencias M, el dispositivo y el historial del cliente, con unos 35 mil cada uno. El historial de la tarjeta aporta cerca de cero porque el del cliente ya contiene esa información.

## 30 · Árbol de profundidad 3 como conjunto de reglas

**Ver.** Apéndice: hojas de un árbol de profundidad 3, ordenadas por dólares de fraude por pago.

**Decir.** Un árbol de profundidad 3 ofrece reglas legibles. Es fácil de interpretar, pero lleva 160 mil dólares a la cola, contra 264 mil del modelo en el mismo bloque.

## 31 · Controles

**Ver.** Apéndice: controles en el segundo bloque de desarrollo: azar, etiquetas permutadas, monto, RFM y atípicos.

**Decir.** Con las etiquetas permutadas el modelo cae a 117 mil dólares, por debajo de ordenar por monto, lo que descarta una fuga de información. El bosque de aislamiento queda abajo: la rareza por sí sola no identifica fraude.

## 32 · Calidad de los datos

**Ver.** Apéndice: hallazgos de calidad de los datos y su tratamiento.

**Decir.** Los faltantes son frecuentes en dispositivo e identidad; se conservan con indicadores porque el faltante también es informativo. El punto más delicado es que la etiqueta se propaga a la cuenta, y se declara como advertencia.

## 33 · 93 variables en cinco grupos

**Ver.** Apéndice: catálogo de variables por grupo, cantidad y tratamiento en la matriz de diseño.

**Decir.** El catálogo incluye 56 numéricas con cuantiles e indicadores de faltante y 37 categóricas con one-hot y una categoría para valores infrecuentes; las 367 columnas opacas quedan fuera por diseño. El desbalance no se repondera para no distorsionar la probabilidad; ponderar por monto se evaluó y dio menos dólares.

## 34 · Seis controles contra la fuga de información

**Ver.** Apéndice: cada riesgo de fuga de información, su control y cómo se verifica.

**Decir.** Los seis controles van del margen de 30 días a la prueba congelada. El más fino es el del historial: los pagos del mismo segundo no se ven entre sí.

## 35 · Ocho grupos candidatos, todos con pagos anteriores

**Ver.** Apéndice: cada grupo candidato, qué mide, cuántas variables tiene y su resultado en la búsqueda.

**Decir.** Todos los grupos se calculan con pagos en segundos estrictamente anteriores, y las frecuencias se ajustan con el entrenamiento de cada bloque. Se aceptan tres: perfil del monto, novedad y diversidad, y cliente fino. El historial de contracargos usa etiquetas con 30 días o más de antigüedad; en las ventanas internas suma +5.8% y se reporta aparte.

## 36 · Cada ronda prueba todos los grupos restantes

**Ver.** Apéndice: ganancia de cada grupo sobre el paso anterior en cada ronda, con el número de ventanas en que mejora.

**Decir.** Cada celda muestra la ganancia en las tres ventanas sumadas y en cuántas sube; el recuadro marca el grupo aceptado. La pasada hacia atrás no quita ningún grupo: quitar cualquiera baja el total.

## 37 · El ajuste de hiperparámetros no supera la barra

**Ver.** Apéndice: profundidad, peso mínimo por hoja, árboles elegidos por parada temprana, dólares, AUC y pérdida logarítmica de cada combinación.

**Decir.** La rejilla prueba cuatro combinaciones; el número de árboles de cada ventana se elige con parada temprana en sus últimos 10 días de entrenamiento. La mejor, profundidad 10 y peso mínimo 10, queda 1.5% abajo de los hiperparámetros del protocolo y sube en 1 de 3 ventanas. La rejilla de hiperparámetros no supera la barra y se mantienen los del protocolo. Las cuatro tienen menor pérdida logarítmica que el protocolo y aun así llevan menos dinero.

## 38 · Parada temprana en 618 árboles

**Ver.** Apéndice: curva de aprendizaje de la ventana 3, con la pérdida logarítmica en entrenamiento y en validación.

**Decir.** Es la curva de aprendizaje del capítulo 7. La pérdida en validación es mínima en 618 árboles; después, la de entrenamiento sigue bajando y la de validación ya no mejora. El protocolo usaba 600 árboles sin parada temprana, casi el mismo número.

## 39 · Frente a F3, los grupos nuevos aportan poco

**Ver.** Apéndice: dólares que pierde la cola al permutar las variables del protocolo y cada grupo nuevo, en los días de confirmación.

**Decir.** Al permutar las variables del protocolo se pierden 119 mil dólares; al permutar perfil del monto, 6 mil; cliente fino, 4 mil; novedad y diversidad, −3 mil. Un valor negativo indica que la cola lleva más dinero sin ese grupo.

## 40 · Regularización de la logística

**Ver.** Apéndice: dólares en desarrollo de la logística para cada valor de C, con su AUC.

**Decir.** La penalización de la logística se eligió por dólares: el máximo está en C igual a 0.003, mientras que el AUC es máximo en 0.01. Con el historial del cliente, la logística mejora en todos los valores de C.

## 41 · Un AUC mayor no garantiza más dólares

**Ver.** Apéndice: AUC contra dólares en la cola para cada política de desarrollo.

**Decir.** El mismo modelo, con el mismo AUC, lleva 264 mil dólares con probabilidad por monto y 101 mil con solo probabilidad. Ordenar por monto, con un AUC inferior al azar, supera a la red neuronal. La métrica de selección debe coincidir con la de la decisión.

## 42 · AUC de 0.87

**Ver.** Apéndice: distribución de la probabilidad estimada para fraudes y pagos legítimos, con sus medianas.

**Decir.** El AUC es la probabilidad de que un fraude elegido al azar tenga mayor puntaje que un pago legítimo elegido al azar: 87 de cada 100 pares. Las medianas son 10% y 0.9%. El AUC no considera montos; multiplicar por el monto lo baja a 0.82 y aumenta 90% el dinero en la cola.

## 43 · A partir del decil 4, la tasa de fraude queda bajo la media

**Ver.** Apéndice: tabla de deciles del modelo con tasa, lift, capturas acumuladas y dólares observados y esperados, más la fila de la cola de 60.

**Decir.** Es la tabla de deciles del curso. La cola de 60 tiene 30% de fraude, un lift de 8.7. A partir del cuarto decil, la tasa queda por debajo del promedio. En los deciles altos, el fraude esperado es menor que el observado, igual que en la calibración.

## 44 · Más fraudes atrapados no implica más dólares

**Ver.** Apéndice: una marca por revisión; cuántas de las 60 diarias son fraude con cada orden y los dólares por revisión, segundo mes.

**Decir.** Con el mismo modelo, ordenar solo por probabilidad encuentra 27 fraudes de cada 60 revisiones y ordenar por probabilidad por monto, 16. Son menos fraudes, pero de 444 dólares en promedio contra 154: 122 dólares por revisión contra 70.

## 45 · Los dólares de la regla con menos revisiones

**Ver.** Apéndice: curvas de ganancia en dólares del segundo mes para el modelo, la logística, la regla y el monto.

**Decir.** En el segundo mes, el modelo iguala los dólares de la regla revisando 0.75% de los pagos, 64% menos revisiones. En el cupo, una revisión del modelo vale 23 veces una revisión al azar; una de la regla, 14.

## 46 · La revisión número 60 aporta 59 USD de fraude

**Ver.** Apéndice: dólares de fraude por revisión en tramos de 20 lugares de la cola diaria, con líneas de costo por revisión.

**Decir.** Es la versión marginal de la curva de beneficio. Las primeras 20 revisiones del modelo aportan 205 dólares cada una y la número 60 todavía aporta 59. Con 10 dólares por revisión, el cupo elegido en desarrollo sería de 450 al día, aunque en la prueba el valor marginal cayó antes; con 50 dólares, 66.

## 47 · CRISP-DM

**Ver.** Apéndice: las seis fases de CRISP-DM con lo que se hizo, las técnicas del curso y sus láminas.

**Decir.** Esta tabla resume las seis fases de CRISP-DM y dónde aparece cada técnica del curso.

## 48 · Mapa de requisitos

**Ver.** Apéndice: cada requisito del proyecto, cómo se cumple y en qué lámina.

**Decir.** Este es el mapa de requisitos, con la lámina donde se cumple cada uno.
