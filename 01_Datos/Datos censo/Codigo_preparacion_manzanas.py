"""
Preparación de manzanas censales para análisis de población en APs
==============================================================================
Este script corresponde al PASO 1 del proceso de cálculo de población en zonas
de influencia de las 97 Áreas Protegidas terrestres de Chile (SNASPE).

Objetivo:
    Seleccionar las manzanas y entidades censales (CPV 2024) que se encuentran
    dentro del área de influencia de las APs, calcular su área original completa
    en hectáreas (MZ_HA) y enriquecerlas con atributos del AP más cercano
    mediante un spatial join.

¿Por qué calcular el área antes de cualquier corte?
    Si primero cortamos la manzana y luego medimos su área, obtenemos el área
    del fragmento recortado en lugar del área total original. Esto haría que la
    fracción de ponderación (MZ_RATIO_P = MZ_HA_F / MZ_HA) sea incorrecta
    (siempre ≈ 1.0), asignando la población completa a cada fragmento en lugar
    de la parte proporcional que corresponde.

¿Por qué usar SelectLayerByLocation en lugar de Clip?
    SelectLayerByLocation selecciona las manzanas que tocan el área de influencia
    sin recortar su geometría, preservando las manzanas completas para que el
    cálculo de fracción en el Paso 2 sea correcto.

Flujo del proceso:
    Manzanas CPV24 → Reproyección UTM 19S → Cálculo MZ_HA completa
    → Filtro espacial (sin clip) → Spatial Join con AP → Shapefile de salida

Output:
    01_Manzanas/Manzanas_v02.shp
        Manzanas seleccionadas con atributos del AP asignado y área original.

Requisitos:
    - ArcGIS Pro
    - Shapefile de manzanas y entidades censales CPV 2024 (INE)
    - Shapefile del buffer de 10km (usado solo como máscara de filtro)
    - Permisos de escritura en la carpeta de salida

Nota:
    Este script debe ejecutarse ANTES del Paso 2 (02_interseccion_ponderacion.py).
    El archivo Manzanas_v02.shp generado aquí es la entrada del Paso 2.
------------------------------------------------------------------------------
CÓMO USAR ESTE SCRIPT
------------------------------------------------------------------------------
1. Revisa la sección "CONFIGURACIÓN DE ENTRADA Y SALIDA" más abajo.
2. Reemplaza las rutas marcadas con ">>> REEMPLAZAR <<<" con tus propias rutas.
3. Ejecuta el script en ArcGIS Pro (Python Window o herramienta de script).
4. Verifica que el output Manzanas_v02.shp tenga 0 registros sin NOMBRE_TOT.
------------------------------------------------------------------------------
"""

import arcpy
import os
import time

arcpy.env.overwriteOutput = True

# ==============================================================================
# CONFIGURACIÓN DE ENTRADA Y SALIDA
# ==============================================================================

# INPUT — Shapefile de manzanas y entidades censales CPV 2024 (INE).
# Columnas requeridas: n_per, TIPO_MZ, CATEGORIA (censal).
# >>> REEMPLAZAR <
MANZANAS_ORIG = r"C:\Users\valen\Desktop\Datos_censo_2024\Objetivo_01\Manzanas\Manzanas_metadata\Manzanas_opcion_02\Manzanas_Entidades_CPV24_urbano_rural.shp"

# INPUT — Shapefile del buffer de 10km. Se usa solo como máscara de filtro
# espacial, no para recortar geometría. Debe contener la columna NOMBRE_TOT.
# >>> REEMPLAZAR <
BUFFER_10K = r"C:\Users\valen\Desktop\Fondecyt\areas_protegidas_totales_actualizadas-20251109T203707Z-1-001\Buffer\Buffer_consecutivos\Buffer_clip\Buffer_clip_modificacion_v6\Buffer_10km_clip.shp"

# OUTPUT — Carpeta raíz de salida. Se crearán subcarpetas automáticamente.
# >>> REEMPLAZAR <
SALIDA_BASE = r"C:\Users\valen\Desktop\Datos_censo_2024\Objetivo_01\Manzanas\Manzanas_metadata\Anillos\Anillos_v02"

