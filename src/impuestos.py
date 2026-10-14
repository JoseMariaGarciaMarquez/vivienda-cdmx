"""Impuestos sobre la vivienda en CDMX — tarifas fiscales 2026.

Fuentes verificadas contra texto oficial:
- ISAI: art. 113 del Código Fiscal de la CDMX, tarifa 2026 (G.O. 19-dic-2025,
  factor inflacionario 1.0391; corroborada por el decreto citado en
  oscar­mirandaabogado.com). Base: mayor de precio de compra o valor
  catastral (art. 116).
- Predial: art. 130 del Código Fiscal de la CDMX, tarifa 2026. La tarifa se
  aplica POR BIMESTRE (art. 130) -> anual = 6 x bimestre. La columna
  "porcentaje" se divide entre 100 (continuidad exacta entre rangos). La SAF
  da 8% de descuento por pago en enero y 5% en febrero (2026). El valor
  catastral equivale a ~30-50% del precio de mercado (SAF).
- IVA: LIVA art. 9-II (compraventa de casa habitación exenta) y art. 20-II
  (renta de casa habitación exenta; 16% solo si es amueblada o hospedaje).
- ISR venta: LISR art. 93 XIX a) — exenta hasta 700,000 UDIS de precio.
- ISR renta: LISR art. 115 (deducción ciega 35%) + tarifa anual art. 152
  (Anexo 8 RMF 2026). Sin subsidio al empleo (aplica solo a asalariados).
"""
from __future__ import annotations

from typing import Sequence

# --- ISAI (compra, una sola vez) -------------------------------------------
# (rango, límite inferior, cuota fija, factor sobre el excedente del límite)
TARIFA_ISAI: list[tuple[str, float, float, float]] = [
    ("A", 0.12, 327.29, 0.01446),
    ("B", 123_988.82, 2_120.18, 0.03083),
    ("C", 198_382.04, 4_413.73, 0.04028),
    ("D", 297_572.77, 8_409.14, 0.04699),
    ("E", 595_145.68, 22_392.10, 0.05219),
    ("F", 1_487_864.16, 68_983.09, 0.05702),
    ("G", 2_975_728.35, 153_821.12, 0.06185),
    ("H", 5_732_476.12, 324_325.98, 0.06425),
    ("I", 14_928_323.93, 915_159.21, 0.06495),
    ("J", 27_529_938.64, 1_733_634.09, 0.06546),
    ("K", 55_059_877.22, 3_535_743.88, 0.09018),
]

# --- Predial (tenencia anual) ----------------------------------------------
# (rango, límite inferior, cuota fija BIMESTRAL, porcentaje sobre excedente)
TARIFA_PREDIAL: list[tuple[str, float, float, float]] = [
    ("A", 0.12, 231.00, 0.02080),
    ("B", 235_095.03, 279.91, 0.03889),
    ("C", 470_189.37, 371.35, 0.12149),
    ("D", 940_380.48, 942.60, 0.14625),
    ("E", 1_410_569.81, 1_630.26, 0.14723),
    ("F", 1_880_760.96, 2_322.53, 0.16801),
    ("G", 2_350_950.28, 3_112.51, 0.17052),
    ("H", 2_821_139.61, 3_914.29, 0.18305),
    ("I", 3_291_330.77, 4_774.98, 0.18814),
    ("J", 3_761_520.10, 5_659.60, 0.19034),
    ("K", 4_231_711.26, 6_554.57, 0.19292),
    ("L", 4_701_900.57, 7_461.67, 0.19490),
    ("M", 5_172_089.91, 8_378.08, 0.20261),
    ("N", 5_642_728.84, 9_331.65, 0.26334),
    ("O", 16_928_184.62, 39_050.78, 0.26142),
    ("P", 35_629_332.12, 87_939.33, 0.30909),
]

DTO_PRONTO_PAGO_ENERO = 0.08  # SAF CDMX 2026
DTO_PRONTO_PAGO_FEBRERO = 0.05
RATIO_CATASTRAL_REF = 0.40  # catastral ≈ 30–50% del precio de mercado (SAF)

