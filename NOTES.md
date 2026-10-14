# vivienda-cdmx · Notas

Panel reproducible del mercado de la vivienda en la CDMX (demanda, oferta,
precios, perfil sociodemográfico), alcaldía + camino a colonia/CP.

## Estado (2026-09-24)

Pipeline verde end-to-end: `python main.py [--refresh]` →
`outputs/vivienda_cdmx.html` + `outputs/resumen_vivienda.txt` + notebook.

**Banda v0 (datos reales descargados hoy):**
- PADIM CDMX: 30,003 observaciones en venta (todas `price_semantics=venta`;
  el API aún no sirve renta).
- Oferta en portales concentrada en 9 alcaldías (las 16 no aparecen: el mercado
  de listados es sesgado). Medianas $/m²: Cuajimalpa $27.8k · Cuauhtémoc $27.8k ·
  Miguel Hidalgo $25.9k · Álvaro Obregón $24.4k · Benito Juárez $22.9k ·
  Coyoacán $22.8k · Tlalpan $17.8k · Xochimilco $14.8k (banda residencial,
  m² 20–600, $/m² 1k–600k). Brecha 87%.
- SNIIV financiamientos CDMX: 2024 → 46,541 acciones / 57,802 MDP; 2025 →
  47,410 / 60,004 MDP; 2026 (YTD) → 22,823 / 26,457 MDP.
- Rezago municipal/estatal 2020 y Déficit: descargados; **los "csv" de SEDATU
  en realidad son XLSX** (dispatch automático por magia `PK`).
- SEDUVI: catálogo de valores de suelo + catastro por alcaldía listo
  (16 conjuntos). Datos crudos aún sin bajar.

**Fuentes verificadas EN VIVO:**
- **PADIM** (`api.padim.org`): ~59k observaciones de CDMX, 30k en venta.
  Fuentes: inmuebles24, vivanuncios, propiedades_com, mls, doorvel, easybroker,
  plalla. Campos: `precio_mxn, m2, municipality, lat/lng (G5 = zona, sin predio),
  price_semantics (venta/renta), observed_at`. API sin key. Límite 500/página.
- **SNIIV/SEDATU** `sniiv.sedatu.gob.mx`:
  - Datos abiertos (alfresco): Déficit y Rezago habitacional municipal 1990–2022.
  - CuboAPI `GetFinanciamiento/{año}/09/000/{dim}` → acciones+monto por organismo
    (verificado: 2024 → INFONAVIT 26,580 acc / BANCA 15,576 acc).
  - Cubo de Inventario/Registro RUV existe pero requiere claves de dimensión;
    quedan fuera del v1 (diccionario en `data/raw/sniiv_diccionario_registro.*`).
- **datos.cdmx.gob.mx (CKAN)** `api/3/action`: conjuntos
  `valores-unitarios-del-suelo-habitacional-...` y `informacion-catastral`.

**Capa sociodemográfica (CONAPO + SEPOMEX, descargado hoy):**
- SEPOMEX: POST `CodigoPostal_Exportar.aspx` (cboEdo=09, __EVENTTARGET=btnDescarga)
  → `.xls` 758 KB, 1,531 asentamientos / 1,110 CP. → `data/processed/cp_cdmx.csv`.
- CONAPO marginación 2020: colonia (`faabdc7b.../imuc_2020.csv`, 2,243 filas CDMX,
  con CP) y AGEB (`9600f414.../imu_2020.csv`). **El `requests` debe mandar headers
  de navegador (UA Chrome + Accept + Referer datos.gob.mx) o da 403.**
- Perfil por alcaldía (pob. en marg. alta/muy alta): Xochimilco 16.5% · Milpa Alta
  15.9% · Tlalpan 11.1% · L. M. Contreras 4.4% · Iztapalapa 3.6%.
- Cruce **log($/m²) ↔ % marg. = −0.94** (las zonas más caras son las menos marginadas).
- **Calidad de gráficas**: QA automático en `report._cierra` — al cerrar cada
  figura compara todas las cajas de texto (títulos, ejes, ticks en vista,
  etiquetas, leyendas) y avisa si hay empalme >50px² o texto fuera del lienzo;
  hoy corre el pipeline con **0 avisos**. `_Colocador` coloca etiquetas
  (mapas y dispersión) en la primera posición libre de una espiral de offsets;
  `_recolorea_mapa` pinta cada etiqueta del mapa blanco/azul según el brillo
  del polígono bajo ella (con trazo de contraste). Títulos centrados en todas
  las figuras (suptitle en mapas y dispersión). Dashboard a ancho completo
  (columna ≥760px) para que los textos se lean al escalar.
