"""ENIGH 2022 (INEGI) + INPC: ingreso de los hogares de la CDMX en pesos 2026.

La ENIGH es encuesta muestral nacional: el ingreso solo se puede estimar a
nivel de entidad federativa (la CDMX entera), nunca por alcaldía. `ing_cor` es
el ingreso corriente trimestral y `factor` el factor de expansión.
El INPC ajusta el ingreso nominal 2022 a pesos de hoy (2026-08).
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

import config

UBICA_CDMX_PREFIX = "09"

VARIABLES = ["ing_cor", "factor", "ubica_geo", "tot_integ", "mayores", "menores", "ocupados"]


def _zip() -> Path:
    return config.RAW / "enigh2022_ns_concentradohogar_csv.zip"


def _csv() -> Path:
    return config.RAW / "enigh_concentradohogar.csv"


def descargar() -> Path:
    import requests

    z = _zip()
    if z.exists():
        return z
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
        "Accept": "application/zip,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    }
    r = requests.get(config.ENIGH_2022_URL, headers=headers, timeout=600, stream=True)
    r.raise_for_status()
    z.write_bytes(r.content)
    with zipfile.ZipFile(z) as arc:
        for mi in arc.namelist():
            if mi.lower().endswith("concentradohogar.csv"):
                with arc.open(mi) as src, open(_csv(), "wb") as dst:
                    dst.write(src.read())
                break
    return z


def _leer() -> pd.DataFrame:
    if not _csv().exists():
        descargar()
    return pd.read_csv(_csv(), encoding="latin-1", low_memory=False)


def _inpc_cdmx_factor() -> float:
    """Factor 2026 / 2022: INPC general promedio 2022 -> último mes disponible."""
    if not Path(config.RAW / "inpc_mensual.csv").exists():
        import requests

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
            "Accept": "application/zip,*/*;q=0.8",
        }
        r = requests.get(config.INPC_URL, headers=headers, timeout=120, stream=True)
        r.raise_for_status()
        z = config.RAW / "inpc_mensual_csv.zip"
        z.write_bytes(r.content)
        with zipfile.ZipFile(z) as arc:
            arc.extractall(config.RAW / "inpc")
        return factor_desde(
            pd.read_csv(config.RAW / "inpc" / "conjunto_de_datos" / "conjunto_de_datos_inpc_mensual.csv",
                        encoding="latin-1")
        )
    return factor_desde(pd.read_csv(Path(config.RAW / "inpc_mensual.csv"), encoding="latin-1"))


def factor_desde(inpc: pd.DataFrame) -> float:
    idx = inpc[inpc["CONCEPTO"].str.contains("INPC", na=False) &
               inpc["COBERTURA"].astype(str).str.lower().eq("nacional")]
    idx = idx[["FECHA", "VALOR"]].dropna().copy()
    idx["VALOR"] = pd.to_numeric(idx["VALOR"], errors="coerce")
    idx["FECHA"] = pd.to_datetime(idx["FECHA"])
    # cuando el archivo trae varias filas por mes (resumen/subíndices), toma general
    general = idx.groupby(idx["FECHA"].dt.to_period("M"))["VALOR"].apply(
        lambda s: s.dropna().sort_values().iloc[0] if len(s) else pd.NA
    )
    prom_2022 = general.loc[general.index.astype(str).str.startswith("2022-")].mean()
    ultimo = general.iloc[-1]
    return float(ultimo / prom_2022)


def ingresos_cdmx() -> pd.DataFrame:
    """Resumen de ingreso de los hogares de la CDMX (pesos 2026) al nivel hogar."""
    df = _leer()
    cdmx = df[df["ubica_geo"].astype(str).str.zfill(5).str.startswith(UBICA_CDMX_PREFIX)].copy()
    cdmx["ing_anual_2022"] = cdmx["ing_cor"] * 4
    cdmx["ing_anual_2026"] = cdmx["ing_anual_2022"] * _inpc_cdmx_factor()
    cdmx["ing_mensual_2026"] = cdmx["ing_anual_2026"] / 12
    resumen = pd.DataFrame([{
        "entidad": "Ciudad de México",
        "hogares_ponderados": int(cdmx["factor"].sum()),
        "ingreso_anual_mediano": _w_quantile(cdmx, "ing_anual_2026", 0.5),
        "ingreso_mensual_mediano": _w_quantile(cdmx, "ing_mensual_2026", 0.5),
        "p25_mensual": _w_quantile(cdmx, "ing_mensual_2026", 0.25),
        "p10_mensual": _w_quantile(cdmx, "ing_mensual_2026", 0.10),
        "p75_mensual": _w_quantile(cdmx, "ing_mensual_2026", 0.75),
        "inpc_factor_2022_2026": round(_inpc_cdmx_factor(), 4),
    }])
    cdmx[["ubica_geo", "ing_mensual_2026", "factor", "tot_integ", "ocupados"]].to_csv(
        config.PROC / "enigh_cdmx_hogares.csv", index=False
    )
    resumen.to_csv(config.PROC / "enigh_cdmx_ingresos.csv", index=False)
    return resumen


def _w_quantile(df: pd.DataFrame, col: str, q: float) -> float:
    s = df.sort_values(col)
    w = s["factor"].cumsum()
    umbral = w.iloc[-1] * q
    idx = w.searchsorted(umbral)
    return float(s[col].iloc[min(idx, len(s) - 1)])