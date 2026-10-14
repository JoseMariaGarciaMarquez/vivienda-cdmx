"""Déficit y rezago habitacional, y presión de la oferta (SNIIV-SEDATU).

Fuentes:
- `data/processed/rezago_cdmx.csv` — rezago habitacional municipal 2020
  (viviendas con/sin rezago), derivado de `rezago_habitacional_mun_2020`.
- `data/raw/sniiv_deficit.csv` — déficit habitacional estatal (años recientes),
  campos: `nec_viv` (necesidades anuales), `rezago` (acumulado) y
  `deficit_h` (déficit habitacional total = rezago + necesidades).
- `data/processed/financiamientos_anual.csv` — acciones de crédito por año
  (producción observada, proxy de oferta nueva).

NOTA sobre las claves municipales: el archivo municipal de SNIIV **no** usa el
orden INEGI alfabético; sigue el catálogo de demarcaciones (IECM), verificado
contra el conteo de viviendas del Censo 2020:
2=Azcapotzalco, 3=Coyoacán, 4=Cuajimalpa, 5=Gustavo A. Madero, 6=Iztacalco,
7=Iztapalapa, 8=Magdalena Contreras, 9=Milpa Alta, 10=Álvaro Obregón,
11=Tláhuac, 12=Tlalpan, 13=Xochimilco, 14=Benito Juárez, 15=Cuauhtémoc,
16=Miguel Hidalgo, 17=Venustiano Carranza.
"""
from __future__ import annotations

import glob

import pandas as pd

import config

CLAVE_ALCALDIA: dict[int, str] = {
    2: "Azcapotzalco",
    3: "Coyoacán",
    4: "Cuajimalpa de Morelos",
    5: "Gustavo A. Madero",
    6: "Iztacalco",
    7: "Iztapalapa",
    8: "La Magdalena Contreras",
    9: "Milpa Alta",
    10: "Álvaro Obregón",
    11: "Tláhuac",
    12: "Tlalpan",
    13: "Xochimilco",
    14: "Benito Juárez",
    15: "Cuauhtémoc",
    16: "Miguel Hidalgo",
    17: "Venustiano Carranza",
}


def panel_rezago_alcaldia() -> pd.DataFrame:
    """Rezago habitacional 2020 por alcaldía: viviendas y porcentaje con rezago."""
    ruta = config.PROC / "rezago_cdmx.csv"
    if not ruta.exists():
        return pd.DataFrame()
    r = pd.read_csv(ruta)
    r = r[r["clave_entidad_federativa"] == 9].copy()
    if r.empty:
        return pd.DataFrame()
    r["alcaldia"] = r["clave_municipio"].map(CLAVE_ALCALDIA)
    r["viviendas"] = r["con_rezago"] + r["sin_rezago"]
    r["rezago_pct"] = 100.0 * r["con_rezago"] / r["viviendas"]
    out = r[["alcaldia", "con_rezago", "sin_rezago", "viviendas", "rezago_pct"]]
    out = out.dropna(subset=["alcaldia"]).sort_values("rezago_pct", ascending=False)
    out.to_csv(config.PROC / "rezago_alcaldia.csv", index=False)
    return out.reset_index(drop=True)


def _leer_deficit() -> pd.DataFrame:
    for f in sorted(glob.glob(str(config.RAW / "*eficit*"))):
        try:
            return pd.read_excel(f)
        except Exception:  # noqa: BLE001
            continue
    return pd.DataFrame()


def cifras_deficit() -> dict:
    """Déficit habitacional de la CDMX y presión de la oferta (SNIIV)."""
    d = _leer_deficit()
    if d.empty or "ent" not in d.columns:
        return {}
    fila = d[d["ent"] == 9]
    if fila.empty:
        return {}
    fila = fila.sort_values("anio").iloc[-1]
    fin = pd.read_csv(config.PROC / "financiamientos_anual.csv")
    fin = fin[fin["anio_calendario"] <= 2024].sort_values("anio_calendario")
    produccion = float(fin.iloc[-1]["acciones"]) if not fin.empty else float("nan")
    anio_prod = int(fin.iloc[-1]["anio_calendario"]) if not fin.empty else None

    nec = float(fila["nec_viv"])
    rezago = float(fila["rezago"])
    deficit = float(fila["deficit_h"])
    brecha = nec - produccion
    return {
        "anio": int(fila["anio"]),
        "necesidades": nec,
        "rezago": rezago,
        "deficit": deficit,
        "produccion": produccion,
        "anio_produccion": anio_prod,
        "cobertura": produccion / nec if nec else float("nan"),
        "brecha": brecha,
        "anios_cierre": rezago / produccion if produccion else float("nan"),
    }


def panel_estres() -> pd.DataFrame:
    """Producción anual de crédito vs. necesidades anuales (SNIIV)."""
    fin = pd.read_csv(config.PROC / "financiamientos_anual.csv")
    return fin[fin["anio_calendario"] <= 2024].sort_values("anio_calendario")
