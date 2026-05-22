#!/usr/bin/env python3
"""
================================================================================
TITULO 
================================================================================

PROYECTO FONDECYT Nº 1251080
"Evaluación de las áreas protegidas y sus zonas de amortiguación en Chile: 
un análisis geoespacial de su eficacia para contrarrestar el cambio global"

AUTOR: Valentina Contreras

================================================================================
DESCRIPCIÓN GENERAL
================================================================================

Este script realiza análisis de datos de asentamientos y genera/exporta anillos
independientes alrededor de 97 Áreas Protegidas (AP). Calcula porcentajes de
píxeles antrópicos y naturales para cada zona de análisis.

El procesamiento incluye:
  - Análisis de AP sin modificación
  - Generación de anillos independientes de 1km a 10km
  - Cálculo de porcentajes de asentamientos (ant) vs natural (otros)
  - Exportación de resultados a CSV
  - Exportación opcional de shapefiles de anillos

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

3. PROCESAMIENTO POR AP
   - Para cada AP:
     * Analizar AP sin modificación
     * Generar anillos independientes (1-10km)
     * Calcular porcentajes de cobertura antrópica
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
• Módulos: arcpy, os, csv, numpy
• Acceso a licencias de ArcGIS
• Rásteres de entrada en formato GeoTIFF

================================================================================
FLUJO DE ENTRADA/SALIDA
================================================================================

ENTRADA:
  - Shapefile de Áreas Protegidas (AP_terrestres_actualizadas.shp)
  - Raster de asentamientos (Asen_buf_2015_modificado.tif)

SALIDA:
  - CSV con resultados de análisis (resultados_anillos.csv)
  - Shapefiles de anillos (opcional, en carpeta ANILLOS_SHAPEFILES)

================================================================================
CONFIGURACIÓN
================================================================================

Antes de ejecutar, modifica los siguientes parámetros:

  • ruta_ap: Ruta al shapefile de Áreas Protegidas
  • ruta_img: Ruta al raster de asentamientos
  • ruta_csv_salida: Ruta de salida para el CSV de resultados
  • EXPORTAR_ANILLOS: True para exportar shapefiles, False para solo CSV
  • ruta_anillos: Carpeta de salida para shapefiles (si EXPORTAR_ANILLOS=True)

================================================================================
USO
================================================================================

1. Abrir el script en Python IDE (ArcGIS Pro Python Console recomendado)
2. Configurar rutas de entrada/salida
3. Cambiar EXPORTAR_ANILLOS a True si desea exportar shapefiles
4. Ejecutar: python Generacion_anillos_analisis_Asentamientos_en_APs.py
5. Revisar reporte de procesamiento en consola
6. Verificar archivos en ruta_csv_salida y ruta_anillos

================================================================================
SALIDA DEL SCRIPT
================================================================================

El script genera:
  • CSV con porcentajes de asentamientos para AP y cada anillo (1-10km)
  • Reporte detallado en consola con progreso y resultados por AP
  • Estadísticas finales (mín, máx, promedio)
  • Shapefiles de anillos independientes (opcional)
  • Información de ubicación de archivos generados

================================================================================
NOTAS IMPORTANTES
================================================================================

• ANILLOS INDEPENDIENTES: Cada anillo es aislado del anterior
  - AP_ant = Solo AP original
  - 1km_ant = Solo anillo 1km (sin AP)
  - 2km_ant = Solo anillo 2km (sin anillo 1km ni AP)
  - etc.

• CÁLCULO DE PORCENTAJES:
  - ant = SOLO píxeles valor 1 (antrópico)
  - otros = SOLO píxeles valor 0 (natural)
  - nodata (2) = se calcula pero NO se incluye en porcentajes

• EXPORTACIÓN DE SHAPEFILES:
  - Cambiar EXPORTAR_ANILLOS = True para activar
  - Se crea una carpeta por AP con anillos como archivos separados

================================================================================
"""

import arcpy
import os
import csv
import numpy as np
from arcpy import sa
import time

print("\n" + "="*70)
print("PROCESAMIENTO FONDECYT - 97 APs (ANILLOS INDEPENDIENTES)")
print("="*70)

# ======================================================
# CONFIGURACIÓN
# ======================================================

