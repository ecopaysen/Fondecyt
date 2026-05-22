#!/usr/bin/env python3
"""
================================================================================
GENERACION DE BUFFERS PARA EL ANALISIS DE ASENTAMIENTOS EN APs
================================================================================

PROYECTO FONDECYT Nº 1251080
"Evaluación de las áreas protegidas y sus zonas de amortiguación en Chile: 
un análisis geoespacial de su eficacia para contrarrestar el cambio global"

AUTOR DEL CODIGO: Valentina Contreras

================================================================================
DESCRIPCIÓN GENERAL
================================================================================

Este script realiza análisis de datos de asentamientos y genera/exporta buffers
acumulativos alrededor de 97 Áreas Protegidas (AP). Calcula porcentajes de
píxeles antrópicos y naturales para cada zona de análisis.

El procesamiento incluye:
  - Análisis de AP sin modificación
  - Generación de buffers acumulativos de 1km a 10km
  - Cálculo de porcentajes de asentamientos (ant) vs natural (otros)
  - Exportación de resultados a CSV
  - Exportación opcional de shapefiles de buffers

================================================================================
FLUJO DE TRABAJO
================================================================================

1. CONFIGURACIÓN
   - Definir rutas de entrada (shapefile de AP, raster de asentamientos)
   - Definir ruta de salida (CSV con resultados)
   - Configurar opción de exportar shapefiles de buffers

2. VERIFICACIÓN
   - Validar existencia de archivos de entrada
   - Cargar cantidad de AP

3. PROCESAMIENTO POR AP
   - Para cada AP:
     * Analizar AP sin modificación
     * Generar buffers acumulativos (1-10km)
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
  - CSV con resultados de análisis (resultados_buffers.csv)
  - Shapefiles de buffers (opcional, en carpeta BUFFERS_SHAPEFILES)

================================================================================
CONFIGURACIÓN
================================================================================

Antes de ejecutar, modifica los siguientes parámetros:

  • ruta_ap: Ruta al shapefile de Áreas Protegidas
  • ruta_img: Ruta al raster de asentamientos
  • ruta_csv_salida: Ruta de salida para el CSV de resultados
  • EXPORTAR_BUFFERS: True para exportar shapefiles, False para solo CSV
  • ruta_buffers: Carpeta de salida para shapefiles (si EXPORTAR_BUFFERS=True)

================================================================================
USO
================================================================================

1. Abrir el script en Python IDE (ArcGIS Pro Python Console recomendado)
2. Configurar rutas de entrada/salida
3. Cambiar EXPORTAR_BUFFERS a True si desea exportar shapefiles
4. Ejecutar: python Generacion_buffer_analisis_Asentamientos_en_APs.py
5. Revisar reporte de procesamiento en consola
6. Verificar archivos en ruta_csv_salida y ruta_buffers

================================================================================
SALIDA DEL SCRIPT
================================================================================

El script genera:
  • CSV con porcentajes de asentamientos para AP y cada buffer (1-10km)
  • Reporte detallado en consola con progreso y resultados por AP
  • Estadísticas finales (mín, máx, promedio)
  • Shapefiles de buffers acumulativos (opcional)
  • Información de ubicación de archivos generados

================================================================================
NOTAS IMPORTANTES - BUFFERS ACUMULATIVOS
================================================================================

• BUFFERS ACUMULATIVOS: Cada buffer es acumulativo desde el borde de la AP
  - AP_ant = Solo AP original
  - 1km_ant = Desde borde AP hasta 1km (solo anillo 1km, SIN AP)
  - 2km_ant = Desde borde AP hasta 2km (anillo 1km + 2km, SIN AP)
  - 3km_ant = Desde borde AP hasta 3km (anillo 1km + 2km + 3km, SIN AP)
  - ...
  - 10km_ant = Desde borde AP hasta 10km (todos los anillos acumulados, SIN AP)

• CÁLCULO DE BUFFERS:
  - Buffer completo = AP buffer hacia afuera en km kilómetros
  - Buffer sin AP = Buffer completo - AP original
  - Esto asegura que el buffer NO incluya la AP

• CÁLCULO DE PORCENTAJES:
  - ant = SOLO píxeles valor 1 (antrópico/asentamientos)
  - otros = SOLO píxeles valor 0 (natural/vegetación)
  - nodata (2) = se calcula pero NO se incluye en porcentajes
  - Porcentaje = (ant / (ant + otros)) × 100

• EXPORTACIÓN DE SHAPEFILES:
  - Cambiar EXPORTAR_BUFFERS = True para activar
  - Se crea una carpeta por AP con buffers como archivos separados
  - Cada carpeta contiene:
    * AP_original.shp = Geometría original del AP
    * Buffer_1km.shp = Buffer desde borde AP hasta 1km
    * Buffer_2km.shp = Buffer desde borde AP hasta 2km
    * ... hasta Buffer_10km.shp

================================================================================
DIFERENCIA ENTRE ANILLOS Y BUFFERS
================================================================================

ANILLOS INDEPENDIENTES (Generacion_anillos_analisis_Asentamientos_en_APs.py):
  - Cada anillo es completamente independiente del anterior
  - 1km_ant = SOLO anillo 1km (sin AP, sin anillo 0-1km)
  - 2km_ant = SOLO anillo 2km (sin AP, sin anillo 1km)
  - No hay acumulación, cada uno es aislado

BUFFERS ACUMULATIVOS (Este script):
  - Cada buffer es acumulativo desde el borde de la AP
  - 1km_ant = Desde borde AP hasta 1km (acumula solo 1km)
  - 2km_ant = Desde borde AP hasta 2km (acumula 1km + 2km)
  - Hay acumulación, cada uno contiene los anteriores

================================================================================
CÁLCULO DE DATOS
================================================================================

El script analiza píxeles raster con los siguientes valores:
  - 1 = Antrópico (asentamientos, zonas urbanas, etc.)
  - 0 = Natural (vegetación, agua, terreno natural)
  - 2 = NoData (sin información)

Para cada zona (AP, Buffer_1km, Buffer_2km, etc.):
  1. Extrae los píxeles dentro de la geometría
  2. Cuenta píxeles con valor 1 (antrópico)
  3. Cuenta píxeles con valor 0 (natural)
  4. Cuenta píxeles con valor 2 (nodata) para referencia
  5. Calcula porcentajes EXCLUYENDO nodata: (ant / (ant + otros)) × 100
  6. Almacena en CSV junto con metadatos de la AP

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
  - AP_ant: % asentamientos en AP
  - AP_otros: % natural en AP
  - 1km_ant: % asentamientos buffer 1km acumulativo
  - 1km_otros: % natural buffer 1km acumulativo
  - 2km_ant: % asentamientos buffer 2km acumulativo
  - 2km_otros: % natural buffer 2km acumulativo
  - ... hasta 10km_ant y 10km_otros

================================================================================
EXPORTACIÓN DE SHAPEFILES
================================================================================

Cuando EXPORTAR_BUFFERS = True:

Estructura de carpetas generada:
  BUFFERS_SHAPEFILES/
  ├── AP_001_Parque_Nacional_Chiloe/
  │   ├── AP_original.shp
  │   ├── AP_original.shx
  │   ├── AP_original.dbf
  │   ├── Buffer_1km.shp
  │   ├── Buffer_1km.shx
  │   ├── Buffer_1km.dbf
  │   ├── Buffer_2km.shp
  │   ├── Buffer_2km.shx
  │   ├── Buffer_2km.dbf
  │   └── ... hasta Buffer_10km.*
  ├── AP_002_Parque_Nacional_Otro/
  │   └── ... (mismo patrón)
  └── AP_097_...

Cada shapefile de buffer es un POLYGON que representa el área acumulativa
desde el borde de la AP hasta esa distancia.

================================================================================
INTERPRETACIÓN DE RESULTADOS
================================================================================

Alto porcentaje de asentamientos en AP:
  - Indica presión antrópica dentro del área protegida
  - Puede sugerir infiltración de asentamientos o zonas urbanas

Bajo porcentaje de asentamientos en buffers:
  - Indica que el área amortiguadora es principalmente natural
  - Protección efectiva del área

Alto porcentaje en buffers cercanos (1-2km):
  - Presión directa en las zonas inmediatas a la AP
  - Riesgo de expansión urbana

Aumento gradual de asentamientos hacia distancias mayores:
  - Patrón normal de ocupación del territorio
  - Fragmentación del paisaje natural

Porcentaje constante en todos los buffers:
  - Ocupación uniforme del territorio alrededor de la AP
  - Patrón de desarrollo territorial consistente

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

Raster de asentamientos (Asen_buf_2015_modificado.tif):
  - Tipo: GeoTIFF
  - Valores: 0 (natural), 1 (antrópico), 2 (nodata)
  - Proyección: Debe coincidir con el shapefile
  - Cobertura: Debe cubrir todas las AP y sus buffers
  - Año: 2015

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

ERROR en calcular_porcentajes_numpy:
  → Puede ser que el raster y shapefile tengan proyecciones diferentes
  → Verificar que proyecciones coinciden
  → Verificar que buffers están dentro de cobertura raster

CSV vacío o con pocos datos:
  → Verificar que raster contiene valores 0, 1, 2
  → Verificar que geometrías del shapefile son válidas
  → Probar con una AP individual primero

Shapefiles no se generan:
  → Verificar EXPORTAR_BUFFERS = True
  → Verificar que ruta_buffers existe y tiene permisos de escritura
  → Verificar espacio en disco suficiente

================================================================================
CASOS DE USO
================================================================================

1. Evaluación de eficacia de áreas protegidas:
   - Analizar expansión de asentamientos dentro y alrededor de APs
   - Identificar APs bajo mayor presión antrópica

2. Planificación de zonas de amortiguación:
   - Determinar ancho efectivo de buffer según ocupación del territorio
   - Recomendar expansión de zonas de protección

3. Monitoreo de cambio de uso de suelo:
   - Comparar resultados con análisis anteriores
   - Detectar cambios en ocupación territorial

4. Priorización de recursos:
   - Identificar APs que requieren mayor vigilancia
   - Asignar recursos de manejo según presión antrópica

5. Investigación de fragmentación del paisaje:
   - Analizar conectividad de hábitat natural
   - Evaluar barreras a la dispersión de fauna

================================================================================
NOTAS DE RENDIMIENTO
================================================================================

- Tiempo de procesamiento: ~1-2 minutos por AP (depende del hardware)
- Memoria requerida: 8GB RAM mínimo recomendado
- Espacio en disco: ~1-2GB para CSV + shapefiles
- Uso de extensión Spatial: Se checkOut/CheckIn automáticamente
- Operaciones: Se usan arrays NumPy para mejor rendimiento

Para optimizar:
  - Usar SSD en lugar de HDD
  - Aumentar memoria RAM del equipo
  - Reducir resolución del raster si es posible
  - Procesar en lotes más pequeños si hay limitaciones

================================================================================
AUTORES Y REFERENCIAS
================================================================================

Código: Valentina Contreras
Proyecto: FONDECYT Nº 1251080
Institución: [Institución responsable]
Año: 2025-2026

Referencias:
  - ArcPy Documentation: https://pro.arcgis.com/en/pro-app/latest/arcpy/
  - NumPy Documentation: https://numpy.org/doc/
  - ESRI Spatial Analyst: https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-analyst/

================================================================================
HISTORIAL DE VERSIONES
================================================================================

v1.0 - 2025-2026:
  - Script inicial para análisis de asentamientos en APs
  - Generación de buffers acumulativos 1-10km
  - Exportación a CSV y shapefiles opcionales
  - Estadísticas finales por AP

================================================================================
"""

