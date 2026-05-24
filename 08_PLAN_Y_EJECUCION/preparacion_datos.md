# Preparación de Datos Sísmicos

## 1. Origen de los Datos
Los datos crudos se obtienen del catálogo sísmico del **Instituto Geofísico de la Escuela Politécnica Nacional (IG-EPN)**. El archivo original (`cat_origen_2012_2025.txt`) se gestiona localmente debido a su formato no estándar y tamaño.

## 2. Plan de Preparación y Limpieza

### Pasos de Limpieza y Justificación
1.  **Estandarización de Cabeceras**: Se eliminan espacios en blanco en los nombres de las columnas (`strip()`) para evitar errores de referencia.
2.  **Conversión de Tipos Coherente**: Transformación de strings a numéricos y fechas. Sin esto, no es posible realizar cálculos estadísticos o visualizaciones geoespaciales.
3.  **Priorización de Magnitud**: Se utiliza `magnitude_value_M` como fuente principal y `magnitude_value_P` como respaldo. Esto maximiza la cantidad de registros con magnitud válida.
4.  **Eliminación de Registros Incompletos**: Se descartan eventos que carecen de coordenadas, profundidad, magnitud o fecha. Un sismo sin ubicación o fuerza no aporta valor al análisis de riesgo.

### Decisiones Técnicas
*   **Nulos**: Se eliminan registros con nulos en columnas críticas. Para la columna `region`, los valores fuera de rango se marcan como "Desconocida".
*   **Duplicados**: Se mantiene la integridad basada en el ID de evento único proporcionado por el IG-EPN.
*   **Outliers**: **No se eliminan** sismos de magnitudes extremas (ej. 7.8), ya que son eventos reales fundamentales para la identificación de zonas de alto riesgo.
*   **Fechas y Encodings**: Uso de encoding UTF-8 y conversión a objetos `datetime` de Python (ISO-8601) para facilitar el manejo de series temporales.
*   **Almacenamiento**: Se utiliza el formato **Parquet** con compresión Snappy para optimizar la velocidad de lectura en el Dashboard y reducir el uso de disco.

## 3. Ingeniería de Variables (Feature Engineering)
Se crearon las siguientes variables para enriquecer el análisis:
*   **`year`, `month`, `day`, `hour`**: Extraídas de la fecha para permitir filtros rápidos y análisis de estacionalidad/tendencia anual.
*   **`region`**: Clasificación en **Norte, Centro y Sur** basada en umbrales de latitud, permitiendo segmentar el riesgo por zonas geográficas del Ecuador.
*   **`categoria`**: Clasificación cualitativa de la magnitud (**Ligero, Moderado, Fuerte**) basada en escalas sismológicas estándar.
*   **`tipo_profundidad`**: Categorización en **Superficial, Intermedio o Profundo**, crítica para entender el potencial de daño estructural.

## 4. Descarte de Datos
*   **Variables de error técnico**: Se descartan columnas de incertidumbre (errores de latitud/longitud) para simplificar el modelo de visualización, manteniendo solo el evento final procesado.
*   **Registros pre-2012**: Se descartan si la calidad del dato no cumple con los estándares mínimos de instrumentación moderna del IG-EPN.

## 5. Diccionario de Datos Procesado
*   **event**: Identificador único del sismo.
*   **date**: Fecha y hora completa (datetime).
*   **lat / lon**: Coordenadas decimales estandarizadas.
*   **depth**: Profundidad en km (numérico).
*   **magnitude**: Magnitud final calculada (numérico).
*   **region**: Zona geográfica asignada.
*   **categoria**: Nivel de intensidad del sismo.