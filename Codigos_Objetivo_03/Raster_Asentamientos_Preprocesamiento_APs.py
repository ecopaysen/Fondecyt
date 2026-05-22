#!/usr/bin/env python3
"""
================================================================================
PROCESAMIENTO Y ESTANDARIZACIÓN DE RÁSTERES DE ASENTAMIENTOS EN ÁREAS PROTEGIDAS
================================================================================

PROYECTO FONDECYT Nº 1251080
"Evaluación de las áreas protegidas y sus zonas de amortiguación en Chile: 
un análisis geoespacial de su eficacia para contrarrestar el cambio global"

AUTOR: Valentina Contreras
INSTITUCIÓN: Ecopaysen - Laboratorio de Análisis Geoespacial
FECHA: 2025
VERSION: 1.0

================================================================================
DESCRIPCIÓN GENERAL
================================================================================

Este script realiza el preprocesamiento y estandarización de rásteres de 
asentamientos humanos en Chile para análisis de cobertura dentro y alrededor 
de las 97 Áreas Protegidas (APs) terrestres del país.

El procesamiento incluye:
  1. Lectura de rásteres originales de asentamientos
  2. Clonación de propiedades espaciales (resolución, extensión, proyección)
  3. Reemplazo de valores NoData por código 2
  4. Normalización de píxeles a valores estándar: {0, 1, 2}
  5. Exportación de rásteres procesados con metadatos preservados

================================================================================
CLASIFICACIÓN DE PÍXELES
================================================================================

El ráster procesado contiene SOLO tres valores:
  • 0 = Píxeles SIN asentamientos (áreas naturales/sin clasificar)
  • 1 = Píxeles CON asentamientos (áreas antrópicas)
  • 2 = Píxeles NoData (sin información disponible)

Este esquema permite cuantificar el impacto de asentamientos humanos dentro 
y en las zonas de amortiguación de las APs hasta 10 km de distancia.

================================================================================
CONTEXTO CIENTÍFICO
================================================================================

Las zonas de amortiguación (buffers) alrededor de las Áreas Protegidas son 
vitales para evaluar la efectividad de la conservación. Este script genera 
datos estandarizados para:

  • Cuantificar presión antrópica en APs y sus alrededores
  • Identificar patrones de ocupación territorial
  • Evaluar eficacia de APs frente al cambio global
  • Comparar datos entre diferentes regiones de Chile

================================================================================
FLUJO DE TRABAJO
================================================================================

1. Identificación de rásteres de entrada (formato GeoTIFF)
2. Iteración sobre cada ráster en la carpeta especificada
3. Clonación de propiedades espaciales del original
4. Aplicación de condicionales para reemplazo NoData → 2
5. Normalización de valores de píxeles
6. Guardado de ráster procesado con MISMO nombre en carpeta de salida
7. Reporte de procesamiento completado

================================================================================
REQUISITOS TÉCNICOS
================================================================================

• Python 3.6+
• ArcGIS Desktop / ArcGIS Pro (con extensión Spatial Analyst)
• Módulos: arcpy, os, glob
• Acceso a licencias de ArcGIS
• Rásteres de entrada en formato GeoTIFF

================================================================================
FLUJO DE ENTRADA/SALIDA
================================================================================

ENTRADA:
  {INPUT_FOLDER}/
  ├── Asentamientos_raster_2015.tif
  ├── Asentamientos_raster_2020.tif
  └── [otros rásteres...]

SALIDA:
  {OUTPUT_FOLDER}/
  ├── Asentamientos_raster_2015.tif [PROCESADO]
  ├── Asentamientos_raster_2020.tif [PROCESADO]
  └── [otros rásteres procesados...]

================================================================================
CONFIGURACIÓN
================================================================================

Antes de ejecutar, modifica los siguientes parámetros:
  • INPUT_FOLDER: Ruta a carpeta con rásteres originales
  • OUTPUT_FOLDER: Ruta a carpeta de salida (se crea si no existe)
  • RASTER_PATTERN: Patrón de búsqueda (ej: "*.tif", "Asen_*.tif")

================================================================================
USO
================================================================================

1. Abrir el script en Python IDE o terminal
2. Configurar rutas de entrada/salida
3. Ejecutar: python Raster_Asentamientos_Preprocesamiento_APs.py
4. Revisar reporte de procesamiento al finalizar
5. Verificar archivos en OUTPUT_FOLDER

================================================================================
SALIDA DEL SCRIPT
================================================================================

El script genera:
  • Rásteres normalizados en OUTPUT_FOLDER
  • Reporte en consola con resumen de procesamiento
  • Conteo de rásteres procesados exitosamente/con errores

================================================================================
NOTAS IMPORTANTES
================================================================================

• Los rásteres de salida REEMPLAZAN los valores NoData por 2
• Se preservan las propiedades espaciales (CRS, resolución, extensión)
• En caso de error, se registra en consola pero continúa procesando
• Requiere permisos de escritura en OUTPUT_FOLDER
• El procesamiento puede tardar según tamaño y cantidad de rásteres

================================================================================
REFERENCIAS
================================================================================

FONDECYT Project Nº 1251080
https://www.fondecyt.cl/

Ecopaysen - Laboratorio de Análisis Geoespacial

================================================================================
"""

