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
          "ganancia", "espejismo", "beneficio", "despliegue", "cierre")
ANEXO = ("crisp", "requisitos", "prueba", "intervalos", "robustez", "costo", "traza", "roc", "calibracion", "observado", "calidad",
         "catalogo", "candados", "ablacion", "regularizacion", "importancia", "aprendizaje", "validacion", "dia")
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
    # Sin pies de página: cada lámina dice una sola cosa en el título y la sostiene con una gráfica. El detalle está en el guion.

    # Portada
    dia = PJ["dia"]
    total_pagos = sum(v[0] for v in PJ["dias"].values())
    s["portada"] = (
        '<section class="slide cover" data-title="Qué pagos revisar">' + G.portada(dia)
        + '<div><h1>Qué pagos<br>revisar</h1><p>Cada día caben 60 revisiones manuales de fraude. ¿Cuáles 60?</p>'
        f'<small>Minería de Datos · ITAM · Proyecto final · {ent(total_pagos)} pagos de comercio electrónico (IEEE-CIS, Vesta)</small></div>'
        f'<p class="map-note">Los {ent(dia["pagos"])} pagos de un día · Azul: los 60 que el modelo manda a revisión · '
        'Naranja: fraudes que no se revisan</p></section>')

    # Resumen: el valor del modelo en una gráfica
    extra = tot(FINAL) - tot(REGLA)
    F["resumen"] = G.resumen([("Práctica actual: la mejor regla", tot(REGLA), G.NARANJA), ("Logística regularizada", tot(LOGIT), G.VERDE),
                              ("Modelo: XGBoost, probabilidad × monto", tot(FINAL), G.AZUL)])
    gana_meses = all(cr[x]["rel_ic95"][0] > 0 for x in P)
    s["resumen"] = pagina(
        f"Con las mismas 60 revisiones al día, el modelo detiene {pct(extra / tot(REGLA), False)} más fraude",
        _split(F["resumen"],
               f'<p class="big">{mil(extra, True)} <span>mil USD</span></p>'
               '<p class="sub">más fraude detenido en los dos meses de prueba</p>'
               '<div class="rule"><p>Mismo equipo y mismas revisiones: solo cambia el orden de la cola.</p>'
               + (f'<p>Gana en cada mes por separado: {pct(cr["P1"]["rel"])} y {pct(cr["P2"]["rel"])}.</p>' if gana_meses else "") + "</div>"),
        fase="Resumen")

    # 1 · Negocio: la decisión
    pagos_dia = round(CC["pagos"] / CC["n_dias"], -2)
    F["decision"] = G.dia_decision(dia)
    s["decision"] = pagina(
        f"La decisión: cada noche, qué 60 de unos {ent(pagos_dia)} pagos revisar",
        '<div class="decision fill"><div class="cifras">'
        f'<p><b>{ent(pagos_dia)}</b><span>pagos al día, en promedio</span></p>'
        f'<p><b class="azul">60</b><span>revisiones manuales al día: {pct(CC["cupo_fraccion"], False)} de los pagos</span></p>'
        f'<p><b class="naranja">{pct(un["tasa_fraude"], False, 1)}</b><span>de los pagos son fraude</span></p></div>'
        '<dl class="ficha">'
        '<dt>Quién decide</dt><dd>El equipo de riesgo del procesador de pagos</dd>'
        '<dt>Cuándo</dt><dd>Cada noche, con los pagos del día</dd>'
        '<dt>Opciones</dt><dd>Revisar el pago o dejarlo pasar</dd>'
        '<dt>Hoy</dt><dd>Una regla fija; aquí, la mejor de seis reglas de tasa histórica × monto</dd>'
        '<dt>Éxito</dt><dd>Más dólares de fraude detenidos con las mismas 60 revisiones</dd></dl></div>',
        fase=FASE[0])

    # 1 · Negocio: qué vale cada caso y por qué se ordena por probabilidad × monto
    pts = dia["puntos"]  # (probabilidad, monto, fraude, revisado)
    caso_a = max((p for p in pts if p[3] and p[2] and p[0] < .15), key=lambda p: p[1])  # fraude revisado con probabilidad baja
    caso_b = max((p for p in pts if p[2] and not p[3]), key=lambda p: p[0])  # fraude que pasó con la probabilidad más alta

    def caso(p, clase, veredicto):
        return (f'<div class="caso {clase}"><p class="cuenta">{p[1]:,.0f} USD × {p[0] * 100:.1f}% = <b>{p[0] * p[1]:,.0f} USD</b></p>'
                f'<p class="veredicto">{veredicto}</p></div>')
    s["matriz"] = pagina(
        "Se revisa el fraude esperado en dólares, no el pago más sospechoso",
        '<div class="split valor fill"><div>'
        '<table class="matrix valor"><thead><tr><th scope="col"></th><th scope="col">Resulta fraude</th><th scope="col">Resulta legítimo</th></tr>'
        '</thead><tbody>'
        '<tr><th scope="row">Se revisa</th><td><b>− costo</b><small>el fraude se detiene; solo se paga la revisión</small></td>'
        '<td><b>− costo</b><small>revisión sin hallazgo</small></td></tr>'
        '<tr><th scope="row">Se deja pasar</th><td class="pierde"><b>− monto</b><small>se pierde el pago completo</small></td>'
        '<td><b>0</b><small>el cliente no nota nada</small></td></tr></tbody></table>'
        '<p class="formula">Revisar evita perder el monto, con probabilidad p, a cambio de una revisión: conviene si '
        '<b>probabilidad × monto</b> supera el costo. Con 60 revisiones fijas, entran los 60 pagos con más probabilidad × monto.</p>'
        '<p class="formula-nota">Es la regla del curso, revisar si p ≥ C / LTV, con el monto como valor en riesgo.</p></div>'
        f'<aside class="ejemplos"><p class="sub">Dos fraudes reales del día {dia["dia"]}</p>'
        + caso(caso_a, "revisa", f"Se revisa: {caso_a[1]:,.0f} USD detenidos")
        + caso(caso_b, "pasa", "Pasa: es más sospechoso, pero vale menos")
        + f'<p class="muted">Ese día entraron a la cola los pagos con {dia["corte"]:,.0f} USD esperados o más.</p></aside></div>',
        fase=FASE[0])

    # 2 · Datos: el dinero está en los montos altos
    dec = _csv("exp_deciles_monto.csv")
    filas_dec = [{"rango": (f"≤{float(r['monto_max']):,.0f}" if i < 9 else f">{float(r['monto_min']):,.0f}"),
                  "parte": float(r["parte_usd_fraude"]), "tasa": float(r["tasa"])} for i, r in enumerate(dec)]
    top10 = X["concentracion"]["top_10pct_pagos_por_monto"]
    tasas = [f["tasa"] for f in filas_dec]
    F["deciles"] = G.deciles(filas_dec)
    s["deciles"] = pagina(
        f"El 10% de los pagos más caros concentra {pct(top10, False)} del fraude en dólares",
        _split(F["deciles"],
               f'<p class="big">{pct(un["tasa_fraude"], False, 1)}</p>'
               f'<p class="sub">de los pagos son fraude: entre {pct(min(tasas), False)} y {pct(max(tasas), False)} en cada tramo de monto</p>'
               '<div class="rule"><p>El dinero no se reparte igual: está en los pagos caros. Ordenar solo por probabilidad llena la cola de '
               'fraudes baratos.</p></div>'),
        fase=FASE[1])

    # 3 · Preparación: el cliente reconstruido
    td = ck["tasa_por_tiempo_desde_anterior"]
    etiquetas = ("Menos de 1 hora", "1 a 24 horas", "1 a 7 días", "Más de 7 días", "Primer pago")
    cats = [(e, td[k]["tasa"], td[k]["pagos"]) for e, k in zip(etiquetas, list(td))]
    capas = [total(f"XGB|{c}") for c in ("F1", "F2", "F3", "F4")]
    veces = cats[0][1] / un["tasa_fraude"]
    assert 1.75 < veces < 2.05, veces
    F["cliente"] = G.cliente(cats, un["tasa_fraude"])
    s["cliente"] = pagina(
        "Reconstruimos al cliente: si volvió a pagar en menos de una hora, el fraude casi se duplica",
        _split(F["cliente"],
               '<p class="sub">Cliente = tarjeta + dirección + fecha de alta</p>'
               '<p>Los datos no traen un identificador de cliente; lo construimos con la columna <code>D1</code>, días desde el alta.</p>'
               '<div class="rule"><p>26 variables de historial —recencia, frecuencia y monto— calculadas solo con pagos anteriores.</p>'
               f'<p>Con ellas, el mismo XGBoost detiene {mil(capas[2] - capas[1])} mil USD más en desarrollo.</p></div>'),
        fase=FASE[2])

    # 4 · Modelado: diseño de la prueba
    F["tiempo"] = G.tiempo(PJ["dias"])
    F["calendario"] = G.tiempo(PJ["dias"], ("Entrenamiento", "Desarrollo: aquí se decide todo", "Prueba: se abre una sola vez"),
                               estudio=False, cortes=(61, 121))
    s["calendario"] = pagina(
        "Se decide con el pasado y se prueba una sola vez con el futuro",
        f'<figure class="fill">{F["calendario"]}</figure>'
        '<div class="clock-line"><p><b>Partición por tiempo</b><span>no al azar: en producción siempre se predice el futuro</span></p>'
        f'<p><b>{margen} días de margen</b><span>entre entrenar y evaluar: el contracargo tarda en llegar</span></p>'
        '<p><b>Protocolo congelado</b><span>modelo, rivales y metas fijados antes de abrir la prueba</span></p>'
        '<p><b>Una sola lectura</b><span>nada se ajustó después de ver la prueba</span></p></div>',
        fase=FASE[3])

    # 4 · Modelado: del árbol al boosting
    F["modelos"] = G.escalera(
        [("Mejor\nregla", total(REGLA), G.NARANJA), ("Árbol\nCART", total("CART|F3"), G.AZUL_MEDIO),
         ("Bosque\naleatorio", total("RF|F3"), G.AZUL_MEDIO), ("XGBoost", total(FINAL), G.AZUL)],
        ("Logística L2", total(LOGIT), G.VERDE),
        [("Ensamble", total("ENS|F3")), ("Red\nneuronal", total("MLP|F3")), ("Bosque de\naislamiento", total("ISO|F3"))])
    s["modelos"] = pagina(
        "Un árbol solo no supera a la regla; el bosque y el boosting sí",
        _split(F["modelos"],
               '<p class="sub">Mismas 93 variables y mismo cupo</p>'
               '<p>Un árbol solo cambia mucho con los datos. El bosque promedia cientos de árboles; el boosting suma árboles que corrigen '
               'los errores de los anteriores.</p>'
               '<div class="rule"><p>XGBoost supera a la logística en los dos bloques de desarrollo y es el que pasa a la prueba.</p></div>'),
        fase=FASE[3])

    # 5 · Evaluación: la ventaja de cada mes contra la meta fijada antes
    meses = [(f"Mes {i + 1}", x) for i, x in enumerate(P)]
    F["hipotesis"] = G.metas([("Contra la práctica actual", U["H1"], [(m, cr[x]["rel"], cr[x]["rel_ic95"]) for m, x in meses]),
                              ("Contra la logística", U["H2"], [(m, cl[x]["rel"], cl[x]["rel_ic95"]) for m, x in meses])])
    cumplen = all(ve[x][k] for x in P for k in ("H1_regla", "H2_logistica"))
    s["hipotesis"] = pagina(
        "En los dos meses de prueba, el modelo supera las metas fijadas antes de abrirla" if cumplen
        else "El modelo no supera todas las metas fijadas antes de la prueba",
        _split(F["hipotesis"],
               '<p class="sub">Metas registradas antes de la prueba</p>'
               f'<p>{pct(U["H1"])} contra la regla y {pct(U["H2"])} contra la logística, con el intervalo de 95% entero sobre cero.</p>'
               f'<div class="rule"><p><span class="nw">Mes 1: {dias["P1"]}.</span> <span class="nw">Mes 2: {dias["P2"]}.</span></p>'
               f'<p>Cada intervalo remuestrea días completos {ent(replicas)} veces.</p></div>'),
        fase=FASE[4])

    # 5 · Evaluación: la exactitud y el AUC eligen otra cola
    claves_m = ("nunca", "solo_p", "regla", "logistica", "modelo")
    paneles = [("Exactitud", [op[k]["exactitud"] for k in claves_m], lambda v: pct(v, False, 1), 1, G.NARANJA),
               ("ROC-AUC", [cv[k]["auc"] if k in cv else None for k in claves_m], lambda v: f"{v:.2f}", 1, G.NARANJA),
               ("Fraude detenido, mil USD", [op[k]["usd"] for k in claves_m], mil, max(op[k]["usd"] for k in claves_m), G.AZUL)]
    ganador = [claves_m[max((i for i, v in enumerate(p[1]) if v is not None), key=lambda i: p[1][i])] for p in paneles]
    assert ganador == ["nunca", "solo_p", "modelo"], ganador
    F["metricas"] = G.tres_metricas([("Nunca revisar", "no revisa ningún pago", G.NEGRO), ("Solo probabilidad", "mismo modelo, sin el monto", G.NEGRO),
                                     ("Mejor regla", "práctica actual", G.NEGRO), ("Logística", "modelo lineal", G.NEGRO),
                                     ("Modelo", "probabilidad × monto", G.AZUL)], paneles)
    s["metricas"] = pagina(
        "La exactitud y el AUC eligen otra cola; solo los dólares eligen el modelo",
        f'<figure class="fill">{F["metricas"]}</figure>'
        f'<p class="takeaway">No revisar nada acierta en {pct(op["nunca"]["exactitud"], False, 1)} de los pagos, porque casi todos son legítimos. '
        'Exactitud, AUC, precisión y F1 cuentan aciertos: un fraude de 8 USD pesa lo mismo que uno de 900 USD.</p>',
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
    F["ganancia_cola"] = G.ganancia_cola([dict(nombre="Modelo", color=G.AZUL, fraccion=gm["modelo"]["fraccion"], usd=gm["modelo"]["usd"], cola=u_cupo),
                                          dict(nombre="Mejor regla", color=G.NARANJA, fraccion=gm["regla"]["fraccion"], usd=gm["regla"]["usd"],
                                               cola=u_regla)], cupo_t)
    s["ganancia"] = pagina(
        f"Revisando {pct(cupo_t, False)} de los pagos, el modelo captura {pct(u_cupo, False)} del fraude en dólares; la regla, {pct(u_regla, False)}",
        _split(F["ganancia_cola"],
               f'<p class="big">×{u_cupo / cupo_t:.0f}</p><p class="sub">lift: {u_cupo / cupo_t:.0f} veces el fraude que atraparía revisar al azar</p>'
               f'<div class="rule"><p>Para detener lo mismo que la regla, al modelo le basta con {pct(1 - ahorro_t, False)} de las revisiones.</p></div>'),
        fase=FASE[4])

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
    F["espejismo"] = G.espejismo(
        [("Donde se\neligieron", f"días {vent[0][1][0]}–{vent[-1][1][1]}", interno, None, G.NARANJA),
         ("Días\napartados", f"días {conf[0]}–{conf[1]}", cm["rel"], cm["rel_ic95"], G.AZUL)]
        + [(f"Prueba,\nmes {i + 1}", dias[x], pc[x][f"{mejor_k}_vs_F3"]["rel"], pc[x][f"{mejor_k}_vs_F3"]["rel_ic95"], G.AZUL_MEDIO)
           for i, x in enumerate(P)])
    s["espejismo"] = pagina(
        (f"Las variables nuevas ganaban {pct(interno, False, 1)} donde se eligieron y perdían {pct(-cm['rel'], False, 1)} en días nuevos"
         if cm["rel"] < 0 else f"Variables nuevas: {pct(interno, d=1)} donde se eligieron, {pct(cm['rel'], d=1)} en días nuevos"),
        _split(F["espejismo"],
               '<p class="sub">Sobreajuste a la validación</p>'
               f'<p>{PALABRA.get(len(cand_g), len(cand_g))} grupos de variables nuevas compitieron con validación cruzada temporal en '
               f'{len(vent)} ventanas, más una rejilla de hiperparámetros.</p>'
               + ('<div class="rule"><p><b>Se adoptan.</b> La mejora se mantiene en días que la búsqueda no vio.</p></div>' if confirma else
                  '<div class="rule"><p><b>Se queda el modelo original.</b> Una mejora se adopta solo si se confirma en días que la búsqueda '
                  'no vio.</p></div>')),
        fase=FASE[4])

    # 6 · Despliegue: tamaño del cupo según el costo de revisar
    ac = L["acumulada"]["modelo"]
    paso_k = L["kmax"] // (len(ac) - 1)
    tonos = {10: G.AZUL, 20: "#4f8fc4", 50: G.AZUL_MEDIO}
    F["beneficio"] = G.beneficio_cupo(
        [dict(costo=c, color=col, puntos=[(i * paso_k, v - c * i * paso_k * L["dias_prueba"]) for i, v in enumerate(ac)],
              k=k_de[c], neto=cst[(c, 1.0)]["modelo"]["neto_prueba"]) for c, col in tonos.items()], cupo)
    m10 = cst[(10, 1.0)]["modelo"]
    assert k_de[10] >= 200 and abs(k_de[50] - cupo) <= 15, k_de  # «cientos» con 10 USD; «casi el actual» con 50 USD
    s["beneficio"] = pagina(
        f"Si una revisión cuesta 10 USD, conviene revisar cientos de pagos al día, no {cupo}",
        _split(F["beneficio"],
               '<p class="sub">Neto = fraude detenido − costo × revisiones</p>'
               f'<p class="big">{mil(m10["neto_prueba"] - m10["neto_60"], True)} <span>mil USD</span></p>'
               f'<p>más de neto en la prueba con 10 USD por revisión y el cupo de {ent(k_de[10])} que eligió el desarrollo. '
               f'Con 50 USD, el mejor cupo es {k_de[50]}, casi el actual.</p>'
               f'<div class="rule"><p>En los {2 * len(costos_t)} escenarios de costo, el modelo deja más neto que la regla y la logística.</p></div>'
               if gana_c == 2 * len(costos_t) else
               '<p class="sub">Neto = fraude detenido − costo × revisiones</p>'),
        fase=FASE[5])

    # 6 · Despliegue
    s["despliegue"] = pagina(
        "Despliegue: el mismo equipo y la misma cola; cambia el orden",
        '<div class="fill centro"><div class="etapas">'
        f'<div><p class="cuando">Cada noche</p><h3>Cola de {cupo}</h3><p>Se puntúan los pagos del día; los {cupo} con más fraude esperado pasan a '
        'revisión. El equipo decide.</p></div>'
        f'<div><p class="cuando">Cada semana</p><h3>Reentrenar y vigilar</h3><p>Reentrenar con pagos de más de {margen} días, que ya tienen '
        'etiqueta. Vigilar dólares por revisión y precisión.</p></div>'
        '<div><p class="cuando">Primer mes</p><h3>Piloto</h3><p>Días al azar con la cola actual o con la del modelo, para medir el efectivo '
        'recuperado.</p></div>'
        '<div class="respaldo"><p class="cuando">Si falla</p><h3>Volver a la regla</h3><p>Si el modelo queda dos semanas por debajo de la regla, '
        'se regresa a ella.</p></div></div>'
        '<p class="takeaway">Un cambio al modelo se adopta solo si gana en días que su búsqueda no vio.</p></div>',
        fase=FASE[5])

    # Cierre: recomendación
    s["cierre"] = (
        '<section class="slide cierre" data-title="Recomendación"><p class="kicker">Recomendación</p>'
        '<h2>Ordenar la cola de revisión por fraude esperado</h2><div class="cierre-cuerpo">'
        f'<div><p class="big">{mil(extra, True)} <span>mil USD</span></p>'
        f'<p class="lead">más fraude detenido en dos meses, con las mismas {cupo} revisiones diarias</p>'
        f'<p class="antes">Práctica actual <b>{mil(tot(REGLA))}</b> → modelo <b class="azul">{mil(tot(FINAL))}</b> mil USD</p></div>'
        '<ol class="pasos3">'
        f'<li><b>Adoptar el modelo con el cupo actual</b><span>{pct(extra / tot(REGLA))} de fraude detenido, sin más personal</span></li>'
        '<li><b>Confirmarlo con un piloto de un mes</b><span>días al azar, cola actual contra modelo: mide el efectivo recuperado</span></li>'
        f'<li><b>Ajustar el cupo al costo real de revisar</b><span>si una revisión cuesta 10 USD, conviene revisar cientos de pagos al día, no {cupo}</span></li>'
        '</ol></div></section>')

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

    # Un día de la prueba: los 60 revisados quedan arriba de la línea de fraude esperado
    s["dia"] = ap(
        f"Los 60 pagos revisados de un día quedan arriba de {dia['corte']:,.0f} USD de fraude esperado",
        f'<figure class="fill">{F["decision"]}</figure>',
        "Ejes en escala logarítmica: un pago caro entra a la cola con menos probabilidad que uno barato", FASE[0])

    # CRISP-DM
    fases = (("Negocio", "Decisión diaria con cupo fijo, dólares por celda y costo de revisar",
              "Matriz de confusión en dólares, t*&nbsp;=&nbsp;C&nbsp;/&nbsp;LTV, curva de beneficio", ("decision", "matriz", "beneficio", "costo", "dia")),
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
.nw { white-space: nowrap; }
.split.fill { grid-template-rows: minmax(0, 1fr); }
.split.fill > figure { height: 100%; }
.cover > div { max-width: 860px; }
.cover p { max-width: 820px; }
.cover small { margin-top: 56px; }
.cover .map-note { left: 1070px; right: auto; width: 720px; bottom: 120px; line-height: 1.35; }
.argument code { font: 500 .9em var(--mono); }
.argument .measure em { color: var(--blue); }
.two-numbers b.orange { color: var(--orange); }
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
.tabla.crisp { font-size: 22px; }
.tabla.crisp th, .tabla.crisp td { padding: 9px 22px 9px 0; }
.tabla.crisp tbody th { font-size: 24px; width: 15%; }
/* Lámina de la decisión */
.decision { display: grid; grid-template-columns: 500px minmax(0, 1fr); gap: 120px; align-items: center; }
.cifras { display: flex; flex-direction: column; gap: 44px; }
.cifras p { margin: 0; display: flex; flex-direction: column; }
.cifras b { font: 600 100px/.95 var(--display); letter-spacing: -.04em; color: var(--ink); }
.cifras b.azul { color: var(--blue); }
.cifras b.naranja { color: var(--orange); }
.cifras span { margin-top: 10px; font: 400 28px/1.25 var(--sans); color: var(--muted); }
.ficha { display: grid; grid-template-columns: 220px minmax(0, 1fr); margin: 0; font: 400 32px/1.3 var(--sans); border-top: 2px solid var(--line); }
.ficha dt, .ficha dd { margin: 0; padding: 25px 0; border-bottom: 2px solid var(--line); }
.ficha dt { font-weight: 600; color: var(--ink); }
.ficha dd { color: var(--text); }
/* Lámina del valor de cada caso */
.split.valor { grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr); gap: 96px; align-items: center; }
.matrix.valor { border-spacing: 10px 10px; }
.matrix.valor th:first-child { width: 23%; }
.matrix.valor thead th { font-size: 28px; }
.matrix.valor tbody th { font-size: 31px; }
.matrix.valor td { padding: 28px 18px; white-space: normal; }
.matrix.valor td b { display: block; font-size: 54px; }
.matrix.valor td small { margin-top: 10px; font-size: 23px; }
.matrix.valor td.pierde { --cell: rgba(242,196,173,.7); }
.matrix.valor td.pierde b { color: var(--orange); }
.formula { margin: 30px 0 0; font: 400 29px/1.38 var(--sans); color: var(--text); }
.formula b { color: var(--blue); }
.formula-nota { margin: 14px 0 0; font: 400 23px/1.3 var(--sans); color: var(--muted); }
.ejemplos > .sub { margin: 0 0 26px; font: 500 34px/1.2 var(--display); letter-spacing: -.017em; }
.caso { margin: 0 0 22px; padding: 24px 28px; background: #f3f5f8; border-left: 8px solid var(--blue); }
.caso.pasa { border-left-color: var(--orange); }
.caso .cuenta { margin: 0; font: 500 32px/1.2 var(--sans); white-space: nowrap; }
.caso .cuenta b { font: 600 40px var(--display); color: var(--blue); }
.caso.pasa .cuenta b { color: var(--orange); }
.caso .veredicto { margin: 10px 0 0; font: 400 27px/1.3 var(--sans); color: var(--text); }
.ejemplos .muted { margin: 6px 0 0; font: 400 25px/1.3 var(--sans); }
/* Despliegue */
.centro { display: flex; flex-direction: column; justify-content: center; gap: 70px; }
.etapas { display: grid; grid-template-columns: repeat(4, 1fr); gap: 48px; }
.etapas > div { border-top: 6px solid var(--blue); padding-top: 26px; }
.etapas > div.respaldo { border-top-color: var(--orange); }
.etapas .cuando { margin: 0; font: 500 24px var(--mono); color: var(--blue); }
.etapas .respaldo .cuando { color: var(--orange); }
.etapas h3 { margin: 14px 0 18px; font: 600 42px/1.1 var(--display); letter-spacing: -.02em; }
.etapas p:not(.cuando) { margin: 0; font: 400 29px/1.38 var(--sans); color: var(--text); }
/* Cierre */
.cierre { justify-content: center; }
.cierre .kicker { margin: 0 0 -28px; }
.cierre h2 { font-size: 76px; }
.cierre-cuerpo { display: grid; grid-template-columns: 600px minmax(0, 1fr); gap: 110px; align-items: start; margin-top: 36px; }
.cierre-cuerpo .big { margin: 0; color: var(--blue); font: 600 132px/.95 var(--display); letter-spacing: -.045em; white-space: nowrap; }
.cierre-cuerpo .big span { font: 500 54px var(--display); color: var(--muted); letter-spacing: -.04em; }
.cierre-cuerpo .lead { margin: 20px 0 0; font: 400 32px/1.3 var(--sans); color: var(--text); }
.cierre-cuerpo .antes { margin: 40px 0 0; padding-top: 28px; border-top: 2px solid var(--line); font: 400 27px/1.4 var(--sans); color: var(--muted); }
.cierre-cuerpo .antes b { font: 600 36px var(--display); color: var(--orange); }
.cierre-cuerpo .antes b.azul { color: var(--blue); }
.pasos3 { list-style: none; margin: 0; padding: 0; counter-reset: paso; }
.pasos3 li { counter-increment: paso; display: grid; grid-template-columns: 74px minmax(0, 1fr); column-gap: 10px; padding: 28px 0;
  border-top: 2px solid var(--line); }
.pasos3 li:last-child { border-bottom: 2px solid var(--line); }
.pasos3 li::before { content: counter(paso); grid-row: span 2; font: 600 54px/1 var(--display); color: var(--blue); }
.pasos3 b { font: 600 40px/1.15 var(--display); letter-spacing: -.02em; }
.pasos3 span { margin-top: 10px; font: 400 28px/1.35 var(--sans); color: var(--text); }
"""
