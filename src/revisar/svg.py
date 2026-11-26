"""Gráficas vectoriales de la presentación, dibujadas con la tipografía y los colores de las láminas."""
from __future__ import annotations

import math
from html import escape

AZUL, VERDE, NARANJA = "#076bb1", "#0d8160", "#bf5128"
NEGRO, GRIS, LINEA = "#0b0d12", "#586172", "#e0e5ec"
HIELO, AZUL_MEDIO, NARANJA_CLARO, GRIS_MEDIO, GRIS_CLARO = "#eef2f6", "#8fb8d8", "#f2c4ad", "#8793a4", "#c9d1db"


def mil(x, signo=False):
    s = f"{abs(x) / 1e3:,.0f}"
    negativo = x < 0 and s != "0"
    return (("−" if negativo else "+") if signo else ("−" if negativo else "")) + s


def pct(x, signo=True, d=0):
    return (("+" if x >= 0 else "−") if signo else ("−" if x < 0 else "")) + f"{abs(x) * 100:.{d}f}%"


def escala(dominio, alcance):
    (a, b), (c, d) = dominio, alcance
    return lambda v: c + (d - c) * (v - a) / (b - a)


def texto(x, y, contenido, clase="label", color=None, ancla="start", peso=None, halo=False):
    """halo=True dibuja un borde blanco detrás de las letras, para leerlas sobre una línea."""
    estilo = ((f"fill:{color};" if color else "") + (f"font-weight:{peso};" if peso else "")
              + ("paint-order:stroke;stroke:#fff;stroke-width:8px;stroke-linejoin:round;" if halo else ""))
    return (f'<text x="{x:.1f}" y="{y:.1f}" class="{clase}" text-anchor="{ancla}"'
            + (f' style="{estilo}"' if estilo else "") + f">{escape(str(contenido))}</text>")


def linea(x, y, x2, y2, color=LINEA, grosor=2, trazos=False):
    g = ' stroke-dasharray="7 8"' if trazos else ""
    return f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{grosor}"{g}/>'


def rect(x, y, ancho, alto, color, opacidad=1.0, borde="none", grosor=0):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(ancho, 0):.1f}" height="{max(alto, 0):.1f}" fill="{color}"'
            f' stroke="{borde}" stroke-width="{grosor}" opacity="{opacidad:.3f}"/>')


def punto(x, y, r, color, borde="#fff", grosor=2, opacidad=1.0):
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" stroke="{borde}" stroke-width="{grosor}"'
            f' opacity="{opacidad:.3f}"/>')


def trazo(puntos, color, grosor=4, relleno="none", cerrar=False, trazos=False):
    pares = " ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)
    g = ' stroke-dasharray="9 9"' if trazos else ""
    return (f'<{"polygon" if cerrar else "polyline"} points="{pares}" stroke="{color}" stroke-width="{grosor}" fill="{relleno}"'
            f' stroke-linejoin="round" stroke-linecap="round"{g}/>')


def svg(ancho, alto, titulo, elementos):
    t = escape(titulo)
    return f'<svg viewBox="0 0 {ancho} {alto}" role="img" aria-label="{t}"><title>{t}</title>' + "".join(elementos) + "</svg>"


def leyenda(x, y, items, paso=None):
    out, px = [], x
    for nombre, color, forma in items:
        if forma == "linea":
            out.append(linea(px, y - 7, px + 26, y - 7, color, 4))
            px2 = px + 36
        elif forma == "trazos":
            out.append(linea(px, y - 7, px + 26, y - 7, color, 4, True))
            px2 = px + 36
        elif forma == "punto":
            out.append(punto(px + 9, y - 7, 9, color))
            px2 = px + 28
        elif forma == "anillo":
            out.append(punto(px + 9, y - 7, 8, "#fff", color, 3))
            px2 = px + 28
        elif forma == "rombo":
            out.append(trazo([(px + 10, y - 18), (px + 21, y - 7), (px + 10, y + 4), (px - 1, y - 7)], "#fff", 2, color, True))
            px2 = px + 30
        else:
            out.append(rect(px, y - 18, 20, 20, color))
            px2 = px + 30
        out.append(texto(px2, y, nombre, "micro"))
        px = px2 + (paso or (len(nombre) * 11.5 + 40))
    return out


