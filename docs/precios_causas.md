# ¿Por qué es cara la vivienda en la CDMX? — hipótesis, datos y escenarios

> Análisis para `vivienda-cdmx` (2026-10). Fuentes propias: Censo 2020 INEGI,
> PADIM (portales), Inside Airbnb (corte 2026-09-23), tarifas 2026 de
> `src/impuestos.py`. Literatura: ver sección de fuentes. Correlaciones
> **descriptivas, sin causalidad** (n pequeño).

## Veredicto rápido

| Hipótesis | Veredicto | Evidencia clave |
|---|---|---|
| **Oferta estresada** (regulación + geografía frenan la oferta) | ✅ **Principal causa** | 59% del territorio es Suelo de Conservación; la CDMX es la entidad con **menos vivienda nueva** de México (3.4% ≤5 años vs 9% nacional); precio/m² de venta $63,577 vs obra $11–22k → suelo+regulación+margen ≈ ⅔ del precio |
| **Especulación** (vivienda vacía retenida) | ⚠️ **Parcial** | Vacancia 6.8% + uso temporal 2.4% del parque; las zonas caras duplican el uso temporal de la periferia (4.6% vs 0.5%); ρ precio↔vacancia = +0.55 (n.s., n=8). Falta: causa de desocupación por alcaldía |
| **Airbnb / rentas temporales** | ⚠️ **Parcial, efecto real pero pequeño** | Densidad central enorme (Cuauhtémoc 71.5 listados/mil viviendas) y correlaciona con uso temporal (ρ=+0.67, p=0.004); pero la evidencia **causal** estima efectos de **0.5–3%** en precios/rentas, no dobles dígitos |
| **Bajar impuestos + desregular uso de suelo + construir más → bajan precios** | 🔀 **Mitad y mitad** | Construir más: sí (−5% a −11% con +10% de stock). Desregular densidad: sí según evidencia internacional. **Bajar impuestos: NO baja precios** — bajar el ISAI subiría el precio de lista ~5% y bajar el predial subiría el precio del suelo 3–6% (capitalización) |

---

## 1. Qué muestran nuestros datos (por alcaldía)

### Vacancia y uso temporal (Censo 2020, `censo2020_alcaldia.csv`)

Vacancia = `VIVPAR_DES / (VIVPAR_HAB + VIVPAR_DES)`; uso temporal = `VIVPAR_UT`
(el único proxy censal de segundas residencias; no existe desglose de
"segundas residencias" para la CDMX).

| Zona caras (vacancia) | % | Periferia (vacancia) | % |
|---|---|---|---|
| Cuauhtémoc | 10.4 | La Magda. Contreras | 3.1 |
| Miguel Hidalgo | 9.8 | Iztapalapa | 3.8 |
| Benito Juárez | 9.8 | Álvaro Obregón | 4.9 |

- Uso temporal: Cuauhtémoc **4.6%**, Miguel Hidalgo **4.4%** vs Iztapalapa
  **0.5%**, Magda. Contreras **0.4%** → la vivienda "no residencial" se
  concentra exactamente donde es cara.
- CDMX en total: 6.8% deshabitadas + 2.4% uso temporal = 9.2% del parque no
  habitado de forma permanente (INEGI, Principales resultados Censo 2020 CDMX).
- ⚠️ La vacancia censal **incluye vivienda en venta/renta** (oferta del
  mercado) — no toda es especulación. La causa de desocupación por alcaldía no
  está disponible (hueco documentado).

### Airbnb (Inside Airbnb, `data/raw/airbnb_cdmx_listings.csv`)

- **30,468 listados** totales; **23,232** con reseñas en los últimos 12 meses.
- **66.8% casa entera** (20,348) = 0.67% del parque residencial; de ellos,
  **14,422 (47.3% de todo el listado)** tienen disponibilidad ≥180 días =
  0.48% del parque — ese es el inventario que compite de facto con la vivienda
  residencial.
- **58%** de listados pertenece a anfitriones con **>2 listados** (oferta
  profesionalizada); disponibilidad media de la casa entera: **242 días/año**.