- Dashboard con **14 gráficas**: m² y box por alcaldía, financiamientos,
  marginación, censo 2020, asequibilidad, **5 mapas** (impuestos ISAI y
  predial, Airbnb, **marginación**, **precio/m²**), dispersión causas y ratio
  precio/renta. El cruce precio↔marginación como dispersión se **eliminó**
  (degenerado: 9/16 alcaldías tienen ~0% de marginación alta) y se sustituyó
  por los dos mapas coropléticos, comparables de un vistazo.
- **Dashboard interactivo** (`src/interactivo.py` → `outputs/vivienda_cdmx_interactivo.html`):
  Plotly con `plotly.js` inline (funciona sin internet). Un choropleth con
  **selector de 8 métricas** (precio m², ISAI % precio, predial % precio,
  Airbnb/1,000 viv., vivienda desocupada, marginación, **índice de oportunidad**,
  **índice de calidad**) + fondo gris de las 16 alcaldías; una **dispersión con
  selector de eje X** (vacancia, Airbnb, uso temporal, oferta) para el cruce con
  precio; y barra de financiamientos. El dashboard estático enlaza al
  interactivo y viceversa.
- Nota de marginación (definición en las tarjetas): índice **compuesto**
  CONAPO 2020 (educación, vivienda/servicios, ingresos, residencia) por
  colonia/AGEB; se reporta el % de población en grado alto o muy alto.

**Índices de compra + rediseño (paleta "turbine" + layout OWID):**
- `src/paleta.py`: 6 colores extraídos de `/home/chema/Descargas/turbine-6-32x.png`
  (`#5ae3ff · #e3feff · #c2eba4 · #39ba2d · #354c4b · #212833`) + rampa
  secuencial `SECUENCIAL` para mapas. `report.py` e `interactivo.py` la importan
  (antes: `#c1272d/#1f4e79/#9db6cf/...`).
- `src/indices.py` → `data/processed/indice_compra.csv`. Dos índices 0–100
  (más alto = mejor), **relativos a la CDMX**, reescalado min-max y promedio
  ponderado:
  - `indice_oportunidad` (comprar): barato 0.30 + asequible 0.20 + servicios
    0.20 + marginación 0.15 + pobreza 0.15. **Exige precio + asequibilidad**
    (requeridos) → solo las **8 alcaldías con portales**. Top: Benito Juárez
    61.4 · Cuajimalpa 59.4 · Coyoacán 58.7; peor Xochimilco 43.7.
  - `indice_calidad` (vivir, sin precio): servicios 0.40 + marginación 0.25 +
    pobreza 0.25 + hacinamiento 0.10 → las **16**. Top: Benito Juárez 100 ·
    Miguel Hidalgo 92.9 · Cuauhtémoc 90.7; peor Xochimilco 7.7 · Milpa Alta 14.2.
  - `src/analyze.py::_bloque_indices` agrega el ranking al resumen;
    `report.grafica_mapa_indice` genera 2 mapas; el interactivo suma las 2
    métricas. Pesos editables en el propio módulo.
