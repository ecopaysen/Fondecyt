"""
Generador de centroides para análisis de conectividad
==============================================================================

Este script genera centroides representativos de las Áreas Protegidas (AP)
a partir de polígonos de hábitat previamente filtrados, siguiendo un
procedimiento de dos pasos:

1. Se calcula el centroide GENERAL de todo el hábitat dentro de cada AP
   (unión de todos los parches/teselas de hábitat presentes en esa AP).
2. Si ese centroide general cae DENTRO del hábitat, se usa directamente.
   Si cae FUERA del hábitat (por ejemplo, porque el hábitat tiene una forma
   irregular o está fragmentado en varias teselas separadas), se busca en
   su lugar el centroide de la tesela de hábitat más cercana al centroide
   general, y ese pasa a ser el centroide final de la AP.

El resultado es un shapefile de puntos (uno por AP) que hereda los campos
del shapefile de Áreas Protegidas, más una serie de campos adicionales que
documentan cómo se calculó cada centroide (área total de hábitat, perímetro,
si el centroide quedó dentro del hábitat, tipo de centroide usado y
distancia respecto al centroide general).

------------------------------------------------------------------------------
CÓMO USAR ESTE SCRIPT
------------------------------------------------------------------------------
1. Revisa la sección "CONFIGURACIÓN" más abajo. Ahí encontrarás variables
   marcadas con ">>> REEMPLAZAR <<<" que debes completar con tus propias
   rutas y valores.
2. No es necesario modificar el resto del código para un uso estándar; las
   funciones ya están preparadas para recibir esos datos de entrada.
3. Ejecuta el script directamente (`python generador_centroides.py`) una vez
   completada la configuración.
------------------------------------------------------------------------------
"""

import arcpy
import os
import sys
import datetime
from pathlib import Path

# ==============================================================================
# CONFIGURACIÓN - AJUSTAR ESTAS RUTAS SEGÚN TU PROYECTO
# ==============================================================================
# Completa las siguientes variables con tus propios datos antes de ejecutar
# el script. Cada una está marcada con ">>> REEMPLAZAR <<<".
# ==============================================================================

# INPUT — Ruta base del proyecto. A partir de esta carpeta se construyen las
# demás rutas relativas (entrada y salida).
CARPETA_BASE = r"C:\ruta\a\tu\proyecto\conectividad"  # >>> REEMPLAZAR <<< por la carpeta base de tu proyecto

# INPUT — Ruta al shapefile de polígonos de hábitat ya filtrados por tamaño
# mínimo (por ejemplo, la salida del script de "ráster a polígono filtrado").
RUTA_POLIGONOS_FILTRADOS = os.path.join(CARPETA_BASE, "datos", "poligonos_filtrados.shp")  # >>> REEMPLAZAR <<< si tu archivo tiene otro nombre/ubicación

# INPUT — Ruta al shapefile de Áreas Protegidas (AP), cuyos campos se
# heredarán en el shapefile de centroides.
RUTA_SHAPEFILE_AP = os.path.join(CARPETA_BASE, "datos", "areas_protegidas.shp")  # >>> REEMPLAZAR <<< si tu archivo tiene otro nombre/ubicación

# INPUT — Carpeta donde se guardará el shapefile de centroides resultante.
# Si no existe, el script la crea automáticamente.
CARPETA_SALIDA_CENTROIDES = os.path.join(CARPETA_BASE, "resultados", "centroides")  # >>> REEMPLAZAR <<< por la carpeta de salida deseada

# INPUT — Nombre del shapefile de salida con los centroides finales.
NOMBRE_SHAPEFILE_CENTROIDES = "centroides_finales.shp"  # >>> REEMPLAZAR <<< si quieres otro nombre de archivo

# ==============================================================================
# PARÁMETROS DEL ANÁLISIS
# ==============================================================================

# INPUT — Sistema de coordenadas de trabajo.
# EPSG 32719 = WGS 1984 UTM Zona 19S (común para Chile continental).
SR_UTM = arcpy.SpatialReference(32719)  # >>> REEMPLAZAR <<< el código EPSG si tu zona de trabajo es distinta

