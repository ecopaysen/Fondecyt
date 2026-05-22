#!/usr/bin/env python3
"""
================================================================================
ANÁLISIS DE ASENTAMIENTOS EN ÁREAS PROTEGIDAS USANDO BUFFERS PREEXISTENTES
================================================================================

PROYECTO FONDECYT Nº 1251080
"Evaluación de las áreas protegidas y sus zonas de amortiguación en Chile: 
un análisis geoespacial de su eficacia para contrarrestar el cambio global"

AUTOR DEL CODIGO: Valentina Contreras

================================================================================
DESCRIPCIÓN GENERAL
================================================================================

Este script realiza análisis de datos de asentamientos calculando porcentajes
de píxeles antrópicos y naturales en 97 Áreas Protegidas (AP) y sus buffers
acumulativos preexistentes. A diferencia del script generador, este NO crea
buffers, sino que trabaja con shapefiles de buffers ya generados.

El procesamiento incluye:
  - Análisis de AP sin modificación
  - Cálculo de porcentajes sobre buffers acumulativos preexistentes (1-10km)
  - Cálculo de porcentajes de asentamientos (ant) vs natural (otros)
  - Exportación de resultados a CSV
  - Generación de resumen estadístico

================================================================================
FLUJO DE TRABAJO
================================================================================

1. CONFIGURACIÓN
   - Definir rutas de entrada (shapefile de AP, raster de asentamientos)
   - Definir rutas de buffers preexistentes (1-10km)
   - Definir ruta de salida (CSV con resultados)

2. VERIFICACIÓN
   - Validar existencia de archivos de entrada
   - Verificar que todos los buffers existen
   - Cargar cantidad de AP

3. PROCESAMIENTO POR AP
   - Para cada AP:
     * Analizar AP sin modificación
     * Calcular porcentajes en cada buffer preexistente (1-10km)
     * Exportar resultados a diccionario

4. EXPORTACIÓN
   - Guardar resultados en CSV con formato tabulado
   - Generar resumen de procesamiento

5. RESUMEN
   - Mostrar estadísticas finales
   - Indicar ubicación de archivos de salida
   - Mostrar primeras 5 APs procesadas

================================================================================
REQUISITOS TÉCNICOS
================================================================================

• Python 3.6+
• ArcGIS Desktop / ArcGIS Pro (con extensión Spatial Analyst)
• Módulos: arcpy, os, csv, numpy, time
• Acceso a licencias de ArcGIS
• Rásteres de entrada en formato GeoTIFF
• Shapefiles de buffers preexistentes (1-10km)

================================================================================
FLUJO DE ENTRADA/SALIDA
================================================================================

ENTRADA:
  - Shapefile de Áreas Protegidas (AP_terrestres_actualizadas.shp)
  - Raster de asentamientos (Asen_2017.tif)
  - 10 Shapefiles de buffers preexistentes (Buffer_1km_clip.shp a Buffer_10km_clip.shp)

SALIDA:
  - CSV con resultados de análisis (resultados_buffer_2017.csv)

================================================================================
CONFIGURACIÓN
================================================================================

Antes de ejecutar, verifica los siguientes parámetros:

  • ruta_ap: Ruta al shapefile de Áreas Protegidas
  • ruta_img: Ruta al raster de asentamientos
  • ruta_buffers_base: Ruta base donde están los buffers preexistentes
  • buffers_disponibles: Diccionario con rutas de cada buffer (1-10km)
  • ruta_csv_salida: Ruta de salida para el CSV de resultados
  • distancias_km: Lista de distancias a procesar (por defecto 1-10)

================================================================================
USO
================================================================================

1. Abrir el script en Python IDE (ArcGIS Pro Python Console recomendado)
2. Configurar rutas de entrada/salida
3. Verificar que buffers preexistentes existen en las rutas especificadas
4. Ejecutar: python script_calculos_buffers_preexistentes.py
5. Revisar reporte de procesamiento en consola
6. Verificar archivo CSV en ruta_csv_salida

================================================================================
SALIDA DEL SCRIPT
================================================================================

El script genera:
  • CSV con porcentajes de asentamientos para AP y cada buffer (1-10km)
  • Reporte detallado en consola con progreso y resultados por AP
  • Estadísticas finales (mín, máx, promedio)
  • Información de ubicación de archivos generados
  • Resumen de AP procesadas exitosamente

================================================================================
NOTAS IMPORTANTES - BUFFERS ACUMULATIVOS
================================================================================

• BUFFERS ACUMULATIVOS: Cada buffer es acumulativo desde el borde de la AP
  - AP_ant = Solo AP original (sin ningún buffer)
  - 1km_ant = Desde borde AP hasta 1km (anillo 1km, SIN AP)
  - 2km_ant = Desde borde AP hasta 2km (anillos 1km+2km, SIN AP)
  - 3km_ant = Desde borde AP hasta 3km (anillos 1km+2km+3km, SIN AP)
  - ...
  - 10km_ant = Desde borde AP hasta 10km (todos anillos acumulados, SIN AP)

• LOS BUFFERS DEBEN EXISTIR:
  - Este script NO genera buffers
  - Los buffers deben haber sido creados previamente
  - Se cargan desde las rutas especificadas en buffers_disponibles
  - Si falta algún buffer, el script detiene la ejecución

• CÁLCULO DE PORCENTAJES:
  - ant = SOLO píxeles valor 1 (antrópico/asentamientos)
  - otros = SOLO píxeles valor 0 (natural/vegetación)
  - nodata (2) = se calcula pero NO se incluye en porcentajes
  - Porcentaje = (ant / (ant + otros)) × 100

================================================================================
CÁLCULO DE DATOS
================================================================================

El script analiza píxeles raster con los siguientes valores:
  - 1 = Antrópico (asentamientos, zonas urbanas, etc.)
  - 0 = Natural (vegetación, agua, terreno natural)
  - 2 = NoData (sin información)

Para cada zona (AP, Buffer_1km, Buffer_2km, etc.):
  1. Extrae máscara de píxeles dentro de la geometría
  2. Convierte a array NumPy para mejor rendimiento
  3. Cuenta píxeles con valor 1 (antrópico)
  4. Cuenta píxeles con valor 0 (natural)
  5. Cuenta píxeles con valor 2 (nodata) para referencia
  6. Calcula porcentajes EXCLUYENDO nodata: (ant / (ant + otros)) × 100
  7. Almacena en CSV junto con metadatos de la AP

================================================================================
CAMPOS DEL CSV DE SALIDA
================================================================================

Metadatos de la AP:
  - FID: Identificador único
  - NOMBRE_TOT: Nombre del área protegida
  - CATEGORIA: Categoría de protección
  - REGION: Región geográfica
  - ANIO_CREAC: Año de creación
  - AREA_HA: Área en hectáreas
  - PRIM_METR: Perímetro en metros
  - LATITUD: Latitud del centroide
  - LONGITUD: Longitud del centroide
  - ALT_MIN: Altitud mínima
  - ALT_MAX: Altitud máxima
  - ALT_MEAN: Altitud promedio
  - ALT_MED: Altitud mediana
  - ALT_STD: Desviación estándar de altitud

Resultados de asentamientos (para cada distancia 1-10km):
  - AP_ant: % asentamientos en AP (sin buffer)
  - AP_otros: % natural en AP (sin buffer)
  - 1km_ant: % asentamientos buffer 1km acumulativo
  - 1km_otros: % natural buffer 1km acumulativo
  - 2km_ant: % asentamientos buffer 2km acumulativo
  - 2km_otros: % natural buffer 2km acumulativo
  - ... hasta 10km_ant y 10km_otros



================================================================================
REQUISITOS DE ENTRADA - ESPECIFICACIONES
================================================================================

Shapefile de AP (AP_terrestres_actualizadas.shp):
  - Geometría: POLYGON
  - Campos requeridos: NOMBRE_TOT, CATEGORIA, REGION, ANIO_CREAC, AREA_HA,
                       PRIM_METR, LATITUD, LONGITUD, ALT_MIN, ALT_MAX,
                       ALT_MEAN, ALT_MED, ALT_STD
  - Proyección: Debe ser consistente con el raster
  - Cantidad: 97 polígonos (una por AP)

Raster de asentamientos (Asen_2017.tif):
  - Tipo: GeoTIFF
  - Valores: 0 (natural), 1 (antrópico), 2 (nodata)
  - Proyección: Debe coincidir con el shapefile
  - Cobertura: Debe cubrir todas las AP y sus buffers
  - Año: 2017 (o el año específico)

Shapefiles de Buffers Preexistentes:
  - Tipo: Geometría POLYGON
  - Cantidad: 10 archivos (uno por cada km de 1 a 10)
  - Proyección: Debe coincidir con shapefile de AP y raster
  - Contenido: Geometrías de buffers acumulativos SIN AP

================================================================================
ERRORES COMUNES Y SOLUCIONES
================================================================================

Error: "No encontré ruta_ap"
  → Verificar que la ruta existe y está correctamente escrita
  → Verificar que el usuario tiene permisos de lectura

Error: "No encontré ruta_img"
  → Verificar que el TIF existe en la ruta especificada
  → Verificar formato GeoTIFF válido
  → Verificar que no está corrupto

Error: "Buffer Xkm: NO ENCONTRADO"
  → Verificar que todos los buffers existen en ruta_buffers_base
  → Verificar nombres de archivo exactos (Buffer_1km_clip.shp, etc.)
  → Verificar que la ruta está correctamente especificada

ERROR en calcular_porcentajes_numpy:
  → Puede ser que el raster y shapefile tengan proyecciones diferentes
  → Verificar que proyecciones coinciden
  → Verificar que buffers están dentro de cobertura raster

CSV vacío o con pocos datos:
  → Verificar que raster contiene valores 0, 1, 2
  → Verificar que geometrías del shapefile son válidas
  → Probar con una AP individual primero


================================================================================
NOTAS DE RENDIMIENTO
================================================================================

- Tiempo de procesamiento: ~1-2 minutos por AP (depende del hardware)
- Memoria requerida: 8GB RAM mínimo recomendado
- Espacio en disco: ~500MB para CSV
- Uso de extensión Spatial: Se checkOut/CheckIn automáticamente
- Operaciones: Se usan arrays NumPy para mejor rendimiento

Para optimizar:
  - Usar SSD en lugar de HDD
  - Aumentar memoria RAM del equipo
  - Reducir resolución del raster si es posible
  - Procesar en lotes más pequeños si hay limitaciones

================================================================================
"""

