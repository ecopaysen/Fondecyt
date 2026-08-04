"""
Conversión de ráster a polígono con filtro de superficie
==============================================================================

Este script automatiza el procesamiento de datos geoespaciales en ArcGIS para:
1. Convertir un archivo ráster (imagen de cuadrícula) en polígonos vectoriales
2. Calcular la superficie de cada polígono en hectáreas
3. Filtrar y conservar solo los polígonos que cumplan con un tamaño mínimo
4. Exportar los resultados a un archivo shapefile (.shp)

Casos de uso: identificar fragmentos de hábitat o cobertura vegetal, analizar
patrones de conectividad entre parches, eliminar ruido y polígonos demasiado
pequeños.

Flujo del proceso:
    Ráster Input → Conversión Vectorial → Cálculo de Área → Filtrado → Shapefile Output

Requisitos:
- ArcGIS Pro con extensión Spatial Analyst
- Archivo ráster de entrada (formato: .tif, .img, .asc, etc.)
- Permisos de escritura en la carpeta de salida

------------------------------------------------------------------------------
CÓMO USAR ESTE SCRIPT
------------------------------------------------------------------------------
1. Revisa la sección "CONFIGURACIÓN DE ENTRADA Y SALIDA" más abajo. Ahí
   encontrarás variables marcadas con ">>> REEMPLAZAR <<<" que debes
   completar con tus propias rutas y valores.
2. Revisa también la sección "PARÁMETROS DE PROCESAMIENTO" si necesitas
   ajustar el sistema de coordenadas o el umbral de superficie mínima.
3. No es necesario modificar el resto del código para un uso estándar; la
   función `main()` ya está preparada para recibir esos datos de entrada.
4. Ejecuta el script directamente (`python raster_a_poligono_filtrado.py`)
   una vez completada la configuración.
------------------------------------------------------------------------------
"""

import arcpy
import os

# ==============================================================================
# CONFIGURACIÓN DE ENTRADA Y SALIDA
# ==============================================================================
# Completa las siguientes variables con tus propios datos antes de ejecutar
# el script. Cada una está marcada con ">>> REEMPLAZAR <<<".
# Ejemplo Windows: r"C:\Users\TuUsuario\Documentos\Datos\raster_mascara.tif"
# Ejemplo Linux/Mac: r"/home/usuario/datos/raster_mascara.tif"
# ==============================================================================

# INPUT — Ruta completa del archivo ráster de entrada.
# Debe ser un archivo ráster válido con celdas de valor numérico.
raster_entrada = r"CAMBIA_ESTA_RUTA\Tu_Raster_Mascara.tif"  # >>> REEMPLAZAR <<< por la ruta real del ráster de entrada

# INPUT — Carpeta de salida donde se guardarán los resultados.
# Si la carpeta no existe, el script la crea automáticamente.
output_folder = r"CAMBIA_ESTA_RUTA\Carpeta_Salida"  # >>> REEMPLAZAR <<< por la carpeta de salida deseada

# INPUT — Nombre del archivo shapefile de salida.
# Se guardará automáticamente dentro de `output_folder`.
nombre_salida = "Parches_Habitat_Filtrados.shp"  # >>> REEMPLAZAR <<< si quieres otro nombre de archivo

# ==============================================================================
# PARÁMETROS DE PROCESAMIENTO
# ==============================================================================

# INPUT — Sistema de Coordenadas: especifica la proyección del proyecto.
# EPSG 32719 = WGS 1984 UTM Zone 19S (común para América del Sur).
# Otros códigos comunes:
#   - 32718 (UTM 18S)
#   - 32720 (UTM 20S)
#   - 4326  (WGS 84 Geográfico)
sr_utm19s = arcpy.SpatialReference(32719)  # >>> REEMPLAZAR <<< el código EPSG si tu zona de trabajo es distinta

# INPUT — Umbral de superficie mínima en hectáreas.
# Los polígonos más pequeños que este valor serán eliminados.
# Ejemplo: 2.5 ha elimina fragmentos muy pequeños.
umbral_ha = 2.5  # >>> REEMPLAZAR <<< por el umbral mínimo que necesites

# ==============================================================================
# PROCESAMIENTO
# ==============================================================================

