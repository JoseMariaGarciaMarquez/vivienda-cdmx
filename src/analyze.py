"""Diagnóstico en texto del mercado de la vivienda en CDMX."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

import config
import impuestos


def _fmt(x: float) -> str:
    return f"${x:,.0f}"


def hacer_resumen(
    mediana: pd.DataFrame,
    ratios: pd.DataFrame,
    financiamientos_anual: pd.DataFrame,
    marginacion: pd.DataFrame | None = None,
    censo: pd.DataFrame | None = None,
    coneval: pd.DataFrame | None = None,
    asequibilidad: pd.DataFrame | None = None,
    causas: pd.DataFrame | None = None,
    indices: pd.DataFrame | None = None,
    rezago: pd.DataFrame | None = None,
    deficit: dict | None = None,
    fecha_corte: str | None = None,
) -> str:  # noqa: PLR0912
    lineas: list[str] = []
    lineas.append("MERCADO DE LA VIVIENDA EN CDMX — RESUMEN")
    lineas.append("=" * 60)
    lineas.append(f"Corte de portales: {fecha_corte or 'snapshot más reciente'}")
    lineas.append("Medidas del INVENTARIO EN VENTA (portales), no de transacciones ni avalúos.")

    venta = mediana[mediana["operacion"] == "venta"]
    if not venta.empty:
        caras = venta.sort_values("precio_m2_mediana", ascending=False)
        lineas.append("")
        lineas.append("Precio mediano por m² (venta), por alcaldía:")
        for _, x in caras.iterrows():
            lineas.append(
                f"  {x['alcaldia']:<22} {_fmt(x['precio_m2_mediana']):>12}/m²"
                f"  (n={int(x['n']):>4}, precio {_fmt(x['precio_mediana'])})"
            )
        top = caras.iloc[0]
        bot = caras.iloc[-1]
        brecha = top["precio_m2_mediana"] / bot["precio_m2_mediana"] - 1
        lineas.append(
            f"  Brecha alcaldía más cara / más barata: {brecha:.0%}"
            f"  ({top['alcaldia']} vs {bot['alcaldia']})"
        )

    if not ratios.empty:
        lineas.append("")
        lineas.append("Meses de renta para pagar la compra (por alcaldía):")
        for _, x in ratios.sort_values("meses_de_renta").iterrows():
            lineas.append(f"  {x['alcaldia']:<22} {x['meses_de_renta']:>7.1f}")

    if not financiamientos_anual.empty:
        recientes = financiamientos_anual.sort_values("anio_calendario").tail(3)
        lineas.append("")
        lineas.append("Financiamientos de vivienda CDMX (acciones, último trienio):")
        for _, x in recientes.iterrows():
            lineas.append(
                f"  {int(x['anio_calendario'])}: {int(x['acciones']):>7,} acciones"
                f"  · {x['monto_mdp']:,.1f} MDP"
            )

    if marginacion is not None and not marginacion.empty:
        lineas.append("")
        lineas.append("Perfil sociodemográfico (CONAPO 2020, por alcaldía):")
        marg = marginacion.copy()
        marg["share_alta_total"] = marg["share_Alto"] + marg["share_Muy_alto"]
        marg = marg.sort_values("share_alta_total", ascending=False)
        for _, x in marg.iterrows():
            alta_muy = x["share_alta_total"] * 100
            lineas.append(
                f"  {x['alcaldia']:<22} {alta_muy:>5.1f}% en marg. alta/muy alta"
                f"  · población {int(x['poblacion_2020']):>8,}"
            )
        _cruza_precio_marginacion(lineas, mediana, marginacion)

    if censo is not None and not censo.empty:
        lineas.append("")
        lineas.append("Censo 2020 (INEGI, por alcaldía; manzanas urbanas):")
        cx = censo.copy()
        cx["menor15"] = cx["P_0A2"] + cx["P_3A5"] + cx["P_6A11"] + cx["P_12A14"]
        cx["60_mas_pct"] = cx["P_60YMAS"] / cx["POBTOT"] * 100
        cx["menor15_pct"] = cx["menor15"] / cx["POBTOT"] * 100
        cx = cx.sort_values("indice_dependencia", ascending=False)
        for _, x in cx.iterrows():
            lineas.append(
                f"  {x['alcaldia']:<22} dep. {x['indice_dependencia']:>5.1f}%"
                f"  · 60+: {x['60_mas_pct']:>4.1f}% · <15: {x['menor15_pct']:>4.1f}%"
                f"  · hacin. {x['hacinamiento_prom']:>4.2f} · sin agua {x['vph_sin_agua_pct']:>4.2f}%"
            )
        lineas.append(
            "  (índice de dependencia = población <15 y 60+ sobre 15-59 años;"
            " hacinamiento = personas por cuarto)"
        )

    if coneval is not None and not coneval.empty:
        lineas.append("")
        lineas.append("Pobreza 2020 (CONEVAL, por alcaldía):")
        for _, x in coneval.sort_values("pobreza_porcentaje", ascending=False).iterrows():
            lineas.append(
                f"  {x['alcaldia']:<22} pobreza {x['pobreza_porcentaje']:>5.1f}%"
                f"  · extrema {x['pobreza_extrema_porcentaje']:>4.1f}%"
                f"  · sin seg. social {x['carencia_seguridad_social_porcentaje']:>5.1f}%"
            )

    if asequibilidad is not None and not asequibilidad.empty:
        lineas.append("")
        lineas.append(
            "Asequibilidad (ingreso mediano del hogar CDMX, ENIGH 2022 → pesos 2026):"
        )
        for _, x in asequibilidad.sort_values("anios_ingreso").iterrows():
            lineas.append(
                f"  {x['alcaldia']:<22} {x['anios_ingreso']:>5.1f} años de ingreso"
                f"  · mensualidad {_fmt(x['mensualidad_estimada'])}"
                f" = {x['pct_ingreso_mensual']:>4.1f}% del ingreso"
                f"  · {x['share_hogares_alcanza_30pct']*100:>4.0f}% de hogares la alcanzan"
            )
        lineas.append(
            "  90% financiado a 20 años @10.5% anual; regla del 30%: la mensualidad"
            " no debe rebasar 30% del ingreso del hogar."
        )

    if not venta.empty:
        _bloque_impuestos(lineas, venta)
    if causas is not None and not causas.empty:
        _bloque_causas(lineas, causas)
    if indices is not None and not indices.empty:
        _bloque_indices(lineas, indices)
    if (rezago is not None and not rezago.empty) or deficit:
        _bloque_deficit(lineas, rezago, deficit)

    texto = "\n".join(lineas)
    Path(config.OUT / "resumen_vivienda.txt").write_text(texto, encoding="utf-8")
    return texto


def _bloque_indices(lineas: list[str], indice: pd.DataFrame) -> None:
    """Ranking de compra y de calidad con los índices compuestos (0–100)."""
    lineas.append("")
    lineas.append(
        "DÓNDE COMPRAR (índices 0–100, más alto = mejor; relativos a la CDMX)"
    )
    lineas.append("-" * 68)
    op = indice.dropna(subset=["indice_oportunidad"]).sort_values(
        "indice_oportunidad", ascending=False
    )
    if not op.empty:
        top = " · ".join(
            f"{i + 1}) {_ABREV_CORTO.get(x['alcaldia'], x['alcaldia'])}"
            f" {x['indice_oportunidad']:.1f}"
            for i, (_, x) in enumerate(op.head(4).iterrows())
        )
        peor = op.iloc[-1]
        lineas.append(
            f"  Oportunidad de compra (precio + asequibilidad + servicios,"
            f" {len(op)} alcaldías con portales):"
        )
        lineas.append(f"    {top}")
        lineas.append(
            f"    menos atractiva: {_ABREV_CORTO.get(peor['alcaldia'], peor['alcaldia'])}"
            f" {peor['indice_oportunidad']:.1f}"
        )
    ca = indice.dropna(subset=["indice_calidad"]).sort_values(
        "indice_calidad", ascending=False
    )
    if not ca.empty:
        top = " · ".join(
            f"{i + 1}) {_ABREV_CORTO.get(x['alcaldia'], x['alcaldia'])}"
            f" {x['indice_calidad']:.1f}"
            for i, (_, x) in enumerate(ca.head(4).iterrows())
        )
        peor = ca.iloc[-1]
        lineas.append(
            f"  Calidad de vida sin precio (servicios + marginación + pobreza,"
            f" las {len(ca)}):"
        )
        lineas.append(f"    {top}")
        lineas.append(
            f"    menos atractiva: {_ABREV_CORTO.get(peor['alcaldia'], peor['alcaldia'])}"
            f" {peor['indice_calidad']:.1f}"
        )
    lineas.append(
        "  Pesos de cada componente en src/indices.py; política e instrumentos"
        " sugeridos en docs/politica.md."
    )


def _bloque_deficit(
    lineas: list[str],
    rezago: pd.DataFrame | None,
    deficit: dict | None,
) -> None:
    """Déficit/rezago habitacional y presión de la oferta (SNIIV-SEDATU)."""
    lineas.append("")
    lineas.append("DÉFICIT HABITACIONAL Y PRESIÓN DE LA OFERTA (SNIIV-SEDATU)")
    lineas.append("-" * 68)
    if deficit:
        lineas.append(
            f"  Déficit habitacional CDMX ({deficit['anio']}): "
            f"{deficit['deficit']:,.0f} viviendas"
        )
        lineas.append(
            f"    · rezago acumulado: {deficit['rezago']:,.0f} viviendas"
            f"  · necesidades anuales: {deficit['necesidades']:,.0f}"
        )
        lineas.append(
            f"    · producción de crédito ({deficit['anio_produccion']}): "
            f"{deficit['produccion']:,.0f} acciones"
            f" = {deficit['cobertura']:.0%} de las necesidades anuales"
        )
        if deficit["brecha"] > 0:
            lineas.append(
                f"    · brecha ~{deficit['brecha']:,.0f} viviendas/año; cerrar el"
                f" rezago al ritmo actual tomaría ~{deficit['anios_cierre']:.1f} años"
            )
        else:
            lineas.append(
                f"    · la producción supera en ~{-deficit['brecha']:,.0f} las"
                f" necesidades anuales (pero el rezago acumulado persiste)"
            )
        lineas.append(
            "    (producción = acciones de crédito SNIIV; incluye mejoras, no solo"
            " vivienda nueva → lectura como proxy de oferta, no de obra terminada)"
        )
    if rezago is not None and not rezago.empty:
        r = rezago.sort_values("rezago_pct", ascending=False)
        top = " · ".join(
            f"{_ABREV_CORTO.get(x['alcaldia'], x['alcaldia'])} {x['rezago_pct']:.1f}%"
            for _, x in r.head(5).iterrows()
        )
        bot = r.iloc[-1]
        lineas.append(
            f"  Rezago habitacional 2020 (% de viviendas con rezago, por alcaldía):"
        )
        lineas.append(f"    más alto: {top}")
        lineas.append(
            f"    más bajo: {_ABREV_CORTO.get(bot['alcaldia'], bot['alcaldia'])}"
            f" {bot['rezago_pct']:.1f}%"
        )


def _bloque_causas(lineas: list[str], causas: pd.DataFrame) -> None:
    """Correlaciones descriptivas: vacancia, Airbnb y oferta vs precio por m²."""
    from scipy.stats import spearmanr

    df = causas.dropna(subset=["precio_m2_mediana"])
    lineas.append("")
    lineas.append(
        "POR QUÉ ES CARA LA VIVIENDA (Censo 2020 + Airbnb + portales:"
        " correlaciones descriptivas, sin causalidad)"
    )
    lineas.append("-" * 68)
    vac = causas.sort_values("vac_pct", ascending=False)
    lineas.append(
        "  Vacancia (viviendas desocupadas %): "
        + " · ".join(
            f"{_ABREV_CORTO.get(x['alcaldia'], x['alcaldia'])} {x['vac_pct']:.1f}"
            for _, x in vac.head(3).iterrows()
        )
        + " (zonas caras)"
        + " vs "
        + " · ".join(
            f"{_ABREV_CORTO.get(x['alcaldia'], x['alcaldia'])} {x['vac_pct']:.1f}"
            for _, x in vac.tail(3).iterrows()
        )
        + " (periferia)."
    )
    ut = causas.sort_values("uso_temporal_pct", ascending=False)
    lineas.append(
        "  Uso temporal (proxy de segundas residencias): "
        + " · ".join(
            f"{_ABREV_CORTO.get(x['alcaldia'], x['alcaldia'])} {x['uso_temporal_pct']:.1f}%"
            for _, x in ut.head(3).iterrows()
        )
        + " vs "
        + f"{ut.iloc[-1]['uso_temporal_pct']:.1f}% en "
        + _ABREV_CORTO.get(ut.iloc[-1]["alcaldia"], ut.iloc[-1]["alcaldia"])
        + "."
    )
    ab = causas.dropna(subset=["airbnb_x1000"]).sort_values(
        "airbnb_x1000", ascending=False
    )
    if not ab.empty:
        total = int(ab["airbnb_listings"].sum())
        lineas.append(
            "  Airbnb (listados por 1,000 viviendas): "
            + " · ".join(
                f"{_ABREV_CORTO.get(x['alcaldia'], x['alcaldia'])} {x['airbnb_x1000']:.1f}"
                for _, x in ab.head(3).iterrows()
            )
            + f" vs {ab.iloc[-1]['airbnb_x1000']:.1f} en "
            + _ABREV_CORTO.get(ab.iloc[-1]["alcaldia"], ab.iloc[-1]["alcaldia"])
            + f" · {total:,} listados en total."
        )
    for col, etiqueta in (
        ("vac_pct", "vacancia"),
        ("uso_temporal_pct", "uso temporal"),
        ("airbnb_x1000", "Airbnb"),
        ("oferta_x1000", "oferta en portales"),
    ):
        d = df.dropna(subset=[col])
        if len(d) >= 5:
            rho, pv = spearmanr(d[col], d["precio_m2_mediana"])
            lineas.append(
                f"  ρ Spearman precio/m² vs {etiqueta:<17}: {rho:+.2f}"
                f" (p={pv:.2f}, n={len(d)})"
            )
    lineas.append(
        "  Cada hipótesis evaluada + escenarios (bajar ISAI/predial, desregular"
        " uso de suelo, +10% de stock): docs/precios_causas.md"
    )


_ABREV_CORTO = {
    "Benito Juárez": "B. Juárez",
    "Miguel Hidalgo": "M. Hidalgo",
    "Cuauhtémoc": "Cuauhtémoc",
    "Iztapalapa": "Iztapalapa",
    "La Magdalena Contreras": "Magda. Contreras",
    "Cuajimalpa de Morelos": "Cuajimalpa",
    "Álvaro Obregón": "A. Obregón",
    "Venustiano Carranza": "V. Carranza",
}


def _bloque_impuestos(lineas: list[str], venta: pd.DataFrame) -> None:
    """Qué % del precio se va en impuestos: compra, tenencia y renta (2026)."""
    df = venta.sort_values("precio_mediana")
    pmin, pmed, pmax = (
        df["precio_mediana"].min(),
        df["precio_mediana"].median(),
        df["precio_mediana"].max(),
    )

    lineas.append("")
    lineas.append("IMPUESTOS SOBRE LA VIVIENDA (tarifas 2026) — ¿qué % del precio se va?")
    lineas.append("-" * 68)
    lineas.append("COMPRA (una sola vez, al escriturar)")
    lineas.append("  ISAI (art. 113 CCF-CDMX) sobre el precio de la mediana, por alcaldía:")
    for _, x in df.iterrows():
        isai = impuestos.isai(x["precio_mediana"])
        lineas.append(
            f"    {x['alcaldia']:<22} {_fmt(x['precio_mediana']):>12}"
            f"  →  ISAI {_fmt(isai):>9}  ({isai / x['precio_mediana'] * 100:>4.2f}%)"
        )
    pcts = [impuestos.isai(p) / p * 100 for p in (pmin, pmax)]
    lineas.append(
        f"  ISAI efectivo en las medianas: {pcts[0]:.1f}%–{pcts[1]:.1f}% del precio."
    )
    lineas.append("  IVA en la compraventa: 0% — venta de casa habitación exenta (LIVA art. 9° II).")
    lineas.append(
        "  ISR de la ganancia del vendedor: exento si el precio ≤ 700,000 UDIS"
        f" (~{_fmt(impuestos.TOPE_EXENCION_ISR_VENTA_UDIS * impuestos.UDI_REFERENCIA)},"
        " LISR art. 93 XIX): no pesa en las medianas."
    )
    lineas.append(
        f"  NO es impuesto — gastos de cierre de la compra (notaría + IVA de la notaría +"
        f" registro RPP + avalúo + gestoría): banda típica"
        f" {impuestos.CIERRE_MIN:.0%}–{impuestos.CIERRE_MAX:.0%} del precio; la comisión"
        " inmobiliaria (3–5%, normalmente del vendedor) es aparte."
    )
    lineas.append(
        f"  → Al comprar, el impuesto 'se come' solo el ISAI:"
        f" ~{pcts[0]:.1f}%–{pcts[1]:.1f}% del precio."
    )

    lineas.append("")
    lineas.append(
        "TENENCIA (cada año mientras se es dueño) — predial, art. 130 CCF-CDMX:"
        " la tarifa es BIMESTRAL (×6 al año); dto. 8% si se paga en enero."
    )
    lineas.append(
        f"  El valor catastral equivale a ~30–50% del precio de mercado (SAF); con 40%:"
    )
    for p in (pmin, pmed, pmax):
        pred = impuestos.predial_desde_precio(p)
        lineas.append(
            f"    precio {_fmt(p):>12}  →  predial {_fmt(pred):>7}/año"
            f"  ({pred / p * 100:.2f}% del precio)"
        )
    lineas.append(
        "  Escenario catastral 30%: {:.2f}% · 50%: {:.2f}% del precio por año.".format(
            impuestos.predial_desde_precio(pmed, ratio_catastral=0.30) / pmed * 100,
            impuestos.predial_desde_precio(pmed, ratio_catastral=0.50) / pmed * 100,
        )
    )

    lineas.append("")
    lineas.append("RENTA (cada mes)")
    lineas.append(
        "  ISR del arrendador (LISR art. 115: deduce 35% de la renta; tarifa anual"
        " art. 152):"
    )
    for r in (6_000, 10_000, 16_000, 25_000, 40_000):
        isr = impuestos.isr_renta_anual(r * 12)
        lineas.append(
            f"    {_fmt(r):>8}/mes → ISR {_fmt(isr):>7}/año"
            f" = {isr / (r * 12) * 100:.1f}% de la renta bruta"
        )
    lineas.append(
        "  IVA: 0% si se renta sin amueblar (LIVA art. 20 II); 16% si está AMUEBLADA"
        " (lo paga el inquilino encima de la renta)."
    )
    lineas.append(
        "  Predial: legalmente lo paga el dueño, pero el contrato casi siempre se lo"
        " traslada al inquilino (~0.2–0.3% del precio/año)."
    )
    lineas.append(
        "  → Por cada $100 de renta sin amueblar, ~$3.5–$9.2 van al ISR del"
        " arrendador; con muebles, +$16 de IVA los paga el inquilino."
    )


def _cruza_precio_marginacion(
    lineas: list[str], mediana: pd.DataFrame, marginacion: pd.DataFrame
) -> None:
    import numpy as np

    venta = mediana[mediana["operacion"] == "venta"].set_index("alcaldia")
    marg = marginacion.set_index("alcaldia")
    df = venta.join(marg, how="inner").dropna(
        subset=["precio_m2_mediana", "share_Alto", "share_Muy_alto"]
    )
    if df.empty:
        return
    df["margin_alta"] = df["share_Alto"] + df["share_Muy_alto"]
    corr = np.corrcoef(np.log(df["precio_m2_mediana"]), df["margin_alta"])[0, 1]
    lineas.append("")
    lineas.append(
        f"Cruce precio↔marginación (alcaldías): log($/m²) vs % marg. alta = {corr:+.2f}"
    )
    if corr < -0.6:
        lineas.append("  Relación negativa fuerte: las zonas más caras son las menos marginadas.")