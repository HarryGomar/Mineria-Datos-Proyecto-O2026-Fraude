# Anexo: búsqueda de variables con validación temporal

Escrito el 24 de noviembre de 2026, después de la prueba congelada y antes de correr
`scripts/06_variables.py` y `scripts/07_anexo_prueba.py`. Este anexo no cambia el protocolo
(`docs/protocolo.md`) ni su veredicto: el resultado principal del proyecto sigue siendo XGBoost con F3.

## Pregunta

¿Cuánto dinero adicional entra a la cola de 60 revisiones diarias si se mejora la ingeniería de variables
y se ajustan los hiperparámetros con una validación cruzada temporal?

## Variables candidatas

Todas se calculan con la regla del protocolo: cada pago ve solo pagos en segundos estrictamente anteriores, y
lo que depende de la distribución (cuantiles, categorías, frecuencias) se ajusta con el entrenamiento de cada
bloque. El código está en `src/revisar/variables.py`.

| Grupo | Contenido |
|---|---|
| ventanas | Pagos en la última hora y en 6 horas; dólares en 24 horas y en 7 días, por tarjeta y por cliente |
| perfil | Desviación previa del monto, z del monto, razón contra el máximo previo, mismo monto repetido, días desde el primer pago |
| novedad | Correos, dispositivos, navegadores y direcciones distintos ya vistos por cliente y por tarjeta; si el de hoy es nuevo |
| compartido | Tarjetas y clientes distintos ya vistos por dispositivo; tarjetas por dirección + correo |
| texto | Proveedor y país del correo, correo del pagador igual al del receptor, familia y versión del sistema y del navegador, área y razón de la pantalla |
| monto_fino | Número de decimales del monto, monto entero, terminación .95 o .99 |
| frecuencia | Frecuencia en el entrenamiento de tarjeta, `card2`, `card5`, dirección, correo, dispositivo, navegador, pantalla y cliente |
| uid_fino | Cliente fino: tarjeta + dirección + día de alta + correo, con las cinco medidas de historial |
| etiquetas | Historial de contracargos: pagos de la llave con 30 días o más de antigüedad y cuántos fueron fraude. **No compite**: Vesta marca como fraude los pagos posteriores de una cuenta con contracargo, así que este grupo aprende esa regla de etiquetado. Se reporta aparte |

## Validación

- **Ventanas internas con origen móvil:** días 61–75, 76–90 y 91–105. Cada una entrena con los pagos de días
  anteriores a su inicio menos 30.
- **Métrica:** dólares de fraude en la cola de 60 por día, ordenada por probabilidad × monto, sumados en las
  tres ventanas. Se registran también AUC, precisión promedio, pérdida logarítmica y Brier.
- **Selección hacia adelante por grupos, desde F3:** en cada ronda se agrega cada grupo restante; se acepta el
  mejor si sube el total al menos 1% y sube en al menos dos de las tres ventanas. Si ninguno cumple, se detiene.
- **Pasada hacia atrás:** se quita un grupo aceptado si sin él el total no baja.
- **Hiperparámetros:** XGBoost con profundidad y peso mínimo por hoja en {(6, 1), (8, 1), (8, 10), (10, 10)}, tasa
  de aprendizaje 0.05, parada temprana por pérdida logarítmica en los últimos 10 días de cada entrenamiento (150
  rondas de paciencia) y reentrenamiento con todo el entrenamiento. Se adoptan con la misma regla del 1% y dos ventanas.
- **Confirmación:** días 106–120, que la búsqueda no usa. Entrenamiento con los días 1–75. Bootstrap pareado de
  1,000 réplicas que remuestrean días.

## Lectura posterior de la prueba

`scripts/07_anexo_prueba.py` corre una sola vez, justo después de `06`, con lo que `06` haya elegido y sin
importar su resultado. Usa el diseño de la prueba congelada (P1: días 121–151, P2: días 152–182, 30 días de
margen), reproduce primero el modelo congelado y compara sus dólares con `resultados/prueba.json`. Se reporta
como lectura posterior: no es una prueba confirmatoria, porque la prueba ya se había abierto.

## Huellas

`scripts/07_anexo_prueba.py` se niega a correr si alguna no coincide.

| Archivo | SHA-256 |
|---|---|
| `src/revisar/variables.py` | `2d6a5275d2ed12c17f1dc2631547d22c7b2b5d037911ba5fd9589b1ee8343347` |
| `scripts/06_variables.py` | `fda7086c4fa0f8e9a7aeb344d562c4156d2cee7775160e3ae4dd6e3406e2b22a` |
| `scripts/07_anexo_prueba.py` | `7d7b71607bfbda49f2d4b7c2b2abe75080e2c0950d82348487f45a1db3234466` |

## Resultado

Agregado después de correr `06` y `07`. Las cifras están en `resultados/variables.json` y
`resultados/anexo_prueba_variables.json`.

**Búsqueda (días 61–105).** Entran perfil del monto (+2.5%, 2 de 3 ventanas), novedad y diversidad (+1.9%,
2 de 3) y cliente fino (+1.6%, 3 de 3). En la ronda 4 el mejor candidato, ventanas de velocidad, da −2.0% y la
búsqueda se detiene. La pasada hacia atrás no quita ningún grupo. El total interno pasa de 295,998 a 314,111
USD (+6.1%). Ninguna combinación de la rejilla cumple la regla (la mejor, profundidad 10 y peso mínimo 10, queda
−1.5% y sube en 1 de 3), así que se mantienen los hiperparámetros del protocolo. La parada temprana en la
ventana 3 elige 618 árboles; el protocolo usa 600. El historial de contracargos suma +5.8% interno y queda aparte.

**Confirmación (días 106–120).** F3 lleva 167,266 USD y el modelo con variables nuevas 158,444: −5.3%, con
IC 95% de −9.6% a −1.1%; gana a F3 en 6 de 15 días. En la logística, las mismas variables suman +1.0% (IC −3.3%
a +5.3%). El historial de contracargos suma +12.2% (IC +7.1% a +17.9%) sobre las variables nuevas, pero no se usa
porque aprende la regla con que Vesta propaga la etiqueta a la cuenta.

**Lectura posterior de la prueba.** F3, la regla por segmento y la logística reconstruidos reproducen
`resultados/prueba.json` exactamente. Contra F3, las variables nuevas dan +1.5% en P1 (IC −2.4% a +6.2%) y
0.0% en P2 (IC −3.1% a +3.8%); en la logística, +5.1% (IC +0.5% a +10.0%) y +2.2% (IC −1.7% a +7.2%).

**Conclusión.** La ganancia de la búsqueda se midió en las mismas ventanas que eligieron los grupos y no se repite
en días nuevos. F3 se mantiene y el veredicto del protocolo no cambia.
