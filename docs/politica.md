# Política de vivienda basada en los índices

Documento de trabajo: traduce el diagnóstico del monitor en instrumentos
concretos. Los pesos y definiciones de los índices están en `src/indices.py`;
las fuentes y huecos en `docs/precios_causas.md` y `docs/fuentes_adicionales.md`.

## Diagnóstico que ordena la política

1. **Compra cara y lenta de alcanzar.** La vivienda mediana cuesta ~11–12.5 años
   del ingreso del hogar (ENIGH 2022 → 2026); el 90% financiado a 20 años exige
   más del 100% del ingreso mensual en Coyoacán y Benito Juárez.
2. **Impuestos regresivos sobre el precio.** ISAI 5.1–5.4% al comprar + predial
   0.23–0.26%/año. En 10 años, ISAI + predial ≈ 7.9% del precio de la vivienda.
3. **Especulación y uso turístico.** La vacancia sube con el precio (ρ=+0.55) y
   Airbnb se correlaciona con ella (ρ=+0.57) y con el uso temporal (ρ=+0.67).
   Son descriptivos, no causales, pero apuntan a un mismo mecanismo.
4. **Brecha centro–periferia.** La calidad de vida sin precio cae de 100 (BJ) a
   7.7 (Xochimilco); la marginación alta se concentra en Xochimilco (16.5%),
   Milpa Alta (15.9%) y Tlalpan (11.0%). No es solo precio: es acceso a
   servicios y oportunidad.

## Índices como semáforo de intervención

- **`indice_oportunidad`** (precio + asequibilidad + servicios; 8 alcaldías con
  portales): 1) Benito Juárez 61.4, 2) Cuajimalpa 59.4, 3) Coyoacán 58.7;
  menos atractiva: Xochimilco 43.7 y Tlalpan 44.8.
- **`indice_calidad`** (servicios + marginación + pobreza; 16 alcaldías):
  1) Benito Juárez 100, 2) Miguel Hidalgo 92.9, 3) Cuauhtémoc 90.7;
  peores: Xochimilco 7.7, Milpa Alta 14.2, Tlalpan 43.4.

Dos lecturas cruzadas:

- **Alta calidad + precio alcanzable** (Cuajimalpa, Coyoacán, Álvaro Obregón):
  ahí conviene *fomentar oferta asequible* porque el capital humano y los
  servicios ya existen y el precio es la barrera.
- **Baja calidad + baja oportunidad** (Xochimilco, Milpa Alta, Tlalpan):
  ahí la prioridad es *mejorar servicios y equipamiento*, no subsidiar compra.

## Instrumentos sugeridos

### 1. Desincentivar el uso especulativo y turístico
- Gravar la **vivienda desocupada** y el **uso temporal** con sobretasa al
  predial en zonas tensionadas (Cuauhtémoc, Miguel Hidalgo), medida que la
  correlación con el precio hace presumible pero que requiere datos de renta
  para validarse.
- Limitar licencias de **renta corta** (Airbnb) por colonia y exigir registro,
  con cuota que financie vivienda social.
- **Indicador de éxito**: reducción de `vac_pct` y `uso_temporal_pct` en el
  monitor.

### 2. Hacer la compra menos regresiva
- Suavizar el **ISAI** para primera vivienda de interés social/bajo ingreso
  (crédito, diferimiento o exención) y mantener la carga en segmentos altos.
- Mantener el **predial progresivo** pero con la **base catastral actualizada**
  (hoy ≈ 40% del precio de mercado): sin actualización, el impuesto es
  inequitativo y no captura plusvalía.
- **Indicador de éxito**: `anios_ingreso` y `pct_ingreso_mensual` a la baja en
  las alcaldías de menor ingreso.

### 3. Aumentar la oferta donde hay demanda y servicios
- En Cuajimalpa, Coyoacán y Álvaro Obregón: **vivienda incluyente** (cuota de
  unidades asequibles en desarrollo nuevo), suelo público y liberación ágil de
  permisos. La inelasticidad de la oferta es el cuello de botella: +10% de
  inventario ≈ −5% a −11% de precio en escenarios de elasticidad estándar.
- **Indicador de éxito**: nuevas unidades por alcaldía y brecha de oferta.

### 4. Cerrar la brecha de calidad en el sur
- En Xochimilco, Milpa Alta y Tlalpan: agua, drenaje, piso firme, equipamiento y
  transporte antes que subsidio a la compra; ahí el problema es de servicios.
- **Indicador de éxito**: subir `indice_calidad` y bajar marginación alta.

### 5. Transparencia de datos
- Publicar **permisos de obra** (SEDUVI) y **rentas** observadas; hoy son los
  dos huecos que más limitan evaluar la política (ver
  `docs/fuentes_adicionales.md`).

## Nota metodológica

Los índices son **relativos a la CDMX**, con pesos editoriales explícitos; no
son una medida absoluta de calidad ni un ranking normativo. Las correlaciones
son descriptivas y no establecen causalidad. Cualquier instrumento de política
debe evaluarse con datos de renta y de permisos que aún no están integrados.
