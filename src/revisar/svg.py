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


def texto(x, y, contenido, clase="label", color=None, ancla="start", peso=None):
    estilo = (f"fill:{color};" if color else "") + (f"font-weight:{peso};" if peso else "")
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
def tiempo(dias):
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
    for a, b, nombre, color in ((1, 60, "Solo entrenamiento", GRIS), (61, 120, "Desarrollo: D1 y D2", AZUL_MEDIO),
                                (121, 182, "Prueba congelada: P1 y P2", AZUL)):
        el += [linea(X(a - .4), 40, X(b + .4), 40, color, 4), texto(X(a - .4), 26, nombre, "label-strong", NEGRO if color != AZUL else AZUL)]
    for d in (61, 91, 121, 152):
        el.append(linea(X(d - .5), 52, X(d - .5), 330, "#a5aebc", 2, True))
    for d in (1, 30, 60, 90, 120, 151, 182):
        el.append(texto(X(d), 364, d, "axis", ancla="middle"))
    el += [linea(X(120.6), 396, X(144.4), 396, VERDE, 5), texto(X(120.6), 430, "nunca leídos", "micro", VERDE),
           linea(X(144.6), 396, X(182.4), 396, NARANJA, 5), texto(X(182.4), 430, "ya usados por otro estudio", "micro", NARANJA, "end"),
           texto(X(1), 430, "día relativo", "micro"), texto(70, 70, "mil USD de fraude por día", "micro")]
    return svg(1680, 444, f"Dólares de fraude por día, días 1 a 182; máximo diario {tope:,.0f} USD.", el)


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
def intervalos(filas, dominio=(-.2, 1.6), alto=84):
    X = escala(dominio, (820, 1640))
    el = [texto(0, 40, "Comparador", "heading"), texto(500, 40, "P1 · P2", "heading"),
          texto(820, 40, "Ventaja del modelo en dólares de fraude, IC 95%", "heading"),
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
    el += leyenda(820, yb + 46, [("días 121–151 (P1)", AZUL_MEDIO, "punto"), ("días 152–182 (P2)", AZUL, "punto"),
                                 ("barra fijada antes", NARANJA, "trazos")], paso=None)
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
