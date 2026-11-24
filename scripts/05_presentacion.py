"""Presentación autónoma (presentacion/que-pagos-revisar.html) y, con --pdf, su PDF.

Las cifras se leen de resultados/ (scripts 01 a 04, 04b_lecciones, 04c_curvas_curso, 06_variables y 07_anexo_prueba); el guion vive en presentacion/guion.md.
Uso: python scripts/05_presentacion.py [--pdf]
"""
from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from revisar.deck import imprimir_pdf  # noqa: E402
from revisar.presentacion import crear  # noqa: E402
from revisar.rutas import RAIZ  # noqa: E402

if __name__ == "__main__":
    d = crear()
    print("presentación:", d.relative_to(RAIZ))
    if "--pdf" in sys.argv:
        imprimir_pdf(d, d.with_suffix(".pdf"))
        print("PDF listo")
