# Proyecto: Actividad Sísmica Ecuador


## Información del Proyecto
* **Nombre del Grupo:** Grupo 5

## 👥 Integrantes
* [Israel López](https://github.com/israel6) - **Data Lead**
* [Jaime Sarabia](https://github.com/maverickgoledu) - **Product Lead**
* [Diego Valdivieso](https://github.com/DiegoAVG16) - **Model Lead**

* **Caso:**  Actividad Sísmica Ecuador
* **Dataset:** [Catálogo Sísmico IG-EPN](https://www.igepn.edu.ec/solicitud-de-datos-sismicos)
---

##  Actividad Práctica


### 1. Entorno Virtual y Estructura de Carpetas 

El proyecto cuenta con la siguiente estructura de carpetas:

```
proyecto_sismica_ecuador/
├── data/
│   ├── raw/                    # Datos originales (3,369 eventos)
│   └── processed/              # Datos procesados
├── src/                        # Código fuente
│   ├── .streamlit/            # Configuración Streamlit
│   └── app.py                 # Aplicación principal
├── notebooks/                  # Jupyter notebooks
│   └── analisis_exploratorio.ipynb
├── docs/                       # Documentación
│   ├── pregunta_negocio.md
│   └── ficha_dataset.md
├── reports/                    # Reportes generados
├── tests/                      # Tests unitarios
├── .gitignore                 # Exclusiones Git
├── requirements.txt           # Dependencias Python
└── README.md                  # Este archivo
```

### 2. Pregunta de Negocio 

**¿Cómo podemos identificar y predecir las zonas de mayor riesgo sísmico en Ecuador para optimizar la asignación de recursos de prevención y respuesta ante desastres?**

**Justificación:**

Es una pregunta muy relevante porque los sismos en Ecuador representan un riesgo significativo para:
- **Vidas humanas**: Prevención de pérdidas y evacuaciones efectivas
- **Economía**: Reducción de costos por daños a infraestructura
- **Planificación urbana**: Regulación de construcción en zonas de riesgo
- **Recursos**: Asignación estratégica de brigadas y equipos de respuesta
- **Alerta temprana**: Mejora de sistemas de detección y notificación

Ver documento completo: [`docs/pregunta_negocio.md`](docs/pregunta_negocio.md)

### 3. Carga y Exploración del Dataset 

#### Información del Dataset

- **Fuente**: Instituto Geofísico - Escuela Politécnica Nacional (IG-EPN)
- **Período**: 2012 - 2025 (13 años)
- **Total de eventos**: 3,369 registros
- **Variables**: 18 columnas

#### Comandos Ejecutados

```python
import pandas as pd

# Cargar datos
df = pd.read_csv('data/raw/cat_origen_2012_2025.txt', comment='#', skipinitialspace=True)

# Exploración básica
df.head()      # Primeras 5 filas
df.info()      # Información de tipos y nulos
df.shape       # Dimensiones: (3369, 18)
df.describe()  # Estadísticas descriptivas
```

#### Resultados Principales

**Dimensiones:**
- Filas: 3,369 eventos sísmicos
- Columnas: 18 variables

**Estadísticas de Magnitud:**
- Media: 3.8
- Máxima: 7.8
- Mínima: 1.0

**Estadísticas de Profundidad:**
- Media: 45.2 km
- Máxima: 300+ km
- Mínima: 0 km (superficial)

**Distribución por Categoría:**
- Ligero (< 5.0): 85%
- Moderado (5.0-6.0): 12%
- Fuerte (≥ 6.0): 3%

**Distribución por Región:**
- Norte: 35%
- Centro: 45%
- Sur: 20%

 Ver análisis completo: [`notebooks/analisis_exploratorio.ipynb`](notebooks/analisis_exploratorio.ipynb)

### 4. Ficha del Dataset 

Se han creado dos versiones de la ficha del dataset:

**Versión Corta** (requerida por la actividad): [`docs/ficha_dataset_corta.md`](docs/ficha_dataset_corta.md)
- URL/origen
- Licencia
- Fecha de extracción
- Número de registros y columnas
- Tipos por columna
- % de nulos
- Limitaciones conocidas

**Versión Completa** (documentación extendida): [`docs/ficha_dataset.md`](docs/ficha_dataset.md)
- Toda la información de la versión corta
- Estructura detallada de 18 columnas
- Transformaciones aplicadas con código
- Variables derivadas
- Uso recomendado y referencias

---

## Producto Analítico

El proyecto incluye un sistema completo de análisis sísmico con:

### Pipeline Técnico

1. **Carga de datos**: `pd.read_csv(file, sep='\s+', comment='#')` — parsea formato no estándar del IG-EPN
2. **Conversión temporal**: `time_value` a datetime; extrae año, mes, hora y categorías
3. **Asignación de región**: `pd.cut(df['lat'], bins=[-5, -2, 0, 2], labels=['Sur','Centro','Norte'])`
4. **Clasificación**: Magnitud (Ligero/Moderado/Fuerte) y profundidad (Superficial/Intermedio/Profundo)
5. **Almacenamiento**: Guardar catálogo procesado en Parquet con compresión Snappy
6. **Visualización**: `@st.cache_data` en Streamlit para rendimiento óptimo

### Arquitectura del Código

```
02_scripts/
├── config.py          # Configuración centralizada (dataclasses)
├── utils.py           # Funciones auxiliares compartidas
├── process_data.py    # Pipeline ETL con logging
├── api.py             # API REST (FastAPI)
└── app.py             # Dashboard interactivo (Streamlit)
```

### API (FastAPI)

**Endpoints disponibles:**

```bash
# Iniciar API
uvicorn src.api:app --reload --port 8000
```

- `GET /sismos/query?start_date=2020-01-01&end_date=2023-12-31&min_magnitude=4.5` — eventos filtrados
- `GET /sismos/stats?region=Centro` — estadísticas de la región (count, magnitud media, profundidad media)
- `GET /sismos/regiones` — lista de regiones disponibles
- `GET /health` — estado de la API

**Documentación interactiva:** http://localhost:8000/docs

### Dashboard (Streamlit)

**Todos los gráficos responden a los mismos filtros de fecha y magnitud simultáneamente:**

1. **Mapa interactivo** (`px.scatter_mapbox`) — tamaño y color representan magnitud; filtros de fecha y magnitud
2. **Gráfico de líneas** — frecuencia mensual por categoría de magnitud
3. **Histograma** — distribución de magnitudes con líneas verticales en umbrales de categoría

**Documentación completa:** [`docs/producto_analitico.md`](docs/producto_analitico.md)

---

## Instalación y Ejecución

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes Python)

### Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/DiegoAVG16/proyecto_sismica_ecuador.git
cd proyecto_sismica_ecuador
```

2. Crear entorno virtual e instalar dependencias:
```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

**Nota:** Nunca instalen paquetes fuera del venv.

### Ejecutar la Aplicación

```bash
streamlit run src/app.py
```

La aplicación estará disponible en:
- **Local**: http://localhost:8501
- **Red**: http://192.168.1.25:8501

---

## Funcionalidades

### Dashboard Principal

- **Filtros interactivos**: Fechas, magnitud, profundidad, región
- **KPIs**: Total eventos, magnitud media/máxima, profundidad media
- **Mapa interactivo**: Visualización geoespacial con tooltips informativos
- **Distribución de magnitudes**: Histograma con categorías (ligero/moderado/fuerte)
- **Frecuencia mensual**: Gráfico de tendencias por categoría

### Predicciones

- **Modelo KDE**: Kernel Density Estimation para zonas de riesgo
- **Parámetros ajustables**: Bandwidth, puntos de riesgo, magnitud mínima
- **Mapa de riesgo**: Zonas coloreadas por intensidad (amarillo→naranja→rojo)
- **Tendencia anual**: Análisis temporal con detección de anomalías

---

## Dependencias Principales

```
streamlit==1.56.0
pandas==3.0.2
numpy==2.4.4
plotly==6.7.0
folium==0.20.0
streamlit-folium==0.27.1
scikit-learn==1.8.0
```

Ver lista completa: [`requirements.txt`](requirements.txt)

---

## Metodología

### Clasificación de Regiones

- **Norte**: Latitud ≥ 0° (Esmeraldas, Carchi, Imbabura, Pichincha)
- **Centro**: 0° > Latitud ≥ -2° (Cotopaxi, Tungurahua, Chimborazo)
- **Sur**: Latitud < -2° (Azuay, Loja, El Oro)

### Clasificación de Magnitudes

- **Ligero**: < 5.0 (perceptible, sin daños significativos)
- **Moderado**: 5.0 - 6.0 (daños menores en estructuras)
- **Fuerte**: ≥ 6.0 (daños significativos, potencial destructivo)

### Modelo Predictivo

**KDE (Kernel Density Estimation)**:
- Método no paramétrico para estimar densidad de probabilidad
- Identifica zonas con mayor concentración histórica de eventos
- Parámetros: bandwidth (suavizado), magnitud mínima, región

---

## Análisis Exploratorio

El notebook [`notebooks/analisis_exploratorio.ipynb`](notebooks/analisis_exploratorio.ipynb) incluye:

1. Carga y limpieza de datos
2. Análisis estadístico por región y categoría
3. Visualizaciones:
   - Distribución de magnitudes
   - Relación profundidad vs magnitud
   - Tendencia anual
   - Mapa de calor mensual
4. Conclusiones y recomendaciones

---

## Documentación

- [`docs/pregunta_negocio.md`](docs/pregunta_negocio.md): Contexto, justificación y objetivos
- [`docs/ficha_dataset_corta.md`](docs/ficha_dataset_corta.md): Ficha corta del dataset (actividad práctica)
- [`docs/ficha_dataset.md`](docs/ficha_dataset.md): Ficha completa del dataset (documentación extendida)
- [`docs/producto_analitico.md`](docs/producto_analitico.md): Pipeline técnico, API y Dashboard completo

---

## Contribuciones

Este proyecto fue desarrollado como parte de una actividad académica. Para contribuciones:

1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

---

## Licencia

Datos públicos del Instituto Geofísico - Escuela Politécnica Nacional (IG-EPN).

---

## Contacto

- **Grupo 5** - Proyecto Actividad Sísmica Ecuador
- **Repositorio**: [https://github.com/DiegoAVG16/proyecto_sismica_ecuador](https://github.com/DiegoAVG16/proyecto_sismica_ecuador)

---

**Última actualización**: 15 de mayo de 2026
Refactorización del código: módulo de utilidades, configuración centralizada, type hints, logging y documentación mejorada
