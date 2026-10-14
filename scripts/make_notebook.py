"""Genera notebooks/analisis_vivienda.ipynb a partir del pipeline.

Uso:
    python scripts/make_notebook.py
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf

RAIZ = Path(__file__).resolve().parents[1]


def cell(tipo: str, src: str):
    src = src.lstrip("\n")
    if tipo == "markdown":
        return nbf.v4.new_markdown_cell(src)
    return nbf.v4.new_code_cell(src)


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    }
    nb.cells = [
        cell("markdown", """
# Mercado de la vivienda en la CDMX

Análisis reproducible de demanda, oferta, precios y perfil sociodemográfico por
alcaldía (y camino a colonia/CP) de la Ciudad de México.

**Fuentes:** PADIM (portales: inmuebles24, vivanuncios, propiedades_com, mls,
doorvel) · SNIIV/SEDATU (déficit, rezago y financiamientos) · SEDUVI (suelo) ·
CONAPO 2020 (marginación por colonia y AGEB) · SEPOMEX (CP↔colonia) ·
INEGI (Censo 2020, ENIGH 2022, INPC) · CONEVAL (pobreza municipal) ·
SHF (índice de precios, manual).

Pipeline: `main.py --refresh` (descarga) → `src/build.py` (paneles) →
`src/derive.py` (derivados) → `src/analyze.py` (diagnóstico). Este notebook
replica el diagnóstico y deja las tablas listas para análisis propios.
"""),
        cell("code", """
import os
import sys
from pathlib import Path

# El kernel puede arrancar en notebooks/ o en la raíz del proyecto
if Path.cwd().name == "notebooks":
    os.chdir(Path.cwd().parent)
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "src"))

import analyze
import build
import conapo
import coneval
import derive
import enigh
import geo
import inegi
import report
import sepomex
import padim
import sniiv
import pandas as pd
"""),
        cell("code", """
paneles = build.paneles_padim()
mediana = build.panel_alcaldias(paneles["portales_actual"])
mediana.query("operacion == 'venta'").sort_values("precio_m2_mediana", ascending=False)
"""),
        cell("markdown", """
## Financiamientos de vivienda (SNIIV)

Acciones y monto de crédito hipotecario por los principales organismos en CDMX.
"""),
        cell("code", """
fin = build.panel_financiamientos()
derive.serie_financiamientos(fin)
"""),
        cell("markdown", """
## Perfil sociodemográfico (CONAPO 2020)

Marginación por colonia (con CP) y por AGEB; se resume por alcaldía.
"""),
        cell("code", """
colonia = conapo.marginacion_colonia()
conapo.marginacion_ageb()
marg = pd.read_csv("data/processed/marginacion_alcaldia.csv")
marg["share_alta_total"] = marg["share_Alto"] + marg["share_Muy_alto"]
marg.sort_values("share_alta_total", ascending=False)
"""),
        cell("markdown", """
## Bridge colonia↔CP (SEPOMEX)

Catálogo de códigos postales de CDMX: cada CP con sus asentamientos y alcaldía.
- `data/processed/cp_cdmx.csv` — CP → asentamiento → alcaldía.
- `data/processed/conapo_marginacion_colonia.csv` — colonia → CP → indicadores.
"""),
        cell("code", """
import pandas as pd
cp = pd.read_csv("data/processed/cp_cdmx.csv")
cp.head(5)
"""),
        cell("markdown", """
## Censo de Población y Vivienda 2020 (INEGI)

Principales resultados por AGEB y manzana urbana de la CDMX: 66,456 manzanas
y 2,211 AGEB con población y vivienda. Paneles:
- `censo2020_manzanas_cdmx.csv` — una fila por manzana (clave `cve_manzana`).
- `censo2020_ageb_cdmx.csv` — agregados por AGEB (cruza con CONAPO vía
  `censo/ageb_marginacion`).
- `censo2020_alcaldia.csv` — agregación por alcaldía con indicadores.
"""),
cell("code", """
censo_al = pd.read_csv("data/processed/censo2020_alcaldia.csv")
censo_al[["alcaldia", "POBTOT", "indice_dependencia", "hacinamiento_prom",
          "vph_sin_agua_pct", "vph_piso_tierra_pct"]].round(2).sort_values(
    "indice_dependencia", ascending=False)
"""),
cell("code", """
censo_ageb = pd.read_csv("data/processed/censo2020_ageb_marginacion.csv")
censo_ageb.shape
"""),
cell("markdown", """
## Pobreza 2020 por alcaldía (CONEVAL)
"""),
cell("code", """
coneval.pobreza_alcaldia()
pd.read_csv("data/processed/coneval_pobreza_alcaldia.csv").sort_values(
    "pobreza_porcentaje", ascending=False).head()
"""),
cell("markdown", """
## Ingresos de los hogares (ENIGH 2022) y asequibilidad

La ENIGH es muestral a nivel entidad: el ingreso se estima para toda la CDMX.
Se infla con el INPC (2022 → 2026-08). La asequibilidad cruza ese ingreso contra
la mediana del inventario en venta de cada alcaldía (años de ingreso para
comprar + % de hogares que solventan el 30% de la mensualidad).
"""),
cell("code", """
enigh.ingresos_cdmx()
ing = pd.read_csv("data/processed/enigh_cdmx_ingresos.csv")
ing
"""),
cell("code", """
hogares = pd.read_csv("data/processed/enigh_cdmx_hogares.csv")
mediana = build.panel_alcaldias(build.paneles_padim()["portales_actual"])
aseq = derive.asequibilidad(mediana, ing, hogares)
aseq.sort_values("anios_ingreso")
"""),
cell("markdown", """
## Notas de nivel geográfico

- `alcaldias_mediana.csv`: precio mediano y m² por alcaldía (venta/renta).
- PADIM entrega geografía G5 (zona de densidad), no predio exacto: el salto a
  colonia/CP exige unir esas zonas con las colonias del INEGI/DENUE.
- Los CP de CDMX no son polígonos: el *bridge* colonia↔CP se arma con SEPOMEX
  + CONAPO (ver `NOTES.md`).
"""),
    ]
    out = RAIZ / "notebooks" / "analisis_vivienda.ipynb"
    nbf.write(nb, out)
    print(f"Notebook generado: {out}")


if __name__ == "__main__":
    main()