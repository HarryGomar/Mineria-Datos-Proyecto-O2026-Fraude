"""Contenido de la presentación, con gráficas vectoriales. Todas las cifras se leen de resultados/.

La charla son 15 láminas: el resumen, las seis fases de CRISP-DM y la recomendación. El apéndice guarda el detalle
para las preguntas. figuras() entrega además las gráficas del reporte y del cuaderno, estén o no en una lámina.
"""
from __future__ import annotations

import csv
import json
import math

import numpy as np

from . import svg as G
from .deck import escribir, pagina
from .rutas import RAIZ, RESULTADOS

SALIDA = RAIZ / "presentacion" / "que-pagos-revisar.html"
GUION = RAIZ / "presentacion" / "guion.md"
APENDICE = "apendice appendix"
P = ("P1", "P2")
CHARLA = ("portada", "resumen", "decision", "matriz", "deciles", "cliente", "calendario", "modelos", "hipotesis", "metricas",
          "ganancia", "beneficio", "espejismo", "despliegue", "cierre")
ANEXO = ("crisp", "requisitos", "prueba", "intervalos", "robustez", "costo", "traza", "roc", "calibracion", "observado", "calidad",
         "catalogo", "candados", "ablacion", "regularizacion", "importancia", "aprendizaje", "validacion")
FASE = ("1 · Comprensión del negocio", "2 · Comprensión de los datos", "3 · Preparación de los datos", "4 · Modelado",
        "5 · Evaluación", "6 · Despliegue")
NOMBRE = {"XGB": "XGBoost", "ENS": "Ensamble XGBoost + bosque", "XGB_pond": "XGBoost ponderado por monto", "RF": "Bosque aleatorio",
          "MLP": "Red neuronal MLP", "CART": "Árbol CART", "ISO": "Bosque de aislamiento", "LOGIT": "Logística",
          "R_segmento": "Regla por segmento", "R_tarjeta": "Regla por tarjeta", "R_tabla": "Regla producto × monto",
          "R_monto": "Mayor monto primero", "R_velocidad": "Regla de velocidad", "R_correo": "Regla por correo"}
pct, mil = G.pct, G.mil
PALABRA = {3: "Tres", 4: "Cuatro", 5: "Cinco", 6: "Seis", 7: "Siete", 8: "Ocho", 9: "Nueve"}
GRUPO_CORTO = {"ventanas": "ventanas", "perfil": "perfil", "novedad": "novedad", "compartido": "compartido", "texto": "texto",
               "monto_fino": "forma del monto", "frecuencia": "frecuencia", "uid_fino": "cliente fino", "etiquetas": "contracargos"}
REPLICAS_ANEXO = 1000  # réplicas del bootstrap en scripts/06_variables.py y 07_anexo_prueba.py


def _j(n):
    return json.loads((RESULTADOS / n).read_text(encoding="utf-8"))


