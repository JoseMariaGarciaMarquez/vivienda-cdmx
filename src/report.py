"""Gráficas del mercado de la vivienda (matplotlib) y dashboard HTML autocontenido."""
from __future__ import annotations

import base64
import unicodedata
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.transforms import Bbox

import config
import impuestos
from build import _alcaldia

import paleta

CONTRASTE = paleta.CIAN
AZUL = paleta.TINTA
AZUL_SUAVE = paleta.VERDE_CLARO
VERDE = paleta.VERDE
GRIS = paleta.GRIS
NARANJA = paleta.CIAN
COLROJO = paleta.CIAN

plt.rcParams.update({
    "figure.max_open_warning": 0,
    "font.size": 10,
    "axes.edgecolor": "#cccccc",
    "axes.labelcolor": GRIS,
    "xtick.color": GRIS,
    "ytick.color": GRIS,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
})


def _textos_fig(fig) -> list:
    """(grupo, texto, bbox) de todos los textos visibles de la figura (píxeles)."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    items = []

    def meter(t, grupo: str) -> None:
        try:
            if not t.get_visible() or not t.get_text().strip():
                return
        except Exception:
            return
        e = t.get_window_extent(renderer=r)
        if e.width >= 1 and e.height >= 1:
            items.append((grupo, " ".join(t.get_text().split()), e))

    for t in fig.texts:
        meter(t, "suptítulo")
    for ax in fig.axes:
        meter(ax.title, "título")
        if ax.axison:
            if ax.get_xlabel():
                meter(ax.xaxis.label, "eje")
            if ax.get_ylabel():
                meter(ax.yaxis.label, "eje")
            x0, x1 = ax.get_xlim()
            y0, y1 = ax.get_ylim()
            ex = max(abs(x1 - x0), 1e-9) * 1e-6
            ey = max(abs(y1 - y0), 1e-9) * 1e-6
            for t in ax.xaxis.get_major_ticks():
                if x0 - ex <= t.get_loc() <= x1 + ex:
                    meter(t.label1, "marcas")
                    meter(t.label2, "marcas")
            for t in ax.yaxis.get_major_ticks():
                if y0 - ey <= t.get_loc() <= y1 + ey:
                    meter(t.label1, "marcas")
                    meter(t.label2, "marcas")
        for t in ax.texts:
            meter(t, "etiqueta")
        leg = ax.get_legend()
        if leg is not None:
            for t in leg.get_texts():
                meter(t, "leyenda")
    return items


def _cierra(fig, path: Path) -> None:
    """Guarda la figura, reporta textos empalmados/fuera del lienzo y la cierra."""
    W, H = fig.canvas.get_width_height()
    items = _textos_fig(fig)
    for i, (gi, ti, ei) in enumerate(items):
        for gj, tj, ej in items[i + 1:]:
            inter = Bbox.intersection(ei, ej)
            if inter is None:
                continue
            a = inter.width * inter.height
            if a > 50:
                print(
                    f"  [texto] {path.name}: empalme {a:,.0f}px² "
                    f"{ti!r} ({gi}) × {tj!r} ({gj})"
                )
    for g, t, e in items:
        if e.x0 < -1 or e.y0 < -1 or e.x1 > W + 1 or e.y1 > H + 1:
            print(
                f"  [texto] {path.name}: fuera del lienzo {t!r} ({g}) "
                f"bbox=({e.x0:.0f},{e.y0:.0f},{e.x1:.0f},{e.y1:.0f}) fig={W}x{H}"
            )
    fig.savefig(path, dpi=140)
    plt.close(fig)


_ESPIRAL = tuple(
    (float(r * np.cos(np.deg2rad(a))), float(r * np.sin(np.deg2rad(a))))
    for r in np.arange(6.0, 37.0, 6.0)
    for a in range(0, 360, 30)
)
_OFF_PUNTO = ((6, 6), (6, -7), (-6, 6), (-6, -7)) + _ESPIRAL


def _recolorea_mapa(fig, textos) -> None:
    """Ajusta color y trazo de las etiquetas al brillo del fondo bajo cada una."""
    for t in textos:
        t.set_visible(False)
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())
    Hb = buf.shape[0]
    r = fig.canvas.get_renderer()
    for t in textos:
        t.set_visible(True)
        e = t.get_window_extent(renderer=r)
        cx = int(min(max((e.x0 + e.x1) / 2, 0), buf.shape[1] - 1))
        cy = int(min(max(Hb - (e.y0 + e.y1) / 2, 0), Hb - 1))
        px = buf[cy, cx, :3].astype(float) / 255.0
        lum = 0.2126 * px[0] + 0.7152 * px[1] + 0.0722 * px[2]
        if lum < 0.55:
            t.set_color("#ffffff")
            t.set_path_effects([pe.withStroke(linewidth=2.2, foreground="#16324a")])
        else:
            t.set_color(AZUL)
            t.set_path_effects([pe.withStroke(linewidth=2.2, foreground="#ffffff")])


class _Colocador:
    """Escribe etiquetas en la primera posición libre (sin empalmar)."""

    def __init__(self, fig):
        self._fig = fig
        self._r = fig.canvas.get_renderer()
        self._bbs = [e for _, _, e in _textos_fig(fig)]

    def _choca(self, e) -> bool:
        W, H = self._fig.canvas.get_width_height()
        if e.x0 < 0 or e.y0 < 0 or e.x1 > W or e.y1 > H:
            return True
        for b in self._bbs:
            inter = Bbox.intersection(e, b)
            if inter is not None and inter.width * inter.height > 30:
                return True
        return False

    def poner(self, ax, x, y, texto, *, fontsize=7, color=AZUL, stroke="#ffffff",
              offsets=None):
        if offsets is None:
            offsets = ((0, 0),) + _ESPIRAL
        fuente = [pe.withStroke(linewidth=2.2, foreground=stroke)] if stroke else None
        t = None
        for dx, dy in offsets:
            if t is not None:
                t.remove()
            t = ax.annotate(
                texto, (x, y), xytext=(dx, dy), textcoords="offset points",
                ha="center", va="center", fontsize=fontsize, color=color,
                linespacing=1.15, zorder=6, path_effects=fuente,
            )
            e = t.get_window_extent(renderer=self._r)
            if e.width >= 1 and e.height >= 1 and not self._choca(e):
                self._bbs.append(e)
                return t
        self._bbs.append(t.get_window_extent(renderer=self._r))
        return t


def grafica_m2_alcaldias(mediana: pd.DataFrame, path: Path) -> str:
    venta = mediana[mediana["operacion"] == "venta"].sort_values("precio_m2_mediana")
    if venta.empty:
        return "Sin datos de portales."
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=140)
    ax.barh(venta["alcaldia"], venta["precio_m2_mediana"], color=AZUL_SUAVE, zorder=2)
    for i, x in enumerate(venta["precio_m2_mediana"]):
        ax.text(x * 1.01, i, f"${x:,.0f}", va="center", fontsize=8, color=GRIS)
    ax.set_xlabel("Pesos por m² (mediana, venta)")
    ax.set_title("Precio mediano por m² en venta, por alcaldía de la CDMX")
    ax.set_xlim(0, venta["precio_m2_mediana"].max() * 1.25)
    ax.grid(axis="x", alpha=0.2, zorder=0)
    fig.tight_layout()
    _cierra(fig, path)
    return ""


def grafica_box_m2(df: pd.DataFrame, path: Path) -> str:
    df = df[df["price_semantics"] == "venta"].copy()
    if df.empty or "m2" not in df.columns:
        return "Sin suficientes datos de portales."
    df["alcaldia"] = df.apply(_alcaldia, axis=1)
    df = df.dropna(subset=["alcaldia"])
    df["precio_m2"] = df["precio_mxn"] / df["m2"].where(df["m2"] > 0)
    df = df[(df["m2"].between(20, 600)) & (df["precio_m2"].between(1000, 600000))]
    if df.empty:
        return "Sin datos suficientes tras filtrar a banda residencial."
    df = df[df["precio_m2"].between(df["precio_m2"].quantile(0.03), df["precio_m2"].quantile(0.97))]
    orden = df.groupby("alcaldia")["precio_m2"].median().sort_values()
    filas: list[pd.DataFrame] = []
    for al in orden.index:
        x = df[df["alcaldia"] == al].sort_values("precio_m2").head(300)
        filas.append(x)
    fig, ax = plt.subplots(figsize=(10, 5.4), dpi=140)
    bp = ax.boxplot(
        [f["precio_m2"].dropna() for f in filas],
        labels=list(orden.index),
        vert=False,
        patch_artist=True,
        medianprops=dict(color=COLROJO, lw=1.6),
        flierprops=dict(marker=".", markersize=2, alpha=0.3),
    )
    for p in bp["boxes"]:
        p.set(facecolor=AZUL_SUAVE, alpha=0.7)
    ax.set_xlabel("Pesos por m² (venta, ±97% para quitar valores extremos)")
    ax.set_title("Distribución del precio por m² en venta, por alcaldía")
    fig.tight_layout()
    _cierra(fig, path)
    return ""


def grafica_financiamientos(anual: pd.DataFrame, path: Path) -> str:
    if anual.empty:
        return "Sin datos de financiamientos (SNIIV)."
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=140)
    ax.bar(anual["anio_calendario"], anual["acciones"], color=NARANJA, alpha=0.85, zorder=2)
    ax.set_ylabel("Acciones de crédito")
    ax.set_title("Financiamientos de vivienda en CDMX (todas las ONAs, anual)")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    _cierra(fig, path)
    return ""


def grafica_estres_oferta(
    anual: pd.DataFrame, cifras: dict, path: Path
) -> str:
    """Producción anual de crédito vs. necesidades anuales (estrés de la oferta)."""
    if anual.empty:
        return "Sin datos de financiamientos (SNIIV)."
    a = anual.sort_values("anio_calendario")
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=140)
    ax.bar(a["anio_calendario"], a["acciones"], color=paleta.VERDE, alpha=0.85,
           zorder=2, label="Producción (acciones de crédito)")
    if cifras:
        ax.axhline(cifras["necesidades"], color=paleta.TINTA, ls="--", lw=1.6,
                   zorder=3, label="Necesidades anuales de vivienda")
        ax.annotate(
            f"necesidades: {cifras['necesidades']:,.0f}/año",
            xy=(a["anio_calendario"].iloc[0], cifras["necesidades"]),
            xytext=(0, 5), textcoords="offset points",
            fontsize=8.5, color=paleta.TINTA, fontweight="bold",
        )
    ax.set_ylabel("Acciones de crédito / viviendas")
    ax.set_title("Estrés de la oferta: producción de vivienda vs. necesidades anuales")
    ax.grid(axis="y", alpha=0.2)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    fig.tight_layout()
    _cierra(fig, path)
    return ""


def grafica_mapa_rezago(rezago: pd.DataFrame, path: Path) -> str:
    """Rezago habitacional 2020 (% de viviendas con rezago) por alcaldía (mapa)."""
    if rezago.empty:
        return "Sin datos de rezago habitacional (SNIIV 2020)."
    df = rezago.copy()
    df["valor"] = pd.to_numeric(df["rezago_pct"], errors="coerce")
    df["etiqueta"] = df["valor"].map(lambda v: f"{v:.1f}%")
    return _mapa_alcaldias(
        df[["alcaldia", "valor", "etiqueta"]], path,
        titulo="Rezago habitacional 2020: % de viviendas con rezago, por alcaldía",
        eje="% de viviendas con rezago habitacional (SNIIV-SEDATU, Censo 2020)",
    )


def grafica_ratio(ratios: pd.DataFrame, path: Path) -> str:
    if ratios.empty:
        return "Sin datos de renta para el ratio."
    r = ratios.sort_values("meses_de_renta")
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=140)
    ax.bar(r["alcaldia"], r["meses_de_renta"], color=VERDE, alpha=0.8, zorder=2)
    ax.axhline(180, color=GRIS, ls="--", lw=1)
    ax.text(len(r) - 0.5, 183, "15 años de renta", fontsize=8, color=GRIS, ha="right")
    ax.set_ylabel("Meses de renta para pagar el precio de venta")
    ax.set_title("Ratio precio/renta por alcaldía (mediana)")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    _cierra(fig, path)
    return ""


def grafica_marginacion(margin_alcaldia: pd.DataFrame, path: Path) -> str:
    """Share de población en marginación Alta y Muy alta, por alcaldía."""
    if margin_alcaldia.empty:
        return "Sin datos de CONAPO."
    df = margin_alcaldia.copy()
    df["share_alta_muy_alta"] = df["share_Alto"] + df["share_Muy_alto"]
    df = df.sort_values("share_alta_muy_alta")
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=140)
    ax.barh(df["alcaldia"], df["share_alta_muy_alta"] * 100, color="#e8a2a5", zorder=2)
    for i, v in enumerate(df["share_alta_muy_alta"] * 100):
        ax.text(v + 0.3, i, f"{v:.1f}%", va="center", fontsize=8, color=GRIS)
    ax.set_xlabel("% de la población en marginación alta o muy alta (CONAPO 2020)")
    ax.set_title("Marginación por alcaldía de la CDMX")
    ax.set_xlim(0, df["share_alta_muy_alta"].max() * 100 * 1.30)
    ax.grid(axis="x", alpha=0.2, zorder=0)
    fig.tight_layout()
    _cierra(fig, path)
    return ""


def grafica_shf(shf_cdmx: pd.DataFrame, path: Path) -> str:
    """Serie del índice SHF por alcaldía (2017-hoy) cuando hay CSV."""
    if shf_cdmx.empty:
        if path.exists():
            path.unlink()
        return "Sin índice SHF (descarga manual)."
    df = shf_cdmx.copy()
    if "trimestre" in df.columns:
        df["fecha"] = pd.to_datetime(
            df["anio"].astype(int).astype(str) + "Q" + df["trimestre"].replace({"Q": "", "-1": ""}).astype(int).astype(str)
        )
    else:
        df["fecha"] = pd.to_datetime(df["anio"].astype(int), format="%Y")
    piv = df.pivot(index="fecha", columns="alcaldia", values="indice").sort_index()
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=140)
    for al in piv.columns:
        ax.plot(piv.index, piv[al], lw=1.5, label=str(al))
    ax.set_ylabel("Índice SHF (base 100 = 2017)")
    ax.set_title("Índice de precios de la vivienda (SHF), por alcaldía")
    ax.grid(alpha=0.2)
    ax.legend(fontsize=8, ncol=2, loc="upper left")
    fig.tight_layout()
    _cierra(fig, path)
    return ""


def grafica_censo(censo: pd.DataFrame, path: Path) -> str:
    """Estructura etaria y condiciones de vivienda del Censo 2020 por alcaldía."""
    if censo.empty:
        return "Sin datos del Censo 2020."
    df = censo.copy()
    df["menor15"] = df["P_0A2"] + df["P_3A5"] + df["P_6A11"] + df["P_12A14"]
    df["mayor60"] = df["P_60YMAS"]
    df["15a59"] = (df["POBTOT"] - df["menor15"] - df["mayor60"]).clip(lower=0)
    for c in ["menor15", "15a59", "mayor60"]:
        df[c + "_pct"] = df[c] / df["POBTOT"] * 100
    df = df.sort_values("mayor60_pct")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 6), dpi=140)
    labels = [a.replace(" de Morelos", "") for a in df["alcaldia"]]
    ax1.barh(labels, df["mayor60_pct"], color=AZUL, label="60+")
    ax1.barh(labels, df["15a59_pct"], left=df["mayor60_pct"], color=AZUL_SUAVE, label="15-59")
    ax1.barh(labels, df["menor15_pct"],
             left=df["mayor60_pct"] + df["15a59_pct"], color=GRIS, label="<15")
    ax1.set_xlabel("% de la población")
    ax1.set_title("Estructura etaria (Censo 2020)")
    ax1.grid(alpha=0.2)
    ax1.legend(fontsize=8, loc="lower right")

    orden = df.sort_values("hacinamiento_prom").set_index("alcaldia")
    y = np.arange(len(orden))
    w = 0.27
    ax2.barh(y + w, orden["hacinamiento_prom"], height=w, color=COLROJO,
             label="hacinamiento (pers./cuarto)")
    ax2.barh(y, np.minimum(orden["vph_sin_agua_pct"], 8), height=w, color=AZUL,
             label="% viviendas sin agua entubada")
    ax2.barh(y - w, orden["vph_piso_tierra_pct"], height=w, color=GRIS,
             label="% viviendas con piso de tierra")
    ax2.set_yticks(y, [a.replace(" de Morelos", "") for a in orden.index], fontsize=7)
    ax2.set_xlabel("% / promedio")
    ax2.set_title("Hacinamiento y carencias (Censo 2020)")
    ax2.grid(alpha=0.2)
    ax2.legend(fontsize=8, loc="lower right")

    fig.tight_layout()
    _cierra(fig, path)
    return ""


def grafica_asequibilidad(aseq: pd.DataFrame, path: Path) -> str:
    """Años de ingreso del hogar mediano (CDMX) para comprar la mediana, por alcaldía."""
    if aseq.empty:
        return "Sin datos de asequibilidad (ENIGH)."
    df = aseq.sort_values("anios_ingreso")
    fig, ax1 = plt.subplots(figsize=(9, 5.2), dpi=140)
    ax1.barh([a.replace(" de Morelos", "") for a in df["alcaldia"]],
             df["anios_ingreso"], color=AZUL)
    for y, (_, x) in enumerate(df.iterrows()):
        ax1.annotate(
            f"{x['share_hogares_alcanza_30pct']*100:.0f}%",
            (x["anios_ingreso"], y), xytext=(4, 0), va="center",
            fontsize=8, color=GRIS, textcoords="offset points",
        )
    ax1.set_xlabel(
        "años de ingreso anual del hogar (mediana CDMX) para comprar la mediana\n"
        "etiqueta al final de la barra: % de hogares que cubren la cuota (regla 30%)"
    )
    ax1.set_title("Asequibilidad de la vivienda en venta (ENIGH 2022 → pesos 2026)")
    ax1.grid(alpha=0.2)
    fig.tight_layout()
    _cierra(fig, path)
    return ""


def _norm_nombre(x) -> str:
    """Clave sin acentos ni mayúsculas para unir portales ↔ geometría."""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(x).lower())
        if unicodedata.category(c) != "Mn"
    )


_ABREV = {
    "cuajimalpa de morelos": "Cuajimalpa",
    "la magdalena contreras": "Magdalena Contreras",
    "gustavo a. madero": "G. A. Madero",
    "venustiano carranza": "V. Carranza",
    "benito juárez": "B. Juárez",
    "álvaro obregón": "A. Obregón",
    "miguel hidalgo": "M. Hidalgo",
    "iztapalapa": "Iztapalapa",
}


def _mapa_alcaldias(
    df: pd.DataFrame, path: Path, *, titulo: str, eje: str
) -> str:
    """Mapa coroplético de la CDMX por alcaldía.

    `df` debe traer: alcaldia, valor (numérico), etiqueta (texto a anotar).
    Las alcaldías sin dato quedan en gris con la leyenda "sin datos".
    """
    import geopandas as gpd

    geo = config.RAIZ / "data" / "raw" / "alcaldias_cdmx.geojson"
    if not geo.exists():
        return "Falta data/raw/alcaldias_cdmx.geojson (pkg 'alcaldias', datos.cdmx.gob.mx)."
    g = gpd.read_file(geo)
    g["_k"] = g["NOMGEO"].map(_norm_nombre)
    df = df.copy()
    df["_k"] = df["alcaldia"].map(_norm_nombre)
    g = g.merge(df[["_k", "valor", "etiqueta"]], on="_k", how="left")
    if g["valor"].notna().sum() == 0:
        return "Sin datos por alcaldía para el mapa."
    vmin, vmax = float(g["valor"].min()), float(g["valor"].max())
    if vmax - vmin < 1e-9:
        vmax = vmin + 1e-9
    cmap = LinearSegmentedColormap.from_list("turbine", paleta.SECUENCIAL)
    norm = Normalize(vmin, vmax)

    fig, ax = plt.subplots(figsize=(7.6, 6.6), dpi=140)
    g.plot(
        column="valor", cmap=cmap, vmin=vmin, vmax=vmax,
        edgecolor="white", linewidth=0.9, ax=ax, legend=False,
        missing_kwds={"color": paleta.SIN_DATO, "edgecolor": "white", "linewidth": 0.9},
    )
    sm = ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cb = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.04, pad=0.03)
    cb.set_label(eje, fontsize=9)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=8, colors=GRIS)
    ax.set_aspect(1.0 / np.cos(np.deg2rad(19.43)))  # corrección ~19.4°N
    ax.set_axis_off()
    fig.suptitle(titulo, fontsize=11.5, fontweight="bold", y=0.975)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    pos = _Colocador(fig)
    for _, x in g.assign(_area=g.geometry.area).sort_values("_area").iterrows():
        pt = x.geometry.representative_point()
        nombre = _ABREV.get(str(x["NOMGEO"]).lower(), str(x["NOMGEO"]))
        if pd.notna(x["valor"]):
            oscuro = norm(float(x["valor"])) > 0.55
            texto = f"{nombre}\n{x['etiqueta']}"
            color = "#ffffff" if oscuro else AZUL
        else:
            texto = f"{nombre}\nsin datos"
            color = "#8a8a8a"
        pos.poner(ax, pt.x, pt.y, texto, fontsize=7, color=color)
    _recolorea_mapa(fig, list(ax.texts))
    _cierra(fig, path)
    return ""


def grafica_mapa_isai(mediana: pd.DataFrame, path: Path) -> str:
    """ISAI al comprar: % del precio mediano por alcaldía (mapa coroplético)."""
    venta = mediana[mediana["operacion"] == "venta"]
    if venta.empty:
        return "Sin datos de portales."
    filas = []
    for _, x in venta.iterrows():
        isai = impuestos.isai(x["precio_mediana"])
        pct = isai / x["precio_mediana"] * 100
        filas.append({
            "alcaldia": x["alcaldia"],
            "valor": pct,
            "etiqueta": f"{pct:.1f}%  ·  ${isai / 1000:,.0f}k",
        })
    return _mapa_alcaldias(
        pd.DataFrame(filas), path,
        titulo="ISAI al comprar la vivienda (2026): % del precio mediano por alcaldía",
        eje="% del precio (ISAI, art. 113 del Código Fiscal de la CDMX)",
    )


def grafica_mapa_predial(mediana: pd.DataFrame, path: Path) -> str:
    """Predial anual: % del precio mediano por alcaldía (mapa coroplético)."""
    venta = mediana[mediana["operacion"] == "venta"]
    if venta.empty:
        return "Sin datos de portales."
    filas = []
    for _, x in venta.iterrows():
        pred = impuestos.predial_desde_precio(x["precio_mediana"])
        pct = pred / x["precio_mediana"] * 100
        filas.append({
            "alcaldia": x["alcaldia"],
            "valor": pct,
            "etiqueta": f"{pct:.2f}%  ·  ${pred / 1000:,.1f}k/año",
        })
    return _mapa_alcaldias(
        pd.DataFrame(filas), path,
        titulo="Predial anual (2026): % del precio mediano por alcaldía",
        eje="% del precio (art. 130 CCF-CDMX; catastral ≈ 40% del precio, pago en enero)",
    )


def grafica_mapa_marginacion(margin_alcaldia: pd.DataFrame, path: Path) -> str:
    """Marginación CONAPO 2020 (% alta o muy alta) por alcaldía (mapa)."""
    if margin_alcaldia.empty:
        return "Sin datos de marginación (CONAPO 2020)."
    df = margin_alcaldia.copy()
    df["valor"] = (df["share_Alto"] + df["share_Muy_alto"]) * 100
    df["etiqueta"] = df["valor"].map(lambda v: f"{v:.1f}%")
    return _mapa_alcaldias(
        df[["alcaldia", "valor", "etiqueta"]], path,
        titulo="Marginación (CONAPO 2020): % de población en alto o muy alto",
        eje="% de la población (índice de marginación por colonia, CONAPO 2020)",
    )


def grafica_mapa_precio(mediana: pd.DataFrame, path: Path) -> str:
    """Precio mediano por m² en venta por alcaldía (mapa)."""
    venta = mediana[mediana["operacion"] == "venta"].dropna(subset=["precio_m2_mediana"])
    if venta.empty:
        return "Sin datos de portales."
    df = venta.copy()
    df["valor"] = df["precio_m2_mediana"]
    df["etiqueta"] = df["valor"].map(lambda v: f"${v:,.0f}/m²")
    return _mapa_alcaldias(
        df[["alcaldia", "valor", "etiqueta"]], path,
        titulo="Precio mediano por m² en venta, por alcaldía (portales PADIM)",
        eje="$ por m² (mediana del inventario en oferta)",
    )


def grafica_mapa_indice(
    indice: pd.DataFrame, path: Path, *, col: str, titulo: str, eje: str
) -> str:
    """Mapa coroplético de un índice compuesto (0–100) por alcaldía."""
    df = indice.dropna(subset=[col]).copy()
    if df.empty:
        return "Sin índice calculado (faltan datos)."
    df["valor"] = pd.to_numeric(df[col], errors="coerce")
    df["etiqueta"] = df["valor"].map(lambda v: f"{v:.1f}")
    return _mapa_alcaldias(
        df[["alcaldia", "valor", "etiqueta"]], path, titulo=titulo, eje=eje
    )


def grafica_mapa_airbnb(causas: pd.DataFrame, path: Path) -> str:
    """Airbnb por alcaldía: listados por 1,000 viviendas (mapa coroplético)."""
    df = causas.dropna(subset=["airbnb_x1000"])
    if df.empty:
        return "Sin datos de Airbnb (Inside Airbnb, data.insideairbnb.com)."
    filas = [
        {
            "alcaldia": x["alcaldia"],
            "valor": x["airbnb_x1000"],
            "etiqueta": f"{x['airbnb_x1000']:.1f} · {int(x['airbnb_listings']):,} ab",
        }
        for _, x in df.iterrows()
    ]
    return _mapa_alcaldias(
        pd.DataFrame(filas), path,
        titulo="Airbnb: listados por cada 1,000 viviendas por alcaldía (Inside Airbnb)",
        eje="listados por 1,000 viviendas (parque Censo 2020)",
    )


def grafica_causas(causas: pd.DataFrame, path: Path) -> str:
    """Dispersión precio/m² vs vacancia y vs Airbnb (Spearman por alcaldía)."""
    from scipy.stats import spearmanr

    df = causas.dropna(subset=["precio_m2_mediana"])
    if len(df) < 5:
        return "Sin suficientes alcaldías con precio de portales."
    pares = [
        ("vac_pct", "viviendas desocupadas (%), Censo 2020"),
        ("airbnb_x1000", "listados Airbnb por 1,000 viviendas"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.4), dpi=140)
    for eje_x, (col, xlabel) in zip(axes, pares):
        d = df.dropna(subset=[col])
        rho, pval = spearmanr(d[col], d["precio_m2_mediana"])
        eje_x.scatter(d[col], d["precio_m2_mediana"], s=70, color=AZUL,
                      zorder=3, edgecolor="white", linewidth=0.8)
        eje_x.set_xlabel(xlabel)
        eje_x.set_ylabel("precio mediano por m² (venta, portales)")
        eje_x.set_title(f"ρ Spearman = {rho:+.2f} (p = {pval:.2f}, n = {len(d)})")
        eje_x.grid(alpha=0.2)
    fig.suptitle(
        "Hipótesis de zonas caras: vacancia y Airbnb por alcaldía (descriptivo, sin causalidad)",
        fontsize=11.5, fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    pos = _Colocador(fig)
    for eje_x, (col, _xl) in zip(axes, pares):
        d = df.dropna(subset=[col])
        for _, x in d.iterrows():
            nombre = _ABREV.get(str(x["alcaldia"]).lower(), str(x["alcaldia"]))
            pos.poner(eje_x, x[col], x["precio_m2_mediana"], nombre,
                      fontsize=7, color=GRIS, stroke="#f7f9fc",
                      offsets=_OFF_PUNTO)
    _cierra(fig, path)
    return ""


def _png_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _slug(texto: str) -> str:
    import re
    import unicodedata

    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return "sec-" + re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")


_COLOR_SEC = {
    "Precios y oferta": paleta.TINTA,
    "Asequibilidad y sociedad": paleta.VERDE_OSCURO,
    "Impuestos": paleta.CIAN,
    "¿Por qué es caro?": paleta.VERDE,
    "¿Dónde comprar?": paleta.VERDE_OSCURO,
    "Déficit y oferta": paleta.VERDE,
    "Crédito y financiamiento": paleta.TINTA,
}

_FEATURE = {
    "causas_dispersion.png", "box_m2.png", "censo2020.png",
    "financiamientos.png",
}


def hacer_dashboard(graficas: list[dict[str, str]], resumen: str) -> Path:
    presentes = []
    for g in graficas:
        if not (config.CHARTS / g["archivo"]).exists():
            print(f"  [report] sin gráfica, omitida: {g['archivo']}")
            continue
        presentes.append(g)

    orden_sec = list(dict.fromkeys(g.get("seccion", "General") for g in presentes))
    vistos: set[str] = set()
    tiles = []
    for g in presentes:
        sec = g.get("seccion", "General")
        ancla = ""
        if sec not in vistos:
            vistos.add(sec)
            ancla = f' id="{_slug(sec)}"'
        img = _png_b64(config.CHARTS / g["archivo"])
        color = _COLOR_SEC.get(sec, paleta.GRIS)
        ancho = " wide" if g["archivo"] in _FEATURE else ""
        tiles.append(f"""
      <figure class="tile{ancho}"{ancla} style="--sc:{color}">
        <span class="badge" style="color:{color}; background:{color}1f">
          <i style="background:{color}"></i>{sec}</span>
        <img src="data:image/png;base64,{img}" alt="{g['titulo']}" loading="lazy"/>
        <figcaption>
          <span class="t">{g['titulo']}</span>
          <span class="n">{g.get('nota', '')}</span>
        </figcaption>
      </figure>""")

    nav = "".join(
        f'<a href="#{_slug(t)}" style="border-color:{_COLOR_SEC.get(t, paleta.GRIS)}' 
        f'66"><i style="background:{_COLOR_SEC.get(t, paleta.GRIS)}"></i>{t}</a>'
        for t in orden_sec
    )

    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vivienda CDMX · Monitor</title>
<style>
  :root {{
    --tinta: {paleta.TINTA}; --tinta2: {paleta.VERDE_OSCURO};
    --verde: {paleta.VERDE}; --cian: {paleta.CIAN};
    --linea: {paleta.LINEA}; --gris: {paleta.GRIS}; --fondo: {paleta.FONDO};
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
  .bar {{ max-width: 1420px; margin: 0 auto; padding: 10px 20px;
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
  nav.chips {{ max-width: 1420px; margin: 0 auto; padding: 8px 20px 10px;
    display: flex; gap: 8px; flex-wrap: wrap; }}
  nav.chips a {{ font-size: 12px; text-decoration: none; color: #3c4348;
    background: #fff; border: 1px solid var(--linea); border-radius: 999px;
    padding: 4px 11px; display: inline-flex; align-items: center; gap: 6px; }}
  nav.chips a i {{ width: 7px; height: 7px; border-radius: 50%; display: inline-block; }}
  nav.chips a:hover {{ border-color: var(--verde); color: var(--tinta); }}
  main {{ max-width: 1420px; margin: 0 auto; padding: 14px 20px 40px; }}
  .intro {{ background: linear-gradient(180deg, {paleta.NIEBLA}, #fff 60%);
    border: 1px solid var(--linea); border-left: 4px solid var(--tinta);
    border-radius: 14px; padding: 12px 14px; margin-bottom: 14px; scroll-margin-top: 108px; }}
  .resumen {{ column-count: 3; column-gap: 24px; white-space: pre-wrap;
    font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 11.5px;
    line-height: 1.45; max-height: 300px; overflow: auto; }}
  .bento {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
    grid-auto-flow: dense; align-items: start; }}
  .tile {{ width: 100%; margin: 0; background: #fff;
    border: 1px solid var(--linea); border-top: 3px solid var(--sc, var(--linea));
    border-radius: 14px; padding: 11px; scroll-margin-top: 108px; }}
  .tile.wide {{ grid-column: span 2; }}
  .badge {{ display: inline-flex; align-items: center; gap: 6px; margin-bottom: 8px;
    font-size: 10.5px; font-weight: 700; text-transform: uppercase;
    letter-spacing: .1em; padding: 3px 10px; border-radius: 999px; }}
  .badge i {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
  .tile img {{ width: 100%; height: auto; border-radius: 8px; display: block; }}
  .tile figcaption {{ margin-top: 8px; display: flex; flex-direction: column; gap: 2px; }}
  .tile figcaption .t {{ font-size: 13px; font-weight: 650; }}
  .tile figcaption .n {{ font-size: 11px; color: var(--gris); line-height: 1.35;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    overflow: hidden; }}
  footer {{ max-width: 1420px; margin: 0 auto; padding: 18px 20px 40px;
    border-top: 1px solid var(--linea); font-size: 12px; color: var(--gris); }}
  @media (max-width: 1100px) {{
    .bento {{ grid-template-columns: repeat(2, 1fr); }}
    .resumen {{ column-count: 2; }}
  }}
  @media (max-width: 680px) {{
    .bento {{ grid-template-columns: 1fr; }}
    .tile.wide {{ grid-column: span 1; }}
    .resumen {{ column-count: 1; }}
    .bar h1 {{ font-size: 17px; }}
  }}
</style></head>
<body>
<div class="strip"></div>
<header>
  <div class="bar">
    <div>
      <div class="kick">Monitor · Ciudad de México</div>
      <h1>El mercado de la vivienda en la CDMX</h1>
    </div>
    <div class="spacer"></div>
    <a class="btn" href="vivienda_cdmx_interactivo.html">Versión interactiva →</a>
  </div>
  <nav class="chips">{nav}</nav>
</header>
<main>
  <section class="intro" id="{_slug('Resumen')}">
    <span class="badge"><i style="background:{paleta.TINTA}"></i>Resumen</span>
    <div class="resumen">{resumen}</div>
  </section>
  <div class="bento">{''.join(tiles)}</div>
</main>
<footer>Generado por el pipeline de vivienda-cdmx · PADIM mide el inventario en
  venta, no transacciones ni avalúos · Fuentes: PADIM · SNIIV/SEDATU · INEGI
  Censo 2020 · CONAPO · CONEVAL · ENIGH · SHF · Inside Airbnb.</footer>
</body></html>"""
    out = config.OUT / "vivienda_cdmx.html"
    out.write_text(html, encoding="utf-8")
    return out