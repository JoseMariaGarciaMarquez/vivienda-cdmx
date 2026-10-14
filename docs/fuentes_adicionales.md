# Fuentes de datos adicionales para el monitor

El proyecto ya integra: PADIM (portales de venta), SNIIV/SEDATU (oferta y
crédito), SEDUVI (catálogo de suelo), SHF (índice de precios), INEGI Censo 2020,
CONAPO (marginación), CONEVAL (pobreza), ENIGH (ingresos) e Inside Airbnb.

Huecos actuales que limitan el análisis:

- **Sin renta**: PADIM solo trae venta, así que no hay ratio precio/renta ni
  rendimiento de alquiler observado en el mismo snapshot (el yield se estima,
  no se mide).
- **Sin transacciones reales**: todo es inventario en oferta, no escrituración
  ni avalúos; el precio de cierre puede diferir del de lista.
- **Sin permisos de obra**: SEDUVI no publica licencias en formato abierto, por
  lo que no se puede medir la respuesta de oferta nueva.
- **Sin causalidad**: no hay estudio causal Airbnb→precio para la CDMX.
- **Cobertura parcial**: solo 8 alcaldías tienen muestra suficiente de precio en
  portales; la periferia queda fuera.

## Candidatas por valor y disponibilidad

| Fuente | Qué aporta | Formato / acceso |
|---|---|---|
| **SHF — Índice de precios** | Serie oficial de referencia por alcaldía | CSV/Excel manual (ya previsto) |
| **Incidencia delictiva FGJ-CDMX** | Seguridad por colonia (carpetas) | Datos abiertos CDMX, CSV |
| **DENUE (INEGI)** | Equipamiento, comercio, servicios por AGEB | API/SHP, gratis |
| **GTFS de transporte (Metro/Metrobús/RTP)** | Accesibilidad, estaciones, tiempos | Datos abiertos CDMX / OSM |
| **OpenStreetMap** | Vialidad, amenidades, huella urbana | Overpass API, gratis |
| **Catastro / valores catastrales** | Base gravable real vs precio de mercado | CDMX, trámite/transparencia |
| **CONEVAL — Rezago social por AGEB** | Detalle intra-alcaldía | Excel/CSV |
| **INEGI — DENUE + Directorio** | Dinámica económica por zona | CSV |
| **Banxico — tasas hipotecarias** | Costo del crédito actualizado | API/SIE, gratis |
| **CONAVI / ONAs — montos y tasas** | Acceso real a crédito por ingreso | Reportes, PDF/CSV |
| **Airbnb (scraping periódico)** | Serie temporal de presión turística | Inside Airbnb trimestral |
| **Índice SHF de costos de construcción** | Costos de edificación | Excel manual |
| **Gobierno CDMX — Programas de vivienda** | Intervención pública por zona | Portales, PDF |
| **RENAVI / RUV** | Vivienda nueva formal en registro | RUV, consulta |
| **Encuesta de movilidad / tiempo de traslado** | Costo de accesibilidad real | PDF/estudios |
| **INPC + subíndice vivienda** | Deflactar precios por zona | API Banxico |

## Prioridad sugerida

1. **Renta de portales** (scraping de anuncios de alquiler) → desbloquea el
   índice de rentabilidad real, hoy estimado.
2. **Incidencia delictiva + DENUE + GTFS** → alimentan accesibilidad y
   seguridad en el índice de "dónde vivir".
3. **Valores catastrales** → medir la brecha entre base gravable y precio de
   mercado (útil para política de predial).
4. **Serie trimestral de Airbnb** → convertir la foto actual en tendencia.
