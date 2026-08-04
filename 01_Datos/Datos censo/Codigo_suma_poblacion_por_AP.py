"""
Suma de población ponderada por Área Protegida y anillo
==============================================================================
Este script corresponde al PASO 3 del proceso de cálculo de población en zonas
de influencia de las 97 Áreas Protegidas terrestres de Chile (SNASPE).

Prerequisito:
    Debe ejecutarse DESPUÉS del Paso 2 (02_interseccion_ponderacion.py).
    Requiere los archivos Manz_Ani_Xkm.shp generados en el Paso 2.

Objetivo:
    Para cada anillo (1km al 10km), agregar la población ponderada (PER_MZ_P)
    de todos los fragmentos de manzanas que pertenecen a cada AP, separando
    entre población urbana y rural según el campo TP_MZ.

Lógica de agregación:
    PER_MZ_TO = suma de PER_MZ_P para todos los fragmentos de la AP en el anillo
    PER_MZ_UR = suma de PER_MZ_P donde TP_MZ = "Urbano"
    PER_MZ_RU = suma de PER_MZ_P donde TP_MZ = "Rural"
    Verificación: PER_MZ_TO = PER_MZ_UR + PER_MZ_RU (siempre)

Flujo del proceso:
    Manz_Ani_Xkm.shp → Suma por NOMBRE_TOT y TP_MZ → Escritura en anillo
    → Exportar ordenado → Anillo_Xkm.shp

Output:
    03_Anillos/Anillo_1km.shp ... Anillo_10km.shp
        Un shapefile por anillo con 97 registros (uno por AP) y las columnas
        PER_MZ_TO, PER_MZ_UR y PER_MZ_RU con la población total, urbana y rural.

Requisitos:
    - ArcGIS Pro
    - Archivos Manz_Ani_Xkm.shp del Paso 2 (02_Intersect/)
    - Shapefiles de anillos originales del 1km al 10km
------------------------------------------------------------------------------
CÓMO USAR ESTE SCRIPT
------------------------------------------------------------------------------
1. Asegúrate de haber ejecutado primero los Pasos 1 y 2.
2. Reemplaza las rutas marcadas con ">>> REEMPLAZAR <<<".
3. Ejecuta el script en ArcGIS Pro.
4. Verifica que PER_MZ_TO = PER_MZ_UR + PER_MZ_RU para cada AP.
------------------------------------------------------------------------------
"""

import arcpy
import os
import time

arcpy.env.overwriteOutput = True

# ==============================================================================
# CONFIGURACIÓN DE ENTRADA Y SALIDA
# ==============================================================================

# INPUT — Carpeta con los shapefiles Manz_Ani_Xkm.shp del Paso 2.
# >>> REEMPLAZAR <
DIR_INTERSECT = r"C:\Users\valen\Desktop\Datos_censo_2024\Objetivo_01\Manzanas\Manzanas_metadata\Anillos\Anillos_v02\02_Intersect"

# INPUT — Carpeta con los shapefiles de anillos originales del 1km al 10km.
# Patrón esperado: Anillos_1km_clip.shp, Anillos_2km_clip.shp, etc.
# >>> REEMPLAZAR <
ANILLO_DIR = r"C:\Users\valen\Desktop\Fondecyt\areas_protegidas_totales_actualizadas-20251109T203707Z-1-001\Anillos\Anillos_consecutivos\Anillos_clip_modificacion"

# OUTPUT — Carpeta raíz. Debe ser la misma que se usó en los Pasos 1 y 2.
# >>> REEMPLAZAR <
SALIDA_BASE = r"C:\Users\valen\Desktop\Datos_censo_2024\Objetivo_01\Manzanas\Manzanas_metadata\Anillos\Anillos_v02"

# ==============================================================================
# PARÁMETROS DE PROCESAMIENTO
# ==============================================================================

# Sistema de referencia proyectado. EPSG 32719 = WGS 1984 UTM Zona 19S.
SR_UTM19S = arcpy.SpatialReference(32719)

# Prefijos de NOMBRE_TOT para derivar la categoría del Área Protegida.
CATEGORIAS_AP = {"PN": "Parque", "RN": "Reserva", "MN": "Monumento"}

# Orden estandarizado de columnas en el shapefile de salida.
ORDEN_COLUMNAS = [
    "NOMBRE_TOT", "NOMBRE_UNI", "REGION", "PROVINCIA", "COMUNA", "CATEGORIA",
    "DECRETO_VI", "ANIO_CREAC", "CAT_PREV", "CAMB_SUP",
    "AREA_HA", "PRIM_METR", "LONGITUD", "LATITUD",
    "ALT_MIN", "ALT_MAX", "ALT_MEAN", "ALT_MED", "ALT_STD",
    "PER_MZ_TO", "PER_MZ_UR", "PER_MZ_RU"
]

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

DIR_ANILLOS = os.path.join(SALIDA_BASE, "03_Anillos")
DIR_UTM     = os.path.join(SALIDA_BASE, "04_UTM_reproyectados")

for d in [DIR_ANILLOS, DIR_UTM]:
    if not os.path.exists(d):
        os.makedirs(d)

# ==============================================================================
# BUCLE PRINCIPAL — Suma de población por AP (1km al 10km)
# ==============================================================================