# ==============================================================================
# PARÁMETROS DE PROCESAMIENTO
# ==============================================================================

# Sistema de referencia proyectado. EPSG 32719 = WGS 1984 UTM Zona 19S.
SR_UTM19S = arcpy.SpatialReference(32719)

# Categorías censales de entidades clasificadas como RURAL (CPV 2024, INE).
CATEGORIAS_RURAL = {
    "Asentamiento Minero", "Asentamiento Pesquero", "Veranada-Majada-Aguada",
    "Parcela de Agrado", "Comunidad Indígena", "Fundo-Estancia-Hacienda",
    "Caserío", "Indeterminada", "Parcela-Hijuela", "Otros"
}

# Categorías censales de entidades clasificadas como URBANO.
CATEGORIAS_URBANO = {"Pueblo", "Ciudad"}

# Equivalencias del campo TIPO_MZ a etiquetas estandarizadas.
# ALDEA se clasifica como Rural por corresponder a localidades rurales pequeñas.
MAPEO_TIPO_MZ = {"URBANO": "Urbano", "ALDEA": "Rural", "RURAL": "Rural"}

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

DIR_MANZANAS = os.path.join(SALIDA_BASE, "01_Manzanas")
DIR_UTM      = os.path.join(SALIDA_BASE, "04_UTM_reproyectados")

for d in [SALIDA_BASE, DIR_MANZANAS, DIR_UTM]:
    if not os.path.exists(d):
        os.makedirs(d)

# ==============================================================================
# PASO 1A — Reproyectar manzanas a UTM 19S
# ==============================================================================
# Las áreas no pueden calcularse correctamente en coordenadas geográficas (grados).
# Se reproyecta toda la capa nacional antes de cualquier operación.
# ==============================================================================

log("=" * 60)
log("PASO 1A — Reproyectando manzanas a UTM 19S")
log("=" * 60)

MANZANAS_UTM_ORIG = os.path.join(DIR_UTM, "v02_ani4_Manzanas_orig_UTM19S.shp")
t0 = time.time()
arcpy.management.Project(MANZANAS_ORIG, MANZANAS_UTM_ORIG, SR_UTM19S)
log(f"✓ Reproyectado en {time.time()-t0:.1f}s — {arcpy.management.GetCount(MANZANAS_UTM_ORIG)[0]} registros")

# ==============================================================================
# PASO 1B — Calcular MZ_HA y MZ_PERI sobre geometría COMPLETA
# ==============================================================================
# Este es el paso crítico: el área se mide sobre la manzana original completa,
# no sobre un fragmento recortado. MZ_HA siempre representa el 100% del área
# de la manzana, independientemente de cuánto caiga dentro de cada zona.
# ==============================================================================

log("\nPASO 1B — Calculando MZ_HA y MZ_PERI sobre geometría completa")
agregar_campo_si_no_existe(MANZANAS_UTM_ORIG, "MZ_HA",   "DOUBLE")
agregar_campo_si_no_existe(MANZANAS_UTM_ORIG, "MZ_PERI", "DOUBLE")
arcpy.management.CalculateGeometryAttributes(
    MANZANAS_UTM_ORIG,
    [["MZ_HA", "AREA"], ["MZ_PERI", "PERIMETER_LENGTH"]],
    area_unit="HECTARES",
    length_unit="METERS"
)
log("✓ MZ_HA y MZ_PERI calculados sobre geometría original")

# ==============================================================================
# PASO 1C — Filtrar manzanas por proximidad al área de influencia
# ==============================================================================
# SelectLayerByLocation selecciona manzanas que intersectan el buffer de 10km
# SIN recortar su geometría. Esto preserva las manzanas completas para que
# el cálculo de fracción en el Paso 2 sea correcto.
# ==============================================================================

