"""Pipeline vivienda-cdmx: datos -> paneles -> diagnóstico -> dashboard.

Uso:
    python main.py            # usa caché de data/raw si existe
    python main.py --refresh  # re-descarga PADIM (snapshot) y SNIIV
"""
from __future__ import annotations

import argparse

import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import analyze
import build
import causas
import indices
import interactivo
import conapo
import coneval
import config
import deficit
import derive
import enigh
import inegi
import padim
import publicar
import report
import seduvi
import sepomex
import shf
import sniiv


def etapa_portales() -> None:
    print("[1/4] Portales (PADIM, snapshot CDMX)...")
    df = padim.fetch_cdmx(con_geo=True)
    if df.empty:
        print("  sin datos de PADIM")
        return
    out = padim.guardar_snapshot(df)
    print(f"  observaciones: {len(df):,} -> {out.name}")


def etapa_sniiv() -> None:
    print("[2/4] SNIIV (oferta + crédito)...")
    indice = sniiv.indice_datos_abiertos()
    print(f"  catálogo datos abiertos: {len(indice)} enlaces")
    sniiv.descarga_abiertos(indice)
    fin = sniiv.financiamientos_cdmx()
    if not fin.empty:
        print(f"  financiamientos: {len(fin)} filas (CDMX 2013-hoy)")
    seduvi.catalogo_suelo()


def etapa_socio() -> None:
    print("[2.5/4] Socio (SEPOMEX CP + CONAPO marginación)...")
    cp = sepomex.preparar()
    print(f"  SEPOMEX: {len(cp):,} asentamientos / {cp['cp'].nunique():,} CP")
    colonia = conapo.marginacion_colonia()
    conapo.marginacion_ageb()
    print(f"  CONAPO: {len(colonia):,} registros de colonia en CDMX")


def etapa_censo() -> None:
    print("[2.6/4] Censo 2020 (INEGI: manzanas + AGEB)...")
    mz = inegi.manzanas()
    ab = inegi.agebs()
    al = inegi.por_alcaldia()
    cruce = inegi.cruce_ageb_marginacion()
    print(f"  manzanas {len(mz):,} · AGEB {len(ab):,} · alcaldías {len(al)}")
    print(f"  AGEB censo↔CONAPO: {len(cruce):,} coincidencias")


def etapa_asequibilidad() -> None:
    print("[2.7/4] Asequibilidad (ENIGH 2022 + CONEVAL 2020 + INPC)...")
    coneval.pobreza_alcaldia()
    pob = _leer("coneval_pobreza_alcaldia.csv")
    print(f"  CONEVAL: {len(pob)} alcaldías con medición de pobreza 2020")
    enigh.ingresos_cdmx()
    ing = _leer("enigh_cdmx_ingresos.csv")
    hog = _leer("enigh_cdmx_hogares.csv")
    mediana = build.panel_alcaldias(build.paneles_padim()["portales_actual"])
    aseq = derive.asequibilidad(mediana, ing, hog)
    if not aseq.empty:
        mejor = aseq.sort_values("anios_ingreso").iloc[0]
        print(f"  + accesible: {mejor['alcaldia']} ({mejor['anios_ingreso']} años de ingreso)")


def etapa_analisis() -> str:
    print("[3/4] Paneles y diagnóstico...")
    paneles = build.paneles_padim()
    mediana = build.panel_alcaldias(paneles["portales_actual"])
    fin = build.panel_financiamientos()
    build.panel_rezago()
    ratios = derive.ratios_venta_renta(mediana)
    fin_anual = derive.serie_financiamientos(fin)
    shf.cargar_indice()
    marg = _leer("marginacion_alcaldia.csv")
    censo = _leer("censo2020_alcaldia.csv")
    coneval_ = _leer("coneval_pobreza_alcaldia.csv")
    aseq = _leer("asequibilidad.csv")
    fecha = _fecha_snapshot()
    df_causas = causas.panel_causas()
    print(f"  causas: {len(df_causas)} alcaldías (vacancia + Airbnb + oferta)")
    df_indices = indices.panel_indices(df_causas, aseq, marg, coneval_)
    df_indices.to_csv(config.PROC / "indice_compra.csv", index=False)
    print(f"  índices de compra: {df_indices['indice_oportunidad'].notna().sum()} alcaldías"
          " con oportunidad · " f"{df_indices['indice_calidad'].notna().sum()} con calidad")
    rezago = deficit.panel_rezago_alcaldia()
    cifras = deficit.cifras_deficit()
    if cifras:
        print(f"  déficit habitacional CDMX {cifras['anio']}: "
              f"{cifras['deficit']:,.0f} viviendas"
              f" · producción {cifras['produccion']:,.0f}/año"
              f" ({cifras['cobertura']:.0%} de las necesidades)")
    return analyze.hacer_resumen(
        mediana, ratios, fin_anual, marg,
        censo=censo, coneval=coneval_, asequibilidad=aseq,
        causas=df_causas, indices=df_indices, rezago=rezago, deficit=cifras,
        fecha_corte=fecha,
    )


