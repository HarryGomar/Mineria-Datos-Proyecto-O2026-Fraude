"""Contenido de la presentación, con gráficas vectoriales. Todas las cifras se leen de resultados/."""
from __future__ import annotations

import csv
import json
import math

import numpy as np

from . import svg as G
from .deck import escribir, pagina
from .rutas import RAIZ, RESULTADOS

SALIDA = RAIZ / "presentacion" / "que-pagos-revisar.html"
LAMINAS = RAIZ / "presentacion" / "laminas.json"  # clave de cada lámina → posición (para reporte y cuaderno)
GUION = RAIZ / "presentacion" / "guion.md"
APENDICE = "apendice appendix"
P = ("P1", "P2")
NOMBRE = {"XGB": "XGBoost", "ENS": "Ensamble XGBoost + bosque", "XGB_pond": "XGBoost ponderado por monto", "RF": "Bosque aleatorio",
          "MLP": "Red neuronal MLP", "CART": "Árbol CART", "ISO": "Bosque de aislamiento", "LOGIT": "Logística",
          "R_segmento": "Regla por segmento", "R_tarjeta": "Regla por tarjeta", "R_tabla": "Regla producto × monto",
          "R_monto": "Mayor monto primero", "R_velocidad": "Regla de velocidad", "R_correo": "Regla por correo"}
pct, mil = G.pct, G.mil
PALABRA = {3: "Tres", 4: "Cuatro", 5: "Cinco", 6: "Seis", 7: "Siete", 8: "Ocho", 9: "Nueve"}
GRUPO = {"ventanas": "Ventanas de velocidad", "perfil": "Perfil del monto", "novedad": "Novedad y diversidad",
         "compartido": "Entidades compartidas", "texto": "Cadenas descompuestas", "monto_fino": "Forma del monto",
         "frecuencia": "Frecuencia de categorías", "uid_fino": "Cliente fino", "etiquetas": "Historial de contracargos"}
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


def _iguala(curvas, per, pol, meta):
    """Fracción de pagos de cada día que la política necesita revisar para llegar a meta USD (interpolación lineal)."""
    f = np.array([float(r["fraccion"]) for r in curvas if r["periodo"] == per and r["politica"] == pol])
    u = np.array([float(r["usd"]) for r in curvas if r["periodo"] == per and r["politica"] == pol])
    return float(np.interp(meta, u, f))


def _curva(curvas, per, pol):
    return [(float(r["fraccion"]), float(r["usd"])) for r in curvas if r["periodo"] == per and r["politica"] == pol]


def _condicion(v, op, u, es_cat):
    signo = "≤" if op == "<=" else ">"
    if v == "TransactionAmt":
        return f"monto {signo} {u:,.0f} USD"
    if v.startswith("h_"):
        est = {"previos": "pagos previos", "ultimo": "pagos del último día", "ultima": "pagos de la última semana",
               "segundos": "segundos desde el pago anterior", "razon": "monto / monto medio previo"}
        partes = v[2:].split("_")
        clave = next(k for k in est if k in partes)
        return f"{est[clave]} del {'cliente' if partes[0] == 'cliente' else 'tarjeta'} {signo} {u:,.3g}"
    return f"{'frecuencia de ' if es_cat else ''}{v} {signo} {(f'{u:,.0f}' if abs(u) >= 100 else f'{u:.3g}')}"


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