log("\nPASO 1C — Filtrando manzanas dentro del área de influencia")
BUFFER_UTM = os.path.join(DIR_UTM, "v02_ani4_Buffer10km_UTM19S.shp")
arcpy.management.Project(BUFFER_10K, BUFFER_UTM, SR_UTM19S)
log("Buffer 10km reproyectado a UTM 19S")

t0 = time.time()
manzanas_lyr = arcpy.management.MakeFeatureLayer(MANZANAS_UTM_ORIG, "manzanas_lyr")
arcpy.management.SelectLayerByLocation(
    in_layer=manzanas_lyr,
    overlap_type="INTERSECT",
    select_features=BUFFER_UTM
)
MANZANAS_FILTRADAS = os.path.join(DIR_UTM, "v02_ani4_Manzanas_filtradas.shp")
arcpy.management.CopyFeatures(manzanas_lyr, MANZANAS_FILTRADAS)
log(f"✓ Filtrado en {time.time()-t0:.1f}s — {arcpy.management.GetCount(MANZANAS_FILTRADAS)[0]} manzanas seleccionadas (geometría sin recortar)")

# ==============================================================================
# PASO 1D — Spatial join con buffer 10km para asignar atributos del AP
# ==============================================================================
# Cada manzana recibe los atributos del AP con el que tiene mayor solapamiento
# (LARGEST_OVERLAP): NOMBRE_TOT, CATEGORIA, REGION, PROVINCIA, etc.
# ==============================================================================

log("\nPASO 1D — Spatial join para asignar atributos del AP a cada manzana")
t0 = time.time()
JOIN_OUT = os.path.join(DIR_UTM, "v02_ani4_Manzanas_join.shp")
arcpy.analysis.SpatialJoin(
    target_features=MANZANAS_FILTRADAS,
    join_features=BUFFER_UTM,
    out_feature_class=JOIN_OUT,
    join_operation="JOIN_ONE_TO_ONE",
    join_type="KEEP_ALL",
    match_option="LARGEST_OVERLAP"
)
log(f"✓ Join completado en {time.time()-t0:.1f}s — {arcpy.management.GetCount(JOIN_OUT)[0]} registros")

count_null = sum(1 for row in arcpy.da.SearchCursor(JOIN_OUT, ["NOMBRE_TOT"]) if not row[0])
log(f"  Manzanas sin NOMBRE_TOT asignado: {count_null} (debe ser 0)")

# ==============================================================================
# PASO 1E — Calcular campos derivados
# ==============================================================================

log("\nPASO 1E — Calculando campos derivados")

# TP_MZ: tipo de manzana (Urbano/Rural). Se deriva de TIPO_MZ para manzanas
# censales y de CATEGORIA censal para entidades (que no tienen TIPO_MZ).
agregar_campo_si_no_existe(JOIN_OUT, "TP_MZ", "TEXT", longitud=10)
with arcpy.da.UpdateCursor(JOIN_OUT, ["TIPO_MZ", "CATEGORIA", "TP_MZ"]) as cur:
    for row in cur:
        tipo_mz   = (row[0] or "").strip().upper()
        categoria = (row[1] or "").strip()
        if tipo_mz in MAPEO_TIPO_MZ:
            row[2] = MAPEO_TIPO_MZ[tipo_mz]
        elif categoria in CATEGORIAS_RURAL:
            row[2] = "Rural"
        elif categoria in CATEGORIAS_URBANO:
            row[2] = "Urbano"
        else:
            row[2] = "Sin dato"
        cur.updateRow(row)
log("  ✓ TP_MZ calculado (Urbano/Rural)")

# PER_MZ: población total de la manzana, directamente del campo n_per del censo.
# Este valor NO se pondera aquí — la ponderación ocurre en el Paso 2.
agregar_campo_si_no_existe(JOIN_OUT, "PER_MZ", "DOUBLE")
arcpy.management.CalculateField(JOIN_OUT, "PER_MZ", "!n_per!", "PYTHON3")
log("  ✓ PER_MZ calculado (población total sin ponderar)")

