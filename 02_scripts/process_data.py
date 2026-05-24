"""
Script para procesar datos sísmicos y guardarlos en formato Parquet.

Este módulo implementa el pipeline ETL (Extract, Transform, Load) completo
para el catálogo sísmico del IG-EPN Ecuador (2012-2025).

Autor: Grupo 5 - Proyecto Actividad Sísmica Ecuador
Última modificación: Mayo 2026
"""

import os
import logging
from typing import Optional

import pandas as pd
import numpy as np
from datetime import datetime

# ── Configuración de logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ── Constantes del proyecto ────────────────────────────────────────────────
ARCHIVO_ORIGEN = "cat_origen_2012_2025.txt"
ARCHIVO_SALIDA = "sismos_procesados.parquet"
CARPETA_CRUDOS = "00_datos_crudos"
CARPETA_PROCESADOS = "01_datos_procesados"

# Umbrales de clasificación sísmica (escala Richter)
UMBRAL_MODERADO = 5.0
UMBRAL_FUERTE = 6.0

# Umbrales de profundidad (km)
UMBRAL_SUPERFICIAL = 70
UMBRAL_INTERMEDIO = 300

# Límites de latitud para regiones de Ecuador
LATITUD_NORTE = 0
LATITUD_CENTRO = -2


def obtener_ruta_base() -> str:
    """Obtiene la ruta base del proyecto de forma dinámica."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cargar_datos_crudos() -> pd.DataFrame:
    """
    Carga datos crudos del catálogo sísmico desde archivo CSV.
    
    Returns:
        pd.DataFrame: DataFrame con los datos crudos sin procesar.
        
    Raises:
        FileNotFoundError: Si el archivo de datos no existe.
    """
    base = obtener_ruta_base()
    path = os.path.join(base, CARPETA_CRUDOS, ARCHIVO_ORIGEN)
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró el archivo de datos: {path}")
    
    logger.info(f"Cargando datos desde: {path}")
    
    # Lectura del CSV con formato no estándar del IG-EPN
    df = pd.read_csv(path, comment='#', skipinitialspace=True)
    df.columns = df.columns.str.strip()
    
    logger.info(f"Datos cargados: {len(df)} registros, {len(df.columns)} columnas")
    return df

def clasificar_magnitud(mag: float) -> str:
    """
    Clasifica un evento sísmico según su magnitud en la escala Richter.
    
    Args:
        mag: Valor de magnitud del evento.
        
    Returns:
        Categoría del sismo: 'Ligero', 'Moderado', 'Fuerte' o 'Desconocida'.
    """
    if pd.isna(mag):
        return 'Desconocida'
    if mag < UMBRAL_MODERADO:
        return 'Ligero'
    if mag < UMBRAL_FUERTE:
        return 'Moderado'
    return 'Fuerte'


def clasificar_profundidad(depth: float) -> str:
    """
    Clasifica un evento sísmico según su profundidad hipocentral.
    
    Args:
        depth: Profundidad en kilómetros.
        
    Returns:
        Tipo de profundidad: 'Superficial', 'Intermedio', 'Profundo' o 'Desconocida'.
    """
    if pd.isna(depth):
        return 'Desconocida'
    if depth < UMBRAL_SUPERFICIAL:
        return 'Superficial'
    if depth < UMBRAL_INTERMEDIO:
        return 'Intermedio'
    return 'Profundo'


def transformar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica todas las transformaciones necesarias al dataset crudo.
    
    Incluye: conversión de tipos, extracción de componentes temporales,
    asignación de regiones geográficas y clasificación por magnitud/profundidad.
    
    Args:
        df: DataFrame con datos crudos del catálogo sísmico.
        
    Returns:
        pd.DataFrame: DataFrame transformado y limpio.
    """
    logger.info("Aplicando transformaciones...")
    
    # 1. Conversión temporal: extraer componentes de fecha
    logger.info("  → Convirtiendo fechas y extrayendo componentes temporales")
    df['date'] = pd.to_datetime(df['time_value'], errors='coerce')
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['hour'] = df['date'].dt.hour
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # 2. Conversión numérica de coordenadas y magnitudes
    logger.info("  → Convirtiendo coordenadas y magnitudes a valores numéricos")
    df['lat'] = pd.to_numeric(df['latitude_value'], errors='coerce')
    df['lon'] = pd.to_numeric(df['longitude_value'], errors='coerce')
    df['depth'] = pd.to_numeric(df['depth_value'], errors='coerce')
    
    # Priorizar magnitud M sobre P cuando ambas están disponibles
    df['magnitude'] = pd.to_numeric(
        df['magnitude_value_M'].fillna(df['magnitude_value_P']), 
        errors='coerce'
    )
    
    # 3. Asignación de región geográfica basada en latitud
    logger.info("  → Asignando regiones geográficas (Norte/Centro/Sur)")
    df['region'] = pd.cut(
        df['lat'], 
        bins=[-5, LATITUD_CENTRO, LATITUD_NORTE, 2], 
        labels=['Sur', 'Centro', 'Norte']
    )
    df['region'] = df['region'].astype(str).replace('nan', 'Desconocida')
    
    # 4. Clasificación por categoría de magnitud
    logger.info("  → Clasificando eventos por categoría de magnitud")
    df['categoria'] = df['magnitude'].apply(clasificar_magnitud)
    
    # 5. Clasificación por tipo de profundidad
    logger.info("  → Clasificando eventos por profundidad hipocentral")
    df['tipo_profundidad'] = df['depth'].apply(clasificar_profundidad)
    
    # 6. Eliminación de registros con valores nulos en columnas críticas
    logger.info("  → Eliminando registros con valores nulos críticos")
    registros_antes = len(df)
    columnas_requeridas = ['lat', 'lon', 'depth', 'magnitude', 'date']
    df = df.dropna(subset=columnas_requeridas).copy()
    registros_eliminados = registros_antes - len(df)
    logger.info(f"    Registros eliminados por nulos: {registros_eliminados}")
    
    logger.info(f"Transformaciones completadas: {len(df)} registros válidos")
    return df

