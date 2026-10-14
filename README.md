# Vivienda CDMX · Monitor

Panel reproducible del mercado de la vivienda en la Ciudad de México: demanda,
oferta, precios y perfil sociodemográfico por alcaldía, con camino a colonia y CP.

## Ejecutar

```bash
python main.py            # usa caché de data/raw si existe
python main.py --refresh  # nuevo snapshot de portales (PADIM) + SNIIV
python scripts/make_notebook.py
```

Salidas:

- `outputs/vivienda_cdmx.html` — dashboard (gráficas + resumen en texto).
- `outputs/vivienda_cdmx_interactivo.html` — explorador Plotly (autocontenido).
- `outputs/resumen_vivienda.txt` — diagnóstico por alcaldía.
- `outputs/charts/*.png` — cada gráfica por separado.
- `docs/` — sitio publicado en GitHub Pages (se reconstruye solo, ver abajo).
- `notebooks/analisis_vivienda.ipynb` — análisis interactivo.

## Página web (GitHub Pages)

El sitio vive en `docs/` y GitHub Pages lo sirve desde la rama `main`:

- `docs/index.html` — portada con acceso a las dos vistas.
- `docs/vivienda_cdmx_interactivo.html` — explorador (mapa + dispersión).
- `docs/vivienda_cdmx.html` — reporte estático.

`src/publicar.py` copia los dashboards de `outputs/` a `docs/` y escribe la
portada; `main.py` lo invoca al final, así que basta con correr el pipeline y
hacer commit de `docs/` para actualizar la página.

## Estructura

```
vivienda-cdmx/
├── main.py                   # orquestador: descarga -> paneles -> dashboard
├── scripts/make_notebook.py  # genera el notebook analítico
├── src/config.py             # rutas, catálogos, alcaldías, URLs de fuentes
├── src/padim.py              # cliente API PADIM (portales, snapshot CDMX)
├── src/sniiv.py              # SNIIV/SEDATU: déficit, rezago, financiamientos
├── src/seduvi.py             # suelo/catastro desde datos.cdmx.gob.mx (CKAN)
├── src/shf.py                # índice SHF de precios (CSV abierto)
├── src/build.py              # montaje de paneles (alcaldías, series)
├── src/derive.py             # ratios, series derivadas
├── src/analyze.py            # resumen en texto
├── src/report.py             # gráficas matplotlib + dashboard HTML
├── src/interactivo.py        # dashboard interactivo (Plotly, autocontenido)
├── src/publicar.py           # portada + copia a docs/ (GitHub Pages)
├── data/raw/                 # caché de descargas + snapshots fechados
├── data/processed/           # paneles
├── outputs/                  # resultados de build (no versionado)
└── docs/                     # sitio publicado (GitHub Pages)
```

## Fuentes

- **PADIM** (api.padim.org): oferta de portales (venta y renta) con coste
  `precio_mxn`, `m2` y geografía honesta G5 (zona). CDMX ~59k observaciones.
- **SNIIV / SEDATU** (sniiv.sedatu.gob.mx): déficit y rezago habitacional
  municipal 1990–2022; financiamientos de vivienda por organismo (CuboAPI).
- **SEDUVI / datos.cdmx.gob.mx**: valores unitarios de suelo y catastro (CKAN).
- **SHF**: índice de precios de la vivienda, por alcaldía (2017–hoy); CSV abierto
  bloqueado por Akamai, descarga manual a `data/raw/shf_indice.csv`.

## Nivel geográfico

- Alcaldía: soportado desde el primer día (PADIM + SNIIV).
- Colonia/CP: los snapshots de PADIM acumulan el campo `colony` y el *bridge*
  colonia↔CP sale del directorio SEPOMEX (los CP de CDMX no son polígonos).
- Ver `NOTES.md` para las decisiones de diseño y el roadmap.