def _csv(n):
    with open(RESULTADOS / n, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ent(x):
    return f"{x:,.0f}"


def ic(par, d=1):
    return f"{pct(par[0], d=d)} a {pct(par[1], d=d)}"


def _y(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]


def _nombre(clave):
    base = clave.partition("|")[0]
    return "Logística" if base.startswith("LOGIT") else NOMBRE.get(base, base)


def _split(figura, aside, clase="split fill"):
    return f'<div class="{clase}"><figure>{figura}</figure><aside class="argument">{aside}</aside></div>'


def _tinte(v, tope=.6):
    if v <= 0:
        return "rgba(242,196,173,.65)"
    return f"rgba(125,190,228,{.08 + .34 * min(v / tope, 1):.3f})"


def _rangos(nums, pre=""):
    nums, out, i = sorted(set(nums)), [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out += [f"{pre}{nums[i]}–{pre}{nums[j]}"] if j - i >= 2 else [f"{pre}{n}" for n in nums[i:j + 1]]
        i = j + 1
    return out


def _lam(donde, *claves):
    """Números de lámina de cada clave, con rangos: 10–13, A1–A5."""
    v = [donde[c] for c in claves if c in donde]
    return ", ".join(_rangos([n for n in v if isinstance(n, int)]) + _rangos([int(n[1:]) for n in v if isinstance(n, str)], "A"))


def _construir():
    """(láminas en orden, {clave: svg}) con las cifras de resultados/."""
    S, R, X, PJ = _j("desarrollo_seleccion.json"), _j("prueba.json"), _j("exploracion.json"), _j("presentacion.json")
    L, CC = _j("lecciones.json"), _j("curvas_curso.json")
    VA, AX = _j("variables.json"), _j("anexo_prueba_variables.json")
    assert not VA["rapido"] and VA["elegidos"] == AX["elegidos"], "variables.json y el anexo de la prueba no corresponden"
    FINAL, REGLA, LOGIT, PUB = S["final"], S["mejor_regla"], S["mejor_logit"], "PUBLICADO"
    U, ve = R["umbrales"], R["veredicto"]
    C = {x: R[x]["contrastes"] for x in P}
    cr, cl, cp = ({x: C[x][k] for x in P} for k in (REGLA, LOGIT, PUB))
    usd = {x: R[x]["usd"] for x in P}
    tot = lambda k: usd["P1"][k] + usd["P2"][k]  # noqa: E731
    dias = {x: f"días {R[x]['dias'][0]}–{R[x]['dias'][1]}" for x in P}
    d_prueba = f"días {R['P1']['dias'][0]}–{R['P2']['dias'][1]}"
    d_desarrollo = f"días {S['bloques']['D1']['inicio']}–{S['bloques']['D2']['fin']}"
    un, ck = X["universo"], X["cliente"]
    dv = S["dolares"]
    total = lambda k: dv[k]["D1"] + dv[k]["D2"]  # noqa: E731
    replicas = len(_csv("bootstrap_P1.csv"))
    hip = (("H1", "H1_regla"), ("H2", "H2_logistica"), ("H3", "H3_publicado"))
    pasan = [h for h, k in hip if all(ve[x][k] for x in P)]
    margen, cupo = S["margen_dias"], S["K"]
    op, cv, dcl = CC["operacion"], CC["curvas"], CC["deciles"]
    dias_t = f"Días {CC['dias'][0]}–{CC['dias'][1]}"
    cst = {(f["costo"], f["recupera"]): f for f in L["costos"]}
    costos_t = (2, 5, 10, 20, 50, 100)
    neto = lambda f, k: f[k]["neto_prueba"]  # noqa: E731
    gana_c = sum(neto(cst[(c, r)], "modelo") > max(neto(cst[(c, r)], "logistica"), neto(cst[(c, r)], "regla")) for c in costos_t for r in (1.0, .5))
    k_de = {c: cst[(c, 1.0)]["modelo"]["K"] for c in (10, 20, 50)}
    donde = {k: i + 1 for i, k in enumerate(CHARLA)} | {k: f"A{i + 1}" for i, k in enumerate(ANEXO)}
    F, s = {}, {}

    def ap(titulo, contenido, pie, fase):
        return pagina(titulo, contenido, pie, APENDICE, f"Apéndice · {fase}")

    # ── Charla ────────────────────────────────────────────────────────────────────────────────────────────────────

    # Portada
    dia = PJ["dia"]
    total_pagos = sum(v[0] for v in PJ["dias"].values())
    s["portada"] = (
        '<section class="slide cover" data-title="Qué pagos revisar">' + G.portada(dia)
        + '<div><h1>Qué pagos<br>revisar</h1><p>Cada día caben 60 revisiones manuales de fraude. ¿Cuáles 60?</p>'
        f'<small>Minería de Datos · ITAM · Proyecto final · {ent(total_pagos)} pagos de comercio electrónico (IEEE-CIS, Vesta)</small></div>'
        f'<p class="map-note">Los {ent(dia["pagos"])} pagos del día {dia["dia"]}, en orden de llegada · Azul: los 60 que el modelo manda a revisión · '
        'Naranja: fraudes que no se revisan</p></section>')

    # Resumen: el valor del modelo en una gráfica
    extra = tot(FINAL) - tot(REGLA)
    F["resumen"] = G.resumen([("Mejor regla: la práctica actual", tot(REGLA), G.NARANJA), ("Logística regularizada", tot(LOGIT), G.VERDE),
                              ("Modelo: XGBoost, probabilidad × monto", tot(FINAL), G.AZUL)], tot("oraculo"), 0, 2)
    sobre_cero = all(C[x][k]["rel_ic95"][0] > 0 for x in P for k in (REGLA, LOGIT))
    s["resumen"] = pagina(
        f"Con las mismas 60 revisiones al día, el modelo atrapa {pct(extra / tot(REGLA), False)} más fraude",
        _split(F["resumen"],
               f'<p class="big">{mil(extra, True)} <span>mil USD</span></p>'
               f'<p class="sub">más fraude detenido antes del contracargo en {R["P1"]["n_dias"] + R["P2"]["n_dias"]} días de prueba</p>'
               '<div class="rule"><p><b>Gana en los dos meses</b></p>'
               f'<p>Contra la regla, {pct(cr["P1"]["rel"])} y {pct(cr["P2"]["rel"])}; contra la logística, {pct(cl["P1"]["rel"])} y {pct(cl["P2"]["rel"])}.'
               + (" Los cuatro intervalos de 95% quedan sobre cero." if sobre_cero else "") + "</p></div>"),
        f"Prueba: {d_prueba}, apartados hasta el final · Modelo, comparadores e hipótesis congelados antes de abrirlos · "
        "Dinero = monto de los fraudes que entran a la cola",
        fase="Resumen")

    # 1 · Negocio: la decisión
    F["decision"] = G.dia_decision(dia)
    s["decision"] = pagina(
        "La decisión: qué 60 pagos revisar cada día",
        f'<div class="split split-right fill"><aside class="argument"><p class="sub">Día {dia["dia"]} · {ent(dia["pagos"])} pagos</p>'
        f'<p class="big">60 <span>de {ent(dia["pagos"])}</span></p>'
        '<div class="rule"><p><b>Se revisan los 60 con mayor fraude esperado</b></p>'
        f'<p>Fraude esperado = probabilidad × monto. Ese día, el corte quedó en {dia["corte"]:,.0f} USD.</p></div>'
        f'</aside><figure>{F["decision"]}</figure></div>'
        '<div class="clock-line"><p><b>Quién</b><span>El equipo de riesgo del procesador de pagos</span></p>'
        '<p><b>Cuándo</b><span>Al cierre del día, con lo que se sabe hasta ese momento</span></p>'
        '<p><b>Opciones</b><span>Revisar el pago o dejarlo pasar</span></p>'
        f'<p><b>Recurso</b><span>60 revisiones al día: {pct(un["cupo_60_parte_pagos"], False, 1)} de los pagos</span></p></div>',
        "Vesta no publica su criterio actual; se representa con la mejor de seis reglas del desarrollo", fase=FASE[0])

    # 1 · Negocio: matriz de confusión en dólares
    mz = R["P2"]["matriz"]
    a, b = mz[REGLA], mz[FINAL]
    matriz = ('<table class="matrix dinero"><thead><tr><th scope="col">Días 152–182</th><th scope="col">El pago es fraude</th>'
              '<th scope="col">El pago es legítimo</th></tr></thead><tbody>'
              f'<tr><th scope="row">Se revisa</th><td class="focus-azul" style="--cell:rgba(125,190,228,.42)">'
              f'<b>{mil(a["revisado_fraude"]["usd"])} → {mil(b["revisado_fraude"]["usd"])}</b><small>mil USD de fraude atrapado</small>'
              f'<small>{ent(a["revisado_fraude"]["pagos"])} → {ent(b["revisado_fraude"]["pagos"])} pagos</small></td>'
              f'<td><b>{ent(a["revisado_legitimo"]["pagos"])} → {ent(b["revisado_legitimo"]["pagos"])}</b><small>revisiones a clientes legítimos</small>'
              '<small>cada una consume una revisión</small></td></tr>'
              f'<tr><th scope="row">No se revisa</th><td style="--cell:rgba(242,196,173,.6)">'
              f'<b>{mil(a["no_revisado_fraude"]["usd"])} → {mil(b["no_revisado_fraude"]["usd"])}</b><small>mil USD de fraude que pasa</small>'
              '<small>pérdida completa del monto</small></td>'
              f'<td><b>{ent(b["no_revisado_legitimo"]["pagos"])}</b><small>pagos legítimos sin fricción</small><small>prácticamente iguales en ambas</small></td></tr>'
              '</tbody></table><p class="matrix-key">Mejor regla → modelo, con el mismo cupo de 60 revisiones por día</p>')
    s["matriz"] = pagina(
        "Un error no cuesta lo mismo en cada pago: la matriz se mide en dólares",
        f'<div class="split matrix-split fill"><div class="matrix-block">{matriz}</div><aside class="argument">'
        '<p class="sub">Regla del curso: revisar si p&nbsp;≥&nbsp;C&nbsp;/&nbsp;LTV</p>'
        '<p>Aquí lo que se pierde es el monto del pago. La regla queda <b>p&nbsp;×&nbsp;monto&nbsp;≥&nbsp;C</b>: la cola se ordena por fraude esperado.</p>'
        f'<div class="rule"><p><b class="measure">{pct(a["precision"], False)} → <em>{pct(b["precision"], False)}</em></b><br>de la cola es fraude</p>'
        f'<p><b class="measure">{pct(a["parte_usd_fraude"], False)} → <em>{pct(b["parte_usd_fraude"], False)}</em></b><br>del dinero de fraude del mes entra a la cola</p></div>'
        '</aside></div>',
        "Revisado o no × fraude o legítimo · C: costo de revisar · LTV: valor en riesgo, aquí el monto del pago", fase=FASE[0])

    # 2 · Datos: el dinero está en los montos altos
    dec = _csv("exp_deciles_monto.csv")
    filas_dec = [{"rango": (f"≤{float(r['monto_max']):,.0f}" if i < 9 else f">{float(r['monto_min']):,.0f}"),
                  "parte": float(r["parte_usd_fraude"]), "tasa": float(r["tasa"])} for i, r in enumerate(dec)]
    top10 = X["concentracion"]["top_10pct_pagos_por_monto"]
    F["deciles"] = G.deciles(filas_dec)
    s["deciles"] = pagina(
        f"El 10% de los pagos más caros concentra {pct(top10, False)} del fraude en dólares",
        _split(F["deciles"],
               f'<p class="big">{pct(un["tasa_fraude"], False, 1)}</p><p class="sub">de los pagos es fraude: uno de cada {1 / un["tasa_fraude"]:.0f}</p>'
               '<div class="rule"><p><b>Contar fraudes no basta</b></p>'
               '<p>Ordenar solo por probabilidad llena la cola de fraudes baratos. El monto tiene que entrar al orden.</p></div>'),
        f"Días 1–120 · {ent(un['pagos'])} pagos · {mil(un['usd_fraude'])} mil USD de fraude · Deciles de monto con el mismo número de pagos",
        fase=FASE[1])

    # 3 · Preparación: el cliente reconstruido
    td = ck["tasa_por_tiempo_desde_anterior"]
    etiquetas = ("Menos de 1 hora", "1 a 24 horas", "1 a 7 días", "Más de 7 días", "Primer pago")
    cats = [(e, td[k]["tasa"], td[k]["pagos"]) for e, k in zip(etiquetas, list(td))]
    capas = [total(f"XGB|{c}") for c in ("F1", "F2", "F3", "F4")]
    F["cliente"] = G.cliente(cats, un["tasa_fraude"])
    s["cliente"] = pagina(
        "Una señal que no viene en los datos: reconstruimos al cliente",
        _split(F["cliente"],
               f'<p class="big">{pct(cats[0][1], False, 1)}</p><p class="sub">de los pagos es fraude si el mismo cliente pagó hace menos de una hora; '
               f'el promedio es {pct(un["tasa_fraude"], False, 1)}</p>'
               '<div class="rule"><p><b>Cliente = tarjeta + dirección + día de alta</b></p>'
               f'<p>Día de alta = día del pago − <code>D1</code>. Con su historial, el mismo XGBoost atrapa {mil(capas[2] - capas[1])} mil USD más en desarrollo.</p>'
               '<p class="muted">Cada medida usa solo pagos anteriores y ninguna etiqueta.</p></div>'),
        "Días 1–120 · Recencia, frecuencia y desvío del monto por tarjeta, por combinaciones de tarjeta, dirección y correo, y por cliente",
        fase=FASE[2])

    # 4 · Modelado: diseño de la prueba
    F["tiempo"] = G.tiempo(PJ["dias"])
    F["calendario"] = G.tiempo(PJ["dias"], estudio=False)
    s["calendario"] = pagina(
        "Se elige con el pasado y se prueba una sola vez con el futuro",
        f'<figure class="fill">{F["calendario"]}</figure>'
        '<div class="clock-line"><p><b>Días 1–60</b><span>Solo entrenamiento</span></p>'
        f'<p><b>Días {S["bloques"]["D1"]["inicio"]}–{S["bloques"]["D2"]["fin"]}</b><span>Desarrollo en dos bloques: aquí se tomaron todas las decisiones</span></p>'
        f'<p><b>Días {R["P1"]["dias"][0]}–{R["P2"]["dias"][1]}</b><span>Prueba con el protocolo congelado, leída una sola vez</span></p>'
        f'<p><b>{margen} días</b><span>de margen entre entrenar y evaluar: el contracargo tarda en llegar</span></p></div>',
        f"Partición por tiempo, no al azar: el fraude cambia de un mes a otro · Huellas SHA-256 del protocolo antes de abrir el día {R['P1']['dias'][0]}",
        fase=f"{FASE[3]} · diseño de la prueba")

    # 4 · Modelado: del árbol al boosting
    ven = S["ventaja"]
    F["modelos"] = G.escalera(
        [("Mejor\nregla", total(REGLA), G.NARANJA), ("Árbol\nCART", total("CART|F3"), G.AZUL_MEDIO),
         ("Bosque\naleatorio", total("RF|F3"), G.AZUL_MEDIO), ("XGBoost", total(FINAL), G.AZUL)],
        ("Logística L2", total(LOGIT), G.VERDE),
        [("Ensamble", total("ENS|F3")), ("Red\nneuronal", total("MLP|F3")), ("Bosque de\naislamiento", total("ISO|F3"))])
    s["modelos"] = pagina(
        "Un árbol solo no supera a la regla; el bosque y el boosting sí",
        _split(F["modelos"],
               '<p class="sub">Mismas 93 variables, mismo cupo, hiperparámetros fijos</p>'
               '<p>El bosque promedia muchos árboles y baja su varianza; el boosting suma árboles que corrigen los errores de los anteriores.</p>'
               '<div class="rule"><p><b>Criterio fijado antes de comparar</b></p>'
               f'<p>Gana el modelo flexible con más dólares, si además supera a la logística en cada bloque: XGBoost, por {pct(ven[LOGIT]["D1"])} y '
               f'{pct(ven[LOGIT]["D2"], d=1)}.</p></div>'),
        f"Desarrollo: {d_desarrollo}, 60 revisiones por día · Porcentajes: cambio contra la barra anterior · En gris, el resto del torneo",
        fase=FASE[3])

    # 5 · Evaluación: hipótesis
    filas_h = [("Contra la mejor regla", f"H1 · barra {pct(U['H1'])}", cr["P1"], cr["P2"], U["H1"]),
               ("Contra la mejor logística", f"H2 · barra {pct(U['H2'])}", cl["P1"], cl["P2"], U["H2"]),
               ("Contra solo probabilidad", "H3 · enfoque de la competencia", cp["P1"], cp["P2"], None)]
    F["hipotesis"] = G.intervalos(filas_h, alto=118)
    s["hipotesis"] = pagina(
        ("Las tres hipótesis fijadas antes de la prueba se cumplen en los dos meses" if len(pasan) == 3
         else f"{_y(pasan)} se cumplen en los dos meses" if pasan else "Las hipótesis no se cumplen en los dos meses"),
        f'<figure class="fill">{F["hipotesis"]}</figure>'
        f'<p class="takeaway">Cada intervalo remuestrea días completos: {ent(replicas)} réplicas pareadas, las mismas para las tres comparaciones. '
        'Una hipótesis se cumple si la ventaja pasa su barra y el límite inferior queda sobre cero.</p>',
        f"Barras registradas en docs/protocolo.md antes de abrir el día {R['P1']['dias'][0]} · P1: {dias['P1']} · P2: {dias['P2']}",
        fase=FASE[4])

    # 5 · Evaluación: las métricas de clasificación eligen otra cola
    cols_m = (("nunca", "Nunca revisar"), ("solo_p", "Solo probabilidad"), ("regla", "Mejor regla"), ("logistica", "Logística"), ("modelo", "Modelo"))
    filas_m = (("Exactitud", "(TP + TN) / N", lambda k: op[k]["exactitud"], lambda v: pct(v, False, 1)),
               ("Precisión", "TP / (TP + FP)", lambda k: op[k]["precision"], lambda v: pct(v, False)),
               ("Recall", "TP / (TP + FN)", lambda k: op[k]["recall"], lambda v: pct(v, False)),
               ("F1", "2TP / (2TP + FP + FN)", lambda k: op[k]["f1"], lambda v: f"{v:.2f}"),
               ("ROC-AUC", "del puntaje que ordena", lambda k: cv[k]["auc"] if k in cv else None, lambda v: f"{v:.2f}"),
               ("PR-AUC", "precisión promedio (AP)", lambda k: cv[k]["ap"] if k in cv else None, lambda v: f"{v:.2f}"),
               ("Fraude en la cola", "mil USD", lambda k: op[k]["usd"], lambda v: mil(v)))
    ganadores = {}

    def fila_m(nombre, formula, val, fmt):
        vals = {k: val(k) for k, _ in cols_m}
        g = max((k for k in vals if vals[k] is not None), key=lambda k: vals[k])
        ganadores[nombre] = g
        dinero = nombre.startswith("Fraude")
        celdas = "".join(
            '<td><b class="muted">—</b></td>' if vals[k] is None else
            f'<td class="{"focus-azul" if dinero and k == g else ""}" style="--cell:{"rgba(125,190,228,.42)" if k == g else "#f3f5f8"}">'
            f'<b>{fmt(vals[k])}</b></td>' for k, _ in cols_m)
        return f'<tr><th scope="row">{nombre}<small>{formula}</small></th>{celdas}</tr>'
    tabla_m = ('<table class="matrix compacta metricas"><thead><tr><th scope="col">60 revisiones por día</th>'
               + "".join(f'<th scope="col">{n}</th>' for _, n in cols_m) + '</tr></thead><tbody>'
               + "".join(fila_m(*f) for f in filas_m) + '</tbody></table>')
    estad = [g for n, g in ganadores.items() if not n.startswith("Fraude")]
    assert ganadores["Fraude en la cola"] == "modelo" and "modelo" not in estad, ganadores
    s["metricas"] = pagina(
        f"{PALABRA[len(estad)]} métricas de clasificación eligen otra cola; solo el dinero elige el modelo",
        f'<div class="split matrix-split fill"><div class="matrix-block">{tabla_m}</div><aside class="argument">'
        f'<p class="big">{pct(op["nunca"]["exactitud"], False, 1)}</p><p class="sub">de exactitud sin revisar ningún pago: más que cualquier cola</p>'
        f'<div class="rule"><p><b>Solo probabilidad gana {estad.count("solo_p")} de {len(estad)}</b></p>'
        f'<p>pero lleva {mil(op["solo_p"]["usd"])} mil USD a la cola, contra {mil(op["modelo"]["usd"])} mil del modelo. '
        'Exactitud, F1 y AUC cuentan aciertos; no pesan el monto.</p></div></aside></div>',
        f"{dias_t} · Mismo cupo para todas · Positivo = fraude · En tono, la mejor de cada fila · AUC y AP del puntaje con que se ordena cada cola",
        fase=FASE[4])

    # 5 · Evaluación: ganancia acumulada y lift
    gm, cupo_t = CC["ganancia"], CC["cupo_fraccion"]
    u_cupo = op["modelo"]["usd"] / CC["usd_fraude"]
    u_regla = op["regla"]["usd"] / CC["usd_fraude"]
    ahorro_t = 1 - float(np.interp(u_regla, gm["modelo"]["usd"], gm["modelo"]["fraccion"])) / cupo_t
    ser_g = [dict(nombre="Modelo: dólares de fraude", color=G.AZUL, fraccion=gm["modelo"]["fraccion"], valores=gm["modelo"]["usd"]),
             dict(nombre="Modelo: número de fraudes", color=G.AZUL, trazos=True, fraccion=gm["modelo"]["fraccion"], valores=gm["modelo"]["fraudes"]),
             dict(nombre="Mejor regla: dólares", color=G.NARANJA, fraccion=gm["regla"]["fraccion"], valores=gm["regla"]["usd"])]
    F["ganancia"] = G.ganancia_acum(ser_g, cupo_t, (dcl[0]["usd_acum"], dcl[0]["fraudes_acum"]))
    s["ganancia"] = pagina(
        f"Revisar {pct(cupo_t, False, 1)} de los pagos captura {pct(u_cupo, False)} del fraude en dólares",
        _split(F["ganancia"],
               f'<p class="big">×{u_cupo / cupo_t:.0f}</p><p class="sub">lift en dólares de la cola de 60: al azar se capturaría {pct(cupo_t, False, 1)}</p>'
               '<div class="rule two-numbers">'
               f'<p><b><em>×{dcl[0]["lift_usd"]:.1f}</em></b><span>lift en dólares del primer decil</span></p>'
               f'<p><b>×{dcl[0]["lift"]:.1f}</b><span>lift en número de fraudes</span></p></div>'
               f'<p class="muted">El modelo alcanza los dólares de la mejor regla con {pct(ahorro_t, False)} menos revisiones.</p>'),
        f"{dias_t} · Decil: 10% de los pagos de cada día en el orden del modelo · Lift = parte del fraude capturado / parte de los pagos revisados",
        fase=FASE[4])

    # 6 · Despliegue: tamaño del cupo según el costo de revisar
    ac = L["acumulada"]["modelo"]
    paso_k = L["kmax"] // (len(ac) - 1)
    tonos = {10: G.AZUL, 20: "#4f8fc4", 50: G.AZUL_MEDIO}
    F["beneficio"] = G.beneficio_cupo(
        [dict(costo=c, color=col, puntos=[(i * paso_k, v - c * i * paso_k * L["dias_prueba"]) for i, v in enumerate(ac)],
              k=k_de[c], neto=cst[(c, 1.0)]["modelo"]["neto_prueba"]) for c, col in tonos.items()], cupo)
    m10 = cst[(10, 1.0)]["modelo"]
    s["beneficio"] = pagina(
        f"Si una revisión cuesta 10 USD, conviene revisar cientos de pagos al día, no {cupo}",
        _split(F["beneficio"],
               '<p class="sub">Neto = fraude detenido − costo × revisiones</p>'
               f'<p class="big">{ent(k_de[10])} <span>al día</span></p>'
               f'<p>es el cupo que elige el desarrollo con 10 USD por revisión: el neto pasa de {mil(m10["neto_60"])} a {mil(m10["neto_prueba"])} mil USD. '
               f'Con 50 USD, el cupo baja a {k_de[50]}.</p>'
               '<div class="rule"><p><b>El ganador no cambia</b></p>'
               f'<p>El modelo deja más neto que la regla y la logística en {gana_c} de {2 * len(costos_t)} escenarios de costo.</p></div>'),
        f"Prueba: {d_prueba} · Cupo elegido con las curvas de los {d_desarrollo} y medido en la prueba · Puntos: ese cupo y su neto",
        fase=f"{FASE[5]} · tamaño del cupo")

    # 5 · Evaluación: optimizar sobre la validación engaña
    conf, hp = VA["confirmacion"], VA["hiperparametros"]
    c6 = VA["confirmacion_resultados"]
    mejor_k = "elegido_ajustado" if hp["adopta"] else "elegido"
    base_i, final_i = VA["base_F3"]["total_usd"], VA["final_interno"]["total_usd"]
    cand_g = VA["candidatos"]
    vent = list(VA["internas"].items())
    rj = VA["rejilla"]
    mejor_rj = max(rj, key=lambda f: f["total_usd"])
    final_hp = mejor_rj["total_usd"] if hp["adopta"] else final_i
    cc = c6["contrastes"]
    pc = {x: AX[x]["contrastes"] for x in P}
    cm = cc[f"{mejor_k}_vs_F3"]
    interno = final_hp / base_i - 1
    confirma = cm["rel_ic95"][0] > 0
    F["espejismo"] = G.espejismo([
        ("Ventanas de búsqueda", f"días {vent[0][1][0]}–{vent[-1][1][1]}: ahí se eligieron las variables", interno, None, G.NARANJA),
        ("Días apartados", f"días {conf[0]}–{conf[1]}: la búsqueda no los vio", cm["rel"], cm["rel_ic95"], G.AZUL)]
        + [(f"Prueba {x}", f"{dias[x]}, lectura posterior", pc[x][f"{mejor_k}_vs_F3"]["rel"], pc[x][f"{mejor_k}_vs_F3"]["rel_ic95"], G.AZUL) for x in P])
    s["espejismo"] = pagina(
        (f"Optimizar sobre la misma validación engaña: {pct(interno, d=1)} donde se eligió, {pct(cm['rel'], d=1)} en días nuevos"
         if cm["rel"] < 0 else f"Variables nuevas: {pct(interno, d=1)} donde se eligieron, {pct(cm['rel'], d=1)} en días nuevos"),
        _split(F["espejismo"],
               '<p class="sub">Búsqueda de variables con validación cruzada temporal</p>'
               f'<p>{PALABRA.get(len(cand_g), len(cand_g))} grupos candidatos, selección hacia adelante en {len(vent)} ventanas y una rejilla de '
               'hiperparámetros con parada temprana.</p>'
               + ('<div class="rule"><p><b>Se adoptan las variables nuevas</b></p><p>La ganancia se mantiene en días que la búsqueda no usó.</p></div>'
                  if confirma else
                  '<div class="rule"><p><b>Se queda el modelo congelado</b></p><p>La ganancia se midió en las mismas ventanas que eligieron las variables: '
                  'es sobreajuste a la validación.</p></div>')),
        f"Diseño registrado en docs/anexo_variables.md antes de correr · IC 95% con {ent(REPLICAS_ANEXO)} réplicas pareadas por día · "
        "Contra el modelo congelado (F3)",
        fase=f"{FASE[4]} · mantenimiento del modelo")

    # 6 · Despliegue
    s["despliegue"] = pagina(
        "Despliegue: la misma cola, otro orden y un piloto",
        '<table class="tabla despliegue"><thead><tr><th>Etapa</th><th>Cuándo</th><th>Qué se hace</th></tr></thead><tbody>'
        f'<tr><th>Operación</th><td>Cada noche</td><td>Se puntúan los pagos del día y los {cupo} con mayor fraude esperado pasan a la cola. '
        'La decisión sobre cada pago sigue siendo del equipo.</td></tr>'
        f'<tr><th>Reentrenamiento</th><td>Cada semana</td><td>Con los pagos de más de {margen} días, que ya tienen etiqueta.</td></tr>'
        '<tr><th>Piloto</th><td>Primer mes</td><td>Los días se asignan al azar a la cola actual o a la del modelo, para medir el efectivo recuperado.</td></tr>'
        '<tr><th>Monitoreo</th><td>Cada semana</td><td>Dólares por revisión, precisión, monto medio de la cola y mezcla de productos.</td></tr>'
        '<tr><th>Respaldo</th><td>Si el modelo falla</td><td>Si durante dos semanas queda por debajo de la regla, se vuelve a la tabla por segmento.</td></tr>'
        '<tr><th>Cambios</th><td>Antes de adoptar</td><td>Toda variable o ajuste nuevo se confirma en días que su búsqueda no usó.</td></tr>'
        '</tbody></table>',
        "El cupo no cambia hasta conocer el costo real de una revisión · La comparación usa la mejor regla como práctica actual", fase=FASE[5])

    # Cierre: recomendación
    s["cierre"] = (
        '<section class="slide closing" data-title="Recomendación"><p class="kicker">Recomendación</p>'
        '<h2>Ordenar la cola de revisión por fraude esperado</h2><ol class="recs">'
        f'<li><b>Usar el modelo con el cupo actual de {cupo}</b><span>{mil(extra, True)} mil USD de fraude detenido en los dos meses de prueba: '
        f'{pct(extra / tot(REGLA), False)} más que la mejor regla.</span></li>'
        '<li><b>Un mes de piloto con días al azar</b><span>Mide el efectivo realmente recuperado, que los datos no traen, contra la cola actual.</span></li>'
        '<li><b>Fijar el cupo con el costo real de revisar</b>'
        f'<span>Con 10 USD por revisión, el desarrollo elige {ent(k_de[10])} revisiones al día; con 50 USD, {ent(k_de[50])}.</span></li></ol>'
        f'<footer>Veredicto contra el protocolo congelado: {_y(pasan) if pasan else "ninguna hipótesis"} en los dos meses · '
        'Límites: el dinero atrapado mide exposición, no efectivo; la etiqueta de Vesta se propaga a la cuenta; datos de 2017-2018</footer></section>')

    # ── Apéndice ──────────────────────────────────────────────────────────────────────────────────────────────────

    # CRISP-DM y requisitos: se arman al final, cuando ya están todas las láminas

    # Prueba contra el techo
    nombres_prueba = (("Modelo", FINAL, G.AZUL), ("Logística", LOGIT, G.VERDE), ("Mejor regla", REGLA, G.NARANJA),
                      ("Solo probabilidad", PUB, G.GRIS_MEDIO), ("Mayor monto", "R_monto", G.GRIS_CLARO))
    F["prueba"] = G.prueba([(dias[x].capitalize(), usd[x]["oraculo"], [(n, usd[x][k], c) for n, k, c in nombres_prueba]) for x in P])
    techo = {x: usd[x][FINAL] / usd[x]["oraculo"] for x in P}
    techo_r = {x: usd[x][REGLA] / usd[x]["oraculo"] for x in P}
    s["prueba"] = ap(
        "La prueba confirma el orden del desarrollo",
        f'<figure class="fill">{F["prueba"]}</figure>'
        f'<p class="takeaway">El oráculo, que conoce las etiquetas, atraparía {mil(usd["P1"]["oraculo"])} y {mil(usd["P2"]["oraculo"])} mil USD con el mismo cupo. '
        f'El modelo captura <b>{pct(techo["P1"], False)} y {pct(techo["P2"], False)}</b> de ese techo; la mejor regla, {pct(techo_r["P1"], False)} y '
        f'{pct(techo_r["P2"], False)}.</p>',
        f"60 revisiones por día: {ent(R['P1']['revisiones'])} y {ent(R['P2']['revisiones'])} en cada mes · Entrenamiento con {ent(R['P1']['entrenamiento'])} y "
        f"{ent(R['P2']['entrenamiento'])} pagos · Fraude total del mes: {mil(R['P1']['usd_fraude'])} y {mil(R['P2']['usd_fraude'])} mil USD", FASE[4])

    # Intervalos contra todos los comparadores
    filas_ic = [("Mejor regla", f"H1 · barra {pct(U['H1'])}", cr["P1"], cr["P2"], U["H1"]),
                ("Mejor logística", f"H2 · barra {pct(U['H2'])}", cl["P1"], cl["P2"], U["H2"]),
                ("Solo probabilidad", "H3 · enfoque de la competencia", cp["P1"], cp["P2"], None),
                ("Bosque aleatorio", "otro flexible", C["P1"]["RF|F3"], C["P2"]["RF|F3"], None),
                ("Ensamble con bosque", "otro flexible", C["P1"]["ENS|F3"], C["P2"]["ENS|F3"], None),
                ("Con columnas opacas", "F4 · fuera por diseño", C["P1"]["XGB|F4"], C["P2"]["XGB|F4"], None)]
    F["intervalos"] = G.intervalos(filas_ic)
    s["intervalos"] = ap(
        "El modelo supera a las reglas y a la logística; con el ensamble empata",
        f'<figure class="fill">{F["intervalos"]}</figure>',
        f"IC 95% con {ent(replicas)} réplicas pareadas que remuestrean días: las mismas para todas las políticas · Barras fijadas en el protocolo "
        "antes de la prueba · Las columnas opacas darían más, pero no es posible fecharlas", FASE[4])

    # Robustez
    rb = {y: R[y]["robustez"] for y in P}
    lim = R["P1"]["limpio"]

    def fila(titulo, sub, vals, fmt=lambda v: pct(v, d=1), tinte=_tinte):
        celdas = "".join('<td style="--cell:rgba(238,242,246,1)"><b class="muted">—</b></td>' if v is None
                         else f'<td style="--cell:{tinte(v)}"><b>{fmt(v)}</b></td>' for v in vals)
        return f'<tr><th scope="row">{titulo}<small>{sub}</small></th>{celdas}</tr>'
    gana = lambda y, c: R[y]["dias_que_gana"][c]  # noqa: E731
    rob = ('<table class="matrix compacta"><thead><tr><th scope="col">Ventaja del modelo</th><th scope="col">Regla · P1</th>'
           '<th scope="col">Regla · P2</th><th scope="col">Logística · P1</th><th scope="col">Logística · P2</th></tr></thead><tbody>'
           + fila("Principal", "60 revisiones por día", [cr["P1"]["rel"], cr["P2"]["rel"], cl["P1"]["rel"], cl["P2"]["rel"]])
           + fila("30 por día", "la mitad del cupo", [rb[y]["K"][c]["30"] for c in (REGLA, LOGIT) for y in P])
           + fila("120 por día", "el doble del cupo", [rb[y]["K"][c]["120"] for c in (REGLA, LOGIT) for y in P])
           + fila("Sin los pagos más caros", "fuera los de monto > p99 del entrenamiento", [rb[y]["sin_top1"][c] for c in (REGLA, LOGIT) for y in P])
           + fila("Monto topado", f"en el p99: {R['P1']['tope_p99']:,.0f} USD", [rb[y]["topado"][c] for c in (REGLA, LOGIT) for y in P])
           + fila("Días que gana", "de 31 en cada mes", [gana(y, c) / R[y]["n_dias"] for c in (REGLA, LOGIT) for y in P],
                  fmt=lambda v: f"{round(v * 31)} de 31", tinte=lambda v: _tinte(v - .5, .5))
           + fila("Días 121–144", "sin lectura previa", [lim["contrastes"][REGLA]["rel"], None, lim["contrastes"][LOGIT]["rel"], None])
           + "</tbody></table>"
           '<p class="matrix-key">Ventaja relativa en dólares de fraude dentro de la cola · El tono crece con la ventaja</p>')
    peor_r = min(min(rb[y]["sin_top1"][REGLA], rb[y]["topado"][REGLA], rb[y]["K"][REGLA]["120"], rb[y]["K"][REGLA]["30"]) for y in P)
    peor_l = min(min(rb[y]["sin_top1"][LOGIT], rb[y]["topado"][LOGIT], rb[y]["K"][LOGIT]["120"], rb[y]["K"][LOGIT]["30"]) for y in P)
    peor_r = min(peor_r, lim["contrastes"][REGLA]["rel"])
    peor_l = min(peor_l, lim["contrastes"][LOGIT]["rel"])
    s["robustez"] = ap(
        "La ventaja se mantiene en todos los escenarios" if min(peor_r, peor_l) > 0 else "La ventaja depende del escenario",
        f'<div class="split matrix-split fill"><div class="matrix-block">{rob}</div><aside class="argument">'
        f'<p class="sub">Peor caso contra la regla</p><p class="big">{pct(peor_r, d=1)}</p>'
        f'<div class="rule"><p class="measure green">{pct(peor_l, d=1)}</p><p>Peor caso contra la logística, donde el margen es menor.</p></div>'
        '</aside></div>',
        f"P1: {dias['P1']} · P2: {dias['P2']} · Escenarios fijados en el protocolo · Días 121–144: "
        f"IC 95% contra la regla {ic(lim['contrastes'][REGLA]['rel_ic95'])}", FASE[4])

    # Costo por revisión: el cupo cambia, el ganador no
    def celda_c(f):
        m, lg, rg = neto(f, "modelo"), neto(f, "logistica"), neto(f, "regla")
        ventaja = (m - max(lg, rg)) / m if m > 0 else 0
        return (f'<td style="--cell:{_tinte(ventaja)}"><b>{mil(m)}</b><small>cupo {ent(f["modelo"]["K"])} al día</small>'
                f'<small>logística {mil(lg)} · regla {mil(rg)}</small></td>')
    tabla_c = ('<table class="matrix costo"><thead><tr><th scope="col">Neto del modelo, mil USD</th><th scope="col">Recupera todo</th>'
               '<th scope="col">Recupera la mitad</th></tr></thead><tbody>'
               + "".join(f'<tr><th scope="row">{c} USD<small>por revisión</small></th>{celda_c(cst[(c, 1.0)])}{celda_c(cst[(c, .5)])}</tr>' for c in costos_t)
               + '</tbody></table>')
    s["costo"] = ap(
        "Con cualquier costo por revisión, el modelo deja más neto" if gana_c == 2 * len(costos_t)
        else f"El modelo deja más neto en {gana_c} de {2 * len(costos_t)} escenarios de costo",
        f'<div class="split matrix-split fill"><div class="matrix-block">{tabla_c}</div><aside class="argument">'
        f'<p class="big">{gana_c} <span>de {2 * len(costos_t)}</span></p>'
        '<p class="sub">escenarios en que el modelo deja más neto que la regla y que la logística</p>'
        '<div class="rule"><p><b>Cada política elige su cupo en desarrollo</b></p>'
        f'<p>Cada una usa el cupo que maximiza su neto en los {d_desarrollo}, y el neto se mide en la prueba. '
        'Con 100 USD por revisión, la regla deja de revisar.</p></div></aside></div>',
        f"Neto = recuperado − costo × revisiones, {d_prueba} · Recuperar la mitad equivale a duplicar el costo · El tono crece con la ventaja",
        FASE[5])

    # Traza del dinero
    tz = PJ["traza"]
    F["traza"] = G.traza([(dias[y].capitalize(), tz[y]) for y in P])
    s["traza"] = ap(
        "Cada dólar de fraude cae en una caja: ambos, solo modelo, solo regla o ninguno",
        f'<figure class="fill">{F["traza"]}</figure>'
        '<div class="clock-line">'
        f'<p><b>{ent(tz["P1"]["pagos_solo_modelo"])} · {ent(tz["P2"]["pagos_solo_modelo"])}</b><span>revisiones en las que modelo y regla difieren</span></p>'
        f'<p><b>{tz["P1"]["fraudes_solo_modelo"]} · {tz["P2"]["fraudes_solo_modelo"]}</b><span>fraudes solo del modelo, de '
        f'{tz["P1"]["monto_medio_fraude_solo_modelo"]:,.0f} y {tz["P2"]["monto_medio_fraude_solo_modelo"]:,.0f} USD</span></p>'
        f'<p><b class="orange">{tz["P1"]["fraudes_solo_regla"]} · {tz["P2"]["fraudes_solo_regla"]}</b><span>fraudes solo de la regla, de '
        f'{tz["P1"]["monto_medio_fraude_solo_regla"]:,.0f} y {tz["P2"]["monto_medio_fraude_solo_regla"]:,.0f} USD</span></p>'
        f'<p><b class="muted">{mil(tz["P1"]["ninguno"])} · {mil(tz["P2"]["ninguno"])} mil</b><span>USD de fraude que no revisa ninguna</span></p></div>',
        "Ambos + solo modelo + solo regla + ninguno = fraude total del mes", FASE[4])

    # ROC contra precisión–recall con el punto de operación
    ser_r = [dict(cv["modelo"], nombre="Modelo: probabilidad × monto", corto="Modelo", color=G.AZUL, op=op["modelo"]),
             dict(cv["solo_p"], nombre="Solo probabilidad", corto="Solo prob.", color=G.GRIS_MEDIO, op=op["solo_p"]),
             dict(cv["regla"], nombre="Mejor regla", corto="Regla", color=G.NARANJA, op=op["regla"])]
    F["roc"] = G.roc_pr(ser_r, CC["prevalencia"])
    s["roc"] = ap(
        "Precisión–recall muestra mejor el punto de operación que la ROC",
        _split(F["roc"],
               f'<p class="big">{pct(1 - op["modelo"]["precision"], False)}</p><p class="sub">de las revisiones del modelo van a pagos legítimos</p>'
               f'<p>En la ROC, el mismo punto queda junto al eje vertical, con {pct(op["modelo"]["fpr"], False, 1)} de falsos positivos.</p>'
               '<div class="rule"><p><b>Ambas curvas ignoran el monto</b></p>'
               f'<p>Ordenar solo por probabilidad da más AUC ({cv["solo_p"]["auc"]:.2f} contra {cv["modelo"]["auc"]:.2f}) y lleva '
               f'{pct(1 - op["solo_p"]["usd"] / op["modelo"]["usd"], False)} menos dinero a la cola.</p></div>'),
        f"{dias_t}: {ent(CC['pagos'])} pagos y {pct(CC['prevalencia'], False, 1)} de fraude · Curvas con el orden de todo el periodo; "
        "puntos: la cola real de 60 por día", FASE[4])

    # Calibración
    ca, bb = L["calibracion"], L["brier_base"]
    habil = {k: 1 - ca[k]["brier"] / bb for k in ca}
    cola_c = ca["modelo"]["cola"]
    F["calibracion"] = G.calibracion([("Modelo", ca["modelo"]["bins"], G.AZUL), ("Logística", ca["logistica"]["bins"], G.VERDE)])
    s["calibracion"] = ap(
        "Las probabilidades subestiman un poco el fraude",
        _split(F["calibracion"],
               f'<p class="big">{pct(habil["modelo"], False)}</p><p class="sub">menos error de Brier que asignar a todos la tasa media; '
               f'la logística, {pct(habil["logistica"], False)}</p>'
               '<div class="rule"><p><b>Fraude esperado → observado en la cola</b></p>'
               f'<p><b class="measure">{mil(cola_c["P1"]["esperado"])} → <em>{mil(cola_c["P1"]["observado"])}</em></b> · '
               f'<b class="measure">{mil(cola_c["P2"]["esperado"])} → <em>{mil(cola_c["P2"]["observado"])}</em></b><br>mil USD, P1 · P2</p>'
               '<p class="muted">La regla t*&nbsp;=&nbsp;C&nbsp;/&nbsp;LTV supone p calibrada; como p subestima, el umbral óptimo queda un poco por debajo del costo.</p></div>'),
        f"{d_prueba.capitalize()} · Ocho tramos de probabilidad · Brier: modelo {ca['modelo']['brier']:.4f}, "
        f"logística {ca['logistica']['brier']:.4f}, tasa media {bb:.4f}", FASE[4])

    # Observado y supuesto
    s["observado"] = ap(
        "Qué se observa y qué se supone",
        '<table class="tabla"><thead><tr><th>Cantidad</th><th>Tipo</th><th>Qué significa para el resultado</th></tr></thead><tbody>'
        '<tr><th>Monto de cada pago</th><td class="obs">Observado</td><td>USD tal como los registró Vesta</td></tr>'
        '<tr><th>Fraude o legítimo</th><td class="obs">Observado, con la regla de Vesta</td><td>Contracargo reportado; Vesta marca también los pagos '
        'posteriores de la misma cuenta, correo o dirección</td></tr>'
        f'<tr><th>Fraude que se repite por cliente</th><td class="obs">Observado</td><td>{pct(ck["fraudes_en_clientes_con_2_o_mas"], False)} de los fraudes '
        'está en clientes con dos o más; parte del acierto proviene de reconocer cuentas ya marcadas</td></tr>'
        '<tr><th>Dinero que salva una revisión</th><td class="sup">Supuesto</td><td>El monto completo del fraude en la cola. Mide exposición, no efectivo '
        'recuperado. Igual para todas las políticas</td></tr>'
        f'<tr><th>Cuándo llega la etiqueta</th><td class="sup">Supuesto</td><td>{margen} días de margen entre entrenar y evaluar</td></tr>'
        '<tr><th>Práctica actual</th><td class="sup">Supuesto</td><td>No está publicada; la representa la mejor de seis reglas del desarrollo</td></tr>'
        '</tbody></table>',
        "Datos de diciembre de 2017 a mayo de 2018 con fechas relativas · Los supuestos afectan a todas las políticas por igual", FASE[1])

    # Calidad de los datos
    fa, pr = X["faltantes"], X["producto"]
    s["calidad"] = ap(
        "Calidad de los datos: faltantes, fechas relativas y etiqueta propagada",
        '<table class="tabla"><thead><tr><th>Hallazgo</th><th>Tratamiento</th></tr></thead><tbody>'
        f'<tr><td>Dispositivo ausente en {pct(fa["DeviceType"], False)} de los pagos; distancia en {pct(fa["dist1"], False)}</td>'
        '<td>Indicador de faltante en cada numérica; categoría propia en cada categórica</td></tr>'
        f'<tr><td>Dirección ausente en {pct(fa["addr1"], False)}; correo en {pct(fa["P_emaildomain"], False)}</td><td>Se conservan porque el faltante también es informativo</td></tr>'
        '<tr><td>Fechas relativas: <code>TransactionDT</code> en segundos desde una referencia</td><td>Días relativos; cupo y evaluación por día</td></tr>'
        f'<tr><td>Producto W: {pct(pr["W"]["parte_pagos"], False)} de los pagos y {pct(pr["W"]["parte_usd_fraude"], False)} del dinero de fraude; '
        f'producto C: tasa de {pct(pr["C"]["tasa"], False, 1)}</td><td>El producto entra al modelo y a las reglas</td></tr>'
        f'<tr><td>{pct(ck["clientes_con_fraude_todo_fraude"], False)} de los clientes con algún fraude tienen todos sus pagos marcados</td>'
        '<td>La etiqueta se propaga a la cuenta; se declara como advertencia</td></tr>'
        '<tr><td>367 columnas opacas C, D y V</td><td>Fuera del modelo final; solo diagnóstico. <code>D1</code> sirve para reconstruir al cliente</td></tr>'
        '</tbody></table>',
        "resultados/exploracion.json · Días 1–120", FASE[1])

    # Catálogo de variables
    s["catalogo"] = ap(
        "93 variables en cinco grupos",
        '<table class="tabla chica"><thead><tr><th>Grupo</th><th>Variables</th><th class="num">Cuántas</th><th>Cómo entran a la matriz</th></tr></thead><tbody>'
        '<tr><th>Monto y reloj</th><td>Monto, log del monto, centavos, hora y día de la semana</td><td class="num">5</td>'
        '<td>Cuantiles → normal (200 cuantiles)</td></tr>'
        '<tr><th>Distancias e identidad</th><td><code>dist1</code>, <code>dist2</code> y 23 numéricas <code>id_</code></td><td class="num">25</td>'
        '<td>Mediana + indicador de faltante, luego cuantiles</td></tr>'
        '<tr><th>Categóricas</th><td>Producto, <code>card1</code>–<code>card6</code>, dirección, correos, <code>M1</code>–<code>M9</code>, '
        'dispositivo y 15 <code>id_</code></td><td class="num">37</td><td>One-hot con mínimo de 50 casos y bolsa de infrecuentes; '
        'frecuencia en los árboles de sklearn</td></tr>'
        '<tr><th>Historial de tarjeta</th><td>4 llaves × previos, último día, última semana, segundos desde el anterior y razón de monto</td>'
        '<td class="num">20</td><td>Solo pagos en segundos anteriores, sin etiquetas</td></tr>'
        '<tr><th>Cliente reconstruido</th><td>Las mismas 5 medidas con <code>card1 | addr1 | día − D1</code>, más <code>D1</code></td><td class="num">6</td>'
        '<td>Igual que el historial</td></tr>'
        '<tr><th>Total del modelo</th><td>56 numéricas y 37 categóricas: el conjunto F3</td><td class="num">93</td>'
        '<td>Misma matriz para logística, XGBoost y red</td></tr>'
        '<tr><th>Fuera por diseño</th><td>Columnas opacas <code>C1</code>–<code>C14</code>, <code>D2</code>–<code>D15</code> y <code>V1</code>–<code>V339</code></td>'
        '<td class="num">367</td><td>Solo diagnóstico (F4): no se sabe cuándo se calculan</td></tr>'
        '</tbody></table>',
        f"Desbalance de {pct(un['tasa_fraude'], False, 1)}: sin reponderar, para no deformar la probabilidad · "
        f"Ponderar por monto perdió en desarrollo: {mil(total('XGB_pond|F3'))} contra {mil(total(FINAL))} mil", FASE[2])

    # Candados contra la fuga de información
    cd = S["diagnosticos_D2"]["cordura"]
    s["candados"] = ap(
        "Seis controles contra la fuga de información",
        '<table class="tabla chica"><thead><tr><th>Riesgo</th><th>Control</th><th>Cómo se comprueba</th></tr></thead><tbody>'
        f'<tr><th>El futuro entra al entrenamiento</th><td>Cada bloque entrena con pagos de {margen} días o más antes de su primer día</td>'
        '<td>Afirmación en la carga: ningún pago posterior al corte</td></tr>'
        '<tr><th>El historial ve el futuro</th><td>Solo pagos en segundos estrictamente anteriores; los del mismo segundo no se ven</td>'
        '<td>Búsqueda binaria sobre llave × segundo, lado izquierdo</td></tr>'
        '<tr><th>La etiqueta se cuela en una variable</th><td>Ninguna variable usa la etiqueta; las tasas de las reglas salen solo del entrenamiento, '
        'suavizadas con 50 casos</td>'
        f'<td>Etiquetas barajadas: el modelo cae a {mil(cd["etiquetas_barajadas"])} mil, debajo de ordenar por monto</td></tr>'
        '<tr><th>Transformar con datos de evaluación</th><td>Cuantiles, medianas, one-hot y frecuencias se ajustan con el entrenamiento de cada bloque</td>'
        '<td>Un solo objeto de diseño, ajustado una vez por bloque</td></tr>'
        '<tr><th>Columnas de origen desconocido</th><td>C, D y V fuera del modelo; <code>D1</code> solo fecha el alta del cliente</td>'
        '<td>Su ganancia se reporta aparte, como F4</td></tr>'
        '<tr><th>Ajustar con la prueba</th><td>Protocolo congelado con huellas SHA-256 antes de abrir el día 121; una sola corrida</td>'
        '<td>docs/protocolo.md y la huella del código</td></tr>'
        '</tbody></table>',
        "Una fuga infla el desempeño en desarrollo y no se sostiene en producción · Los seis controles se fijaron antes de la prueba", FASE[2])

    # Ablación por conjunto de variables
    logits = [max(total(k) for k in dv if k.startswith("LOGIT") and k.endswith(c)) for c in ("F2", "F3")]
    F["ablacion"] = G.ablacion(capas, logits)
    s["ablacion"] = ap(
        f"El historial del cliente agrega {mil(capas[2] - capas[1])} mil USD en desarrollo",
        _split(F["ablacion"],
               '<p class="sub">Conjunto elegido: F3, con descriptivas, historial y cliente</p>'
               '<p>Mismo XGBoost y mismos hiperparámetros; solo cambia el conjunto de variables.</p>'
               '<div class="rule"><p><b>Columnas opacas C, D y V</b></p>'
               f'<p>Agregarían {mil(capas[3] - capas[2])} mil USD, pero no se sabe en qué momento se calculan. Se excluyeron antes de la prueba.</p></div>'),
        f"Desarrollo: {d_desarrollo} sumados, 60 revisiones por día · Rombos: la logística con las mismas variables", FASE[2])

    # Regularización
    rg = L["regularizacion"]
    c_el = float(LOGIT.partition("|")[0].removeprefix("LOGIT_C"))
    auc_max = max((f for f in rg if f["conjunto"] == "F3"), key=lambda f: f["auc"])
    usd_max = max((f for f in rg if f["conjunto"] == "F3"), key=lambda f: f["usd"])
    F["regularizacion"] = G.regularizacion(rg, c_el)
    s["regularizacion"] = ap(
        "La penalización con más dólares no coincide con la de mayor AUC",
        _split(F["regularizacion"],
               '<p class="sub">Logística con penalización L2</p>'
               f'<p>C chico encoge más los coeficientes. El dinero toca techo en C = {usd_max["C"]:g}; el AUC, en C = {auc_max["C"]:g}.</p>'
               '<div class="rule"><p><b>El criterio de selección son los dólares</b></p>'
               '<p>Con el historial del cliente, la logística mejora en todos los valores de C.</p></div>'),
        f"{d_desarrollo.capitalize()} · 60 revisiones por día · AUC promedio de los dos bloques", FASE[3])

    # Importancia por permutación
    im = S["diagnosticos_D2"]["importancia_usd"]
    orden = sorted(im, key=lambda k: -im[k])
    F["importancia"] = G.importancia([(k[0].upper() + k[1:], im[k]) for k in orden])
    s["importancia"] = ap(
        f"Importancia por permutación: {orden[0]} es el grupo principal",
        _split(F["importancia"],
               '<p class="sub">Permutación por grupo</p>'
               '<p>Se barajan juntas las columnas de un grupo y se mide cuánto dinero pierde la cola.</p>'
               f'<div class="rule"><p><b>Sin el historial del cliente: −{mil(im["historial del cliente"])} mil USD</b></p>'
               '<p>El historial de la tarjeta aporta cerca de cero porque el del cliente ya contiene esa información.</p></div>'),
        f"Días 91–120, modelo entrenado con días 1–60 · Base: {mil(cd['base'])} mil USD", FASE[4])

    # Curva de aprendizaje con parada temprana
    apz = VA["aprendizaje"]
    va_u = VA["internas"][apz["ventana"]]
    F["aprendizaje"] = G.aprendizaje(apz["entrenamiento"], apz["validacion"], apz["paso"], apz["mejor_iteracion"], apz["arboles_protocolo"])
    s["aprendizaje"] = ap(
        f"Parada temprana en {ent(apz['mejor_iteracion'])} árboles",
        _split(F["aprendizaje"],
               f'<p class="big">{ent(apz["mejor_iteracion"])}</p><p class="sub">árboles con la menor pérdida en validación</p>'
               '<p>Después de ese punto, la pérdida en entrenamiento sigue bajando y la de validación ya no mejora, señal de sobreajuste.</p>'
               f'<div class="rule"><p><b>El protocolo fija {apz["arboles_protocolo"]} árboles</b></p>'
               + ('<p>La parada temprana llega casi al mismo número usando solo datos de entrenamiento.</p></div>'
                  if abs(apz["mejor_iteracion"] / apz["arboles_protocolo"] - 1) < .1 else
                  '<p>La parada temprana elige el número de árboles con datos de entrenamiento, sin mirar la ventana que se evalúa.</p></div>')),
        f"Ventana interna {apz['ventana'][1:]} (días {va_u[0]}–{va_u[1]}) · Validación: últimos 10 días de su entrenamiento · "
        f"Tasa de aprendizaje {apz['learning_rate']} · Capítulo 7 del curso", FASE[3])

    # Validación cruzada temporal de la búsqueda de variables
    filas_v = ([(f"Ventana {i + 1}", "búsqueda", a, b, "interna") for i, (_, (a, b)) in enumerate(vent)]
               + [("Confirmación", "no se usa en la búsqueda", conf[0], conf[1], "confirma")]
               + [(f"Prueba {x}", "lectura posterior", R[x]["dias"][0], R[x]["dias"][1], "prueba") for x in P])
    F["validacion"] = G.validacion_temporal(filas_v, margen, R["P2"]["dias"][1])
    s["validacion"] = ap(
        "Validación cruzada temporal para buscar variables nuevas",
        f'<figure class="fill">{F["validacion"]}</figure>'
        f'<p class="takeaway">{PALABRA.get(len(cand_g), len(cand_g))} grupos de variables compiten en tres ventanas de búsqueda; '
        f'los días {conf[0]}–{conf[1]} confirman el resultado y la prueba se lee una sola vez.</p>',
        f"Diseño registrado en docs/anexo_variables.md antes de correr · {margen} días de margen entre entrenamiento y evaluación", FASE[4])

    # CRISP-DM
    fases = (("Negocio", "Decisión diaria con cupo fijo, dólares por celda y costo de revisar",
              "Matriz de confusión en dólares, t*&nbsp;=&nbsp;C&nbsp;/&nbsp;LTV, curva de beneficio", ("decision", "matriz", "beneficio", "costo")),
             ("Datos", "182 días, concentración del dinero, faltantes y etiqueta propagada", "Análisis exploratorio, calidad de datos",
              ("deciles", "observado", "calidad")),
             ("Preparación", "Historial previo por tarjeta y cliente; matriz de diseño ajustada por bloque",
              "Ingeniería de variables, RFM, cuantiles, one-hot con mínimo, frecuencia, indicadores de faltante, controles de fuga",
              ("cliente", "catalogo", "candados", "ablacion")),
             ("Modelado", "Seis reglas, logística regularizada y siete modelos; partición por tiempo",
              "CART, bosque, XGBoost, MLP, ensamble, bosque de aislamiento, L2, parada temprana",
              ("calendario", "modelos", "regularizacion", "aprendizaje")),
             ("Evaluación", "Prueba congelada en dos meses con hipótesis, intervalos pareados, robustez y traza",
              "Paradoja de la exactitud, F1, ROC, precisión–recall, ganancia y lift, Brier, bootstrap, validación cruzada temporal",
              ("resumen", "hipotesis", "metricas", "ganancia", "espejismo", "prueba", "intervalos", "robustez", "traza", "roc", "calibracion",
               "importancia", "validacion")),
             ("Despliegue", "Cola nocturna, cupo según el costo, reentrenamiento, piloto, respaldo y regla para adoptar cambios",
              "Curva de beneficio contra el cupo; mantenimiento con validación temporal",
              ("beneficio", "despliegue", "cierre", "costo")))
    s["crisp"] = ap(
        "Las seis fases de CRISP-DM",
        '<table class="tabla chica crisp"><thead><tr><th>Fase</th><th>Qué se hizo</th><th>Técnicas del curso</th><th class="num">Lámina</th></tr></thead><tbody>'
        + "".join(f'<tr><th>{f}</th><td>{q}</td><td>{t}</td><td class="num">{_lam(donde, *ks)}</td></tr>' for f, q, t, ks in fases)
        + '</tbody></table>',
        "Cada lámina indica su fase arriba del título · Código en src/revisar y scripts/01 a 07", "CRISP-DM")

    # Requisitos del proyecto
    filas_req = (
        ("Presentación ejecutiva", "Hallazgos, valor del modelo y plan de despliegue", ("resumen", "despliegue", "cierre")),
        ("Decisión, recurso y dinero", "60 revisiones manuales al día; matriz de confusión en dólares", ("decision", "matriz")),
        ("Umbral de mejora antes de la prueba", f"H1 ≥ {pct(U['H1'])}, H2 ≥ {pct(U['H2'])}, H3 > 0, con límite inferior > 0", ("hipotesis", "intervalos")),
        ("Mismo presupuesto para todas", "60 revisiones por día; con costo, cada política elige su cupo", ("resumen", "prueba", "costo")),
        ("Práctica actual y base aprendida", "Mejor de seis reglas de tasa × monto; logística L2 con la misma matriz", ("modelos", "prueba", "regularizacion")),
        ("Comparador publicado", "Enfoque de la competencia IEEE-CIS: ordenar por probabilidad", ("hipotesis", "metricas", "roc")),
        ("Elegir en desarrollo, probar en ≥ 2 periodos", "Días 61–120 para elegir; 121–151 y 152–182 congelados", ("calendario", "modelos", "prueba")),
        ("Ganancia por periodo con IC pareado", f"Bootstrap de {ent(replicas)} réplicas que remuestrean días", ("hipotesis", "intervalos")),
        ("Quitar los casos más grandes", "Sin pagos sobre el p99, monto topado, cupos de 30 y 120", ("robustez",)),
        ("Traza del dinero", "Ambos, solo modelo, solo regla y ninguno suman el fraude del mes", ("traza",)),
        ("Observado contra estimado", "Monto y etiqueta observados; dinero salvado supuesto; calibración", ("observado", "calibracion")),
        ("Lecciones del curso", "Exactitud contra dinero, ROC, PR, lift, beneficio, L2, fuga", ("metricas", "ganancia", "beneficio", "roc", "candados")),
        ("Ajuste de hiperparámetros y mantenimiento", "Rejilla con parada temprana; reentrenar y adoptar cambios solo si confirman",
         ("espejismo", "despliegue", "aprendizaje", "validacion")),
        ("CRISP-DM", "Seis fases; cada lámina indica la suya", ("crisp",)))
    s["requisitos"] = ap(
        "Mapa de requisitos",
        '<table class="tabla chica requisitos"><thead><tr><th>Requisito del proyecto</th><th>Cómo se cumple</th><th class="num">Dónde</th></tr></thead><tbody>'
        + "".join(f'<tr><td>{a}</td><td>{b}</td><td class="num">{_lam(donde, *ks)}</td></tr>' for a, b, ks in filas_req if _lam(donde, *ks))
        + "</tbody></table>",
        "Protocolo, criterio y código: docs/ y src/revisar · Reproducir: scripts/01 a 07 · Detalle completo: reporte/reporte.md", "Requisitos")

    # ── Figuras que solo usan el reporte y el cuaderno ───────────────────────────────────────────────────────────

    F["resultado"] = G.marcas([(f"{dias[x].capitalize()} · {x}", [("Mejor regla", usd[x][REGLA], G.NARANJA), ("Modelo", usd[x][FINAL], G.AZUL)],
                                cr[x]["dif"], cr[x]["rel"]) for x in P])
    F["tuberia"] = G.historial_cliente()

    fam = {}
    for k in dv:
        base = k.partition("|")[0]
        base = "LOGIT" if base.startswith("LOGIT") else base
        if base.startswith("XGB") and k.split("|")[-1] in ("F1", "F4"):
            continue
        if base not in fam or total(k) > total(fam[base]):
            fam[base] = k
    azar = sum(S["info_bloques"][b]["azar_esperado"] for b in ("D1", "D2"))

    def color(k):
        if k == FINAL:
            return G.AZUL
        if k == LOGIT:
            return G.VERDE
        if k == REGLA:
            return G.NARANJA
        return G.AZUL_MEDIO if k.partition("|")[0] in NOMBRE and "|" in k and not k.startswith("ISO") else G.GRIS_CLARO
    F["torneo"] = G.torneo(sorted(((_nombre(k), total(k), color(k)) for k in fam.values()), key=lambda t: -t[1])
                           + [("Revisar al azar", azar, G.GRIS_CLARO)])

    F["diario"] = G.diario([(int(r["dia"]), float(r[FINAL]) - float(r[REGLA])) for r in _csv("prueba_dias.csv")])

    co = PJ["cola"]["P2"]
    F["exactitud"] = G.exactitud([(n, c["fraudes_por_dia"], c["usd_por_revision"], c["monto_medio_fraude"], col) for n, c, col in
                                  (("Solo probabilidad", co["publicado"], G.GRIS_MEDIO), ("Mejor regla", co["regla"], G.NARANJA),
                                   ("Probabilidad × monto", co["modelo"], G.AZUL))])

    um = CC["umbral"]
    bm = um["politicas"]["modelo"]
    tonos_m = {"10": G.AZUL, "20": "#4f8fc4", "50": G.AZUL_MEDIO}
    F["montana"] = G.montana(um["t"], [dict(costo=int(c), color=tonos_m[c], valores=bm[c]["curva"], t_dev=bm[c]["t_dev"],
                                            neto_dev=bm[c]["neto_prueba"]) for c in tonos_m], CC["corte_60"]["mediana"])

    pasos = [dict(etiqueta="F3", sub="protocolo", usd=base_i, previo=None, candidatos=[])]
    for r in VA["rondas"]:
        cand = [(GRUPO_CORTO[g], v["total_usd"]) for g, v in r["pruebas"].items()]
        if r["acepta"]:
            pasos.append(dict(etiqueta=f"+ {GRUPO_CORTO[r['mejor']]}", sub=f"{pct(r['ganancia'], d=1)} · {r['suben']} de {len(vent)}",
                              usd=r["pruebas"][r["mejor"]]["total_usd"], previo=r["partida_usd"], candidatos=cand))
        else:
            pasos.append(dict(etiqueta=f"Ronda {r['ronda']}\nse detiene", sub=f"{pct(r['ganancia'], d=1)} · {r['suben']} de {len(vent)}",
                              usd=None, previo=r["partida_usd"], candidatos=cand))
    for a_ in VA["atras"]:
        if a_["quita"]:
            pasos.append(dict(etiqueta=f"− {GRUPO_CORTO[a_['grupo']]}", sub="pasada hacia atrás", usd=a_["sin_usd"], previo=None, candidatos=[]))
    pasos.append(dict(etiqueta="+ rejilla" if hp["adopta"] else "Rejilla\nse descarta", usd=mejor_rj["total_usd"] if hp["adopta"] else None,
                      sub=f"{pct(hp['ganancia'], d=1)} · {hp['suben']} de {len(vent)}", previo=final_i,
                      candidatos=[(f"{f['params']['max_depth']}/{f['params']['min_child_weight']}", f["total_usd"]) for f in rj]))
    F["escalada"] = G.escalada(pasos, VA["regla"]["min_ganancia"])

    filas_cf = [("Variables nuevas", "XGBoost, contra F3", G.AZUL, [cc["elegido_vs_F3"]] + [pc[x]["elegido_vs_F3"] for x in P])]
    if hp["adopta"]:
        filas_cf.append(("Con hiperparámetros ajustados", "contra F3", G.AZUL,
                         [cc["elegido_ajustado_vs_F3"]] + [pc[x]["elegido_ajustado_vs_F3"] for x in P]))
    filas_cf += [("Logística con variables nuevas", "contra la logística con F3", G.VERDE,
                  [cc["logit_elegido_vs_logit_F3"]] + [pc[x]["logit_elegido_vs_logit_F3"] for x in P]),
                 ("Historial de contracargos", "no compite · contra variables nuevas", G.GRIS_MEDIO, [cc["con_etiquetas_vs_elegido"], None, None])]
    extremos = [v for _, _, _, cs in filas_cf for c in cs if c for v in c["rel_ic95"]]
    dom = (max(-.4, min(0, math.floor(min(extremos) * 20) / 20)), min(.9, max(.1, math.ceil((max(extremos) + .1) * 20) / 20)))
    F["confirmacion"] = G.confirmacion(filas_cf, [("Confirmación", f"días {conf[0]}–{conf[1]}")] + [(f"Prueba {x}", "lectura posterior") for x in P], dom)

    assert set(s) == set(CHARLA) | set(ANEXO), set(s) ^ (set(CHARLA) | set(ANEXO))
    return [s[k] for k in CHARLA] + [s[k] for k in ANEXO], F


def figuras() -> dict[str, str]:
    """{clave: svg} de todas las gráficas: las de la charla, las del apéndice y las que solo usan el reporte y el cuaderno."""
    return _construir()[1]


def crear():
    paginas, _ = _construir()
    escribir(paginas, CSS, GUION, "Qué pagos revisar", SALIDA)
    return SALIDA


CSS = r"""
.kicker { margin: 0 0 -28px; font: 500 25px/1.2 var(--sans); color: var(--muted); }
.slide h2 em { color: inherit; }
.split.fill { grid-template-rows: minmax(0, 1fr); }
.split.fill > figure { height: 100%; }
.cover > div { max-width: 860px; }
.cover p { max-width: 820px; }
.cover small { margin-top: 56px; }
.cover .map-note { left: 1070px; right: auto; width: 720px; bottom: 120px; line-height: 1.35; }
.argument code { font: 500 .9em var(--mono); }
.argument .measure em { color: var(--blue); }
.two-numbers b.orange { color: var(--orange); }
.matrix td.focus-azul { box-shadow: inset 0 0 0 3px var(--blue); }
.matrix.dinero td { white-space: normal; padding: 30px 18px; }
.matrix.dinero td b { font-size: 54px; display: block; margin-bottom: 8px; }
.matrix.dinero tbody th { font-size: 31px; }
.matrix.compacta { border-spacing: 7px 5px; }
.matrix.compacta th, .matrix.compacta td { padding: 11px 10px; }
.matrix.compacta td b { font-size: 36px; }
.matrix.compacta tbody th { font-size: 26px; }
.matrix.compacta th small { font-size: 20px; }
.matrix td b.green { color: var(--green); }
.matrix td b.orange { color: var(--orange); }
.tabla { width: 100%; border-collapse: collapse; font: 400 27px/1.3 var(--sans); color: var(--text); }
.tabla th, .tabla td { text-align: left; padding: 17px 26px 17px 0; border-bottom: 2px solid var(--line); vertical-align: top; }
.tabla thead th { color: var(--muted); font: 500 24px/1.15 var(--sans); border-bottom-color: #a5aebc; }
.tabla tbody th { font: 600 27px/1.25 var(--sans); color: var(--ink); width: 25%; }
.tabla .num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
.tabla tr > :last-child { padding-right: 0; }
.tabla code { font: 500 .9em var(--mono); }
.tabla .obs { color: var(--blue); font-weight: 600; white-space: nowrap; }
.tabla .sup { color: var(--orange); font-weight: 600; white-space: nowrap; }
.tabla.chica { font-size: 24px; }
.tabla.chica th, .tabla.chica td { padding: 11px 22px 11px 0; }
.appendix h2 { font-size: 58px; }
.matrix.costo { border-spacing: 7px 5px; }
.matrix.costo th, .matrix.costo td { padding: 9px 12px; }
.matrix.costo td b { font-size: 38px; }
.matrix.costo td small { font-size: 20px; margin-top: 2px; }
.matrix.costo tbody th { font-size: 27px; }
.matrix.costo th small { font-size: 20px; }
.tabla.requisitos { font-size: 22px; }
.tabla.requisitos th, .tabla.requisitos td { padding: 7px 22px 7px 0; }
.tabla.requisitos td.num { white-space: nowrap; }
.tabla.requisitos td:first-child { width: 33%; }
.tabla.requisitos thead th { font-size: 21px; }
.matrix.metricas td b { font-size: 34px; }
.matrix.metricas thead th { font-size: 23px; }
.tabla.crisp { font-size: 22px; }
.tabla.crisp th, .tabla.crisp td { padding: 9px 22px 9px 0; }
.tabla.crisp tbody th { font-size: 24px; width: 15%; }
.tabla.despliegue th, .tabla.despliegue td { padding-top: 15px; padding-bottom: 15px; }
.closing h2 { font-size: 80px; margin-top: 40px; }
.closing .kicker { margin: 0; }
.recs { list-style: none; margin: 72px 0 0; padding: 0; display: grid; grid-template-columns: repeat(3, 1fr); gap: 64px; counter-reset: rec; }
.recs li { border-top: 5px solid var(--blue); padding-top: 26px; counter-increment: rec; }
.recs li::before { content: counter(rec); display: block; margin-bottom: 16px; font: 500 25px var(--mono); color: var(--blue); }
.recs b { display: block; font: 600 40px/1.12 var(--display); letter-spacing: -.02em; }
.recs span { display: block; margin-top: 20px; font: 400 29px/1.36 var(--sans); color: var(--text); }
"""
