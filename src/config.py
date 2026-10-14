"""Rutas, fuentes y catálogos del proyecto vivienda-cdmx."""
from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "data" / "raw"
PROC = RAIZ / "data" / "processed"
OUT = RAIZ / "outputs"
CHARTS = OUT / "charts"
for _p in (RAW, PROC, OUT, CHARTS):
    _p.mkdir(parents=True, exist_ok=True)

# Entidades y geografía -----------------------------------------------------
CDMX_CLAVE = "09"

ALCALDIAS = [
    "Álvaro Obregón", "Azcapotzalco", "Benito Juárez", "Coyoacán",
    "Cuajimalpa de Morelos", "Cuauhtémoc", "Gustavo A. Madero",
    "Iztacalco", "Iztapalapa", "La Magdalena Contreras", "Miguel Hidalgo",
    "Milpa Alta", "Tláhuac", "Tlalpan", "Venustiano Carranza", "Xochimilco",
]

# INEGI agebs/manzanas -> CP: los CP de CDMX NO son polígonos contiguos
# (cuadras agrupadas). El bridge colonia<->CP se arma con el directorio
# SEPOMEX; decisión de diseño documentada en NOTES.md.

# SNIIV / SEDATU ------------------------------------------------------------
SNIIV_DATOS_ABIERTOS = "https://sniiv.sedatu.gob.mx/Reporte/Datos_abiertos"
SNIIV_CUBO = "https://sniiv.sedatu.gob.mx/api/CuboAPI"

# URLs de ficheros abiertos verificados (jun 2026). Si cambian, la función
# descubre candidatas desde SNIIV_DATOS_ABIERTOS y filtra por estos patrones.
SNIIV_MANIFEST = {
    "deficit_vivienda": None,  # nombre genérico; se resuelve por descubrimiento
    "rezago_municipal_2020": ("brPGRXRIRl21UTZLP1ic4A", "rezago_habitacional_mun_2020.csv"),
    "rezago_estatal_2020": ("kOs6u3tBRtuIxzql5nTcfQ", "rezago_habitacional_est_2020.csv"),
}

# PADIM ----------------------------------------------------------------------
PADIM_BASE = "https://api.padim.org"

# SEDUVI / datos.cdmx -------------------------------------------------------
CKAN_CDMX = "https://datos.cdmx.gob.mx/api/3/action"
CKAN_DATASETS = {
    "valores_suelo": "valores-unitarios-del-suelo-habitacional-habitacional-comercial-en-pesos-valor-promedio",
    "catastro": "informacion-catastral-de-la-ciudad-de-mexico",
}

# CONAPO / marginación -------------------------------------------------------
CONAPO_BASE_DATASET = "d8f2a534-bcee-4114-853d-82982a81ce24"
CONAPO_URLS = {
    "marginacion_colonia": (
        f"https://www.datos.gob.mx/dataset/{CONAPO_BASE_DATASET}/resource/faabdc7b-dc41-4df3-9664-ee14e805f0df/download/imuc_2020.csv"
    ),
    "marginacion_ageb": (
        f"https://www.datos.gob.mx/dataset/{CONAPO_BASE_DATASET}/resource/9600f414-c1ba-408a-8dd6-7f73d76601d4/download/imu_2020.csv"
    ),
}

# SEPOMEX --------------------------------------------------------------------
SEPOMEX_URL = "https://www.correosdemexico.gob.mx/SSLServicios/ConsultaCP/CodigoPostal_Exportar.aspx"

# INEGI Censo 2020 / ENIGH / INPC --------------------------------------------
INEGI_DATOS_ABIERTOS = "https://www.inegi.org.mx/contenidos/programas"
CENSO_AGEB_MZA_URL = (
    INEGI_DATOS_ABIERTOS + "/ccpv/2020/datosabiertos/ageb_manzana/"
    f"ageb_mza_urbana_{CDMX_CLAVE}_cpv2020_csv.zip"
)
ENIGH_2022_URL = (
    INEGI_DATOS_ABIERTOS + "/enigh/nc/2022/microdatos/"
    "enigh2022_ns_concentradohogar_csv.zip"
)
INPC_URL = (
    INEGI_DATOS_ABIERTOS + "/inpc/2018a/datosabiertos/"
    "conjunto_de_datos_inpc_indicador_mensual_csv.zip"
)

# CONEVAL pobreza a nivel municipal (2020) -----------------------------------
CONEVAL_POBREZA_URL = (
    "https://www.datos.gob.mx/dataset/b6981ccc-083b-4e57-ba6f-d800a7398fa8/"
    "resource/6e409e3a-aa08-45f5-b84b-f5d8cc6fafa8/download/pobreza_municipal.csv"
)

# SHF (índice de precios) ----------------------------------------------------
# El CSV abierto vive en transparencia.shf.gob.mx / gob.mx pero detrás de
# Akamai (bloquea UA no-browser). Serie 2017T1->último trimestre, por alcaldía,
# vivienda nueva/usada y tipología. Descarga manual -> data/raw/shf_indice.csv
SHF_CSV_RAW = RAW / "shf_indice.csv"