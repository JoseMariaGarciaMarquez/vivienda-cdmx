"""Causas del precio alto: vacancia, uso temporal, Airbnb y oferta de portales.

Cruza por alcaldía:
- Censo 2020 (INEGI): viviendas desocupadas y de uso temporal (proxy de
  segundas residencias / especulación).
- Inside Airbnb (data.insideairbnb.com, corte mensual): listados por alcaldía.
- PADIM: densidad de oferta en venta por portales (con sesgo de cobertura
  documentado: periferia casi sin listados).
- PADIM medianas: precio por m² (salida de build.panel_alcaldias).

Salida: data/processed/causas_alcaldia.csv (16 alcaldías).
"""
from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd

import config

AIRBNB_URL = (
    "https://data.insideairbnb.com/mexico/df/mexico-city/"
    "2026-09-23/visualisations/listings.csv"
)
AIRBNB_RAW = "airbnb_cdmx_listings.csv"


def _norm(x: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", str(x).lower())
        if unicodedata.category(c) != "Mn"
    )


def descarga_airbnb(url: str = AIRBNB_URL) -> Path | None:
    """Descarga el CSV de Inside Airbnb CDMX si no existe (o con force)."""
    import requests

    dest = config.RAW / AIRBNB_RAW
    if dest.exists() and dest.stat().st_size > 100_000:
        return dest
    try:
        r = requests.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=120
        )
        r.raise_for_status()
        dest.write_bytes(r.content)
        print(f"  airbnb: {len(r.content):,} bytes -> {dest.name}")
        return dest
    except Exception as exc:  # sin red o URL vencida: seguir sin Airbnb
        print(f"  [airbnb] sin descarga ({exc}); el panel sigue sin Airbnb")
        return None


def panel_causas() -> pd.DataFrame:
    """Construye data/processed/causas_alcaldia.csv (vacancia + Airbnb + oferta)."""
    censo = pd.read_csv(config.PROC / "censo2020_alcaldia.csv")
    censo["stock"] = censo["VIVPAR_HAB"] + censo["VIVPAR_DES"]
    censo["vac_pct"] = censo["VIVPAR_DES"] / censo["stock"] * 100
    censo["uso_temporal_pct"] = censo["VIVPAR_UT"] / censo["stock"] * 100
    censo["k"] = censo["alcaldia"].map(_norm)

    med = pd.read_csv(config.PROC / "alcaldias_mediana.csv")
    med = med[med["operacion"] == "venta"].copy()
    med["k"] = med["alcaldia"].map(_norm)
    precios = (
        med.groupby("k", as_index=False)
        .agg(precio_mediana=("precio_mediana", "first"),
             precio_m2_mediana=("precio_m2_mediana", "first"))
    )

    import glob as _glob

    snaps = sorted(_glob.glob(str(config.RAW / "padim_cdmx_*.csv.gz")))
    if snaps:
        pad = pd.read_csv(snaps[-1])
        pad["k"] = pad["municipality"].map(_norm)
        oferta = (
            pad[pad["price_semantics"] == "venta"].groupby("k").size()
            .rename("listados_portales").reset_index()
        )
    else:
        oferta = pd.DataFrame(columns=["k", "listados_portales"])

    df = censo.merge(precios, on="k", how="left").merge(oferta, on="k", how="left")
    df["oferta_x1000"] = df["listados_portales"] / df["stock"] * 1000

    air = descarga_airbnb()
    if air is not None:
        ab = pd.read_csv(air)
        ab["k"] = ab["neighbourhood_group"].fillna(ab["neighbourhood"]).map(_norm)
        conteo = ab.groupby("k").size().rename("airbnb_listings")
        df = df.merge(conteo, on="k", how="left")
        df["airbnb_x1000"] = df["airbnb_listings"] / df["stock"] * 1000
        df.attrs["airbnb_total"] = int(len(ab))
    else:
        df["airbnb_listings"] = float("nan")
        df["airbnb_x1000"] = float("nan")
        df.attrs["airbnb_total"] = 0

    out = config.PROC / "causas_alcaldia.csv"
    df.to_csv(out, index=False)
    return df