def _fecha_snapshot() -> str:
    import os

    snapshots = sorted(os.path.basename(p) for p in glob.glob(str(config.RAW / "padim_cdmx_*.csv.gz")))
    if not snapshots:
        return "sin snapshot"
    return snapshots[-1].replace("padim_cdmx_", "").replace(".csv.gz", "")


def etapa_report(resumen: str) -> None:
    print("[4/4] Gráficas y dashboard HTML...")
    report.grafica_m2_alcaldias(_leer("alcaldias_mediana.csv"), config.CHARTS / "m2_alcaldias.png")
    report.grafica_box_m2(_leer("portales_series.csv").copy(), config.CHARTS / "box_m2.png")
    report.grafica_financiamientos(_leer("financiamientos_anual.csv"), config.CHARTS / "financiamientos.png")
    report.grafica_ratio(_leer("ratios_venta_renta.csv"), config.CHARTS / "ratio_precio_renta.png")
    report.grafica_marginacion(_leer("marginacion_alcaldia.csv"), config.CHARTS / "marginacion.png")
    report.grafica_mapa_marginacion(
        _leer("marginacion_alcaldia.csv"), config.CHARTS / "mapa_marginacion.png"
    )
    report.grafica_mapa_precio(
        _leer("alcaldias_mediana.csv"), config.CHARTS / "mapa_precio.png"
    )
    report.grafica_shf(_leer("shf_cdmx.csv"), config.CHARTS / "shf_indices.png")
    report.grafica_censo(_leer("censo2020_alcaldia.csv"), config.CHARTS / "censo2020.png")
    report.grafica_asequibilidad(
        _leer("asequibilidad.csv"),
        config.CHARTS / "asequibilidad.png",
    )
    report.grafica_mapa_isai(
        _leer("alcaldias_mediana.csv"),
        config.CHARTS / "mapa_isai_compra.png",
    )
    report.grafica_mapa_predial(
        _leer("alcaldias_mediana.csv"),
        config.CHARTS / "mapa_predial.png",
    )
    causas_df = _leer("causas_alcaldia.csv")
    report.grafica_mapa_airbnb(causas_df, config.CHARTS / "mapa_airbnb.png")
    report.grafica_causas(causas_df, config.CHARTS / "causas_dispersion.png")
    indice_df = _leer("indice_compra.csv")
    report.grafica_mapa_indice(
        indice_df, config.CHARTS / "mapa_oportunidad.png",
        col="indice_oportunidad",
        titulo="¿Dónde comprar? Índice de oportunidad (0–100), por alcaldía",
        eje="índice de oportunidad (precio + asequibilidad + servicios; 0–100)",
    )
    report.grafica_mapa_indice(
        indice_df, config.CHARTS / "mapa_calidad.png",
        col="indice_calidad",
        titulo="Calidad de vida sin precio (0–100), por alcaldía",
        eje="índice de calidad (servicios + marginación + pobreza; 0–100)",
    )
    rezago_df = _leer("rezago_alcaldia.csv")
    report.grafica_mapa_rezago(rezago_df, config.CHARTS / "mapa_rezago.png")
    cifras_deficit = deficit.cifras_deficit()
    report.grafica_estres_oferta(
        deficit.panel_estres(), cifras_deficit, config.CHARTS / "estres_oferta.png"
    )
    graficas = [
        {"seccion": "Precios y oferta", "archivo": "m2_alcaldias.png",
         "titulo": "Precio mediano del m² en venta",
         "nota": "Mediana sobre el inventario en oferta de portales (PADIM)."},
        {"seccion": "Precios y oferta", "archivo": "mapa_precio.png",
         "titulo": "Precio del m² en venta, mapa",
         "nota": "Centro-poniente caro, sur-periferia barato. Gris = alcaldías sin muestra suficiente en portales."},
        {"seccion": "Precios y oferta", "archivo": "box_m2.png",
         "titulo": "Distribución del precio por m² en venta",
         "nota": "Por alcaldía, banda residencial recortada a percentil 3-97."},
        {"seccion": "Precios y oferta", "archivo": "shf_indices.png",
         "titulo": "Índice de precios SHF por alcaldía",
         "nota": "Serie oficial de referencia (2017-hoy); requiere descarga manual."},
        {"seccion": "Asequibilidad y sociedad", "archivo": "asequibilidad.png",
         "titulo": "Asequibilidad de la vivienda en venta",
         "nota": "Años del ingreso mediano del hogar (CDMX, ENIGH 2022 + INPC 2026) para comprar la mediana."},
        {"seccion": "Asequibilidad y sociedad", "archivo": "ratio_precio_renta.png",
         "titulo": "Ratio precio/renta por alcaldía",
         "nota": "Pendiente: PADIM aún no sirve renta."},
        {"seccion": "Asequibilidad y sociedad", "archivo": "marginacion.png",
         "titulo": "Marginación (CONAPO 2020) por alcaldía",
         "nota": "Porcentaje de la población en marginación alta o muy alta."},
        {"seccion": "Asequibilidad y sociedad", "archivo": "mapa_marginacion.png",
         "titulo": "Marginación (CONAPO 2020), mapa",
         "nota": "Índice compuesto (educación, vivienda, servicios, ingresos, residencia) "
                 "por colonia/AGEB; % de la población en grado alto o muy alto. Se concentra "
                 "en el sur (Xochimilco, Milpa Alta, Tlalpan)."},
        {"seccion": "Asequibilidad y sociedad", "archivo": "censo2020.png",
         "titulo": "Estructura y vivienda (Censo 2020 INEGI)",
         "nota": "Grupos de edad, hacinamiento y viviendas sin servicios, por alcaldía."},
        {"seccion": "Impuestos", "archivo": "mapa_isai_compra.png",
         "titulo": "Mapa: ISAI al comprar (2026)",
         "nota": "Impuesto sobre Adquisición de Inmuebles (art. 113 CCF-CDMX): % del precio mediano de la alcaldía; gris = sin dato en portales."},
        {"seccion": "Impuestos", "archivo": "mapa_predial.png",
         "titulo": "Mapa: predial anual (2026)",
         "nota": "Art. 130 CCF-CDMX, tarifa bimestral ×6 con 8% de dto. por pago en enero; catastral ≈ 40% del precio; gris = sin dato."},
        {"seccion": "¿Por qué es caro?", "archivo": "causas_dispersion.png",
         "titulo": "¿Por qué es cara la vivienda?",
         "nota": "Precio/m² vs vacancia (Censo 2020) y vs densidad de Airbnb, con ρ de Spearman; descriptivo, sin causalidad."},
        {"seccion": "¿Por qué es caro?", "archivo": "mapa_airbnb.png",
         "titulo": "Mapa: Airbnb por alcaldía",
         "nota": "Listados Inside Airbnb por cada 1,000 viviendas (parque Censo 2020). Concentración en el centro: Cuauhtémoc y Miguel Hidalgo."},
        {"seccion": "¿Dónde comprar?", "archivo": "mapa_oportunidad.png",
         "titulo": "Índice de oportunidad de compra (0–100), mapa",
         "nota": "Combina precio/m², asequibilidad y servicios de la vivienda. Alto = "
                 "mejor equilibrio para comprar. Solo las alcaldías con precio en portales."},
        {"seccion": "¿Dónde comprar?", "archivo": "mapa_calidad.png",
         "titulo": "Calidad de vida sin precio (0–100), mapa",
         "nota": "Combina servicios, marginación y pobreza para las 16 alcaldías; "
                 "útil cuando no hay dato de precio comparable."},
        {"seccion": "Déficit y oferta", "archivo": "mapa_rezago.png",
         "titulo": "Rezago habitacional 2020, mapa",
         "nota": "Porcentaje de viviendas con rezago habitacional por alcaldía (SNIIV-SEDATU, "
                 "base Censo 2020). Más alto en el sur rural (Milpa Alta, Xochimilco, Tláhuac)."},
        {"seccion": "Déficit y oferta", "archivo": "estres_oferta.png",
         "titulo": "¿Alcanza la oferta? Producción vs. necesidades",
         "nota": "Acciones de crédito por año (SNIIV) frente a las necesidades anuales de "
                 "vivienda de la CDMX; cuando la barra cae bajo la línea, el déficit crece."},
        {"seccion": "Crédito y financiamiento", "archivo": "financiamientos.png",
         "titulo": "Financiamientos de vivienda CDMX",
         "nota": "Acciones de crédito anuales, todas las ONAs (SNIIV)."},
    ]
    out = report.hacer_dashboard(graficas, resumen)
    interactivo.hacer_dashboard_interactivo(
        resumen,
        causas=causas_df,
        margin_alcaldia=_leer("marginacion_alcaldia.csv"),
        financiamientos=_leer("financiamientos_anual.csv"),
        indice=indice_df,
        rezago=rezago_df,
    )
    pagina = publicar.hacer_pagina()
    print(f"Dashboard: {out}")
    print(f"Resumen:   {config.OUT / 'resumen_vivienda.txt'}")
    print(f"Página:    {pagina}  (GitHub Pages sirve /docs)")


def _leer(nombre: str):
    import pandas as pd

    path = config.PROC / nombre
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def main() -> None:
    parser = argparse.ArgumentParser(description="Mercado de la vivienda en CDMX")
    parser.add_argument("--refresh", action="store_true", help="re-descargar fuentes")
    args = parser.parse_args()

    if args.refresh:
        etapa_portales()
        etapa_sniiv()
    else:
        print("[saltando descargas: usa --refresh para re-descargar]")

    etapa_socio()
    etapa_censo()
    etapa_asequibilidad()

    resumen = etapa_analisis()
    etapa_report(resumen)


if __name__ == "__main__":
    main()