"""Huellas del código congelado. La prueba solo corre si coinciden con las del protocolo."""
from __future__ import annotations

import hashlib
import re

from .rutas import RAIZ

PROTOCOLO = RAIZ / "docs" / "protocolo.md"
CONGELADOS = ["src/revisar/datos.py", "src/revisar/politicas.py", "src/revisar/evaluacion.py",
              "scripts/03_prueba.py", "resultados/desarrollo_seleccion.json"]


def huella(ruta: str) -> str:
    # Sin finales de línea de Windows: la huella no cambia si git convierte LF y CRLF.
    return hashlib.sha256((RAIZ / ruta).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def verificar() -> None:
    if not PROTOCOLO.exists():
        raise SystemExit("No hay protocolo congelado (docs/protocolo.md).")
    registradas = dict(re.findall(r"\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|", PROTOCOLO.read_text(encoding="utf-8")))
    faltan = [r for r in CONGELADOS if r not in registradas]
    if faltan:
        raise SystemExit(f"El protocolo no registra la huella de: {faltan}")
    distintas = [r for r in CONGELADOS if huella(r) != registradas[r]]
    if distintas:
        raise SystemExit(f"El código cambió después de congelar el protocolo: {distintas}")


if __name__ == "__main__":
    for r in CONGELADOS:
        print(f"| `{r}` | `{huella(r)}` |")
