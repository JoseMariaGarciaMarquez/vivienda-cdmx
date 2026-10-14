"""Dashboard interactivo (Plotly, autocontenido) del mercado de vivienda CDMX.

Genera `outputs/vivienda_cdmx_interactivo.html`: mapas coropléticos con selector
de métrica, dispersión con selector de eje X y serie de financiamientos, todo
con hover/zoom nativos. Plotly.js se incrusta inline → funciona sin internet.
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

import config
import deficit
import impuestos

import paleta

AZUL = paleta.TINTA
AZUL_SUAVE = paleta.VERDE_CLARO
GRIS = paleta.GRIS
COLORSCALE = [
    [i / (len(paleta.SECUENCIAL) - 1), c]
    for i, c in enumerate(paleta.SECUENCIAL)
]


def _normaliza(x) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", str(x).lower())
        if unicodedata.category(c) != "Mn"
    )


def _abrev(nombre: str) -> str:
    cambios = {
        "cuajimalpa de morelos": "Cuajimalpa",
        "la magdalena contreras": "Magdalena Contreras",
        "gustavo a. madero": "G. A. Madero",
        "venustiano carranza": "V. Carranza",
        "benito juárez": "B. Juárez",
        "álvaro obregón": "A. Obregón",
        "miguel hidalgo": "M. Hidalgo",
    }
    return cambios.get(str(nombre).lower(), str(nombre))


def _geojson() -> dict | None:
    ruta = config.RAIZ / "data" / "raw" / "alcaldias_cdmx.geojson"
    if not ruta.exists():
        return None
    gj = json.loads(ruta.read_text(encoding="utf-8"))
    for f in gj["features"]:
        f["properties"]["_k"] = _normaliza(f["properties"]["NOMGEO"])
    return gj


def _titulo(texto: str) -> dict:
    return dict(text=texto, x=0.5, xanchor="center",
                font=dict(size=15, color="#1a1a1a"))


def _layout(height: int = 560) -> dict:
    return dict(template="plotly_white", margin=dict(l=8, r=8, t=56, b=8),
                height=height, font=dict(family="system-ui, sans-serif"))


def _fig_mapa(geo: dict, df: pd.DataFrame, metricas: list[dict]) -> go.Figure:
    """Choropleth con dropdown: una traza por métrica (mismo geojson/locations)."""
    dm = df.copy()
    dm["_k"] = dm["alcaldia"].map(_normaliza)
    zonas = sorted(f["properties"]["_k"] for f in geo["features"])
    feats = [
        go.Choropleth(
            geojson=geo, featureidkey="properties._k", locations=zonas,
            z=[0] * len(zonas), colorscale=[[0, "#ececec"], [1, "#ececec"]],
            showscale=False, marker_line_color="white", marker_line_width=0.8,
            hoverinfo="skip", showlegend=False,
        )
    ]
    for m in metricas:
        r = dm.dropna(subset=[m["col"]])
        feats.append(
            go.Choropleth(
                geojson=geo, featureidkey="properties._k",
                locations=r["_k"].to_numpy(), z=r[m["col"]].to_numpy(),
                customdata=r[m.get("extra_col", m["col"])].to_numpy().reshape(-1, 1),
                colorscale=COLORSCALE, marker_line_color="white",
                marker_line_width=0.8,
                colorbar=dict(title=m["cb"], thickness=12, len=0.72,
                              ticksuffix=m.get("sufijo", "")),
                hovertemplate=m["hover"],
                name=m["nombre"],
                visible=False,
            )
        )
    for i, m in enumerate(metricas):
        feats[i + 1].visible = i == 0
    botones = []
    for i, m in enumerate(metricas):
        bt = feats[i + 1]
        botones.append(
            dict(
                label=m["nombre"], method="update",
                args=[
                    {"z": [bt.z], "customdata": [bt.customdata],
                     "visible": [True] + [j == i for j in range(len(metricas))],
                     "colorbar": {"title": m["cb"], "thickness": 12,
                                  "len": 0.72, "ticksuffix": m.get("sufijo", "")},
                     "hovertemplate": m["hover"]},
                    {"title": _titulo(m["titulo"])},
                ],
            )
        )
    fig = go.Figure(data=feats)
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(**_layout(), title=_titulo(metricas[0]["titulo"]))
    fig.update_layout(
        updatemenus=[dict(
            buttons=botones, direction="down", showactive=True,
            x=0.0, xanchor="left", y=1.12, yanchor="top",
            bgcolor="white", bordercolor="#cccccc",
        )]
    )
    return fig


def _fig_dispersion(df: pd.DataFrame, pares: list[tuple[str, str]]) -> go.Figure:
    """Dispersión precio/m² contra varias X, con selector de eje X."""
    dm = df.copy()
    dm["_k"] = dm["alcaldia"].map(_normaliza)
    trazas = []
    for col, nombre in pares:
        d = dm.dropna(subset=[col, "precio_m2_mediana"])
        trazas.append(
            go.Scatter(
                x=d[col].to_numpy(), y=d["precio_m2_mediana"].to_numpy(),
                mode="markers+text", text=d["alcaldia"].map(_abrev).to_numpy(),
                textposition="top center", textfont=dict(size=10, color=GRIS),
                marker=dict(size=11, color=AZUL, line=dict(width=1, color="white")),
                customdata=d[["alcaldia"]].to_numpy(),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>" + nombre +
                    ": %{x}<br>precio: $%{y:,.0f}/m²<extra></extra>"
                ),
                name=nombre, visible=False,
            )
        )
    trazas[0].visible = True
    botones = []
    for i, (col, nombre) in enumerate(pares):
        botones.append(
            dict(
                label=nombre, method="update",
                args=[
                    {"x": [trazas[i].x], "visible": [j == i for j in range(len(trazas))],
                     "hovertemplate": trazas[i].hovertemplate},
                    {"xaxis.title.text": nombre,
                     "title": _titulo(f"Precio del m² vs {nombre.lower()} (por alcaldía)")},
                ],
            )
        )
    fig = go.Figure(data=trazas)
    fig.update_layout(
        **_layout(),
        title=_titulo(f"Precio del m² vs {pares[0][1].lower()} (por alcaldía)"),
        xaxis_title=pares[0][1],
        yaxis_title="precio mediano por m² (venta, portales)",
        updatemenus=[dict(
            buttons=botones, direction="down", showactive=True,
            x=0.0, xanchor="left", y=1.12, yanchor="top",
            bgcolor="white", bordercolor="#cccccc",
        )],
    )
    return fig


def _fig_financiamientos(fin: pd.DataFrame) -> go.Figure | None:
    if fin.empty or "acciones" not in fin.columns:
        return None
    fig = go.Figure(
        go.Bar(
            x=fin["anio_calendario"].to_numpy(), y=fin["acciones"].to_numpy(),
            marker_color=paleta.CIAN,
            hovertemplate="<b>%{x}</b><br>%{y:,.0f} acciones<extra></extra>",
            name="Acciones de crédito",
        )
    )
    fig.update_layout(
        **_layout(560),
        title=_titulo("Financiamientos de vivienda en CDMX (SNIIV, anual)"),
        xaxis_title="año", yaxis_title="acciones de crédito",
    )
    return fig


def _agrega_impuestos(df: pd.DataFrame) -> pd.DataFrame:
    """Añade ISAI y predial como % del precio (columnas isai_pct/predial_pct)."""
    def pct_isai(p):
        return impuestos.isai(p) / p * 100 if pd.notna(p) and p else None

    def pct_predial(p):
        return impuestos.predial_desde_precio(p) / p * 100 if pd.notna(p) and p else None

    df = df.copy()
    df["isai_pct"] = df["precio_mediana"].map(pct_isai)
    df["predial_pct"] = df["precio_mediana"].map(pct_predial)
    return df


def _metricas_mapas() -> list[dict]:
    return [
        dict(nombre="Precio m² (venta)", col="precio_m2_mediana",
             cb="$/m²", sufijo="",
             titulo="Precio mediano por m² en venta, por alcaldía (PADIM)",
             hover="<b>%{location}</b><br>$%{z:,.0f} por m²<extra></extra>"),
        dict(nombre="ISAI al comprar", col="isai_pct",
             cb="% del precio", sufijo="%",
             titulo="ISAI al comprar (2026): % del precio mediano",
             hover="<b>%{location}</b><br>ISAI: %{z:.2f}% del precio<extra></extra>"),
        dict(nombre="Predial anual", col="predial_pct",
             cb="% del precio/año", sufijo="%",
             titulo="Predial anual (2026): % del precio mediano",
             hover="<b>%{location}</b><br>predial: %{z:.3f}% del precio al año<extra></extra>"),
        dict(nombre="Airbnb (por 1,000 viv.)", col="airbnb_x1000",
             cb="listados/1,000 viv.", extra_col="airbnb_listings", sufijo="",
             titulo="Airbnb: listados por 1,000 viviendas (Inside Airbnb)",
             hover=("<b>%{location}</b><br>%{z:.1f} listados por 1,000 viviendas"
                    "<br>%{customdata[0]:,.0f} listados<extra></extra>")),
        dict(nombre="Vivienda desocupada", col="vac_pct",
             cb="% del parque", extra_col="uso_temporal_pct", sufijo="%",
             titulo="Viviendas desocupadas (Censo 2020): % del parque",
             hover=("<b>%{location}</b><br>desocupadas: %{z:.1f}%"
                    "<br>uso temporal: %{customdata[0]:.1f}%<extra></extra>")),
        dict(nombre="Índice de oportunidad", col="indice_oportunidad",
             cb="índice 0–100", sufijo="",
             titulo="¿Dónde comprar? Índice de oportunidad (0–100)",
             hover=("<b>%{location}</b><br>oportunidad: %{z:.1f}/100"
                    "<br>precio + asequibilidad + servicios<extra></extra>")),
        dict(nombre="Índice de calidad (vivir)", col="indice_calidad",
             cb="índice 0–100", sufijo="",
             titulo="Calidad de vida sin precio (0–100)",
             hover=("<b>%{location}</b><br>calidad: %{z:.1f}/100"
                    "<br>servicios + marginación + pobreza<extra></extra>")),
        dict(nombre="Marginación alta/muy alta", col="marg_alta_pct",
             cb="% población", sufijo="%",
             titulo=("Marginación CONAPO 2020 (índice compuesto por colonia): "
                     "% de población en grado alto o muy alto"),
             hover=("<b>%{location}</b><br>%{z:.1f}% de la población en "
                    "marginación alta o muy alta (CONAPO 2020)<extra></extra>")),
        dict(nombre="Rezago habitacional", col="rezago_pct",
             cb="% de viviendas", sufijo="%",
             titulo="Rezago habitacional 2020: % de viviendas con rezago",
             hover=("<b>%{location}</b><br>%{z:.1f}% de las viviendas con rezago "
                    "habitacional (SNIIV-SEDATU, Censo 2020)<extra></extra>")),
    ]


def hacer_dashboard_interactivo(
    resumen: str, causas: pd.DataFrame, margin_alcaldia: pd.DataFrame,
    financiamientos: pd.DataFrame, indice: pd.DataFrame | None = None,
    rezago: pd.DataFrame | None = None,
) -> Path | None:
    geo = _geojson()
    if geo is None or causas.empty:
        return None
    df = causas.copy()
    df["_k"] = df["alcaldia"].map(_normaliza)
    mg = margin_alcaldia.copy()
    mg["_k"] = mg["alcaldia"].map(_normaliza)
    mg["marg_alta_pct"] = (mg["share_Alto"] + mg["share_Muy_alto"]) * 100
    df = df.merge(mg[["_k", "marg_alta_pct"]], on="_k", how="left")
    if indice is not None and not indice.empty:
        ix = indice[["alcaldia", "indice_oportunidad", "indice_calidad"]].copy()
        ix["_k"] = ix["alcaldia"].map(_normaliza)
        df = df.merge(ix[["_k", "indice_oportunidad", "indice_calidad"]],
                      on="_k", how="left")
    if rezago is not None and not rezago.empty:
        rz = rezago[["alcaldia", "rezago_pct"]].copy()
        rz["_k"] = rz["alcaldia"].map(_normaliza)
        df = df.merge(rz[["_k", "rezago_pct"]], on="_k", how="left")

    fig_mapa = _fig_mapa(geo, _agrega_impuestos(df), _metricas_mapas())
    fig_disp = _fig_dispersion(
        df,
        [("vac_pct", "viviendas desocupadas (%)"),
         ("airbnb_x1000", "listados Airbnb por 1,000 viviendas"),
         ("uso_temporal_pct", "vivienda de uso temporal (%)"),
         ("oferta_x1000", "oferta en portales por 1,000 viviendas")],
    )
    fig_fin = _fig_financiamientos(financiamientos)

    bloques = [fig_mapa, fig_disp] + ([fig_fin] if fig_fin is not None else [])
    divs = [fig.to_html(full_html=False, include_plotlyjs=("inline" if i == 0 else False),
                        config={"displayModeBar": False, "responsive": True})
            for i, fig in enumerate(bloques)]

    dfp = causas.dropna(subset=["precio_m2_mediana"])
    precio_ref = float(dfp["precio_m2_mediana"].median())
    isai_ref = impuestos.isai(precio_ref)
    predial_ref = impuestos.predial_desde_precio(precio_ref)
    ab = causas.sort_values("airbnb_x1000", ascending=False).iloc[0]
    vac_prom = causas["vac_pct"].mean()
    stats = [
        ("Precio mediano", f"${precio_ref:,.0f}/m²",
         "en venta (8 alcaldías con portales)"),
        ("ISAI al comprar", f"${isai_ref:,.0f}",
         f"{isai_ref / precio_ref * 100:.1f}% del precio, una vez"),
        ("Predial al año", f"${predial_ref:,.0f}",
         f"{predial_ref / precio_ref * 100:.2f}% del precio"),
        ("Airbnb", f"{ab['airbnb_x1000']:.1f}/1,000",
         f"máximo: {_abrev(ab['alcaldia'])}"),
        ("Desocupación", f"{vac_prom:.1f}%", "viviendas desocupadas (promedio)"),
    ]
    cifras = deficit.cifras_deficit()
    if cifras:
        stats.append(
            ("Déficit habitacional", f"{cifras['deficit']:,.0f}",
             f"viviendas ({cifras['anio']}); oferta cubre {cifras['cobertura']:.0%}/año")
        )
    if indice is not None and not indice.empty and indice["indice_oportunidad"].notna().any():
        op = indice.dropna(subset=["indice_oportunidad"]).sort_values(
            "indice_oportunidad", ascending=False
        ).iloc[0]
        stats.append(("Mejor oportunidad", f"{op['indice_oportunidad']:.0f}/100",
                      _abrev(op["alcaldia"])))
    stats_html = "".join(
        f'<div class="stat"><div class="k">{k}</div><div class="v">{v}</div>'
        f'<div class="d">{d}</div></div>'
        for k, v, d in stats
    )

    tiles = f"""
      <figure class="tile span2" style="--sc:{paleta.CIAN}">
        <figcaption><span class="t">Mapa interactivo</span>
          <span class="n">Elige la métrica con el selector; pasa el cursor, haz zoom y
          arrastra. Las 8 alcaldías grises no tienen muestra suficiente en PADIM
          (precio/ISAI/predial); las sociodemográficas cubren las 16.</span></figcaption>
        {divs[0]}
      </figure>
      <figure class="tile stats" style="--sc:{paleta.VERDE}">
        <figcaption><span class="t">Cifras clave</span>
          <span class="n">Referencias de la CDMX (2026).</span></figcaption>
        <div class="stats-grid">{stats_html}</div>
      </figure>
      <figure class="tile span2" style="--sc:{paleta.VERDE_OSCURO}">
        <figcaption><span class="t">Hipótesis del precio alto</span>
          <span class="n">Cambia el eje X para comparar el precio del m² con
          desocupación, Airbnb, uso temporal u oferta. Descriptivo, sin causalidad.</span></figcaption>
        {divs[1]}
      </figure>"""
    if fig_fin is not None:
        tiles += f"""
      <figure class="tile" style="--sc:{paleta.TINTA}">
        <figcaption><span class="t">Financiamientos</span>
          <span class="n">Crédito de vivienda anual, todas las ONAs (SNIIV).</span></figcaption>
        {divs[2]}
      </figure>"""
    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vivienda CDMX · Monitor interactivo</title>
<style>
  :root {{
    --tinta: {paleta.TINTA}; --tinta2: {paleta.VERDE_OSCURO};
    --verde: {paleta.VERDE}; --linea: {paleta.LINEA}; --gris: {paleta.GRIS};
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: {paleta.FONDO}; color: var(--tinta);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    line-height: 1.5; -webkit-font-smoothing: antialiased; }}
  .strip {{ height: 5px; background: linear-gradient(90deg,
    {paleta.CIAN}, {paleta.NIEBLA}, {paleta.VERDE_CLARO},
    {paleta.VERDE}, {paleta.VERDE_OSCURO}, {paleta.TINTA});
    position: sticky; top: 0; z-index: 20; }}
  header {{ position: sticky; top: 5px; z-index: 19; background: {paleta.NIEBLA}e6;
    backdrop-filter: blur(8px); border-bottom: 1px solid var(--linea); }}
  .bar {{ max-width: 1180px; margin: 0 auto; padding: 10px 20px;
    display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }}
  .bar h1 {{ font-family: Georgia, serif; font-weight: 400; font-size: 20px;
    margin: 0; white-space: nowrap; }}
  .bar .kick {{ font-size: 11px; text-transform: uppercase; letter-spacing: .16em;
    color: var(--tinta2); font-weight: 700; }}
  .bar .spacer {{ flex: 1 1 auto; }}
  .btn {{ background: var(--tinta); color: #fff; text-decoration: none;
    padding: 8px 14px; border-radius: 999px; font-size: 13px; font-weight: 600;
    white-space: nowrap; }}
  .btn:hover {{ background: var(--tinta2); }}
  main {{ max-width: 1180px; margin: 0 auto; padding: 14px 20px 50px; }}
  section {{ margin-bottom: 22px; scroll-margin-top: 100px; }}
  section h2 {{ margin: 0 0 10px; font-size: 13px; font-weight: 700;
    text-transform: uppercase; letter-spacing: .12em; color: var(--tinta2);
    display: flex; align-items: center; gap: 10px; }}
  section h2::after {{ content: ""; flex: 1; height: 1px; background: var(--linea); }}
  .resumen {{ background: linear-gradient(180deg, {paleta.NIEBLA}, #fff 60%);
    border: 1px solid var(--linea); border-left: 4px solid var(--tinta);
    border-radius: 14px; padding: 12px 14px; column-count: 3; column-gap: 24px;
    white-space: pre-wrap; max-height: 280px; overflow: auto;
    font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 11.5px;
    line-height: 1.45; }}
  .card {{ margin: 0; background: #fff; border: 1px solid var(--linea);
    border-radius: 14px; padding: 12px; }}
  .card figcaption {{ font-size: 12px; color: var(--gris); margin-top: 8px; }}
  .bento {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
    align-items: stretch; }}
  .tile {{ margin: 0; background: #fff; border: 1px solid var(--linea);
    border-top: 3px solid var(--sc, var(--linea)); border-radius: 14px;
    padding: 12px; min-width: 0; }}
  .tile.span2 {{ grid-column: span 2; }}
  .tile figcaption {{ display: flex; flex-direction: column; gap: 2px;
    margin-bottom: 8px; }}
  .tile .t {{ font-size: 13px; font-weight: 650; }}
  .tile .n {{ font-size: 11px; color: var(--gris); line-height: 1.35; }}
  .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
  .stat {{ border: 1px solid var(--linea); border-radius: 10px; padding: 10px 12px; }}
  .stat .k {{ font-size: 10.5px; font-weight: 700; text-transform: uppercase;
    letter-spacing: .08em; color: var(--tinta2); }}
  .stat .v {{ font-size: 19px; font-weight: 700; margin: 2px 0; }}
  .stat .d {{ font-size: 11px; color: var(--gris); line-height: 1.3; }}
  @media (max-width: 900px) {{
    .bento {{ grid-template-columns: 1fr; }}
    .tile.span2 {{ grid-column: span 1; }}
  }}
  @media (max-width: 680px) {{
    .resumen {{ column-count: 1; }}
    .bar h1 {{ font-size: 17px; }}
    .stats-grid {{ grid-template-columns: 1fr; }}
  }}
</style></head>
<body>
<div class="strip"></div>
<header>
  <div class="bar">
    <div>
      <div class="kick">Monitor interactivo · Ciudad de México</div>
      <h1>Explora la vivienda de la CDMX</h1>
    </div>
    <div class="spacer"></div>
    <a class="btn" href="vivienda_cdmx.html">← Versión estática</a>
  </div>
</header>
<main>
  <section>
    <h2>Resumen</h2>
    <div class="resumen">{resumen}</div>
  </section>
  <section>
    <h2>Tablero</h2>
    <div class="bento">{tiles}
    </div>
  </section>
</main></body></html>"""
    out = config.OUT / "vivienda_cdmx_interactivo.html"
    out.write_text(html, encoding="utf-8")
    return out
