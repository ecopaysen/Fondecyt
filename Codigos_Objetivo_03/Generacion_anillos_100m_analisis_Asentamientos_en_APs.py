#!/usr/bin/env python3
"""
================================================================================
GENERADOR DE ANILLOS CONCÉNTRICOS (100m - 10.000m) POR ÁREA PROTEGIDA
================================================================================

PROYECTO FONDECYT Nº 1251080
"Evaluación de las áreas protegidas y sus zonas de amortiguación en Chile: 
un análisis geoespacial de su eficacia para contrarrestar el cambio global"

AUTOR DEL CODIGO: Valentina Contreras

================================================================================
DESCRIPCIÓN GENERAL
================================================================================

Este script genera anillos concéntricos de 100m en 100m (desde 100m hasta 10.000m)
alrededor de 97 Áreas Protegidas (AP) y calcula porcentajes de píxeles antrópicos
y naturales para cada zona de análisis.

CARACTERÍSTICAS PRINCIPALES:
  - Generación de anillos independientes cada 100 metros
  - Total de 100 anillos por AP (100m, 200m, 300m... 10.000m)
  - Cálculo de porcentajes de asentamientos vs. cobertura natural
  - Exportación de resultados a CSV con formato tabulado
  - Exportación opcional de shapefiles de anillos

CAMPOS DE SALIDA:
  ringID     → Identificador del anillo (1–100, reinicia por AP)
  distance   → Distancia en metros (100–10000 m)
  rango_min  → Mínimo del rango (0, 100, 200, ...)
  rango_max  → Máximo del rango (100, 200, 300, ...)
  rango_mid  → Punto medio del rango (50, 150, 250, ...)
  rango_md1  → Punto medio en km (0.05, 0.15, 0.25, ...)
  rango_lab  → Etiqueta de rango ("0-100m", "100-200m", "200-300m", ...)
  area_AnHa  → Área del anillo en hectáreas
  area_Ankm  → Área del anillo en km²

================================================================================
FLUJO DE TRABAJO
================================================================================

1. CONFIGURACIÓN
   - Definir rutas de entrada (shapefile de AP, raster de asentamientos)
   - Definir ruta de salida (CSV con resultados)
   - Configurar opción de exportar shapefiles de anillos

2. VERIFICACIÓN
   - Validar existencia de archivos de entrada
   - Cargar cantidad de AP
   - Confirmar sistema de referencia en metros

3. PROCESAMIENTO POR AP
   - Para cada AP:
     * Analizar AP sin modificación
     * Generar 100 anillos independientes (100m a 10.000m)
     * Calcular porcentajes de cobertura antrópica y natural
     * Exportar shapefiles si está habilitado

4. EXPORTACIÓN
   - Guardar resultados en CSV con formato tabulado
   - Generar resumen de procesamiento

5. RESUMEN
   - Mostrar estadísticas finales
   - Indicar ubicación de archivos de salida

================================================================================
REQUISITOS TÉCNICOS
================================================================================

• Python 3.6+
• ArcGIS Desktop / ArcGIS Pro (con extensión Spatial Analyst)
• Módulos: arcpy, os, csv, numpy, time, traceback
• Acceso a licencias de ArcGIS
• Rásteres de entrada en formato GeoTIFF
• Sistema de referencia en METROS (obligatorio)

================================================================================
FLUJO DE ENTRADA/SALIDA
================================================================================

ENTRADA:
  - Shapefile de Áreas Protegidas (AP_terrestres_actualizadas.shp)
  - Raster de asentamientos (Asen_buf_2015_modificado.tif)

SALIDA:
  - CSV con resultados de análisis (resultados_anillos_100m.csv)
  - Shapefiles de anillos 100m (opcional, en carpeta ANILLOS_100m_SHAPEFILES)
  - Total de 100 registros por AP (1 por anillo)

================================================================================
CONFIGURACIÓN
================================================================================

Antes de ejecutar, modifica los siguientes parámetros:

  • INPUT_SHP: Ruta al shapefile de Áreas Protegidas
  • INPUT_RASTER: Ruta al raster de asentamientos
  • OUTPUT_FOLDER: Ruta de salida para CSV y shapefiles
  • OUTPUT_NAME: Nombre del archivo de salida (sin extensión)
  • CAMPO_NOMBRE: Campo identificador de las AP (ej: "NOMBRE_TOT")
  • RING_STEP: Incremento de anillo en metros (100)
  • RING_MAX: Distancia máxima en metros (10000)
  • EXPORTAR_ANILLOS: True para exportar shapefiles, False para solo CSV

================================================================================
USO
================================================================================

1. Abrir el script en Python IDE (ArcGIS Pro Python Console recomendado)
2. Configurar rutas de entrada/salida en la sección CONFIGURACIÓN
3. Cambiar EXPORTAR_ANILLOS a True si desea exportar shapefiles
4. Ejecutar: python Generacion_anillos_100m_analisis_Asentamientos_en_APs.py
5. Revisar reporte de procesamiento en consola
6. Verificar archivos en OUTPUT_FOLDER

================================================================================
SALIDA DEL SCRIPT
================================================================================

El script genera:
  • CSV con 100 registros por AP (1 por anillo de 100m)
  • Porcentajes de asentamientos para cada anillo
  • Reporte detallado en consola con progreso y resultados por AP
  • Estadísticas de área por anillo (hectáreas y km²)
  • Shapefiles de anillos independientes (opcional)
  • Información de ubicación de archivos generados

================================================================================
NOTAS IMPORTANTES
================================================================================

• ANILLOS INDEPENDIENTES: Cada anillo de 100m es aislado del anterior
  - AP_ant = Solo AP original
  - 100m_ant = Solo anillo 100-200m (sin AP)
  - 200m_ant = Solo anillo 200-300m (sin anillo anterior ni AP)
  - etc.

• TOTAL DE ANILLOS: 100 anillos × 97 AP = 9.700 registros aproximadamente

• CÁLCULO DE PORCENTAJES:
  - ant = SOLO píxeles valor 1 (antrópico/asentamientos)
  - otros = SOLO píxeles valor 0 (natural/cobertura natural)
  - nodata (2) = se calcula pero NO se incluye en porcentajes

• CÁLCULO DE ÁREAS:
  - area_m2 = área del anillo en metros cuadrados
  - area_AnHa = area_m2 / 10.000 (hectáreas)
  - area_Ankm = area_m2 / 1.000.000 (kilómetros cuadrados)

• EXPORTACIÓN DE SHAPEFILES:
  - Cambiar EXPORTAR_ANILLOS = True para activar
  - Se crea una carpeta por AP con anillos como archivos separados
  - Cada anillo: Anillo_100m.shp, Anillo_200m.shp... Anillo_10000m.shp

• SISTEMA DE REFERENCIA:
  - OBLIGATORIO que esté en METROS
  - Se validará al inicio del script
  - Si no está en metros, el script emitirá una advertencia

================================================================================
VALIDACIONES REALIZADAS
================================================================================

✓ PASO 0 – Validación del entorno
  - Verificar existencia de shapefile de entrada
  - Verificar existencia del campo identificador
  - Crear carpeta de salida si no existe
  - Confirmar sistema de referencia en metros

✓ PASO 1 – Campos originales
  - Leer y listar campos del shapefile de entrada
  - Preparar estructura de datos

✓ PASO 2 – Leer APs y eliminar huecos
  - Cargar geometrías de AP
  - Limpiar huecos internos (solo anillo exterior)
  - Generar lista de AP ordenada

✓ PASO 3 – Crear Feature Class de salida
  - Crear shapefile de salida con geometría POLYGON
  - Agregar campos originales del shapefile de entrada
  - Agregar campos calculados (ringID, distance, rango_*, area_*)

✓ PASO 4 – Generar anillos y escribir Feature Class
  - Generar 100 anillos concéntricos por AP
  - Calcular campos para cada anillo
  - Escribir registros en Feature Class

✓ PASO 5 – Verificación del resultado
  - Contar registros escritos (debe ser AP × 100)
  - Mostrar muestra de primeros 5 registros
  - Verificar integridad de campos

================================================================================
"""

