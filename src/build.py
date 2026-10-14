"""Montaje de paneles: portales (PADIM), financiamientos (SNIIV) y rezago.

Todos los paneles se guardan en data/processed con fecha de corte para que las
series temporales sean trazables (el snapshot de cada corrida es un punto).
"""
from __future__ import annotations

import glob
from pathlib import Path
from typing import Any

import pandas as pd

import config
from geo import alcaldia_desde_fila


def _alcaldia(row: pd.Series) -> str | None:
    return alcaldia_desde_fila(row, "state", "municipality")


def paneles_padim() -> dict[str, pd.DataFrame]:
    """Une todos los snapshots de portales (raw/padim_cdmx_*.csv.gz) y devuelve
    (i) la observación más reciente consolidada y (ii) el panel histórico."""
    archivos = sorted(glob.glob(str(config.RAW / "padim_cdmx_*.csv.gz")))
    if not archivos:
        return {"portales_actual": pd.DataFrame(), "portales_series": pd.DataFrame()}
    partes = [pd.read_csv(a, compression="gzip") for a in archivos]
    series = pd.concat(partes, ignore_index=True)
    series.to_csv(config.PROC / "portales_series.csv", index=False)
    actual = series[series["recorded_at"] == series["recorded_at"].max()].copy()
    return {"portales_actual": actual, "portales_series": series}


def panel_alcaldias(df: pd.DataFrame) -> pd.DataFrame:
    """Mediana de precio y precio/m² por alcaldía (venta y renta).

    La oferta de portales mezcla casas, departamentos y terrenos; se fija la
    banda residencial (m² y precio/m²) antes de mediar y se exige muestra mínima.
    """
    if df.empty or "municipality" not in df.columns:
        return pd.DataFrame()
    df = df.copy()
    df["alcaldia"] = df.apply(_alcaldia, axis=1)
    df = df.dropna(subset=["alcaldia"])
    if "m2" in df.columns and "precio_mxn" in df.columns:
        df = df[df["m2"].between(20, 600) & (df["precio_mxn"] > 0)]
        df["precio_m2"] = df["precio_mxn"] / df["m2"]
        df = df[df["precio_m2"].between(1000, 600000)]
    vals: list[dict[str, Any]] = []
    for operacion in ("venta", "renta"):
        sub = df[df["price_semantics"] == operacion]
        if sub.empty:
            continue
        g = sub.groupby("alcaldia")
        for al, x in g:
            if len(x) < 10:
                continue
            prices = x["precio_mxn"].quantile([0.1, 0.5, 0.9])
            vals.append({
                "alcaldia": al,
                "operacion": operacion,
                "n": len(x),
                "precio_mediana": prices.get(0.5, float("nan")),
                "precio_p10": prices.get(0.1, float("nan")),
                "precio_p90": prices.get(0.9, float("nan")),
                "precio_m2_mediana": x["precio_m2"].median() if "precio_m2" in x else float("nan"),
                "m2_mediana": x["m2"].median() if "m2" in x else float("nan"),
            })
    out = pd.DataFrame(vals)
    out.to_csv(config.PROC / "alcaldias_mediana.csv", index=False)
    return out


def panel_financiamientos() -> pd.DataFrame:
    archivo = config.RAW / "sniiv_financiamientos_cdmx.csv"
    if not archivo.exists():
        return pd.DataFrame()
    df = pd.read_csv(archivo)
    df.to_csv(config.PROC / "financiamientos_cdmx.csv", index=False)
    return df


def _leer_tabla(path: Path) -> pd.DataFrame:
    """Lee un fichero del portal SNIIV: a veces vienen XLSX disfrazados de .csv."""
    magic = path.read_bytes()[:2]
    if magic == b"PK":
        return pd.read_excel(path)
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1")


def panel_rezago() -> pd.DataFrame:
    """Rezago habitacional municipal: filtra CDMX y pivota a serie por año."""
    candidatos = sorted(glob.glob(str(config.RAW / "sniiv_rezago_mun_*.csv")))
    if not candidatos:
        return pd.DataFrame()
    partes: list[pd.DataFrame] = [_leer_tabla(Path(a)) for a in candidatos]
    out = pd.concat(partes, ignore_index=True)
    out.to_csv(config.PROC / "rezago_cdmx.csv", index=False)
    return out