# INPUT — Umbral de superficie mínima de parches (hectáreas). Se incluye aquí
# como referencia del filtro ya aplicado a `RUTA_POLIGONOS_FILTRADOS`; no
# vuelve a filtrar dentro de este script.
UMBRAL_HA = 2.5  # >>> REEMPLAZAR <<< por el umbral mínimo que hayas usado en el filtrado previo

# Campos que NO se heredan del shapefile de AP (campos de geometría interna
# de ArcGIS que no aportan información temática y que además no deben
# duplicarse en la capa de puntos de salida).
CAMPOS_EXCLUIR = {"Shape", "Shape_Length", "Shape_Area", "Shape_Leng",
                  "Shape_Le_1", "Shape_Le_2", "Shape_Le_3"}

# ==============================================================================
# FUNCIONES DE APOYO
# ==============================================================================

def log(mensaje, nivel="INFO"):
    """
    Registra un mensaje con marca de tiempo, tanto en la consola de Python
    como en el panel de mensajes de ArcGIS (arcpy.AddMessage).

    Parameters
    ----------
    mensaje : str
        Texto del mensaje a mostrar.
    nivel : str
        Etiqueta de nivel del mensaje (por ejemplo "INFO", "WARN", "ERROR"),
        solo con fines de lectura en consola.
    """
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    msg = f"[{hora}] [{nivel}] {mensaje}"
    print(msg)
    arcpy.AddMessage(msg)

def eliminar_si_existe(ruta):
    """
    Elimina un archivo o capa temporal si ya existe.

    Se usa para limpiar resultados de corridas anteriores antes de volver a
    generarlos, evitando conflictos de sobrescritura.

    Parameters
    ----------
    ruta : str
        Ruta (o nombre de capa en memoria) a verificar y eliminar si existe.
    """
    if arcpy.Exists(ruta):
        arcpy.management.Delete(ruta)
        log(f"Eliminado: {ruta}")

def validar_rutas():
    """
    Valida que los archivos de entrada definidos en la CONFIGURACIÓN
    (polígonos filtrados y shapefile de AP) existan antes de iniciar el
    procesamiento.

    Returns
    -------
    bool
        True si ambos archivos existen, False si falta alguno (en cuyo caso
        se registra un mensaje de error indicando cuál).
    """
    if not arcpy.Exists(RUTA_POLIGONOS_FILTRADOS):
        log(f"ERROR: No se encuentra {RUTA_POLIGONOS_FILTRADOS}", "ERROR")
        return False
    if not arcpy.Exists(RUTA_SHAPEFILE_AP):
        log(f"ERROR: No se encuentra {RUTA_SHAPEFILE_AP}", "ERROR")
        return False
    return True

# ==============================================================================
# PROCESO PRINCIPAL
# ==============================================================================