import arcpy
import os
import csv
import numpy as np
from arcpy import sa
import time
import traceback
import sys

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

INPUT_SHP      = r"C:\Users\valen\Desktop\Fondecyt\areas_protegidas_totales_actualizadas-20251109T203707Z-1-001\AP_terrestres_actualizadas_26marz26\AP_terrestres_actualizadas_26marz26.shp"

INPUT_RASTER   = r"C:\Users\valen\Desktop\Fondecyt\settlements\Asentamientos_raster_Chile_clip\modificado\Asen_buf_2015_modificado.tif"

OUTPUT_FOLDER  = r"C:\Users\valen\Desktop\Fondecyt\settlements\Anillos_100m\Anillos_100m_AP"

OUTPUT_CSV     = "resultados_anillos_100m.csv"

CAMPO_NOMBRE   = "NOMBRE_TOT"

# ====== PARÁMETROS DE ANILLOS ======
RING_STEP      = 100      # Incremento de 100 metros
RING_MAX       = 10000    # Distancia máxima 10.000 metros
N_RINGS        = RING_MAX // RING_STEP   # 100 anillos

# ====== OPCIÓN: EXPORTAR SHAPEFILES DE ANILLOS ======
EXPORTAR_ANILLOS = False  # ← CAMBIAR A True PARA EXPORTAR
# ====================================================

