"""
Intersección y ponderación de población por anillo
==============================================================================
Este script corresponde al PASO 2 del proceso de cálculo de población en zonas
de influencia de las 97 Áreas Protegidas terrestres de Chile (SNASPE).

Prerequisito:
    Debe ejecutarse DESPUÉS del Paso 1 (01_preparacion_manzanas.py).
    Requiere el archivo Manzanas_v02.shp generado en el Paso 1.

Objetivo:
    Para cada anillo independiente (1km al 10km), cortar las manzanas censales
    y calcular qué fracción del área de cada manzana quedó dentro del anillo.
    La población se pondera proporcionalmente a esa fracción.

Lógica de ponderación:
    MZ_RATIO_P = MZ_HA_F / MZ_HA         (fracción del área dentro del anillo)
    PER_MZ_P   = PER_MZ × MZ_RATIO_P     (población proporcional al fragmento)

    Ejemplo: manzana de 200 ha con 400 personas, anillo corta 100 ha (50%)
    → PER_MZ_P = 400 × 0.5 = 200 personas en este anillo
    → La otra mitad (200 personas) queda en el anillo adyacente

Nota sobre MZ_HA:
    El área de referencia (MZ_HA) se obtiene del diccionario construido desde
    Manzanas_v02.shp, que contiene el área ORIGINAL completa calculada en el
    Paso 1 (ANTES de cualquier corte). Esto garantiza que MZ_RATIO_P sea
    una fracción real (0-1) y no ≈1.0 por error de orden de operaciones.

Flujo del proceso:
    Manzanas_v02 → Reproyección → Intersect por anillo → Cálculo de fracción
    → Ponderación de población → Shapefile de salida por anillo

Output:
    02_Intersect/Manz_Ani_1km.shp ... Manz_Ani_10km.shp
        Un shapefile por anillo con fragmentos de manzanas y población ponderada.

Columnas clave del output:
    MZ_HA      : Área total original de la manzana (hectáreas)
    MZ_HA_F    : Área del fragmento dentro del anillo (hectáreas)
    MZ_RATIO_P : Fracción del área dentro del anillo (0–1)
    MZ_PCT_P   : Porcentaje del área dentro del anillo (0–100)
    PER_MZ     : Población total de la manzana (sin ponderar)
    PER_MZ_P   : Población estimada en el fragmento (PER_MZ × MZ_RATIO_P)

Requisitos:
    - ArcGIS Pro
    - Manzanas_v02.shp (output del Paso 1)
    - Shapefiles de anillos del 1km al 10km
------------------------------------------------------------------------------
CÓMO USAR ESTE SCRIPT
------------------------------------------------------------------------------
1. Asegúrate de haber ejecutado primero el Paso 1.
2. Verifica que las rutas de MANZANAS_V02, ANILLO_DIR y SALIDA_BASE sean
   correctas y estén marcadas con ">>> REEMPLAZAR <<<".
3. Ejecuta el script en ArcGIS Pro.
4. Verifica que se generaron los 10 shapefiles Manz_Ani_Xkm.shp en 02_Intersect.
------------------------------------------------------------------------------
"""

import arcpy
import os
import time

arcpy.env.overwriteOutput = True

# ==============================================================================
# CONFIGURACIÓN DE ENTRADA Y SALIDA
# ==============================================================================

# INPUT — Manzanas_v02.shp generado en el Paso 1.
# Debe contener las columnas MZ_HA y PER_MZ con valores correctos.
# >>> REEMPLAZAR <
MANZANAS_V02 = r"C:\Users\valen\Desktop\Datos_censo_2024\Objetivo_01\Manzanas\Manzanas_metadata\Anillos\Anillos_v02\01_Manzanas\Manzanas_v02.shp"

