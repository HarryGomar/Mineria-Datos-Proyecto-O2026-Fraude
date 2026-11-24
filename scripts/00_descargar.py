"""Descarga la copia pública de IEEE-CIS Fraud Detection (OpenML 46858) y verifica su huella SHA-256.

La dirección y la huella están en datos/fuente.json. El archivo queda donde lo espera src/revisar/datos.py:
<crudos>/openml-46858/openml-46858.parquet, con <crudos> definido en src/revisar/rutas.py.
Uso: python scripts/00_descargar.py
"""
from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
from revisar.datos import ARCHIVO, FUENTE  # noqa: E402


def huella(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while bloque := f.read(1 << 20):
            h.update(bloque)
    return h.hexdigest()


def main() -> None:
    if ARCHIVO.exists() and huella(ARCHIVO) == FUENTE["sha256"]:
        print("El archivo ya está y su huella coincide.")
        return
    ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
    parcial = ARCHIVO.with_suffix(".parcial")
    pedido = urllib.request.Request(FUENTE["url"], headers={"User-Agent": "revisar-pagos/0.1"})
    print(f"Descargando {FUENTE['copia']} ({FUENTE['bytes'] / 1e6:.0f} MB)...")
    with urllib.request.urlopen(pedido, timeout=300) as r, open(parcial, "wb") as f:
        while bloque := r.read(1 << 20):
            f.write(bloque)
    if huella(parcial) != FUENTE["sha256"]:
        parcial.unlink()
        raise SystemExit("La huella SHA-256 no coincide con datos/fuente.json; el archivo se descartó.")
    parcial.replace(ARCHIVO)
    print("Listo: huella verificada.")


if __name__ == "__main__":
    main()
