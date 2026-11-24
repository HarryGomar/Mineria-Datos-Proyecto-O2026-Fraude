# Criterio de selección del torneo de desarrollo

Escrito el 23 de noviembre de 2026, antes de correr `scripts/02_desarrollo.py`.

## Qué se compara

- **Decisión.** Al cierre de cada día relativo, el equipo de riesgo revisa K = 60 pagos ya
  autorizados (cerca de 2% de los pagos del día).
- **Dinero.** USD (`TransactionAmt`) de los pagos etiquetados como fraude que entran a la cola.
- **Puntaje.** Los modelos y las reglas ordenan por *probabilidad × monto*. "Mayor monto primero"
  ordena solo por monto.
- **Bloques de desarrollo.** Días 61–90 (D1) y 91–120 (D2). Cada bloque entrena con los pagos de
  días anteriores a su inicio menos 30 (madurez de la etiqueta). Los días 121 a 182 no se leen.

## Conjuntos de variables

| Conjunto | Contenido | Elegible como modelo final |
|---|---|---|
| F1 · descriptivas | Monto, centavos, hora, día de la semana, producto, tarjeta, dirección, distancia, correo, dispositivo, `M1–M9`, `id_*` | No (punto de partida de la ablación) |
| F2 · + historial | F1 más recencia, frecuencia y desvío del monto en pagos estrictamente anteriores, por cuatro claves de tarjeta | Sí |
| F3 · + cliente | F2 más la antigüedad de la tarjeta (`D1`) y el mismo historial por cliente reconstruido: tarjeta + dirección + día de alta (día − `D1`) | Sí |
| F4 · + columnas de Vesta | F3 más `C1–C14`, `D2–D15` y `V1–V339` | No: diagnóstico. La descripción pública no certifica cuándo se calculan |

## Políticas

- **Reglas, sin aprendizaje supervisado más allá de una tasa histórica:**
  - mayor monto primero;
  - tasa de fraude suavizada × monto por tarjeta (`card1`);
  - por segmento (producto × red × tipo de tarjeta × dispositivo);
  - por dominio de correo × producto;
  - tabla producto × decil de monto;
  - velocidad de la tarjeta (producto × pagos previos × pagos del último día).
- **Lineal:** logística L2 con C ∈ {0.001, 0.003, 0.01, 0.03, 0.1}, sobre F2 y F3.
- **Flexibles, sobre F2 y F3:**
  - árbol CART de profundidad 3;
  - bosque aleatorio;
  - XGBoost;
  - XGBoost ponderado por monto;
  - red MLP;
  - ensamble XGBoost + bosque.
- **Ablación:** XGBoost sobre F1 y F4.
- **Otros:** bosque de aislamiento como política no supervisada. Oráculo como techo.

Los hiperparámetros están escritos en `src/revisar/politicas.py` antes del torneo. No hay ajuste fino.

## Reglas de selección

1. **Modelo final.** La combinación (modelo flexible, conjunto F2 o F3) con más dólares totales en
   D1 + D2, con K = 60.
2. **Desempate a favor de lo simple.** Si gana el ensamble por menos de 1% sobre el mejor modelo
   único, se elige el modelo único.
3. **Condición sobre la lineal.** El elegido debe superar a la mejor logística en los dos bloques.
   Si no, el modelo final es la mejor logística y se declara que el aprendizaje flexible no aporta.
4. **Mejor regla.** La regla con más dólares totales en D1 + D2. Hace el papel de práctica actual:
   Vesta no publica la suya.
5. **Mejor logística.** El valor de C y el conjunto con más dólares totales en D1 + D2.
6. **Comparador publicado.** El enfoque de la competencia de Kaggle, que premió el AUC: el mismo
   modelo final, ordenado solo por probabilidad.
7. **Prueba.** Las hipótesis, sus umbrales y el código se congelan con huellas SHA-256 en
   `docs/protocolo.md` antes de leer los días 121 a 182.

## Aviso sobre los días de prueba

Un estudio anterior de este repositorio (`../docs/fraude-avanzado.md`) usó estos datos con otra
decisión: turnos de cuatro horas y un margen de 120 días. Usó los días 145–160 para elegir y los
161–182 para comparar XGBoost contra un LambdaRank. Ninguna elección de este proyecto usa esos días.
Aun así, no son días que nadie haya visto. Por eso la prueba reporta aparte los días 121–144, que
ningún estudio leyó.
