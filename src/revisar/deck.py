"""Utilidades para armar la presentación autónoma (HTML con fuentes, figuras y notas embebidas)."""
from __future__ import annotations

import json
import os
import re
from base64 import b64encode
from html import escape
from pathlib import Path
from shutil import which
from subprocess import run
from tempfile import TemporaryDirectory

from .rutas import RAIZ

MARCO = RAIZ / "presentacion" / "marco"


def fuentes_embebidas() -> str:
    estilos = []
    for nombre, archivo, pesos in (("Inter", "inter", "400 700"), ("Space Grotesk", "spacegrotesk", "500 700"),
                                   ("JetBrains Mono", "jetbrainsmono", "400 500")):
        datos = b64encode((MARCO / "fuentes" / f"{archivo}.woff2").read_bytes()).decode("ascii")
        estilos.append(f"@font-face {{ font-family: '{nombre}'; font-style: normal; font-weight: {pesos}; "
                       f"src: url(data:font/woff2;base64,{datos}) format('woff2'); font-display: swap; }}")
    return "\n".join(estilos)


def pagina(titulo: str, contenido: str, pie: str = "", clase: str = "", fase: str = "", sub: str = "") -> str:
    """Una lámina: fase de CRISP-DM (etiqueta pequeña), título, subtítulo opcional, contenido y pie."""
    return (f'<section class="slide {clase}" data-title="{escape(re.sub("<[^>]+>", "", titulo))}">'
            + (f'<p class="kicker">{fase}</p>' if fase else "")
            + f"<h2>{titulo}</h2>" + (f'<p class="subtitulo">{sub}</p>' if sub else "") + f"{contenido}{f'<footer>{pie}</footer>' if pie else ''}</section>")


def notas(guion: Path, n: int) -> str:
    texto = guion.read_text(encoding="utf-8")
    filas = re.findall(r"^## \d+ · ([^\n]+)\n\n\*\*Ver\.\*\* [^\n]+\n\n\*\*Decir\.\*\* ([^\n]+)", texto, re.M)
    if len(filas) != n:
        raise ValueError(f"El guion tiene {len(filas)} notas y la presentación {n} diapositivas.")
    return json.dumps([{"heading": t, "text": d} for t, d in filas], ensure_ascii=False).replace("<", "\\u003c")


def escribir(paginas: list[str], css_extra: str, guion: Path, titulo: str, salida: Path) -> None:
    controles = (MARCO / "controles.html").read_text(encoding="utf-8")
    controles = controles.replace("@@notas@@", notas(guion, len(paginas))).replace(
        "@@navegacion@@", (MARCO / "navegacion.js").read_text(encoding="utf-8"))
    licencias = "\n".join(r.read_text(encoding="utf-8") for r in sorted((MARCO / "fuentes").glob("*-OFL.txt")))
    estilos = (MARCO / "estilos.css").read_text(encoding="utf-8") + css_extra
    salida.write_text(
        f'<!doctype html>\n<!--\n{licencias}\n-->\n<html lang="es-MX"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(titulo)}</title>'
        f"<style>{fuentes_embebidas()}{estilos}</style></head><body>"
        '<main class="viewport" aria-label="Presentación"><div class="stage">' + "\n".join(paginas) + "</div>" + controles,
        encoding="utf-8")


def navegador() -> Path:
    """Chrome, Edge o Chromium: REVISAR_NAVEGADOR, luego el PATH, luego las carpetas usuales de Windows y macOS."""
    if os.environ.get("REVISAR_NAVEGADOR"):
        return Path(os.environ["REVISAR_NAVEGADOR"])
    for nombre in ("chrome", "msedge", "chromium", "google-chrome", "google-chrome-stable", "chromium-browser", "microsoft-edge"):
        if which(nombre):
            return Path(which(nombre))
    for var in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        raiz = os.environ.get(var)
        for ruta in ("Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe"):
            if raiz and (Path(raiz) / ruta).is_file():
                return Path(raiz) / ruta
    for raiz in (Path("/Applications"), Path.home() / "Applications"):
        for app in ("Google Chrome", "Microsoft Edge", "Chromium"):
            if (raiz / f"{app}.app" / "Contents" / "MacOS" / app).is_file():
                return raiz / f"{app}.app" / "Contents" / "MacOS" / app
    raise FileNotFoundError("No se encontró Chrome, Edge ni Chromium para exportar el PDF (REVISAR_NAVEGADOR indica otra ruta).")


def imprimir_pdf(html: Path, pdf: Path) -> None:
    with TemporaryDirectory(prefix="focal-pdf-") as temp:
        borrador = Path(temp) / "deck.pdf"
        run([str(navegador()), "--headless", "--disable-gpu", "--no-first-run", "--no-pdf-header-footer",
             f"--user-data-dir={Path(temp) / 'perfil'}", f"--print-to-pdf={borrador}", html.resolve().as_uri() + "?print"],
            check=True, timeout=90, capture_output=True)
        contenido = borrador.read_bytes()
        if not contenido.startswith(b"%PDF-"):
            raise ValueError("El navegador no generó un PDF válido.")
        pdf.write_bytes(contenido)
