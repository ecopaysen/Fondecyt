# =========================================================
# SCRIPT DE CORRECCIÓN DE MAPAS RASTER DE COBERTURA (MapBiomas)
# Corrección selectiva de píxeles dentro de polígonos
# ArcGIS Pro - Python Integration
# =========================================================
# Autor: Valentina Contreras 
# Fecha: Enero 2026
# Propósito: Cambiar valores específicos de rasters solo dentro de áreas
#           definidas por polígonos (shapefiles), sin afectar píxeles externos
# =========================================================


# =========================================================
# PARTE 1: IMPORTAR LIBRERÍAS Y ACTIVAR EXTENSIONES
# =========================================================
"""
Esta sección carga las librerías necesarias para:
- Manipulación de rasters y vectores (arcpy)
- Operaciones espaciales avanzadas (arcpy.sa - Spatial Analyst)
- Gestión de rutas de archivos (os)
"""

import arcpy               # Librería principal de ArcGIS para manipulación geoespacial
from arcpy.sa import *     # Módulo Spatial Analyst para operaciones raster avanzadas
import os                  # Librería estándar de Python para manejar rutas y carpetas

# Activar extensión Spatial Analyst (REQUERIDO para Con(), ExtractByMask, etc.)
arcpy.CheckOutExtension("Spatial")  

# Permitir sobrescribir archivos de salida existentes (evita error si archivo existe)
arcpy.env.overwriteOutput = True

print("✓ Librerías importadas exitosamente")
print("✓ Extensión Spatial Analyst activada")
print("=" * 70)


# =========================================================
# PARTE 2: DEFINIR RUTAS DE ENTRADA Y SALIDA
# =========================================================
"""
IMPORTANTE: REEMPLAZAR las rutas según tu estructura de carpetas local
Usar formato: r"C:\ruta\completa" (raw string con 'r' prefix)
"""

# -------- REEMPLAZAR CON TU RUTA DE RASTERS --------
# Carpeta donde están almacenados los rasters originales de MapBiomas
raster_folder = r"C:\Proyectos\MapBiomas\Rasters_Originales"

# -------- REEMPLAZAR CON TU RUTA DE SHAPEFILE --------
# Ruta completa del shapefile que contiene los polígonos de corrección
# El shapefile debe tener campos: Id, clase_orig, clase_corr
shp_poligono = r"C:\Proyectos\MapBiomas\Shapefiles\Correccion_zonas.shp"

# -------- REEMPLAZAR CON TU RUTA DE SALIDA --------
# Carpeta donde se guardarán los rasters corregidos
# Se recomienda crear una carpeta nueva para no sobrescribir originales
output_folder = r"C:\Proyectos\MapBiomas\Rasters_Corregidos"

# Crear la carpeta de salida automáticamente si no existe
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"✓ Carpeta de salida creada: {output_folder}")
else:
    print(f"✓ Carpeta de salida existente: {output_folder}")

print("=" * 70)


# =========================================================
# PARTE 3: CREAR LISTA DE RASTERS A PROCESAR
# =========================================================
"""
Especificar los rasters que serán corregidos.
Pueden ser de diferentes años (series temporales).
La misma corrección se aplicará a todos.

Formato: os.path.join(carpeta, "nombre_archivo.tif")
"""

# REEMPLAZAR con los nombres exactos de tus rasters
rasters = [
    os.path.join(raster_folder, "2024_coverage_lclu.tif"),
    os.path.join(raster_folder, "2020_coverage_lclu.tif"),
    os.path.join(raster_folder, "2016_coverage_lclu.tif"),
    os.path.join(raster_folder, "2012_coverage_lclu.tif")
]

print(f"Rasters a procesar ({len(rasters)} archivos):")
for i, raster in enumerate(rasters, 1):
    print(f"  {i}. {os.path.basename(raster)}")
print("=" * 70)


# =========================================================
# PARTE 4: LEER LA TABLA DE ATRIBUTOS DEL SHAPEFILE
# =========================================================
"""
Este segmento lee los atributos del shapefile que especifican:
- clase_orig: valores originales del raster a cambiar
- clase_corr: nuevo valor que reemplazará a clase_orig

Importante: Todos los polígonos DEBEN tener el mismo clase_corr
"""

# Lista para almacenar los pares (clase_orig, clase_corr)
# Cada tupla representa un cambio: (valor_original, valor_nuevo)
clases = []