def ejecutar_generador_centroides():
    """
    Genera los centroides finales de cada Área Protegida mediante un
    procedimiento de dos pasos (centroide general → tesela más cercana si
    corresponde).

    Flujo interno:
    0. Valida rutas de entrada y prepara el entorno de ArcGIS.
    1. Crea la estructura del shapefile de salida (feature class de puntos)
       y le agrega tanto los campos heredados del shapefile de AP como los
       campos nuevos propios del análisis de centroides.
    2. Recorre cada Área Protegida, selecciona los polígonos de hábitat que
       intersectan con ella, calcula el centroide general del hábitat y
       determina si ese punto cae dentro o fuera del hábitat:
         - Si cae DENTRO, se usa el centroide general tal cual.
         - Si cae FUERA, se busca la tesela de hábitat más cercana y se usa
           el centroide de esa tesela en su lugar.
    3. Calcula área total (ha) y perímetro total (m) del hábitat dentro de
       cada AP, y escribe una fila por AP en el shapefile de centroides.

    No recibe parámetros directamente: toma sus valores de las variables de
    configuración definidas más arriba (`RUTA_POLIGONOS_FILTRADOS`,
    `RUTA_SHAPEFILE_AP`, `CARPETA_SALIDA_CENTROIDES`,
    `NOMBRE_SHAPEFILE_CENTROIDES`, `SR_UTM`).
    """

    log("="*70)
    log("INICIANDO GENERADOR DE CENTROIDES - FONDECYT")
    log("="*70)

    # --- Validación de entrada ---
    log("VALIDACIÓN: Verificando rutas de entrada...")
    if not validar_rutas():
        log("Proceso cancelado por rutas inválidas", "ERROR")
        return

    # --- Configuración de entorno ---
    log("CONFIGURACIÓN: Preparando entorno...")
    arcpy.env.overwriteOutput = True
    arcpy.env.addOutputsToMap = False

    # Crear carpeta de salida si no existe
    if not os.path.exists(CARPETA_SALIDA_CENTROIDES):
        os.makedirs(CARPETA_SALIDA_CENTROIDES)
        log(f"Carpeta creada: {CARPETA_SALIDA_CENTROIDES}")

    # --------------------------------------------------------------------------
    # PASO 0: Crear estructura de feature class de centroides
    # --------------------------------------------------------------------------
    log("PASO 0: Creando estructura de centroides...")
    ruta_centroides = os.path.join(CARPETA_SALIDA_CENTROIDES, NOMBRE_SHAPEFILE_CENTROIDES)
    eliminar_si_existe(ruta_centroides)

    # Se crea una capa de puntos vacía, en el sistema de coordenadas definido,
    # que luego se irá llenando con un centroide por cada AP
    arcpy.management.CreateFeatureclass(
        CARPETA_SALIDA_CENTROIDES,
        NOMBRE_SHAPEFILE_CENTROIDES,
        "POINT",
        spatial_reference=SR_UTM
    )
    log(f"Feature class creado: {ruta_centroides}")

    # --- Heredar campos del shapefile de AP ---
    # Se recorren todos los campos del shapefile de AP y se replican en la
    # capa de centroides (excluyendo campos de geometría interna definidos
    # en CAMPOS_EXCLUIR). Los nombres se acortan a 10 caracteres por la
    # restricción de longitud de nombres de campo en shapefiles.
    log("Heredando campos de Áreas Protegidas...")
    campos_ap = []
    for field in arcpy.ListFields(RUTA_SHAPEFILE_AP):
        if field.type not in ("OID", "Geometry") and field.name not in CAMPOS_EXCLUIR:
            # Limitar nombre a 10 caracteres (restricción de shapefiles)
            nombre_limpio = field.name[:10]
            tipo = "TEXT" if field.type == "String" else \
                   "DOUBLE" if field.type in ("Double", "Single") else "LONG"
            largo = field.length if tipo == "TEXT" else None

            arcpy.management.AddField(ruta_centroides, nombre_limpio, tipo,
                                    field_length=largo)
            campos_ap.append((field.name, nombre_limpio))
            log(f"  Campo heredado: {field.name} → {nombre_limpio}")

    # --- Campos nuevos específicos del análisis ---
    # Estos campos documentan cómo se generó cada centroide (útil para
    # revisar y auditar los resultados más adelante)
    log("Añadiendo campos del análisis de centroides...")
    campos_nuevos = [
        ("AP_OID", "LONG", None),
        ("ARE_HA_TOT", "DOUBLE", None),      # Área total en ha
        ("PERI_M_TOT", "DOUBLE", None),      # Perímetro total en m
        ("EN_HABITAT", "TEXT", 5),           # ¿Centroide en hábitat? SI/NO
        ("CENTR_TIPO", "TEXT", 20),          # GENERAL o TESELA_CERCANA
        ("DIST_CENTR", "DOUBLE", None)       # Distancia a centroide general (m)
    ]

    for c_nombre, c_tipo, c_largo in campos_nuevos:
        arcpy.management.AddField(ruta_centroides, c_nombre, c_tipo,
                                field_length=c_largo)
        log(f"  Campo añadido: {c_nombre} ({c_tipo})")

    # --------------------------------------------------------------------------
    # PASO 1 Y 2: Procesar cada AP
    # --------------------------------------------------------------------------
    log("="*70)
    log("PASO 1-2: Calculando centroides por AP...")
    log("="*70)

    # Se crean capas de trabajo en memoria para acelerar las selecciones
    # espaciales repetidas (una por cada AP)
    arcpy.env.workspace = "memory"
    capa_ap = arcpy.management.MakeFeatureLayer(RUTA_SHAPEFILE_AP, "lyr_ap")
    capa_poligonos = arcpy.management.MakeFeatureLayer(RUTA_POLIGONOS_FILTRADOS,
                                                       "lyr_poligonos")

    oid_field = arcpy.Describe(RUTA_SHAPEFILE_AP).OIDFieldName
    nombres_campos_heredados = [c[1] for c in campos_ap]
    columnas_insertar = (["SHAPE@XY"] + nombres_campos_heredados +
                        ["AP_OID", "ARE_HA_TOT", "PERI_M_TOT",
                         "EN_HABITAT", "CENTR_TIPO", "DIST_CENTR"])

    contador_ap = 0
    contador_exitosos = 0

    # Cursor de inserción: escribe una fila por cada AP procesada en el
    # shapefile de centroides de salida
    with arcpy.da.InsertCursor(ruta_centroides, columnas_insertar) as cursor_ins:
        # Cursor de búsqueda: recorre cada AP del shapefile de entrada
        with arcpy.da.SearchCursor(RUTA_SHAPEFILE_AP,
                                  [oid_field, "SHAPE@"] +
                                  [c[0] for c in campos_ap]) as cursor_ap:

            for fila_ap in cursor_ap:
                contador_ap += 1
                oid_ap = fila_ap[0]
                geom_ap = fila_ap[1]
                atributos_ap = list(fila_ap[2:])

                # Seleccionar el AP actual dentro de la capa de AP
                arcpy.management.SelectLayerByAttribute(
                    capa_ap, "NEW_SELECTION", f"{oid_field} = {oid_ap}"
                )

                # Seleccionar los polígonos de hábitat que intersectan con
                # el AP actual
                arcpy.management.SelectLayerByLocation(
                    capa_poligonos, "INTERSECT", capa_ap
                )

                count_poligonos = int(
                    arcpy.management.GetCount(capa_poligonos)[0]
                )

                # Si el AP no tiene hábitat asociado, se omite y se avisa
                if count_poligonos == 0:
                    log(f"AP {oid_ap}: Sin polígonos de hábitat", "WARN")
                    continue

                # Recorta los polígonos de hábitat seleccionados a los
                # límites exactos del AP actual
                clip_ap = f"memory\\clip_ap_{oid_ap}"
                eliminar_si_existe(clip_ap)
                arcpy.analysis.Clip(capa_poligonos, capa_ap, clip_ap)

                # ------------------------------------------------------------
                # PASO 1: Centroide general
                # ------------------------------------------------------------
                # Se disuelven todos los parches de hábitat del AP en una
                # sola geometría (multi-parte) y se calcula su centroide
                log(f"AP {oid_ap}: Calculando centroide general...")

                diss_todos = f"memory\\diss_todos_{oid_ap}"
                eliminar_si_existe(diss_todos)
                arcpy.management.Dissolve(clip_ap, diss_todos, multi_part="MULTI_PART")

                centroide_general = None
                with arcpy.da.SearchCursor(diss_todos, ["SHAPE@"]) as c:
                    for row in c:
                        geom = row[0]
                        centroide_general = (geom.centroid.X, geom.centroid.Y)

                # Se verifica si ese centroide general cae efectivamente
                # dentro de alguno de los parches de hábitat (puede no ser
                # así si el hábitat tiene forma de "U" o está muy fragmentado)
                centroide_en_habitat = False
                with arcpy.da.SearchCursor(clip_ap, ["SHAPE@"]) as c:
                    for row in c:
                        geom = row[0]
                        # Crear punto test
                        punto_test = arcpy.PointGeometry(
                            arcpy.Point(centroide_general[0], centroide_general[1])
                        )
                        if punto_test.within(geom):
                            centroide_en_habitat = True
                            break

                if centroide_en_habitat:
                    # ✓ El centroide general es válido: se usa directamente
                    log(f"  → Centroide general está EN hábitat")
                    xy_final = centroide_general
                    tipo_centroide = "GENERAL"
                    distancia = 0.0
                    en_habitat = "SI"
                else:
                    # ------------------------------------------------------------
                    # PASO 2: Centroide de la tesela más cercana
                    # ------------------------------------------------------------
                    # Si el centroide general quedó fuera del hábitat, se
                    # recorren todas las teselas (parches individuales) del
                    # AP, se calcula el centroide de cada una y se elige el
                    # que esté más cerca del centroide general original
                    log(f"  → Centroide general está FUERA hábitat. Buscando tesela más cercana...")

                    xy_final = None
                    distancia_minima = float('inf')
                    tipo_centroide = "TESELA_CERCANA"
                    en_habitat = "SI"

                    with arcpy.da.SearchCursor(clip_ap, ["SHAPE@"]) as c:
                        for row in c:
                            geom_tesela = row[0]
                            centroide_tesela = (geom_tesela.centroid.X,
                                              geom_tesela.centroid.Y)

                            # Verificar que el centroide de la tesela esté
                            # realmente dentro de ella (no siempre ocurre en
                            # geometrías muy irregulares)
                            punto_test = arcpy.PointGeometry(
                                arcpy.Point(centroide_tesela[0], centroide_tesela[1])
                            )

                            if punto_test.within(geom_tesela):
                                # Calcular distancia euclidiana al centroide
                                # general, para quedarse con la tesela más
                                # cercana
                                dist = ((centroide_tesela[0] - centroide_general[0])**2 +
                                       (centroide_tesela[1] - centroide_general[1])**2)**0.5

                                if dist < distancia_minima:
                                    distancia_minima = dist
                                    xy_final = centroide_tesela
                                    distancia = dist

                    # Caso extremo: si ninguna tesela pasó la validación
                    # "dentro de sí misma", se usa el centroide general como
                    # respaldo y se marca explícitamente como fuera de hábitat
                    if xy_final is None:
                        log(f"  ⚠ ALERTA: No se encontró tesela válida. Usando centroide general",
                            "WARN")
                        xy_final = centroide_general
                        tipo_centroide = "GENERAL"
                        distancia = 0.0
                        en_habitat = "NO"

                # Calcular área y perímetro total del hábitat dentro del AP
                # (usando cálculo geodésico, más preciso que el planar)
                area_total = 0.0
                perim_total = 0.0
                with arcpy.da.SearchCursor(clip_ap, ["SHAPE@"]) as c:
                    for row in c:
                        geom = row[0]
                        # Calcular área en hectáreas (metros² → hectáreas)
                        area_total += geom.getArea('GEODESIC') / 10000
                        # Calcular perímetro en metros
                        perim_total += geom.getLength('GEODESIC')

                # Insertar la fila del centroide final de esta AP, combinando
                # coordenadas, atributos heredados y campos propios del análisis
                fila_insertar = (
                    [xy_final] +  # SHAPE@XY
                    atributos_ap +  # Campos heredados
                    [oid_ap, area_total, perim_total, en_habitat,
                     tipo_centroide, distancia]
                )

                cursor_ins.insertRow(fila_insertar)
                contador_exitosos += 1

                # Limpiar capas temporales de esta AP antes de pasar a la
                # siguiente, para no acumular memoria innecesariamente
                eliminar_si_existe(clip_ap)
                eliminar_si_existe(diss_todos)

                # Aviso de avance cada 50 AP procesadas
                if contador_ap % 50 == 0:
                    log(f"Procesadas {contador_ap} APs ({contador_exitosos} exitosas)...")

    # --------------------------------------------------------------------------
    # RESULTADO FINAL
    # --------------------------------------------------------------------------
    log("="*70)
    log("RESULTADO:")
    log(f"  Áreas Protegidas procesadas: {contador_ap}")
    log(f"  Centroides generados: {contador_exitosos}")
    log(f"  Archivo de salida: {ruta_centroides}")
    log("="*70)
    log("PROCESO COMPLETADO EXITOSAMENTE")
    log("="*70)

# ==============================================================================
# EJECUCIÓN
# ==============================================================================

if __name__ == "__main__":
    ejecutar_generador_centroides()
