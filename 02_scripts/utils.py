"""
Módulo de utilidades compartidas para el proyecto de sismicidad Ecuador.

Contiene funciones auxiliares reutilizables entre los diferentes módulos
del sistema (API, dashboard, pipeline de procesamiento).

Autor: Grupo 5 - Proyecto Actividad Sísmica Ecuador
"""

import os
from typing import Tuple

import pandas as pd
import numpy as np


# ── Constantes compartidas ─────────────────────────────────────────────────
UMBRAL_MAGNITUD_MODERADO: float = 5.0
UMBRAL_MAGNITUD_FUERTE: float = 6.0
UMBRAL_PROFUNDIDAD_SUPERFICIAL: float = 70.0
UMBRAL_PROFUNDIDAD_INTERMEDIO: float = 300.0

# Coordenadas centrales de Ecuador para mapas
ECUADOR_LAT_CENTRO: float = -1.83
ECUADOR_LON_CENTRO: float = -78.18

# Límites geográficos de las regiones
LATITUD_LIMITE_NORTE: float = 0.0
LATITUD_LIMITE_CENTRO: float = -2.0


def obtener_ruta_proyecto() -> str:
    """
    Obtiene la ruta raíz del proyecto de forma dinámica.
    
    Returns:
        str: Ruta absoluta al directorio raíz del proyecto.
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def clasificar_magnitud(magnitud: float) -> str:
    """
    Clasifica un evento sísmico según su magnitud.
    
    Categorías basadas en la escala de Richter:
        - Ligero: < 5.0
        - Moderado: 5.0 - 5.9
        - Fuerte: >= 6.0
    
    Args:
        magnitud: Valor de magnitud del sismo.
        
    Returns:
        Categoría del evento como string.
    """
    if pd.isna(magnitud):
        return 'Desconocida'
    if magnitud < UMBRAL_MAGNITUD_MODERADO:
        return 'Ligero'
    if magnitud < UMBRAL_MAGNITUD_FUERTE:
        return 'Moderado'
    return 'Fuerte'


def clasificar_profundidad(profundidad_km: float) -> str:
    """
    Clasifica un evento según la profundidad del hipocentro.
    
    Categorías:
        - Superficial: < 70 km
        - Intermedio: 70 - 300 km
        - Profundo: > 300 km
    
    Args:
        profundidad_km: Profundidad en kilómetros.
        
    Returns:
        Tipo de profundidad como string.
    """
    if pd.isna(profundidad_km):
        return 'Desconocida'
    if profundidad_km < UMBRAL_PROFUNDIDAD_SUPERFICIAL:
        return 'Superficial'
    if profundidad_km < UMBRAL_PROFUNDIDAD_INTERMEDIO:
        return 'Intermedio'
    return 'Profundo'


def clasificar_region(latitud: float) -> str:
    """
    Asigna la región geográfica de Ecuador basada en la latitud.
    
    Regiones:
        - Norte: lat >= 0° (Esmeraldas, Carchi, Imbabura, Pichincha)
        - Centro: -2° <= lat < 0° (Cotopaxi, Tungurahua, Chimborazo)
        - Sur: lat < -2° (Azuay, Loja, El Oro)
    
    Args:
        latitud: Latitud del epicentro en grados decimales.
        
    Returns:
        Nombre de la región geográfica.
    """
    if pd.isna(latitud):
        return 'Desconocida'
    if latitud >= LATITUD_LIMITE_NORTE:
        return 'Norte'
    if latitud >= LATITUD_LIMITE_CENTRO:
        return 'Centro'
    return 'Sur'


def calcular_estadisticas_basicas(df: pd.DataFrame, columna: str) -> dict:
    """
    Calcula estadísticas descriptivas básicas para una columna numérica.
    
    Args:
        df: DataFrame con los datos.
        columna: Nombre de la columna a analizar.
        
    Returns:
        dict: Diccionario con media, mediana, min, max y desviación estándar.
    """
    serie = df[columna].dropna()
    return {
        'media': round(serie.mean(), 2),
        'mediana': round(serie.median(), 2),
        'minimo': round(serie.min(), 2),
        'maximo': round(serie.max(), 2),
        'desv_estandar': round(serie.std(), 2),
        'total_registros': len(serie)
    }


def validar_rango_fechas(fecha_inicio: str, fecha_fin: str) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """
    Valida y convierte un rango de fechas en formato string a Timestamps.
    
    Args:
        fecha_inicio: Fecha de inicio en formato 'YYYY-MM-DD'.
        fecha_fin: Fecha de fin en formato 'YYYY-MM-DD'.
        
    Returns:
        Tuple con (timestamp_inicio, timestamp_fin).
        
    Raises:
        ValueError: Si las fechas no son válidas o el rango es incoherente.
    """
    try:
        inicio = pd.to_datetime(fecha_inicio)
        fin = pd.to_datetime(fecha_fin)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Formato de fecha inválido: {e}")
    
    if inicio > fin:
        raise ValueError(
            f"La fecha de inicio ({fecha_inicio}) no puede ser posterior "
            f"a la fecha de fin ({fecha_fin})"
        )
    
    return inicio, fin


def formatear_numero(valor: float, decimales: int = 2) -> str:
    """
    Formatea un número con separador de miles y decimales especificados.
    
    Args:
        valor: Número a formatear.
        decimales: Cantidad de decimales (default: 2).
        
    Returns:
        String formateado del número.
    """
    if pd.isna(valor):
        return "N/A"
    return f"{valor:,.{decimales}f}"
