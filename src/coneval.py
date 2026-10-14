"""CONEVAL: medición de la pobreza 2020 a nivel municipal (datos.gob.mx).

Incidencia de pobreza (y extrema), carencias sociales y situación de ingresos
por demarcación territorial de la CDMX. Complementa la marginación de CONAPO:
la pobreza usa el ingreso (LPIs de CONEVAL) + carencias captadas en el censo.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

import config
from geo import norm_alcaldia

ANIO = "2020-01-01"

COLS = [
    "municipio", "poblacion",
    "pobreza_porcentaje", "pobreza_extrema_porcentaje", "pobreza_moderada_porcentaje",
    "vulnerable_carencias_sociales_porcentaje", "vulnerable_ingresos_porcentaje",
    "no_pobre_no_vulnerable_porcentaje",
    "carencia_rezago_educativo_porcentaje", "carencia_servicios_de_salud_porcentaje",
    "carencia_seguridad_social_porcentaje", "carencia_calidad_espacios_vivienda_porcentaje",
    "carencia_servicios_basicos_vivienda_porcentaje",
    "carencia_alimentacion_nutritiva_calidad_porcentaje",
    "al_menos_una_carencia_porcentaje", "al_menos_tres_carencias_porcentaje",
    "ingreso_inferior_a_lpi_porcentaje", "ingreso_inferior_a_lpei_porcentaje",
]


def _archivo() -> Path:
    return config.RAW / "coneval_pobreza_municipal.csv"


def descargar() -> Path:
    import requests

    destino = _archivo()
    if destino.exists():
        return destino
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
        "Accept": "text/csv,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    }
    r = requests.get(config.CONEVAL_POBREZA_URL, headers=headers, timeout=120)
    r.raise_for_status()
    destino.write_bytes(r.content)
    return destino


def pobreza_alcaldia() -> pd.DataFrame:
    """Incidencia de pobreza y carencias 2020 por alcaldía (16 filas)."""
    descargar()
    df = pd.read_csv(_archivo(), low_memory=False)
    df = df[(df["periodo"] == ANIO) & (df["clave_entidad"] == 9)].copy()
    df["alcaldia"] = df["municipio"].map(norm_alcaldia)
    df = df.dropna(subset=["alcaldia"])
    out = df[["alcaldia"] + COLS].reset_index(drop=True)
    out.to_csv(config.PROC / "coneval_pobreza_alcaldia.csv", index=False)
    return out