- Densidad (listados por 1,000 viviendas): **Cuauhtémoc 71.5** · Miguel
  Hidalgo 34.7 · Benito Juárez 19.5 · Coyoacán 11.5 vs Iztapalapa 0.7 ·
  Tláhuac 0.4. El Airbnb es un fenómeno **del centro turístico**, no de la
  ciudad.
- Contexto regulatorio: la reforma de la Ley de Turismo/Ley de Vivienda CDMX
  (tope 180 noches) está **aprobada pero bloqueada por amparo de Airbnb**
  (Wired, ene-2025); una fuente periodística estimó 7,532 propiedades (28%)
  por encima del límite legal.

### Oferta en portales (PADIM)

- Densidad de listados en venta por 1,000 viviendas: Benito Juárez **49.3** ·
  Miguel Hidalgo **45.2** · Cuauhtémoc **30.2** vs Iztapalapa ≈ **0.01**.
- ⚠️ **Sesgo de cobertura documentado**: la periferia casi no tiene listados
  en portales, así que esta densidad mide *presencia en portales*, no oferta
  real. ρ precio/m² vs densidad de oferta = +0.10 (ruido).

### Correlaciones con precio/m² (Spearman, n=8 alcaldías con precio)

| Variable | ρ | p |
|---|---|---|
| Vacancia (Censo) | +0.55 | 0.16 |
| Uso temporal | +0.38 | 0.35 |
| Airbnb (por 1,000 viviendas) | +0.57 | 0.14 |
| Oferta en portales (por 1,000) | +0.10 | 0.82 |

Ninguna significativa con n=8 (potencia mínima). Sí es significativa, con
n=16: **Airbnb ↔ uso temporal ρ = +0.67 (p = 0.004)** — el Airbnb se
instala donde ya hay vivienda de uso no residencial (o lo provoca: la
causalidad corre en ambos sentidos).

---

## 2. Qué dice la literatura

### Oferta y regulación de suelo (la causa principal)

- **Glaeser & Gyourko (2002, NBER 8835)**: en mercados caros el "impuesto de
  zonificación" implícito (valor del suelo × densidad permitida vs precio)
  explica la brecha precio–costo de construcción. En Manhattan se permitieron
  13,000 unidades en 1960 vs 21,000 en todo el decenio 1990
  (Glaeser-Gyourko-Saks 2005): la escasez es regulatoria, no de tierra.
- **Glaeser & Ward (2009, JUE)**: en Boston los precios subieron y la oferta
  cayó *sin* falta física de tierra.
- **Saiz (2010, QJE)**: la geografía (agua, montañas) baja la elasticidad de
  oferta por ciudad — la CDMX, con **59% de suelo de conservación
  inurbanizable** (CDHCM), combina geografía + regulación.
- México: **no existe estudio causal "reforma de zonificación → precios"**
  (hueco). La evidencia más cercana es la reforma de Auckland 2016
  (Greenaway-McGrevy & Phillips, Cowles 2023): el upzoning sobre ¾ del suelo
  residencial detonó la construcción.
- Cifras locales: CDMX es la entidad con **menor % de vivienda nueva** de
  México (3.4% ≤5 años, ENVI 2020 vs 9% nacional); 63.1% de las operaciones
  2025 fueron vivienda **usada** (SHF). Precio de venta ZMCDMX **$63,577/m²**
  (Softec DIME, abr-2026) vs costo de obra paramétrico **$11,000–22,000/m²**
  (fuente secundaria, cautela) → **suelo + regulación + margen ≈ 65–83% del
  precio**. En vivienda social mexicana el terreno es 5–7% del costo en
  periferia y ~20% en centro (BID) — en CDMX la proporción de suelo es mucho
  mayor por el valor del centro.
- Permisos de construcción CDMX: **SEDUVI no publica serie histórica**
  (solo licencias caso por caso, Portal de Transparencia 46888) — no se pudo
  cruzar construcción vs precios. PIB construcción +0.3% (feb-2026), sigue
  deprimida (Fitch/INEGI).