for km in range(1, 11):
    intersect_shp = os.path.join(DIR_INTERSECT, f"Manz_Ani_{km}km.shp")
    anillo_shp    = os.path.join(ANILLO_DIR, f"Anillos_{km}km_clip.shp")

    if not arcpy.Exists(intersect_shp):
        log(f"[AVISO] No encontrado: {intersect_shp}")
        continue

    log(f"\n{'=' * 60}")
    log(f"Procesando Anillo_{km}km")
    log(f"{'=' * 60}")

    # ── Acumular PER_MZ_P por NOMBRE_TOT separado por TP_MZ ──────────────────
    # Se recorre el intersect del Paso 2 y se suman los fragmentos de cada AP
    # en diccionarios separados por tipo (total, urbano, rural).
    pob_total  = {}
    pob_urbano = {}
    pob_rural  = {}

    with arcpy.da.SearchCursor(intersect_shp, ["NOMBRE_TOT", "TP_MZ", "PER_MZ_P"]) as cur:
        for nombre, tp_mz, per_mz_p in cur:
            per_mz_p = per_mz_p if per_mz_p else 0
            # Suma total: todos los fragmentos de la AP en este anillo
            pob_total[nombre]  = pob_total.get(nombre, 0) + per_mz_p
            # Suma por tipo: urbano o rural según TP_MZ de la manzana
            if tp_mz == "Urbano":
                pob_urbano[nombre] = pob_urbano.get(nombre, 0) + per_mz_p
            elif tp_mz == "Rural":
                pob_rural[nombre]  = pob_rural.get(nombre, 0)  + per_mz_p

    log(f"  APs con población acumulada: {len(pob_total)}")

    # ── Reproyectar anillo original a UTM 19S ─────────────────────────────────
    anillo_utm = os.path.join(DIR_UTM, f"Anillo_{km}km_UTM19S.shp")
    arcpy.management.Project(anillo_shp, anillo_utm, SR_UTM19S)

    campos = [f.name for f in arcpy.ListFields(anillo_utm)]

    # ── Agregar CATEGORIA derivada del prefijo de NOMBRE_TOT ──────────────────
    agregar_campo_si_no_existe(anillo_utm, "CATEGORIA", "TEXT", longitud=150)
    with arcpy.da.UpdateCursor(anillo_utm, ["NOMBRE_TOT", "CATEGORIA"]) as cur:
        for row in cur:
            nombre = row[0] if row[0] else ""
            row[1] = CATEGORIAS_AP.get(nombre[:2].upper(), "Sin categoría")
            cur.updateRow(row)

    # ── Agregar columnas de población y escribir valores acumulados ───────────
    # PER_MZ_TO: suma total (urbano + rural)
    # PER_MZ_UR: solo manzanas urbanas
    # PER_MZ_RU: solo manzanas rurales
    # Verificación: PER_MZ_TO = PER_MZ_UR + PER_MZ_RU siempre
    for campo in ["PER_MZ_TO", "PER_MZ_UR", "PER_MZ_RU"]:
        agregar_campo_si_no_existe(anillo_utm, campo, "DOUBLE")

    with arcpy.da.UpdateCursor(anillo_utm,
                               ["NOMBRE_TOT", "PER_MZ_TO", "PER_MZ_UR", "PER_MZ_RU"]) as cur:
        for row in cur:
            nombre = row[0]
            row[1] = round(pob_total.get(nombre, 0), 2)
            row[2] = round(pob_urbano.get(nombre, 0), 2)
            row[3] = round(pob_rural.get(nombre, 0), 2)
            cur.updateRow(row)

    # ── Exportar con orden de columnas estandarizado ──────────────────────────
    campos_existentes = [f.name for f in arcpy.ListFields(anillo_utm)
                         if f.type not in ("OID", "Geometry")]
    fm = arcpy.FieldMappings()
    for campo in ORDEN_COLUMNAS:
        if campo in campos_existentes:
            fmap = arcpy.FieldMap()
            fmap.addInputField(anillo_utm, campo)
            fm.addFieldMap(fmap)
        else:
            log(f"  [AVISO] Campo no encontrado en columnas: {campo}")

    salida_tmp = os.path.join(DIR_UTM, f"tmp_Anillo_{km}km.shp")
    arcpy.conversion.ExportFeatures(anillo_utm, salida_tmp, field_mapping=fm)

    SALIDA_ANI = os.path.join(DIR_ANILLOS, f"Anillo_{km}km.shp")
    arcpy.management.Sort(
        in_dataset=salida_tmp,
        out_dataset=SALIDA_ANI,
        sort_field=[["NOMBRE_TOT", "ASCENDING"]]
    )

    arcpy.management.Delete(anillo_utm)
    arcpy.management.Delete(salida_tmp)
    log(f"  ✓ Anillo_{km}km.shp guardado")

log(f"\n✓ PASO 3 COMPLETADO")
log(f"  Output: {DIR_ANILLOS}")
log(f"  Archivos generados: Anillo_1km.shp ... Anillo_10km.shp")
log(f"  Columnas clave: PER_MZ_TO, PER_MZ_UR, PER_MZ_RU")
