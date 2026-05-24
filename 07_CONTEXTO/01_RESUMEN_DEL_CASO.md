# Resumen del Caso: Análisis y Visualización de la Actividad Sísmica en Ecuador

El presente proyecto está enfocado en el análisis y predicción de la actividad sísmica en territorio nacional ecuatoriano, utilizando para su efecto datos históricos recopilados por el Instituto Geofísico de la Escuela Politécnica Nacional (IG-EPN), en cosecuencia a la ubicación del país en el Cinturón de Fuego del Pacífico y la interacción de las placas de Nazca y Sudamericana, el riesgo sísmico representa una constante crítica para la seguridad nacional y su infraestructura.

El sistema busca transformar grandes volúmenes de datos crudos en un tablero de control, un dashboard interactivo que facilite la visualización de la densidad sísmica mediante estimaciones de Kernel (KDE) así como la predicción de comportamientos mediante modelos de aprendizaje automático como Random Forest, simplificando la interpretación técnica para la prevención de desastres.

## Contexto del dominio

El monitoreo sísmico en Ecuador es gestionado principalmente por el IG-EPN, institución que opera la Red Nacional de Estaciones Sísmicas. No obstante, las decisiones recaen sobre la Secretaría de Gestión de Riesgos y las administraciones locales, cuya prioridad es mitigar las pérdidas humanas y el perjuicio económico derivados de un sismo. Por ello, la precisión en la categorización de los datos es vital para la planificación urbana y la respuesta inmediata ante emergencias

## 3. Objetivos
*   **Limpieza de Datos**: Procesar el catálogo sísmico nacional para eliminar inconsistencias y errores de formato.
*   **Visualización**: Implementar un dashboard interactivo utilizando Python y Streamlit para representar magnitudes, profundidades y geolocalización de eventos.
*   **Análisis Estadístico**: Identificar zonas de mayor recurrencia sísmica en el territorio ecuatoriano.

## 4. Tecnologías Utilizadas
*   **Lenguaje**: Python 3.x
*   **Framework de Visualización**: Streamlit
*   **Procesamiento de Datos**: Pandas / NumPy
*   **Fuente de Datos**: IG-EPN (Instituto Geofísico de la Escuela Politécnica Nacional)

## 4. Referencias
*   **Instituto Geofísico (IG-EPN).** (2012-2026). Informe del Estado de la Vigilancia Sísmica y Volcánica en el Ecuador. Escuela Politécnica Nacional.

*   **Servicio Geológico de los Estados Unidos (USGS)** (2016). Tectonic Summary of Ecuador and surroundings. Earthquake Hazards Program.

*   **Secretaría de Gestión de Riesgos.** (2024). Plan Nacional de Respuesta ante Desastres (Ecuador 2024). Gobierno de la República del Ecuador.

# Preguntas del Negocio

*  ¿Es posible identificar zonas de alto riesgo sísmico y predecir la magnitud de futuros eventos mediante modelos supervisados basados en el historial 2012-2026?

    * ¿Cómo varía la densidad de sismos (KDE) entre las regiones Norte, Centro y Sur del país?

    * ¿Qué relación existe entre la profundidad de los eventos y su magnitud registrada en las costas ecuatorianas?

# Métrica de Éxito (KPI)

* **KPI** Error Absoluto Medio (MAE) del modelo de predicción de magnitud.

* **Dirección** Disminución (Se busca que el error de predicción sea menor al 15% respecto a la magnitud real registrada).

# Diccionario de variables

| Nombre | Tipo | Descripción | Rango | % Nulos | Observaciones |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `time_value` | Datetime | Fecha y hora exacta del evento | 2012 - 2025 | 0% | Variable temporal crítica. |
| `latitude_value` | Float | Coordenada geográfica (Latitud) | -5.0 a 1.5 | 0% | Usada para el mapa KDE. |
| `longitude_value` | Float | Coordenada geográfica (Longitud) | -82.0 a -75.0 | 0% | Esencial para georreferenciación. |
| `depth_value` | Float | Profundidad del hipocentro (km) | 0 - 300 km | 2% | Predictor para el Random Forest. |
| `magnitude` | Float | Magnitud del sismo (Escala Mw/Ml) | 1.5 - 7.8 | 0% | Variable objetivo (Target). |
| `region` | Categorical | Clasificación geográfica | Norte, Centro, Sur | 0% | Creada mediante Feature Engineering. |

# Hipótesis Iniciales

   * Los sismos registrados en la región Sur presentan una profundidad promedio significativamente mayor a los de la región Norte.

   * Existe una correlación positiva entre la magnitud del evento y el tiempo transcurrido desde el último sismo de gran escala en la misma falla.

   * El modelo de Random Forest tendrá mayor precisión prediciendo magnitudes en eventos superficiales (profundidad < 30km) que en eventos profundos.

   * La densidad sísmica detectada por KDE mostrará una mayor concentración de eventos en el perfil costero que en la región amazónica.

   * Los sismos de magnitud superior a 5.0 tienden a ocurrir en racimos (clusters) temporales de menos de 48 horas.
