"""
Script para procesar datos sísmicos y guardarlos en formato Parquet
Implementa el pipeline técnico completo
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

def cargar_datos_crudos():
    """Carga datos crudos del catálogo sísmico"""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "data", "raw", "cat_origen_2012_2025.txt")
    
    print(f"📂 Cargando datos desde: {path}")
    
    # pd.read_csv con formato no estándar
    df = pd.read_csv(path, comment='#', skipinitialspace=True)
    df.columns = df.columns.str.strip()
    
    print(f"✅ Datos cargados: {len(df)} registros, {len(df.columns)} columnas")
    return df

def transformar_datos(df):
    """Aplica transformaciones al dataset"""
    print("\n🔄 Aplicando transformaciones...")
    
    # 1. Convertir time_value a datetime; extraer año, mes y categorías
    print("  - Convirtiendo fechas y extrayendo componentes temporales")
    df['date'] = pd.to_datetime(df['time_value'], errors='coerce')
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['hour'] = df['date'].dt.hour
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # 2. Convertir coordenadas y magnitudes
    print("  - Convirtiendo coordenadas y magnitudes")
    df['lat'] = pd.to_numeric(df['latitude_value'], errors='coerce')
    df['lon'] = pd.to_numeric(df['longitude_value'], errors='coerce')
    df['depth'] = pd.to_numeric(df['depth_value'], errors='coerce')
    df['magnitude'] = pd.to_numeric(
        df['magnitude_value_M'].fillna(df['magnitude_value_P']), 
        errors='coerce'
    )
    
    # 3. Asignar región usando pd.cut
    print("  - Asignando regiones geográficas")
    df['region'] = pd.cut(
        df['lat'], 
        bins=[-5, -2, 0, 2], 
        labels=['Sur', 'Centro', 'Norte']
    )
    # Convertir a string para manejar valores fuera de rango
    df['region'] = df['region'].astype(str)
    df['region'] = df['region'].replace('nan', 'Desconocida')
    
    # 4. Clasificar por categoría de magnitud
    print("  - Clasificando por categoría de magnitud")
    def clasificar_magnitud(mag):
        if pd.isna(mag): return 'Desconocida'
        if mag < 5: return 'Ligero'
        if mag < 6: return 'Moderado'
        return 'Fuerte'
    
    df['categoria'] = df['magnitude'].apply(clasificar_magnitud)
    
    # 5. Clasificar por profundidad
    print("  - Clasificando por profundidad")
    def clasificar_profundidad(depth):
        if pd.isna(depth): return 'Desconocida'
        if depth < 70: return 'Superficial'
        if depth < 300: return 'Intermedio'
        return 'Profundo'
    
    df['tipo_profundidad'] = df['depth'].apply(clasificar_profundidad)
    
    # 6. Limpiar datos nulos en columnas críticas
    print("  - Eliminando registros con valores nulos críticos")
    antes = len(df)
    df = df.dropna(subset=['lat', 'lon', 'depth', 'magnitude', 'date']).copy()
    despues = len(df)
    print(f"    Registros eliminados: {antes - despues}")
    
    print(f"✅ Transformaciones completadas: {len(df)} registros válidos")
    return df

def guardar_parquet(df):
    """Guarda el dataset procesado en formato Parquet"""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base, "data", "processed")
    output_path = os.path.join(output_dir, "sismos_procesados.parquet")
    
    # Crear directorio si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n💾 Guardando datos procesados en: {output_path}")
    
    # Seleccionar columnas relevantes (solo las que existen)
    columnas = [
        'event', 'date', 'date_str', 'year', 'month', 'day', 'hour',
        'lat', 'lon', 'depth', 'magnitude', 
        'region', 'categoria', 'tipo_profundidad'
    ]
    
    # Agregar columnas opcionales si existen
    if 'used_station_count' in df.columns:
        columnas.append('used_station_count')
    if 'used_phase_count' in df.columns:
        columnas.append('used_phase_count')
    
    df_export = df[columnas].copy()
    
    # Guardar en Parquet con compresión
    df_export.to_parquet(output_path, index=False, compression='snappy')
    
    # Calcular tamaño del archivo
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✅ Archivo guardado: {size_mb:.2f} MB")
    
    return output_path

def generar_estadisticas(df):
    """Genera estadísticas del dataset procesado"""
    print("\n📊 ESTADÍSTICAS DEL DATASET PROCESADO")
    print("=" * 60)
    
    print(f"\n📈 Dimensiones:")
    print(f"  - Total de eventos: {len(df):,}")
    print(f"  - Columnas: {len(df.columns)}")
    print(f"  - Período: {df['year'].min()} - {df['year'].max()}")
    
    print(f"\n🌍 Distribución por Región:")
    for region, count in df['region'].value_counts().items():
        pct = (count / len(df)) * 100
        print(f"  - {region}: {count:,} ({pct:.1f}%)")
    
    print(f"\n📊 Distribución por Categoría:")
    for cat, count in df['categoria'].value_counts().items():
        pct = (count / len(df)) * 100
        print(f"  - {cat}: {count:,} ({pct:.1f}%)")
    
    print(f"\n🔢 Estadísticas de Magnitud:")
    print(f"  - Media: {df['magnitude'].mean():.2f}")
    print(f"  - Mediana: {df['magnitude'].median():.2f}")
    print(f"  - Mínima: {df['magnitude'].min():.2f}")
    print(f"  - Máxima: {df['magnitude'].max():.2f}")
    print(f"  - Desv. Estándar: {df['magnitude'].std():.2f}")
    
    print(f"\n📏 Estadísticas de Profundidad:")
    print(f"  - Media: {df['depth'].mean():.2f} km")
    print(f"  - Mediana: {df['depth'].median():.2f} km")
    print(f"  - Mínima: {df['depth'].min():.2f} km")
    print(f"  - Máxima: {df['depth'].max():.2f} km")
    
    print(f"\n📅 Eventos por Año:")
    for year, count in df['year'].value_counts().sort_index().items():
        print(f"  - {year}: {count:,}")
    
    print("\n" + "=" * 60)

def main():
    """Función principal del pipeline"""
    print("🚀 PIPELINE DE PROCESAMIENTO DE DATOS SÍSMICOS")
    print("=" * 60)
    print(f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Cargar datos crudos
    df = cargar_datos_crudos()
    
    # 2. Transformar datos
    df_procesado = transformar_datos(df)
    
    # 3. Guardar en Parquet
    output_path = guardar_parquet(df_procesado)
    
    # 4. Generar estadísticas
    generar_estadisticas(df_procesado)
    
    print("\n✅ PIPELINE COMPLETADO EXITOSAMENTE")
    print(f"📁 Archivo de salida: {output_path}")

if __name__ == "__main__":
    main()