# SearchCursor itera sobre todas las filas de la tabla de atributos del shapefile
# IMPORTANTE: Los nombres de los campos deben coincidir exactamente
# Si tu shapefile tiene campos diferentes, reemplazar ["clase_orig", "clase_corr"]
try:
    with arcpy.da.SearchCursor(shp_poligono, ["clase_orig", "clase_corr"]) as cursor:
        for row in cursor:
            # row[0] = clase_orig
            # row[1] = clase_corr
            clase_original = row[0]
            clase_correccion = row[1]
            clases.append((clase_original, clase_correccion))
            
    # Mostrar en pantalla las clases que se van a corregir
    print(f"✓ Tabla del shapefile leída exitosamente")
    print(f"✓ Total de registros encontrados: {len(clases)}")
    print("\nClases a corregir (original → nuevo):")
    for orig, corr in clases:
        print(f"  {orig} → {corr}")
    
    # Validación: verificar que todos tengan el mismo clase_corr
    valores_corr = [c[1] for c in clases]
    if len(set(valores_corr)) > 1:
        print("\n⚠ ADVERTENCIA: Se detectaron múltiples valores de corrección!")
        print("  El script usará el primer valor encontrado.")
        print("  Recomendación: Crear shapefiles separados para cada corrección.")
    
except Exception as e:
    print(f"✗ ERROR al leer shapefile: {e}")
    print("  Verificar que el shapefile existe y tiene campos 'clase_orig' y 'clase_corr'")
    exit()

print("=" * 70)


# =========================================================
# PARTE 5: PROCESAR CADA RASTER Y APLICAR LA CORRECCIÓN
# =========================================================
"""
Este es el núcleo del script. Para cada raster:
1. Configura el entorno para mantener alineación original
2. Crea una máscara espacial del shapefile
3. Identifica píxeles que coinciden con clase_orig
4. Aplica cambio condicional solo dentro del polígono
5. Guarda el resultado

El proceso es iterativo: raster por raster.
"""

# BUCLE PRINCIPAL: Procesar cada raster
for raster_path in rasters:
    
    print(f"\n{'='*70}")
    print(f"PROCESANDO: {os.path.basename(raster_path)}")
    print(f"{'='*70}")
    
    try:
        # --------- CONFIGURACIÓN DE ENTORNO ---------
        # Estos parámetros garantizan que el raster de salida tenga la misma
        # resolución, alineación y extensión que el original
        
        arcpy.env.snapRaster = raster_path  
        # Alinea todos los cálculos al grid del raster original
        # Evita cambios no deseados en posicionamiento
        
        arcpy.env.cellSize   = raster_path  
        # Mantiene el tamaño de celda original (típicamente 30m para Landsat)
        
        arcpy.env.extent     = raster_path  
        # Limita el análisis a la extensión exacta del raster
        
        print("✓ Entorno configurado (snapRaster, cellSize, extent)")
        
        # --------- CARGAR RASTER COMO OBJETO ---------
        # Raster() crea un objeto manipulable en memoria
        # Permite operaciones algebraicas como ==, &, |, etc.
        raster_base = Raster(raster_path)
        print(f"✓ Raster cargado en memoria")
        
        # --------- DEFINIR RUTA DE SALIDA ---------
        # El nombre del archivo se mantiene igual, pero se guarda en carpeta de salida
        raster_salida = os.path.join(output_folder, os.path.basename(raster_path))
        print(f"✓ Archivo de salida: {os.path.basename(raster_salida)}")
        
        
        # --------- CREAR MÁSCARA ESPACIAL ---------
        # Esta es la operación más crítica para garantizar que solo se cambie
        # píxeles dentro del shapefile
        
        # ExtractByMask: Extrae solo píxeles que intersectan con el shapefile
        # ~IsNull(): Invierte la máscara (1 = dentro, 0 = fuera)
        dentro_poligono = ~IsNull(ExtractByMask(raster_base, shp_poligono))
        
        print("✓ Máscara espacial creada (dentro/fuera del polígono)")
        
        
        # --------- CONSTRUIR CONDICIÓN PARA VALORES A CORREGIR ---------
        # Identifica todos los píxeles que coinciden con clase_orig
        # Si hay múltiples valores originales, se combinan con OR lógico
        
        condicion = None  # Inicializar como nulo
        
        for clase_orig, clase_corr in clases:
            # (raster_base == clase_orig) devuelve matriz booleana (True/False)
            expr = (raster_base == clase_orig)
            
            if condicion is None:
                # Primera clase original
                condicion = expr
            else:
                # Agregar más clases con OR lógico (|)
                # Esto permite múltiples valores originales
                condicion = condicion | expr
        
        print(f"✓ Condición lógica construida para {len(clases)} clase(s)")
        
        
        # --------- OBTENER VALOR DE CORRECCIÓN ---------
        # Todos los polígonos del shapefile deben tener el mismo valor de corrección
        # Se extrae del primer registro (por convención, todos deben ser iguales)
        valor_corr = clases[0][1]
        print(f"✓ Valor de corrección a aplicar: {valor_corr}")
        
        
        # --------- APLICAR CORRECCIÓN CONDICIONAL ---------
        # Esta es la función clave que permite corrección selectiva:
        # Con(condición, valor_si_verdadero, valor_si_falso)
        #
        # Lógica:
        # SI (dentro_poligono AND condicion):
        #     Cambiar a valor_corr
        # SINO:
        #     Mantener raster_base original
        
        # dentro_poligono & condicion: Ambas condiciones deben ser verdaderas
        # & = AND lógico (intersección espacial + coincidencia de valor)
        
        raster_final = Con(dentro_poligono & condicion, valor_corr, raster_base)
        
        print("✓ Corrección aplicada mediante función condicional")
        
        
        # --------- GUARDAR RASTER FINAL ---------
        # .save() escribe el raster procesado a disco
        # Mantiene automáticamente los metadatos espaciales (CRS, geotransform)
        
        raster_final.save(raster_salida)
        print(f"✓ Raster guardado: {raster_salida}")
        
        
        # --------- MENSAJES DE CONFIRMACIÓN ---------
        # Feedback al usuario sobre qué se hizo exactamente
        
        print("\n📊 RESUMEN DE CORRECCIÓN:")
        print(f"  • Clases originales corregidas: {[c[0] for c in clases]}")
        print(f"  • Todas las clases convertidas a: {valor_corr}")
        print(f"  • Área de corrección: shapefile '{os.path.basename(shp_poligono)}'")
        print(f"  • Píxeles fuera del shapefile: SIN CAMBIOS")
        print(f"  • Píxeles sin coincidencia dentro del shapefile: SIN CAMBIOS")
        print("✓ PROCESAMIENTO COMPLETADO EXITOSAMENTE")
        
    except Exception as e:
        # Capturar errores durante el procesamiento
        print(f"\n✗ ERROR durante procesamiento de {os.path.basename(raster_path)}:")
        print(f"  {str(e)}")
        print("  Continuando con próximo raster...")
        continue