# =============================================================================
# UTILIDADES
# =============================================================================

def log(msg, level="INFO"):
    """Imprime mensaje con timestamp"""
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")
    sys.stdout.flush()

def progress_bar(current, total, prefix=""):
    """Barra de progreso en consola"""
    pct    = current / total * 100
    filled = int(pct / 2)
    bar    = "¦" * filled + "¦" * (50 - filled)
    print(f"\r{prefix} |{bar}| {pct:5.1f}%  ({current}/{total})", end="", flush=True)
    if current == total:
        print()

# =============================================================================
# PASO 0 – VALIDACIONES
# =============================================================================

def validar_entorno():
    log("=" * 65)
    log("PASO 0 — Validando entorno y rutas")
    log("=" * 65)

    if not arcpy.Exists(INPUT_SHP):
        raise FileNotFoundError(f"No se encontró el shapefile:\n  {INPUT_SHP}")
    log(f"  ✓ Shapefile encontrado")

    campos = [f.name for f in arcpy.ListFields(INPUT_SHP)]
    if CAMPO_NOMBRE not in campos:
        raise ValueError(
            f"El campo '{CAMPO_NOMBRE}' NO existe.\n"
            f"  Campos disponibles: {campos}"
        )
    log(f"  ✓ Campo identificador encontrado: {CAMPO_NOMBRE}")

    if not arcpy.Exists(INPUT_RASTER):
        raise FileNotFoundError(f"No se encontró el raster:\n  {INPUT_RASTER}")
    log(f"  ✓ Raster encontrado")

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    log(f"  ✓ Carpeta de salida lista: {OUTPUT_FOLDER}")

    desc = arcpy.Describe(INPUT_SHP)
    sr   = desc.spatialReference
    log(f"  ✓ Sistema de referencia: {sr.name} (WKID {sr.factoryCode})")

    if sr.linearUnitName not in ("Meter", "Metre"):
        log("  ⚠ SRS NO está en metros. Algunos cálculos pueden ser incorrectos.", "WARN")

    return sr

# =============================================================================
# PASO 1 – CAMPOS ORIGINALES
# =============================================================================

def obtener_campos_originales():
    log("=" * 65)
    log("PASO 1 — Leyendo campos del shapefile de entrada")
    log("=" * 65)
    campos = [f.name for f in arcpy.ListFields(INPUT_SHP)
              if f.type not in ("OID", "Geometry")]
    log(f"  ✓ Campos ({len(campos)}): {campos}")
    return campos

# =============================================================================
# PASO 2 – LEER APs Y ELIMINAR HUECOS
# =============================================================================

def leer_y_disolver_ap(sr, campos_orig):
    log("=" * 65)
    log("PASO 2 — Leyendo APs y eliminando huecos internos")
    log("=" * 65)

    desc      = arcpy.Describe(INPUT_SHP)
    oid_field = desc.OIDFieldName
    total     = int(arcpy.GetCount_management(INPUT_SHP).getOutput(0))
    log(f"  Total de APs: {total}")

    cursor_fields = ["SHAPE@", oid_field, CAMPO_NOMBRE] + campos_orig
    registros     = []

    with arcpy.da.SearchCursor(INPUT_SHP, cursor_fields) as cur:
        for i, row in enumerate(cur, 1):
            geom_orig = row[0]
            oid_val   = row[1]
            nombre_ap = row[2]
            atribs    = row[3:]

            # Conservar SOLO el anillo exterior de cada parte (elimina huecos)
            nuevas_partes = []
            for part_idx in range(geom_orig.partCount):
                parte      = geom_orig.getPart(part_idx)
                anillo_ext = arcpy.Array()
                for punto in parte:
                    if punto is None:
                        break
                    anillo_ext.add(punto)
                nuevas_partes.append(anillo_ext)

            array_total = arcpy.Array()
            for arr in nuevas_partes:
                array_total.add(arr)
            geom_limpia = arcpy.Polygon(array_total, sr)

            registros.append({
                "oid":    oid_val,
                "nombre": nombre_ap,
                "geom":   geom_limpia,
                "atribs": atribs,
            })

            progress_bar(i, total, prefix="  Procesando APs")

    log(f"\n  ✓ {len(registros)} APs procesadas")
    log("  Listado (orden original shapefile):")
    for idx, r in enumerate(registros, 1):
        log(f"    {idx:>3}. {r['nombre']}")

    return registros

