"""Índices compuestos "dónde comprar" por alcaldía.

Dos índices en escala 0–100 (más alto = mejor), calculados con las variables
disponibles en el proyecto. Los pesos son una decisión editorial explícita y
ajustable aquí:

- `indice_oportunidad` (para comprar): requiere precio de portales, por lo que
  solo cubre las alcaldías con muestra suficiente en PADIM (~8).
    · barato          0.30  → precio/m² bajo vs el resto (min-max invertido)
    · asequible       0.20  → % de hogares que cubren la cuota al 30% (ENIGH)
    · servicios       0.20  → vivienda con agua, drenaje, luz y piso firme
    · marginación     0.15  → menor % de población en marginación alta (CONAPO)
    · pobreza         0.15  → menor % de población en pobreza (CONEVAL)

- `indice_calidad` (para vivir): sin precio, cubre las 16 alcaldías.
    · servicios       0.40
    · marginación     0.25
    · pobreza         0.25
    · hacinamiento    0.10  → menos personas por cuarto

Cada variable se reescala a 0–100 con min-max entre alcaldías y se orienta
"más = mejor" antes de promediar. Los índices son **relativos a la CDMX**.
"""
from __future__ import annotations

import pandas as pd

PESOS_OPORTUNIDAD = {
    "barato": 0.30,
    "asequible": 0.20,
    "servicios": 0.20,
    "marginacion": 0.15,
    "pobreza": 0.15,
}
PESOS_CALIDAD = {
    "servicios": 0.40,
    "marginacion": 0.25,
    "pobreza": 0.25,
    "hacinamiento": 0.10,
}


def _escala(serie: pd.Series, *, invertir: bool = False) -> pd.Series:
    """Reescala a 0–100 (min-max). `invertir` para que el valor bajo sea mejor."""
    v = pd.to_numeric(serie, errors="coerce")
    lo, hi = v.min(), v.max()
    if pd.isna(lo) or hi - lo < 1e-12:
        return pd.Series(50.0, index=serie.index)
    esc = (v - lo) / (hi - lo) * 100
    return 100 - esc if invertir else esc


def _promedio_ponderado(
    comps: pd.DataFrame, pesos: dict, requeridos: tuple[str, ...] = ()
) -> pd.Series:
    num = pd.Series(0.0, index=comps.index)
    den = pd.Series(0.0, index=comps.index)
    for var, w in pesos.items():
        if var not in comps.columns:
            continue
        num = num.add(comps[var] * w, fill_value=0)
        den = den.add(comps[var].notna() * w, fill_value=0)
    faltan = pd.Series(False, index=comps.index)
    for var in requeridos:
        if var in comps.columns:
            faltan = faltan | comps[var].isna()
        else:
            faltan = pd.Series(True, index=comps.index)
    res = (num / den).round(1)
    return res.mask(faltan)


def panel_indices(
    causas: pd.DataFrame,
    asequibilidad: pd.DataFrame,
    marginacion: pd.DataFrame,
    coneval: pd.DataFrame,
) -> pd.DataFrame:
    """Construye el panel de índices por alcaldía (CSV en data/processed)."""
    base = pd.DataFrame({"alcaldia": causas["alcaldia"].astype(str)})
    base = base.join(causas.set_index("alcaldia").astype(object), on="alcaldia")[
        ["alcaldia", "precio_m2_mediana", "airbnb_x1000", "vac_pct",
         "uso_temporal_pct", "oferta_x1000", "hacinamiento_prom",
         "vph_sin_agua_pct", "vph_sin_drenaje_pct", "vph_sin_elec_pct",
         "vph_piso_tierra_pct"]
    ]
    base = base.merge(
        asequibilidad[["alcaldia", "share_hogares_alcanza_30pct", "anios_ingreso"]],
        on="alcaldia", how="left",
    )
    marg = marginacion.copy()
    marg["marg_alta_pct"] = (marg["share_Alto"] + marg["share_Muy_alto"]) * 100
    base = base.merge(marg[["alcaldia", "marg_alta_pct"]], on="alcaldia", how="left")
    base = base.merge(
        coneval[["alcaldia", "pobreza_porcentaje"]], on="alcaldia", how="left",
    )

    servicios = 100 - base[
        ["vph_sin_agua_pct", "vph_sin_drenaje_pct",
         "vph_sin_elec_pct", "vph_piso_tierra_pct"]
    ].mean(axis=1)

    comps = pd.DataFrame(index=base.index)
    comps["barato"] = _escala(base["precio_m2_mediana"], invertir=True)
    comps["asequible"] = _escala(base["share_hogares_alcanza_30pct"])
    comps["servicios"] = _escala(servicios)
    comps["marginacion"] = _escala(base["marg_alta_pct"], invertir=True)
    comps["pobreza"] = _escala(base["pobreza_porcentaje"], invertir=True)
    comps["hacinamiento"] = _escala(base["hacinamiento_prom"], invertir=True)

    base["indice_oportunidad"] = _promedio_ponderado(
        comps, PESOS_OPORTUNIDAD, requeridos=("barato", "asequible", "servicios")
    )
    base["indice_calidad"] = _promedio_ponderado(
        comps, PESOS_CALIDAD, requeridos=("servicios", "marginacion", "pobreza")
    )
    base["rank_oportunidad"] = base["indice_oportunidad"].rank(
        ascending=False, method="min"
    )
    base["rank_calidad"] = base["indice_calidad"].rank(ascending=False, method="min")
    for c in comps.columns:
        base[f"c_{c}"] = comps[c].round(1)
    return base
