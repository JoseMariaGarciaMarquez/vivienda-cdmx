"""CONAPO: índice de marginación 2020 a nivel colonia y AGEB (datos.gob.mx).

Incluye las carencias crudas (sin educación básica, piso de tierra, hacinamiento,
sin internet...) que alimentan el perfil sociodemográfico profundo; a nivel
colonia viene con CP y alcaldía, y a nivel AGEB con la clave que enlaza al censo.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

import config
from geo import norm_alcaldia

GRADOS = ["Muy bajo", "Bajo", "Medio", "Alto", "Muy alto"]


def _bajar(nombre: str) -> Path:
    import requests

    destino = config.RAW / f"conapo_{nombre}.csv"
    if destino.exists():
        return destino
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        "Referer": "https://www.datos.gob.mx/es/dataset/indices_marginacion",
    }
    r = requests.get(config.CONAPO_URLS[nombre], headers=headers, timeout=180)
    r.raise_for_status()
    destino.write_bytes(r.content)
    return destino


def _leer(nombre: str) -> pd.DataFrame:
    import numpy as np

    df = pd.read_csv(config.RAW / f"conapo_{nombre}.csv", encoding="utf-8", low_memory=False)
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].replace({np.nan: None})
    return df


def marginacion_colonia() -> pd.DataFrame:
    """Corte CDMX a nivel colonia (con CP y alcaldía) + panel por alcaldía."""
    _bajar("marginacion_colonia")
    df = _leer("marginacion_colonia")
    cdmx = df[df["NOM_ENT"] == "Ciudad de México"].copy()
    cdmx["alcaldia"] = cdmx["NOM_MUN"].map(norm_alcaldia)
    cdmx = cdmx.dropna(subset=["alcaldia"])
    cdmx.to_csv(config.PROC / "conapo_marginacion_colonia.csv", index=False)

    g = _resumen_alcaldias(cdmx, pob="POB_TOT", grado="GM_2020")
    g.to_csv(config.PROC / "marginacion_alcaldia.csv", index=False)
    return cdmx


def marginacion_ageb() -> pd.DataFrame:
    _bajar("marginacion_ageb")
    df = _leer("marginacion_ageb")
    cdmx = df[df["NOM_ENT"] == "Ciudad de México"].copy()
    cdmx["alcaldia"] = cdmx["NOM_MUN"].map(norm_alcaldia)
    cdmx = cdmx.dropna(subset=["alcaldia"])
    cdmx.to_csv(config.PROC / "conapo_marginacion_ageb.csv", index=False)
    return cdmx


def _resumen_alcaldias(
    cdmx: pd.DataFrame, pob: str = "POB_TOT", grado: str = "GM_2020"
) -> pd.DataFrame:
    """Share de población por grado de marginación y IMN promedio por alcaldía."""
    filas: list[dict] = []
    for al, x in cdmx.groupby("alcaldia"):
        pop = x[pob].sum(skipna=True)
        if pop <= 0:
            continue
        fila: dict = {"alcaldia": al, "poblacion_2020": pop}
        for g in GRADOS:
            fila[f"share_{g.replace(' ', '_')}"] = x.loc[x[grado] == g, pob].sum() / pop
        fila["imn_promedio"] = (x[pob] * x["IMN_2020"]).sum() / pop
        filas.append(fila)
    return pd.DataFrame(filas)