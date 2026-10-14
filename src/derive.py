"""Derivados: spreads de precios, ratio precio/renta y asequibilidad precaria.

Al tener series temporales (más de un snapshot) se añadirán: índice mix-adjusted
por alcaldía, variación a/a del precio/m² y pronóstico simple.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

import config


def _cargar(nombre: str) -> pd.DataFrame:
    path = config.PROC / nombre
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def ratios_venta_renta(mediana: pd.DataFrame) -> pd.DataFrame:
    """Ratio precio de venta / renta anualizada por alcaldía (proxy de techo de
    retorno por renta; ver ratio >12-15% sugiere mercado de renta sana)."""
    venta = mediana[(mediana["operacion"] == "venta")].set_index("alcaldia")
    renta = mediana[mediana["operacion"] == "renta"].set_index("alcaldia")
    if venta.empty or renta.empty:
        return pd.DataFrame()
    filas: list[dict[str, Any]] = []
    for al in venta.index.intersection(renta.index):
        filas.append({
            "alcaldia": al,
            "precio_mediana": venta.loc[al, "precio_mediana"],
            "renta_mensual_mediana": renta.loc[al, "precio_mediana"],
            "meses_de_renta": venta.loc[al, "precio_mediana"] / renta.loc[al, "precio_mediana"],
        })
    out = pd.DataFrame(filas)
    out.to_csv(config.PROC / "ratios_venta_renta.csv", index=False)
    return out


def serie_financiamientos(fin: pd.DataFrame) -> pd.DataFrame:
    """Acciones y monto total de crédito por año en CDMX (agrega organismos)."""
    if fin.empty:
        return pd.DataFrame()
    g = fin.groupby("anio_calendario").agg(
        acciones=("acciones", "sum"),
        monto_mdp=("monto", lambda s: s.sum() / 1e6),
    ).reset_index()
    g.to_csv(config.PROC / "financiamientos_anual.csv", index=False)
    return g


def asequibilidad(
    mediana: pd.DataFrame,
    enigh: pd.DataFrame,
    hogares: pd.DataFrame,
) -> pd.DataFrame:
    """Años de ingreso del hogar mediano de CDMX para comprar la vivienda mediana
    de cada alcaldía + fracción de hogares que solventaría la mensualidad del 30%.

    Precios del inventario en portales (2026, nominal); ingresos ENIGH 2022
    inflados con INPC a pesos de 2026. Escenario de crédito: 90% financiado a
    20 años, tasa fija anual 10.5%.
    """
    if mediana.empty or enigh.empty:
        return pd.DataFrame()
    venta = mediana[(mediana["operacion"] == "venta")].copy()
    if venta.empty:
        return pd.DataFrame()
    tasa = 0.105 / 12
    n = 240
    filas: list[dict[str, Any]] = []
    ingreso_anual = float(enigh["ingreso_anual_mediano"].iloc[0])
    for _, x in venta.iterrows():
        precio = float(x["precio_mediana"])
        anios = precio / ingreso_anual
        cuota = 0.9 * precio * tasa * (1 + tasa) ** n / ((1 + tasa) ** n - 1)
        pct_ingreso = cuota / (ingreso_anual / 12) * 100
        alcanza = _share_ingreso(hogares, cuota)
        filas.append({
            "alcaldia": x["alcaldia"],
            "precio_mediana": precio,
            "anios_ingreso": round(anios, 1),
            "mensualidad_estimada": cuota,
            "pct_ingreso_mensual": round(pct_ingreso, 1),
            "share_hogares_alcanza_30pct": round(alcanza, 3),
        })
    out = pd.DataFrame(filas)
    out.to_csv(config.PROC / "asequibilidad.csv", index=False)
    return out


def _share_ingreso(hogares: pd.DataFrame, cuota: float) -> float:
    """Fracción (ponderada) de hogares cuyo ingreso cubre la cuota con la regla
    del 30%: ingreso mensual ≥ cuota / 0.30."""
    if hogares.empty:
        return float("nan")
    ingreso_minimo = cuota / 0.30
    topes = hogares["ing_mensual_2026"] - ingreso_minimo > 0
    numeros = hogares.loc[topes, "factor"].sum()
    total = hogares["factor"].sum()
    return float(numeros / total) if total else float("nan")