# INPUT — Carpeta con los shapefiles de anillos del 1km al 10km.
# Patrón esperado: Anillos_1km_clip.shp, Anillos_2km_clip.shp, etc.
# >>> REEMPLAZAR <
ANILLO_DIR = r"C:\Users\valen\Desktop\Fondecyt\areas_protegidas_totales_actualizadas-20251109T203707Z-1-001\Anillos\Anillos_consecutivos\Anillos_clip_modificacion"

# OUTPUT — Carpeta raíz. Debe ser la misma que se usó en el Paso 1.
# >>> REEMPLAZAR <
SALIDA_BASE = r"C:\Users\valen\Desktop\Datos_censo_2024\Objetivo_01\Manzanas\Manzanas_metadata\Anillos\Anillos_v02"

# ==============================================================================
# PARÁMETROS DE PROCESAMIENTO
# ==============================================================================

# Sistema de referencia proyectado. EPSG 32719 = WGS 1984 UTM Zona 19S.
SR_UTM19S = arcpy.SpatialReference(32719)

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def log(msg):
    """Imprime un mensaje con timestamp para seguimiento del progreso."""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def agregar_campo_si_no_existe(capa, nombre, tipo, longitud=None):
    """Agrega un campo a la capa solo si no existe previamente."""
    if nombre not in [f.name for f in arcpy.ListFields(capa)]:
        if longitud:
            arcpy.management.AddField(capa, nombre, tipo, field_length=longitud)
        else:
            arcpy.management.AddField(capa, nombre, tipo)

# ==============================================================================
# RUTAS DE SALIDA
# ==============================================================================

DIR_INTERSECT = os.path.join(SALIDA_BASE, "02_Intersect")
DIR_UTM       = os.path.join(SALIDA_BASE, "04_UTM_reproyectados")

for d in [DIR_INTERSECT, DIR_UTM]:
    if not os.path.exists(d):
        os.makedirs(d)

# ==============================================================================
# PREPARACIÓN — Diccionario OID → {area_ha, per_mz}
# ==============================================================================
# Se reproyecta Manzanas_v02 a UTM 19S y se construye un diccionario que mapea
# el OID de cada manzana a su área original completa y su población total.
# Este diccionario se consulta en el bucle de intersect para calcular la fracción
# correcta sin depender del área del fragmento recortado.
# ==============================================================================

log("=" * 60)
log("PREPARACIÓN — Reproyectando manzanas y construyendo diccionario")
log("=" * 60)

MANZANAS_V02_UTM = os.path.join(DIR_UTM, "v02_int_Manzanas_UTM.shp")
arcpy.management.Project(MANZANAS_V02, MANZANAS_V02_UTM, SR_UTM19S)
log(f"✓ Manzanas reproyectadas: {arcpy.management.GetCount(MANZANAS_V02_UTM)[0]} registros")

oid_field = arcpy.Describe(MANZANAS_V02_UTM).OIDFieldName
oid_to_data = {}
with arcpy.da.SearchCursor(MANZANAS_V02_UTM, [oid_field, "MZ_HA", "PER_MZ"]) as cur:
    for oid, area_ha, per_mz in cur:
        oid_to_data[oid] = {
            "area_ha": area_ha if area_ha else 0,
            "per_mz":  per_mz  if per_mz  else 0
        }
log(f"✓ Diccionario construido: {len(oid_to_data)} manzanas")

# ==============================================================================
# BUCLE PRINCIPAL — Intersección por anillo (1km al 10km)
# ==============================================================================