- **Layout "bento"** (tras feedback: el OWID con sidebar se veía mal y
  obligaba a desplazar demasiado): barra superior *sticky* compacta + chips de
  navegación de color, resumen en bloque de 3 columnas de texto, y **mosaico
  tipo bento** en `display:grid` 3 columnas con `grid-auto-flow: dense` y
  tarjetas anchas (`grid-column: span 2`) para las gráficas de mayor aspecto
  (`_FEATURE`); responsive 2/1. 16 tarjetas con imagen + título + nota,
  insignia de sección en píldora de color y borde superior por sección
  (`--sc`). La página completa mide ~2,700 px a 1440 de ancho (≈3 pantallas;
  antes ~13). Mismo shell compacto + bento de 4 tiles (mapa `span2` + "cifras
  clave" + dispersión `span2` + financiamientos) en el interactivo.
- **Pase de color** (feedback: "solo azul y blanco"): paleta turbine aplicada
  a insignias, chips de navegación, borde superior de tarjetas y degradados
  tenues (NIEBLA) en las cabeceras de resumen; verificado por screenshot
  (NIEBLA ~10%, VERDE_CLARO ~2.6% de los píxeles).

**Déficit y oferta de vivienda (SNIIV-SEDATU):**
- `src/deficit.py`: `CLAVE_ALCALDIA` (claves municipales SNIIV **no** en orden
  INEGI alfabético; verificado vs catálogo IECM y conteos del Censo 2020),
  `panel_rezago_alcaldia()` → `data/processed/rezago_alcaldia.csv`,
  `cifras_deficit()` y `panel_estres()`.
- CDMX 2024: déficit habitacional **234,615** viviendas (rezago 184,279 +
  necesidades anuales 50,336); producción de crédito 46,541 acciones/año
  (**92%** de las necesidades, brecha ~3,795/año). `nec_viv` solo existe a
  nivel estatal y 2024 (archivo XLSX → `pd.read_excel`); es *proxy* de oferta
  (incluye mejoras, no solo vivienda nueva).
- Rezago 2020 por alcaldía (16): Milpa Alta 22.5% · Xochimilco 17.8% ·
  Tláhuac 12.8% · Magdalena 12.6% · Tlalpan 11.5% … Benito Juárez 2.1%.
- Integración: `report.grafica_mapa_rezago` (`mapa_rezago.png`, mapa) y
  `grafica_estres_oferta` (`estres_oferta.png`, barras vs línea de
  necesidades); sección "Déficit y oferta" en el dashboard estático,
  `_bloque_deficit` en el resumen, métrica "Rezago habitacional" + stat de
  déficit en el interactivo.

- `docs/politica.md`: instrumentos basados en los índices (sobretasa a vivienda
  vacía/uso turístico, suavizar ISAI a primera vivienda, oferta incluyente donde
  calidad alta + precio alcanzable, cerrar brecha de servicios en el sur,
  transparencia de permisos/rentas).
- `docs/fuentes_adicionales.md`: fuentes candidatas (SHF, FGJ incidencia, DENUE,
  GTFS, OSM, catastro, Banxico, CONAVI, Airbnb serie, RUV) con prioridad.

**Censo 2020 (INEGI, DATOS ABIERTOS SIN TOKEN):**
- Fuente: `datosabiertos/ageb_manzana/ageb_mza_urbana_{ent}_cpv2020_csv.zip`
  (verificado: 200, 13 MB ZIP → CSV 44 MB, 230 indicadores, único archivo con
  manzanas + AGEB + localidad + municipio + entidad). `src/inegi.py`.
- CDMX: **66,456 manzanas** y **2,211 AGEB** urbanas; población 9,145,590
  (contra 9,209,944 del CONAPO — cierre del censo; pequeña dif. por AGEBs no
  urbanas/manzanas faltantes).
- Paneles: `censo2020_manzanas_cdmx.csv` (clave `cve_manzana` =
  ent+mun+loc+ageb+mza), `censo2020_ageb_cdmx.csv`, `censo2020_alcaldia.csv`
  con indicadores (índice de dependencia, hacinamiento = pers./cuarto
  `PRO_OCUP_C`, % vivienda sin agua/drenaje/luz, piso de tierra, tasa de
  actividad, masculinidad).
- Cruce censo↔CONAPO: clave `cve_ageb` = ent(2)+mun(3)+loc(4)+ageb(4) casa con
  `CVE_AGEB` de CONAPO: **2,161/2,211 AGEB** con `POBTOT == POB_TOTAL` (99.9%
  consistente). → `censo2020_ageb_marginacion.csv` (AGEB con IM/IMN/GM).
- Lectura: `AGEB/LOC/MZA` se leen como **str** (conservan ceros) y se numeran
  aparte; las claves nunca por float (se genera `0900...00.0`). Único gotcha.
- Highlights: Gustavo A. Madero dep. 52.4% · Benito Juárez 60+ 20.1% y
  hacinamiento mínimo 2.68 · Milpa Alta <15 22.2%, hacin. 4.07, 4.4% sin agua ·
  Xochimilco 6.47% viviendas sin agua entubada.

**ENIGH 2022 + CONEVAL 2020 → asequibilidad (auto-descargado):**
- ENIGH 2022, microdatos `concentradohogar` (INEGI, 12.5 MB ZIP): `ubica_geo`
  ent+mun (leer como **int → `zfill(5)`**, el `09x` no aparece como cadena).
  `ing_cor` trimestral × `factor`. CDMX: ~2.99M hogares ponderados, ingreso
  mediano mensual **$24,835** (pesos 2026).
- INPC 2018a `conjunto_de_datos_inpc_mensual.csv` (llega a 2026-08): factor
  **1.1874** (último mes / promedio 2022) para inflar ingresos 2022 → 2026.
  `src/enigh.py`, `src/coneval.py`, `data/processed/enigh_cdmx_{ingresos,hogares}.csv`,
  `coneval_pobreza_alcaldia.csv`, `asequibilidad.csv`.
- CONEVAL pobreza municipal: datos.gob.mx `pobreza_municipal.csv`; **filtrar
  `clave_entidad==9`** (hay municipios homónimos en otros estados → sin el filtro
  salían 29 filas). Rango pobreza 2020: Benito Juárez 7.9% → Milpa Alta 54.7%.
- Asequibilidad (mediana en venta por alcaldía vs ingreso mediano CDMX): 8.7–12.6
  **años de ingreso** para comprar; mensualidad = 94–135% del ingreso mediano;
  solo **3–8% de los hogares** cubren la cuota (90% a 20 años @10.5%, regla 30%).
  Gráfica `asequibilidad.png` + bloque en resumen + celdas de notebook.
- Dashboard suma bloques CONEVAL y asequibilidad (conteo de gráficas arriba).

**Causas del precio alto (docs/precios_causas.md + bloque en el resumen):**
- `src/causas.py` → `data/processed/causas_alcaldia.csv` (16 alcaldías):
  vacancia y uso temporal (Censo 2020 `VIVPAR_DES`/`VIVPAR_UT`), densidad de
  Airbnb (`airbnb_x1000`) y de oferta portales (`oferta_x1000`) + precios PADIM.
- Airbnb: descarga automática de Inside Airbnb (`AIRBNB_URL` en `causas.py`,
  corte 2026-09-23; si la URL vence o no hay red, el panel sigue sin él).
  30,468 listados · 66.8% casa entera · 58% anfitriones con >2 listados ·
  Cuauhtémoc 71.5 listados/mil viviendas vs Tláhuac 0.4.
- Correlaciones Spearman (n=8): precio/m² vs vacancia +0.55 (p=0.16), vs
  Airbnb +0.57 (p=0.14), vs oferta +0.10 → **no significativas**; sí
  Airbnb↔uso temporal ρ=+0.67 (p=0.004, n=16). Todo **descriptivo, no causal**.
- **`docs/precios_causas.md`**: evaluación de las 3 hipótesis (oferta
  estresada ✅ / especulación ⚠️ / Airbnb ⚠️) + literatura citable (Glaeser &
  Gyourko, Glaeser & Ward, Saiz, Barron-Kung-Proserpio, García-López, Wales &
  Wiens) + escenarios: bajar ISAI sube precio de lista ~5% (incidencia con
  oferta vertical); bajar predial sube precio del suelo 4–6% (capitalización);
  Airbnb completo mueve precios −1.2% a −2.6% (elasticidades BKP) o −13% (tesis
  Colmex, no causal); +10% stock → −5% a −11% precios (|η_d|=0.7, η_s=0.5),
  +10% toma ~15 años al ritmo actual de construcción (20.6k/año ENVI).
- Huecos: causa de desocupación por alcaldía, permisos SEDUVI, elasticidades
  mexicanas, % de suelo en precio CDMX, estudio causal Airbnb→precios CDMX.

**Impuestos 2026 (bloque en el resumen + 2 mapas):**
- `src/impuestos.py`: tarifas 2026 verificadas contra texto oficial y
  validadas por **continuidad entre rangos (±$0.01)** y por checks de recaudación:
  - ISAI art. 113 CCF-CDMX (G.O. 19-dic-2025): $2M → $98,185 (4.91%);
    efectivo en las medianas 5.1%–5.4%; base = mayor de precio/catastral (art. 116).
  - Predial art. 130 CCF-CDMX: **tarifa BIMESTRAL → anual ×6**, columna
    "porcentaje" ÷100; dto. 8% pago en enero. Cross-check: recaudación SAF
    2026 $28,133.8 M ÷ 2.4 M cuentas = $11.7k promedio → catastral promedio
    ~$1.63M con ×6 (sin ×6 daría $6.8M, imposible) → ×6 confirmado.
    Catastral ≈ 30–50% del precio (SAF) → predial ≈ 0.17%–0.34% del precio/año.
  - IVA: 0% compraventa (LIVA 9-II), 0% renta sin amueblar (20-II), 16% amueblada.
  - ISR venta exento ≤ 700,000 UDIS (art. 93 XIX, UDI 8.83 ≈ $6.18M).
  - ISR renta: deducción ciega 35% (art. 115) + tarifa anual art. 152 (Anexo 8
    RMF 2026) → 3.5%–9.2% de la renta bruta; **sin subsidio al empleo** (solo
    asalariados, Decreto DOF 01-05-2024).
  - Gastos de cierre (NO impuestos): banda 3%–7%; comisión 3%–5% aparte.
- Geometría: `data/raw/alcaldias_cdmx.geojson` (pkg `alcaldias`, datos.cdmx.gob.mx,
  16 polígonos EPSG:4326). Unión portales↔geo por nombre sin acentos.

**Pendiente SHF:** índice de precios (CSV abierto) vive detrás de Akamai y
bloquea descarga no-browser. Descarga manual → `data/raw/shf_indice.csv`; el
loader `src/shf.py` ya normaliza el CSV (esquema tolerante, encodings utf-8/
latin-1, alias de alcaldía sin acentos) y su gráfica aparecerá sola en el
dashboard cuando exista el archivo. Verificado con CSV sintético.

## Decisiones de diseño

- **Geografía → mapas, nunca barras:** cualquier dato con lugar (alcaldía, CP,
  colonia) se grafica como **mapa coroplético** con `geopandas` sobre
  `data/raw/alcaldias_cdmx.geojson` (preferencia explícita del usuario). Las
  barras por alcaldía son un error de diseño; reservarlas solo para series no
  geográficas (tiempo, categorías).

- **CP ≠ polígono:** en CDMX los CP son cuadras agrupadas; NO son contiguos.
  El nivel "CP real" se arma con: (a) colonia desde PADIM (campo `colony` cuando
  existe), (b) directorio SEPOMEX colonia↔CP, (c) agregación de manzanas INEGI.
  Nunca fusionar RUV (alcaldía) + portales (colonia) + censo (AGEB) sin el bridge.
- **Fechas:** cada corrida con `--refresh` guarda un snapshot
  `padim_cdmx_YYYYMMDD.csv.gz`; la serie de precios de portales se construye con
  tiempo, no se improvisa.
- **Escalas:** precios en pesos (MXN); renta mensual. `precio_m2 = precio/m²`.
- **Limpieza portales:** la G5 desagrega pero NO geodesica: `precio_mxn > 0`,
  quitar duplicados por `property_canonical_id` por snapshot, valores extremos
  por percentiles (3–97) en la gráfica, nunca borrar del panel crudo.

## Roadmap

0. ✅ Esqueleto + PADIM + SNIIV financiamientos + dashboard v0.
1. 🔶 SHF índice de precios (alcaldía, 2017–hoy): loader listo, falta el CSV
   manual (Akamai). Cuando esté, `shf_indices.png` entra al dashboard.
2. ✅ Cocina del nivel colonia/CP: SEPOMEX + CONAPO colonia (con CP) bajan y se
   cruzan; falta PADIM `colony` (hoy 100% nulo) y las manzanas INEGI.
3. ✅ Censo 2020 (manzanas/AGEB): población (etaria), vivienda (hacinamiento,
   servicios) por alcaldía/AGEB; cruce con marginación. Pendiente fino:
   ENIGH para ingresos y jóvenes/hogares unipersonales por colonia.
4. ✅ ENIGH (ingresos) + CONEVAL pobreza + INPC → asequibilidad (años de
   ingreso y % de hogares que cubren la cuota, por alcaldía). Pendiente fino:
   ENIGH no permite desagregar por alcaldía (muestra por entidad); el paso
   colonia/CP de pobreza e ingresos sigue sin fuente municipal/sub-municipal
   (CONEVAL solo entrega a nivel municipal ~ alcaldía para la CDMX).
5. ✅ **Dashboard interactivo** (`outputs/vivienda_cdmx_interactivo.html`):
   Plotly con JS inline (sin servidor), mapa con selector de 8 métricas,
   dispersión con selector de eje X y serie de financiamientos. Extra de esta
   sesión: **índices "dónde comprar"** (2 métricas más), **paleta turbine**,
   layout **bento** compacto y `docs/politica.md` + `docs/fuentes_adicionales.md`.
   Extra: **déficit/rezago habitacional** (`src/deficit.py`, mapa + estrés de la
   oferta) y **pase de color** turbine en ambos dashboards.
5b. 🔜 Tabla ordenable / filtros por alcaldía y drill-down colonia/CP (aún no).
6. Modelo hedónico y mix-adjusted una vez existan >4 snapshots de portales.
7. Suelo: valores unitarios SEDUVI vs precio de vivienda → *share de suelo*.

## Ejecutar

```bash
python main.py --refresh   # descarga + paneles + dashboard
python main.py             # usa caché
python scripts/make_notebook.py
```

## Ojo / deuda técnica
- PADIM cambia su modelo sin aviso (es proyecto joven): el shape de `/v1/properties`
  se verificó a ago-2026; si rompe, revisar `/openapi.json`.
- CuboAPI GetFinanciamiento devuelve anual aunque pidamos dimensión; detalle
  mensual vía CSVs mensuales de SNIIV (fuera de v1).
- `main.py` no crea git; queda pendiente `git init` para la cueva.