def main():
    """
    Función principal que ejecuta todo el procesamiento.

    Flujo interno:
    1. Valida que el archivo de entrada exista y que la carpeta de salida
       esté disponible (creándola si es necesario).
    2. Configura el entorno de ArcGIS (sobrescritura de resultados y sistema
       de coordenadas de salida).
    3. Convierte el ráster de entrada a polígonos vectoriales.
    4. Calcula la superficie de cada polígono en hectáreas.
    5. Filtra los polígonos según el umbral mínimo definido y exporta el
       resultado final a un shapefile.

    No recibe parámetros directamente: toma sus valores de las variables de
    configuración definidas más arriba (`raster_entrada`, `output_folder`,
    `nombre_salida`, `sr_utm19s`, `umbral_ha`).
    """

    try:
        # Validación inicial
        print("=" * 80)
        print("INICIANDO PROCESAMIENTO DE RÁSTER A POLÍGONO")
        print("=" * 80)

        # Se verifica que el archivo ráster de entrada exista físicamente
        if not os.path.exists(raster_entrada):
            raise FileNotFoundError(f"Archivo de entrada no encontrado: {raster_entrada}")

        # Se crea la carpeta de salida si aún no existe
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"✓ Carpeta de salida creada: {output_folder}")

        # Configurar el entorno de ArcGIS:
        # - overwriteOutput permite sobrescribir resultados de corridas anteriores
        # - outputCoordinateSystem asegura que toda salida quede en el sistema definido
        arcpy.env.overwriteOutput = True
        arcpy.env.outputCoordinateSystem = sr_utm19s

        print(f"\n[1/4] Leyendo archivo de entrada...")
        print(f"      Archivo: {raster_entrada}")
        print(f"      Sistema de coordenadas: UTM 19S (EPSG: 32719)")

        # ----------------------------------------------------------------------
        # PASO 1: Convertir ráster a polígono
        # ----------------------------------------------------------------------
        # Cada celda del ráster se transforma en un polígono vectorial. Se usa
        # "NO_SIMPLIFY" para conservar los bordes exactos de los píxeles (sin
        # suavizar los contornos), y "Value" como campo que identifica la
        # clase de cada celda.
        print(f"\n[2/4] Convirtiendo ráster a polígonos...")
        poligono_temp = arcpy.management.CreateUniqueName(
            "temp_vector",
            arcpy.env.scratchGDB
        )

        arcpy.conversion.RasterToPolygon(
            in_raster=raster_entrada,
            out_polygon_features=poligono_temp,
            simplify="NO_SIMPLIFY",  # Mantiene bordes exactos de píxeles
            raster_field="Value"
        )
        print(f"      ✓ Polígonos generados (temporal)")

        # ----------------------------------------------------------------------
        # PASO 2: Calcular la superficie en hectáreas
        # ----------------------------------------------------------------------
        # Se agrega un nuevo campo "Superficie_HA" a la capa temporal, calculado
        # a partir de la geometría de cada polígono en el sistema de coordenadas
        # definido (UTM, para asegurar unidades métricas correctas).
        print(f"\n[3/4] Calculando superficie de cada polígono...")
        arcpy.management.CalculateGeometryAttributes(
            in_features=poligono_temp,
            geometry_property=[["Superficie_HA", "AREA"]],
            area_unit="HECTARES",
            coordinate_system=sr_utm19s
        )
        print(f"      ✓ Campo 'Superficie_HA' calculado")

        # ----------------------------------------------------------------------
        # PASO 3: Filtrar por tamaño mínimo y exportar
        # ----------------------------------------------------------------------
        # Se seleccionan únicamente los polígonos cuya superficie sea mayor o
        # igual al umbral mínimo definido (`umbral_ha`), y se exportan como
        # shapefile final a la carpeta de salida.
        print(f"\n[4/4] Filtrando polígonos (mínimo: {umbral_ha} ha)...")
        ruta_final = os.path.join(output_folder, nombre_salida)

        expresion_filtro = f"Superficie_HA >= {umbral_ha}"
        arcpy.analysis.Select(
            in_features=poligono_temp,
            out_feature_class=ruta_final,
            where_clause=expresion_filtro
        )
        print(f"      ✓ Filtrado completado")

        # Mensaje de éxito con resumen del proceso
        print("\n" + "=" * 80)
        print("✅ PROCESAMIENTO COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        print(f"\nArchivo de salida guardado en:")
        print(f"  {ruta_final}")
        print(f"\nParámetros utilizados:")
        print(f"  - Umbral mínimo: {umbral_ha} hectáreas")
        print(f"  - Sistema de coordenadas: UTM 19S")
        print(f"\nPróximos pasos:")
        print(f"  1. Abre el archivo .shp en ArcGIS para visualizar resultados")
        print(f"  2. Verifica la columna 'Superficie_HA' para confirmar filtrado")
        print(f"  3. Realiza análisis adicionales de conectividad si es necesario")

    except arcpy.ExecuteError as e:
        # Captura errores específicos generados por herramientas de ArcGIS
        print("\n" + "=" * 80)
        print("❌ ERROR EN LA EJECUCIÓN DE ARCGIS")
        print("=" * 80)
        print(arcpy.GetMessages(2))
        print(f"\nTrucos para solucionar:")
        print(f"  - Verifica que el archivo ráster sea válido")
        print(f"  - Comprueba que tienes permisos de escritura en la carpeta destino")
        print(f"  - Asegúrate que ArcGIS Pro está correctamente instalado")

    except FileNotFoundError as e:
        # Captura errores de archivo no encontrado (ej. ruta mal escrita)
        print("\n" + "=" * 80)
        print("❌ ARCHIVO NO ENCONTRADO")
        print("=" * 80)
        print(f"Error: {e}")
        print(f"\nVerifica que:")
        print(f"  - La ruta del archivo está correcta")
        print(f"  - El archivo existe y no está en uso")
        print(f"  - La ruta no contiene caracteres especiales problemáticos")

    except Exception as e:
        # Captura cualquier otro error inesperado no contemplado arriba
        print("\n" + "=" * 80)
        print("❌ ERROR INESPERADO")
        print("=" * 80)
        print(f"Error: {e}")
        print(f"\nContacta al administrador si el problema persiste")


# ==============================================================================
# EJECUCIÓN
# ==============================================================================

if __name__ == "__main__":
    main()