# SUB_TP_MZ: subtipo censal de la manzana (ej: Caserío, Ciudad, Parcela, etc.)
agregar_campo_si_no_existe(JOIN_OUT, "SUB_TP_MZ", "TEXT", longitud=254)
arcpy.management.CalculateField(JOIN_OUT, "SUB_TP_MZ", "!CATEGORIA!", "PYTHON3")
log("  ✓ SUB_TP_MZ calculado (subtipo censal)")

# ==============================================================================
# PASO 1F — Exportar con orden de columnas estandarizado
# ==============================================================================

log("\nPASO 1F — Exportando Manzanas_v02.shp con columnas estandarizadas")

fm = arcpy.FieldMappings()
campos_join = [f.name for f in arcpy.ListFields(JOIN_OUT)]

def add_field(src, campo_in, campo_out=None):
    """Agrega un campo al FieldMappings, con renombrado opcional."""
    if campo_in not in [f.name for f in arcpy.ListFields(src)]:
        log(f"  [AVISO] Campo no encontrado: {campo_in}")
        return
    fmap = arcpy.FieldMap()
    fmap.addInputField(src, campo_in)
    if campo_out:
        f = fmap.outputField
        f.name = campo_out
        fmap.outputField = f
    fm.addFieldMap(fmap)

# Bloque común: atributos del Área Protegida
add_field(JOIN_OUT, "NOMBRE_TOT")
add_field(JOIN_OUT, "NOMBRE_UNI")
add_field(JOIN_OUT, "REGION_1",   "REGION")    if "REGION_1"   in campos_join else add_field(JOIN_OUT, "REGION")
add_field(JOIN_OUT, "PROVINCI_1", "PROVINCIA") if "PROVINCI_1" in campos_join else add_field(JOIN_OUT, "PROVINCIA")
add_field(JOIN_OUT, "COMUNA_1",   "COMUNA")    if "COMUNA_1"   in campos_join else add_field(JOIN_OUT, "COMUNA")
add_field(JOIN_OUT, "CATEGORI_1", "CATEGORIA") if "CATEGORI_1" in campos_join else add_field(JOIN_OUT, "CATEGORIA")
add_field(JOIN_OUT, "DECRETO_VI")
add_field(JOIN_OUT, "ANIO_CREAC")
add_field(JOIN_OUT, "CAT_PREV")
add_field(JOIN_OUT, "CAMB_SUP")
add_field(JOIN_OUT, "AREA_HA")
add_field(JOIN_OUT, "PRIM_METR")
add_field(JOIN_OUT, "LONGITUD")
add_field(JOIN_OUT, "LATITUD")
add_field(JOIN_OUT, "ALT_MIN")
add_field(JOIN_OUT, "ALT_MAX")
add_field(JOIN_OUT, "ALT_MEAN")
add_field(JOIN_OUT, "ALT_MED")
add_field(JOIN_OUT, "ALT_STD")
# Atributos de la manzana censal
add_field(JOIN_OUT, "TP_MZ")
add_field(JOIN_OUT, "SUB_TP_MZ")
add_field(JOIN_OUT, "MZ_HA")
add_field(JOIN_OUT, "MZ_PERI")
add_field(JOIN_OUT, "PER_MZ")

# Exportar y ordenar alfabéticamente por NOMBRE_TOT
salida_tmp = os.path.join(DIR_MANZANAS, "Manzanas_v02_tmp.shp")
SALIDA_MNZ = os.path.join(DIR_MANZANAS, "Manzanas_v02.shp")
arcpy.conversion.ExportFeatures(JOIN_OUT, salida_tmp, field_mapping=fm)
arcpy.management.Sort(
    in_dataset=salida_tmp,
    out_dataset=SALIDA_MNZ,
    sort_field=[["NOMBRE_TOT", "ASCENDING"]]
)
arcpy.management.Delete(salida_tmp)

log(f"\n✓ PASO 1 COMPLETADO")
log(f"  Output: {SALIDA_MNZ}")
log(f"  Registros: {arcpy.management.GetCount(SALIDA_MNZ)[0]}")
log(f"  Siguiente paso: ejecutar 02_interseccion_ponderacion.py")
