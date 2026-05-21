#!/usr/bin/env python3
"""
SCRIPT ULTRA-RÁPIDO PARA 97 APs
GENERACIÓN DE BUFFERS ACUMULATIVOS (desde borde AP hacia afuera)
- AP_ant = Solo AP original
- 1km_ant = % desde borde AP hasta 1km (anillo 1km, SIN AP)
- 2km_ant = % desde borde AP hasta 2km (anillo 1km + 2km, SIN AP)
- 3km_ant = % desde borde AP hasta 3km (anillo 1km + 2km + 3km, SIN AP)
- etc.

CÁLCULO:
- ant = SOLO píxeles valor 1
- otros = SOLO píxeles valor 0
- nodata (2) = se calcula pero NO se incluye en porcentajes
"""

import arcpy
import os
import csv
import numpy as np
from arcpy import sa
import time

print("\n" + "="*70)
print("PROCESAMIENTO FONDECYT - 97 APs (BUFFERS SIN AP)")
print("="*70)

# ======================================================
# CONFIGURACIÓN
# ======================================================

ruta_ap = r"C:\Users\valen\Desktop\Fondecyt\areas_protegidas_totales_actualizadas-20251109T203707Z-1-001\AP_terrestres_actualizadas_26marz26\AP_terrestres_actualizadas_26marz26.shp"

ruta_img = r"C:\Users\valen\Desktop\Fondecyt\settlements\Asentamientos_raster_Chile_clip\modificado\Asen_buf_2015_modificado.tif"

ruta_csv_salida = r"C:\Users\valen\Desktop\Fondecyt\settlements\CSV\csv_anillos\resultados_anillos.csv"

distancias_km = list(range(1, 11))

os.makedirs(os.path.dirname(ruta_csv_salida), exist_ok=True)

print("\n📁 CONFIGURACIÓN:")
print(f"  AP: {ruta_ap}")
print(f"  Imagen: {ruta_img}")
print(f"  CSV salida: {ruta_csv_salida}")

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
    # AP SIN BUFFER (INDEPENDIENTE)
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
    # GENERACIÓN DE BUFFERS ACUMULATIVOS (restando AP - desde borde hacia afuera)
    # ======================================================
    for km in distancias_km:
        # Buffer de km km MENOS la AP = desde borde AP hasta km km
        buffer_completo = geometry.buffer(km * 1000)
        buffer_sin_ap = buffer_completo.difference(geometry)
        
        # 1km_ant = anillo 1km (desde borde AP hasta 1km)
        # 2km_ant = anillo 1km + 2km (desde borde AP hasta 2km)
        # 3km_ant = anillo 1km + 2km + 3km (desde borde AP hasta 3km)
        pct_ant, pct_otros, cnt_ant, cnt_otros, cnt_nodata = calcular_porcentajes_numpy(raster_obj, buffer_sin_ap)
        
        fila[f'{km}km_ant'] = pct_ant
        fila[f'{km}km_otros'] = pct_otros
        
        if pct_ant is not None:
            print(f"  📍 Buffer {km}km: ant={pct_ant}% | otros={pct_otros}%")
        else:
            print(f"  📍 Buffer {km}km: ❌ ERROR")
    
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

print("\n\n🎉 ¡PROCESAMIENTO COMPLETADO EN", tiempo_total, "MINUTOS!\n")
