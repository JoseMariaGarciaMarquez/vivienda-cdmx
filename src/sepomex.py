"""SEPOMEX: catálogo nacional de códigos postales (bridge colonia→CP).

Descarga oficial vía ASP.NET del portal de Correos de México (botón
download, per-ENT) — se selecciona Ciudad de México (entidad 09). El fichero
es .xls real (BIFF); se lee con xlrd. Resultado: tabla CP→asentamiento→
alcaldía, base del nivel geográfico CDMX.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import requests

import config
from geo import norm_alcaldia

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120"}
URL = "https://www.correosdemexico.gob.mx/SSLServicios/ConsultaCP/CodigoPostal_Exportar.aspx"
_HIDDEN = ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION", "__LASTFOCUS")


def _ocultos(html: str) -> dict[str, str]:
    vals: dict[str, str] = {}
    for f in _HIDDEN:
        m = re.search(rf'name="{f}"[^>]*value="([^"]*)"', html)
        vals[f] = m.group(1) if m else ""
    return vals


def descargar_cp(xls: Path = config.RAW / "sepomex_cdmx.xls") -> Path:
    s = requests.Session()
    s.headers.update(UA)
    r = s.get(URL, timeout=60)
    r.raise_for_status()
    data = {
        **_ocultos(r.text),
        "__EVENTTARGET": "btnDescarga",
        "__EVENTARGUMENT": "",
        "cboEdo": "09",
    }
    r2 = s.post(URL, data=data, timeout=120)
    r2.raise_for_status()
    if not r2.content[:2] == b"\xd0\xcf":
        raise RuntimeError("SEPOMEX no devolvió un .xls; revisar el flujo ASP.NET")
    xls.write_bytes(r2.content)
    return xls


def catalogo_cp(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia el catálogo CDMX y lo deja listo para unir (CP→asentamiento→alcaldía)."""
    col_map = {
        "d_codigo": "cp",
        "d_asenta": "asentamiento",
        "d_tipo_asenta": "tipo_asentamiento",
        "D_mnpio": "alcaldia",
        "d_zona": "zona",
    }
    out = df.rename(columns=col_map)
    out["alcaldia"] = out["alcaldia"].map(norm_alcaldia)
    out = out.dropna(subset=["alcaldia"])
    out["cp"] = out["cp"].astype(int)
    out = out[["cp", "asentamiento", "tipo_asentamiento", "alcaldia", "zona"]].copy()
    out.to_csv(config.PROC / "cp_cdmx.csv", index=False)
    return out


def preparar(df: pd.DataFrame | None = None) -> pd.DataFrame:
    if df is None:
        xls = config.RAW / "sepomex_cdmx.xls"
        if not xls.exists():
            descargar_cp(xls)
        df = pd.read_excel(xls, sheet_name="Distrito_Federal")
    return catalogo_cp(df)