print("\n" + "=" * 70)
print("✓ SCRIPT FINALIZADO - Todos los rasters han sido procesados")
print("=" * 70)
print(f"\nRasters corregidos guardados en:")
print(f"  {output_folder}")
print("\nPróximos pasos:")
print("  1. Abrir rasters corregidos en ArcGIS Pro")
print("  2. Comparar visualmente con originales")
print("  3. Verificar límites de corrección coinciden con polígonos")
print("  4. Documentar cambios realizados")
print("=" * 70)


# =========================================================
# REFERENCIAS Y NOTAS TÉCNICAS
# =========================================================
"""
FUNCIÓN Con() - Sintaxis General:
Con(in_conditional_raster, in_true_raster_or_constant, in_false_raster_or_constant)

Operadores lógicos disponibles:
  & = AND (ambas condiciones deben ser verdaderas)
  | = OR (al menos una condición es verdadera)
  ~ = NOT (invierte la condición)

Funciones de enmascaramiento:
  ExtractByMask(): Extrae valores dentro de polígono
  IsNull(): Detecta celdas sin datos (NoData)
  ~ invierte máscara para operaciones con Con()

LIMITACIONES Y CONSIDERACIONES:
  • Resolución: limitada por resolución del raster (30m típicamente)
  • Precisión de límites: pixelada según resolución raster
  • Memoria: rasters muy grandes pueden requiere optimización
  • Un solo valor de corrección: no permite heterogeneidad dentro del shapefile

TROUBLESHOOTING COMÚN:
  1. "Spatial Analyst extension not available"
     → Verificar licencia de ArcGIS Pro incluye Spatial Analyst
  
  2. "Shapefile fields not found"
     → Verificar que campos se llamen exactamente "clase_orig" y "clase_corr"
  
  3. "Raster and shapefile have different projections"
     → Reproyectar ambos al mismo CRS antes de ejecutar
  
  4. "Output raster has no data"
     → Verificar que existe intersección espacial entre raster y shapefile
"""

# FIN DEL SCRIPT