# 1 · Portada: los pagos de un día, en orden de llegada
def portada(dia):
    pts = dia["puntos"]
    x0, y0, ancho, alto = 1040, 120, 760, 800
    cols = 56
    filas = math.ceil(len(pts) / cols)
    celda = min(ancho / cols, alto / filas)
    capas = ([], [], [])
    for i, (p, m, f, r) in enumerate(pts):
        lado = min(max(2.6 + 2.3 * math.log10(max(m, 1)), 2.6), celda - 2)
        cx, cy = x0 + (i % cols) * celda + celda / 2, y0 + (i // cols) * celda + celda / 2
        if r:
            capas[2].append(rect(cx - lado / 2, cy - lado / 2, lado, lado, AZUL if f else "#fff", 1, AZUL, 2))
        elif f:
            capas[1].append(rect(cx - lado / 2, cy - lado / 2, lado, lado, NARANJA, .9))
        else:
            capas[0].append(rect(cx - lado / 2, cy - lado / 2, lado, lado, "#a9b5c3", .38))
    return svg(1920, 1080, f"Los {len(pts):,} pagos de un día de la prueba. Azul: los 60 que revisa el modelo. Naranja: fraude que pasa.",
               capas[0] + capas[1] + capas[2])


# 2 · Una marca por cada 5 mil USD de fraude atrapado
def marcas(periodos, unidad=5000):
    paso, w, h = 22, 16, 38
    el = [texto(0, 30, "Fraude atrapado con 60 revisiones por día", "heading"),
          texto(1012, 30, f"Una marca por cada {unidad // 1000} mil USD", "micro", ancla="end")]
    y = 92
    for titulo, filas, dif, rel in periodos:
        el.append(texto(0, y, titulo, "label", GRIS))
        y += 46
        fin = []
        for nombre, usd, color in filas:
            n = round(usd / unidad)
            el += [texto(0, y, nombre, "label-strong", color if color == AZUL else None),
                   texto(1012, y, f"{mil(usd)} mil USD", "data", color if color == AZUL else NEGRO, "end")]
            for i in range(n):
                el.append(rect(i * paso, y + 16, w, h, color))
            fin.append(n * paso - (paso - w))
            y += 104
        a, b = fin[0] + 4, fin[1]
        yb = y - 104 + 16 + h + 12
        el += [linea(a, yb, b, yb, AZUL, 3), linea(a, yb - 9, a, yb, AZUL, 3), linea(b, yb - 9, b, yb, AZUL, 3),
               texto((a + b) / 2, yb + 34, f"{mil(dif, True)} mil · {pct(rel)}", "label-strong", AZUL, "middle")]
        y += 58
    return svg(1040, y - 20, "Dólares de fraude atrapados por la mejor regla y por el modelo en cada mes de prueba.", el)


# 3 · Un día: probabilidad contra monto, y la línea del cupo
def dia_decision(dia):
    X = escala((-4, 0), (130, 1050))
    Y = escala((0, 4), (560, 60))
    lx = lambda p: X(math.log10(min(max(p, 1e-4), 1)))  # noqa: E731
    ly = lambda m: Y(math.log10(min(max(m, 1), 1e4)))  # noqa: E731
    c = dia["corte"]
    el = [texto(130, 26, f"Día {dia['dia']} de la prueba · {dia['pagos']:,} pagos · un punto por pago", "heading")]
    p_lo = c / 1e4
    zona = [(lx(p_lo), ly(1e4)), (lx(1), ly(1e4)), (lx(1), ly(c))]
    el.append(trazo(zona, "none", 0, "#e3f0fa", True))
    for d in range(-4, 1):
        el += [linea(X(d), 60, X(d), 560), texto(X(d), 596, ["0.01%", "0.1%", "1%", "10%", "100%"][d + 4], "axis", ancla="middle")]
    for d in range(0, 5):
        el += [linea(130, Y(d), 1050, Y(d)), texto(116, Y(d) + 7, f"{10 ** d:,}", "axis", ancla="end")]
    pts = dia["puntos"]
    el += [punto(lx(p), ly(m), 3.2, GRIS_MEDIO, "none", 0, .35) for p, m, f, r in pts if not f and not r]
    el += [punto(lx(p), ly(m), 5, NARANJA, "#fff", 1) for p, m, f, r in pts if f and not r]
    el += [punto(lx(p), ly(m), 7, AZUL if f else "#9cc3e0", AZUL if f else "#fff", 2) for p, m, f, r in pts if r]
    el.append(linea(lx(p_lo), ly(1e4), lx(1), ly(c), AZUL, 3, True))
    el.append(texto(lx(p_lo) - 18, ly(1e4) + 34, f"probabilidad × monto = {c:,.0f} USD", "label", AZUL, "end"))
    el.append(texto(lx(p_lo) - 18, ly(1e4) + 64, "arriba de la diagonal: los 60 revisados", "micro", AZUL, "end"))
    el += [texto(590, 640, "Probabilidad de fraude estimada por el modelo", "label", ancla="middle"),
           texto(0, 40, "USD", "axis")]
    el += leyenda(130, 690, [("revisado y fraude", AZUL, "punto"), ("revisado y legítimo", "#9cc3e0", "punto"),
                             ("fraude que pasa", NARANJA, "punto"), ("legítimo", GRIS_CLARO, "punto")], paso=None)
    return svg(1080, 704, "Pagos de un día por probabilidad estimada y monto. Se revisan los 60 con mayor probabilidad por monto.", el)


# 5 · Línea del tiempo: fraude por día y uso de cada tramo
TRAMOS = ("Solo entrenamiento", "Desarrollo: D1 y D2", "Prueba congelada: P1 y P2")


def tiempo(dias, tramos=TRAMOS, estudio=True, cortes=(61, 91, 121, 152), notas=(), pie=""):
    """estudio=True marca qué días de la prueba leyó un estudio anterior (versión del reporte). notas: una frase bajo cada tramo."""
    ds = sorted(int(k) for k in dias)
    tope = max(v[1] for v in dias.values())
    X = escala((0.5, 182.5), (70, 1660))
    Y = escala((0, 40000), (330, 80))
    el = []
    for v in (0, 10000, 20000, 30000, 40000):
        el += [linea(70, Y(v), 1660, Y(v)), texto(58, Y(v) + 7, f"{v // 1000}", "axis", ancla="end")]
    for d in ds:
        color = GRIS_CLARO if d < 61 else (AZUL_MEDIO if d < 121 else AZUL)
        el.append(rect(X(d - .42), Y(min(dias[str(d)][1], 40000)), X(d + .42) - X(d - .42), Y(0) - Y(min(dias[str(d)][1], 40000)), color))
    for (a, b, color), nombre in zip(((1, 60, GRIS), (61, 120, AZUL_MEDIO), (121, 182, AZUL)), tramos):
        el += [linea(X(a - .4), 40, X(b + .4), 40, color, 4), texto(X(a - .4), 26, nombre, "label-strong", NEGRO if color != AZUL else AZUL)]
    for d in cortes:
        el.append(linea(X(d - .5), 52, X(d - .5), 330, "#a5aebc", 2, True))
    for d in (1, 30, 60, 90, 120, 151, 182):
        el.append(texto(X(d), 364, d, "axis", ancla="middle"))
    if estudio:
        el += [linea(X(120.6), 396, X(144.4), 396, VERDE, 5), texto(X(120.6), 430, "nunca leídos", "micro", VERDE),
               linea(X(144.6), 396, X(182.4), 396, NARANJA, 5), texto(X(182.4), 430, "ya usados por otro estudio", "micro", NARANJA, "end"),
               texto(X(1), 430, "día relativo", "micro")]
    else:
        el.append(texto(X(1), 404, "día", "micro"))
    for a, nota in zip((1, 61, 121), notas):
        el.append(texto(X(a - .4), 462, nota, "label"))
    if pie:
        el.append(texto(X(1 - .4), 512, pie, "micro"))
    el.append(texto(70, 70, "mil USD de fraude por día", "micro"))
    alto = 444 if estudio else (526 if pie else 476 if notas else 418)
    return svg(1680, alto, f"Dólares de fraude por día, días 1 a 182; máximo diario {tope:,.0f} USD.", el)


# 6 · Deciles de monto
def deciles(filas):
    X = lambda i: 170 + i * 91  # noqa: E731
    Y = escala((0, .55), (470, 80))
    el = [texto(0, 30, "Parte de los dólares de fraude, por decil de monto del pago", "heading")]
    for v in (0, .1, .2, .3, .4, .5):
        el += [linea(170, Y(v), 1080, Y(v)), texto(158, Y(v) + 7, f"{v * 100:.0f}%", "axis", ancla="end")]
    for i, f in enumerate(filas):
        top = i == 9
        el += [rect(X(i) + 10, Y(f["parte"]), 71, Y(0) - Y(f["parte"]), AZUL if top else GRIS_CLARO),
               texto(X(i) + 45.5, Y(f["parte"]) - 12, f"{f['parte'] * 100:.0f}%", "data" if top else "axis", AZUL if top else None, "middle"),
               texto(X(i) + 45.5, 508, f["rango"], "axis", ancla="middle"),
               texto(X(i) + 45.5, 556, f"{f['tasa'] * 100:.1f}%", "axis", NARANJA if f["tasa"] > .045 else GRIS, "middle")]
    el += [texto(0, 508, "monto USD", "micro"), texto(0, 556, "tasa fraude", "micro", NARANJA)]
    return svg(1100, 576, "Parte de los dólares de fraude y tasa de fraude por decil de monto.", el)


# 7 · Tiempo desde el pago anterior del cliente
def cliente(cats, promedio):
    X = escala((0, .08), (300, 1000))
    el = [texto(0, 30, "Pagos que resultan fraude, según el pago anterior del cliente", "heading"),
          linea(X(promedio), 60, X(promedio), 470, NARANJA, 3, True),
          texto(X(promedio) + 8, 82, f"promedio {promedio * 100:.1f}%", "micro", NARANJA)]
    for i, (nombre, tasa, n) in enumerate(cats):
        y = 120 + i * 78
        color = AZUL if tasa > promedio else GRIS_MEDIO
        el += [texto(0, y + 26, nombre, "label-strong" if tasa > promedio else "label"),
               rect(X(0), y, X(tasa) - X(0), 40, color),
               texto(X(tasa) + 12, y + 30, f"{tasa * 100:.1f}%", "data", color),
               texto(0, y + 54, f"{n:,} pagos", "micro")]
    return svg(1080, 520, "Tasa de fraude por tiempo desde el pago anterior del mismo cliente reconstruido.", el)


# 8 · Ablación de variables
def ablacion(xgb, logit):
    Y = escala((340e3, 540e3), (470, 90))
    pos = (150, 440, 730, 1000)
    etiquetas = ("Descriptivas", "+ historial\nde la tarjeta", "+ cliente", "+ columnas\nopacas")
    el = [texto(0, 36, "Dólares en desarrollo (D1 + D2) según las variables", "heading")]
    for v in range(350_000, 540_001, 50_000):
        el += [linea(90, Y(v), 1080, Y(v)), texto(80, Y(v) + 7, mil(v), "axis", ancla="end")]
    for i, (px, v) in enumerate(zip(pos, xgb)):
        gris = i == 3
        if i:
            ant = xgb[i - 1]
            el.append(linea(pos[i - 1] + 11, Y(ant), px - 11, Y(v), GRIS_MEDIO if gris else AZUL, 3, gris))
            el.append(texto((pos[i - 1] + px) / 2, (Y(ant) + Y(v)) / 2 + (40 if v > ant else -16), f"{mil(v - ant, True)}",
                            "axis", GRIS if gris else AZUL, "middle"))
        el += [punto(px, Y(v), 11, GRIS_MEDIO if gris else AZUL), texto(px, Y(v) - 26, mil(v), "data", GRIS if gris else (AZUL if i == 2 else NEGRO), "middle")]
        for j, parte in enumerate(etiquetas[i].split("\n")):
            el.append(texto(px, 516 + j * 30, parte, "label", GRIS if gris else None, "middle"))
    for (px, v) in zip(pos[1:3], logit):
        el += [trazo([(px, Y(v) - 11), (px + 11, Y(v)), (px, Y(v) + 11), (px - 11, Y(v))], "#fff", 2, VERDE, True),
               texto(px + 20, Y(v) + 30, mil(v), "axis", VERDE)]
    el.append(texto(1000, 588, "no elegible", "micro", GRIS, "middle"))
    el += leyenda(150, 630, [("XGBoost", AZUL, "punto"), ("Logística, mejor C", VERDE, "rombo")], paso=170)
    return svg(1100, 640, "Dólares en desarrollo de XGBoost y la logística con cada conjunto de variables.", el)


# 9 · Torneo de desarrollo
def torneo(filas):
    X = escala((0, max(v for _, v, _ in filas) * 1.12), (440, 1080))
    el = [texto(440, 26, "Miles de USD en D1 + D2", "micro")]
    for i, (nombre, v, color) in enumerate(filas):
        y = 50 + i * 42
        el += [texto(0, y + 24, nombre, "label-strong" if color in (AZUL, NARANJA, VERDE) else "label",
                     color if color in (AZUL, NARANJA, VERDE) else None),
               rect(X(0), y + 4, X(v) - X(0), 28, color),
               texto(X(v) + 10, y + 27, mil(v), "axis", color if color in (AZUL, NARANJA, VERDE) else None)]
    return svg(1120, 50 + len(filas) * 42 + 10, "Dólares en desarrollo de cada política.", el)


# 10 · Prueba: parte del techo que captura cada política
def prueba(periodos):
    el = []
    for k, (titulo, techo, filas) in enumerate(periodos):
        x0 = k * 900
        X = escala((0, techo), (x0 + 250, x0 + 740))
        el.append(texto(x0, 34, titulo, "heading"))
        el.append(texto(x0, 70, f"techo del oráculo: {mil(techo)} mil USD", "micro"))
        for i, (nombre, v, color) in enumerate(filas):
            y = 110 + i * 82
            fuerte = color in (AZUL, VERDE, NARANJA)
            el += [texto(x0, y + 31, nombre, "label-strong" if fuerte else "label", color if fuerte else None),
                   rect(X(0), y, X(techo) - X(0), 46, HIELO), rect(X(0), y, X(v) - X(0), 46, color)]
            dentro = X(v) - X(0) > 150 and color not in (GRIS_CLARO, GRIS_MEDIO)
            el.append(texto(X(v) - 12 if dentro else X(v) + 12, y + 32, f"{mil(v)} mil", "data" if color == AZUL else "label-strong",
                            "#fff" if dentro else NEGRO, "end" if dentro else "start"))
            el.append(texto(X(techo) + 12, y + 31, f"{v / techo * 100:.0f}%", "axis"))
    return svg(1700, 110 + len(periodos[0][2]) * 82, "Dólares de fraude en la cola de cada política frente al techo del oráculo.", el)


# 11 · Intervalos pareados
def intervalos(filas, dominio=(-.2, 1.6), alto=84, cabeza=("Comparador", "P1 · P2", "Ventaja del modelo en dólares de fraude, IC 95%"),
               meses=("días 121–151 (P1)", "días 152–182 (P2)"), barra_nombre="barra fijada antes"):
    X = escala(dominio, (820, 1640))
    el = [texto(0, 40, cabeza[0], "heading"), texto(500, 40, cabeza[1], "heading"),
          texto(820, 40, cabeza[2], "heading"),
          linea(X(0), 70, X(0), 80 + len(filas) * alto, NEGRO, 2)]
    for i, (nombre, sub, c1, c2, barra) in enumerate(filas):
        y = 116 + i * alto
        tono = AZUL if min(c1["rel_ic95"][0], c2["rel_ic95"][0]) > 0 else (NARANJA if max(c1["rel"], c2["rel"]) < 0 else GRIS)
        el += [texto(0, y + 6, nombre, "label-strong"), texto(0, y + 36, sub, "micro"),
               texto(500, y + 14, f"{pct(c1['rel'])} · {pct(c2['rel'])}", "data", tono),
               linea(820, y, 1640, y)]
        if barra is not None:
            el += [linea(X(barra), y - 30, X(barra), y + 30, NARANJA, 3, True)]
        for c, dy, color in ((c1, -12, AZUL_MEDIO), (c2, 12, AZUL)):
            lo, hi = (max(min(v, dominio[1]), dominio[0]) for v in c["rel_ic95"])
            el += [linea(X(lo), y + dy, X(hi), y + dy, color, 4), linea(X(lo), y + dy - 8, X(lo), y + dy + 8, color, 3),
                   punto(X(min(c["rel"], dominio[1])), y + dy, 9, color)]
            if c["rel_ic95"][1] > dominio[1]:
                el.append(trazo([(X(dominio[1]) - 6, y + dy - 8), (X(dominio[1]) + 6, y + dy), (X(dominio[1]) - 6, y + dy + 8)], color, 3))
            else:
                el.append(linea(X(hi), y + dy - 8, X(hi), y + dy + 8, color, 3))
    yb = 80 + len(filas) * alto + 30
    for t in [v / 10 for v in range(round(dominio[0] * 10), round(dominio[1] * 10) + 1, 2)]:
        el.append(texto(X(t), yb, "0" if abs(t) < 1e-9 else f"{t * 100:+.0f}%", "axis", ancla="middle"))
    el += leyenda(820, yb + 46, [(meses[0], AZUL_MEDIO, "punto"), (meses[1], AZUL, "punto"),
                                 (barra_nombre, NARANJA, "trazos")], paso=None)
    return svg(1664, yb + 60, "Ventaja del modelo contra cada comparador con intervalos de 95% en los dos meses de prueba.", el)


# 12 · Exactitud no es dinero
def exactitud(filas):
    paso, w = 16.8, 12
    el = [texto(0, 30, "Una marca por revisión: 60 por día", "heading")]
    y = 90
    for nombre, fraudes, usd_rev, monto, color in filas:
        n = round(fraudes)
        el += [texto(0, y, nombre, "label-strong", color), texto(1010, y, f"{n} de 60 son fraude", "data", color, "end")]
        for i in range(60):
            el.append(rect(i * paso, y + 18, w, 44, color if i < n else HIELO))
        el += [texto(0, y + 100, f"{usd_rev:,.0f} USD de fraude por revisión", "label", color),
               texto(1010, y + 100, f"fraude medio atrapado: {monto:,.0f} USD", "micro", ancla="end")]
        y += 178
    return svg(1020, y - 50, "Fraudes por día y dólares por revisión al ordenar por probabilidad o por probabilidad por monto.", el)


# 13 · Curvas de ganancia
def curvas(series, cupo, iguala, meta):
    xmax = .08
    ymax = max(max(v for f, v in pts if f <= xmax) for _, pts, _ in series) * 1.08
    X = escala((0, xmax), (100, 1050))
    Y = escala((0, ymax), (520, 60))
    el = [texto(100, 28, "Dólares de fraude acumulados al revisar más pagos de cada día", "heading")]
    for v in range(0, int(ymax), 100_000):
        el += [linea(100, Y(v), 1050, Y(v)), texto(88, Y(v) + 7, mil(v), "axis", ancla="end")]
    for f in (0, .02, .04, .06, .08):
        el.append(texto(X(f), 556, f"{f * 100:.0f}%", "axis", ancla="middle"))
    el += [linea(X(cupo), 60, X(cupo), 520, NARANJA, 3, True), texto(X(cupo) + 8, 84, "60 por día", "micro", NARANJA)]
    el += [linea(X(iguala), Y(meta), X(cupo), Y(meta), NARANJA, 2, True), punto(X(iguala), Y(meta), 9, AZUL),
           linea(X(iguala), Y(meta), X(iguala), Y(0), AZUL, 2, True),
           texto(X(iguala) - 14, Y(meta) - 14, f"{iguala * 100:.2f}%", "label-strong", AZUL, "end"),
           texto(100, 62, "mil USD", "micro")]
    for nombre, pts, color in series:
        el.append(trazo([(X(f), Y(v)) for f, v in pts if f <= xmax], color, 4 if color == AZUL else 3))
    el.append(texto(575, 600, "Pagos revisados cada día", "label", ancla="middle"))
    el += leyenda(100, 650, [(n, c, "linea") for n, _, c in series], paso=None)
    return svg(1080, 664, "Curvas de ganancia en dólares del modelo, la logística, la mejor regla y mayor monto primero.", el)


# 15 · Traza del dinero
def traza(periodos):
    total = max(t["fraude_total"] for _, t in periodos)
    X = escala((0, total), (250, 1660))
    seg = (("ambos", "Lo revisan ambos", AZUL, "#fff"), ("solo_modelo", "Solo el modelo", AZUL_MEDIO, NEGRO),
           ("solo_regla", "Solo la regla", NARANJA_CLARO, NEGRO), ("ninguno", "Ninguno: pasa sin revisión", HIELO, NEGRO))
    el = []
    px = 250
    for _, nombre, color, _ in seg:
        el += [rect(px, 22, 20, 20, color), texto(px + 30, 40, nombre, "micro")]
        px += len(nombre) * 11.5 + 80
    for i, (titulo, t) in enumerate(periodos):
        y = 90 + i * 150
        el += [texto(0, y + 50, titulo, "label-strong"), texto(0, y + 82, f"{mil(t['fraude_total'])} mil USD de fraude", "micro")]
        a = 0.0
        for clave, _, color, tinta in seg:
            v = t[clave]
            el.append(rect(X(a), y, X(a + v) - X(a) - 3, 100, color))
            if X(a + v) - X(a) > 70:
                el.append(texto((X(a) + X(a + v)) / 2, y + 68, mil(v), "chart-big", tinta, "middle"))
            a += v
    el.append(texto(1660, 90 + len(periodos) * 150 + 6, "mil USD", "micro", ancla="end"))
    return svg(1680, 90 + len(periodos) * 150 + 16, "Dólares de fraude del mes según lo revisen el modelo, la regla, ambos o ninguno.", el)


# Apéndice · diferencia diaria
def diario(filas):
    lim = max(abs(v) for _, v in filas) * 1.1
    X = escala((120.5, 182.5), (80, 1660))
    Y = escala((-lim, lim), (440, 40))
    el = []
    for v in (-20000, -10000, 0, 10000, 20000):
        if abs(v) < lim:
            el += [linea(80, Y(v), 1660, Y(v), NEGRO if v == 0 else LINEA, 2), texto(68, Y(v) + 7, mil(v, v != 0), "axis", ancla="end")]
    for d, v in filas:
        el.append(rect(X(d - .38), min(Y(v), Y(0)), X(d + .38) - X(d - .38), abs(Y(v) - Y(0)), AZUL if v >= 0 else NARANJA))
    el.append(linea(X(151.5), 30, X(151.5), 450, "#a5aebc", 2, True))
    el += [texto(X(136), 26, "P1 · días 121–151", "label-strong", ancla="middle"), texto(X(167), 26, "P2 · días 152–182", "label-strong", ancla="middle")]
    for d in (121, 136, 151, 166, 182):
        el.append(texto(X(d), 482, d, "axis", ancla="middle"))
    el.append(texto(0, 26, "mil USD", "axis"))
    return svg(1680, 500, "Diferencia diaria de dólares de fraude en la cola, modelo menos la mejor regla.", el)


# Apéndice · importancia por grupo
def importancia(filas, titulo="Miles de USD que se pierden al permutar el grupo (D2)", destacar=lambda n: "cliente" in n):
    vmax = max(v for _, v in filas)
    X = escala((0, vmax * 1.15), (420, 1080))
    el = [texto(420, 26, titulo, "micro")]
    for i, (nombre, v) in enumerate(filas):
        y = 50 + i * 48
        d = destacar(nombre)
        color = AZUL if d else (GRIS_MEDIO if v > 0 else GRIS_CLARO)
        el += [texto(0, y + 26, nombre, "label-strong" if d else "label", AZUL if d else None),
               rect(X(0), y + 6, max(X(max(v, 0)) - X(0), 2), 30, color),
               texto(X(max(v, 0)) + 10, y + 29, mil(v, v < 0), "axis")]
    return svg(1100, 60 + len(filas) * 48, "Dólares perdidos al barajar cada grupo de variables.", el)


# Preparación de datos: el historial de un cliente visto desde el pago de hoy (esquema ilustrativo)
PAGOS_PREVIOS = [(-9, 35), (-6.2, 42), (-3.5, 29), (-2.1, 38), (-0.62, 31), (-0.03, 36)]  # (días antes de hoy, USD)
PAGO_HOY = 120


def historial_cliente():
    # eje comprimido (raíz de los días) para que el pago de hace 43 minutos no se encime con el de hoy
    X = lambda d: 40 + (math.copysign(math.sqrt(abs(d)), d) + 3.15) * 940 / 4.55  # noqa: E731
    y0, x0 = 340, X(0)
    el = [texto(0, 30, "Pagos del mismo cliente antes del pago de hoy", "heading"),
          texto(0, 66, "Monto de cada pago en USD · eje de tiempo comprimido", "micro"),
          rect(x0 + 84, 96, 1080 - x0 - 84, 290, HIELO),
          texto((x0 + 84 + 1080) / 2, 134, "Futuro: no se usa", "label", GRIS, "middle"),
          linea(20, y0, 1080, y0, "#a5aebc", 2)]
    for d0, nombre, yb in ((-7, f"Última semana: {sum(1 for d, _ in PAGOS_PREVIOS if d >= -7)} pagos", 172),
                           (-1, f"Último día: {sum(1 for d, _ in PAGOS_PREVIOS if d >= -1)} pagos", 232)):
        el += [linea(X(d0), yb, x0, yb, AZUL, 3), linea(X(d0), yb, X(d0), yb + 12, AZUL, 3), linea(x0, yb, x0, yb + 12, AZUL, 3),
               texto((X(d0) + x0) / 2, yb - 14, nombre, "micro", AZUL, "middle")]
    for d, m in PAGOS_PREVIOS:
        el += [punto(X(d), y0, 10, AZUL_MEDIO), texto(X(d), y0 - 26, m, "axis", ancla="middle")]
    for d in (0.45, 1.35):
        el.append(punto(X(d), y0, 10, "#fff", GRIS_CLARO, 3))
    el += [punto(x0, y0, 15, AZUL), texto(x0 + 20, y0 - 24, PAGO_HOY, "data", AZUL)]
    for d, t in ((-7, "hace 7 días"), (-3, "hace 3 días"), (-1, "hace 1 día")):
        el.append(texto(X(d), y0 + 48, t, "micro", ancla="middle"))
    el.append(texto(x0, y0 + 48, "hoy", "label-strong", AZUL, "middle"))
    return svg(1080, y0 + 60, "Esquema del historial de un cliente: solo cuentan los pagos anteriores al pago de hoy.", el)


# Valor de la revisión marginal: USD de fraude por revisión en cada tramo de la cola diaria
def marginal(series, tramo, costos, dev, kmax=700):
    X = escala((0, kmax), (120, 1040))
    Y = escala((math.log10(2), math.log10(300)), (540, 70))
    ly = lambda v: Y(math.log10(min(max(v, 2), 300)))  # noqa: E731
    el = [texto(120, 30, "USD de fraude por revisión, en tramos de 20 lugares", "heading")]
    for v in (3, 10, 30, 100, 300):
        el += [linea(120, ly(v), 1040, ly(v)), texto(108, ly(v) + 7, v, "axis", ancla="end")]
    for k in range(0, kmax + 1, 100):
        el.append(texto(X(k), 576, k, "axis", ancla="middle"))
    el += [linea(X(60), 60, X(60), 540, NARANJA, 3, True), texto(X(60) + 8, 86, "60 por día", "micro", NARANJA)]
    for c, _ in costos:
        el += [linea(120, ly(c), 1040, ly(c), GRIS_MEDIO, 2, True), texto(1040, ly(c) - 10, f"costo {c} USD", "micro", ancla="end")]

    def suave(v):
        n = min(len(v), kmax // tramo)
        s = [v[i] if i < 5 else sum(v[i - 2: i + 3]) / len(v[i - 2: i + 3]) for i in range(n)]
        return [(X(i * tramo + tramo / 2), ly(s[i])) for i in range(n)]
    for _, v, color in series[::-1]:
        el.append(trazo(suave(v), color, 4 if color == AZUL else 3))
    el.append(trazo(suave(dev), AZUL, 2, trazos=True))
    for c, kstar in costos:
        el += [punto(X(kstar), ly(c), 9, AZUL), texto(X(kstar) + 14, ly(c) - 12, kstar, "label-strong", AZUL)]
    el.append(texto(580, 614, "Lugar en la cola de cada día", "label", ancla="middle"))
    el += leyenda(120, 662, [(f"{n}, prueba" if i == 0 else n, c, "linea") for i, (n, _, c) in enumerate(series)])
    el += leyenda(120, 702, [("Modelo, desarrollo", AZUL, "trazos"), ("cupo elegido en desarrollo para ese costo", AZUL, "punto")])
    return svg(1080, 716, "Valor de la revisión marginal según el lugar en la cola diaria, con líneas de costo por revisión.", el)


# Calibración: probabilidad estimada contra tasa observada
def calibracion(series):
    X = escala((math.log10(0.002), 0), (130, 1030))
    Y = escala((math.log10(0.002), 0), (590, 60))
    lx = lambda p: X(math.log10(max(p, 0.002)))  # noqa: E731
    ly = lambda p: Y(math.log10(max(p, 0.002)))  # noqa: E731
    el = [texto(130, 26, "Tasa de fraude observada por tramo de probabilidad", "heading")]
    for v, t in ((0.003, "0.3%"), (0.01, "1%"), (0.03, "3%"), (0.1, "10%"), (0.3, "30%"), (1, "100%")):
        el += [linea(130, ly(v), 1030, ly(v)), linea(lx(v), 60, lx(v), 590), texto(118, ly(v) + 7, t, "axis", ancla="end"),
               texto(lx(v), 624, t, "axis", ancla="middle")]
    el += [linea(lx(0.002), ly(0.002), lx(1), ly(1), NEGRO, 2, True),
           texto(lx(0.012), ly(0.006), "diagonal: calibración perfecta", "micro"),
           texto(150, 98, "arriba: subestima el fraude", "micro"),
           texto(1010, 566, "abajo: sobreestima el fraude", "micro", ancla="end")]
    nmax = max(b["n"] for _, bins, _ in series for b in bins)
    for _, bins, color in series[::-1]:
        pts = [(lx(b["p_media"]), ly(b["tasa"])) for b in bins]
        el.append(trazo(pts, color, 3))
        el += [punto(x, y, round(6 + 12 * math.sqrt(b["n"] / nmax), 1), color) for (x, y), b in zip(pts, bins)]
    el.append(texto(580, 664, "Probabilidad estimada", "label", ancla="middle"))
    el += leyenda(130, 712, [(n, c, "punto") for n, _, c in series] + [("tamaño del punto: pagos en el tramo", GRIS_CLARO, "punto")])
    return svg(1060, 724, "Diagrama de calibración: probabilidad estimada contra tasa de fraude observada.", el)


# Apéndice · regularización de la logística: dinero y AUC según C
def regularizacion(filas, elegido):
    cs = sorted({f["C"] for f in filas})
    X = lambda c: 200 + cs.index(c) * 200  # noqa: E731
    Y = escala((330e3, 410e3), (470, 90))
    el = [texto(0, 30, "Miles de USD en desarrollo (D1 + D2) según la fuerza de la penalización", "heading")]
    for v in range(340_000, 410_001, 20_000):
        el += [linea(150, Y(v), 1060, Y(v)), texto(138, Y(v) + 7, mil(v), "axis", ancla="end")]
    for conj, color in (("F2", GRIS_MEDIO), ("F3", VERDE)):
        fs = [f for f in filas if f["conjunto"] == conj]
        el.append(trazo([(X(f["C"]), Y(f["usd"])) for f in fs], color, 4 if conj == "F3" else 3))
        for f in fs:
            grande = conj == "F3" and f["C"] == elegido
            el.append(punto(X(f["C"]), Y(f["usd"]), 12 if grande else 8, color))
            if conj == "F3":
                el.append(texto(X(f["C"]), Y(f["usd"]) - 24, mil(f["usd"]), "data" if grande else "label-strong", VERDE if grande else NEGRO, "middle"))
    aucs = {c: next(f["auc"] for f in filas if f["conjunto"] == "F3" and f["C"] == c) for c in cs}
    for c in cs:
        alto = aucs[c] == max(aucs.values())
        el += [texto(X(c), 512, f"C = {c:g}", "label", ancla="middle"),
               texto(X(c), 546, f"AUC {aucs[c]:.3f}", "axis", NEGRO if alto else None, "middle", 700 if alto else None)]
    el += [texto(200, 596, "← más penalización", "micro"), texto(1000, 596, "menos penalización →", "micro", ancla="end")]
    el += leyenda(200, 648, [("Logística con F3", VERDE, "punto"), ("con F2", GRIS_MEDIO, "punto")], paso=240)
    return svg(1080, 660, "Dólares en desarrollo de la logística para cada valor de C, con su AUC.", el)


# Apéndice · AUC contra dinero: cada política de desarrollo con 60 revisiones por día
def auc_dinero(puntos, destacados, hueco):
    X = escala((0.45, 0.92), (130, 1050))
    Y = escala((0, 320e3), (560, 60))
    el = [texto(130, 26, "Días 91–120 · miles de USD de fraude en la cola de cada política", "heading")]
    for v in range(0, 300_001, 100_000):
        el += [linea(130, Y(v), 1050, Y(v)), texto(118, Y(v) + 7, mil(v), "axis", ancla="end")]
    for a in (0.5, 0.6, 0.7, 0.8, 0.9):
        el.append(texto(X(a), 596, f"{a:.1f}", "axis", ancla="middle"))
    pm = {p["politica"]: p for p in puntos if p["puntaje"] == "p_x_monto"}
    solo = next(p for p in puntos if p["politica"] == hueco and p["puntaje"] == "p")
    el += [linea(X(solo["auc"]), Y(solo["usd"]), X(pm[hueco]["auc"]), Y(pm[hueco]["usd"]), AZUL, 2, True),
           punto(X(solo["auc"]), Y(solo["usd"]), 9, "#fff", AZUL, 3),
           texto(X(solo["auc"]) - 18, Y(solo["usd"]) + 8, f"el mismo modelo, solo probabilidad: {mil(solo['usd'])} mil", "label", NEGRO, "end")]
    for nombre, p in pm.items():
        if nombre not in destacados:
            el.append(punto(X(p["auc"]), Y(p["usd"]), 7, GRIS_CLARO))
    for nombre, (etq, color, dx, dy) in destacados.items():
        p = pm[nombre]
        el += [punto(X(p["auc"]), Y(p["usd"]), 10, color),
               texto(X(p["auc"]) + dx, Y(p["usd"]) + dy, etq, "label-strong", NEGRO if color in (GRIS_MEDIO,) else color, "end" if dx < 0 else "start")]
    el.append(texto(590, 636, "AUC en los días 91–120", "label", ancla="middle"))
    el += [punto(139, 677, 9, GRIS_CLARO), texto(158, 684, "cada política, ordenada por probabilidad × monto", "micro"),
           punto(689, 677, 9, "#fff", AZUL, 3), texto(708, 684, "ordenada solo por probabilidad", "micro")]
    return svg(1080, 700, "AUC contra dólares en la cola para cada política de desarrollo.", el)


def _ejes_unitarios(x0, y0, lado, etiqueta_x, etiqueta_y):
    X = escala((0, 1), (x0, x0 + lado))
    Y = escala((0, 1), (y0 + lado, y0))
    el = []
    for v in (0, .25, .5, .75, 1):
        el += [linea(x0, Y(v), x0 + lado, Y(v)), linea(X(v), y0, X(v), y0 + lado),
               texto(x0 - 12, Y(v) + 7, f"{v * 100:.0f}%", "axis", ancla="end"), texto(X(v), y0 + lado + 34, f"{v * 100:.0f}%", "axis", ancla="middle")]
    el += [texto(x0 + lado / 2, y0 + lado + 72, etiqueta_x, "label", ancla="middle"), texto(x0 - 70, y0 - 18, etiqueta_y, "micro")]
    return X, Y, el


# Capítulo 4 del curso · la misma cola vista en ROC y en precisión–recall, con el punto de operación de 60 por día
def roc_pr(series, prevalencia):
    lado, y0 = 400, 104
    XA, YA, el = _ejes_unitarios(110, y0, lado, "Falsos positivos (FPR)", "Recall (TPR)")
    XB, YB, eb = _ejes_unitarios(660, y0, lado, "Recall", "Precisión")
    el += eb + [texto(40, 36, "ROC", "heading"), texto(590, 36, "Precisión–recall", "heading"),
                linea(XA(0), YA(0), XA(1), YA(1), GRIS_MEDIO, 2, True),
                linea(XB(0), YB(prevalencia), XB(1), YB(prevalencia), GRIS_MEDIO, 2, True)]
    for s in series[::-1]:
        tr = 4 if s["color"] == AZUL else 3
        el.append(trazo([(XA(0), YA(0))] + [(XA(a), YA(b)) for a, b in zip(s["fpr"], s["tpr"])], s["color"], tr, trazos=s.get("trazos", False)))
        el.append(trazo([(XB(a), YB(b)) for a, b in zip(s["tpr"], s["precision"]) if a >= .004], s["color"], tr, trazos=s.get("trazos", False)))
    for s in series[::-1]:
        o = s["op"]
        el += [punto(XA(o["fpr"]), YA(o["recall"]), 9, s["color"]), punto(XB(o["recall"]), YB(o["precision"]), 9, s["color"])]
    m = series[0]["op"]
    el += [texto(XB(m["recall"]) + 10, YB(m["precision"]) + 46, f"{m['precision'] * 100:.0f}%", "label-strong", AZUL)]
    # áreas: AUC abajo a la derecha de la ROC, AP arriba a la derecha de precisión–recall
    el += [texto(XA(1), YA(.3), "AUC", "micro", ancla="end"), texto(XB(1), YB(.92), "AP (PR-AUC)", "micro", ancla="end")]
    for i, s in enumerate(series):
        el += [texto(XA(1), YA(.3) + 32 + 30 * i, f"{s['corto']} {s['auc']:.3f}", "label", s["color"] if s["color"] != GRIS_MEDIO else NEGRO, "end"),
               texto(XB(1), YB(.92) + 32 + 30 * i, f"{s['corto']} {s['ap']:.2f}", "label", s["color"] if s["color"] != GRIS_MEDIO else NEGRO, "end")]
    el += leyenda(110, 636, [(s["nombre"], s["color"], "trazos" if s.get("trazos") else "linea") for s in series])
    el += leyenda(110, 676, [("punto: 60 revisiones por día", GRIS_MEDIO, "punto"),
                             (f"azar: la diagonal en ROC, {prevalencia * 100:.1f}% en precisión–recall", GRIS_MEDIO, "trazos")])
    return svg(1080, 690, "Curvas ROC y precisión–recall de las colas, con su punto de operación de 60 revisiones por día.", el)


# Capítulo 4 del curso · ganancia acumulada (cumulative gains) con el orden de cada día
def ganancia_acum(series, cupo, decil1):
    X = escala((0, 1), (110, 1050))
    Y = escala((0, 1), (540, 70))
    el = [texto(110, 30, "Parte del fraude capturado al revisar más pagos de cada día", "heading")]
    for v in (0, .2, .4, .6, .8, 1):
        el += [linea(110, Y(v), 1050, Y(v)), texto(98, Y(v) + 7, f"{v * 100:.0f}%", "axis", ancla="end")]
    for v in (0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1):
        el.append(texto(X(v), 576, f"{v * 100:.0f}%", "axis", ancla="middle"))
    el += [linea(X(0), Y(0), X(1), Y(1), GRIS_MEDIO, 2, True), texto(X(.62), Y(.62) + 34, "al azar", "micro", ancla="middle"),
           linea(X(cupo), 60, X(cupo), 540, NARANJA, 3, True), texto(X(cupo) - 4, 54, "60 por día", "micro", NARANJA),
           linea(X(.1), 60, X(.1), 540, GRIS_CLARO, 2), texto(X(.1) + 8, 530, "decil 1", "micro")]
    for s in series[::-1]:
        el.append(trazo([(X(f), Y(v)) for f, v in zip(s["fraccion"], s["valores"])], s["color"], 4 if s["color"] == AZUL else 3,
                        trazos=s.get("trazos", False)))
    u, f = decil1
    el += [punto(X(.1), Y(u), 9, AZUL), punto(X(.1), Y(f), 9, "#fff", AZUL, 3),
           texto(X(.6), Y(.3), "En el decil 1:", "micro"),
           punto(X(.6) + 9, Y(.3) + 34, 9, AZUL), texto(X(.6) + 30, Y(.3) + 43, f"{u * 100:.0f}% del dinero", "label-strong", AZUL),
           punto(X(.6) + 9, Y(.3) + 76, 9, "#fff", AZUL, 3), texto(X(.6) + 30, Y(.3) + 85, f"{f * 100:.0f}% de los fraudes", "label", AZUL)]
    el.append(texto(580, 614, "Pagos revisados de cada día, en orden del modelo", "label", ancla="middle"))
    el += leyenda(110, 662, [(s["nombre"], s["color"], "trazos" if s.get("trazos") else "linea") for s in series])
    return svg(1080, 676, "Curvas de ganancia acumulada en dólares y en número de fraudes, con la línea del azar.", el)


# Capítulo 4 del curso · curva de beneficio contra el umbral, para varios costos por revisión
def montana(t, curvas, corte60, tmin=1, tmax=3000, ymin=-200e3, ymax=600e3):
    X = escala((math.log10(tmin), math.log10(tmax)), (120, 1040))
    Y = escala((ymin, ymax), (540, 70))
    lx = lambda v: X(math.log10(v))  # noqa: E731
    el = [texto(120, 30, "Beneficio neto al revisar todo pago con fraude esperado ≥ t", "heading")]
    for v in range(int(ymin), int(ymax) + 1, 200_000):
        el += [linea(120, Y(v), 1040, Y(v), "#a5aebc" if v == 0 else LINEA, 2), texto(108, Y(v) + 7, mil(v), "axis", ancla="end")]
    for v in (1, 3, 10, 30, 100, 300, 1000, 3000):
        el.append(texto(lx(v), 576, f"{v:,}", "axis", ancla="middle"))
    el += [linea(lx(corte60), 60, lx(corte60), 540, NARANJA, 3, True), texto(lx(corte60), 54, "60 por día", "micro", NARANJA, "middle"),
           texto(120, 62, "mil USD", "micro")]
    for c in curvas:
        pts = [(lx(a), Y(b)) for a, b in zip(t, c["valores"]) if tmin <= a <= tmax and b >= ymin]
        el.append(trazo(pts, c["color"], 4 if c["color"] == AZUL else 3))
    for c in curvas:
        j = next(j for j, (a, b) in enumerate(zip(t, c["valores"])) if a >= tmin and b >= ymin)
        if c["valores"][j] > ymin + .25 * (ymax - ymin):  # la curva entra por la izquierda: etiqueta abajo de su arranque
            xe, ye = lx(t[j]) + 14, Y(c["valores"][j]) + 34
        else:  # la curva sube desde abajo: etiqueta junto al piso, a la derecha de donde ya subió
            k = next(k for k, (a, b) in enumerate(zip(t, c["valores"])) if a >= tmin and b >= ymin + .12 * (ymax - ymin))
            xe, ye = lx(t[k]) + 10, Y(ymin) - 8
        el += [punto(lx(c["t_dev"]), Y(c["neto_dev"]), 9, c["color"]),
               texto(xe, ye, f"{c['costo']} USD", "label-strong", c["color"] if c["color"] != AZUL_MEDIO else GRIS)]
    el.append(texto(580, 614, "Umbral t: fraude esperado del pago, probabilidad × monto (USD, escala log)", "label", ancla="middle"))
    el += leyenda(120, 662, [(f"costo {c['costo']} USD", c["color"], "linea") for c in curvas]
                  + [("elegido en desarrollo", GRIS_MEDIO, "punto")])
    return svg(1080, 676, "Curvas de beneficio contra el umbral de fraude esperado para tres costos por revisión.", el)


# Apéndice · distribución de la probabilidad por clase (el duelo del AUC)
def distribucion(bordes, fraude, legitimo, med_f, med_l):
    X = escala((bordes[0], bordes[-1]), (120, 1040))
    top = max(max(fraude), max(legitimo)) * 1.32
    Y = escala((0, top), (520, 70))
    w = (X(bordes[1]) - X(bordes[0])) / 2 - 1
    el = [texto(120, 30, "Parte de cada clase en cada tramo de probabilidad del modelo", "heading")]
    for v in (0, .02, .04, .06, .08, .1, .12):
        if v <= top:
            el += [linea(120, Y(v), 1040, Y(v)), texto(108, Y(v) + 7, f"{v * 100:.0f}%", "axis", ancla="end")]
    for e, tx in ((-4, "0.01%"), (-3, "0.1%"), (-2, "1%"), (-1, "10%"), (0, "100%")):
        el.append(texto(X(e), 556, tx, "axis", ancla="middle"))
    for i in range(len(fraude)):
        x = X(bordes[i])
        el += [rect(x + 1, Y(legitimo[i]), w, Y(0) - Y(legitimo[i]), AZUL_MEDIO), rect(x + w + 1, Y(fraude[i]), w, Y(0) - Y(fraude[i]), NARANJA)]
    for m, nombre, color, lado in ((med_l, "mediana legítimos", AZUL, -1), (med_f, "mediana fraudes", NARANJA, 1)):
        xm, ancla = X(math.log10(m)), "end" if lado < 0 else "start"
        el += [linea(xm, 70, xm, 520, color, 3, True), texto(xm + 12 * lado, 96, nombre, "label", color, ancla),
               texto(xm + 12 * lado, 128, f"{m * 100:.1f}%", "label-strong", color, ancla)]
    el.append(texto(580, 594, "Probabilidad de fraude estimada (escala log)", "label", ancla="middle"))
    el += leyenda(120, 640, [("pagos legítimos", AZUL_MEDIO, "cuadro"), ("fraudes", NARANJA, "cuadro")], paso=230)
    return svg(1080, 654, "Distribución de la probabilidad estimada para fraudes y pagos legítimos.", el)


# Mantenimiento · validación cruzada temporal: ventanas con origen móvil, confirmación y prueba
def validacion_temporal(filas, margen, ultimo=182):
    """filas: (nombre, sub, ini, fin, tipo), tipo interna | confirma | prueba. Cada fila entrena con los días < ini − margen."""
    x0, x1, alto = 360, 1660, 70
    X = escala((0.5, ultimo + .5), (x0, x1))
    relleno = {"interna": AZUL_MEDIO, "confirma": AZUL, "prueba": NARANJA_CLARO}
    tinta = {"interna": NEGRO, "confirma": "#fff", "prueba": NEGRO}
    el = [texto(X(d), 28, d, "axis", ancla="middle") for d in (1, 30, 60, 90, 120, 151, 182)]
    y0 = 58
    fondo = y0 + len(filas) * alto
    el.append(linea(X(120.5), 40, X(120.5), fondo, "#a5aebc", 2, True))
    for i, (nombre, sub, ini, fin, tipo) in enumerate(filas):
        y = y0 + i * alto
        corte = ini - margen
        el += [texto(0, y + 24, nombre, "label-strong", AZUL if tipo == "confirma" else (NARANJA if tipo == "prueba" else None)),
               texto(0, y + 52, sub, "micro"),
               rect(X(.5), y + 6, X(corte - .5) - X(.5), 40, GRIS_CLARO),
               rect(X(corte - .5), y + 6, X(ini - .5) - X(corte - .5), 40, HIELO, 1, "#c9d1db", 1.5),
               rect(X(ini - .5), y + 6, X(fin + .5) - X(ini - .5), 40, relleno[tipo]),
               texto((X(ini - .5) + X(fin + .5)) / 2, y + 35, f"{ini}–{fin}", "axis", tinta[tipo], "middle")]
        if X(corte - .5) - X(.5) > 190:
            el.append(texto(X(.5) + 12, y + 35, f"entrena: días 1–{corte - 1}", "micro", NEGRO))
        if i == 0:
            el.append(texto((X(corte - .5) + X(ini - .5)) / 2, y + 35, f"{margen} días", "micro", GRIS, "middle"))
    yl = fondo + 52
    items = [("entrenamiento", GRIS_CLARO, None), (f"margen de {margen} días, sin uso", HIELO, "#c9d1db"),
             ("evaluación de la búsqueda", AZUL_MEDIO, None), ("confirmación", AZUL, None), ("prueba", NARANJA_CLARO, None)]
    px = x0
    for nombre, color, borde in items:
        el += [rect(px, yl - 18, 22, 22, color, 1, borde or "none", 1.5 if borde else 0), texto(px + 32, yl, nombre, "micro")]
        px += 32 + len(nombre) * 11.2 + 40
    return svg(1680, yl + 14, "Diseño de validación: tres ventanas internas con origen móvil, un bloque de confirmación y la prueba.", el)


# Mantenimiento · búsqueda hacia adelante: cada ronda prueba los grupos restantes y acepta el mejor si cumple la regla
def escalada(pasos, minimo):
    """pasos: dicts con etiqueta, sub, usd (valor aceptado o None), previo (valor de partida o None), candidatos [(nombre, usd)]."""
    vals = [p["usd"] for p in pasos if p["usd"] is not None] + [u for p in pasos for _, u in p["candidatos"]]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * .18 or hi * .02
    paso_y = max(5_000, round((hi - lo + 2 * pad) / 5 / 5_000) * 5_000)
    a, b = math.floor((lo - pad) / paso_y) * paso_y, math.ceil((hi + pad) / paso_y) * paso_y
    Y = escala((a, b), (520, 80))
    n = len(pasos)
    xs = [160 + i * (840 / max(n - 1, 1)) for i in range(n)]
    el = [texto(120, 30, "Miles de USD en la cola, suma de las tres ventanas internas", "heading")]
    for v in range(int(a), int(b) + 1, int(paso_y)):
        el += [linea(120, Y(v), 1060, Y(v)), texto(108, Y(v) + 7, mil(v), "axis", ancla="end")]
    camino = [(x, Y(p["usd"])) for x, p in zip(xs, pasos) if p["usd"] is not None]
    for x, p in zip(xs, pasos):
        cand = sorted(p["candidatos"], key=lambda c: c[1])
        if p["previo"] is not None:
            meta = p["previo"] * (1 + minimo)
            el.append(linea(x - 50, Y(meta), x + 50, Y(meta), NARANJA, 3, True))
        for j, (_, u) in enumerate(cand):
            dx = (j - (len(cand) - 1) / 2) * 11
            el.append(punto(x + dx, Y(u), 7, GRIS_CLARO, "#fff", 1.5))
        if p["usd"] is None and cand:
            nombre, u = cand[-1]
            dx = ((len(cand) - 1) / 2) * 11
            el += [punto(x + dx, Y(u), 9, "#fff", NARANJA, 3), texto(x + dx, Y(u) - 20, nombre, "micro", NARANJA, "middle")]
        partes = p["etiqueta"].split("\n")
        for j, parte in enumerate(partes):
            el.append(texto(x, 560 + j * 30, parte, "label-strong" if p["usd"] is not None else "label", None, "middle"))
        el.append(texto(x, 560 + 30 * len(partes), p["sub"], "micro", GRIS, "middle"))
    el.append(trazo(camino, AZUL, 4))
    for x, p in zip(xs, pasos):
        if p["usd"] is not None:
            el += [punto(x, Y(p["usd"]), 11, AZUL), texto(x, Y(p["usd"]) - 24, mil(p["usd"]), "data", AZUL, "middle")]
    yl = 560 + 30 * max(len(p["etiqueta"].split("\n")) for p in pasos) + 72
    el += leyenda(120, yl, [("aceptado", AZUL, "punto"), ("cada grupo o rejilla probado", GRIS_CLARO, "punto"),
                            (f"barra: +{minimo * 100:.0f}% sobre el paso anterior", NARANJA, "trazos")])
    return svg(1080, yl + 14, "Selección hacia adelante por grupos: dinero en las ventanas internas en cada ronda.", el)


# Mantenimiento · confirmación y lectura posterior: ventaja relativa con intervalos de 95% en cada bloque
def confirmacion(filas, paneles, dominio):
    """filas: (nombre, sub, color, [contraste o None por panel]); paneles: (titulo, sub)."""
    ancho, gap, alto, y0 = 320, 44, 112, 96
    W = len(paneles) * (ancho + gap) - gap
    fondo = y0 + len(filas) * alto
    el, escalas = [], []
    for k, (titulo, sub) in enumerate(paneles):
        a = k * (ancho + gap)
        X = escala(dominio, (a + 10, a + ancho - 10))
        escalas.append(X)
        el += [texto(a, 30, titulo, "label-strong", AZUL if k == 0 else GRIS), texto(a, 62, sub, "micro")]
        el += [linea(X(0), y0 + i * alto + 50, X(0), y0 + (i + 1) * alto, NEGRO, 2) for i in range(len(filas))]
        for t in (([dominio[0]] if dominio[0] < -.08 else []) + [0, dominio[1]]):
            ancla = "middle" if abs(t) < 1e-9 else ("start" if t < 0 else "end")
            xt = X(t) + {"middle": 0, "start": -10, "end": 10}[ancla]
            el.append(texto(xt, fondo + 36, "0" if abs(t) < 1e-9 else f"{t * 100:+.0f}%".replace("-", "−"), "axis", ancla=ancla))
    for i, (nombre, sub, color, cs) in enumerate(filas):
        y = y0 + i * alto
        el += [linea(0, y, W, y), texto(0, y + 32, nombre, "label-strong", color if color != GRIS_MEDIO else None),
               texto(W, y + 32, sub, "micro", ancla="end")]
        yc = y + 76
        for k, c in enumerate(cs):
            X = escalas[k]
            if c is None:
                el.append(texto(X((dominio[0] + dominio[1]) / 2), yc + 7, "—", "axis", ancla="middle"))
                continue
            lo, hi = (max(min(v, dominio[1]), dominio[0]) for v in c["rel_ic95"])
            col = color if k == 0 else (AZUL_MEDIO if color == AZUL else color)
            xr = X(max(min(c["rel"], dominio[1]), dominio[0]))
            xd = max(X(hi), X(0)) if X(hi) < X(0) else X(hi)  # intervalo bajo cero: la cifra va después de la línea de cero
            derecha = xd + 12 + 70 <= k * (ancho + gap) + ancho
            el += [linea(X(lo), yc, X(hi), yc, col, 4), linea(X(lo), yc - 9, X(lo), yc + 9, col, 3), linea(X(hi), yc - 9, X(hi), yc + 9, col, 3),
                   punto(xr, yc, 9, col),
                   texto(xd + 12 if derecha else X(lo) - 12, yc + 8, pct(c["rel"], d=1), "label-strong", NEGRO, "start" if derecha else "end")]
    return svg(W + 4, fondo + 50, "Ventaja relativa en dólares con intervalos de 95% en la confirmación y en la lectura posterior de la prueba.", el)


# Resumen ejecutivo: dinero de fraude detenido por cada política en la prueba
def resumen(filas):
    """filas: (nombre, usd, color), de arriba abajo; la primera es la práctica actual y la última el modelo."""
    tope = max(v for _, v, _ in filas)
    X = escala((0, tope), (0, 820))
    y0, paso, grueso = 76, 150, 66
    el = [texto(0, 30, "Fraude detenido en los dos meses de prueba, miles de USD", "heading")]
    base = X(filas[0][1])
    el.append(linea(base, y0 + 46, base, y0 + (len(filas) - 1) * paso + 46 + grueso, GRIS_MEDIO, 2, True))
    for i, (nombre, v, color) in enumerate(filas):
        y = y0 + i * paso
        el += [texto(0, y + 30, nombre, "label-strong", color), rect(0, y + 46, X(v), grueso, color),
               texto(X(v) + 20, y + 46 + grueso / 2 + 18, mil(v), "chart-big", color)]
    return svg(1080, y0 + (len(filas) - 1) * paso + 46 + grueso + 6,
               "Dinero de fraude detenido por la práctica actual, la logística y el modelo en los dos meses de prueba.", el)


# Modelado: del árbol al bosque y al boosting, con la logística como referencia y los demás modelos en gris
def escalera(pasos, referencia, otros, tope=500e3):
    """pasos: (nombre, usd, color) en el orden del curso; referencia: (nombre, usd, color), una línea; otros: (nombre, usd)."""
    Y = escala((0, tope), (500, 70))
    ancho, ancho_o = 130, 100
    xs = [90 + i * 190 for i in range(len(pasos))]
    xo = [xs[-1] + ancho + 110 + j * 140 for j in range(len(otros))]
    fin = (xo[-1] + ancho_o) if otros else xs[-1] + ancho
    el = [texto(0, 26, "Miles de USD de fraude detenido en desarrollo", "micro")]
    for v in range(0, int(tope) + 1, 100_000):
        el += [linea(70, Y(v), fin + 10, Y(v), "#a5aebc" if v == 0 else LINEA, 2), texto(58, Y(v) + 7, mil(v), "axis", ancla="end")]
    nombre_r, v_r, color_r = referencia
    el.append(linea(70, Y(v_r), xs[-1] + ancho + 30, Y(v_r), color_r, 3, True))  # detrás de las barras
    for i, (nombre, v, color) in enumerate(pasos):
        x = xs[i]
        el += [rect(x, Y(v), ancho, Y(0) - Y(v), color), texto(x + ancho / 2, Y(v) - 16, mil(v), "data", color, "middle")]
        for j, parte in enumerate(nombre.split("\n")):
            el.append(texto(x + ancho / 2, 536 + j * 30, parte, "label-strong" if color == AZUL else "label", None, "middle"))
    if otros:
        el.append(texto((xo[0] + xo[-1] + ancho_o) / 2, Y(tope) - 16, "Otros modelos probados", "micro", ancla="middle"))
    for j, (nombre, v) in enumerate(otros):
        x = xo[j]
        el += [rect(x, Y(v), ancho_o, Y(0) - Y(v), GRIS_CLARO), texto(x + ancho_o / 2, Y(v) - 14, mil(v), "axis", ancla="middle")]
        for k, parte in enumerate(nombre.split("\n")):
            el.append(texto(x + ancho_o / 2, 536 + k * 30, parte, "micro", ancla="middle"))
    el.append(texto(90, Y(v_r) - 14, f"{nombre_r}: {mil(v_r)}", "label-strong", color_r))
    return svg(fin + 20, 600, "Dinero en desarrollo de la mejor regla, el árbol, el bosque y XGBoost, con la logística como referencia.", el)


# Evaluación: la ventaja de cada mes de prueba contra la meta fijada antes de la prueba
def metas(grupos, dominio=(0, 1.0)):
    """grupos: (nombre, meta, [(mes, rel, (lo, hi))]). Punto = ventaja medida; barra = intervalo de 95%; trazos = meta.
    Una meta se cumple si la ventaja llega a la meta y el intervalo queda arriba de cero."""
    X = escala(dominio, (130, 740))
    marcas = [v for v in (0, .2, .4, .6, .8, 1.0) if dominio[0] <= v <= dominio[1]]
    xv, xc = 930, 1030
    el = [texto(xv, 30, "Ventaja medida", "micro", ancla="end"), texto(xc, 30, "Cumple", "micro", ancla="middle")]
    fondo, y = [], 30
    for nombre, meta, filas in grupos:
        el += [texto(0, y + 46, nombre, "heading"), texto(X(meta) + 10, y + 84, f"meta {pct(meta)}", "label-strong", NARANJA)]
        top, y = y + 94, y + 94
        for mes, rel, (lo, hi) in filas:
            yc = y + 38
            el += [texto(0, yc + 9, mes, "label"),
                   f'<rect x="{X(lo):.1f}" y="{yc - 9:.1f}" width="{X(hi) - X(lo):.1f}" height="18" rx="9" fill="{AZUL_MEDIO}"/>',
                   punto(X(rel), yc, 14, AZUL, "#fff", 3),
                   texto(xv, yc + 6, pct(rel), "data", AZUL, "end"), texto(xv, yc + 36, f"{pct(lo)} a {pct(hi)}", "micro", ancla="end")]
            if rel >= meta and lo > 0:
                el.append(trazo([(xc - 16, yc), (xc - 4, yc + 12), (xc + 18, yc - 14)], AZUL, 6))
            else:
                el += [linea(xc - 13, yc - 13, xc + 13, yc + 13, NARANJA, 6), linea(xc - 13, yc + 13, xc + 13, yc - 13, NARANJA, 6)]
            y += 84
        fondo += [linea(X(v), top, X(v), y, "#a5aebc" if v == 0 else LINEA, 2) for v in marcas]
        el.append(linea(X(meta), top - 30, X(meta), y, NARANJA, 3, True))
        y += 10
    el = fondo + [texto(X(v), y + 22, pct(v) if v else "0", "axis", ancla="middle") for v in marcas] + el
    y += 82
    el += [punto(X(0) + 14, y - 8, 14, AZUL, "#fff", 3), texto(X(0) + 40, y, "ventaja medida", "micro"),
           f'<rect x="{X(0) + 250:.1f}" y="{y - 17:.1f}" width="56" height="18" rx="9" fill="{AZUL_MEDIO}"/>',
           texto(X(0) + 320, y, "intervalo de 95%", "micro"),
           linea(X(0) + 530, y - 8, X(0) + 566, y - 8, NARANJA, 3, True), texto(X(0) + 578, y, "meta", "micro")]
    return svg(1080, y + 14, "Ventaja del modelo por mes de prueba, con intervalos de 95% y la meta fijada antes de la prueba.", el)


AZUL_PALIDO, NARANJA_PALIDO = "#e3f0fa", "#fbe8df"


def _caja(x, y, ancho, alto, fondo, rx=14):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{ancho:.1f}" height="{alto:.1f}" rx="{rx}" fill="{fondo}"/>'


def _flecha(puntos, color=GRIS_MEDIO, grosor=3):
    """Polilínea con punta de flecha en el último punto."""
    (x1, y1), (x2, y2) = puntos[-2], puntos[-1]
    a = math.atan2(y2 - y1, x2 - x1)
    base = (x2 - 12 * math.cos(a), y2 - 12 * math.sin(a))
    punta = [(x2, y2), (x2 - 18 * math.cos(a - .45), y2 - 18 * math.sin(a - .45)), (x2 - 18 * math.cos(a + .45), y2 - 18 * math.sin(a + .45))]
    return trazo(list(puntos[:-1]) + [base], color, grosor) + trazo(punta, color, 1, color, True)


# Negocio: la decisión de cada noche como árbol; cada resultado dice lo que cuesta
def decision_arbol(pagos, cupo):
    el = [texto(0, 28, "Cada noche", "micro"), texto(300, 28, "Decide el equipo de riesgo", "micro"), texto(640, 28, "Qué pasa", "micro")]
    el += [_caja(0, 170, 250, 180, HIELO), texto(28, 236, "Pagos del día", "label"), texto(28, 306, f"≈{pagos:,}", "chart-big")]
    el += [_flecha([(250, 260), (275, 260), (275, 110), (300, 110)]), _flecha([(275, 260), (275, 410), (300, 410)])]
    el += [_caja(300, 55, 290, 110, AZUL_PALIDO), texto(328, 100, "Revisar", "label-strong", AZUL),
           texto(328, 138, f"{cupo} al día: {cupo / pagos:.0%} de los pagos", "micro"),
           _caja(300, 355, 290, 110, HIELO), texto(328, 400, "Dejar pasar", "label-strong"),
           texto(328, 438, f"≈{pagos - cupo:,} al día", "micro")]
    el += [_flecha([(590, 110), (640, 110)]),
           texto(668, 100, "Si es fraude, se detiene", "label-strong"), texto(668, 138, "costo: la revisión", "micro")]
    el += [_flecha([(590, 410), (612, 410), (612, 330), (640, 330)]), _flecha([(612, 410), (612, 455), (640, 455)]),
           texto(668, 322, "Si es legítimo: nada", "label-strong"), texto(668, 358, "costo: 0", "micro"),
           _caja(640, 400, 400, 112, NARANJA_PALIDO, 10),
           texto(668, 446, "Si es fraude: contracargo", "label-strong", NARANJA), texto(668, 484, "costo: todo el monto del pago", "micro", NARANJA)]
    return svg(1040, 520, "La decisión de cada noche: revisar o dejar pasar cada pago, y lo que cuesta cada resultado.", el)


# Negocio: lo que cuesta un fraude que pasa, en un día típico y uno por uno
def fraude_montos(c):
    X = escala((-1, 4), (0, 600))
    el = [texto(0, 30, "Lo que cuesta el fraude que pasa", "heading"),
          texto(0, 112, f"≈{c['usd_dia'] / 1e3:.0f} mil USD", "chart-big", NARANJA),
          texto(0, 148, f"al día, en unos {c['fraudes_dia']:.0f} fraudes (mediana de los días 1–120)", "micro"),
          texto(0, 222, "Monto de cada fraude, USD", "label-strong")]
    tope = max(c["fraudes"])
    for a, b, n in zip(c["bordes"], c["bordes"][1:], c["fraudes"]):
        h = 150 * n / tope
        el.append(rect(X(math.log10(a)) + 1, 400 - h, X(math.log10(b)) - X(math.log10(a)) - 2, h, NARANJA_CLARO))
    el.append(linea(0, 400, 600, 400, "#a5aebc", 2))
    for v, t in ((1, "1"), (10, "10"), (100, "100"), (1000, "1,000")):
        el.append(texto(X(math.log10(v)), 432, t, "axis", ancla="middle"))
    for i, (nombre, v) in enumerate((("mínimo", c["minimo"]), ("mediana", c["mediana"]), ("promedio", c["promedio"]), ("máximo", c["maximo"]))):
        x = i * 152
        el += [texto(x, 482, nombre, "micro"), texto(x, 516, f"{v:,.2f}" if v < 1 else f"{v:,.0f}", "data", NARANJA if nombre == "promedio" else NEGRO)]
    return svg(600, 526, "Lo que cuesta el fraude que pasa: total de un día típico y distribución del monto de cada fraude.", el)


# Datos: matriz de dispersión de cuatro variables, fraude contra legítimo (puntos: muestra al azar; diagonal: todos los pagos)
def matriz_dispersion(M, n):
    V = M["variables"]
    k, ML, MT, CW, CH, g = len(V), 96, 64, 200, 132, 14
    cx = lambda j: ML + j * (CW + g)  # noqa: E731
    cy = lambda i: MT + i * (CH + g)  # noqa: E731
    fondo = cy(k) - g
    ex = [escala(v["rango"], (0, CW)) for v in V]
    ey = [escala(v["rango"], (0, CH)) for v in V]
    el = []
    for i in range(k):
        for j in range(i + 1):
            px, py = cx(j), cy(i)
            el.append(f'<rect x="{px}" y="{py}" width="{CW}" height="{CH}" fill="#fff" stroke="{LINEA}" stroke-width="2"/>')
            if i == j:  # histograma de cada clase; altura en raíz cuadrada para que el pico de un valor no aplaste al resto
                v = V[i]
                tope = max(max(v["fraude"]), max(v["legitimo"]))
                alto = lambda d: (CH - 14) * math.sqrt(d / tope)  # noqa: E731
                for a, b, d in zip(v["bordes"], v["bordes"][1:], v["legitimo"]):
                    el.append(rect(px + ex[i](a) + 1, py + CH - alto(d), ex[i](b) - ex[i](a) - 2, alto(d), GRIS_CLARO))
                pts = [(px + ex[i](v["bordes"][0]), py + CH)]
                for a, b, d in zip(v["bordes"], v["bordes"][1:], v["fraude"]):
                    pts += [(px + ex[i](a), py + CH - alto(d)), (px + ex[i](b), py + CH - alto(d))]
                el.append(trazo(pts + [(px + ex[i](v["bordes"][-1]), py + CH)], NARANJA, 3))
                continue
            for clase, color, op in (("legitimo", GRIS_MEDIO, .45), ("fraude", NARANJA, .65)):
                puntos = "".join(f'<circle cx="{px + ex[j](f[j]):.1f}" cy="{py + CH - ey[i](f[i]):.1f}" r="2.6"/>'
                                 for f in M["muestra"][clase] if f[i] is not None and f[j] is not None)
                el.append(f'<g fill="{color}" fill-opacity="{op}">{puntos}</g>')
    nombres = {"Desde su pago anterior": ("Desde su pago", "anterior")}
    for i, v in enumerate(V):
        partes = nombres.get(v["nombre"], (v["nombre"],))
        for r, parte in enumerate(partes):  # el nombre va sobre su histograma; arriba de la diagonal no hay celdas
            el.append(texto(cx(i), cy(i) - 14 - 32 * (len(partes) - 1 - r), parte, "label-strong"))
        for a, t, *solo in v["marcas"]:  # "solo y": la marca no cabe en el eje de abajo
            if not solo:
                el.append(texto(cx(i) + ex[i](a), fondo + 30, t, "tick", ancla="middle"))
            if i:
                el.append(texto(ML - 10, cy(i) + CH - ey[i](a) + 6, t, "tick", ancla="end"))
    lx = cx(1)
    el += [punto(lx + 9, 22, 9, NARANJA, "none", 0), texto(lx + 28, 30, "Fraude", "label"),
           punto(lx + 149, 22, 9, GRIS_MEDIO, "none", 0), texto(lx + 168, 30, "Legítimo", "label"),
           texto(lx, 76, f"Puntos: {n} pagos al azar de cada clase.", "micro"),
           texto(lx, 106, "Diagonal: todos los pagos, sin extremos.", "micro")]
    return svg(cx(k) - g + 4, fondo + 44, "Matriz de dispersión de cuatro variables para pagos fraudulentos y legítimos.", el)


# Datos: qué parte del fraude y de los legítimos cae en cada categoría
def clases_fraude(paneles):
    el, ancho, paso_x, base, paso_y, xb = [], 390, 425, 112, 70, 212
    X = escala((0, .8), (0, 130))
    alto_max = 0
    for p, panel in enumerate(paneles):
        x0 = p * paso_x
        filas = [f for f in panel["filas"] if max(f["fraude"], f["legitimo"]) >= .01]
        top = max(filas, key=lambda f: f["tasa"])
        el += [texto(x0, 30, panel["nombre"], "heading"),
               texto(x0, 66, f"{top['nombre']}: {top['tasa'] * 100:.1f}% son fraude", "micro", NARANJA)]
        for r, f in enumerate(filas):
            y = base + r * paso_y
            el += [texto(x0, y + 32, f["nombre"], "label-strong" if f is top else "label"),
                   rect(x0 + xb, y, X(f["fraude"]), 22, NARANJA),
                   texto(x0 + xb + 8 + X(f["fraude"]), y + 18, f"{f['fraude'] * 100:.0f}%", "tick", NARANJA),
                   rect(x0 + xb, y + 26, X(f["legitimo"]), 22, GRIS_CLARO),
                   texto(x0 + xb + 8 + X(f["legitimo"]), y + 44, f"{f['legitimo'] * 100:.0f}%", "tick", GRIS)]
        alto_max = max(alto_max, base + len(filas) * paso_y)
    el += leyenda(0, alto_max + 30, [("de los fraudes", NARANJA, "caja"), ("de los legítimos", GRIS_CLARO, "caja")], 250)
    return svg(len(paneles) * paso_x - (paso_x - ancho), alto_max + 40, "Distribución de pagos fraudulentos y legítimos en cuatro variables categóricas.", el)


# Negocio: un día de pagos por probabilidad y monto; la cola son los 60 de mayor fraude esperado
def cola_dia(dia, casos):
    """casos: (probabilidad, monto, renglón 1, renglón 2, color), señalados con un anillo y una nota a la derecha."""
    X = escala((-4, 0), (130, 1000))
    Y = escala((0, 4), (560, 80))
    lx = lambda p: X(math.log10(min(max(p, 1e-4), 1)))  # noqa: E731
    ly = lambda m: Y(math.log10(min(max(m, 1), 1e4)))  # noqa: E731
    c = dia["corte"]
    p_lo = c / 1e4
    el = [texto(130, 30, f"Los {dia['pagos']:,} pagos del día {dia['dia']}, uno por punto", "heading"),
          trazo([(lx(p_lo), ly(1e4)), (lx(1), ly(1e4)), (lx(1), ly(c))], "none", 0, AZUL_PALIDO, True)]
    for d in range(-4, 1):
        el += [linea(X(d), 80, X(d), 560), texto(X(d), 596, ["0.01%", "0.1%", "1%", "10%", "100%"][d + 4], "axis", ancla="middle")]
    for d in range(0, 5):
        el += [linea(130, Y(d), 1000, Y(d)), texto(116, Y(d) + 7, f"{10 ** d:,}", "axis", ancla="end")]
    pts = dia["puntos"]
    el += [punto(lx(p), ly(m), 3.2, GRIS_MEDIO, "none", 0, .35) for p, m, f, r in pts if not f and not r]
    el += [punto(lx(p), ly(m), 5, NARANJA, "#fff", 1) for p, m, f, r in pts if f and not r]
    el += [punto(lx(p), ly(m), 7, AZUL if f else "#9cc3e0", AZUL if f else "#fff", 2) for p, m, f, r in pts if r]
    el += [linea(lx(p_lo), ly(1e4), lx(1), ly(c), AZUL, 3, True),
           texto(lx(p_lo) - 16, ly(1e4) + 48, f"probabilidad × monto = {c:,.0f} USD", "label-strong", AZUL, "end"),
           texto(lx(p_lo) - 16, ly(1e4) + 78, "arriba de la línea: los 60 revisados", "micro", AZUL, "end"),
           texto(0, 50, "USD", "axis"), texto(565, 640, "Probabilidad de fraude estimada por el modelo", "label", ancla="middle")]
    xr = 1070
    for i, (p, m, r1, r2, color) in enumerate(casos):
        yc = 190 + i * 230
        px, py = lx(p), ly(m)
        el += [linea(px + 16, py, xr - 14, yc - 12, color, 2), punto(px, py, 16, "none", color, 4),
               texto(xr, yc - 20, r1, "label-strong"), texto(xr, yc + 24, r2, "data", color)]
    el += leyenda(130, 690, [("revisado: fraude", AZUL, "punto"), ("revisado: legítimo", "#9cc3e0", "punto"),
                             ("fraude que pasa", NARANJA, "punto"), ("legítimo", GRIS_CLARO, "punto")])
    return svg(1640, 704, "Pagos de un día por probabilidad estimada y monto; se revisan los 60 con más fraude esperado.", el)


# Evaluación: el mejor AUC no es el que más dinero detiene
def auc_prueba(puntos, enlace=None):
    """puntos: (nombre, auc, usd, color, lado de la etiqueta). enlace: dos nombres que se unen con trazos (el mismo modelo, otro orden)."""
    X = escala((.6, .9), (130, 1040))
    Y = escala((200e3, 460e3), (560, 70))
    el = [texto(130, 26, "Fraude detenido en la prueba, mil USD", "heading")]
    for v in range(200_000, 450_001, 50_000):
        el += [linea(130, Y(v), 1040, Y(v)), texto(116, Y(v) + 7, mil(v), "axis", ancla="end")]
    for a in (.6, .65, .7, .75, .8, .85, .9):
        el.append(texto(X(a), 596, f"{a:.2f}", "axis", ancla="middle"))
    pos = {n: (X(a), Y(u)) for n, a, u, _, _ in puntos}
    if enlace:
        (xa, ya), (xb, yb) = pos[enlace[0]], pos[enlace[1]]
        el.append(linea(xa, ya, xb, yb, GRIS_MEDIO, 2, True))
    for nombre, auc, usd, color, lado in puntos:
        x, y = pos[nombre]
        dx, an = (-26, "end") if lado == "izq" else (26, "start")
        el += [punto(x, y, 15, color), texto(x + dx, y - 4, nombre, "label-strong", color, an),
               texto(x + dx, y + 28, f"AUC {auc:.2f} · {mil(usd)} mil USD", "micro", ancla=an)]
    el.append(texto(585, 640, "ROC-AUC en la prueba", "label", ancla="middle"))
    return svg(1080, 656, "ROC-AUC contra dólares de fraude detenido en la prueba, para cada política con 60 revisiones por día.", el)


# Evaluación: ganancia acumulada en dólares, en la zona donde se decide el cupo
def ganancia_cola(series, cupo, xmax=.2):
    """series: dicts nombre, color, fraccion, usd. Marca el cupo de 60 por día y la línea del azar."""
    X = escala((0, xmax), (110, 1000))
    Y = escala((0, 1), (520, 60))
    el = [texto(110, 22, "Parte del fraude en dólares que entra a la cola", "heading")]
    for v in (0, .2, .4, .6, .8, 1):
        el += [linea(110, Y(v), 1000, Y(v), "#a5aebc" if v == 0 else LINEA, 2), texto(98, Y(v) + 7, f"{v * 100:.0f}%", "axis", ancla="end")]
    for v in (0, .05, .1, .15, .2):
        if v <= xmax:
            el.append(texto(X(v), 556, f"{v * 100:.0f}%", "axis", ancla="middle"))
    el += [linea(X(0), Y(0), X(xmax), Y(xmax), GRIS_MEDIO, 3, True), texto(X(xmax) - 6, Y(xmax) - 16, "al azar", "label", GRIS, "end"),
           linea(X(cupo), 60, X(cupo), 520, NARANJA, 3, True)]
    for i, s in list(enumerate(series))[::-1]:
        pts = [(X(f), Y(v)) for f, v in zip(s["fraccion"], s["usd"]) if f <= xmax + 1e-9]
        el += [trazo(pts, s["color"], 5),
               texto(pts[-1][0] - 6, pts[-1][1] + (-18 if i == 0 else 42), s["nombre"], "label-strong", s["color"], "end", halo=True)]
    for s in series:
        v = s.get("cola", _interp(cupo, s["fraccion"], s["usd"]))  # la cola real de 60 por día, si se conoce
        el += [punto(X(cupo), Y(v), 11, s["color"]), texto(X(cupo) + 20, Y(v) + 10, f"{v * 100:.0f}%", "data", s["color"], halo=True)]
    el += [punto(X(cupo), Y(cupo), 8, GRIS_MEDIO), texto(X(cupo) + 18, Y(cupo) - 10, f"{cupo * 100:.0f}%", "label", GRIS, halo=True),
           texto(X(cupo) - 10, 92, "60 al día", "label-strong", NARANJA, "end", halo=True)]
    el.append(texto(555, 600, "Pagos revisados de cada día, en el orden de cada política", "label", ancla="middle"))
    return svg(1080, 614, "Parte del fraude en dólares capturado según los pagos revisados, para el modelo, la regla y el azar.", el)


def _interp(x, xs, ys):
    for (a, ya), (b, yb) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
        if a <= x <= b:
            return ya + (yb - ya) * (x - a) / (b - a)
    return ys[-1]


# Negocio: curva de beneficio contra el número de revisiones por día, para varios costos por revisión
def beneficio_cupo(series, cupo, kmax=500, ymin=-200e3, ymax=600e3):
    """series: dicts costo, color, puntos [(revisiones por día, neto USD)], k (cupo elegido en desarrollo) y neto (su neto en la prueba)."""
    X = escala((0, kmax), (120, 1040))
    Y = escala((ymin, ymax), (520, 70))
    el = [texto(120, 30, "Beneficio neto en la prueba según las revisiones por día", "heading"), texto(120, 62, "mil USD", "micro")]
    for v in range(int(ymin), int(ymax) + 1, 200_000):
        el += [linea(120, Y(v), 1040, Y(v), "#a5aebc" if v == 0 else LINEA, 2), texto(108, Y(v) + 7, mil(v), "axis", ancla="end")]
    for k in range(0, kmax + 1, 100):
        el.append(texto(X(k), 556, k, "axis", ancla="middle"))
    el += [linea(X(cupo), 70, X(cupo), 520, NARANJA, 3, True), texto(X(cupo) + 10, 96, f"hoy: {cupo}", "label-strong", NARANJA)]
    for s in series:
        pts = []
        for k, n in s["puntos"]:
            if k > kmax or n < ymin:
                break
            pts.append((X(k), Y(n)))
        el.append(trazo(pts, s["color"], 4))
        fin_x, fin_y = pts[-1]
        dentro = fin_x > 1000
        el.append(texto(fin_x - 6 if dentro else fin_x + 12, fin_y + 40 if dentro else fin_y - 14, f"{s['costo']} USD por revisión",
                        "label-strong", s["color"], "end" if dentro else "start", halo=True))
    for s in series:
        el += [punto(X(s["k"]), Y(s["neto"]), 11, s["color"]),
               texto(X(s["k"]), Y(s["neto"]) - 22, f"{s['k']}", "label-strong", s["color"], "middle", halo=True)]
    el.append(texto(580, 600, "Revisiones por día", "label", ancla="middle"))
    el += leyenda(120, 650, [("mejor cupo según el desarrollo", GRIS_MEDIO, "punto"), ("cupo actual", NARANJA, "trazos")])
    return svg(1080, 664, "Beneficio neto en la prueba según las revisiones por día, para tres costos por revisión.", el)


# Evaluación: lo que se gana donde se elige no se repite en días que la búsqueda no vio
def espejismo(filas, dominio=(-.08, .08)):
    """filas: (nombre, sub, rel, color), una columna cada una."""
    Y = escala(dominio, (500, 100))
    ancho, paso, x0 = 280, 460, 190
    el = [texto(0, 30, "Cambio en el fraude detenido con las variables nuevas", "heading")]
    for t in (-.05, 0, .05):
        el += [linea(120, Y(t), x0 + (len(filas) - 1) * paso + ancho + 70, Y(t), NEGRO if t == 0 else LINEA, 3 if t == 0 else 2),
               texto(104, Y(t) + 7, "0" if t == 0 else f"{t * 100:+.0f}%".replace("-", "−"), "axis", ancla="end")]
    for i, (nombre, sub, rel, color) in enumerate(filas):
        x = x0 + i * paso
        xc = x + ancho / 2
        el += [rect(x, min(Y(rel), Y(0)), ancho, abs(Y(0) - Y(rel)), color),
               texto(xc, Y(rel) - 22 if rel >= 0 else Y(rel) + 64, pct(rel, d=1), "chart-big", color, "middle"),
               texto(xc, 580, nombre, "label-strong", ancla="middle"), texto(xc, 616, sub, "micro", ancla="middle")]
    return svg(1080, 630, "Cambio en el fraude detenido con las variables nuevas: donde se eligieron y en días que la búsqueda no vio.", el)


# Preparación: cómo se arma el cliente con un ejemplo real, y lo que revela su historial
def cliente_armado(ejemplo, clientes, tarjetas, cats, promedio, extra):
    """ejemplo: dict card1, addr1 y filas (día, monto, D1, alta, fraude); cats: (nombre corto, tasa, pagos)."""
    el = [texto(0, 30, "Seis pagos reales con la misma tarjeta y dirección", "heading"),
          texto(0, 66, f"card1 = {ejemplo['card1']}, addr1 = {ejemplo['addr1']}; D1 = días desde el alta de la cuenta.", "micro"),
          texto(0, 96, "La fecha de alta (día − D1) los separa en dos clientes.", "micro")]
    xs = dict(dia=96, monto=270, d1=390, alta=600, cliente=660, res=860)
    yh = 150
    el += [texto(xs["dia"], yh, "Día", "micro", ancla="end"), texto(xs["monto"], yh, "Monto, USD", "micro", ancla="end"),
           texto(xs["d1"], yh, "D1", "micro", ancla="end"), texto(xs["alta"], yh, "Alta = día − D1", "micro", ancla="end"),
           texto(xs["cliente"], yh, "Cliente", "micro"), texto(xs["res"], yh, "Resultado", "micro"), linea(0, yh + 16, 1000, yh + 16, "#a5aebc", 2)]
    altas = sorted({f[3] for f in ejemplo["filas"]})
    tono = {altas[0]: (AZUL, "#fff", "A"), altas[1]: (AZUL_MEDIO, NEGRO, "B")}
    for r, (dia, monto, d1, alta, fraude) in enumerate(ejemplo["filas"]):
        y = yh + 56 + r * 50
        fondo, tinta, letra = tono[alta]
        el += [texto(xs["dia"], y, dia, "label", ancla="end"), texto(xs["monto"], y, f"{monto:,.2f}".removesuffix(".00"), "label", ancla="end"),
               texto(xs["d1"], y, d1, "label", ancla="end"), texto(xs["alta"], y, f"día {alta}", "label-strong", AZUL if letra == "A" else GRIS, "end"),
               _caja(xs["cliente"], y - 28, 150, 38, fondo, 19), texto(xs["cliente"] + 75, y - 2, f"Cliente {letra}", "label-strong", tinta, "middle"),
               texto(xs["res"], y, "fraude" if fraude else "legítimo", "label-strong" if fraude else "label", NARANJA if fraude else GRIS)]
    y = yh + 56 + len(ejemplo["filas"]) * 50 - 22
    el += [linea(0, y, 1000, y, "#a5aebc", 2),
           texto(0, y + 58, f"{clientes:,} clientes", "data", AZUL), texto(300, y + 58, f"de {tarjetas:,} tarjetas", "label"),
           texto(0, y + 96, "Por cliente, y solo con sus pagos anteriores: cuántos pagos lleva,", "micro"),
           texto(0, y + 124, "hace cuánto pagó y si el monto es raro para él.", "micro")]
    xb, xr = 1276, 1100
    Xb = escala((0, .07), (xb, xb + 290))
    el += [texto(xr, 30, "Lo que revela su historial", "heading"), texto(xr, 66, "Tasa de fraude según el tiempo desde su pago anterior", "micro"),
           linea(Xb(promedio), 112, Xb(promedio), 400, NARANJA, 3, True),
           texto(Xb(promedio), 428, f"promedio {promedio * 100:.1f}%", "micro", NARANJA, "middle")]
    for i, (nombre, tasa, _) in enumerate(cats):
        y = 120 + i * 56
        alto = tasa > promedio
        color = AZUL if alto else GRIS_MEDIO
        el += [texto(xr, y + 27, nombre, "label-strong" if alto else "label"), rect(xb, y, Xb(tasa) - xb, 36, color),
               texto(1664, y + 28, f"{tasa * 100:.1f}%", "label-strong", color, "end")]
    el += [linea(xr, 460, 1664, 460), texto(xr, 530, f"{mil(extra, True)} mil USD", "chart-big", AZUL),
           texto(xr, 570, "más fraude detenido en desarrollo", "label"), texto(xr, 602, "al sumar el historial del cliente", "micro")]
    return svg(1664, 612, "Cómo se arma el cliente con seis pagos reales y la tasa de fraude según el tiempo desde su pago anterior.", el)


# Despliegue: la cola que recibe el equipo una noche, ordenada por fraude esperado
def cola_noche(dia, filas, colas):
    """filas: (lugar, monto, probabilidad, fraude) de la cola del modelo, en orden; None marca los renglones omitidos.
    colas: (nombre, fraudes, usd, color) de cada cola esa misma noche."""
    xl, xm, xp, xe, xb, xr, ancho_b = 36, 236, 430, 556, 576, 790, 170
    tope = max(f[1] * f[2] for f in filas if f)
    yh = 112
    el = [texto(0, 30, f"Ejemplo: la lista de la noche del día {dia['dia']}", "heading"),
          texto(0, 66, f"Los 60 pagos con mayor fraude esperado, de {dia['pagos']:,}", "micro"),
          texto(xl, yh, "#", "micro", ancla="end"), texto(xm, yh, "Monto, USD", "micro", ancla="end"),
          texto(xp, yh, "Probabilidad", "micro", ancla="end"), texto(xe - 90, yh, "Fraude esperado, USD", "micro"),
          texto(xr, yh, "Resultado real", "micro"), linea(0, yh + 18, 960, yh + 18, "#a5aebc", 2)]
    y = yh + 44
    for i, f in enumerate(filas):
        if f is None:
            omitidos = filas[i + 1][0] - filas[i - 1][0] - 1
            el += [texto(xl, y - 6, "⋮", "label", GRIS, "end"), texto(xl + 28, y - 6, f"{omitidos} pagos más", "micro")]
            y += 40
            continue
        lugar, m, p, fraude = f
        e = m * p
        el += [texto(xl, y, lugar, "axis", ancla="end"), texto(xm, y, f"{m:,.0f}", "label", ancla="end"),
               texto(xp, y, f"{p:.0%}", "label", ancla="end"), texto(xe, y, f"{e:,.0f}", "label-strong", ancla="end"),
               rect(xb, y - 20, ancho_b * e / tope, 22, AZUL_MEDIO),
               punto(xr + 9, y - 8, 9, AZUL if fraude else GRIS_CLARO, "none", 0),
               texto(xr + 28, y, "fraude" if fraude else "legítimo", "label-strong" if fraude else "label", AZUL if fraude else GRIS)]
        y += 44
    y -= 20
    el.append(linea(0, y, 960, y, "#a5aebc", 2))
    y += 50
    el.append(texto(0, y, f"Fraude detenido esa noche, con {filas[-1][0]} revisiones", "micro"))
    mx = max(u for _, _, u, _ in colas)
    for nombre, fraudes, usd, color in colas:
        y += 18
        w = 330 * usd / mx
        el += [texto(0, y + 25, nombre, "label-strong", color), rect(190, y, w, 32, color),
               texto(190 + w + 16, y + 26, f"{fraudes} fraudes · {usd:,.0f} USD", "label", color)]
        y += 32
    return svg(960, y + 8, f"La cola de 60 pagos que recibe el equipo la noche del día {dia['dia']}, con el resultado a los 30 días.", el)


# Despliegue: el ciclo de operación, de la lista de cada noche al reentrenamiento semanal, con su respaldo
def operacion(cupo, margen):
    pasos = [("El modelo ordena los pagos", "de cada noche por fraude esperado"),
             (f"El equipo revisa los primeros {cupo}", "el mismo equipo y el mismo cupo de hoy"),
             (f"A los {margen} días llega la etiqueta", "el contracargo dice qué pagos eran fraude"),
             ("Cada semana se reentrena", "con los pagos que ya tienen etiqueta")]
    xc, x0, y0, paso = 58, 112, 120, 112
    ys = [y0 + i * paso for i in range(len(pasos))]
    el = [texto(0, 30, "Cómo opera", "heading"), linea(xc, ys[0], xc, ys[-1], GRIS_CLARO, 4),
          _flecha([(xc - 26, ys[-1]), (12, ys[-1]), (12, ys[0]), (xc - 28, ys[0])], GRIS_MEDIO, 3)]
    for i, ((fuerte, detalle), y) in enumerate(zip(pasos, ys)):
        el += [punto(xc, y, 26, AZUL, "#fff", 4), texto(xc, y + 10, i + 1, "label-strong", "#fff", "middle"),
               texto(x0, y - 4, fuerte, "label-strong"), texto(x0, y + 28, detalle, "micro")]
    yr = ys[-1] + 84
    el += [_caja(0, yr, 620, 124, NARANJA_PALIDO, 12), texto(28, yr + 46, "Respaldo", "label-strong", NARANJA),
           texto(28, yr + 80, "Si dos semanas seguidas detiene menos que la", "micro", NEGRO),
           texto(28, yr + 108, "regla, se vuelve a la regla.", "micro", NEGRO)]
    return svg(620, yr + 128, "Ciclo de operación: cada noche la lista, a los 30 días la etiqueta, cada semana el reentrenamiento.", el)


# Cierre: el fraude detenido se acumula noche a noche en los dos meses de prueba
def acumulado(dias, modelo, regla, otras, inicio_mes2, gana):
    """modelo, regla: (nombre, [usd por día], color), con la brecha sombreada; otras: (nombre, [usd por día], color, trazos)."""
    suma = lambda v: [sum(v[:i + 1]) for i in range(len(v))]  # noqa: E731
    tope = 450e3
    X = escala((dias[0], dias[-1]), (100, 800))
    Y = escala((0, tope), (560, 150))
    (n_m, v_m, c_m), (n_r, v_r, c_r) = modelo, regla
    a_m, a_r = suma(v_m), suma(v_r)
    resto = [(n, suma(v), c, t) for n, v, c, t in otras]
    assert max(a_m + [a[-1] for _, a, _, _ in resto]) < tope
    el = [texto(0, 30, "Fraude detenido acumulado en la prueba, mil USD", "heading"),
          texto(0, 66, f"El modelo detiene más que la regla en {gana} de los {len(dias)} días", "micro")]
    el += leyenda(0, 116, [(n_m, c_m, "linea"), (n_r, c_r, "linea")] + [(n, c, "trazos" if t else "linea") for n, _, c, t in resto])
    for v in range(0, int(tope), 100_000):
        el += [linea(100, Y(v), 800, Y(v), "#a5aebc" if v == 0 else LINEA, 2), texto(86, Y(v) + 7, mil(v), "axis", ancla="end")]
    xm = X(inicio_mes2 - .5)
    el.append(linea(xm, 150, xm, 560, GRIS_CLARO, 2, True))
    for d in (dias[0], inicio_mes2, dias[-1]):
        el.append(texto(X(d), 596, d, "axis", ancla="middle"))
    el += [texto((X(dias[0]) + xm) / 2, 636, "Mes 1", "label", GRIS, "middle"), texto((xm + X(dias[-1])) / 2, 636, "Mes 2", "label", GRIS, "middle")]
    el.append(trazo([(X(d), Y(v)) for d, v in zip(dias, a_m)] + [(X(d), Y(v)) for d, v in zip(dias[::-1], a_r[::-1])],
                    "none", 0, AZUL_PALIDO, True))
    xe = X(dias[-1])
    for _, a, c, t in resto:
        el += [trazo([(X(d), Y(v)) for d, v in zip(dias, a)], c, 4, trazos=t), punto(xe, Y(a[-1]), 8, c),
               texto(xe + 20, Y(a[-1]) + 12, mil(a[-1]), "data", c)]
    for a, c in ((a_r, c_r), (a_m, c_m)):
        el += [trazo([(X(d), Y(v)) for d, v in zip(dias, a)], c, 5), punto(xe, Y(a[-1]), 9, c), texto(xe + 20, Y(a[-1]) + 12, mil(a[-1]), "data", c)]
    ym, yr = Y(a_m[-1]), Y(a_r[-1])
    el += [linea(902, ym, 902, yr, NEGRO, 2), linea(890, ym, 902, ym, NEGRO, 2), linea(890, yr, 902, yr, NEGRO, 2),
           texto(920, (ym + yr) / 2 + 12, mil(a_m[-1] - a_r[-1], True), "chart-big", AZUL),
           texto(922, (ym + yr) / 2 + 48, "mil USD", "micro")]
    return svg(1080, 650, "Fraude detenido acumulado día a día en los dos meses de prueba: modelo, logística, regla y revisión al azar.", el)


# Capítulo 7 del curso · curva de aprendizaje con parada temprana
def aprendizaje(entr, val, paso, mejor, protocolo):
    n = min(len(val), len(entr))
    xs = [i * paso for i in range(n)]
    xmax = xs[-1]
    val, entr = val[:n], entr[:n]
    lo = min(min(val), min(entr))
    hi = max(val[min(3, n - 1):] + entr[min(3, n - 1):])
    pad = (hi - lo) * .08
    Y = escala((lo - pad, hi + pad), (520, 80))
    X = escala((0, xmax), (130, 1040))
    el = [texto(130, 22, "Pérdida logarítmica según el número de árboles", "heading")]
    paso_y = (hi - lo + 2 * pad) / 5
    for j in range(6):
        v = lo - pad + j * paso_y
        el += [linea(130, Y(v), 1040, Y(v)), texto(118, Y(v) + 7, f"{v:.3f}", "axis", ancla="end")]
    paso_x = 250 if xmax <= 1500 else 500
    for v in range(0, int(xmax) + 1, paso_x):
        el.append(texto(X(v), 556, f"{v:,}", "axis", ancla="middle"))
    tope = hi + pad
    el += [trazo([(X(x), Y(min(v, tope))) for x, v in zip(xs, entr)], GRIS_MEDIO, 3),
           trazo([(X(x), Y(min(v, tope))) for x, v in zip(xs, val)], AZUL, 4)]
    lejos = abs(protocolo - mejor) > xmax * .25
    der = X(mejor) < 700
    el += [linea(X(mejor), 76, X(mejor), 520, AZUL, 3, True),
           texto(X(mejor) + (10 if der else -10), 64, f"parada temprana: {mejor:,} árboles", "label-strong", AZUL, "start" if der else "end")]
    if protocolo <= xmax:
        el += [linea(X(protocolo), 76, X(protocolo), 520, NARANJA, 3, True),
               texto(X(protocolo) + (10 if lejos and der else -10), 104, f"protocolo: {protocolo:,}", "label", NARANJA,
                     "start" if lejos and der else "end")]
    el.append(texto(585, 594, "Árboles (rondas de boosting)", "label", ancla="middle"))
    el += leyenda(130, 642, [("validación: últimos 10 días del entrenamiento", AZUL, "linea"), ("entrenamiento", GRIS_MEDIO, "linea")])
    return svg(1080, 656, "Curva de aprendizaje: pérdida logarítmica en entrenamiento y validación según el número de árboles.", el)
