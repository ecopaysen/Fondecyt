"""
Procesamiento de datos ráster y generación de máscaras de cobertura de suelo
==============================================================================

Este módulo procesa datos de uso y cobertura de suelo del Landcover de MapBiomas Chile
para los años 2000 y 2024, generando tres máscaras temáticas:
- Máscara de Bosque
- Máscara de Estepa
- Máscara de Áreas sin Vegetación

Las máscaras se utilizan para análisis de conectividad de hábitats.

------------------------------------------------------------------------------
CÓMO USAR ESTE SCRIPT
------------------------------------------------------------------------------
1. Revisa la sección "CONFIGURACIÓN DE ENTRADA" al final del archivo (bloque
   `if __name__ == "__main__":`). Ahí encontrarás variables marcadas con
   ">>> REEMPLAZAR <<<" que debes completar con tus propias rutas y valores.
2. No es necesario modificar el resto del código para un uso estándar; las
   clases y funciones ya están preparadas para recibir esos datos de entrada.
3. Ejecuta el script directamente (`python procesar_mascaras_mapbiomas.py`)
   una vez completada la configuración.
------------------------------------------------------------------------------
"""

import numpy as np
import rasterio
from rasterio.features import geometry_mask
from pathlib import Path
import logging
from typing import Tuple, Dict