import arcpy
import os
import csv
import numpy as np
from arcpy import sa
import time

print("\n" + "="*70)
print("PROCESAMIENTO FONDECYT - 97 APs (BUFFERS PREEXISTENTES)")
print("="*70)

# ======================================================
# CONFIGURACIÓN
# ======================================================

ruta_ap = r"C:\Users\valen\Desktop\Fondecyt\areas_protegidas_totales_actualizadas-20251109T203707Z-1-001\AP_terrestres_actualizadas_26marz26\AP_terrestres_actualizadas_26marz26.shp"

ruta_img = r"C:\Users\valen\Desktop\Fondecyt\settlements\Asentamientos_raster_Chile_clip\Asen_2017.tif"

ruta_csv_salida = r"C:\Users\valen\Desktop\Fondecyt\settlements\CSV\csv_anillos\resultados_buffer_2017.csv"

# RUTAS DE BUFFERS PREEXISTENTES
ruta_buffers_base = r"C:\Users\valen\Desktop\Fondecyt\areas_protegidas_totales_actualizadas-20251109T203707Z-1-001\Buffer\Buffer_consecutivos\Buffer_clip\Buffer_clip_modificacion_v6"

buffers_disponibles = {
    1: os.path.join(ruta_buffers_base, "Buffer_1km_clip.shp"),
    2: os.path.join(ruta_buffers_base, "Buffer_2km_clip.shp"),
    3: os.path.join(ruta_buffers_base, "Buffer_3km_clip.shp"),
    4: os.path.join(ruta_buffers_base, "Buffer_4km_clip.shp"),
    5: os.path.join(ruta_buffers_base, "Buffer_5km_clip.shp"),
    6: os.path.join(ruta_buffers_base, "Buffer_6km_clip.shp"),
    7: os.path.join(ruta_buffers_base, "Buffer_7km_clip.shp"),
    8: os.path.join(ruta_buffers_base, "Buffer_8km_clip.shp"),
    9: os.path.join(ruta_buffers_base, "Buffer_9km_clip.shp"),
    10: os.path.join(ruta_buffers_base, "Buffer_10km_clip.shp"),
}