import arcpy
from arcpy.sa import *
import os
import glob
import sys
from datetime import datetime

print("\n" + "="*80)
print("PROCESAMIENTO Y ESTANDARIZACIÓN DE RÁSTERES DE ASENTAMIENTOS")
print("FONDECYT Nº 1251080 - APs y Zonas de Amortiguación en Chile")
print("Autor: Valentina Contreras | Ecopaysen")
print("="*80 + "\n")

# ========================================
# CONFIGURACIÓN DE RUTAS
# ========================================
# Reemplaza estas rutas según tu estructura de directorios
INPUT_FOLDER = r"C:\ruta\a\tus\rasters\input"  # Carpeta con rásteres originales
OUTPUT_FOLDER = r"C:\ruta\a\tus\rasters\output"  # Carpeta de salida

RASTER_PATTERN = "*.tif"  # Patrón de búsqueda para rásteres

# ========================================
# CONFIGURACIÓN ARCGIS
# ========================================
arcpy.env.overwriteOutput = True

try:
    arcpy.CheckOutExtension("Spatial")
except:
    print("⚠ ADVERTENCIA: No se pudo acceder a extensión Spatial Analyst")

# ========================================
# OBTENER LISTA DE RÁSTERES
# ========================================
if not os.path.exists(INPUT_FOLDER):
    print(f"❌ ERROR: La carpeta de entrada no existe: {INPUT_FOLDER}")
    sys.exit(1)

# Buscar todos los archivos .tif en la carpeta
input_rasters = glob.glob(os.path.join(INPUT_FOLDER, RASTER_PATTERN))

if not input_rasters:
    print(f"❌ ERROR: No se encontraron rásteres en: {INPUT_FOLDER}")
    sys.exit(1)

print(f"✓ Se encontraron {len(input_rasters)} rásteres para procesar")
print(f"  Entrada: {INPUT_FOLDER}")
print(f"  Salida: {OUTPUT_FOLDER}\n")

# Crear carpeta de salida si no existe
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)
    print(f"✓ Carpeta de salida creada\n")

# ========================================
# PROCESAMIENTO DE CADA RÁSTER
# ========================================
print("="*80)
print("INICIANDO PROCESAMIENTO")
print("="*80 + "\n")

total_procesados = 0
errores = 0
inicio_total = datetime.now()

for idx, raster_path in enumerate(input_rasters, 1):
    try:
        filename = os.path.basename(raster_path)
        print(f"[{idx}/{len(input_rasters)}] Procesando: {filename}")
        
        inicio = datetime.now()

        # Cargar ráster
        raster = Raster(raster_path)

        # ====================================
        # Clonar propiedades espaciales
        # ====================================
        arcpy.env.snapRaster = raster
        arcpy.env.cellSize = raster
        arcpy.env.extent = raster.extent

        # ====================================
        # Reemplazar NoData por 2
        # ====================================
        final = Con(IsNull(raster), 2, raster)

        # ====================================
        # Normalizar valores a 0, 1, 2
        # ====================================
        # Solo mantiene píxeles con valores 0, 1 o 2
        # El resto se convierte a 0
        final = Con(
            (final == 0) | (final == 1) | (final == 2),
            final,
            0
        )

        # ====================================
        # Guardar ráster procesado
        # ====================================
        output_raster = os.path.join(OUTPUT_FOLDER, filename)
        final.save(output_raster)
        
        tiempo_proceso = (datetime.now() - inicio).total_seconds()
        print(f"   ✔ Guardado en: {output_raster} ({tiempo_proceso:.1f}s)")
        total_procesados += 1

    except Exception as e:
        errores += 1
        print(f"   ✗ ERROR en {filename}: {str(e)}")

print("\n" + "="*80)
print("PROCESAMIENTO FINALIZADO")
print("="*80)
print(f"\n📊 RESUMEN:")
print(f"   Total de rásteres: {len(input_rasters)}")
print(f"   ✔ Procesados exitosamente: {total_procesados}")
print(f"   ✗ Errores: {errores}")
print(f"   Ubicación de salida: {OUTPUT_FOLDER}")

tiempo_total = (datetime.now() - inicio_total).total_seconds()
print(f"\n⏱ Tiempo total: {tiempo_total/60:.1f} minutos")
print("\n" + "="*80 + "\n")

try:
    arcpy.CheckInExtension("Spatial")
except:
    pass