for km in range(1, 11):
    anillo_shp = os.path.join(ANILLO_DIR, f"Anillos_{km}km_clip.shp")
    if not arcpy.Exists(anillo_shp):
        log(f"[AVISO] No encontrado: {anillo_shp}")
        continue

    log(f"\n{'=' * 60}")
    log(f"Procesando anillo {km}km")
    log(f"{'=' * 60}")
    t0 = time.time()

    # ── Reproyectar anillo a UTM 19S ──────────────────────────────────────────
    anillo_utm = os.path.join(DIR_UTM, f"int_Anillo_{km}km_UTM19S.shp")
    arcpy.management.Project(anillo_shp, anillo_utm, SR_UTM19S)

    # ── Intersect: cortar manzanas con el anillo ──────────────────────────────
    # Genera un fragmento por cada manzana que intersecta el anillo,
    # conservando todos los atributos de ambas capas (manzanas + anillo).
    intersect_tmp = os.path.join(DIR_UTM, f"tmp_Manz_Ani_{km}km.shp")
    arcpy.analysis.Intersect(
        in_features=[MANZANAS_V02_UTM, anillo_utm],
        out_feature_class=intersect_tmp,
        join_attributes="ALL"
    )
    log(f"  Intersect completado en {time.time()-t0:.1f}s — {arcpy.management.GetCount(intersect_tmp)[0]} fragmentos")

    # ── Calcular MZ_HA_F: área del fragmento dentro del anillo ───────────────
    agregar_campo_si_no_existe(intersect_tmp, "MZ_HA_F", "DOUBLE")
    arcpy.management.CalculateGeometryAttributes(
        intersect_tmp, [["MZ_HA_F", "AREA"]], area_unit="HECTARES"
    )

    # ── Detectar campo FID de manzanas en el resultado del intersect ──────────
    # ArcGIS nombra este campo automáticamente como FID_<nombre_capa>.
    campos_i = [f.name for f in arcpy.ListFields(intersect_tmp)]
    oid_ref = None
    for c in campos_i:
        if c.upper().startswith("FID_") and "MANZ" in c.upper():
            oid_ref = c
            break
    if not oid_ref:
        for c in campos_i:
            if c.upper().startswith("FID_") and "ANI" not in c.upper():
                oid_ref = c
                break
    log(f"  Campo OID manzanas detectado: {oid_ref}")

    # ── Agregar campos de fracción y población ponderada ──────────────────────
    for campo, tipo in [("FID_MZ",    "INTEGER"),
                        ("MZ_RATIO_P","DOUBLE"),
                        ("MZ_PCT_P",  "DOUBLE"),
                        ("PER_MZ_P",  "DOUBLE")]:
        agregar_campo_si_no_existe(intersect_tmp, campo, tipo)

    # ── Calcular fracción y población ponderada ───────────────────────────────
    # Para cada fragmento se consulta el diccionario para obtener el área
    # ORIGINAL completa de la manzana (no el área del fragmento), garantizando
    # que MZ_RATIO_P sea la fracción real y no ≈1.0 por error.
    with arcpy.da.UpdateCursor(intersect_tmp,
                               [oid_ref, "MZ_HA_F", "FID_MZ",
                                "MZ_RATIO_P", "MZ_PCT_P", "PER_MZ_P"]) as cur:
        for row in cur:
            oid_orig  = row[0]   # OID de la manzana original
            area_frag = row[1]   # Área del fragmento dentro del anillo (ha)

            if oid_orig in oid_to_data:
                area_orig = oid_to_data[oid_orig]["area_ha"]  # Área completa original
                per_mz    = oid_to_data[oid_orig]["per_mz"]   # Población total
                fraccion  = min(area_frag / area_orig, 1.0) if area_orig > 0 else 0
            else:
                fraccion = 0
                per_mz   = 0

            row[2] = oid_orig                    # FID_MZ: referencia al OID original
            row[3] = round(fraccion, 6)          # MZ_RATIO_P: fracción (0–1)
            row[4] = round(fraccion * 100, 2)    # MZ_PCT_P: porcentaje (0–100)
            row[5] = round(per_mz * fraccion, 2) # PER_MZ_P: población ponderada
            cur.updateRow(row)

    # ── Exportar con orden de columnas estandarizado ──────────────────────────
    campos_existentes = [f.name for f in arcpy.ListFields(intersect_tmp)
                         if f.type not in ("OID", "Geometry")]

    fm = arcpy.FieldMappings()

    def add_fm(src, campo_in, campo_out=None):
        """Agrega un campo al FieldMappings, con renombrado opcional."""
        if campo_in not in campos_existentes:
            return
        fmap = arcpy.FieldMap()
        fmap.addInputField(src, campo_in)
        if campo_out:
            f = fmap.outputField
            f.name = campo_out
            fmap.outputField = f
        fm.addFieldMap(fmap)

    # Bloque común AP (sufijo _1 por el intersect en campos del anillo)
    add_fm(intersect_tmp, "NOMBRE_TOT")
    add_fm(intersect_tmp, "NOMBRE_T_1", "NOMBRE_UNI") if "NOMBRE_T_1" in campos_existentes else add_fm(intersect_tmp, "NOMBRE_UNI")
    add_fm(intersect_tmp, "REGION_1",   "REGION")     if "REGION_1"   in campos_existentes else add_fm(intersect_tmp, "REGION")
    add_fm(intersect_tmp, "PROVINCI_1", "PROVINCIA")  if "PROVINCI_1" in campos_existentes else add_fm(intersect_tmp, "PROVINCIA")
    add_fm(intersect_tmp, "COMUNA_1",   "COMUNA")     if "COMUNA_1"   in campos_existentes else add_fm(intersect_tmp, "COMUNA")
    add_fm(intersect_tmp, "CATEGORIA")
    add_fm(intersect_tmp, "DECRETO_VI")
    add_fm(intersect_tmp, "ANIO_CREAC")
    add_fm(intersect_tmp, "CAT_PREV")
    add_fm(intersect_tmp, "CAMB_SUP")
    add_fm(intersect_tmp, "AREA_HA")
    add_fm(intersect_tmp, "PRIM_METR")
    add_fm(intersect_tmp, "LONGITUD")
    add_fm(intersect_tmp, "LATITUD")
    add_fm(intersect_tmp, "ALT_MIN")
    add_fm(intersect_tmp, "ALT_MAX")
    add_fm(intersect_tmp, "ALT_MEAN")
    add_fm(intersect_tmp, "ALT_MED")
    add_fm(intersect_tmp, "ALT_STD")
    # Atributos de manzana y ponderación
    add_fm(intersect_tmp, "TP_MZ")
    add_fm(intersect_tmp, "SUB_TP_MZ")
    add_fm(intersect_tmp, "MZ_HA")
    add_fm(intersect_tmp, "MZ_PERI")
    add_fm(intersect_tmp, "PER_MZ")
    add_fm(intersect_tmp, "FID_MZ")
    add_fm(intersect_tmp, "MZ_HA_F")
    add_fm(intersect_tmp, "MZ_RATIO_P")
    add_fm(intersect_tmp, "MZ_PCT_P")
    add_fm(intersect_tmp, "PER_MZ_P")

    salida_sin_orden = os.path.join(DIR_UTM, f"tmp_export_{km}km.shp")
    arcpy.conversion.ExportFeatures(intersect_tmp, salida_sin_orden, field_mapping=fm)

    SALIDA_INT = os.path.join(DIR_INTERSECT, f"Manz_Ani_{km}km.shp")
    arcpy.management.Sort(
        in_dataset=salida_sin_orden,
        out_dataset=SALIDA_INT,
        sort_field=[["NOMBRE_TOT", "ASCENDING"]]
    )

    arcpy.management.Delete(intersect_tmp)
    arcpy.management.Delete(anillo_utm)
    arcpy.management.Delete(salida_sin_orden)
    log(f"  ✓ Manz_Ani_{km}km.shp guardado")

log(f"\n✓ PASO 2 COMPLETADO")
log(f"  Output: {DIR_INTERSECT}")
log(f"  Siguiente paso: ejecutar 03_suma_poblacion_por_ap.py")