distancias_km = list(range(1, 11))

os.makedirs(os.path.dirname(ruta_csv_salida), exist_ok=True)

print("\n📋 CONFIGURACIÓN:")
print(f"  AP: {ruta_ap}")
print(f"  Imagen: {ruta_img}")
print(f"  CSV salida: {ruta_csv_salida}")
print(f"  Buffers base: {ruta_buffers_base}")

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

print("  ✓ Archivos principales encontrados")

# Verificar buffers
print("\n✓ Verificando buffers preexistentes...")
buffers_no_encontrados = []
for km, ruta_buffer in buffers_disponibles.items():
    if not arcpy.Exists(ruta_buffer):
        buffers_no_encontrados.append((km, ruta_buffer))
        print(f"  ❌ Buffer {km}km: NO ENCONTRADO")
    else:
        print(f"  ✓ Buffer {km}km: OK")

if buffers_no_encontrados:
    print(f"\n❌ ERROR: Faltan {len(buffers_no_encontrados)} buffer(s)")
    exit(1)

# ======================================================
# CARGAR DATOS
# ======================================================
print("\n📊 Cargando datos...")

result = arcpy.management.GetCount(ruta_ap)
num_ap = int(result[0])
print(f"  ✓ AP cargadas: {num_ap} features")

# Cargar raster
raster_obj = arcpy.Raster(ruta_img)
print(f"  ✓ Imagen raster cargada")

