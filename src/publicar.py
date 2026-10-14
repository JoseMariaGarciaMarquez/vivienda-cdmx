"""Publica la página del proyecto (GitHub Pages) en `docs/`.

Copia los dashboards generados por `main.py` a `docs/` y escribe una portada
(`docs/index.html`) con la paleta del proyecto. GitHub Pages sirve `/docs` de la
rama `main`; los propios dashboards se enlazan entre sí por nombre relativo, así
que basta con que ambos vivan en la misma carpeta.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import config
import paleta

# nombre original -> nombre publicado (deben coincidir con los enlaces cruzados
# que ya traen los dashboards entre sí)
ARCHIVOS = [
    "vivienda_cdmx_interactivo.html",
    "vivienda_cdmx.html",
]


def _portada() -> str:
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vivienda CDMX · Monitor</title>
<style>
  :root {{
    --tinta: {paleta.TINTA}; --tinta2: {paleta.VERDE_OSCURO};
    --verde: {paleta.VERDE}; --verde-claro: {paleta.VERDE_CLARO};
    --cian: {paleta.CIAN}; --niebla: {paleta.NIEBLA};
    --gris: {paleta.GRIS}; --linea: {paleta.LINEA}; --fondo: {paleta.FONDO};
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--fondo); color: var(--tinta);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    line-height: 1.5; -webkit-font-smoothing: antialiased; }}
  .strip {{ height: 5px; background: linear-gradient(90deg,
    var(--cian), var(--niebla), var(--verde-claro),
    var(--verde), var(--tinta2), var(--tinta)); }}
  .wrap {{ max-width: 880px; margin: 0 auto; padding: 56px 22px 72px; }}
  .kick {{ font-size: 12px; text-transform: uppercase; letter-spacing: .18em;
    color: var(--tinta2); font-weight: 700; }}
  h1 {{ font-family: Georgia, "Times New Roman", serif; font-weight: 400;
    font-size: clamp(30px, 6vw, 48px); line-height: 1.08; margin: 10px 0 0;
    letter-spacing: -.01em; }}
  .lead {{ font-size: clamp(15px, 2.4vw, 18px); color: var(--gris);
    max-width: 60ch; margin: 16px 0 0; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
    margin-top: 34px; }}
  a.card {{ display: block; text-decoration: none; color: inherit;
    background: #fff; border: 1px solid var(--linea); border-radius: 16px;
    padding: 22px 22px 20px; transition: transform .12s ease, box-shadow .12s ease;
    border-top: 4px solid var(--sc, var(--linea)); }}
  a.card:hover {{ transform: translateY(-3px);
    box-shadow: 0 10px 26px rgba(33,40,51,.10); }}
  .card .t {{ font-size: 19px; font-weight: 650; display: flex;
    align-items: center; gap: 8px; }}
  .card .d {{ font-size: 13.5px; color: var(--gris); margin-top: 8px; }}
  .card .go {{ font-size: 12.5px; font-weight: 700; color: var(--tinta2);
    margin-top: 14px; display: inline-block; }}
  footer {{ margin-top: 44px; padding-top: 18px; border-top: 1px solid var(--linea);
    font-size: 12.5px; color: var(--gris); }}
  footer a {{ color: var(--tinta2); }}
  @media (max-width: 640px) {{ .grid {{ grid-template-columns: 1fr; }}
    .wrap {{ padding: 40px 18px 56px; }} }}
</style></head>
<body>
<div class="strip"></div>
<div class="wrap">
  <div class="kick">Monitor del mercado de la vivienda</div>
  <h1>La vivienda en la Ciudad de México</h1>
  <p class="lead">Precios, oferta, asequibilidad, impuestos y perfil
  sociodemográfico por alcaldía — construido a partir de fuentes abiertas
  (PADIM, SNIIV-SEDATU, INEGI Censo 2020, CONAPO, CONEVAL, ENIGH/INPC, SEDUVI,
  Inside Airbnb).</p>

  <div class="grid">
    <a class="card" href="vivienda_cdmx_interactivo.html" style="--sc:{paleta.CIAN}">
      <div class="t">Explorador interactivo</div>
      <div class="d">Mapa con selector de 8 métricas (precio/m², impuestos,
      Airbnb, índices, rezago…), dispersión con eje X variable y cifras clave.</div>
      <span class="go">Abrir el explorador →</span>
    </a>
    <a class="card" href="vivienda_cdmx.html" style="--sc:{paleta.VERDE}">
      <div class="t">Reporte estático</div>
      <div class="d">El panorama completo en 16 gráficas y el resumen por
      alcaldía: precios, déficit, asequibilidad e impuestos 2026.</div>
      <span class="go">Abrir el reporte →</span>
    </a>
  </div>

  <footer>
    Datos de referencia (no valuación ni transacción). Cada corrida de
    <code>python main.py --refresh</code> genera un nuevo corte.
    Fuentes y metodología en el repositorio.
  </footer>
</div>
</body></html>"""


def hacer_pagina() -> Path:
    """Copia los dashboards a `docs/` y escribe la portada. Idempotente."""
    dest = config.RAIZ / "docs"
    dest.mkdir(exist_ok=True)
    faltan = []
    for nombre in ARCHIVOS:
        origen = config.OUT / nombre
        if origen.exists():
            shutil.copy2(origen, dest / nombre)
        else:
            faltan.append(nombre)
    (dest / "index.html").write_text(_portada(), encoding="utf-8")
    if faltan:
        print(f"  aviso: faltan dashboards por publicar: {', '.join(faltan)}")
    return dest / "index.html"
