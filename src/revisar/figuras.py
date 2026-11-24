"""Figuras de la presentación para el reporte y el cuaderno.

Las gráficas se dibujan una sola vez, en scripts/05_presentacion.py. Este módulo las toma del HTML de la
presentación (presentacion/laminas.json dice en qué lámina está cada una) y las vuelve SVG autónomos: con
xmlns y con sus estilos dentro del archivo, para que se vean igual en GitHub, en el cuaderno y en el reporte.
"""
from __future__ import annotations

import json
import re

from revisar.presentacion import LAMINAS, SALIDA

ESTILO = """
text { font-family: Inter, system-ui, 'Segoe UI', sans-serif; fill: #0b0d12; }
.heading { font: 600 31px 'Space Grotesk', Inter, system-ui, sans-serif; }
.label { font: 500 25px Inter, system-ui, 'Segoe UI', sans-serif; }
.label-strong { font: 600 28px Inter, system-ui, 'Segoe UI', sans-serif; }
.axis { font: 400 22px 'JetBrains Mono', ui-monospace, Consolas, monospace; fill: #586172; }
.micro { font: 400 22px Inter, system-ui, 'Segoe UI', sans-serif; fill: #586172; }
.data { font: 600 34px 'Space Grotesk', Inter, system-ui, sans-serif; }
.chart-big { font: 600 50px 'Space Grotesk', Inter, system-ui, sans-serif; letter-spacing: -.04em; }
.grid { stroke: #e0e5ec; stroke-width: 2; }
.axis-line { stroke: #a5aebc; stroke-width: 2; }
"""


def laminas() -> dict[str, str]:
    """SVG de cada lámina registrada que tenga una gráfica: {clave: svg}."""
    if not SALIDA.exists() or not LAMINAS.exists():
        raise FileNotFoundError("Primero corre scripts/05_presentacion.py")
    secciones = re.findall(r'<section class="slide[^"]*" data-title="[^"]*">(.*?)</section>', SALIDA.read_text(encoding="utf-8"), re.S)
    out = {}
    for clave, i in json.loads(LAMINAS.read_text(encoding="utf-8")).items():
        m = re.search(r"<svg\b.*?</svg>", secciones[i - 1], re.S)
        if m:
            out[clave] = m.group(0)
    return out


def autonomo(svg: str, margen: int = 12) -> str:
    """Agrega xmlns, tamaño, un margen alrededor del viewBox y los estilos de texto de la presentación.

    En la presentación el SVG puede dibujar texto un poco fuera de su caja; fuera de ella no, así que se
    agrega un margen para que no se corten los acentos ni las etiquetas de los bordes.
    """
    svg = re.sub(r"<title>.*?</title>", "", svg, count=1, flags=re.S)
    w, h = (float(v) for v in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups())
    caja = f'viewBox="{-margen} {-margen} {w + 2 * margen:g} {h + 2 * margen:g}" width="{w + 2 * margen:g}" height="{h + 2 * margen:g}"'
    svg = re.sub(r'viewBox="0 0 [\d.]+ [\d.]+"', caja, svg, count=1)
    return svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1).replace(">", f"><style>{ESTILO}</style>", 1)
