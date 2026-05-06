"""
API FastAPI para el Sistema de Monitoreo Sísmico de Ecuador
Proporciona endpoints para consultar eventos sísmicos y estadísticas
"""

import os
from datetime import datetime
from typing import Optional, List
import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ══════════════════════════════════════════════════════════════════════════════
#  MODELOS DE DATOS
# ══════════════════════════════════════════════════════════════════════════════

class EventoSismico(BaseModel):
    """Modelo de un evento sísmico"""
    event: str
    fecha: str
    latitud: float
    longitud: float
    profundidad: float
    magnitud: float
    region: str
    categoria: str

class EstadisticasRegion(BaseModel):
    """Estadísticas de una región"""
    region: str
    total_eventos: int
    magnitud_media: float
    magnitud_maxima: float
    profundidad_media: float

class RespuestaEventos(BaseModel):
    """Respuesta con lista de eventos"""
    total: int
    eventos: List[EventoSismico]

# ══════════════════════════════════════════════════════════════════════════════
#  CARGA DE DATOS
# ══════════════════════════════════════════════════════════════════════════════

def cargar_datos():
    """Carga y procesa el dataset de eventos sísmicos"""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "data", "raw", "cat_origen_2012_2025.txt")
    
    df = pd.read_csv(path, comment='#', skipinitialspace=True)
    df.columns = df.columns.str.strip()
    
    # Convertir tipos
    df['date'] = pd.to_datetime(df['time_value'], errors='coerce')
    df['lat'] = pd.to_numeric(df['latitude_value'], errors='coerce')
    df['lon'] = pd.to_numeric(df['longitude_value'], errors='coerce')
    df['depth'] = pd.to_numeric(df['depth_value'], errors='coerce')
    df['magnitude'] = pd.to_numeric(
        df['magnitude_value_M'].fillna(df['magnitude_value_P']), 
        errors='coerce'
    )
    
    # Clasificar región
    def clasificar_region(lat):
        if pd.isna(lat): return 'Desconocida'
        if lat >= 0: return 'Norte'
        if lat >= -2: return 'Centro'
        return 'Sur'
    
    df['region'] = df['lat'].apply(clasificar_region)
    
    # Clasificar categoría
    def clasificar_categoria(mag):
        if pd.isna(mag): return 'Desconocida'
        if mag < 5: return 'Ligero'
        if mag < 6: return 'Moderado'
        return 'Fuerte'
    
    df['categoria'] = df['magnitude'].apply(clasificar_categoria)
    
    # Limpiar datos
    df = df.dropna(subset=['lat', 'lon', 'depth', 'magnitude', 'date']).copy()
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return df

# Cargar datos al iniciar
df_global = cargar_datos()

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE LA API
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="API Sísmica Ecuador",
    description="API para consultar eventos sísmicos registrados en Ecuador (2012-2025)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════════════════════════════════
#  ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["General"])
def root():
    """Endpoint raíz con información de la API"""
    return {
        "nombre": "API Sísmica Ecuador",
        "version": "1.0.0",
        "descripcion": "API para consultar eventos sísmicos del IG-EPN",
        "total_eventos": len(df_global),
        "periodo": "2012-2025",
        "endpoints": {
            "eventos": "/sismos/query",
            "estadisticas": "/sismos/stats",
            "documentacion": "/docs"
        }
    }

@app.get("/sismos/query", response_model=RespuestaEventos, tags=["Eventos"])
def consultar_eventos(
    start_date: Optional[str] = Query("2020-01-01", description="Fecha inicio (YYYY-MM-DD)"),
    end_date: Optional[str] = Query("2023-12-31", description="Fecha fin (YYYY-MM-DD)"),
    min_magnitude: Optional[float] = Query(4.5, description="Magnitud mínima"),
    max_magnitude: Optional[float] = Query(10.0, description="Magnitud máxima"),
    min_depth: Optional[float] = Query(0.0, description="Profundidad mínima (km)"),
    max_depth: Optional[float] = Query(300.0, description="Profundidad máxima (km)"),
    region: Optional[str] = Query(None, description="Región (Norte, Centro, Sur)"),
    limit: Optional[int] = Query(100, description="Límite de resultados")
):
    """
    Consulta eventos sísmicos con filtros
    
    Ejemplo:
    ```
    GET /sismos/query?start_date=2020-01-01&end_date=2023-12-31&min_magnitude=4.5
    ```
    """
    try:
        # Filtrar datos
        df = df_global.copy()
        
        # Filtros de fecha
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        df = df[(df['date'] >= start) & (df['date'] <= end)]
        
        # Filtros de magnitud
        df = df[(df['magnitude'] >= min_magnitude) & (df['magnitude'] <= max_magnitude)]
        
        # Filtros de profundidad
        df = df[(df['depth'] >= min_depth) & (df['depth'] <= max_depth)]
        
        # Filtro de región
        if region:
            df = df[df['region'] == region]
        
        # Limitar resultados
        df = df.head(limit)
        
        # Convertir a lista de eventos
        eventos = []
        for _, row in df.iterrows():
            eventos.append(EventoSismico(
                event=row['event'],
                fecha=row['date_str'],
                latitud=round(row['lat'], 4),
                longitud=round(row['lon'], 4),
                profundidad=round(row['depth'], 2),
                magnitud=round(row['magnitude'], 2),
                region=row['region'],
                categoria=row['categoria']
            ))
        
        return RespuestaEventos(total=len(eventos), eventos=eventos)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en la consulta: {str(e)}")

@app.get("/sismos/stats", tags=["Estadísticas"])
def estadisticas_region(
    region: Optional[str] = Query("Centro", description="Región (Norte, Centro, Sur, o 'Todas')")
):
    """
    Obtiene estadísticas de eventos sísmicos por región
    
    Ejemplo:
    ```
    GET /sismos/stats?region=Centro
    ```
    
    Retorna:
    - Total de eventos
    - Magnitud media
    - Magnitud máxima
    - Profundidad media
    """
    try:
        df = df_global.copy()
        
        if region and region != "Todas":
            df = df[df['region'] == region]
        
        if len(df) == 0:
            raise HTTPException(status_code=404, detail="No se encontraron eventos para la región especificada")
        
        # Calcular estadísticas
        stats = {
            "region": region,
            "total_eventos": int(len(df)),
            "magnitud_media": round(df['magnitude'].mean(), 2),
            "magnitud_maxima": round(df['magnitude'].max(), 2),
            "magnitud_minima": round(df['magnitude'].min(), 2),
            "profundidad_media": round(df['depth'].mean(), 2),
            "profundidad_maxima": round(df['depth'].max(), 2),
            "profundidad_minima": round(df['depth'].min(), 2),
            "distribucion_categoria": {
                "Ligero": int((df['categoria'] == 'Ligero').sum()),
                "Moderado": int((df['categoria'] == 'Moderado').sum()),
                "Fuerte": int((df['categoria'] == 'Fuerte').sum())
            }
        }
        
        return stats
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al calcular estadísticas: {str(e)}")

@app.get("/sismos/regiones", tags=["Estadísticas"])
def listar_regiones():
    """
    Lista todas las regiones disponibles con conteo de eventos
    """
    regiones = df_global['region'].value_counts().to_dict()
    return {
        "regiones": regiones,
        "total": len(regiones)
    }

@app.get("/health", tags=["General"])
def health_check():
    """Verifica el estado de la API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "eventos_cargados": len(df_global)
    }

# ══════════════════════════════════════════════════════════════════════════════
#  EJECUCIÓN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
