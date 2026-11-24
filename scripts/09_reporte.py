"""Arma reporte/reporte.html (y reporte/reporte.pdf con --pdf) desde reporte/reporte.md.

Las figuras son las de la presentación (scripts/05_presentacion.py debe correr antes). Se escriben como SVG
autónomos en reporte/figuras/, para que el Markdown se vea en GitHub, y se insertan dentro del HTML con las
fuentes de la presentación.
Uso: python scripts/09_reporte.py [--pdf]
"""
from __future__ import annotations

import re
import sys
from html import escape
from pathlib import Path

import markdown

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from revisar.deck import fuentes_embebidas, imprimir_pdf  # noqa: E402
from revisar.figuras import autonomo, laminas  # noqa: E402

CARPETA = RAIZ / "reporte"
FIGURAS = CARPETA / "figuras"
# Una figura es una imagen sola en su línea seguida de su pie en cursiva.
FIGURA = re.compile(r"^!\[[^\]]*\]\(figuras/([a-z_]+)\.svg\)\n\*([^*\n]+)\*$", re.M)

CSS = """
:root { color-scheme: light; }
body { max-width: 980px; margin: 40px auto; padding: 0 24px; font: 16px/1.6 Georgia, 'Times New Roman', serif; color: #1b1f27; background: #fff; }
h1, h2, h3 { font-family: Inter, 'Segoe UI', system-ui, sans-serif; line-height: 1.2; color: #0b0d12; }
h1 { font-size: 36px; margin-bottom: 6px; letter-spacing: -0.01em; }
h2 { margin-top: 48px; border-top: 2px solid #e0e5ec; padding-top: 18px; }
h3 { margin-top: 30px; }
table { border-collapse: collapse; margin: 16px 0; font: 14px/1.4 Inter, 'Segoe UI', system-ui, sans-serif; width: 100%; }
th, td { border-bottom: 1px solid #e0e5ec; padding: 6px 8px; text-align: left; vertical-align: top; }
thead th { background: #f5f7fa; }
td { font-variant-numeric: tabular-nums; }
figure { margin: 26px 0 32px; }
figure svg { display: block; width: 100%; max-width: 820px; height: auto; margin: 0 auto; }
figcaption { max-width: 820px; margin: 10px auto 0; font: 14px/1.45 Inter, 'Segoe UI', system-ui, sans-serif; color: #586172; }
code, pre { font-size: 14px; background: #f3f5f8; }
code { padding: 1px 4px; } pre { padding: 12px; overflow-x: auto; }
@media (max-width: 700px) { table { display: block; overflow-x: auto; } }
@page { size: Letter; margin: 16mm 15mm; }
@media print { body { margin: 0 auto; max-width: none; padding: 0; font-size: 11.5pt; }
  figure, table, pre { break-inside: avoid; } h2, h3 { break-after: avoid; } }
"""


def main() -> None:
    md = (CARPETA / "reporte.md").read_text(encoding="utf-8")
    fig = laminas()
    FIGURAS.mkdir(exist_ok=True)
    bloques: list[str] = []
    usadas: set[str] = set()

    def figura(m: re.Match) -> str:
        clave, pie = m.group(1), m.group(2)
        svg = autonomo(fig[clave])
        (FIGURAS / f"{clave}.svg").write_text(svg, encoding="utf-8", newline="\n")
        usadas.add(clave)
        bloques.append(f"<figure>{svg}<figcaption>{escape(pie)}</figcaption></figure>")
        return f"FIGURA{len(bloques) - 1}FIN"

    cuerpo = markdown.markdown(FIGURA.sub(figura, md), extensions=["tables", "fenced_code"])
    for i, bloque in enumerate(bloques):
        cuerpo = cuerpo.replace(f"<p>FIGURA{i}FIN</p>", bloque)
    assert "FIGURA" not in re.sub(r"<figcaption>.*?</figcaption>", "", cuerpo), "una figura quedó sin insertar"
    for viejo in FIGURAS.glob("*.svg"):
        if viejo.stem not in usadas:
            viejo.unlink()

    salida = CARPETA / "reporte.html"
    salida.write_text(
        '<!doctype html><html lang="es-MX"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1"><title>Qué pagos revisar</title>'
        f"<style>{fuentes_embebidas()}\n{CSS}</style></head><body>{cuerpo}</body></html>", encoding="utf-8")
    print(f"reporte: {salida.relative_to(RAIZ)} · {len(bloques)} figuras")
    if "--pdf" in sys.argv:
        imprimir_pdf(salida, salida.with_suffix(".pdf"))
        print("PDF:", salida.with_suffix(".pdf").relative_to(RAIZ))


if __name__ == "__main__":
    main()
