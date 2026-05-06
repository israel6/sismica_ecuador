# Preparación de Datos Sísmicos

## 1. Origen de los Datos
Los datos crudos se obtienen del catálogo sísmico del **Instituto Geofísico de la Escuela Politécnica Nacional (IG-EPN)**, debido a su tamaño (>100MB), el archivo original se gestiona localmente y no se sincroniza en GitHub.

## 2. Proceso de ETL (Extract, Transform, Load)
El script `02_scripts/process_data.py` realiza las siguientes tareas:
*   **Limpieza**: Manejo de valores nulos en las columnas de magnitud y profundidad.
*   **Normalización**: Conversión de fechas y horas al formato ISO-8601.
*   **Filtrado Geográfico**: Delimitación de eventos dentro del territorio ecuatoriano (incluyendo Galápagos).
*   **Reducción**: Exportación de una muestra representativa (`muestra_sismica.csv`) de ~15MB para asegurar la funcionalidad del dashboard en entornos de prueba.

## 3. Diccionario de Datos Básico
*   **timestamp**: Fecha y hora del evento.
*   **latitude/longitude**: Coordenadas epicentrales.
*   **depth**: Profundidad en kilómetros.
*   **mag**: Magnitud del sismo.