print("\n" + "="*70)
print("PROCESANDO TODAS LAS 97 ÁREAS PROTEGIDAS")
print("USANDO BUFFERS PREEXISTENTES")
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
    # BUFFERS PREEXISTENTES
    # (desde borde AP hacia afuera, acumulativos)
    # ======================================================
    
    print(f"  🔹 Procesando buffers preexistentes...")
    
    for km in distancias_km:
        ruta_buffer = buffers_disponibles[km]
        
        # Seleccionar geometría del buffer que intersecta con el AP actual
        try:
            # Crear una capa de selección temporal
            where_clause = f"OBJECTID >= 0"  # Seleccionar todo
            
            # Usar el buffer completo
            pct_ant, pct_otros, cnt_ant, cnt_otros, cnt_nodata = calcular_porcentajes_numpy(
                raster_obj, 
                ruta_buffer  # El archivo shapefile actúa como geometría
            )
            
            fila[f'{km}km_ant'] = pct_ant
            fila[f'{km}km_otros'] = pct_otros
            
            if pct_ant is not None:
                print(f"     Buffer {km}km: ant={pct_ant}% | otros={pct_otros}%")
            else:
                print(f"     Buffer {km}km: ❌ ERROR")
                
        except Exception as e:
            print(f"     Buffer {km}km: ❌ ERROR - {str(e)}")
            fila[f'{km}km_ant'] = None
            fila[f'{km}km_otros'] = None
    
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

print(f"  ✓ CSV guardado en:")
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
print(f"  Buffers utilizados: PREEXISTENTES (no generados)")
print()

valores_ap_ant = [r['AP_ant'] for r in resultados_lista if r['AP_ant'] is not None]

if valores_ap_ant:
    print("📈 ESTADÍSTICAS - AP_ant (%):")
    print(f"  Mínimo: {min(valores_ap_ant)}%")
    print(f"  Máximo: {max(valores_ap_ant)}%")
    print(f"  Promedio: {round(sum(valores_ap_ant)/len(valores_ap_ant), 2)}%")
    print()

print("📌 PRIMERAS 5 APs PROCESADAS:")
for i, row in enumerate(resultados_lista[:5]):
    print(f"  {i+1}. {row['NOMBRE_TOT']}")
    print(f"     AP_ant={row['AP_ant']}% | 1km_ant={row['1km_ant']}% | 10km_ant={row['10km_ant']}%")

print("\n\n🎉 ¡PROCESAMIENTO COMPLETADO EN", tiempo_total, "MINUTOS!\n")
