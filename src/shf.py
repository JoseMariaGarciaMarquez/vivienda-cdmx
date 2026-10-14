"""Índice SHF de precios de la vivienda en CDMX.

El CSV abierto (T1 2017 en adelante, por alcaldía/municipio, nueva/usada y
tipología) se publica en gob.mx / transparencia.shf.gob.mx detrás de Akamai
y no se puede descargar por línea de comandos desde este entorno. Flujo:

1. Descargar a mano "Índice SHF Datos Abiertos <trimestre>" desde
   https://www.gob.mx/shf/documentos/indice-shf-de-precios-de-la-vivienda-en-mexico-2025-a-2026
2. Guardarlo como `data/raw/shf_indice.csv`.
3. `cargar_indice()` lo normaliza y produce `data/processed/shf_cdmx.csv`.

El esquema cambia entre archivos; el loader es tolerante: busca columnas por
patrón (año, trimestre, entidad/alcaldía, índice) y deja el mapa detallado si
no reconoce algo.
"""
from __future__ import annotations

import unicodedata

import pandas as pd

import config
from geo import norm_alcaldia

PATRONES = {
    "anio": ["AÑO", "ANO", "YEAR", "PERIODO"],
    "trim": ["TRIMESTRE", "TRIM", "QUARTER"],
    "ent": ["ENTIDAD", "ESTADO", "DELEGACION", "MUNICIPIO", "ALCALDIA"],
    "indice": ["INDICE", "INDEX", "VARIACION"],
}


def _limpia(nombre: str) -> str:
    n = unicodedata.normalize("NFKD", str(nombre))
    n = "".join(c for c in n if not unicodedata.combining(c))
    return n.upper().strip()


def _columna(df: pd.DataFrame, grupo: str) -> str | None:
    for p in PATRONES[grupo]:
        lim = _limpia(p)
        for c in df.columns:
            if lim in _limpia(c):
                return c
    return None


def cargar_indice() -> pd.DataFrame | None:
    if not config.SHF_CSV_RAW.exists():
        print("[shf] CSV no presente: descarga manual -> data/raw/shf_indice.csv")
        print("[shf] https://www.gob.mx/shf/documentos/indice-shf-de-precios-de-la-vivienda-en-mexico-2025-a-2026")
        return None
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(config.SHF_CSV_RAW, encoding=encoding, low_memory=False)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError("SHF CSV sin codificación reconocible")
    df = df.loc[:, ~df.columns.duplicated()]
    anio = _columna(df, "anio")
    ent = _columna(df, "ent")
    indice = _columna(df, "indice")
    if not (anio and ent and indice):
        print("[shf] esquema no reconocido. Columnas:", list(df.columns))
        return None

    salida = pd.DataFrame()
    salida["anio"] = pd.to_numeric(df[anio], errors="coerce")
    salida["alcaldia"] = df[ent].map(norm_alcaldia)
    salida["indice"] = pd.to_numeric(df[indice], errors="coerce")
    if _columna(df, "trim"):
        salida["trimestre"] = pd.to_numeric(df[_columna(df, "trim")], errors="coerce")
    salida = salida.dropna(subset=["alcaldia", "anio", "indice"])
    salida.to_csv(config.PROC / "shf_cdmx.csv", index=False)
    print(f"[shf] índice normalizado: {len(salida):,} filas -> data/processed/shf_cdmx.csv")
    return salida