def guardar_parquet(df: pd.DataFrame, compresion: str = 'snappy') -> str:
    """
    Guarda el dataset procesado en formato Parquet optimizado.
    
    Args:
        df: DataFrame procesado listo para exportar.
        compresion: Algoritmo de compresión ('snappy', 'gzip', 'brotli').
        
    Returns:
        str: Ruta absoluta del archivo Parquet generado.
    """
    base = obtener_ruta_base()
    output_dir = os.path.join(base, CARPETA_PROCESADOS)
    output_path = os.path.join(output_dir, ARCHIVO_SALIDA)
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Guardando datos procesados en: {output_path}")
    
    # Columnas principales para el archivo de salida
    columnas_exportar = [
        'event', 'date', 'date_str', 'year', 'month', 'day', 'hour',
        'lat', 'lon', 'depth', 'magnitude', 
        'region', 'categoria', 'tipo_profundidad'
    ]
    
    # Incluir columnas opcionales de metadatos si están disponibles
    columnas_opcionales = ['used_station_count', 'used_phase_count']
    for col in columnas_opcionales:
        if col in df.columns:
            columnas_exportar.append(col)
    
    df_export = df[columnas_exportar].copy()
    
    # Exportar a Parquet con compresión especificada
    df_export.to_parquet(output_path, index=False, compression=compresion)
    
    # Reportar tamaño del archivo generado
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"Archivo guardado exitosamente: {size_mb:.2f} MB ({compresion})")
    
    return output_path

