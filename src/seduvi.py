"""Suelo, catastro y permisos desde datos.cdmx.gob.mx (CKAN).

La variable física clave es el valor unitario del suelo por zona; cruzada con el
precio de la vivienda da el *share de suelo* (qué tanto del precio es terreno).
"""
from __future__ import annotations

import requests

import config

TIMEOUT = 60


def buscar_datos(consulta: str, filas: int = 5) -> list[dict]:
    r = requests.get(
        f"{config.CKAN_CDMX}/package_search",
        params={"q": consulta, "rows": filas},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()["result"]["results"]


def recursos_conjunto(nombre: str) -> list[dict]:
    """Recursos (CSV/SHP/GeoJSON) de un conjunto de datos por su slug."""
    r = requests.get(
        f"{config.CKAN_CDMX}/package_show", params={"id": nombre}, timeout=TIMEOUT
    )
    r.raise_for_status()
    return r.json()["result"]["resources"]


def catalogo_suelo() -> None:
    """Imprime y guarda el catálogo de valores de suelo / catastro disponible."""
    resultados: list[dict] = []
    for slug in config.CKAN_DATASETS.values():
        recursos = recursos_conjunto(slug)
        resultados.append({"conjunto": slug, "recursos": len(recursos)})
        for rec in recursos:
            print(f"  {slug} :: {rec['name']} [{rec.get('format')}]")
    import csv

    with (config.PROC / "cdmx_suelo_catalogo.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["conjunto", "recursos"])
        w.writeheader()
        w.writerows(resultados)