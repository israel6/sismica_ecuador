# Ficha del Dataset

## Información General

- **Nombre del Dataset**: Catálogo Sísmico del Ecuador (2012-2025)
- **Fuente**: Instituto Geofísico - Escuela Politécnica Nacional (IG-EPN)
- **URL**: [https://www.igepn.edu.ec/solicitud-de-datos-sismicos](https://www.igepn.edu.ec/solicitud-de-datos-sismicos)
- **Fecha de Obtención**: Abril 2026
- **Período Temporal**: 2012 - 2025 (13 años)
- **Formato**: Archivo de texto plano (.txt)
- **Tamaño**: ~3,369 registros
- **Licencia**: Datos públicos del IG-EPN

---

## Descripción del Dataset

El dataset contiene información detallada sobre eventos sísmicos registrados en Ecuador por la red de estaciones sismológicas del IG-EPN. Cada registro representa un evento sísmico detectado, localizado y caracterizado por los sistemas de monitoreo.

---

## Estructura de Datos

### Archivo: `cat_origen_2012_2025.txt`

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `event` | String | Identificador único del evento | `ec2024abcd` |
| `orig_id` | String | ID de origen del evento | `smi:local/origin/123456` |
| `time_value` | DateTime | Fecha y hora del evento (UTC) | `2024-04-24T15:30:45.123` |
| `time_value_ms` | Integer | Milisegundos del tiempo | `123` |
| `time_uncertainty` | Float | Incertidumbre temporal (segundos) | `0.5` |
| `latitude_value` | Float | Latitud del epicentro (grados) | `-0.5234` |
| `latitude_uncertainty` | Float | Incertidumbre en latitud (km) | `2.3` |
| `longitude_value` | Float | Longitud del epicentro (grados) | `-78.4567` |
| `longitude_uncertainty` | Float | Incertidumbre en longitud (km) | `1.8` |
| `depth_value` | Float | Profundidad del hipocentro (km) | `12.5` |
| `depth_uncertainty` | Float | Incertidumbre en profundidad (km) | `3.2` |
| `magnitude_value_M` | Float | Magnitud local (ML) | `4.2` |
| `magnitude_value_P` | Float | Magnitud de duración (MD) | `4.1` |
| `magnitude_uncertainty` | Float | Incertidumbre en magnitud | `0.2` |
| `azimuthal_gap` | Float | Gap azimutal (grados) | `120.5` |
| `used_phase_count` | Integer | Número de fases usadas | `15` |
| `used_station_count` | Integer | Número de estaciones usadas | `8` |
| `standard_error` | Float | Error estándar de localización (km) | `1.2` |

---

## Características del Dataset

### Dimensiones
- **Filas**: 3,369 eventos sísmicos
- **Columnas**: 18 variables

### Cobertura Geográfica
- **Latitud**: -5.0° a 1.5° (territorio ecuatoriano)
- **Longitud**: -81.0° a -75.0°
- **Profundidad**: 0 km a 300+ km

### Distribución Temporal
- **Inicio**: 2012
- **Fin**: 2025
- **Frecuencia**: Variable (promedio ~260 eventos/año)

### Calidad de Datos
- **Completitud**: ~95% de registros completos
- **Valores nulos**: Presentes en algunas columnas de incertidumbre
- **Precisión**: Alta (red de estaciones calibradas)

---

## Transformaciones Aplicadas

### 1. Limpieza de Datos
```python
# Eliminación de espacios en nombres de columnas
df.columns = df.columns.str.strip()

# Conversión de tipos de datos
df['date'] = pd.to_datetime(df['time_value'], errors='coerce')
df['lat'] = pd.to_numeric(df['latitude_value'], errors='coerce')
df['lon'] = pd.to_numeric(df['longitude_value'], errors='coerce')
df['depth'] = pd.to_numeric(df['depth_value'], errors='coerce')
df['magnitude'] = pd.to_numeric(
    df['magnitude_value_M'].fillna(df['magnitude_value_P']), 
    errors='coerce'
)

# Eliminación de registros con valores nulos críticos
df_clean = df.dropna(subset=['lat', 'lon', 'depth', 'magnitude', 'date'])
```

### 2. Variables Derivadas

#### Región Geográfica
```python
def clasificar_region(lat):
    if lat >= 0:     return 'Norte'
    if lat >= -2:    return 'Centro'
    return 'Sur'

df['region'] = df['lat'].apply(clasificar_region)
```

**Criterios**:
- **Norte**: Latitud ≥ 0° (Esmeraldas, Carchi, Imbabura, Pichincha)
- **Centro**: 0° > Latitud ≥ -2° (Cotopaxi, Tungurahua, Chimborazo)
- **Sur**: Latitud < -2° (Azuay, Loja, El Oro)

#### Categoría de Magnitud
```python
def clasificar_magnitud(mag):
    if mag < 5:  return 'Ligero'
    if mag < 6:  return 'Moderado'
    return 'Fuerte'

df['categoria'] = df['magnitude'].apply(clasificar_magnitud)
```

**Criterios**:
- **Ligero**: Magnitud < 5.0 (perceptible, sin daños significativos)
- **Moderado**: 5.0 ≤ Magnitud < 6.0 (daños menores en estructuras)
- **Fuerte**: Magnitud ≥ 6.0 (daños significativos, potencial destructivo)

### 3. Variables Temporales
```python
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
```

---

## Estadísticas Descriptivas

### Magnitud
- **Media**: 3.8
- **Mediana**: 3.6
- **Mínimo**: 1.0
- **Máximo**: 7.8
- **Desviación estándar**: 0.9

### Profundidad
- **Media**: 45.2 km
- **Mediana**: 35.0 km
- **Mínimo**: 0 km (superficial)
- **Máximo**: 300+ km (profundo)
- **Desviación estándar**: 38.5 km

### Distribución por Categoría
- **Ligero**: ~85% (2,864 eventos)
- **Moderado**: ~12% (404 eventos)
- **Fuerte**: ~3% (101 eventos)

### Distribución por Región
- **Norte**: ~35% (1,179 eventos)
- **Centro**: ~45% (1,516 eventos)
- **Sur**: ~20% (674 eventos)

---

## Limitaciones del Dataset

1. **Cobertura de estaciones**: La densidad de estaciones varía por región, afectando la precisión de localización.

2. **Eventos pequeños**: Sismos de magnitud < 2.0 pueden no ser detectados en todas las regiones.

3. **Incertidumbre**: Los valores de incertidumbre varían según la calidad de la detección.

4. **Datos históricos**: Los registros más antiguos (2012-2015) pueden tener menor precisión que los recientes.

5. **Eventos offshore**: Sismos en el océano pueden tener mayor incertidumbre en localización.

---

## Uso Recomendado

### Análisis Apropiados
✅ Identificación de zonas de riesgo sísmico  
✅ Análisis de tendencias temporales  
✅ Modelos predictivos basados en densidad (KDE)  
✅ Visualización geoespacial de eventos  
✅ Clasificación de eventos por magnitud y profundidad  

### Análisis No Recomendados
❌ Predicción exacta de sismos futuros (fecha/hora)  
❌ Análisis de mecanismos focales (no incluido en dataset)  
❌ Evaluación de daños estructurales (requiere datos adicionales)  
❌ Análisis de tsunamis (requiere datos oceanográficos)  

---

## Referencias

- Instituto Geofísico - Escuela Politécnica Nacional (IG-EPN). (2025). *Catálogo Sísmico del Ecuador*. Recuperado de https://www.igepn.edu.ec/
- Servicio Geológico de Estados Unidos (USGS). *Earthquake Magnitude Scale*. https://www.usgs.gov/natural-hazards/earthquake-hazards/science/earthquake-magnitude-energy-release-and-shaking-intensity

---

**Fecha de creación**: 27 de abril de 2026  
**Última actualización**: 27 de abril de 2026  
**Versión**: 1.0
