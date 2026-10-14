"""Datos oficiales de oferta y crédito: SNIIV (SEDATU).

- Déficit/rezago habitacional (municipal y estatal, 1990–2022) en CSVs abiertos.
- Financiamientos de vivienda por organismo (CuboAPI), serie CDMX por año.
- Inventario RUV: cubo existe pero requiere claves de dimensión
  (`diccionario_registro.xlsx`); se deja parametrizado.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import requests

import config

TIMEOUT = 90
UA = {"User-Agent": "Mozilla/5.0 (vivienda-cdmx research)"}

ALFRESCO_RE = re.compile(r'href="(https://sistemas\.sedatu\.gob\.mx/repositorio[^"]+content/([^"?]+))')


def _descargar(url: str, destino: Path) -> Path:
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(r.content)
    return destino


def indice_datos_abiertos() -> pd.DataFrame:
    """Catálogo de enlaces del portal de datos abiertos del SNIIV."""
    r = requests.get(config.SNIIV_DATOS_ABIERTOS, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    filas = [{"url": url, "archivo": archivo} for url, archivo in ALFRESCO_RE.findall(r.text)]
    df = pd.DataFrame(filas)
    df.to_csv(config.PROC / "sniiv_open_data_links.tsv", sep="\t", index=False)
    return df


def descarga_abiertos(df: pd.DataFrame | None = None) -> None:
    """Baja Déficit y Rezago municipal/estatal para CDMX (resuelve por nombre)."""
    df = df if df is not None else indice_datos_abiertos()
    objetivo = {
        "rezago_mun_2020": "rezago_habitacional_mun_2020",
        "rezago_est_2020": "rezago_habitacional_est_2020",
        "deficit": "Deficit_Vivienda",
    }
    for etiqueta, patron in objetivo.items():
        fila = df[df["archivo"].str.contains(patron, case=False, regex=False)]
        if fila.empty:
            print(f"  [sniiv] no encontrado: {patron}")
            continue
        url = fila.iloc[0]["url"].replace("&amp;", "&")
        _descargar(url, config.RAW / f"sniiv_{etiqueta}.csv")
        print(f"  [sniiv] descargado {patron}")


def financiamientos_cdmx(anios: tuple[int, int] = (2013, 2026)) -> pd.DataFrame:
    """Financiamientos de vivienda por organismo en CDMX, anual (CuboAPI)."""
    filas: list[dict] = []
    for anio in range(anios[0], anios[1] + 1):
        url = f"{config.SNIIV_CUBO}/GetFinanciamiento/{anio}/{config.CDMX_CLAVE}/000/0"
        r = requests.get(url, headers=UA, timeout=TIMEOUT)
        if r.status_code != 200:
            continue
        for fila in r.json():
            fila["anio_calendario"] = anio
            filas.append(fila)
    df = pd.DataFrame(filas)
    if not df.empty:
        df = df.rename(columns={"año": "periodo"})
        df.to_csv(config.RAW / "sniiv_financiamientos_cdmx.csv", index=False)
    return df