import arcpy
import os
import csv
import numpy as np
from arcpy import sa
import time

print("\n" + "="*70)
print("PROCESAMIENTO FONDECYT - 97 APs (BUFFERS ACUMULATIVOS SIN AP)")
print("="*70)

# ======================================================
# CONFIGURACIÓN
# ======================================================

ruta_ap = r"C:\Users\valen\Desktop\Fondecyt\areas_protegidas_totales_actualizadas-20251109T203707Z-1-001\AP_terrestres_actualizadas_26marz26\AP_terrestres_actualizadas_26marz26.shp"

ruta_img = r"C:\Users\valen\Desktop\Fondecyt\settlements\Asentamientos_raster_Chile_clip\modificado\Asen_buf_2015_modificado.tif"

ruta_csv_salida = r"C:\Users\valen\Desktop\Fondecyt\settlements\CSV\csv_anillos\resultados_buffers.csv"

# ====== OPCIÓN: EXPORTAR SHAPEFILES DE BUFFERS ======
# Cambiar a True si quieres exportar los shapefiles
EXPORTAR_BUFFERS = False  # ← CAMBIAR A True PARA EXPORTAR
ruta_buffers = r"C:\Users\valen\Desktop\Fondecyt\settlements\CSV\csv_anillos\BUFFERS_SHAPEFILES"
# ====================================================