# --- ISR --------------------------------------------------------------------
# Tarifa anual art. 152 LISR (Anexo 8 RMF 2026): (límite inferior,
# límite superior o None, cuota fija, % sobre excedente)
TARIFA_ISR_ANUAL: list[tuple[float, float | None, float, float]] = [
    (0.12, 10_135.08, 0.00, 0.0192),
    (10_135.20, 86_022.12, 194.64, 0.0640),
    (86_022.24, 151_176.24, 5_051.40, 0.1088),
    (151_176.36, 175_735.68, 12_140.16, 0.1600),
    (175_735.80, 210_403.68, 16_069.68, 0.1792),
    (210_403.80, 424_353.96, 22_282.08, 0.2136),
    (424_354.08, 668_840.16, 67_981.92, 0.2352),
    (668_840.28, 1_276_926.00, 125_485.08, 0.3000),
    (1_276_926.12, 1_702_567.92, 307_910.76, 0.3200),
    (1_702_568.04, 5_107_703.88, 444_116.28, 0.3400),
    (5_107_704.00, None, 1_601_862.48, 0.3500),
]

DEDUCCION_CIEGA_RENTA = 0.35  # LISR art. 115: deducir 35% sin comprobantes
IVA_TASA = 0.16
TOPE_EXENCION_ISR_VENTA_UDIS = 700_000.0  # LISR art. 93 XIX a)
UDI_REFERENCIA = 8.83  # referencia jun-2026 (~$6.18 M el tope)

# Gastos de cierre de la compra — NO son impuestos (notaría + IVA de la
# notaría + registro RPP + avalúo + gestoría). La comisión inmobiliaria
# (3–5%, normalmente del vendedor) es aparte.
CIERRE_MIN = 0.03
CIERRE_MAX = 0.07


def _tarifa(
    valor: float,
    tabla: Sequence[tuple[str, float, float, float]],
    es_porcentaje: bool = False,
) -> float:
    """Aplica cuota fija + factor sobre el excedente del límite inferior."""
    fila = tabla[0]
    for cand in tabla:
        if valor >= cand[1]:
            fila = cand
    _, li, cuota, factor = fila
    factor = factor / 100.0 if es_porcentaje else factor
    return max(cuota + factor * (valor - li), 0.0)


def isai(valor: float) -> float:
    """Impuesto sobre Adquisición de Inmuebles (compra), pesos."""
    return _tarifa(max(valor, 0.12), TARIFA_ISAI)


def predial_bimestral(catastral: float) -> float:
    """Predial de un bimestre (art. 130), pesos."""
    return _tarifa(max(catastral, 0.12), TARIFA_PREDIAL, es_porcentaje=True)


def predial_anual(
    catastral: float,
    *,
    descuento: float = DTO_PRONTO_PAGO_ENERO,
) -> float:
    """Predial anual = 6 bimestres con descuento por pronto pago (0 = sin dto)."""
    return predial_bimestral(catastral) * 6 * (1 - descuento)


def predial_desde_precio(
    precio: float,
    *,
    ratio_catastral: float = RATIO_CATASTRAL_REF,
    descuento: float = DTO_PRONTO_PAGO_ENERO,
) -> float:
    """Predial anual estimado asumiendo catastral = ratio del precio."""
    return predial_anual(precio * ratio_catastral, descuento=descuento)


def isr_renta_anual(renta_bruta_anual: float) -> float:
    """ISR anual del arrendador (régimen general, deducción ciega 35%).

    Sobre la renta bruta anual; no aplica subsidio al empleo (solo asalariados)
    ni deducciones personales del art. 151, que reducirían el resultado.
    """
    if renta_bruta_anual <= 0:
        return 0.0
    base = renta_bruta_anual * (1 - DEDUCCION_CIEGA_RENTA)
    fila = TARIFA_ISR_ANUAL[0]
    for cand in TARIFA_ISR_ANUAL:
        if base >= cand[0]:
            fila = cand
    li, _ls, cuota, pct = fila
    return max(cuota + pct * (base - li), 0.0)


def isr_venta_exenta(precio: float) -> bool:
    """¿La ganancia de la venta queda exenta (precio ≤ 700,000 UDIS)?"""
    return precio <= TOPE_EXENCION_ISR_VENTA_UDIS * UDI_REFERENCIA


def iva_renta(amueblada: bool) -> float:
    """IVA de la renta: 0% casa habitación sin amueblar, 16% amueblada."""
    return IVA_TASA if amueblada else 0.0