ruta_ap = r"C:\Users\valen\Desktop\Fondecyt\areas_protegidas_totales_actualizadas-20251109T203707Z-1-001\AP_terrestres_actualizadas_26marz26\AP_terrestres_actualizadas_26marz26.shp"

ruta_img = r"C:\Users\valen\Desktop\Fondecyt\settlements\Asentamientos_raster_Chile_clip\modificado\Asen_buf_2015_modificado.tif"

ruta_csv_salida = r"C:\Users\valen\Desktop\Fondecyt\settlements\CSV\csv_anillos\resultados_anillos.csv"

# ====== OPCIÓN: EXPORTAR SHAPEFILES DE ANILLOS ======
# Cambiar a True si quieres exportar los shapefiles
EXPORTAR_ANILLOS = False  # ← CAMBIAR A True PARA EXPORTAR
ruta_anillos = r"C:\Users\valen\Desktop\Fondecyt\settlements\CSV\csv_anillos\ANILLOS_SHAPEFILES"
# ====================================================

distancias_km = list(range(1, 11))

os.makedirs(os.path.dirname(ruta_csv_salida), exist_ok=True)

if EXPORTAR_ANILLOS:
    os.makedirs(ruta_anillos, exist_ok=True)

print("\n📁 CONFIGURACIÓN:")
print(f"  AP: {ruta_ap}")
print(f"  Imagen: {ruta_img}")
print(f"  CSV salida: {ruta_csv_salida}")
if EXPORTAR_ANILLOS:
    print(f"  Anillos shapefiles: {ruta_anillos}")

# ======================================================
# VERIFICAR
# ======================================================
print("\n✓ Verificando archivos...")

if not arcpy.Exists(ruta_ap):
    print(f"❌ ERROR: No encontré {ruta_ap}")
    exit(1)

if not arcpy.Exists(ruta_img):
    print(f"❌ ERROR: No encontré {ruta_img}")
    exit(1)

print("  ✅ Archivos encontrados")

# ======================================================
# CARGAR DATOS
# ======================================================
print("\n📍 Cargando datos...")

result = arcpy.management.GetCount(ruta_ap)
num_ap = int(result[0])
print(f"  ✓ AP cargadas: {num_ap} features")

# Cargar raster
raster_obj = arcpy.Raster(ruta_img)
print(f"  ✓ Imagen raster cargada")

print("\n" + "="*70)
print("PROCESANDO TODAS LAS 97 ÁREAS PROTEGIDAS")
print("="*70)

# Habilitar Spatial
try:
    arcpy.CheckOutExtension("Spatial")
except:
    pass

# ======================================================
# FUNCIÓN: CALCULAR PORCENTAJES CON NUMPY
# ======================================================

def calcular_porcentajes_numpy(raster_obj, geometry):
    """
    Calcula porcentajes usando NumPy directamente
    ant = SOLO píxeles valor 1
    otros = SOLO píxeles valor 0
    nodata (2) = se calcula pero NO se incluye en porcentajes
    Retorna: (pct_ant, pct_otros, count_ant, count_otros, count_nodata)
    """
    try:
        # Extraer raster a array NumPy (en memoria)
        raster_array = arcpy.RasterToNumPyArray(
            sa.ExtractByMask(raster_obj, geometry),
            nodata_to_value=0
        )
        
        # Contar valores
        count_1 = np.sum(raster_array == 1)      # Antrópico
        count_0 = np.sum(raster_array == 0)      # Natural
        count_2 = np.sum(raster_array == 2)      # NoData
        
        count_ant = count_1
        count_otros = count_0
        
        # Total SIN contar nodata (2)
        total = count_ant + count_otros
        
        if total > 0:
            pct_ant = round(count_ant / total * 100, 2)
            pct_otros = round(count_otros / total * 100, 2)
        else:
            pct_ant = None
            pct_otros = None
        
        return pct_ant, pct_otros, count_ant, count_otros, count_2
    
    except Exception as e:
        return None, None, 0, 0, 0

# ======================================================
# PROCESAR TODAS LAS 97 APs
# ======================================================

resultados_lista = []
tiempo_inicio = time.time()

cursor = arcpy.da.SearchCursor(ruta_ap, 
    ['OID@', 'SHAPE@', 'NOMBRE_TOT', 'CATEGORIA', 'REGION', 'ANIO_CREAC', 
     'AREA_HA', 'PRIM_METR', 'LATITUD', 'LONGITUD', 'ALT_MIN', 'ALT_MAX', 
     'ALT_MEAN', 'ALT_MED', 'ALT_STD'])