def generar_estadisticas(df: pd.DataFrame) -> dict:
    """
    Genera y muestra estadísticas descriptivas del dataset procesado.
    
    Args:
        df: DataFrame procesado con datos sísmicos.
        
    Returns:
        dict: Diccionario con las estadísticas calculadas para uso programático.
    """
    logger.info("Generando estadísticas del dataset procesado...")
    
    print("\n" + "=" * 60)
    print("  ESTADÍSTICAS DEL DATASET PROCESADO")
    print("=" * 60)
    
    # Dimensiones generales
    periodo_inicio = int(df['year'].min())
    periodo_fin = int(df['year'].max())
    print(f"\n📊 Dimensiones:")
    print(f"  - Total de eventos: {len(df):,}")
    print(f"  - Columnas: {len(df.columns)}")
    print(f"  - Período: {periodo_inicio} - {periodo_fin}")
    
    # Distribución geográfica
    print(f"\n🌎 Distribución por Región:")
    for region, count in df['region'].value_counts().items():
        pct = (count / len(df)) * 100
        print(f"  - {region}: {count:,} ({pct:.1f}%)")
    
    # Distribución por categoría de magnitud
    print(f"\n⚡ Distribución por Categoría:")
    for cat, count in df['categoria'].value_counts().items():
        pct = (count / len(df)) * 100
        print(f"  - {cat}: {count:,} ({pct:.1f}%)")
    
    # Estadísticas de magnitud
    stats_magnitud = {
        'media': df['magnitude'].mean(),
        'mediana': df['magnitude'].median(),
        'minima': df['magnitude'].min(),
        'maxima': df['magnitude'].max(),
        'desv_estandar': df['magnitude'].std()
    }
    print(f"\n📈 Estadísticas de Magnitud:")
    print(f"  - Media: {stats_magnitud['media']:.2f}")
    print(f"  - Mediana: {stats_magnitud['mediana']:.2f}")
    print(f"  - Mínima: {stats_magnitud['minima']:.2f}")
    print(f"  - Máxima: {stats_magnitud['maxima']:.2f}")
    print(f"  - Desv. Estándar: {stats_magnitud['desv_estandar']:.2f}")
    
    # Estadísticas de profundidad
    stats_profundidad = {
        'media': df['depth'].mean(),
        'mediana': df['depth'].median(),
        'minima': df['depth'].min(),
        'maxima': df['depth'].max()
    }
    print(f"\n🔽 Estadísticas de Profundidad:")
    print(f"  - Media: {stats_profundidad['media']:.2f} km")
    print(f"  - Mediana: {stats_profundidad['mediana']:.2f} km")
    print(f"  - Mínima: {stats_profundidad['minima']:.2f} km")
    print(f"  - Máxima: {stats_profundidad['maxima']:.2f} km")
    
    # Eventos por año
    print(f"\n📅 Eventos por Año:")
    for year, count in df['year'].value_counts().sort_index().items():
        print(f"  - {year}: {count:,}")
    
    print("\n" + "=" * 60)
    
    return {
        'total_eventos': len(df),
        'periodo': (periodo_inicio, periodo_fin),
        'magnitud': stats_magnitud,
        'profundidad': stats_profundidad
    }

def main():
    """
    Función principal que orquesta el pipeline ETL completo.
    
    Pasos:
        1. Carga de datos crudos desde CSV
        2. Transformación y limpieza
        3. Exportación a formato Parquet
        4. Generación de estadísticas de validación
    """
    print("\n" + "═" * 60)
    print("  PIPELINE DE PROCESAMIENTO DE DATOS SÍSMICOS")
    print("  Instituto Geofísico - EPN | Ecuador 2012-2025")
    print("═" * 60)
    logger.info(f"Inicio de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Paso 1: Extracción - Cargar datos crudos
        df = cargar_datos_crudos()
        
        # Paso 2: Transformación - Limpiar y enriquecer datos
        df_procesado = transformar_datos(df)
        
        # Paso 3: Carga - Guardar en formato optimizado
        output_path = guardar_parquet(df_procesado)
        
        # Paso 4: Validación - Generar estadísticas
        estadisticas = generar_estadisticas(df_procesado)
        
        logger.info("PIPELINE COMPLETADO EXITOSAMENTE ✓")
        logger.info(f"Archivo de salida: {output_path}")
        logger.info(f"Total eventos procesados: {estadisticas['total_eventos']:,}")
        
    except FileNotFoundError as e:
        logger.error(f"Error de archivo: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en el pipeline: {e}")
        raise


if __name__ == "__main__":
    main()