### Airbnb

- **Barron, Kung & Proserpio (2021, Marketing Science)** — causal, EE.UU.:
  **+1% de listados → +0.018% rentas y +0.026% precios** (elasticidad ≈0.02).
- **García-López et al. (2020, JUE)** — causal, Barcelona: efecto promedio
  +1.9% rentas / +4.6% precios; en el **decil superior de actividad Airbnb: +7%
  rentas / +17% precios**.
- CDMX: **tesis Colmex (Martínez Torres)** afirma **+13% precios** por Airbnb —
  trabajo **no revisado por pares y no identificación causal** (estima
  primas hedónicas; además Airbnb se instala en zonas caras: correlación, no
  causa). No hay paper peer-reviewed de Airbnb→vivienda en CDMX (hueco).
- Colmex (DT-2021-7): 41% de la oferta CDMX es de anfitriones con >2 listados.

### Impuestos

- **Incidence**: el ISAI lo paga el adquirente; con oferta (casi) vertical en
  la CDMX (stock fijo a corto plazo), **la carga la termina soportando el
  vendedor** → eliminar el ISAI sube el precio de lista hasta el monto del
  impuesto y baja el costo total del comprador; no "baja precios" en el
  sentido usual. No hay estudio de incidencia del ISAI en México (hueco), la
  teoría estándar (Mieszkowski/Harberger) basta para el signo.
- **Predial se capitaliza en el precio del suelo**: bajarlo **sube** el precio
  de los terrenos (Wales & Wiens 1974, REStat; síntesis Hilber 2017). La
  recaudación predial mexicana es ~0.2% del PIB con solo 52.5% de efectividad
  (INEGI CNGMD 2024) — hay margen de recaudación, no de recorte.
- ISAI art. 113: la SCJN lo declaró **inconstitucional** por
  proporcionalidad (efectos 2021–2024); el Congreso CDMX lo reformó en
  2024 y la tarifa vigente es la 2026 que usamos en `src/impuestos.py`.

---

## 3. Escenarios cuantificados (nuestros cálculos)

Elasticidades de referencia (literatura internacional; **no hay estimación
para México**): demanda |η_d| = 0.7, oferta η_s = 0.5 (rango 0.2–1.0).

### A. Bajar o eliminar el ISAI (5.1–5.4% del precio)

- Oferta vertical (stock fijo): el precio de lista **subiría** ~5.1–5.4%
  (ej.: Benito Juárez $201,153 en la mediana $3.74 M → precio de lista
  ~$3.94 M) y el **costo total del comprador bajaría** ~$132k–$201k.
- Efecto secundario positivo: menos fricción de transacción → más volumen
  de operaciones (elástica de transferencia).
- **Conclusión: bajar el ISAI no baja los precios; baja el costo de comprar
  y sube el precio de etiqueta.**

### B. Bajar el predial (0.23–0.26% del precio/año)

- Predial anual mediano ≈ $8,824 (precio mediano $3.47 M, catastral 40%,
  dto. enero). Capitalizado al 4–6%: **$147k–$221k = 4.2–6.4% del precio**.
- **Bajar el predial subiría el precio del suelo/vivienda** ese rango;
  bajarlo a cero no hace la vivienda más barata, la hace más cara y además
  deja de financiar alcaldías. (Simétrico: subirlo con recaudación real
  presionaría precios a la baja y desincentiva retención de suelo vacío.)

### C. Regular/desactivar Airbnb

- Suprimir el inventario no conforme (casa entera con ≥180 días de
  disponibilidad: 14,422 listados = −47% del total) y aplicar elasticidades
  de Barron-Kung-Proserpio:
  - precios **−1.2%**, rentas **−0.9%** (lado demanda).
  - Lado oferta: regresar 20,348 casas enteras al mercado residencial
    = **+0.67% de stock** → precios **−0.6%** [ΔlnP = ln(1.0067)/(0.7+0.5)].
- Suprimir Airbnb **completo** con la misma elasticidad: precios −2.6%,
  rentas −1.8%.