idx = 0
for row in cursor:
    idx += 1
    
    pct_progreso = round(idx / num_ap * 100, 1)
    nombre_ap = str(row[2]) if row[2] else f'AP_{idx}'
    
    # MOSTRAR ENCABEZADO
    print(f"\n{'='*70}")
    print(f"AP {idx}/{num_ap} ({pct_progreso}%) - {nombre_ap}")
    print(f"  Categoría: {row[3]} | Región: {row[4]} | Área: {row[6]} ha")
    print(f"{'='*70}")
    
    tiempo_ap_inicio = time.time()
    
    fila = {
        'FID': idx - 1,
        'NOMBRE_TOT': row[2],
        'CATEGORIA': row[3],
        'REGION': row[4],
        'ANIO_CREAC': row[5],
        'AREA_HA': row[6],
        'PRIM_METR': row[7],
        'LATITUD': row[8],
        'LONGITUD': row[9],
        'ALT_MIN': row[10],
        'ALT_MAX': row[11],
        'ALT_MEAN': row[12],
        'ALT_MED': row[13],
        'ALT_STD': row[14],
    }
    
    geometry = row[1]
    
    # ======================================================
    # AP SIN ANILLO (INDEPENDIENTE)
    # ======================================================
    pct_ant_ap, pct_otros_ap, cnt_ant_ap, cnt_otros_ap, cnt_nodata_ap = calcular_porcentajes_numpy(raster_obj, geometry)
    fila['AP_ant'] = pct_ant_ap
    fila['AP_otros'] = pct_otros_ap
    
    if pct_ant_ap is not None:
        print(f"  📍 AP (solo):") 
        print(f"     ant={pct_ant_ap}% ({int(cnt_ant_ap)} píx) | otros={pct_otros_ap}% ({int(cnt_otros_ap)} píx) | nodata={int(cnt_nodata_ap)} píx")
    else:
        print(f"  📍 AP (solo): ❌ ERROR")
    
    # ======================================================
    # EXPORTAR SHAPEFILES DE ANILLOS (OPCIONAL)
    # ======================================================
    if EXPORTAR_ANILLOS:
        # Crear carpeta para esta AP
        carpeta_ap = os.path.join(ruta_anillos, f"AP_{idx:03d}_{nombre_ap.replace(' ', '_')}")
        os.makedirs(carpeta_ap, exist_ok=True)
        
        # Exportar AP original
        try:
            fc_ap = os.path.join(carpeta_ap, "AP_original.shp")
            arcpy.management.CreateFeatureclass(
                carpeta_ap, "AP_original", geometry_type="POLYGON"
            )
            with arcpy.da.InsertCursor(fc_ap, ['SHAPE@']) as cursor_insert:
                cursor_insert.insertRow([geometry])
        except:
            pass
    
    # ======================================================
    # ANILLOS INDEPENDIENTES (cada uno aislado)
    # ======================================================
    anillo_anterior = geometry  # Comenzar desde la AP
    
    for km in distancias_km:
        # Anillo actual
        anillo_actual = geometry.buffer(km * 1000)
        
        # Anillo = anillo_actual - anillo_anterior
        # Ejemplo:
        # 1km: anillo_1km - AP = solo anillo 1km
        # 2km: anillo_2km - anillo_1km = solo anillo 2km
        # 3km: anillo_3km - anillo_2km = solo anillo 3km
        anillo = anillo_actual.difference(anillo_anterior)
        
        pct_ant, pct_otros, cnt_ant, cnt_otros, cnt_nodata = calcular_porcentajes_numpy(raster_obj, anillo)
        
        fila[f'{km}km_ant'] = pct_ant
        fila[f'{km}km_otros'] = pct_otros
        
        if pct_ant is not None:
            print(f"  📍 Anillo {km}km (independiente): ant={pct_ant}% | otros={pct_otros}%")
        else:
            print(f"  📍 Anillo {km}km (independiente): ❌ ERROR")
        
        # Exportar shapefile del anillo si está habilitado
        if EXPORTAR_ANILLOS:
            try:
                fc_anillo = os.path.join(carpeta_ap, f"Anillo_{km}km.shp")
                arcpy.management.CreateFeatureclass(
                    carpeta_ap, f"Anillo_{km}km", geometry_type="POLYGON"
                )
                with arcpy.da.InsertCursor(fc_anillo, ['SHAPE@']) as cursor_insert:
                    cursor_insert.insertRow([anillo])
            except:
                pass
        
        # Guardar para próxima iteración
        anillo_anterior = anillo_actual
    
    resultados_lista.append(fila)
    
    tiempo_ap_fin = time.time()
    tiempo_ap = round(tiempo_ap_fin - tiempo_ap_inicio, 1)
    
    if fila['AP_ant'] is not None:
        print(f"\n  ✅ COMPLETADO ({tiempo_ap}s)")
    else:
        print(f"\n  ❌ ERROR ({tiempo_ap}s)")

