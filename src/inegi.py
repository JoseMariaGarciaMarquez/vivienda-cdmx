"""INEGI Censo 2020: principales resultados por AGEB y manzana urbana (CDMX).

Descarga directa desde Datos Abiertos (sin token): el ZIP de la entidad 09 trae
un CSV único con 230 indicadores del cuestionario básico a nivel manzana
(~66k), AGEB, localidad, municipio y entidad. Variables de población (grupos
etarios, PEA), vivienda (cuartos, servicios, hacinamiento) y geografía.

Referencia: https://www.inegi.org.mx/programas/ccpv/2020/#Datos-abiertos
Patrón:     datosabiertos/ageb_manzana/ageb_mza_urbana_{entidad}_cpv2020_csv.zip
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

import config
from geo import norm_alcaldia

URL_BASE = (
    "https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/ageb_manzana"
)
ENTIDAD = "09"
NA = ["N/A", "N/D", "*", ""]

VARS_CENSO = [
    "ENTIDAD", "MUN", "LOC", "AGEB", "MZA",
    "POBTOT", "POBFEM", "POBMAS",
    "P_0A2", "P_3A5", "P_6A11", "P_12A14", "P_15A17", "P_18A24", "P_60YMAS",
    "P_12YMAS", "P_15YMAS", "P_18YMAS", "PEA", "POCUPADA", "PDESOCUP",
    "VIVTOT", "VIVPAR_HAB", "VIVPAR_DES", "VIVPAR_UT", "OCUPVIVPAR",
    "PROM_OCUP", "PRO_OCUP_C",
    "VPH_1CUART", "VPH_2CUART", "VPH_3YMASC",
    "VPH_C_ELEC", "VPH_S_ELEC", "VPH_AGUADV", "VPH_AGUAFV",
    "VPH_DRENAJ", "VPH_NODREN", "VPH_EXCSA", "VPH_LETR",
    "VPH_PISOTI", "VPH_PISODT", "VPH_C_SERV", "VPH_NDEAED",
]

ZIP = "ageb_mza_urbana_{ent}_cpv2020_csv.zip"


def _zip_path() -> Path:
    return config.RAW / "inegi" / ZIP.format(ent=ENTIDAD)


def _csv_path() -> Path:
    return (
        config.RAW / "inegi"
        / f"ageb_mza_urbana_{ENTIDAD}_cpv2020/conjunto_de_datos/"
        / f"conjunto_de_datos_ageb_urbana_{ENTIDAD}_cpv2020.csv"
    )


def descargar() -> Path:
    import requests

    z = _zip_path()
    if z.exists():
        return z
    config.RAW.joinpath("inegi").mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
        "Accept": "application/zip,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    }
    url = f"{URL_BASE}/{ZIP.format(ent=ENTIDAD)}"
    r = requests.get(url, headers=headers, timeout=300, stream=True)
    r.raise_for_status()
    z.write_bytes(r.content)
    import zipfile

    with zipfile.ZipFile(z) as arc:
        arc.extractall(config.RAW / "inegi")
    return z


def _leer() -> pd.DataFrame:
    if not _csv_path().exists():
        descargar()
    dtype_str = {c: str for c in ("ENTIDAD", "MUN", "LOC", "AGEB", "MZA")}
    df = pd.read_csv(_csv_path(), encoding="utf-8-sig", na_values=NA, low_memory=False,
                     dtype=dtype_str)
    df["_MZA_str"] = df["MZA"]
    for c in VARS_CENSO:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["alcaldia"] = df["NOM_MUN"].map(norm_alcaldia)
    df["entidad"] = df["ENTIDAD"].map(lambda s: _llenar(s, 2))
    df["mun"] = df["MUN"].map(lambda s: _llenar(s, 3))
    df["loc"] = df["LOC"].map(lambda s: _llenar(s, 4))
    df["ageb"] = df["AGEB"].map(lambda s: _llenar(s, 4))
    df["cve_ageb"] = df["entidad"] + df["mun"] + df["loc"] + df["ageb"]
    return df


def _llenar(valor: object, n: int) -> str:
    """Clave geográfica: valor como cadena con ceros a la izquierda."""
    s = str(valor).strip()
    if s in {"", "nan", "None"}:
        return "0" * n
    return s.split(".")[0].zfill(n)


def _indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """Indicadores de vivienda/población por fila (manzana o AGEB)."""
    x = df.copy()
    men = x["P_0A2"] + x["P_3A5"] + x["P_6A11"] + x["P_12A14"]
    x["pob_menor15"] = men
    x["pob_15a59"] = (x["POBTOT"] - men - x["P_60YMAS"]).clip(lower=0)
    x["pob_mayor60"] = x["P_60YMAS"]
    x["indice_dependencia"] = (
        (x["pob_menor15"] + x["pob_mayor60"]) / x["pob_15a59"].replace(0, pd.NA) * 100
    )
    x["tasa_masculinidad"] = x["POBFEM"].replace(0, pd.NA)
    x["tasa_masculinidad"] = x["POBMAS"] / x["tasa_masculinidad"] * 100
    x["hacinamiento_prom"] = x["PRO_OCUP_C"]
    x["vph_sin_agua_pct"] = x["VPH_AGUAFV"] / x["VIVPAR_HAB"].replace(0, pd.NA) * 100
    x["vph_sin_drenaje_pct"] = x["VPH_NODREN"] / x["VIVPAR_HAB"].replace(0, pd.NA) * 100
    x["vph_sin_elec_pct"] = x["VPH_S_ELEC"] / x["VIVPAR_HAB"].replace(0, pd.NA) * 100
    x["vph_piso_tierra_pct"] = x["VPH_PISOTI"] / x["VIVPAR_HAB"].replace(0, pd.NA) * 100
    x["vph_sin_3_serv_pct"] = x["VPH_NDEAED"] / x["VIVPAR_HAB"].replace(0, pd.NA) * 100
    x["tasa_actividad"] = x["PEA"] / x["P_12YMAS"].replace(0, pd.NA) * 100
    return x


def manzanas() -> pd.DataFrame:
    """Panel de manzanas urbanas CDMX (66k) + indicadores derivados."""
    df = _leer()
    m = df[df["MZA"] > 0].copy()
    m["mza"] = m["_MZA_str"].map(lambda s: _llenar(s, 3))
    m["cve_manzana"] = m["cve_ageb"] + m["mza"]
    m = _indicadores(m)
    m = m.dropna(subset=["alcaldia"])
    cols = ["cve_manzana", "cve_ageb", "entidad", "mun", "loc", "ageb", "alcaldia",
            "NOM_LOC"] + [c for c in m.columns if c not in
                          {"cve_manzana", "cve_ageb", "entidad", "mun", "loc", "ageb",
                           "alcaldia", "NOM_LOC", "MZA", "ENTIDAD", "MUN", "LOC", "AGEB"}]
    m[cols].to_csv(config.PROC / "censo2020_manzanas_cdmx.csv", index=False)
    return m


def agebs() -> pd.DataFrame:
    """Panel de AGEB urbanas (agregado oficial del censo) + indicadores."""
    df = _leer()
    a = df[(df["MZA"] == 0) & (df["ageb"] != "0000")].copy()
    a = _indicadores(a)
    a = a.dropna(subset=["alcaldia"])
    cols = ["cve_ageb", "entidad", "mun", "loc", "ageb", "alcaldia", "NOM_LOC"] + [
        c for c in a.columns if c not in
        {"cve_ageb", "entidad", "mun", "loc", "ageb", "alcaldia", "NOM_LOC",
         "MZA", "ENTIDAD", "MUN", "LOC", "AGEB"}]
    a[cols].to_csv(config.PROC / "censo2020_ageb_cdmx.csv", index=False)
    return a


def por_alcaldia() -> pd.DataFrame:
    """Agregación de manzanas a nivel alcaldía con indicadores ponderados."""
    m = manzanas()
    nums = [c for c in VARS_CENSO if c in m.columns and m[c].dtype.kind in "fi"]
    g = m.groupby("alcaldia")[nums].sum(min_count=1)
    g["pob_menor15"] = (g["P_0A2"] + g["P_3A5"] + g["P_6A11"] + g["P_12A14"])
    g["pob_15a59"] = (g["POBTOT"] - g["pob_menor15"] - g["P_60YMAS"]).clip(lower=0)
    g["indice_dependencia"] = (
        (g["pob_menor15"] + g["P_60YMAS"]) / g["pob_15a59"].replace(0, pd.NA) * 100
    )
    vh = g["VIVPAR_HAB"]
    g["tasa_masculinidad"] = g["POBMAS"] / g["POBFEM"].replace(0, pd.NA) * 100
    g["hacinamiento_prom"] = g["OCUPVIVPAR"] / vh.replace(0, pd.NA)
    g["vph_sin_agua_pct"] = g["VPH_AGUAFV"] / vh.replace(0, pd.NA) * 100
    g["vph_sin_drenaje_pct"] = g["VPH_NODREN"] / vh.replace(0, pd.NA) * 100
    g["vph_sin_elec_pct"] = g["VPH_S_ELEC"] / vh.replace(0, pd.NA) * 100
    g["vph_piso_tierra_pct"] = g["VPH_PISOTI"] / vh.replace(0, pd.NA) * 100
    g["vph_sin_3_serv_pct"] = g["VPH_NDEAED"] / vh.replace(0, pd.NA) * 100
    g["tasa_actividad"] = g["PEA"] / g["P_12YMAS"].replace(0, pd.NA) * 100
    g = g.reset_index()
    g.to_csv(config.PROC / "censo2020_alcaldia.csv", index=False)
    return g


def cruce_ageb_marginacion() -> pd.DataFrame:
    """AGEB del censo cruzadas con la marginación CONAPO (misma clave)."""
    a = agebs()
    m = a[["cve_ageb", "alcaldia", "POBTOT", "VIVPAR_HAB", "VPH_NDEAED"]]
    con = pd.read_csv(config.PROC / "conapo_marginacion_ageb.csv")
    c = m.merge(
        con[["CVE_AGEB", "IM_2020", "GM_2020", "IMN_2020", "POB_TOTAL"]],
        left_on="cve_ageb", right_on="CVE_AGEB", how="inner",
    )
    c.to_csv(config.PROC / "censo2020_ageb_marginacion.csv", index=False)
    return c