def crear():
    S, R, X, PJ = _j("desarrollo_seleccion.json"), _j("prueba.json"), _j("exploracion.json"), _j("presentacion.json")
    filas_csv = {(r["periodo"], r["politica"]): r for r in _csv("prueba.csv")}
    curvas = _csv("prueba_curvas.csv")
    FINAL, REGLA, LOGIT, PUB = S["final"], S["mejor_regla"], S["mejor_logit"], "PUBLICADO"
    U, ve = R["umbrales"], R["veredicto"]
    C = {x: R[x]["contrastes"] for x in P}
    cr, cl, cp = ({x: C[x][k] for x in P} for k in (REGLA, LOGIT, PUB))
    usd = {x: R[x]["usd"] for x in P}
    dias = {x: f"días {R[x]['dias'][0]}–{R[x]['dias'][1]}" for x in P}
    un, ck = X["universo"], X["cliente"]
    dv = S["dolares"]
    total = lambda k: dv[k]["D1"] + dv[k]["D2"]  # noqa: E731
    replicas = len(_csv("bootstrap_P1.csv"))
    hip = (("H1", "H1_regla"), ("H2", "H2_logistica"), ("H3", "H3_publicado"))
    pasan = [h for h, k in hip if all(ve[x][k] for x in P)]
    L = _j("lecciones.json")
    p, donde, estado, indice = [], {}, {"principal": None}, {}

    def aqui(clave):
        n = estado["principal"]
        indice[clave] = len(p) + 1
        donde[clave] = len(p) + 1 if n is None else f"A{len(p) - n + 1}"

    # 1 · Portada
    dia = PJ["dia"]
    p.append('<section class="slide cover" data-title="Qué pagos revisar">' + G.portada(dia) +
             '<div><h1>Qué pagos<br>revisar</h1><p>Priorización diaria de revisiones de fraude con un cupo fijo de 60 pagos</p>'
             '<small>Minería de Datos · ITAM · Pagos de comercio electrónico de Vesta (IEEE-CIS)</small></div>'
             f'<p class="map-note">Los {ent(dia["pagos"])} pagos del día {dia["dia"]} en orden de llegada · Azul: los 60 que revisa el modelo · '
             'Naranja: fraudes no revisados</p></section>')

    # Resultado
    aqui("resultado")
    extra = sum(cr[x]["dif"] for x in P)
    graf = G.marcas([(f"{dias[x].capitalize()} · {x}", [("Mejor regla", usd[x][REGLA], G.NARANJA), ("Modelo", usd[x][FINAL], G.AZUL)],
                      cr[x]["dif"], cr[x]["rel"]) for x in P])
    p.append(pagina(
        f"El modelo lleva a revisión <em>{mil(extra)} mil USD más</em> de fraude",
        _split(graf, f'<p class="big">{mil(extra, True)}</p><p class="sub">mil USD adicionales de fraude en la cola durante los dos meses de prueba, con el mismo número de revisiones</p>'
               f'<div class="rule"><p><b>{_y(pasan)} se cumplen en los dos meses.</b></p>'
               f'<p>Ventaja sobre la logística: {pct(cl["P1"]["rel"])} y {pct(cl["P2"]["rel"])}; sobre ordenar solo por probabilidad: '
               f'{pct(cp["P1"]["rel"])} y {pct(cp["P2"]["rel"])}.</p></div>'),
        f"Prueba congelada: {dias['P1']} y {dias['P2']} · Mejor regla: tasa histórica de fraude por segmento × monto · "
        "Dólares de los pagos etiquetados como fraude que entran a la cola"))

    # Decisión
    aqui("decision")
    p.append(pagina(
        "Qué 60 pagos <em>revisar cada día</em>",
        f'<div class="split split-right fill"><aside class="argument"><p class="sub">Día {dia["dia"]} · {ent(dia["pagos"])} pagos</p>'
        f'<p class="big">60 <span>de {ent(dia["pagos"])}</span></p>'
        '<p>Al cierre de cada día, el equipo de riesgo envía a revisión manual pagos ya autorizados. Un fraude detectado se detiene antes del contracargo.</p>'
        '<div class="rule"><p><b>Probabilidad × monto</b></p>'
        f'<p>Se revisan los 60 pagos con mayor fraude esperado. Ese día el corte fue de {dia["corte"]:,.0f} USD.</p></div>'
        f'</aside><figure>{G.dia_decision(dia)}</figure></div>'
        '<div class="clock-line"><p><b>Quién</b><span>El equipo de riesgo del procesador de pagos</span></p>'
        '<p><b>Cuándo</b><span>Al cierre de cada día, con la información disponible hasta ese momento</span></p>'
        '<p><b>Opciones</b><span>Revisar el pago o dejarlo pasar</span></p>'
        f'<p><b>Recurso</b><span>60 revisiones al día: {pct(un["cupo_60_parte_pagos"], False, 1)} de los pagos</span></p></div>',
        "Vesta no publica su criterio actual de revisión; se representa con la mejor regla del periodo de desarrollo"))

    # Matriz de confusión en dólares
    aqui("matriz")
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
    p.append(pagina(
        "Matriz de confusión <em>en dólares</em>",
        f'<div class="split matrix-split fill"><div class="matrix-block">{matriz}</div><aside class="argument">'
        f'<p class="sub">{ent(R["P2"]["revisiones"])} revisiones en {R["P2"]["n_dias"]} días</p>'
        f'<p><b class="measure">{pct(a["precision"], False)} → <em>{pct(b["precision"], False)}</em></b><br>de la cola es fraude</p>'
        f'<p><b class="measure">{pct(a["parte_usd_fraude"], False)} → <em>{pct(b["parte_usd_fraude"], False)}</em></b><br>del dinero de fraude del mes entra a la cola</p>'
        '<p class="muted rule">Con un cupo fijo, la métrica de decisión es la celda superior izquierda: dólares de fraude dentro de la cola.</p></aside></div>',
        "Matriz de confusión de la cola: revisado o no × fraude o legítimo · Cada política revisa exactamente 60 pagos por día"))

    # Datos y línea de tiempo
    aqui("tiempo")
    total_pagos = sum(v[0] for v in PJ["dias"].values())
    p.append(pagina(
        "Los dos últimos meses <em>se reservan para la prueba</em>",
        f'<figure class="fill">{G.tiempo(PJ["dias"])}</figure>'
        '<div class="clock-line"><p><b>Días 1–60</b><span>Solo entrenamiento</span></p>'
        f'<p><b>Días {S["bloques"]["D1"]["inicio"]}–{S["bloques"]["D2"]["fin"]}</b><span>Desarrollo en dos bloques, donde se tomaron todas las decisiones</span></p>'
        f'<p><b>Días {R["P1"]["dias"][0]}–{R["P2"]["dias"][1]}</b><span>Prueba con el protocolo congelado, evaluada una sola vez</span></p>'
        f'<p><b>{S["margen_dias"]} días</b><span>De margen entre entrenamiento y evaluación, por el retraso de la etiqueta</span></p></div>',
        f"IEEE-CIS Fraud Detection (Vesta, 2019) · Copia pública OpenML 46858, SHA-256 verificado · {ent(total_pagos)} pagos con tarjeta"))

    # Concentración del dinero
    aqui("deciles")
    dec = _csv("exp_deciles_monto.csv")
    filas_dec = [{"rango": (f"≤{float(r['monto_max']):,.0f}" if i < 9 else f">{float(r['monto_min']):,.0f}"),
                  "parte": float(r["parte_usd_fraude"]), "tasa": float(r["tasa"])} for i, r in enumerate(dec)]
    top10 = X["concentracion"]["top_10pct_pagos_por_monto"]
    p.append(pagina(
        "El fraude se concentra <em>en los montos altos</em>",
        _split(G.deciles(filas_dec),
               f'<p class="big">{pct(un["tasa_fraude"], False, 1)}</p><p class="sub">de los pagos es fraude; en dólares, el fraude se concentra en los montos altos</p>'
               f'<div class="rule"><p><b>Mediana: {un["monto_mediano_fraude"]:.0f} USD en fraudes y {un["monto_mediano_legitimo"]:.0f} en legítimos</b></p>'
               '<p>Ordenar solo por probabilidad llenaría la cola de fraudes de monto bajo. Por eso la cola se ordena por <b>probabilidad × monto</b>.</p></div>'),
        f"Días 1–120 · {ent(un['pagos'])} pagos · {mil(un['usd_fraude'])} mil USD de fraude · Deciles de monto con el mismo número de pagos"))

    # Preparación de datos: tubería y cálculo "as-of"
    aqui("tuberia")
    previos = [m for _, m in G.PAGOS_PREVIOS]
    media_prev = sum(previos) / len(previos)
    medidas = [("Pagos previos", ent(len(previos))),
               ("Pagos en el último día", ent(sum(1 for d, _ in G.PAGOS_PREVIOS if d >= -1))),
               ("Pagos en la última semana", ent(sum(1 for d, _ in G.PAGOS_PREVIOS if d >= -7))),
               ("Tiempo desde el pago anterior", f"{-G.PAGOS_PREVIOS[-1][0] * 24 * 60:.0f} min"),
               ("Monto contra su promedio", f"{G.PAGO_HOY / media_prev:.1f} veces")]
    p.append(pagina(
        "Preparación de datos <em>sin información futura</em>",
        _split(G.historial_cliente(),
               '<p class="sub">Cinco medidas para el pago de hoy</p>'
               '<dl class="medidas">' + "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in medidas) + '</dl>'
               '<p class="muted nota-medidas">Cada medida usa solo pagos de segundos anteriores y nunca la etiqueta.</p>', "split split-medidas fill"),
        "Esquema ilustrativo · Cinco llaves: cuatro de tarjeta y una de cliente · "
        "Las transformaciones se ajustan con el entrenamiento de cada bloque"))

    # Ingeniería de variables
    aqui("cliente")
    td = ck["tasa_por_tiempo_desde_anterior"]
    claves = list(td)
    etiquetas = ("Menos de 1 hora", "1 a 24 horas", "1 a 7 días", "Más de 7 días", "Primer pago")
    cats = [(e, td[k]["tasa"], td[k]["pagos"]) for e, k in zip(etiquetas, claves)]
    p.append(pagina(
        "Reconstrucción del <em>identificador de cliente</em>",
        _split(G.cliente(cats, un["tasa_fraude"]),
               f'<p class="big">{pct(cats[0][1], False, 1)}</p><p class="sub">de los pagos es fraude si el mismo cliente pagó hace menos de una hora</p>'
               '<div class="rule"><p><b>Cliente = tarjeta + dirección + día de alta</b></p>'
               f'<p>Día de alta = día del pago − <code>D1</code>. Salen {ent(ck["clientes"])} clientes de {ent(ck["tarjetas_card1"])} tarjetas.</p>'
               '<p class="muted">El historial usa solo pagos anteriores y ninguna etiqueta.</p></div>'),
        "Días 1–120 · Recencia, frecuencia y desvío del monto por tarjeta, por combinaciones de tarjeta, dirección y correo, y por cliente"))

    # Ablación
    aqui("ablacion")
    capas = [total(f"XGB|{c}") for c in ("F1", "F2", "F3", "F4")]
    logits = [max(total(k) for k in dv if k.startswith("LOGIT") and k.endswith(c)) for c in ("F2", "F3")]
    p.append(pagina(
        f"El historial del cliente agrega <em>{mil(capas[2] - capas[1])} mil USD</em> en desarrollo",
        _split(G.ablacion(capas, logits),
               '<p class="sub">Conjunto elegido: F3, con descriptivas, historial y cliente</p>'
               '<p>Mismo XGBoost y mismos hiperparámetros; solo cambia el conjunto de variables.</p>'
               '<div class="rule"><p><b>Columnas opacas C, D y V</b></p>'
               f'<p>Agregarían {mil(capas[3] - capas[2])} mil USD, pero no se sabe en qué momento se calculan. Se excluyeron antes de la prueba.</p></div>'),
        "Desarrollo: días 61–90 y 91–120 sumados, 60 revisiones por día · Rombos: la logística con las mismas variables"))

    # Torneo de desarrollo
    aqui("torneo")
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
    torneo = sorted(((_nombre(k), total(k), color(k)) for k in fam.values()), key=lambda t: -t[1]) + [("Revisar al azar", azar, G.GRIS_CLARO)]
    ven = S["ventaja"]
    p.append(pagina(
        f"En desarrollo, el mejor modelo es <em>{_nombre(FINAL)} con F3</em>",
        _split(G.torneo(torneo),
               '<p class="sub">Criterio fijado antes de comparar</p>'
               '<p>Se elige el modelo flexible con más dólares en los dos bloques, siempre que supere a la mejor logística en cada uno.</p>'
               f'<div class="rule"><p><b class="measure">{pct(ven[REGLA]["D1"])} · {pct(ven[REGLA]["D2"])}</b><br>sobre la mejor regla, D1 · D2</p>'
               f'<p><b class="measure orange">{pct(ven[LOGIT]["D1"])} · {pct(ven[LOGIT]["D2"], d=1)}</b><br>sobre la logística; '
               'el margen estrecho en D2 se registró como riesgo para H2</p></div>'),
        "Miles de USD de fraude en la cola, días 61–120 · Cada familia con su mejor conjunto de variables · Hiperparámetros fijos, sin ajuste fino"))

    # Prueba
    aqui("prueba")
    nombres_prueba = (("Modelo", FINAL, G.AZUL), ("Logística", LOGIT, G.VERDE), ("Mejor regla", REGLA, G.NARANJA),
                      ("Solo probabilidad", PUB, G.GRIS_MEDIO), ("Mayor monto", "R_monto", G.GRIS_CLARO))
    graf = G.prueba([(dias[x].capitalize(), usd[x]["oraculo"], [(n, usd[x][k], c) for n, k, c in nombres_prueba]) for x in P])
    techo = {x: usd[x][FINAL] / usd[x]["oraculo"] for x in P}
    techo_r = {x: usd[x][REGLA] / usd[x]["oraculo"] for x in P}
    p.append(pagina(
        "La prueba confirma <em>el orden del desarrollo</em>",
        f'<figure class="fill">{graf}</figure>'
        f'<p class="takeaway">El oráculo, que conoce las etiquetas, atraparía {mil(usd["P1"]["oraculo"])} y {mil(usd["P2"]["oraculo"])} mil USD con el mismo cupo. '
        f'El modelo captura <b>{pct(techo["P1"], False)} y {pct(techo["P2"], False)}</b> de ese techo; la mejor regla, {pct(techo_r["P1"], False)} y '
        f'{pct(techo_r["P2"], False)}.</p>',
        f"60 revisiones por día: {ent(R['P1']['revisiones'])} y {ent(R['P2']['revisiones'])} en cada mes · Entrenamiento con {ent(R['P1']['entrenamiento'])} y "
        f"{ent(R['P2']['entrenamiento'])} pagos · Fraude total del mes: {mil(R['P1']['usd_fraude'])} y {mil(R['P2']['usd_fraude'])} mil USD"))

    # Intervalos
    aqui("intervalos")
    filas_ic = [("Mejor regla", f"H1 · barra {pct(U['H1'])}", cr["P1"], cr["P2"], U["H1"]),
                ("Mejor logística", f"H2 · barra {pct(U['H2'])}", cl["P1"], cl["P2"], U["H2"]),
                ("Solo probabilidad", "H3 · enfoque de la competencia", cp["P1"], cp["P2"], None),
                ("Bosque aleatorio", "otro flexible", C["P1"]["RF|F3"], C["P2"]["RF|F3"], None),
                ("Ensamble con bosque", "otro flexible", C["P1"]["ENS|F3"], C["P2"]["ENS|F3"], None),
                ("Con columnas opacas", "F4 · fuera por diseño", C["P1"]["XGB|F4"], C["P2"]["XGB|F4"], None)]
    p.append(pagina(
        f"{'Las tres hipótesis' if len(pasan) == 3 else _y(pasan)} <em>se cumplen en los dos meses</em>" if pasan else "Las hipótesis <em>no se cumplen</em>",
        f'<figure class="fill">{G.intervalos(filas_ic)}</figure>',
        f"IC 95% con {ent(replicas)} réplicas pareadas que remuestrean días: las mismas para todas las políticas · Barras fijadas en el protocolo "
        "antes de la prueba · El ensamble queda empatado; las columnas opacas darían más, pero no es posible fecharlas"))

    # Capítulo 4 del curso · comparación final: cada métrica estadística elige otra cola, el dinero elige el modelo
    aqui("metricas")
    CC = _j("curvas_curso.json")
    op, cv, dcl = CC["operacion"], CC["curvas"], CC["deciles"]
    dias_t = f"Días {CC['dias'][0]}–{CC['dias'][1]}"
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
               + "".join(fila_m(*f) for f in filas_m) + '</tbody></table>'
               '<p class="matrix-key">Positivo = fraude · El tono marca a la ganadora de cada fila</p>')
    estad = [g for n, g in ganadores.items() if not n.startswith("Fraude")]
    assert ganadores["Fraude en la cola"] == "modelo" and "modelo" not in estad, ganadores
    p.append(pagina(
        f"{PALABRA[len(estad)]} métricas de clasificación <em>prefieren otra cola</em>",
        f'<div class="split matrix-split fill"><div class="matrix-block">{tabla_m}</div><aside class="argument">'
        f'<p class="big">{pct(op["nunca"]["exactitud"], False, 1)}</p><p class="sub">de exactitud sin revisar ningún pago, más que cualquiera de las colas</p>'
        f'<div class="rule"><p><b>Solo probabilidad gana {estad.count("solo_p")} de {len(estad)}</b></p>'
        f'<p>pero lleva {mil(op["solo_p"]["usd"])} mil USD a la cola, contra {mil(op["modelo"]["usd"])} mil del modelo. F1 y AUC miden aciertos sin ponderar el monto.</p></div>'
        '</aside></div>',
        f"{dias_t} · Mismo cupo para todas · Fórmulas del capítulo 4 del curso · AUC y AP del puntaje con que se ordena cada cola"))

    # Capítulo 4 del curso · ROC contra precisión–recall con el punto de operación
    aqui("roc")
    ser_r = [dict(cv["modelo"], nombre="Modelo: probabilidad × monto", corto="Modelo", color=G.AZUL, op=op["modelo"]),
             dict(cv["solo_p"], nombre="Solo probabilidad", corto="Solo prob.", color=G.GRIS_MEDIO, op=op["solo_p"]),
             dict(cv["regla"], nombre="Mejor regla", corto="Regla", color=G.NARANJA, op=op["regla"])]
    p.append(pagina(
        "Precisión–recall <em>muestra mejor el punto de operación</em>",
        _split(G.roc_pr(ser_r, CC["prevalencia"]),
               f'<p class="big">{pct(1 - op["modelo"]["precision"], False)}</p><p class="sub">de las revisiones del modelo van a pagos legítimos</p>'
               f'<p>En la ROC, el mismo punto queda junto al eje vertical, con {pct(op["modelo"]["fpr"], False, 1)} de falsos positivos.</p>'
               '<div class="rule"><p><b>Ambas curvas ignoran el monto</b></p>'
               f'<p>Ordenar solo por probabilidad da más AUC ({cv["solo_p"]["auc"]:.2f} contra {cv["modelo"]["auc"]:.2f}) y lleva '
               f'{pct(1 - op["solo_p"]["usd"] / op["modelo"]["usd"], False)} menos dinero a la cola.</p></div>'),
        f"{dias_t}: {ent(CC['pagos'])} pagos y {pct(CC['prevalencia'], False, 1)} de fraude · Curvas con el orden de todo el periodo; "
        "puntos: la cola real de 60 por día"))

    # Capítulo 4 del curso · ganancia acumulada y lift
    aqui("ganancia")
    gm, cupo_t = CC["ganancia"], CC["cupo_fraccion"]
    u_cupo = op["modelo"]["usd"] / CC["usd_fraude"]
    u_regla = op["regla"]["usd"] / CC["usd_fraude"]
    ahorro_t = 1 - float(np.interp(u_regla, gm["modelo"]["usd"], gm["modelo"]["fraccion"])) / cupo_t
    ser_g = [dict(nombre="Modelo: dólares de fraude", color=G.AZUL, fraccion=gm["modelo"]["fraccion"], valores=gm["modelo"]["usd"]),
             dict(nombre="Modelo: número de fraudes", color=G.AZUL, trazos=True, fraccion=gm["modelo"]["fraccion"], valores=gm["modelo"]["fraudes"]),
             dict(nombre="Mejor regla: dólares", color=G.NARANJA, fraccion=gm["regla"]["fraccion"], valores=gm["regla"]["usd"])]
    p.append(pagina(
        f"Revisar {pct(cupo_t, False)} de los pagos <em>captura {pct(u_cupo, False)} del fraude en USD</em>",
        _split(G.ganancia_acum(ser_g, cupo_t, (dcl[0]["usd_acum"], dcl[0]["fraudes_acum"])),
               f'<p class="big">×{u_cupo / cupo_t:.0f}</p><p class="sub">lift en dólares de la cola de 60; al azar se capturaría {pct(cupo_t, False)}</p>'
               '<div class="rule two-numbers">'
               f'<p><b><em>×{dcl[0]["lift_usd"]:.1f}</em></b><span>lift en dólares del primer decil</span></p>'
               f'<p><b>×{dcl[0]["lift"]:.1f}</b><span>lift en número de fraudes</span></p></div>'
               f'<p class="muted">El modelo alcanza los dólares de la mejor regla con {pct(ahorro_t, False)} menos revisiones.</p>'),
        f"{dias_t} · Decil: 10% de los pagos de cada día en el orden del modelo · Lift = parte del fraude capturado / parte de los pagos revisados"))

    # Capítulo 4 del curso · curva de beneficio contra el umbral
    aqui("montana")
    um = CC["umbral"]
    bm = um["politicas"]["modelo"]
    tonos = {"10": G.AZUL, "20": "#4f8fc4", "50": G.AZUL_MEDIO}
    cur = [dict(costo=int(c), color=tonos[c], valores=bm[c]["curva"], t_dev=bm[c]["t_dev"], neto_dev=bm[c]["neto_prueba"]) for c in tonos]
    cima = {c: um["t"][int(np.argmax(bm[c]["curva"]))] for c in tonos}
    p.append(pagina(
        "El beneficio neto es máximo <em>cerca del costo</em>",
        _split(G.montana(um["t"], cur, CC["corte_60"]["mediana"]),
               '<p class="sub">Regla del curso: revisar si p&nbsp;≥&nbsp;t*&nbsp;=&nbsp;C&nbsp;/&nbsp;LTV</p>'
               '<p>Aquí el valor en riesgo es el monto del pago, de modo que la regla equivale a revisar si <b>p × monto ≥ c</b>. Por eso la cola se ordena por fraude esperado.</p>'
               f'<div class="rule"><p><b>Máximos en t = {cima["10"]:.0f}, {cima["20"]:.0f} y {cima["50"]:.0f} USD</b></p>'
               '<p>Para costos de 10, 20 y 50 USD, el máximo queda un poco por debajo de c porque p subestima el fraude. '
               f'Revisar 60 pagos al día equivale a un umbral de {CC["corte_60"]["mediana"]:.0f} USD.</p></div>'),
        f"{dias_t} · Revisar todo pago con p × monto ≥ t, sin cupo · Neto = recuperado − costo × revisiones · "
        f"Puntos: umbral elegido en los días {S['bloques']['D1']['inicio']}–{S['bloques']['D2']['fin']}"))

    # Para el apéndice: las láminas anteriores de exactitud, ganancia en dólares por periodo y valor marginal
    co = PJ["cola"]["P2"]
    auc = float(filas_csv[("P2", FINAL)]["auc"])
    filas_ex = [("Solo probabilidad", co["publicado"], G.GRIS_MEDIO), ("Mejor regla", co["regla"], G.NARANJA),
                ("Probabilidad × monto", co["modelo"], G.AZUL)]
    menos = 1 - co["modelo"]["fraudes_por_dia"] / co["publicado"]["fraudes_por_dia"]
    ap_exactitud = pagina(
        "Más fraudes atrapados <em>no implica más dólares</em>",
        _split(G.exactitud([(n, c["fraudes_por_dia"], c["usd_por_revision"], c["monto_medio_fraude"], col) for n, c, col in filas_ex]),
               f'<p class="sub">Mismo modelo, mismo AUC: {auc:.3f}</p><p class="big">{pct(cp["P2"]["rel"])}</p>'
               f'<p>más dólares al multiplicar por el monto, con {pct(menos, False)} menos fraudes atrapados.</p>'
               '<div class="rule"><p><b>La competencia evaluaba con AUC</b></p>'
               '<p>Con un cupo fijo, lo relevante es el dinero que aporta cada revisión.</p></div>'),
        f"Días 152–182 · Promedio por día de cada cola · En los días 121–151: {pct(cp['P1']['rel'])} sobre ordenar solo por probabilidad", APENDICE)

    x = "P2"
    series = [("Modelo", _curva(curvas, x, FINAL), G.AZUL), ("Logística", _curva(curvas, x, LOGIT), G.VERDE),
              ("Mejor regla", _curva(curvas, x, REGLA), G.NARANJA), ("Mayor monto", _curva(curvas, x, "R_monto"), G.GRIS_MEDIO)]
    cupo = {y: 60 / R[y]["pagos_por_dia"] for y in P}
    fr = {y: _iguala(curvas, y, FINAL, usd[y][REGLA]) for y in P}
    ahorro = {y: 1 - fr[y] / cupo[y] for y in P}
    lift = {y: usd[y][FINAL] / R[y]["azar_esperado"] for y in P}
    liftr = {y: usd[y][REGLA] / R[y]["azar_esperado"] for y in P}
    ap_curvas = pagina(
        "Los dólares de la regla <em>con menos revisiones</em>",
        _split(G.curvas(series, cupo[x], fr[x], usd[x][REGLA]),
               f'<p class="big">{pct(ahorro[x], False)}</p><p class="sub">menos revisiones para atrapar lo mismo que la mejor regla</p>'
               '<div class="rule two-numbers">'
               f'<p><b><em>×{lift[x]:.0f}</em></b><span>modelo contra azar</span></p>'
               f'<p><b>×{liftr[x]:.0f}</b><span>regla contra azar</span></p></div>'
               f'<p class="muted">En los días 121–151: {pct(ahorro["P1"], False)} menos, ×{lift["P1"]:.0f} y ×{liftr["P1"]:.0f}.</p>'),
        "Días 152–182 · Ganancia acumulada en dólares con la logística y el monto · Cada política revisa sus pagos en su propio orden", APENDICE)

    mg, tramo = L["marginal"], L["tramo"]
    cst = {(f["costo"], f["recupera"]): f for f in L["costos"]}
    k_de = {c: cst[(c, 1.0)]["modelo"]["K"] for c in (10, 20, 50)}
    banda60 = mg["modelo"][60 // tramo - 1]
    ap_marginal = pagina(
        f"La revisión número 60 aporta <em>{banda60:.0f} USD</em> de fraude",
        _split(G.marginal([("Modelo", mg["modelo"], G.AZUL), ("Logística", mg["logistica"], G.VERDE), ("Mejor regla", mg["regla"], G.NARANJA)],
                          tramo, [(c, k_de[c]) for c in (10, 20, 50)], L["marginal_dev"]["modelo"]),
               f'<p class="big">{mg["modelo"][0]:.0f} <span>USD</span></p><p class="sub">por revisión en los primeros 20 lugares de cada día; '
               f'la regla trae {mg["regla"][0]:.0f}</p>'
               '<div class="rule"><p><b>Conviene revisar más mientras el valor marginal supere el costo</b></p>'
               f'<p>Con 10 USD por revisión convendrían {k_de[10]} al día; con 20, {k_de[20]}; con 50, {k_de[50]}, cerca del cupo actual.</p>'
               f'<p class="muted">En la prueba el valor marginal cae antes; con 10 USD, el mejor cupo habría sido {cst[(10, 1.0)]["modelo"]["kstar_prueba"]}.</p></div>'),
        f"Días {R['P1']['dias'][0]}–{R['P2']['dias'][1]} · Tramos de {tramo} lugares; desde el lugar 100, promedio de cinco tramos · "
        f"Cupos elegidos con las curvas de desarrollo, días {S['bloques']['D1']['inicio']}–{S['bloques']['D2']['fin']}", APENDICE)

    # Costo por revisión: el cupo cambia, el ganador no
    aqui("costo")
    costos_t = (2, 5, 10, 20, 50, 100)
    neto = lambda f, k: f[k]["neto_prueba"]  # noqa: E731
    gana_c = sum(neto(cst[(c, r)], "modelo") > max(neto(cst[(c, r)], "logistica"), neto(cst[(c, r)], "regla")) for c in costos_t for r in (1.0, .5))

    def celda_c(f):
        m, lg, rg = neto(f, "modelo"), neto(f, "logistica"), neto(f, "regla")
        ventaja = (m - max(lg, rg)) / m if m > 0 else 0
        return (f'<td style="--cell:{_tinte(ventaja)}"><b>{mil(m)}</b><small>cupo {ent(f["modelo"]["K"])} al día</small>'
                f'<small>logística {mil(lg)} · regla {mil(rg)}</small></td>')
    tabla_c = ('<table class="matrix costo"><thead><tr><th scope="col">Neto del modelo, mil USD</th><th scope="col">Recupera todo</th>'
               '<th scope="col">Recupera la mitad</th></tr></thead><tbody>'
               + "".join(f'<tr><th scope="row">{c} USD<small>por revisión</small></th>{celda_c(cst[(c, 1.0)])}{celda_c(cst[(c, .5)])}</tr>' for c in costos_t)
               + '</tbody></table>')
    p.append(pagina(
        "Con cualquier costo, <em>el modelo deja más neto</em>" if gana_c == 2 * len(costos_t)
        else f"El modelo deja más neto en <em>{gana_c} de {2 * len(costos_t)} escenarios de costo</em>",
        f'<div class="split matrix-split fill"><div class="matrix-block">{tabla_c}</div><aside class="argument">'
        f'<p class="big">{gana_c} <span>de {2 * len(costos_t)}</span></p>'
        '<p class="sub">escenarios en que el modelo deja más neto que la regla y que la logística</p>'
        '<div class="rule"><p><b>Cada política elige su cupo en desarrollo</b></p>'
        f'<p>Cada una usa el cupo que maximiza su neto en los días {S["bloques"]["D1"]["inicio"]}–{S["bloques"]["D2"]["fin"]}, y el neto se mide en la prueba. '
        f'Con 100 USD por revisión, la regla deja de revisar.</p></div></aside></div>',
        f"Neto = recuperado − costo × revisiones, días {R['P1']['dias'][0]}–{R['P2']['dias'][1]} · Recuperar la mitad equivale a duplicar el costo · "
        "El tono crece con la ventaja"))

    # Calibración
    aqui("calibracion")
    ca, bb = L["calibracion"], L["brier_base"]
    habil = {k: 1 - ca[k]["brier"] / bb for k in ca}
    cola_c = ca["modelo"]["cola"]
    p.append(pagina(
        "Las probabilidades <em>subestiman un poco el fraude</em>",
        _split(G.calibracion([("Modelo", ca["modelo"]["bins"], G.AZUL), ("Logística", ca["logistica"]["bins"], G.VERDE)]),
               f'<p class="big">{pct(habil["modelo"], False)}</p><p class="sub">menos error de Brier que asignar a todos la tasa media; '
               f'la logística, {pct(habil["logistica"], False)}</p>'
               '<div class="rule"><p><b>Fraude esperado → observado en la cola</b></p>'
               f'<p><b class="measure">{mil(cola_c["P1"]["esperado"])} → <em>{mil(cola_c["P1"]["observado"])}</em></b> · '
               f'<b class="measure">{mil(cola_c["P2"]["esperado"])} → <em>{mil(cola_c["P2"]["observado"])}</em></b><br>mil USD, P1 · P2</p>'
               '<p class="muted">La regla t*&nbsp;=&nbsp;C&nbsp;/&nbsp;LTV supone p calibrada; como p subestima, el umbral óptimo queda un poco por debajo del costo.</p></div>'),
        f"Días {R['P1']['dias'][0]}–{R['P2']['dias'][1]} · Ocho tramos de probabilidad · Brier: modelo {ca['modelo']['brier']:.4f}, "
        f"logística {ca['logistica']['brier']:.4f}, tasa media {bb:.4f}"))

    # Robustez
    aqui("robustez")
    rb = {y: R[y]["robustez"] for y in P}
    lim = R["P1"]["limpio"]

    def fila(titulo, sub, vals, fmt=lambda v: pct(v, d=1), tinte=_tinte):
        celdas = "".join('<td style="--cell:rgba(238,242,246,1)"><b class="muted">—</b></td>' if v is None
                         else f'<td style="--cell:{tinte(v)}"><b>{fmt(v)}</b></td>' for v in vals)
        return f'<tr><th scope="row">{titulo}<small>{sub}</small></th>{celdas}</tr>'
    gana = lambda y, c: R[y]["dias_que_gana"][c]  # noqa: E731
    rob = ('<table class="matrix compacta"><thead><tr><th scope="col">Ventaja del modelo</th><th scope="col">Regla · P1</th>'
           '<th scope="col">Regla · P2</th><th scope="col">Logística · P1</th><th scope="col">Logística · P2</th></tr></thead><tbody>'
           + fila("<em>Principal</em>", "60 revisiones por día", [cr["P1"]["rel"], cr["P2"]["rel"], cl["P1"]["rel"], cl["P2"]["rel"]])
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
    p.append(pagina(
        "La ventaja se mantiene <em>en todos los escenarios</em>" if min(peor_r, peor_l) > 0 else "La ventaja <em>depende del escenario</em>",
        f'<div class="split matrix-split fill"><div class="matrix-block">{rob}</div><aside class="argument">'
        f'<p class="sub">Peor caso contra la regla</p><p class="big">{pct(peor_r, d=1)}</p>'
        f'<div class="rule"><p class="measure green">{pct(peor_l, d=1)}</p><p>Peor caso contra la logística, donde el margen es menor.</p></div>'
        '</aside></div>',
        f"P1: {dias['P1']} · P2: {dias['P2']} · Escenarios fijados en el protocolo · Días 121–144: "
        f"IC 95% contra la regla {ic(lim['contrastes'][REGLA]['rel_ic95'])}"))

    # Traza del dinero
    aqui("traza")
    tz = PJ["traza"]
    p.append(pagina(
        "Origen de la <em>diferencia en dólares</em>",
        f'<figure class="fill">{G.traza([(dias[y].capitalize(), tz[y]) for y in P])}</figure>'
        '<div class="clock-line">'
        f'<p><b>{ent(tz["P1"]["pagos_solo_modelo"])} · {ent(tz["P2"]["pagos_solo_modelo"])}</b><span>revisiones en las que modelo y regla difieren</span></p>'
        f'<p><b>{tz["P1"]["fraudes_solo_modelo"]} · {tz["P2"]["fraudes_solo_modelo"]}</b><span>fraudes solo del modelo, de '
        f'{tz["P1"]["monto_medio_fraude_solo_modelo"]:,.0f} y {tz["P2"]["monto_medio_fraude_solo_modelo"]:,.0f} USD</span></p>'
        f'<p><b class="orange">{tz["P1"]["fraudes_solo_regla"]} · {tz["P2"]["fraudes_solo_regla"]}</b><span>fraudes solo de la regla, de '
        f'{tz["P1"]["monto_medio_fraude_solo_regla"]:,.0f} y {tz["P2"]["monto_medio_fraude_solo_regla"]:,.0f} USD</span></p>'
        f'<p><b class="muted">{mil(tz["P1"]["ninguno"])} · {mil(tz["P2"]["ninguno"])} mil</b><span>USD de fraude que no revisa ninguna</span></p></div>',
        "Cada dólar de fraude del mes cae en una sola caja: ambos + solo modelo + solo regla + ninguno = fraude total"))

    # Observado y supuesto
    aqui("observado")
    obs = ('<table class="tabla"><thead><tr><th>Cantidad</th><th>Tipo</th><th>Qué significa para el resultado</th></tr></thead><tbody>'
           '<tr><th>Monto de cada pago</th><td class="obs">Observado</td><td>USD tal como los registró Vesta</td></tr>'
           '<tr><th>Fraude o legítimo</th><td class="obs">Observado, con la regla de Vesta</td><td>Contracargo reportado; Vesta marca también los pagos '
           'posteriores de la misma cuenta, correo o dirección</td></tr>'
           f'<tr><th>Fraude que se repite por cliente</th><td class="obs">Observado</td><td>{pct(ck["fraudes_en_clientes_con_2_o_mas"], False)} de los fraudes '
           'está en clientes con dos o más; parte del acierto proviene de reconocer cuentas ya marcadas</td></tr>'
           '<tr><th>Dinero que salva una revisión</th><td class="sup">Supuesto</td><td>El monto completo del fraude en la cola. Mide exposición, no efectivo '
           'recuperado. Igual para todas las políticas</td></tr>'
           f'<tr><th>Cuándo llega la etiqueta</th><td class="sup">Supuesto</td><td>{S["margen_dias"]} días de margen entre entrenar y evaluar</td></tr>'
           '<tr><th>Práctica actual</th><td class="sup">Supuesto</td><td>No está publicada; la representa la mejor de seis reglas del desarrollo</td></tr>'
           '</tbody></table>')
    p.append(pagina("Cantidades observadas <em>y supuestos</em>", obs,
                    "Datos de diciembre de 2017 a mayo de 2018 con fechas relativas · Los supuestos afectan a todas las políticas por igual"))

    hay_variables = all((RESULTADOS / n).exists() for n in ("variables.json", "anexo_prueba_variables.json"))
    if hay_variables:  # anexo posterior: las láminas aparecen cuando scripts/06 y 07 ya corrieron
        # Mantenimiento · búsqueda de variables con validación cruzada temporal (anexo posterior a la prueba; el veredicto no cambia)
        VA, AX = _j("variables.json"), _j("anexo_prueba_variables.json")
        assert not VA["rapido"] and VA["elegidos"] == AX["elegidos"], "variables.json y el anexo de la prueba no corresponden"
        margen = S["margen_dias"]
        conf, eleg, hp = VA["confirmacion"], VA["elegidos"], VA["hiperparametros"]
        c6 = VA["confirmacion_resultados"]
        mejor_k = "elegido_ajustado" if hp["adopta"] else "elegido"
        base_i, final_i = VA["base_F3"]["total_usd"], VA["final_interno"]["total_usd"]
        cand_g = VA["candidatos"]
        vent = list(VA["internas"].items())

        aqui("validacion")
        filas_v = ([(f"Ventana {i + 1}", "búsqueda", a, b, "interna") for i, (_, (a, b)) in enumerate(vent)]
                   + [("Confirmación", "no se usa en la búsqueda", conf[0], conf[1], "confirma")]
                   + [(f"Prueba {x}", "lectura posterior", R[x]["dias"][0], R[x]["dias"][1], "prueba") for x in P])
        p.append(pagina(
            "Validación cruzada temporal <em>para mejorar las variables</em>",
            f'<figure class="fill">{G.validacion_temporal(filas_v, margen, R["P2"]["dias"][1])}</figure>'
            f'<p class="takeaway">{str(PALABRA.get(len(cand_g), len(cand_g)))} grupos de variables compiten en tres ventanas de búsqueda; '
            f'los días {conf[0]}–{conf[1]} confirman el resultado y la prueba se lee una sola vez.</p>',
            f"Diseño registrado en docs/anexo_variables.md antes de correr · {margen} días de margen entre entrenamiento y evaluación"))

        aqui("escalada")
        pasos = [dict(etiqueta="F3", sub="protocolo", usd=base_i, previo=None, candidatos=[])]
        for r in VA["rondas"]:
            cand = [(GRUPO_CORTO[g], v["total_usd"]) for g, v in r["pruebas"].items()]
            if r["acepta"]:
                pasos.append(dict(etiqueta=f"+ {GRUPO_CORTO[r['mejor']]}", sub=f"{pct(r['ganancia'], d=1)} · {r['suben']} de {len(vent)}",
                                  usd=r["pruebas"][r["mejor"]]["total_usd"], previo=r["partida_usd"], candidatos=cand))
            else:
                pasos.append(dict(etiqueta=f"Ronda {r['ronda']}\nse detiene", sub=f"{pct(r['ganancia'], d=1)} · {r['suben']} de {len(vent)}",
                                  usd=None, previo=r["partida_usd"], candidatos=cand))
        for a in VA["atras"]:
            if a["quita"]:
                pasos.append(dict(etiqueta=f"− {GRUPO_CORTO[a['grupo']]}", sub="pasada hacia atrás", usd=a["sin_usd"], previo=None, candidatos=[]))
        rj = VA["rejilla"]
        mejor_rj = max(rj, key=lambda f: f["total_usd"])
        pasos.append(dict(etiqueta="+ rejilla" if hp["adopta"] else "Rejilla\nse descarta", usd=mejor_rj["total_usd"] if hp["adopta"] else None,
                          sub=f"{pct(hp['ganancia'], d=1)} · {hp['suben']} de {len(vent)}", previo=final_i,
                          candidatos=[(f"{f['params']['max_depth']}/{f['params']['min_child_weight']}", f["total_usd"]) for f in rj]))
        final_hp = mejor_rj["total_usd"] if hp["adopta"] else final_i
        rechazados = [GRUPO_CORTO[g] for g in cand_g if g not in eleg]
        sujeto = {1: "Un grupo nuevo sube", 2: "Dos grupos nuevos suben"}.get(len(eleg), f"{PALABRA.get(len(eleg), len(eleg))} grupos nuevos suben")
        p.append(pagina(
            (f"{sujeto} <em>{pct(final_hp / base_i - 1, False, d=1)} en validación</em>" if eleg
             else "Ningún grupo nuevo <em>cumple la regla de aceptación</em>"),
            _split(G.escalada(pasos, VA["regla"]["min_ganancia"]),
                   f'<p class="big">{pct(final_hp / base_i - 1, d=1)}</p><p class="sub">{mil(base_i)} → {mil(final_hp)} mil USD, medidos en las mismas '
                   'ventanas que eligen los grupos</p>'
                   f'<div class="rule"><p><b>{"Aceptados: " + _y([GRUPO_CORTO[g] for g in eleg]) if eleg else "Ningún grupo aceptado"}</b></p>'
                   f'<p>Cada uno sube el total al menos {VA["regla"]["min_ganancia"] * 100:.0f}% y mejora en {VA["regla"]["min_ventanas"]} de '
                   f'{len(vent)} ventanas. No cumplen: {_y(rechazados)}.</p>'
                   + (f'<p class="muted">La rejilla de hiperparámetros agrega {pct(hp["ganancia"], d=1)} y se adopta.</p>' if hp["adopta"] else
                      '<p class="muted">La rejilla de hiperparámetros no supera la barra.</p>')
                   + '</div>'),
            f"Días {vent[0][1][0]}–{vent[-1][1][1]} en {len(vent)} ventanas de 15 días · XGBoost del protocolo · "
            "Rejilla: profundidad / peso mínimo por hoja"))

        aqui("confirmacion")
        cc = c6["contrastes"]
        pc = {x: AX[x]["contrastes"] for x in P}
        filas_cf = [("Variables nuevas", "XGBoost, contra F3", G.AZUL, [cc["elegido_vs_F3"]] + [pc[x]["elegido_vs_F3"] for x in P])]
        if hp["adopta"]:
            filas_cf.append(("Con hiperparámetros ajustados", "contra F3", G.AZUL,
                             [cc["elegido_ajustado_vs_F3"]] + [pc[x]["elegido_ajustado_vs_F3"] for x in P]))
        filas_cf += [("Logística con variables nuevas", "contra la logística con F3", G.VERDE,
                      [cc["logit_elegido_vs_logit_F3"]] + [pc[x]["logit_elegido_vs_logit_F3"] for x in P]),
                     ("Historial de contracargos", "no compite · contra variables nuevas", G.GRIS_MEDIO, [cc["con_etiquetas_vs_elegido"], None, None])]
        extremos = [v for _, _, _, cs in filas_cf for c in cs if c for v in c["rel_ic95"]]
        dom = (max(-.4, min(0, math.floor(min(extremos) * 20) / 20)), min(.9, max(.1, math.ceil((max(extremos) + .1) * 20) / 20)))
        cm = cc[f"{mejor_k}_vs_F3"]
        usd_c = c6["usd"]
        dg = c6["dias_gana"]
        confirma = cm["rel_ic95"][0] > 0
        if confirma:
            tit_c = f"En días no usados, la mejora se confirma: <em>{pct(cm['rel'], d=1)}</em>"
        elif cm["rel_ic95"][1] < 0:
            tit_c = "En días no usados, <em>la ganancia no se repite</em>"
        elif cm["rel"] > 0:
            tit_c = f"En días no usados, la mejora de {pct(cm['rel'], d=1)} <em>no es concluyente</em>"
        else:
            tit_c = "En días no usados, <em>la mejora no se confirma</em>"
        etq_c = cc["con_etiquetas_vs_elegido"]
        rep_f3 = {x: AX[x]["reproduce"]["F3"] for x in P}
        exacto = all(abs(a - b) < 1 for a, b in rep_f3.values())
        regla_c = ('<div class="rule"><p><b>Se adoptan las variables nuevas</b></p><p>La ganancia se mantiene en días que la búsqueda no usó.</p>'
                   if confirma else
                   f'<div class="rule"><p><b>F3 se mantiene</b></p><p>La ganancia de {pct(final_hp / base_i - 1, d=1)} se midió en las mismas ventanas '
                   'que eligieron los grupos y no se repite en días nuevos.</p>')
        p.append(pagina(
            tit_c,
            _split(G.confirmacion(filas_cf, [("Confirmación", f"días {conf[0]}–{conf[1]}")] + [(f"Prueba {x}", "lectura posterior") for x in P], dom),
                   f'<p class="big">{pct(cm["rel"], d=1)}</p><p class="sub">{mil(usd_c["F3"])} → {mil(usd_c[mejor_k])} mil USD · '
                   f'IC 95%: {ic(cm["rel_ic95"])}</p>'
                   f'<p>Gana a F3 en {dg[mejor_k]} de {dg["dias"]} días. En la prueba, como lectura posterior: '
                   f'{pct(pc["P1"][f"{mejor_k}_vs_F3"]["rel"], d=1)} y {pct(pc["P2"][f"{mejor_k}_vs_F3"]["rel"], d=1)}.</p>'
                   + regla_c
                   + '<p class="muted">Los contracargos aprenden cómo Vesta propaga la etiqueta; no se usan.</p></div>'),
            f"Entrena con los días 1–{conf[0] - margen - 1} · Bootstrap pareado de {ent(REPLICAS_ANEXO)} réplicas por día · "
            + ("F3 reconstruido reproduce la prueba congelada" if exacto else
               f"F3 reconstruido: {mil(rep_f3['P1'][0])} y {mil(rep_f3['P2'][0])} mil USD, contra {mil(rep_f3['P1'][1])} y "
               f"{mil(rep_f3['P2'][1])} de la corrida congelada")))

    # Despliegue
    aqui("despliegue")
    p.append(pagina(
        "Despliegue <em>y monitoreo</em>",
        '<table class="tabla despliegue"><thead><tr><th>Etapa</th><th>Cuándo</th><th>Qué se hace</th></tr></thead><tbody>'
        '<tr><th>Operación</th><td>Cada noche</td><td>Se puntúan los pagos del día y los 60 con mayor fraude esperado pasan a la cola. '
        'La decisión sobre cada pago sigue siendo del equipo.</td></tr>'
        f'<tr><th>Reentrenamiento</th><td>Cada semana</td><td>Con los pagos de más de {S["margen_dias"]} días, que ya tienen etiqueta.</td></tr>'
        '<tr><th>Piloto</th><td>Primer mes</td><td>Los días se asignan al azar a la cola actual o a la del modelo, para medir el efectivo recuperado.</td></tr>'
        '<tr><th>Monitoreo</th><td>Cada semana</td><td>Dólares por revisión, precisión, monto medio de la cola y mezcla de productos.</td></tr>'
        '<tr><th>Respaldo</th><td>Si el modelo falla</td><td>Si durante dos semanas queda por debajo de la regla, se vuelve a la tabla por segmento.</td></tr>'
        '</tbody></table>',
        "El cupo de 60 revisiones no cambia; cambia qué pagos entran · La comparación usa la mejor regla como práctica actual"))

    # Cierre
    aqui("cierre")
    tot = lambda k: usd["P1"][k] + usd["P2"][k]  # noqa: E731
    p.append(
        '<section class="slide closing" data-title="Recomendación">'
        '<h2>Ordenar la cola <em>con el modelo</em></h2>'
        f'<p class="closing-lead">Con las mismas 60 revisiones diarias, el modelo lleva a la cola {pct(cr["P1"]["rel"])} y {pct(cr["P2"]["rel"])} más dólares de fraude '
        'que la mejor regla en los dos meses de prueba, evaluados una sola vez.</p>'
        '<div class="closing-evidence"><div>'
        f'<p class="closing-label">Mil USD de fraude en la cola, días {R["P1"]["dias"][0]}–{R["P2"]["dias"][1]}</p>'
        '<dl class="closing-counts">'
        f'<div><dt>Mejor regla</dt><dd>{mil(tot(REGLA))}</dd></div>'
        f'<div><dt>Logística</dt><dd class="green">{mil(tot(LOGIT))}</dd></div>'
        f'<div><dt>Modelo</dt><dd class="blue">{mil(tot(FINAL))}</dd></div></dl></div>'
        '<div><p class="closing-label">Pendiente</p>'
        '<p>El efectivo realmente recuperado y la comparación con la práctica actual de Vesta. Un piloto con asignación aleatoria de días permite medir ambos.</p></div></div>'
        f'<footer>Veredicto contra el protocolo congelado: {_y(pasan) if pasan else "ninguna hipótesis"} en los dos meses · '
        f'{"El caso cumple" if R["exito"] else "El caso no cumple"} su criterio de éxito · Seis meses de 2017-2018</footer></section>')
    estado["principal"] = len(p)

    # Apéndice · Veredicto
    aqui("veredicto")
    def celda_h(h, k, y):
        c = C[y][{"H1_regla": REGLA, "H2_logistica": LOGIT, "H3_publicado": PUB}[k]]
        si = ve[y][k]
        return (f'<td style="--cell:{"rgba(13,129,96,.16)" if si else "rgba(242,196,173,.6)"}"><b class="{"green" if si else "orange"}">'
                f'{"Sí" if si else "No"}</b> <b>{pct(c["rel"], d=1)}</b><small>IC 95%: {ic(c["rel_ic95"])}</small></td>')
    textos_h = {"H1": f"Supera a la mejor regla por ≥ {pct(U['H1'])}", "H2": f"Supera a la mejor logística por ≥ {pct(U['H2'])}",
                "H3": "Supera a ordenar solo por probabilidad"}
    ver = ('<table class="matrix"><thead><tr><th scope="col">Hipótesis fijada antes</th>'
           f'<th scope="col">{dias["P1"].capitalize()}</th><th scope="col">{dias["P2"].capitalize()}</th></tr></thead><tbody>'
           + "".join(f'<tr><th scope="row">{h}<small>{textos_h[h]}, límite inferior &gt; 0</small></th>{celda_h(h, k, "P1")}{celda_h(h, k, "P2")}</tr>'
                     for h, k in hip)
           + f'<tr><th scope="row">Éxito del caso<small>H1, H2 y H3 en los dos meses</small></th><td colspan="2" style="--cell:'
             f'{"rgba(13,129,96,.16)" if R["exito"] else "rgba(242,196,173,.6)"}"><b>{"Sí" if R["exito"] else "No"}</b></td></tr></tbody></table>')
    p.append(pagina("Veredicto <em>del protocolo congelado</em>", f'<div class="fill matrix-block">{ver}</div>',
                    f"docs/protocolo.md, congelado con huellas SHA-256 antes de abrir el día 121 · Bootstrap pareado de {ent(replicas)} réplicas por día",
                    APENDICE))

    # Apéndice · Día por día
    aqui("diario")
    dd = [r for r in _csv("prueba_dias.csv")]
    difs = [(int(r["dia"]), float(r[FINAL]) - float(r[REGLA])) for r in dd]
    g_tot = sum(R[y]["dias_que_gana"][REGLA] for y in P)
    n_tot = sum(R[y]["n_dias"] for y in P)
    p.append(pagina(
        f"El modelo supera a la regla <em>en {g_tot} de {n_tot} días</em>",
        f'<figure class="fill">{G.diario(difs)}</figure>'
        '<p class="takeaway">Azul: días en que el modelo captura más; naranja: días en que la regla captura más. '
        'La ventaja no depende de unos pocos días con fraudes grandes.</p>',
        "Dólares de fraude en la cola, modelo menos mejor regla, 60 revisiones por día cada una · La línea punteada separa los dos meses",
        APENDICE))

    # Apéndice · Importancia
    aqui("importancia")
    im = S["diagnosticos_D2"]["importancia_usd"]
    orden = sorted(im, key=lambda k: -im[k])
    p.append(pagina(
        f"Importancia por permutación: <em>{orden[0]}</em> es el grupo principal",
        _split(G.importancia([(k[0].upper() + k[1:], im[k]) for k in orden]),
               '<p class="sub">Permutación por grupo</p>'
               '<p>Se barajan juntas las columnas de un grupo y se mide cuánto dinero pierde la cola.</p>'
               f'<div class="rule"><p><b>Sin el historial del cliente: −{mil(im["historial del cliente"])} mil USD</b></p>'
               '<p>El historial de la tarjeta aporta cerca de cero porque el del cliente ya contiene esa información.</p></div>'),
        f"Días 91–120, modelo entrenado con días 1–60 · Base: {mil(S['diagnosticos_D2']['cordura']['base'])} mil USD", APENDICE))

    # Apéndice · Árbol
    aqui("arbol")
    ar = S["diagnosticos_D2"]["arbol"]
    hojas = sorted(ar["hojas"], key=lambda h: -h["usd_fraude_por_pago"])
    arbol = ('<table class="tabla chica"><thead><tr><th>Hoja: condiciones</th><th class="num">Fraude</th><th class="num">USD de fraude por pago</th>'
             '<th class="num">Pagos</th></tr></thead><tbody>'
             + "".join(f'<tr><td>{" · ".join(_condicion(*r) for r in h["reglas"])}</td><td class="num">{pct(h["tasa"], False, 1)}</td>'
                       f'<td class="num">{h["usd_fraude_por_pago"]:,.2f}</td><td class="num">{ent(h["pagos"])}</td></tr>' for h in hojas)
             + "</tbody></table>")
    p.append(pagina(
        "Árbol de profundidad 3 <em>como conjunto de reglas</em>", arbol,
        f"Entrenado para los días 91–120 · Ordenado por probabilidad × monto lleva {mil(ar['usd_D2'])} mil USD, contra {mil(dv[FINAL]['D2'])} del modelo y "
        f"{mil(dv[REGLA]['D2'])} de la mejor regla", APENDICE))

    # Apéndice · Controles
    aqui("controles")
    cd = S["diagnosticos_D2"]["cordura"]
    ctl = ('<table class="tabla"><thead><tr><th>Política o control, días 91–120</th><th class="num">Mil USD</th><th>Lectura</th></tr></thead><tbody>'
           f'<tr><th>{_nombre(FINAL)} con el cliente</th><td class="num">{mil(cd["base"])}</td><td>Referencia</td></tr>'
           f'<tr><th>El mismo modelo con etiquetas permutadas</th><td class="num">{mil(cd["etiquetas_barajadas"])}</td><td>Solo conserva el efecto del monto; '
           'sin señal real no hay ganancia, lo que descarta una fuga</td></tr>'
           f'<tr><th>Mayor monto primero</th><td class="num">{mil(dv["R_monto"]["D2"])}</td><td>Solo el tamaño del pago</td></tr>'
           f'<tr><th>Regla de velocidad (RFM)</th><td class="num">{mil(dv["R_velocidad"]["D2"])}</td><td>Historial reciente de la tarjeta como regla</td></tr>'
           f'<tr><th>Bosque de aislamiento × monto</th><td class="num">{mil(dv["ISO|F3"]["D2"])}</td><td>La rareza por sí sola no identifica fraude</td></tr>'
           f'<tr><th>Revisar al azar</th><td class="num">{mil(cd["azar_esperado"])}</td><td>Referencia mínima</td></tr></tbody></table>')
    p.append(pagina("Controles: <em>azar, etiquetas permutadas y atípicos</em>", ctl,
                    "Mismo cupo de 60 por día · Recencia, frecuencia y monto entran también como variables del modelo", APENDICE))

    # Apéndice · Calidad
    aqui("calidad")
    fa, pr = X["faltantes"], X["producto"]
    cal = ('<table class="tabla"><thead><tr><th>Hallazgo</th><th>Tratamiento</th></tr></thead><tbody>'
           f'<tr><td>Dispositivo ausente en {pct(fa["DeviceType"], False)} de los pagos; distancia en {pct(fa["dist1"], False)}</td>'
           '<td>Indicador de faltante en cada numérica; categoría propia en cada categórica</td></tr>'
           f'<tr><td>Dirección ausente en {pct(fa["addr1"], False)}; correo en {pct(fa["P_emaildomain"], False)}</td><td>Se conservan porque el faltante también es informativo</td></tr>'
           '<tr><td>Fechas relativas: <code>TransactionDT</code> en segundos desde una referencia</td><td>Días relativos; cupo y evaluación por día</td></tr>'
           f'<tr><td>Producto W: {pct(pr["W"]["parte_pagos"], False)} de los pagos y {pct(pr["W"]["parte_usd_fraude"], False)} del dinero de fraude; '
           f'producto C: tasa de {pct(pr["C"]["tasa"], False, 1)}</td><td>El producto entra al modelo y a las reglas</td></tr>'
           f'<tr><td>{pct(ck["clientes_con_fraude_todo_fraude"], False)} de los clientes con algún fraude tienen todos sus pagos marcados</td>'
           '<td>La etiqueta se propaga a la cuenta; se declara como advertencia</td></tr>'
           '<tr><td>367 columnas opacas C, D y V</td><td>Fuera del modelo final; solo diagnóstico. <code>D1</code> sirve para reconstruir al cliente</td></tr>'
           '</tbody></table>')
    p.append(pagina("Calidad de los datos", cal, "resultados/exploracion.json · Días 1–120", APENDICE))

    # Apéndice · Catálogo de variables
    aqui("catalogo")
    cat_v = ('<table class="tabla chica"><thead><tr><th>Grupo</th><th>Variables</th><th class="num">Cuántas</th><th>Cómo entran a la matriz</th></tr></thead><tbody>'
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
             '</tbody></table>')
    p.append(pagina("93 variables <em>en cinco grupos</em>", cat_v,
                    f"Desbalance de {pct(un['tasa_fraude'], False, 1)}: sin reponderar, para no deformar la probabilidad · "
                    f"Ponderar por monto perdió en desarrollo: {mil(total('XGB_pond|F3'))} contra {mil(total(FINAL))} mil", APENDICE))

    # Apéndice · Candados contra la fuga de información
    aqui("candados")
    fuga = ('<table class="tabla chica"><thead><tr><th>Riesgo</th><th>Control</th><th>Cómo se comprueba</th></tr></thead><tbody>'
            f'<tr><th>El futuro entra al entrenamiento</th><td>Cada bloque entrena con pagos de {S["margen_dias"]} días o más antes de su primer día</td>'
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
            '</tbody></table>')
    p.append(pagina("Seis controles <em>contra la fuga de información</em>", fuga,
                    "Una fuga infla el desempeño en desarrollo y no se sostiene en producción · Los seis controles se fijaron antes de la prueba", APENDICE))

    if hay_variables:
        # Apéndice · grupos candidatos de la búsqueda de variables
        aqui("grupos")
        ultima = {}
        for r in VA["rondas"]:
            for g, v in r["pruebas"].items():
                ultima[g] = (r["ronda"], v)
        ronda_acepta = {r["mejor"]: r["ronda"] for r in VA["rondas"] if r["acepta"]}
        ei = VA["etiquetas_internas"]

        def resultado_g(g):
            if g == "etiquetas":
                return f'<b class="muted">Aparte</b><br>{pct(ei["ganancia"], d=1)} interno'
            if g in eleg:
                return f'<b class="blue">Aceptado</b><br>ronda {ronda_acepta[g]}'
            rr, v = ultima[g]
            quitado = any(a["grupo"] == g and a["quita"] for a in VA["atras"])
            return (f'<b class="muted">{"Quitado" if quitado else "No cumple"}</b><br>{pct(v["ganancia"], d=1)} · {v["suben"]} de {len(vent)}, ronda {rr}')
        tabla_g = ('<table class="tabla chica grupos"><thead><tr><th>Grupo</th><th>Qué mide</th><th class="num">Variables</th><th>Resultado</th></tr></thead><tbody>'
                   + "".join(f'<tr><th>{GRUPO[g]}</th><td>{VA["descripcion"][g].partition(": ")[2] or VA["descripcion"][g]}</td>'
                             f'<td class="num">{len(VA["variables_por_grupo"][g])}</td><td>{resultado_g(g)}</td></tr>' for g in cand_g + ["etiquetas"])
                   + "</tbody></table>")
        p.append(pagina(f"{PALABRA.get(len(cand_g), len(cand_g))} grupos candidatos, <em>todos con pagos anteriores</em>", tabla_g,
                        "Solo pagos en segundos estrictamente anteriores · Frecuencias y categorías ajustadas con el entrenamiento de cada bloque · "
                        "Historial de contracargos: etiquetas con 30 días o más de antigüedad · src/revisar/variables.py", APENDICE))

        # Apéndice · rondas de la selección hacia adelante
        aqui("rondas")
        cab = "".join(f'<th scope="col">Ronda {r["ronda"]}<small>desde {mil(r["partida_usd"])} mil</small></th>' for r in VA["rondas"])

        def celda_r(r, g):
            if g not in r["pruebas"]:
                return '<td style="--cell:#f6f8fa"><b class="muted">—</b></td>'
            v = r["pruebas"][g]
            elegido_aqui = r["acepta"] and r["mejor"] == g
            return (f'<td class="{"focus-azul" if elegido_aqui else ""}" style="--cell:{_tinte(v["ganancia"], .06)}">'
                    f'<b>{pct(v["ganancia"], d=1)}</b><small>{v["suben"]} de {len(vent)}</small></td>')
        tabla_r = ('<table class="matrix compacta rondas"><thead><tr><th scope="col">Grupo</th>' + cab + '</tr></thead><tbody>'
                   + "".join(f'<tr><th scope="row">{GRUPO[g]}</th>{"".join(celda_r(r, g) for r in VA["rondas"])}</tr>' for g in cand_g)
                   + '</tbody></table>')
        quitados = [GRUPO_CORTO[a["grupo"]] for a in VA["atras"] if a["quita"]]
        p.append(pagina(
            "Cada ronda prueba <em>todos los grupos restantes</em>", f'<div class="fill matrix-block">{tabla_r}</div>',
            f"Ganancia sobre el paso anterior, suma de las {len(vent)} ventanas internas · k de {len(vent)}: ventanas en que sube · Recuadro: aceptado · "
            f"Pasada hacia atrás: {'quita ' + _y(quitados) if quitados else 'no quita ningún grupo'}", APENDICE))

        # Apéndice · rejilla de hiperparámetros con parada temprana
        aqui("rejilla")
        fi = VA["final_interno"]

        def fila_rj(nombre, prof, peso, arboles, f, ref=False):
            g = f["total_usd"] / final_i - 1
            clase = ' class="cola"' if (hp["adopta"] and not ref and f["params"] == hp["params"]) else ""
            return (f'<tr{clase}><th>{nombre}</th><td class="num">{prof}</td><td class="num">{peso}</td><td class="num">{arboles}</td>'
                    f'<td class="num">{mil(f["total_usd"])}</td><td class="num">{"—" if ref else pct(g, d=1)}</td>'
                    f'<td class="num">{f["auc"]:.3f}</td><td class="num">{f["logloss"]:.4f}</td></tr>')
        px = VA["protocolo_xgb"]
        tabla_rj = ('<table class="tabla chica deciles rejilla"><thead><tr><th>Configuración</th><th class="num">Profundidad</th><th class="num">Peso mínimo por hoja</th>'
                    '<th class="num">Árboles por ventana</th><th class="num">Mil USD</th><th class="num">Contra el protocolo</th><th class="num">AUC</th>'
                    '<th class="num">Pérdida log.</th></tr></thead><tbody>'
                    + fila_rj("Protocolo, fijo", px["max_depth"], 1, f'{px["n_estimators"]} fijos', fi, True)
                    + "".join(fila_rj(f"Rejilla {i + 1}", f["params"]["max_depth"], f["params"]["min_child_weight"],
                                      " · ".join(ent(f["arboles"][n]) for n, _ in vent), f) for i, f in enumerate(rj))
                    + "</tbody></table>")
        n_ll = sum(f["logloss"] < fi["logloss"] and f["total_usd"] < fi["total_usd"] for f in rj)
        frase_ll = ("" if n_ll == 0 else
                    " Una combinación tiene menor pérdida logarítmica que el protocolo y aun así lleva menos dinero." if n_ll == 1 else
                    f" {'Todas' if n_ll == len(rj) else str(n_ll)} tienen menor pérdida logarítmica que el protocolo y aun así llevan menos dinero.")
        nota_rj = (f'<p class="takeaway">La mejor combinación queda {pct(hp["ganancia"], d=1)} contra el protocolo y mejora en {hp["suben"]} de '
                   f'{len(vent)} ventanas.{frase_ll}</p>')
        p.append(pagina(
            (f"Profundidad {hp['params']['max_depth']} y peso mínimo {hp['params']['min_child_weight']}: <em>{pct(hp['ganancia'], d=1)}</em>"
             if hp["adopta"] else "El ajuste de hiperparámetros <em>no supera la barra</em>"),
            tabla_rj + nota_rj,
            f"Variables F3 + {_y([GRUPO_CORTO[g] for g in eleg]) if eleg else 'ninguna'} · Tasa de aprendizaje {px['learning_rate']} · Parada temprana por pérdida "
            "logarítmica en los últimos 10 días de cada entrenamiento, paciencia de 150 árboles y tope de 4,000 · Reentrenamiento con 10% más árboles", APENDICE))

        # Apéndice · curva de aprendizaje (capítulo 7)
        aqui("aprendizaje")
        apz = VA["aprendizaje"]
        va_u = VA["internas"][apz["ventana"]]
        p.append(pagina(
            f"Parada temprana en <em>{ent(apz['mejor_iteracion'])} árboles</em>",
            _split(G.aprendizaje(apz["entrenamiento"], apz["validacion"], apz["paso"], apz["mejor_iteracion"], apz["arboles_protocolo"]),
                   f'<p class="big">{ent(apz["mejor_iteracion"])}</p><p class="sub">árboles con la menor pérdida en validación</p>'
                   '<p>Después de ese punto, la pérdida en entrenamiento sigue bajando y la de validación ya no mejora, señal de sobreajuste.</p>'
                   f'<div class="rule"><p><b>El protocolo fija {apz["arboles_protocolo"]} árboles</b></p>'
                   + ('<p>La parada temprana llega casi al mismo número usando solo datos de entrenamiento.</p></div>'
                      if abs(apz["mejor_iteracion"] / apz["arboles_protocolo"] - 1) < .1 else
                      '<p>La parada temprana elige el número de árboles con datos de entrenamiento, sin mirar la ventana que se evalúa.</p></div>')),
            f"Ventana interna {apz['ventana'][1:]} (días {va_u[0]}–{va_u[1]}) · Validación: últimos 10 días de su entrenamiento · "
            f"Tasa de aprendizaje {apz['learning_rate']} · Capítulo 7 del curso", APENDICE))

        # Apéndice · importancia de los grupos en la confirmación
        aqui("importancia_nuevas")
        ic6 = VA["importancia_confirmacion"]
        orden_i = sorted(ic6, key=lambda k: -ic6[k])
        nuevo_top = next((g for g in orden_i if g != "F3"), None)
        nuevos_i = [g for g in orden_i if g != "F3"]
        if nuevo_top and ic6[nuevo_top] < .1 * ic6["F3"]:
            tit_i = "Frente a F3, los grupos nuevos <em>aportan poco</em>"
        elif nuevo_top:
            tit_i = f"En la confirmación, el grupo nuevo más útil es <em>{GRUPO[nuevo_top].lower()}</em>"
        else:
            tit_i = "Importancia en la confirmación"
        p.append(pagina(
            tit_i,
            _split(G.importancia([("F3 completo" if g == "F3" else GRUPO[g], ic6[g]) for g in orden_i],
                                 f"Miles de USD que se pierden al permutar el grupo (días {conf[0]}–{conf[1]})", lambda n: n != "F3 completo"),
                   '<p class="sub">Permutación por grupo</p>'
                   '<p>Se permutan juntas las columnas de cada grupo en los días de confirmación y se mide el dinero que pierde la cola.</p>'
                   '<div class="rule"><p><b>F3 completo como referencia</b></p>'
                   + (f'<p>Al permutar las 93 variables del protocolo se pierden {mil(ic6["F3"])} mil USD; al permutar '
                      + "; ".join(f"{GRUPO_CORTO[g]}, {mil(ic6[g])} mil" for g in nuevos_i) + ".</p>"
                      + ('<p class="muted">Un valor negativo indica que la cola lleva más dinero sin ese grupo.</p>'
                         if any(ic6[g] < 0 for g in nuevos_i) else '')
                      if nuevos_i else '<p>No se aceptó ningún grupo nuevo.</p>')
                   + '</div>'),
            f"Modelo con variables nuevas e hiperparámetros del protocolo, entrenado con los días 1–{conf[0] - margen - 1} · Promedio de tres permutaciones",
            APENDICE))

    # Apéndice · Regularización
    aqui("regularizacion")
    rg = L["regularizacion"]
    c_el = float(LOGIT.partition("|")[0].removeprefix("LOGIT_C"))
    auc_max = max((f for f in rg if f["conjunto"] == "F3"), key=lambda f: f["auc"])
    usd_max = max((f for f in rg if f["conjunto"] == "F3"), key=lambda f: f["usd"])
    p.append(pagina(
        "La penalización con más dólares <em>no coincide con la de mayor AUC</em>",
        _split(G.regularizacion(rg, c_el),
               '<p class="sub">Logística con penalización L2</p>'
               f'<p>C chico encoge más los coeficientes. El dinero toca techo en C = {usd_max["C"]:g}; el AUC, en C = {auc_max["C"]:g}.</p>'
               '<div class="rule"><p><b>El criterio de selección son los dólares</b></p>'
               '<p>Con el historial del cliente, la logística mejora en todos los valores de C.</p></div>'),
        f"Días {S['bloques']['D1']['inicio']}–{S['bloques']['D2']['fin']} · 60 revisiones por día · AUC promedio de los dos bloques", APENDICE))

    # Apéndice · AUC contra dinero
    aqui("auc")
    ad = L["auc_dinero"]
    dest = {FINAL: ("Modelo", G.AZUL, 16, 8), "XGB|F4": ("con columnas opacas", G.GRIS_MEDIO, -16, 8),
            LOGIT: ("Logística", G.VERDE, -16, -14), REGLA: ("Mejor regla", G.NARANJA, -16, 8),
            "R_monto": ("Mayor monto", G.GRIS_MEDIO, 16, 8), "MLP|F3": ("Red MLP", G.GRIS_MEDIO, 16, 8),
            "ISO|F3": ("Bosque de aislamiento", G.GRIS_MEDIO, 16, 8)}
    au = {(a["politica"], a["puntaje"]): a for a in ad}
    p.append(pagina(
        "Un AUC mayor <em>no garantiza más dólares</em>",
        _split(G.auc_dinero(ad, dest, FINAL),
               f'<p class="sub">Mismo AUC, {au[(FINAL, "p")]["auc"]:.3f}</p>'
               f'<p class="big">{mil(au[(FINAL, "p_x_monto")]["usd"])} <span>contra {mil(au[(FINAL, "p")]["usd"])}</span></p>'
               '<p>mil USD con probabilidad × monto y con solo probabilidad. El AUC no considera el monto.</p>'
               f'<div class="rule"><p><b>Mayor monto: AUC {au[("R_monto", "p_x_monto")]["auc"]:.2f}</b></p>'
               f'<p>Ordena fraudes peor que el azar y aun así lleva {mil(au[("R_monto", "p_x_monto")]["usd"])} mil USD a la cola, más que la red neuronal '
               f'(AUC {au[("MLP|F3", "p_x_monto")]["auc"]:.2f}).</p></div>'),
        "Días 91–120, entrenamiento con días 1–60 · Cada punto, una política de desarrollo · La métrica de selección debe coincidir con la de la decisión",
        APENDICE))

    # Apéndice · El AUC es un duelo: distribución de la probabilidad por clase
    aqui("duelo")
    di = CC["distribucion"]
    p.append(pagina(
        f"AUC de {cv['solo_p']['auc']:.2f}: <em>{cv['solo_p']['auc'] * 100:.0f} de cada 100 pares bien ordenados</em>",
        _split(G.distribucion(di["bordes"], di["fraude"], di["legitimo"], di["mediana_fraude"], di["mediana_legitimo"]),
               f'<p class="sub">AUC de la probabilidad: {cv["solo_p"]["auc"]:.3f}</p>'
               '<p>Es la probabilidad de que un fraude tomado al azar tenga más puntaje que un legítimo tomado al azar.</p>'
               f'<div class="rule"><p><b>Mediana: {pct(di["mediana_fraude"], False, 1)} contra {pct(di["mediana_legitimo"], False, 2)}</b></p>'
               f'<p>El AUC no considera montos. Multiplicar por el monto baja el AUC a {cv["modelo"]["auc"]:.2f} y aumenta el dinero en la cola '
               f'{pct(op["modelo"]["usd"] / op["solo_p"]["usd"] - 1, False)}.</p></div>'),
        f"{dias_t} · Probabilidad del modelo final · 40 tramos en escala logarítmica; cada clase suma 100%", APENDICE))

    # Apéndice · Tabla de deciles del curso, con la cola de 60 y lo esperado contra lo observado
    aqui("tabla_deciles")
    cola_e = sum(L["calibracion"]["modelo"]["cola"][y]["esperado"] for y in P)
    om = op["modelo"]
    fila_cola = dict(tasa=om["precision"], lift=om["precision"] / CC["prevalencia"], lift_acum=om["precision"] / CC["prevalencia"],
                     fraudes_acum=om["recall"], usd=om["usd"], usd_acum=om["usd"] / CC["usd_fraude"], usd_esperado=cola_e)

    def fila_d(nombre, d, clase=""):
        return (f'<tr class="{clase}"><th>{nombre}</th><td class="num">{pct(d["tasa"], False, 1)}</td><td class="num">×{d["lift"]:.1f}</td>'
                f'<td class="num">×{d["lift_acum"]:.1f}</td><td class="num">{pct(d["fraudes_acum"], False)}</td><td class="num">{mil(d["usd"])}</td>'
                f'<td class="num">{pct(d["usd_acum"], False)}</td><td class="num">{mil(d["usd_esperado"])}</td></tr>')
    tabla_d = ('<table class="tabla chica deciles"><thead><tr><th>Decil del día</th><th class="num">Tasa de fraude</th><th class="num">Lift</th>'
               '<th class="num">Lift acumulado</th><th class="num">Fraudes acumulados</th><th class="num">Mil USD de fraude</th>'
               '<th class="num">Dinero acumulado</th><th class="num">Mil USD esperados</th></tr></thead><tbody>'
               + fila_d(f"Cola de 60 · {pct(cupo_t, False, 1)}", fila_cola, "cola")
               + "".join(fila_d(str(d["decil"]), d) for d in dcl) + "</tbody></table>")
    k1 = next(d["decil"] for d in dcl if d["lift"] < 1)
    p.append(pagina(
        f"A partir del decil {k1}, <em>la tasa de fraude queda bajo la media</em>", tabla_d,
        f"{dias_t} · Deciles con el orden de cada día · Lift = tasa del decil / tasa media de {pct(CC['prevalencia'], False, 1)} · "
        "Esperado = suma de probabilidad × monto", APENDICE))

    aqui("exactitud")
    p.append(ap_exactitud)
    aqui("curvas")
    p.append(ap_curvas)
    aqui("marginal")
    p.append(ap_marginal)

    # Apéndice · CRISP-DM
    aqui("crisp")
    fases = (("Negocio", "Decisión diaria, cupo fijo, dólares por celda y costo de revisar",
              "Matriz de confusión en dólares, t*&nbsp;=&nbsp;C&nbsp;/&nbsp;LTV", ("decision", "matriz", "montana", "costo")),
             ("Datos", "182 días, concentración del dinero, faltantes, etiqueta propagada", "Análisis exploratorio, calidad de datos",
              ("tiempo", "deciles", "calidad")),
             ("Preparación", "Historial previo por tarjeta y cliente; matriz de diseño ajustada por bloque",
              "Ingeniería de variables, RFM, ventanas de velocidad, novedad, entidades compartidas, cuantiles, one-hot con mínimo, frecuencia, indicadores de faltante",
              ("tuberia", "cliente", "ablacion", "catalogo", "candados", "grupos")),
             ("Modelado", "Seis reglas, logística regularizada y siete modelos con hiperparámetros fijos",
              "CART, bosque, XGBoost, MLP, ensamble, bosque de aislamiento, L2, selección hacia adelante, rejilla con parada temprana",
              ("torneo", "arbol", "regularizacion", "escalada", "rondas", "rejilla", "aprendizaje")),
             ("Evaluación", "Prueba congelada en dos meses, intervalos pareados, robustez, calibración y traza",
              "Paradoja de la exactitud, F1, ROC y precisión–recall, ganancia y lift, Brier, bootstrap, validación cruzada temporal",
              ("prueba", "intervalos", "metricas", "roc", "ganancia", "calibracion", "robustez", "traza", "observado",
               "veredicto", "diario", "importancia", "controles", "auc", "duelo", "tabla_deciles", "exactitud", "curvas",
               "validacion", "confirmacion", "importancia_nuevas")),
             ("Despliegue", "Cola nocturna, cupo según el costo, reentrenamiento, piloto, respaldo y protocolo para evaluar cambios",
              "Umbral por el cupo o por la curva de beneficio; mantenimiento con validación temporal",
              ("montana", "costo", "marginal", "despliegue", "validacion")))
    crisp = ('<table class="tabla chica crisp"><thead><tr><th>Fase</th><th>Qué se hizo</th><th>Técnicas del curso</th><th class="num">Lámina</th></tr></thead><tbody>'
             + "".join(f'<tr><th>{f}</th><td>{q}</td><td>{t}</td><td class="num">{_lam(donde, *ks)}</td></tr>' for f, q, t, ks in fases)
             + '</tbody></table>')
    p.append(pagina("Las seis fases de <em>CRISP-DM</em>", crisp, "Cada fase con sus láminas · Código en src/revisar y scripts/01 a 07", APENDICE))

    # Apéndice · Requisitos
    aqui("requisitos")
    filas_req = (
        ("Decisión: quién, cuándo, opciones y recurso", "Revisión manual de pagos ya autorizados, 60 por día", ("decision",)),
        ("Dinero de la decisión", "Dólares de fraude dentro de la cola; matriz en dólares", ("matriz",)),
        ("Umbral de mejora antes de la prueba", f"H1 ≥ {pct(U['H1'])}, H2 ≥ {pct(U['H2'])}, H3 > 0, con límite inferior > 0", ("intervalos", "veredicto")),
        ("Mismo presupuesto para todas las políticas", "60 revisiones por día; con costo, cada una elige su cupo en desarrollo", ("resultado", "prueba", "costo")),
        ("Práctica actual y reglas fuertes", "Seis reglas de tasa histórica × monto; la mejor representa la práctica", ("torneo", "prueba")),
        ("Base aprendida con la misma información", "Logística regularizada con las mismas variables y la misma matriz", ("ablacion", "intervalos", "regularizacion")),
        ("Comparador publicado", "El enfoque de la competencia IEEE-CIS: ordenar por probabilidad", ("metricas", "roc", "exactitud", "auc")),
        ("Elegir en desarrollo, probar en ≥ 2 periodos", "Días 61–120 para elegir; 121–151 y 152–182 congelados", ("tiempo", "torneo", "prueba")),
        ("Ganancia por periodo con IC pareado", f"Bootstrap de {ent(replicas)} réplicas que remuestrean días", ("prueba", "intervalos", "diario", "curvas")),
        ("Quitar los casos más grandes", "Sin pagos sobre el p99, monto topado, cupos de 30 y 120", ("robustez",)),
        ("Traza del dinero", "Ambos, solo modelo, solo regla y ninguno suman el fraude del mes", ("traza",)),
        ("Observado contra estimado", "Monto y etiqueta observados; dinero salvado supuesto; calibración",
         ("observado", "calibracion", "tabla_deciles")),
        ("Curvas y lecciones del curso", "Exactitud contra dinero, ROC, PR, lift, beneficio, calibración, L2, fuga, "
         "aprendizaje", ("metricas", "roc", "ganancia", "montana", "costo", "calibracion", "tabla_deciles", "candados",
                                  "regularizacion", "auc", "aprendizaje")),
        ("Optimización: ajuste de hiperparámetros", "Rejilla con parada temprana en tres ventanas; barra de +1% y 2 de 3",
         ("escalada", "rejilla", "aprendizaje")),
        ("Mantenimiento", "Reentrenamiento, vigilancia y búsqueda de variables con confirmación",
         ("despliegue", "validacion", "confirmacion")),
        ("CRISP-DM", "Seis fases con sus láminas", ("crisp",)))
    req = ('<table class="tabla chica requisitos"><thead><tr><th>Requisito del proyecto</th><th>Cómo se cumple</th><th class="num">Dónde</th></tr></thead><tbody>'
           + "".join(f'<tr><td>{a}</td><td>{b}</td><td class="num">{_lam(donde, *ks)}</td></tr>' for a, b, ks in filas_req if _lam(donde, *ks))
           + "</tbody></table>")
    p.append(pagina("Mapa de <em>requisitos</em>", req, "Protocolo, criterio y código: docs/ y src/revisar · Reproducir: scripts/01 a 07", APENDICE))

    escribir(p, CSS, GUION, "Qué pagos revisar", SALIDA)
    LAMINAS.write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")
    return SALIDA


CSS = r"""
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
.pasos { display: grid; grid-template-columns: repeat(5, 1fr); gap: 40px; align-content: center; }
.pasos p { margin: 0; border-top: 5px solid var(--blue); padding-top: 26px; }
.pasos p:last-child { border-top-color: var(--orange); }
.pasos b { display: block; font: 500 25px var(--mono); color: var(--blue); }
.pasos p:last-child b { color: var(--orange); }
.pasos strong { display: block; margin: 16px 0 16px; font: 600 50px/1 var(--display); letter-spacing: -.03em; }
.pasos span { display: block; font: 400 28px/1.34 var(--sans); color: var(--text); }
.closing-counts .green { color: var(--green); }
.appendix h2 { font-size: 58px; }
.matrix.costo { border-spacing: 7px 5px; }
.matrix.costo th, .matrix.costo td { padding: 9px 12px; }
.matrix.costo td b { font-size: 38px; }
.matrix.costo td small { font-size: 20px; margin-top: 2px; }
.matrix.costo tbody th { font-size: 27px; }
.matrix.costo th small { font-size: 20px; }
.tabla.requisitos { font-size: 22px; }
.tabla.requisitos th, .tabla.requisitos td { padding: 7px 22px 7px 0; }
.tabla.requisitos td:first-child { width: 33%; }
.tabla.requisitos thead th { font-size: 21px; }
.matrix.metricas td b { font-size: 34px; }
.matrix.metricas thead th { font-size: 23px; }
.tabla.deciles { font-size: 25px; }
.tabla.crisp { font-size: 22px; }
.tabla.crisp th, .tabla.crisp td { padding: 9px 22px 9px 0; }
.tabla.crisp tbody th { font-size: 24px; width: 15%; }
.tabla.deciles th, .tabla.deciles td { padding: 9px 18px 9px 0; }
.tabla.deciles tbody th { width: 17%; }
.tabla.deciles thead th { font-size: 21px; }
.tabla b.blue { color: var(--blue); }
.tabla.grupos { font-size: 21px; line-height: 1.22; }
.tabla.grupos th, .tabla.grupos td { padding: 6px 20px 6px 0; }
.tabla.grupos tbody th { font-size: 23px; }
.tabla.grupos tbody th { width: 19%; }
.tabla.grupos td:last-child { width: 21%; }
.matrix.rondas { border-spacing: 6px 3px; }
.matrix.rondas th, .matrix.rondas td { padding: 5px 10px; }
.matrix.rondas td b { font-size: 26px; }
.matrix.rondas td small { font-size: 17px; margin-top: 0; }
.matrix.rondas tbody th { font-size: 23px; }
.matrix.rondas thead th small { font-size: 18px; }
.tabla.deciles tr.cola > * { color: var(--blue); font-weight: 600; border-bottom-color: #a5aebc; }
"""