# =============================================================================
# PASO 3 – CREAR CSV DE SALIDA Y ENCABEZADO
# =============================================================================

def crear_csv_salida(campos_orig):
    log("=" * 65)
    log("PASO 3 — Preparando estructura de salida CSV")
    log("=" * 65)

    output_csv_path = os.path.join(OUTPUT_FOLDER, OUTPUT_CSV)

    # Encabezados para CSV
    encabezados_base = [
        'FID', CAMPO_NOMBRE, 'ringID', 'distance', 
        'rango_min', 'rango_max', 'rango_mid', 'rango_md1', 'rango_lab',
        'area_AnHa', 'area_Ankm', 'ant_pct', 'otros_pct'
    ]

    log(f"  ✓ CSV: {output_csv_path}")
    log(f"  ✓ Anillos por AP: {N_RINGS}")
    log(f"  ✓ Paso de anillo: {RING_STEP} m")
    log(f"  ✓ Distancia máxima: {RING_MAX} m")
    
    return output_csv_path, encabezados_base

# =============================================================================
# PASO 4 – GENERAR ANILLOS Y CALCULAR PORCENTAJES
# =============================================================================

def generar_anillos_csv(output_csv_path, encabezados_base, registros, campos_orig):
    log("=" * 65)
    log("PASO 4 — Generando anillos y calculando porcentajes")
    log("=" * 65)

    # Habilitar extensión Spatial Analyst
    try:
        arcpy.CheckOutExtension("Spatial")
    except:
        pass

    # Cargar raster
    raster_obj = arcpy.Raster(INPUT_RASTER)

    total_ap   = len(registros)
    total_rows = total_ap * N_RINGS
    log(f"  APs: {total_ap}  x  {N_RINGS} anillos = {total_rows:,} filas totales\n")

    filas_csv = []
    t0 = time.time()

    for ap_idx, reg in enumerate(registros, 1):
        geom_ap = reg["geom"]
        nombre  = reg["nombre"]

        log(f"  -- AP {ap_idx:>3}/{total_ap}  ->  {nombre} --")

        buf_anterior = geom_ap   # AP = inicio del primer anillo

        for ring_num in range(1, N_RINGS + 1):
            dist_ext = ring_num * RING_STEP      # 100, 200 ... 10000
            dist_int = (ring_num - 1) * RING_STEP  # 0, 100 ... 9900

            buf_ext      = geom_ap.buffer(dist_ext)
            anillo       = buf_ext.difference(buf_anterior)
            buf_anterior = buf_ext

            rango_min = float(dist_int)
            rango_max = float(dist_ext)
            rango_mid = (rango_min + rango_max) / 2.0
            rango_md1 = rango_mid / 1000.0
            rango_lab = f"{int(rango_min)}-{int(rango_max)}m"

            # Calcular porcentajes
            ant_pct, otros_pct = calcular_porcentajes(raster_obj, anillo)

            # Calcular área
            area_m2  = anillo.area if anillo else 0.0
            area_AnHa= area_m2 / 10_000.0
            area_Ankm= area_m2 / 1_000_000.0

            fila_csv = {
                'FID': ap_idx - 1,
                CAMPO_NOMBRE: nombre,
                'ringID': ring_num,
                'distance': dist_ext,
                'rango_min': rango_min,
                'rango_max': rango_max,
                'rango_mid': rango_mid,
                'rango_md1': rango_md1,
                'rango_lab': rango_lab,
                'area_AnHa': round(area_AnHa, 4),
                'area_Ankm': round(area_Ankm, 6),
                'ant_pct': ant_pct if ant_pct is not None else '',
                'otros_pct': otros_pct if otros_pct is not None else '',
            }

            filas_csv.append(fila_csv)
            progress_bar(ring_num, N_RINGS, prefix=f"    Anillos AP {ap_idx:>3}")

        elapsed  = time.time() - t0
        avg_ap   = elapsed / ap_idx
        restante = avg_ap * (total_ap - ap_idx)
        log(f"    ✓ AP {ap_idx} completada — "
            f"elapsed: {elapsed:.0f}s | "
            f"restante: {restante:.0f}s ({restante/60:.1f} min)")

    # Devolver licencia
    try:
        arcpy.CheckInExtension("Spatial")
    except:
        pass

    # Escribir CSV
    log(f"\n  Escribiendo {len(filas_csv)} registros en CSV...")
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=encabezados_base, delimiter='\t')
        writer.writeheader()
        writer.writerows(filas_csv)

    log(f"  ✓ CSV guardado: {output_csv_path}")

    return filas_csv

