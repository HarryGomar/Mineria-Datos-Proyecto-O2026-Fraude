"""Rutas de datos: variables de entorno, luego config_local.json, luego datos/ del proyecto."""
from __future__ import annotations

import json
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
_cfg = {}
if (RAIZ / "config_local.json").exists():
    _cfg = json.loads((RAIZ / "config_local.json").read_text(encoding="utf-8"))

CRUDOS = Path(os.environ.get("REVISAR_CRUDOS") or _cfg.get("crudos") or RAIZ / "datos" / "crudos")
PROCESADOS = Path(os.environ.get("REVISAR_PROCESADOS") or _cfg.get("procesados") or RAIZ / "datos" / "procesados")
RESULTADOS = RAIZ / "resultados"
for _p in (PROCESADOS, RESULTADOS):
    _p.mkdir(parents=True, exist_ok=True)
