"""
Configuración centralizada del proyecto de sismicidad Ecuador.

Este módulo contiene todas las constantes y parámetros configurables
del sistema, facilitando ajustes sin modificar la lógica de negocio.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ConfiguracionDatos:
    """Configuración para la carga y procesamiento de datos."""
    archivo_origen: str = "cat_origen_2012_2025.txt"
    archivo_procesado: str = "sismos_procesados.parquet"
    carpeta_crudos: str = "00_datos_crudos"
    carpeta_procesados: str = "01_datos_procesados"
    compresion_parquet: str = "snappy"
    periodo_inicio: int = 2012
    periodo_fin: int = 2025


@dataclass(frozen=True)
class ConfiguracionMapa:
    """Configuración para visualizaciones de mapas."""
    latitud_centro: float = -1.83
    longitud_centro: float = -78.18
    zoom_inicial: int = 6
    zoom_detalle: int = 7
    max_puntos_mapa: int = 500
    max_puntos_historicos: int = 300
    tile_provider: str = "CartoDB positron"


@dataclass(frozen=True)
class ConfiguracionModelo:
    """Configuración para el modelo KDE de predicción."""
    bandwidth_default: float = 0.3
    bandwidth_min: float = 0.1
    bandwidth_max: float = 2.0
    puntos_riesgo_default: int = 200
    magnitud_minima_default: float = 3.5


@dataclass(frozen=True)
class UmbralesSismicos:
    """Umbrales para clasificación de eventos sísmicos."""
    magnitud_moderado: float = 5.0
    magnitud_fuerte: float = 6.0
    profundidad_superficial: float = 70.0
    profundidad_intermedio: float = 300.0
    latitud_norte: float = 0.0
    latitud_centro: float = -2.0


@dataclass(frozen=True)
class ConfiguracionAPI:
    """Configuración para la API FastAPI."""
    titulo: str = "API Sísmica Ecuador"
    version: str = "1.0.0"
    host: str = "0.0.0.0"
    puerto: int = 8000
    limite_resultados_default: int = 100
    limite_resultados_max: int = 1000


# ── Instancias de configuración (singleton) ────────────────────────────────
DATOS = ConfiguracionDatos()
MAPA = ConfiguracionMapa()
MODELO = ConfiguracionModelo()
UMBRALES = UmbralesSismicos()
API = ConfiguracionAPI()


def obtener_ruta_base() -> str:
    """Retorna la ruta base del proyecto."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