# ------------------------------------------------------------------------------
# Configuración de logging: permite ver mensajes informativos en consola
# a medida que el script avanza (lectura de datos, creación de máscaras, etc.)
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MapBiomasMaskProcessor:
    """
    Procesador de datos ráster de MapBiomas Chile para generar máscaras de cobertura.

    Esta clase recibe como INPUT la ruta a un archivo ráster de MapBiomas Chile
    (formato .tif) y permite generar tres máscaras temáticas de cobertura de suelo:
    bosque, estepa y áreas sin vegetación.
    """

    # --------------------------------------------------------------------------
    # Diccionario de clases originales de MapBiomas Chile.
    # Estos son los códigos numéricos que trae el ráster original de MapBiomas
    # para cada tipo de cobertura. NO deben modificarse salvo que MapBiomas
    # cambie su leyenda de clasificación oficial.
    # --------------------------------------------------------------------------
    CLASES_MAPBIOMAS = {
        'bosque_primario': 59,
        'bosque_secundario': 60,
        'bosque_achaparrado': 67,
        'estepa': 63,
        'arena_playa_duna': 23,
        'otra_area_sin_vegetacion': 25,
        'salar': 61
    }

    # --------------------------------------------------------------------------
    # Diccionario de valores reclasificados: son los códigos NUEVOS que se le
    # asignarán a cada máscara de salida (por ejemplo, todo lo que sea bosque
    # pasará a tener el valor 3 en el ráster de salida).
    # --------------------------------------------------------------------------
    VALORES_RECLASIFICADOS = {
        'bosque': 3,
        'estepa': 63,
        'areas_sin_vegetacion': 99
    }

    def __init__(self, ruta_raster: str):
        """
        Inicializar el procesador.

        Parameters
        ----------
        ruta_raster : str
            INPUT — Ruta al archivo ráster de MapBiomas Chile (.tif) que se
            desea procesar. Debe ser reemplazada por la ruta real del archivo
            en el equipo del usuario (ver sección de CONFIGURACIÓN al final
            del script).
        """
        self.ruta_raster = Path(ruta_raster)
        if not self.ruta_raster.exists():
            raise FileNotFoundError(f"Archivo ráster no encontrado: {ruta_raster}")

        logger.info(f"Leyendo archivo ráster: {ruta_raster}")
        with rasterio.open(ruta_raster) as src:
            self.data = src.read(1)       # Banda única con los códigos de clase
            self.profile = src.profile    # Metadatos del ráster (CRS, tamaño, etc.)
            self.crs = src.crs            # Sistema de referencia de coordenadas
            self.transform = src.transform  # Transformación geoespacial (origen y resolución)

    def crear_mascara_bosque(self) -> np.ndarray:
        """
        Crear máscara de bosque.

        Selecciona clases: Bosque Primario (59), Bosque Secundario (60),
        Bosque Achaparrado (67) y las reclasifica a valor 3.

        Returns
        -------
        np.ndarray
            Array con máscara de bosque (valor 3 para bosque, 0 para no-bosque).
        """
        logger.info("Creando máscara de Bosque...")

        # Se agrupan las tres subclases de bosque definidas por MapBiomas
        clases_bosque = [
            self.CLASES_MAPBIOMAS['bosque_primario'],
            self.CLASES_MAPBIOMAS['bosque_secundario'],
            self.CLASES_MAPBIOMAS['bosque_achaparrado']
        ]

        # Se crea un array vacío (todo en 0) del mismo tamaño que el ráster original
        mascara = np.zeros_like(self.data, dtype=np.uint8)

        # Por cada clase de bosque, se asigna el valor reclasificado (3)
        # en los píxeles que correspondan a esa clase
        for clase in clases_bosque:
            mascara[self.data == clase] = self.VALORES_RECLASIFICADOS['bosque']

        logger.info(f"Máscara de Bosque creada: {np.sum(mascara > 0)} píxeles clasificados")
        return mascara

    def crear_mascara_estepa(self) -> np.ndarray:
        """
        Crear máscara de estepa.

        Selecciona clase: Estepa (63) y conserva su valor original.

        Returns
        -------
        np.ndarray
            Array con máscara de estepa (valor 63 para estepa, 0 para no-estepa).
        """
        logger.info("Creando máscara de Estepa...")

        clase_estepa = self.CLASES_MAPBIOMAS['estepa']
        mascara = np.zeros_like(self.data, dtype=np.uint8)

        # Se marca con el valor reclasificado (63) todos los píxeles de estepa
        mascara[self.data == clase_estepa] = self.VALORES_RECLASIFICADOS['estepa']

        logger.info(f"Máscara de Estepa creada: {np.sum(mascara > 0)} píxeles clasificados")
        return mascara

    def crear_mascara_areas_sin_vegetacion(self) -> np.ndarray:
        """
        Crear máscara de áreas sin vegetación.

        Selecciona clases: Arena, Playa y Duna (23), Otra área sin vegetación (25),
        Salar (61) y las reclasifica a valor 99.

        Returns
        -------
        np.ndarray
            Array con máscara de áreas sin vegetación (valor 99 para sin veg, 0 resto).
        """
        logger.info("Creando máscara de Áreas sin Vegetación...")

        # Se agrupan las tres subclases de "sin vegetación" definidas por MapBiomas
        clases_sin_veg = [
            self.CLASES_MAPBIOMAS['arena_playa_duna'],
            self.CLASES_MAPBIOMAS['otra_area_sin_vegetacion'],
            self.CLASES_MAPBIOMAS['salar']
        ]

        mascara = np.zeros_like(self.data, dtype=np.uint8)

        for clase in clases_sin_veg:
            mascara[self.data == clase] = self.VALORES_RECLASIFICADOS['areas_sin_vegetacion']

        logger.info(f"Máscara de Áreas sin Vegetación creada: {np.sum(mascara > 0)} píxeles clasificados")
        return mascara

    def procesar_todas_las_mascaras(self) -> Dict[str, np.ndarray]:
        """
        Procesar todas las máscaras en una sola operación.

        Returns
        -------
        Dict[str, np.ndarray]
            Diccionario con las tres máscaras generadas:
            - 'bosque': máscara de bosque
            - 'estepa': máscara de estepa
            - 'areas_sin_vegetacion': máscara de áreas sin vegetación
        """
        mascaras = {
            'bosque': self.crear_mascara_bosque(),
            'estepa': self.crear_mascara_estepa(),
            'areas_sin_vegetacion': self.crear_mascara_areas_sin_vegetacion()
        }
        return mascaras

    def guardar_mascara(self, mascara: np.ndarray, ruta_salida: str,
                       nombre_banda: str = "mascara") -> None:
        """
        Guardar máscara a archivo ráster.

        Parameters
        ----------
        mascara : np.ndarray
            Array con la máscara a guardar (generado por alguno de los
            métodos `crear_mascara_*`).
        ruta_salida : str
            INPUT — Ruta del archivo de salida (.tif) donde se guardará la
            máscara. Debe reemplazarse por la ruta deseada en el equipo del
            usuario.
        nombre_banda : str
            Nombre descriptivo de la banda que quedará como metadato del
            archivo ráster (por defecto "mascara").
        """
        logger.info(f"Guardando máscara en: {ruta_salida}")

        # Se copia el perfil (metadatos) del ráster original y se ajusta
        # para que la salida tenga una sola banda con el tipo de dato de la máscara
        profile = self.profile.copy()
        profile.update(count=1, dtype=mascara.dtype)

        with rasterio.open(ruta_salida, 'w', **profile) as dst:
            dst.write(mascara, 1)
            dst.descriptions = (nombre_banda,)

        logger.info(f"Máscara guardada exitosamente: {ruta_salida}")

    def generar_estadisticas(self, mascaras: Dict[str, np.ndarray]) -> Dict:
        """
        Generar estadísticas de cobertura para cada máscara.

        Parameters
        ----------
        mascaras : Dict[str, np.ndarray]
            Diccionario con las máscaras generadas (salida de
            `procesar_todas_las_mascaras`).

        Returns
        -------
        Dict
            Diccionario con estadísticas de cobertura (píxeles clasificados,
            porcentaje de cobertura y total de píxeles) para cada máscara.
        """
        logger.info("Generando estadísticas de cobertura...")

        total_pixeles = self.data.size
        estadisticas = {}

        for nombre_mascara, mascara in mascaras.items():
            pixeles_clasificados = np.sum(mascara > 0)
            porcentaje = (pixeles_clasificados / total_pixeles) * 100

            estadisticas[nombre_mascara] = {
                'pixeles_clasificados': int(pixeles_clasificados),
                'porcentaje_cobertura': round(porcentaje, 2),
                'total_pixeles': int(total_pixeles)
            }

            logger.info(f"{nombre_mascara.upper()}: {porcentaje:.2f}% de cobertura")

        return estadisticas