- Tope superior alternativo (tesis Colmex, no causal): ~13% — no conciliable
  con la evidencia causal; usar solo como escenario maximalista.
- **Conclusión: Airbnb mueve la aguja 1–3% (tal vez 13% en el peor caso no
  causal), no explica la diferencia de precios entre alcaldías (×1.9 por m²).**

### D. Construir más (+10% de stock = 303,513 viviendas)

- ΔlnP = −ln(1.10) / (|η_d| + η_s) = −0.095/1.2 → **−7.9% de precio**;
  rango con η_s 0.2–1.0 → **−11.2% a −5.3%** (demanda fija; con demanda
  creciente el efecto es menor).
- Ritmo necesario: la CDMX produce ~20.6k viviendas/año (3.4% del parque
  tiene ≤5 años, ENVI 2020) → **+10% toma ~15 años al ritmo actual**;
  5 años exigiría ~3× el ritmo (60.7k/año).
- El cuello de botella es justamente la hipótesis 1: suelo permitido,
  permisos y costo de obra.

### E. Desregular uso de suelo (densificar el tejido existente)

- Sin estudio mexicano; la evidencia internacional (Auckland 2016, Boston,
  Manhattan) dice que la densidad permitida es el determinante del precio
  relativo al costo. En la CDMX el margen real es **densificar lo ya
  urbanizado** (COS/FAR de zonas habitacionales), porque el 59% restante es
  Suelo de Conservación intocable.
- Efecto combinado plausibile: desregular + construir = escenario D con
  η_s alto → hasta −11% en 5 años si la oferta responde rápido.

---

## 4. Huecos documentados (sin dato seguro)

1. Causa de desocupación (¿en venta/renta vs segundas residencias vs obra
   nueva?) por alcaldía en la CDMX — INEGI no la publica en nuestros paneles.
2. Serie anual de permisos/licencias de construcción CDMX (SEDUVI no la
   publica consolidada).
3. Estudio causal Airbnb→precios en CDMX (solo tesis no revisada).
4. Elasticidad de oferta/demanda de vivienda **de México** (se usan
   rangos internacionales).
5. % de suelo en el precio de la vivienda en CDMX (solo cifra BID de
   vivienda social y precios Softec vs obra de fuente secundaria).
6. Incidencia empírica del ISAI (solo teoría estándar de incidencia).

## 5. Fuentes principales

- INEGI, Censo 2020 CDMX (vacancia/uso temporal), ENVI 2020 (3.4% vivienda
  nueva) · https://en.www.inegi.org.mx/contenidos/programas/ccpv/2020/doc/cpv2020_pres_res_cdmx.pdf
- Inside Airbnb, CDMX 2026-09-23 · https://data.insideairbnb.com/mexico/df/mexico-city/2026-09-23/visualisations/listings.csv
- Barron, Kung & Proserpio (2021), *Marketing Science* 40(1) · DOI 10.1287/mksc.2020.1227
- García-López, Jofre-Monseny, Martínez-Mazza & Segú (2020), *JUE* (Barcelona).
- Glaeser & Gyourko (2002) NBER 8835 · Glaeser & Ward (2009) JUE 65(3) · Saiz (2010) QJE 125(3).
- Greenaway-McGrevy & Phillips (2023), Cowles 1863 (Auckland).
- Wales & Wiens (1974), *REStat* 56 (capitalización predial) · Hilber (2017) *Real Estate Economics*.
- SHF (índice de precios, precio medio CDMX $3.97M 4T-2025) · Softec DIME abr-2026 ($63,577/m²) · Banorte/El Financiero jul-2026 (brecha por alcaldía).
- Tesis Colmex Airbnb +13% (no causal) · https://reimaginarelcapitalismo.colmex.mx/airbnb-y-el-mercado-de-vivienda-en-mexico
- Ley de Turismo CDMX 180 noches y amparo Airbnb (Wired, 2025).
- BID, *¿Por qué allí?* (suelo en costo de vivienda social).
- IEG/SCJN/Congreso CDMX (inconstitucionalidad y reforma del ISAI art. 113).
