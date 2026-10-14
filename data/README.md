# data/

Esta carpeta **no se versiona** (ver `.gitignore` raíz). Todo su contenido es
descargado o derivado de fuentes públicas y se regenera con el pipeline.

```bash
python main.py --refresh   # descarga crudos y reconstruye procesados
python main.py             # reconstruye procesados desde el caché en raw/
```

Estructura:

- `raw/` — descargas crudas (PADIM, SNIIV/SEDATU, CONAPO, SEPOMEX, INEGI
  Censo/ENIGH/INPC, CONEVAL, SEDUVI, Airbnb). Incluye un snapshot fechado de
  portales (`padim_cdmx_YYYYMMDD.csv.gz`) por cada corrida con `--refresh`.
- `processed/` — paneles derivados (precios por alcaldía, índices, censo,
  asequibilidad, impuestos, rezago, causas).

Fuentes, URLs y notas de verificación: `docs/` y `NOTES.md` en la raíz.