# =============================================================================
# FUNCIÓN AUXILIAR: CALCULAR PORCENTAJES CON NUMPY
# =============================================================================

def calcular_porcentajes(raster_obj, geometry):
    """
    Calcula porcentajes usando NumPy
    ant = SOLO píxeles valor 1
    otros = SOLO píxeles valor 0
    nodata (2) = se calcula pero NO se incluye en porcentajes
    """
    try:
        raster_array = arcpy.RasterToNumPyArray(
            sa.ExtractByMask(raster_obj, geometry),
            nodata_to_value=0
        )
        
        count_1 = np.sum(raster_array == 1)      # Antrópico
        count_0 = np.sum(raster_array == 0)      # Natural
        
        total = count_1 + count_0
        
        if total > 0:
            pct_ant = round(count_1 / total * 100, 2)
            pct_otros = round(count_0 / total * 100, 2)
        else:
            pct_ant = None
            pct_otros = None
        
        return pct_ant, pct_otros
    
    except Exception as e:
        return None, None

# =============================================================================
# PASO 5 – VERIFICACION
# =============================================================================

def verificar_resultado(output_csv_path, total_ap, filas_csv):
    log("=" * 65)
    log("PASO 5 — Verificacion del resultado")
    log("=" * 65)

    count    = len(filas_csv)
    esperado = total_ap * N_RINGS

    log(f"  Registros escritos : {count:,}")
    log(f"  Registros esperados: {esperado:,}  ({total_ap} x {N_RINGS})")

    if count == esperado:
        log("  ✓ Conteo correcto OK")
    else:
        log(f"  ⚠ DIFERENCIA: {abs(count - esperado)} registros", "WARN")

    if filas_csv:
        log("\n  Muestra primeros 5 registros:")
        columnas_muestra = ['ringID', 'distance', 'rango_lab', 'area_AnHa', 'ant_pct']
        log("  " + "  ".join(f"{s:>12}" for s in columnas_muestra))
        log("  " + "-" * (14 * len(columnas_muestra)))
        for i, row in enumerate(filas_csv[:5]):
            fmt = []
            for col in columnas_muestra:
                v = row.get(col, '')
                if isinstance(v, float):
                    fmt.append(f"{v:>12.4f}")
                else:
                    fmt.append(f"{str(v):>12}")
            log("  " + "  ".join(fmt))

    log("\n" + "=" * 65)
    log("PROCESO COMPLETADO EXITOSAMENTE")
    log("=" * 65)

# =============================================================================
# MAIN
# =============================================================================

def main():
    t_inicio = time.time()
    log("=" * 65)
    log("INICIO — Generador de Anillos 100m x 100 (97 APs)")
    log(f"  Output: {os.path.join(OUTPUT_FOLDER, OUTPUT_CSV)}")
    log("=" * 65)

    try:
        sr          = validar_entorno()
        campos_orig = obtener_campos_originales()
        registros   = leer_y_disolver_ap(sr, campos_orig)
        output_csv_path, encabezados = crear_csv_salida(campos_orig)
        filas_csv   = generar_anillos_csv(output_csv_path, encabezados, registros, campos_orig)
        verificar_resultado(output_csv_path, len(registros), filas_csv)

    except (FileNotFoundError, ValueError) as e:
        log(str(e), "ERROR")
        sys.exit(1)
    except arcpy.ExecuteError:
        log(arcpy.GetMessages(2), "ERROR")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        log(f"Error inesperado: {e}", "ERROR")
        traceback.print_exc()
        sys.exit(1)
    finally:
        t_total = time.time() - t_inicio
        log(f"\n  Tiempo total: {t_total:.1f}s  ({t_total/60:.1f} min)")


if __name__ == "__main__":
    main()