distancias_km = list(range(1, 11))

os.makedirs(os.path.dirname(ruta_csv_salida), exist_ok=True)

if EXPORTAR_BUFFERS:
    os.makedirs(ruta_buffers, exist_ok=True)

print("\n📁 CONFIGURACIÓN:")
print(f"  AP: {ruta_ap}")
print(f"  Imagen: {ruta_img}")
print(f"  CSV salida: {ruta_csv_salida}")
if EXPORTAR_BUFFERS:
    print(f"  Buffers shapefiles: {ruta_buffers}")

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
    # EXPORTAR SHAPEFILES DE BUFFERS (OPCIONAL)
    # ======================================================
    if EXPORTAR_BUFFERS:
        # Crear carpeta para esta AP
        carpeta_ap = os.path.join(ruta_buffers, f"AP_{idx:03d}_{nombre_ap.replace(' ', '_')}")
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
    # BUFFERS ACUMULATIVOS (restando AP - desde borde hacia afuera)
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
        
        # Exportar shapefile del buffer si está habilitado
        if EXPORTAR_BUFFERS:
            try:
                fc_buffer = os.path.join(carpeta_ap, f"Buffer_{km}km.shp")
                arcpy.management.CreateFeatureclass(
                    carpeta_ap, f"Buffer_{km}km", geometry_type="POLYGON"
                )
                with arcpy.da.InsertCursor(fc_buffer, ['SHAPE@']) as cursor_insert:
                    cursor_insert.insertRow([buffer_sin_ap])
            except:
                pass
    
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
print(f"  Tipo: BUFFERS ACUMULATIVOS (desde borde AP hacia afuera)")
if EXPORTAR_BUFFERS:
    print(f"  Buffers exportados: SÍ")
else:
    print(f"  Buffers exportados: NO (cambiar EXPORTAR_BUFFERS = True)")
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

if EXPORTAR_BUFFERS:
    print(f"\n📁 Shapefiles guardados en:")
    print(f"   {ruta_buffers}")

print("\n\n🎉 ¡PROCESAMIENTO COMPLETADO EN", tiempo_total, "MINUTOS!\n")