del cursor

tiempo_fin = time.time()
tiempo_total = round((tiempo_fin - tiempo_inicio) / 60, 1)

# Devolver licencia
try:
    arcpy.CheckInExtension("Spatial")
except:
    pass

# ======================================================
# EXPORTAR A CSV
# ======================================================
print("\n" + "="*70)
print("💾 EXPORTANDO CSV...")

columnas_orden = [
    'FID', 'NOMBRE_TOT', 'CATEGORIA', 'REGION', 'ANIO_CREAC', 'AREA_HA', 'PRIM_METR',
    'LATITUD', 'LONGITUD', 'ALT_MIN', 'ALT_MAX', 'ALT_MEAN', 'ALT_MED', 'ALT_STD',
    'AP_ant', 'AP_otros',
    '1km_ant', '1km_otros', '2km_ant', '2km_otros', '3km_ant', '3km_otros',
    '4km_ant', '4km_otros', '5km_ant', '5km_otros', '6km_ant', '6km_otros',
    '7km_ant', '7km_otros', '8km_ant', '8km_otros', '9km_ant', '9km_otros',
    '10km_ant', '10km_otros'
]

with open(ruta_csv_salida, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=columnas_orden, 
                           extrasaction='ignore', delimiter='\t')
    writer.writeheader()
    writer.writerows(resultados_lista)

print(f"  ✅ CSV guardado en:")
print(f"    {ruta_csv_salida}")

# ======================================================
# RESUMEN FINAL
# ======================================================
print("\n" + "="*70)
print("✅ PROCESAMIENTO COMPLETADO")
print("="*70 + "\n")

con_datos = sum(1 for r in resultados_lista if r['AP_ant'] is not None)

print("📊 RESUMEN FINAL:")
print(f"  Total de AP procesadas: {len(resultados_lista)}")
print(f"  AP con datos: {con_datos}/{len(resultados_lista)}")
print(f"  Tiempo total: {tiempo_total} minutos")
print(f"  Tiempo promedio por AP: {round(tiempo_total*60/len(resultados_lista), 1)} segundos")
print(f"  Cálculo: ant=solo 1 | otros=solo 0 | nodata(2)=no incluido")
print(f"  Tipo: ANILLOS INDEPENDIENTES (cada anillo aislado)")
if EXPORTAR_ANILLOS:
    print(f"  Anillos exportados: SÍ")
else:
    print(f"  Anillos exportados: NO (cambiar EXPORTAR_ANILLOS = True)")
print()

valores_ap_ant = [r['AP_ant'] for r in resultados_lista if r['AP_ant'] is not None]

if valores_ap_ant:
    print("📈 ESTADÍSTICAS - AP_ant (%):")
    print(f"  Mínimo: {min(valores_ap_ant)}%")
    print(f"  Máximo: {max(valores_ap_ant)}%")
    print(f"  Promedio: {round(sum(valores_ap_ant)/len(valores_ap_ant), 2)}%")
    print()

print("📋 PRIMERAS 5 APs PROCESADAS:")
for i, row in enumerate(resultados_lista[:5]):
    print(f"  {i+1}. {row['NOMBRE_TOT']}")
    print(f"     AP_ant={row['AP_ant']}% | 1km_ant={row['1km_ant']}% | 10km_ant={row['10km_ant']}%")

if EXPORTAR_ANILLOS:
    print(f"\n📁 Shapefiles guardados en:")
    print(f"   {ruta_anillos}")

print("\n\n🎉 ¡PROCESAMIENTO COMPLETADO EN", tiempo_total, "MINUTOS!\n")
