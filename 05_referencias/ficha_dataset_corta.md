# Ficha del Dataset - Catálogo Sísmico Ecuador

## Información Básica

- **URL/Origen**: [Instituto Geofísico - Escuela Politécnica Nacional (IG-EPN)](https://www.igepn.edu.ec/solicitud-de-datos-sismicos)
- **Licencia**: Datos públicos del IG-EPN
- **Fecha de extracción**: Abril 2026
- **Período temporal**: 2012 - 2025 (13 años)

---

## Características del Dataset

### Dimensiones
- **Número de registros**: 3,369 eventos sísmicos
- **Número de columnas**: 18 variables

### Columnas Principales

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `event` | String | Identificador único del evento |
| `time_value` | DateTime | Fecha y hora del evento (UTC) |
| `latitude_value` | Float | Latitud del epicentro (grados) |
| `longitude_value` | Float | Longitud del epicentro (grados) |
| `depth_value` | Float | Profundidad del hipocentro (km) |
| `magnitude_value_M` | Float | Magnitud local (ML) |
| `magnitude_value_P` | Float | Magnitud de duración (MD) |
| `used_station_count` | Integer | Número de estaciones usadas |

### Tipos por Columna

- **String**: 2 columnas (identificadores)
- **DateTime**: 1 columna (tiempo)
- **Float**: 13 columnas (coordenadas, magnitudes, incertidumbres)
- **Integer**: 2 columnas (contadores)

---

## Calidad de Datos

### Porcentaje de Nulos

- **Columnas críticas** (lat, lon, depth, magnitude, date): ~5% nulos
- **Columnas de incertidumbre**: ~15% nulos
- **Columnas de conteo**: 0% nulos

**Total de registros completos**: ~3,200 (95%)

---

## Limitaciones Conocidas

1. **Cobertura geográfica desigual**: Mayor densidad de estaciones en la región Centro, menor en zonas remotas.

2. **Detección de eventos pequeños**: Sismos de magnitud < 2.0 pueden no ser detectados en todas las regiones.

3. **Incertidumbre variable**: La precisión de localización depende del número de estaciones que detectaron el evento.

4. **Datos históricos**: Los registros más antiguos (2012-2015) tienen menor precisión que los recientes debido a mejoras en la red de monitoreo.

5. **Eventos offshore**: Sismos en el océano Pacífico tienen mayor incertidumbre en localización por menor cobertura de estaciones.

6. **Magnitud dual**: Algunos eventos tienen dos tipos de magnitud (ML y MD), requiere consolidación.

---

## Estadísticas Descriptivas

### Magnitud
- Media: 3.8
- Mediana: 3.6
- Mínimo: 1.0
- Máximo: 7.8
- Desviación estándar: 0.9

### Profundidad
- Media: 45.2 km
- Mediana: 35.0 km
- Mínimo: 0 km
- Máximo: 300+ km
- Desviación estándar: 38.5 km

### Distribución por Categoría
- **Ligero** (< 5.0): 85% (2,864 eventos)
- **Moderado** (5.0-6.0): 12% (404 eventos)
- **Fuerte** (≥ 6.0): 3% (101 eventos)

---

**Fecha de creación**: 27 de abril de 2026  
**Versión**: 1.0