def procesar_mapbiomas(ruta_entrada: str, directorio_salida: str,
                      año: int = 2024) -> None:
    """
    Función principal para procesar MapBiomas y generar todas las máscaras.

    Esta función encapsula todo el flujo: lee el ráster de entrada, genera
    las tres máscaras, las guarda en disco y muestra un resumen de
    estadísticas de cobertura en consola.

    Parameters
    ----------
    ruta_entrada : str
        INPUT — Ruta al archivo ráster de MapBiomas Chile (.tif) que se desea
        procesar. Reemplazar por la ruta real del archivo.
    directorio_salida : str
        INPUT — Carpeta donde se guardarán las máscaras generadas (.tif).
        Reemplazar por la carpeta de salida deseada. Si la carpeta no
        existe, se crea automáticamente.
    año : int
        INPUT — Año correspondiente al ráster procesado (por defecto 2024).
        Se usa solo para nombrar los archivos de salida
        (ej. "mascara_bosque_2024.tif").
    """
    # Crear directorio de salida si no existe
    Path(directorio_salida).mkdir(parents=True, exist_ok=True)

    # Inicializar procesador con el ráster de entrada
    procesador = MapBiomasMaskProcessor(ruta_entrada)

    # Generar las tres máscaras (bosque, estepa, áreas sin vegetación)
    mascaras = procesador.procesar_todas_las_mascaras()

    # Guardar cada máscara como un archivo .tif independiente
    procesador.guardar_mascara(
        mascaras['bosque'],
        f"{directorio_salida}/mascara_bosque_{año}.tif",
        "Máscara de Bosque"
    )

    procesador.guardar_mascara(
        mascaras['estepa'],
        f"{directorio_salida}/mascara_estepa_{año}.tif",
        "Máscara de Estepa"
    )

    procesador.guardar_mascara(
        mascaras['areas_sin_vegetacion'],
        f"{directorio_salida}/mascara_areas_sin_veg_{año}.tif",
        "Máscara de Áreas sin Vegetación"
    )

    # Generar y mostrar estadísticas de cobertura en consola
    estadisticas = procesador.generar_estadisticas(mascaras)

    print("\n" + "="*60)
    print(f"RESUMEN DE COBERTURA - AÑO {año}")
    print("="*60)
    for mascara_tipo, stats in estadisticas.items():
        print(f"\n{mascara_tipo.upper()}")
        print(f"  Píxeles clasificados: {stats['pixeles_clasificados']:,}")
        print(f"  Porcentaje de cobertura: {stats['porcentaje_cobertura']}%")
    print("="*60 + "\n")


if __name__ == "__main__":
    # --------------------------------------------------------------------------
    # CONFIGURACIÓN DE ENTRADA (INPUT)
    # --------------------------------------------------------------------------
    # Completa las siguientes variables con tus propios datos antes de ejecutar
    # el script. Cada una está marcada con ">>> REEMPLAZAR <<<".
    # --------------------------------------------------------------------------

    # Ruta al archivo ráster de MapBiomas Chile del año 2000
    ruta_mapbiomas_2000 = "ruta/a/mapbiomas_2000.tif"  # >>> REEMPLAZAR <<< por la ruta real del archivo 2000

    # Ruta al archivo ráster de MapBiomas Chile del año 2024
    ruta_mapbiomas_2024 = "ruta/a/mapbiomas_2024.tif"  # >>> REEMPLAZAR <<< por la ruta real del archivo 2024

    # Carpeta donde se guardarán las máscaras generadas (se crea si no existe)
    carpeta_salida = "salida/mascaras"  # >>> REEMPLAZAR <<< por la carpeta de salida deseada

    # --------------------------------------------------------------------------
    # EJECUCIÓN
    # --------------------------------------------------------------------------
    # Descomenta las líneas correspondientes al año que quieras procesar.
    # Puedes ejecutar ambas si necesitas procesar los dos años en la misma corrida.
    # --------------------------------------------------------------------------

    # Procesar datos de 2000
    # procesar_mapbiomas(
    #     ruta_entrada=ruta_mapbiomas_2000,
    #     directorio_salida=carpeta_salida,
    #     año=2000
    # )

    # Procesar datos de 2024
    # procesar_mapbiomas(
    #     ruta_entrada=ruta_mapbiomas_2024,
    #     directorio_salida=carpeta_salida,
    #     año=2024
    # )

    pass
