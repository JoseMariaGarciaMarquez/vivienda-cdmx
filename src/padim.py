"""Cliente de la API de PADIM (Protocolo Abierto de Datos Inmobiliarios de MX).

Cobertura CDMX (agos 2026): ~59k observaciones (30k en venta), fuentes:
inmuebles24, vivanuncios, propiedades_com, mls, doorvel, easybroker, plalla.
Nivel geográfico honesto: G5 (zona de densidad, no predio).
"""
from __future__ import annotations

import csv
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

import config

TIMEOUT = 60


def _get(path: str, **params: object) -> dict:
    r = requests.get(f"{config.PADIM_BASE}{path}", params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def coverage() -> dict:
    return _get("/v1/coverage")


def stats() -> dict:
    return _get("/v1/stats")


def properties(limit: int = 500, offset: int = 0, **filtros: object) -> dict:
    """Propiedades con filtros opcionales (state, municipality, capa, geo_level,
    precio_min/max, con_geo, source_id). Máximo limit=500, paginar por offset."""
    return _get("/v1/properties", limit=limit, offset=offset, **filtros)


def fetch_cdmx(con_geo: bool | None = True) -> pd.DataFrame:
    """Pagina TODA la oferta de CDMX y devuelve un DataFrame plano."""
    filas: list[dict] = []
    offset = 0
    total = float("inf")
    while offset < total:
        pagina = properties(limit=500, offset=offset, state="CDMX", con_geo=con_geo)
        items = pagina.get("items", [])
        total = pagina["pagination"]["total"]
        filas.extend(items)
        offset += len(items)
        if not items:
            break
        time.sleep(0.5)
    df = pd.DataFrame(filas)
    if df.empty:
        return df
    for col in ("precio_mxn", "m2", "lat", "lng", "record_confidence"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "observed_at" in df.columns:
        df["observed_at"] = pd.to_datetime(df["observed_at"], errors="coerce")
    return df


def snapshot_fecha() -> str:
    return datetime.now().strftime("%Y%m%d")


def guardar_snapshot(df: pd.DataFrame, fecha: str | None = None) -> Path:
    """Snapshot con fecha para series temporales de portales (verder datos propios)."""
    fecha = fecha or snapshot_fecha()
    out = config.RAW / f"padim_cdmx_{fecha}.csv.gz"
    df.to_csv(out, index=False, compression="gzip", quoting=csv.QUOTE_MINIMAL)
    return out