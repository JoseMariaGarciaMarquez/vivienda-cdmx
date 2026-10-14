"""Normalización de nombres de alcaldía y puentes geográficos."""
from __future__ import annotations

import unicodedata

import pandas as pd

ALIAS_ALCALDIA = {
    "alvaro obregon": "Álvaro Obregón",
    "azcapotzalco": "Azcapotzalco",
    "benito juarez": "Benito Juárez",
    "coyoacan": "Coyoacán",
    "cuajimalpa": "Cuajimalpa de Morelos",
    "cuajimalpa de morelos": "Cuajimalpa de Morelos",
    "cuauhtemoc": "Cuauhtémoc",
    "gustavo a madero": "Gustavo A. Madero",
    "gustavo madero": "Gustavo A. Madero",
    "iztacalco": "Iztacalco",
    "iztapalapa": "Iztapalapa",
    "la magdalena contreras": "La Magdalena Contreras",
    "magdalena contreras": "La Magdalena Contreras",
    "miguel hidalgo": "Miguel Hidalgo",
    "milpa alta": "Milpa Alta",
    "tlahuac": "Tláhuac",
    "tlalpan": "Tlalpan",
    "venustiano carranza": "Venustiano Carranza",
    "xochimilco": "Xochimilco",
}


def norm_alcaldia(nombre: object) -> str | None:
    """Normaliza cualquier variante (sin acentos, alias) a la alcaldía canónica."""
    if nombre is None or pd.isna(nombre):
        return None
    n = unicodedata.normalize("NFKD", str(nombre))
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower().replace(".", "").strip()
    return ALIAS_ALCALDIA.get(n, None)


def alcaldia_desde_fila(row: pd.Series, col_estado: str, col_municipio: str) -> str | None:
    """Alcaldía canónica para una fila con estado/municipio (solo CDMX)."""
    if str(row.get(col_estado, "")) == "CDMX":
        return norm_alcaldia(row.get(col_municipio))
    return None