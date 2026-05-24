import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import joblib

# ── Constantes de configuración ────────────────────────────────────────────
TITULO_APP = "Monitor Sísmico | IG-EPN Ecuador"
CENTRO_MAPA_LAT = -1.83
CENTRO_MAPA_LON = -78.18
ZOOM_INICIAL = 6

# Umbrales de clasificación sísmica
MAG_MODERADO = 5.0
MAG_FUERTE = 6.0

# Colores del sistema de alertas
COLOR_LIGERO = "#4ade80"
COLOR_MODERADO = "#f97316"
COLOR_FUERTE = "#ef4444"
COLOR_PRINCIPAL = "#6366f1"

# Límites de muestreo para rendimiento del mapa
MAX_PUNTOS_MAPA = 500
MAX_PUNTOS_HISTORICOS = 300

# ── Configuración de página ────────────────────────────────────────────────
st.set_page_config(
    page_title=TITULO_APP,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS personalizado ──────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Forzar fondo blanco en toda la app */
  [data-testid="stAppViewContainer"],
  [data-testid="stAppViewContainer"] > section,
  .main { background: #f4f6f9 !important; }

  /* Header blanco */
  [data-testid="stHeader"] {
    background: #ffffff !important;
    border-bottom: 1px solid #e0e4e8 !important;
  }
  /* Toolbar del header */
  [data-testid="stToolbar"] { background: #ffffff !important; }

  /* Texto del header visible */
  [data-testid="stHeader"] * { color: #222 !important; }

  .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

  /* ── KPI cards ── */
  .kpi-card {
    background: #ffffff; border-radius: 12px; padding: 1.2rem 1.5rem;
    border: 1px solid #e0e4e8; box-shadow: 0 2px 6px rgba(0,0,0,0.05);
  }
  .kpi-label { font-size: 0.72rem; font-weight: 700; color: #888; text-transform: uppercase; margin-bottom: 4px; }
  .kpi-value { font-size: 2rem; font-weight: 800; color: #222; line-height: 1.1; }
  .kpi-value.red { color: #dc2626; }
  .kpi-badge {
    display: inline-block; margin-top: 6px;
    font-size: 0.72rem; font-weight: 600;
    padding: 3px 10px; border-radius: 12px;
  }
  .badge-blue  { background: #e0f2fe; color: #0284c7; }
  .badge-green { background: #dcfce7; color: #16a34a; }
  .badge-red   { background: #fee2e2; color: #dc2626; }
  .badge-orange{ background: #ffedd5; color: #ea580c; }
  .section-title { font-size: 1.05rem; font-weight: 700; margin-bottom: 0.5rem; }

  /* ── Filtros: fondo blanco en inputs y selects ── */
  [data-testid="stNumberInput"] input,
  [data-testid="stDateInput"]   input,
  [data-testid="stSelectbox"]   div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
    color: #222 !important;
  }
  [data-testid="stNumberInput"] input:focus,
  [data-testid="stDateInput"]   input:focus {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 2px rgba(249,115,22,0.15) !important;
  }
  /* Label de los filtros */
  [data-testid="stNumberInput"] label,
  [data-testid="stDateInput"]   label,
  [data-testid="stSelectbox"]   label {
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    color: #888 !important;
    text-transform: uppercase !important;
  }
  /* Contenedor de filtros con fondo blanco */
  [data-testid="stHorizontalBlock"] {
    background: #ffffff;
    border-radius: 12px;
    padding: 1rem 1.2rem 0.5rem;
    border: 1px solid #e0e4e8;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
  }
</style>
""", unsafe_allow_html=True)

# ── Carga de datos ─────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Carga y preprocesa el dataset de sismos desde el archivo Parquet.
    
    Realiza mapeo de columnas, conversión de tipos y clasificación
    regional. Utiliza cache de Streamlit para evitar recargas innecesarias.
    
    Returns:
        pd.DataFrame: Dataset limpio y listo para visualización.
    """
    # 1. Rutas dinámicas basadas en la estructura de carpetas
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "01_datos_procesados", "sismos_procesados.parquet")
    
    # 2. Carga y limpieza inicial de columnas
    df = pd.read_parquet(path)
    df.columns = df.columns.str.strip()

    # 3. Mapeo flexible de columnas 
    # Busca nombres comunes y los estandariza
    rename_rules = {
        'time_value': 'date', 
        'latitude_value': 'lat', 
        'longitude_value': 'lon', 
        'depth_value': 'depth'
    }
    
    for old_col, new_col in rename_rules.items():
        if old_col in df.columns:
            if new_col == 'date':
                df['date'] = pd.to_datetime(df[old_col], errors='coerce')
            else:
                df[new_col] = pd.to_numeric(df[old_col], errors='coerce')

    # 4. Lógica de Magnitud 
    if 'magnitude' not in df.columns:
        m_val = df['magnitude_value_M'] if 'magnitude_value_M' in df.columns else None
        p_val = df['magnitude_value_P'] if 'magnitude_value_P' in df.columns else None
        
        if m_val is not None and p_val is not None:
            df['magnitude'] = pd.to_numeric(m_val.fillna(p_val), errors='coerce')
        elif m_val is not None:
            df['magnitude'] = pd.to_numeric(m_val, errors='coerce')

    # 5. Clasificación por Regiones 
    def asignar_region(lat: float) -> str:
        """Asigna región geográfica basada en la latitud del epicentro."""
        if pd.isna(lat): return 'Desconocida'
        if lat >= 0:    return 'Norte'
        if lat >= -2:   return 'Centro'
        return 'Sur'
    
    if 'lat' in df.columns:
        df['region'] = df['lat'].apply(asignar_region)

    # 6. Limpieza final y formato para el Dashboard
    # Eliminamos nulos en columnas críticas para Random Forest y KDE
    columnas_criticas = ['lat', 'lon', 'depth', 'magnitude', 'date']
    df = df.dropna(subset=[col for col in columnas_criticas if col in df.columns]).copy()
    
    if 'date' in df.columns:
        df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')

    return df

df_all = load_data()

@st.cache_resource
def load_rf_model():
    """
    Carga el modelo Random Forest Regressor desde la carpeta de modelos.
    """
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base, "04_modelos", "random_forest_regressor.joblib")
    if os.path.exists(model_path):
        try:
            return joblib.load(model_path)
        except Exception as e:
            st.error(f"Error al cargar el modelo Random Forest: {e}")
            return None
    return None

# ── Cabecera ───────────────────────────────────────────────────────────────
col_logo, col_tabs, col_space = st.columns([2, 3, 1])
with col_logo:
    st.markdown("###  Monitor Sísmico\n<small style='color:#888'>IG-EPN · ECUADOR</small>", unsafe_allow_html=True)
with col_tabs:
    tab_sel = st.radio("Vista", ["Dashboard", "Análisis de Patrones", "Predicciones"],
                       horizontal=True, label_visibility="collapsed")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if tab_sel == "Dashboard":

    # ── Filtros ────────────────────────────────────────────────────────────
    with st.container():
        st.markdown("##### FILTROS")
        fc1, fc2, fc3, fc4, fc5, fc6, fc7 = st.columns(7)
        with fc1:
            date_from = st.date_input("DESDE", value=pd.to_datetime("2012-01-01"))
        with fc2:
            date_to   = st.date_input("HASTA", value=pd.to_datetime("2026-04-24"))
        with fc3:
            mag_min   = st.number_input("MAG. MÍN",  value=1.0, step=0.1, format="%.1f")
        with fc4:
            mag_max   = st.number_input("MAG. MÁX",  value=7.0, step=0.1, format="%.1f")
        with fc5:
            dep_min_val = st.number_input("PROF. MÍN (KM)", value=10.0, step=1.0, format="%.0f")
            dep_min = float(dep_min_val)
        with fc6:
            dep_max_val = st.number_input("PROF. MÁX (KM)", value=15.0, step=1.0, format="%.0f")
            dep_max = float(dep_max_val)
        with fc7:
            region    = st.selectbox("REGIÓN", ["Todas","Norte","Centro","Sur"])

    # ── Aplicar filtros ────────────────────────────────────────────────────
    df = df_all.copy()
    df = df[df['date'].dt.date >= date_from]
    df = df[df['date'].dt.date <= date_to]
    df = df[df['magnitude'] >= mag_min]
    df = df[df['magnitude'] <= mag_max]
    df = df[df['depth'] >= dep_min]
    df = df[df['depth'] <= dep_max]
    if region != "Todas":
        df = df[df['region'] == region]

    # ── KPIs ───────────────────────────────────────────────────────────────
    total       = len(df)
    avg_mag     = round(df['magnitude'].mean(), 2) if total else 0
    max_mag     = round(df['magnitude'].max(),  2) if total else 0
    avg_dep     = round(df['depth'].mean(),     2) if total else 0
    n_regions   = df['region'].nunique() if total else 0
    n_ligeros   = int((df['magnitude'] < 5).sum())
    n_fuertes   = int((df['magnitude'] >= 6).sum())
    n_superf    = int((df['depth'] < 70).sum())

    k1, k2, k3, k4 = st.columns(4)
    for col, label, value, badge_txt, badge_cls, red in [
        (k1, "TOTAL EVENTOS",     total,   f"{n_regions} regiones",    "badge-blue",   False),
        (k2, "MAGNITUD MEDIA",    avg_mag, f"{n_ligeros} ligeros",     "badge-green",  False),
        (k3, "MAGNITUD MÁXIMA",   max_mag, f"{n_fuertes} fuertes",     "badge-red",    True),
        (k4, "PROFUNDIDAD MEDIA", f"{avg_dep} km", f"{n_superf} superficiales", "badge-orange", False),
    ]:
        with col:
            val_class = "kpi-value red" if red else "kpi-value"
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-label">{label}</div>
              <div class="{val_class}">{value}</div>
              <span class="kpi-badge {badge_cls}">{badge_txt}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Mapa + Distribución ────────────────────────────────────────────────
    col_map, col_chart = st.columns(2)

    with col_map:
        st.markdown(f'<div class="section-title"> Mapa de Eventos &nbsp;<span class="kpi-badge badge-blue">{total} eventos</span></div>', unsafe_allow_html=True)

        @st.cache_data(show_spinner=False)
        def build_event_map(lats, lons, mags, depths, dates, regions):
            """Construye mapa Folium con marcadores circulares para cada evento sísmico."""
            m = folium.Map(location=[CENTRO_MAPA_LAT, CENTRO_MAPA_LON], zoom_start=ZOOM_INICIAL,
                           tiles="CartoDB positron")
            for lat, lon, mag, dep, dt, reg in zip(lats, lons, mags, depths, dates, regions):
                # Asignar color según nivel de magnitud
                color = COLOR_LIGERO
                if mag >= MAG_FUERTE:   color = COLOR_FUERTE
                elif mag >= MAG_MODERADO: color = COLOR_MODERADO

                if mag >= MAG_FUERTE:
                    cat = "Fuerte"
                    nivel = "🔴 FUERTE"
                elif mag >= 5:
                    cat = "Moderado"
                    nivel = "🟠 MODERADO"
                else:
                    cat = "Ligero"
                    nivel = "🟢 LIGERO"

                tooltip_html = f"""
                <div style="font-family:sans-serif;min-width:190px;padding:4px">
                  <b style="font-size:13px">{nivel}</b>
                  <hr style="margin:6px 0;border-color:#eee">
                  <table style="font-size:12px;width:100%">
                    <tr><td style="color:#888">Magnitud</td><td><b>{mag}</b> ({cat})</td></tr>
                    <tr><td style="color:#888">Profundidad</td><td><b>{dep} km</b></td></tr>
                    <tr><td style="color:#888">Fecha</td><td><b>{dt}</b></td></tr>
                    <tr><td style="color:#888">Región</td><td><b>{reg}</b></td></tr>
                    <tr><td style="color:#888">Coordenadas</td><td><b>{round(lat,3)}, {round(lon,3)}</b></td></tr>
                  </table>
                </div>"""

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=mag * 1.5,
                    color="#ffffff", weight=1,
                    fill=True, fill_color=color, fill_opacity=0.8,
                    tooltip=folium.Tooltip(tooltip_html, sticky=True),
                    popup=folium.Popup(tooltip_html, max_width=220)
                ).add_to(m)
            return m

        m = build_event_map(
            tuple(df['lat']), tuple(df['lon']),
            tuple(df['magnitude']), tuple(df['depth']),
            tuple(df['date_str']), tuple(df['region'])
        )
        st_folium(m, height=460, use_container_width=True)

    # The original layout had only a single column for the interactive map.
    # The distribution chart was removed to restore the initial structure.

    # ── Frecuencia mensual ─────────────────────────────────────────────────
    st.markdown('<div class="section-title"> Frecuencia Mensual por Categoría</div>', unsafe_allow_html=True)
    if total:
        df['ym'] = df['date'].dt.to_period('M').astype(str)
        monthly = df.groupby('ym').apply(lambda g: pd.Series({
            'Total':    len(g),
            'Ligero':   (g['magnitude'] < 5).sum(),
            'Moderado': ((g['magnitude'] >= 5) & (g['magnitude'] < 6)).sum(),
            'Fuerte':   (g['magnitude'] >= 6).sum(),
        }), include_groups=False).reset_index()

        fig_freq = go.Figure()
        for serie, color in [('Total','#6366f1'),('Ligero','#3b82f6'),('Moderado','#f97316'),('Fuerte','#ef4444')]:
            fig_freq.add_trace(go.Scatter(
                x=monthly['ym'], y=monthly[serie],
                name=serie, mode='lines', line=dict(color=color, width=2.5, shape='spline'),
                fill='tozeroy' if serie == 'Total' else 'none',
                fillcolor='rgba(99,102,241,0.06)',
                hovertemplate=f'{serie}: %{{y}}<extra></extra>'
            ))
        y_max = int(monthly[['Total','Ligero','Moderado','Fuerte']].max().max())
        fig_freq.update_layout(
            xaxis_title="Mes", yaxis_title="Nº de Eventos",
            height=360, plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=50, r=20, t=30, b=60),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(tickangle=-45, showgrid=True, gridcolor='#f0f0f0'),
            yaxis=dict(
                rangemode='tozero',
                range=[0, max(y_max * 1.3, 6)],
                showgrid=True, gridcolor='#f0f0f0',
                dtick=max(1, y_max // 6)
            )
        )
        st.plotly_chart(fig_freq, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  ANÁLISIS DE PATRONES HORARIOS
# ══════════════════════════════════════════════════════════════════════════════
elif tab_sel == "Análisis de Patrones":
    st.markdown("### 🕰️ Análisis de Patrones por Horario y Zona")
    st.caption("Identifica concentraciones de actividad sísmica en ventanas de tiempo específicas.")

    # ── Configuración del Patrón ───────────────────────────────────────────
    with st.container():
        c1, c2, c3, c4 = st.columns([1.5, 1.5, 1.5, 1])
        with c1:
            h_start, h_end = st.select_slider(
                "RANGO DE HORAS (24H)",
                options=list(range(24)),
                value=(17, 20)
            )
        with c2:
            reg_patron = st.selectbox("ZONA / REGIÓN", ["Todas","Norte","Centro","Sur"], key="reg_patron")
        with c3:
            mag_min_patron = st.number_input("MAGNITUD MÍNIMA", value=1.0, step=0.5, key="mag_min_patron")
        with c4:
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("Actualizar Análisis", use_container_width=True)

    # ── Procesamiento de Datos del Patrón ──────────────────────────────────
    dp = df_all.copy()
    # Filtro de hora
    dp = dp[(dp['hour'] >= h_start) & (dp['hour'] <= h_end)]
    # Filtro de zona
    if reg_patron != "Todas":
        dp = dp[dp['region'] == reg_patron]
    # Filtro de magnitud
    dp = dp[dp['magnitude'] >= mag_min_patron]

    total_patron = len(dp)
    
    # ── Indicadores del Patrón ─────────────────────────────────────────────
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-label">EVENTOS EN EL RANGO</div>
          <div class="kpi-value">{total_patron}</div>
          <span class="kpi-badge badge-blue">{h_start}:00 - {h_end}:00</span>
        </div>""", unsafe_allow_html=True)
    with k2:
        perc = (total_patron / len(df_all) * 100) if len(df_all) else 0
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-label">% DEL TOTAL HISTÓRICO</div>
          <div class="kpi-value">{perc:.1f}%</div>
          <span class="kpi-badge badge-green">Representatividad</span>
        </div>""", unsafe_allow_html=True)
    with k3:
        avg_m = round(dp['magnitude'].mean(), 2) if total_patron else 0
        st.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-label">MAGNITUD PROMEDIO</div>
          <div class="kpi-value">{avg_m}</div>
          <span class="kpi-badge badge-orange">En este horario</span>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Visualización del Patrón ───────────────────────────────────────────
    col_map_p, col_dist_p = st.columns([1.5, 1])

    with col_map_p:
        st.markdown(f'<div class="section-title">📍 Distribución Espacial del Patrón ({h_start}:00 - {h_end}:00)</div>', unsafe_allow_html=True)
        
        m_patron = folium.Map(location=[-1.83, -78.18], zoom_start=6, tiles="CartoDB positron")
        
        # Mostrar solo una muestra si son demasiados para no ralentizar
        sample_p = dp.sample(min(MAX_PUNTOS_MAPA, len(dp)), random_state=42) if len(dp) > MAX_PUNTOS_MAPA else dp
        
        for _, row in sample_p.iterrows():
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=row['magnitude'] * 1.2,
                color="#6366f1", weight=1, fill=True, fill_opacity=0.4,
                tooltip=f"Hora: {row['hour']}:00 | Mag: {row['magnitude']}"
            ).add_to(m_patron)
        
        st_folium(m_patron, height=400, use_container_width=True)

    with col_dist_p:
        st.markdown('<div class="section-title">📊 Histograma Horario Detallado</div>', unsafe_allow_html=True)
        if total_patron:
            # Mostrar la distribución dentro de las horas del día para ver si hay picos
            by_hour = dp.groupby('hour').size().reset_index(name='count')
            fig_h = px.bar(by_hour, x='hour', y='count', 
                          labels={'hour':'Hora', 'count':'Eventos'},
                          color_discrete_sequence=['#6366f1'])
            fig_h.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20),
                               xaxis=dict(tickmode='linear', tick0=0, dtick=1))
            st.plotly_chart(fig_h, use_container_width=True)

    st.info(f"💡 Este análisis permite ver si en la zona **{reg_patron}**, durante el intervalo **{h_start}:00 - {h_end}:00**, existe una acumulación inusual de eventos en comparación con otros horarios.")

# ══════════════════════════════════════════════════════════════════════════════
#  PREDICCIONES
# ══════════════════════════════════════════════════════════════════════════════
else:
    rf_model = load_rf_model()
    
    st.markdown("### 🔮 Predicción y Análisis de Riesgo Sísmico")
    st.caption("Esta sección combina dos modelos: la predicción de magnitudes mediante Random Forest y la estimación geoespacial con KDE.")
    
    if rf_model is not None:
        # ------------------------------------------------------------------
        # 1. Simulador de Magnitud Dinámico (Random Forest)
        # ------------------------------------------------------------------
        st.markdown('<div class="section-title">1. Simulador de Magnitud Dinámico (Random Forest)</div>', unsafe_allow_html=True)
        st.info("💡 **Cómo usar:** Haz clic en cualquier punto del mapa para mover el marcador y el círculo de afectación. También puedes usar los sliders de la izquierda.")

        # --- 1. Inicialización de los Estados de Sesión Únicos ----------------
        for key, default in [
            ('rf_lat', -1.50), 
            ('rf_lon', -78.50), 
            ('rf_depth', 25.0),
            ('last_map_click', None),
            ('map_click_lat', None),
            ('map_click_lon', None)
        ]:
            if key not in st.session_state:
                st.session_state[key] = default

        # --- 2. Procesar clic del mapa ANTES de crear los widgets ----------------
        # Si hay un clic pendiente del ciclo anterior, actualizar las coordenadas
        if st.session_state.map_click_lat is not None and st.session_state.map_click_lon is not None:
            st.session_state.rf_lat = st.session_state.map_click_lat
            st.session_state.rf_lon = st.session_state.map_click_lon
            # Limpiar el clic pendiente
            st.session_state.map_click_lat = None
            st.session_state.map_click_lon = None
            st.rerun()  # Forzar actualización inmediata

        # --- 3. Predicción con el Modelo de Machine Learning -----------------
        input_data = pd.DataFrame(
            [[st.session_state.rf_lat, st.session_state.rf_lon, st.session_state.rf_depth]], 
            columns=['lat', 'lon', 'depth']
        )
        pred_mag = float(rf_model.predict(input_data)[0])

        # Determinar categorías y colores basados en la magnitud predicha
        if pred_mag >= 6.0:
            cat_name, cat_color, cat_badge = "FUERTE", COLOR_FUERTE, "badge-red"
            cat_desc = "Sismo de gran intensidad."
        elif pred_mag >= 5.0:
            cat_name, cat_color, cat_badge = "MODERADO", COLOR_MODERADO, "badge-orange"
            cat_desc = "Sismo moderado. Daños menores."
        else:
            cat_name, cat_color, cat_badge = "LIGERO", COLOR_LIGERO, "badge-green"
            cat_desc = "Sismo ligero. Sin riesgo estructural."

        # --- 4. Layout Panorámico Horizontal Exacto (Como tu referencia) -----
        col_sliders, col_gauge, col_map = st.columns([1.5, 1.2, 1.8])

        with col_sliders:
            with st.container(border=True):
                st.markdown("<p style='font-weight:bold; color:#333; margin:0 0 5px 0; font-size:0.85rem;'>CONTROLES DEL HIPOCENTRO</p>", unsafe_allow_html=True)
                
                # Callback para actualizar cuando se mueven los sliders
                def update_coords():
                    # Esta función se ejecuta cuando cambian los sliders
                    pass
                
                # LA CLAVE: Enlazamos los sliders directamente al session_state usando 'key'
                st.slider("LATITUD", min_value=-5.0, max_value=1.5, step=0.01, format="%.2f", 
                         key="rf_lat", on_change=update_coords)
                st.slider("LONGITUD", min_value=-82.0, max_value=-75.0, step=0.01, format="%.2f", 
                         key="rf_lon", on_change=update_coords)
                st.slider("PROFUNDIDAD (KM)", min_value=0.0, max_value=300.0, step=1.0, format="%.0f", 
                         key="rf_depth", on_change=update_coords)

        with col_gauge:
            with st.container(border=True):
                st.markdown("<p style='font-weight:bold; font-size:0.75rem; text-align:center; color:#666; margin:0 0 5px 0;'>MAGNITUD ESTIMADA</p>", unsafe_allow_html=True)
                
                # Configuración optimizada del gráfico Plotly para que encaje horizontalmente
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = pred_mag,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    number = {'font': {'size': 20, 'weight': 'bold'}, 'suffix': " Mw"},
                    gauge = {
                        'axis': {'range': [1.0, 8.0], 'tickwidth': 1, 'tickcolor': "#888"},
                        'bar': {'color': cat_color},
                        'bgcolor': "white",
                        'borderwidth': 1,
                        'bordercolor': "#e0e4e8",
                        'steps': [
                            {'range': [1.0, 5.0], 'color': '#f3f4f6'},
                            {'range': [5.0, 6.0], 'color': '#ffedd5'},
                            {'range': [6.0, 8.0], 'color': '#fee2e2'}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 3},
                            'thickness': 0.75,
                            'value': 6.0
                        }
                    }
                ))
                # Ajuste de tamaño exacto para que no se desborde verticalmente
                fig_gauge.update_layout(height=110, margin=dict(l=10, r=10, t=5, b=5), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
                
                st.markdown(f"""
                <div style="text-align: center; margin-top: -5px;">
                    <span class="kpi-badge {cat_badge}" style="font-size:0.75rem; font-weight:bold; padding:2px 10px;">{cat_name}</span>
                    <p style="font-size:0.65rem; color:#666; margin-top:3px; margin-bottom:0;">{cat_desc}</p>
                </div>
                """, unsafe_allow_html=True)

        with col_map:
            # Construcción del mapa centrado en las coordenadas activas
            m_pred = folium.Map(
                location=[st.session_state.rf_lat, st.session_state.rf_lon], 
                zoom_start=7, 
                tiles="CartoDB positron",
                zoom_control=True,
                scrollWheelZoom=True
            )
            
            # Círculo de afectación (Se mueve en tiempo real)
            folium.Circle(
                location=[st.session_state.rf_lat, st.session_state.rf_lon],
                radius=pred_mag * 12000,
                color=cat_color,
                weight=2,
                fill=True,
                fill_color=cat_color,
                fill_opacity=0.25,
                tooltip=f"Zona de afectación estimada ({pred_mag:.2f} Mw)"
            ).add_to(m_pred)
            
            # Marcador arrastrable
            folium.Marker(
                location=[st.session_state.rf_lat, st.session_state.rf_lon],
                icon=folium.Icon(color="red" if pred_mag >= 6.0 else ("orange" if pred_mag >= 5.0 else "blue"), icon="info-sign"),
                draggable=True,
                tooltip="Haz clic en el mapa para cambiar ubicación"
            ).add_to(m_pred)
            
            # Renderizado panorámico con st_folium
            map_output = st_folium(m_pred, height=195, use_container_width=True, key="mapa_rf_unico", returned_objects=["last_clicked"])
            
            # Detectar clics en el mapa para actualizar posición en el PRÓXIMO ciclo
            if map_output and map_output.get("last_clicked"):
                new_click = map_output["last_clicked"]
                # Verificar si es un clic nuevo
                if new_click != st.session_state.last_map_click:
                    st.session_state.last_map_click = new_click
                    new_lat = round(float(new_click["lat"]), 2)
                    new_lon = round(float(new_click["lng"]), 2)
                    
                    # Guardar el clic para procesarlo en el próximo ciclo
                    if new_lat != st.session_state.rf_lat or new_lon != st.session_state.rf_lon:
                        st.session_state.map_click_lat = new_lat
                        st.session_state.map_click_lon = new_lon
                        st.rerun()
            
            # Mostrar coordenadas actuales
            st.markdown(f"""
            <div style="text-align: center; margin-top: 5px; font-size: 0.7rem; color: #666;">
                📍 <b>Lat:</b> {st.session_state.rf_lat:.2f}° | <b>Lon:</b> {st.session_state.rf_lon:.2f}°
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        
    st.markdown('<div class="section-title">2. Estimación de Densidad Geoespacial (Modelo KDE)</div>', unsafe_allow_html=True)
    st.markdown("""
    Visualiza las áreas calientes de acumulación de sismos históricos. 
    Ajusta el bandwidth y la magnitud mínima para ver cómo cambia la concentración de riesgo.
    """)
    
    st.markdown("##### PARÁMETROS DEL MODELO KDE")
    pc1, pc2, pc3, pc4 = st.columns(4)
    with pc1:
        bandwidth   = st.slider("BANDWIDTH KDE",   0.1, 2.0, 0.3, 0.1)
    with pc2:
        risk_points = st.slider("PUNTOS DE RIESGO", 10, 500, 200, 10)
    with pc3:
        mag_min_kde = st.number_input("MAGNITUD MÍNIMA", value=3.5, step=0.5, format="%.1f")
    with pc4:
        region_kde  = st.selectbox("REGIÓN TENDENCIA", ["Todas","Norte","Centro","Sur"])

    # Filtrar datos para KDE
    dk = df_all[df_all['magnitude'] >= mag_min_kde].copy()
    if region_kde != "Todas":
        dk = dk[dk['region'] == region_kde]
    dk = dk.dropna(subset=['lat','lon','magnitude','date_str'])

    total_kde = len(dk)

    # ── Mapa KDE ───────────────────────────────────────────────────────────
    @st.cache_data(show_spinner=False)
    def build_kde_map(bw: float, n_risk: int, mag_min_k: float, reg: str):
        """
        Construye mapa de zonas de riesgo usando estimación de densidad kernel (KDE).
        
        Args:
            bw: Bandwidth del kernel gaussiano.
            n_risk: Número de puntos de riesgo a evaluar.
            mag_min_k: Magnitud mínima para incluir en el análisis.
            reg: Región a filtrar ('Todas' para incluir todo).
            
        Returns:
            tuple: (mapa Folium, total de eventos usados)
        """
        data = df_all[df_all['magnitude'] >= mag_min_k].copy()
        if reg != "Todas":
            data = data[data['region'] == reg]
        data = data.dropna(subset=['lat','lon','magnitude','date_str'])

        m = folium.Map(location=[CENTRO_MAPA_LAT, CENTRO_MAPA_LON], zoom_start=7,
                       tiles="CartoDB positron")

        # Puntos históricos — máximo para rendimiento
        hist = data.sample(min(MAX_PUNTOS_HISTORICOS, len(data)), random_state=1)
        for _, row in hist.iterrows():
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=3, color="transparent",
                fill=True, fill_color="#94a3b8", fill_opacity=0.5,
                popup=f"Mag: {row['magnitude']} | {row['date_str']}"
            ).add_to(m)

        # Zonas KDE
        sample = data.sample(min(n_risk, len(data)), random_state=42)
        mag_arr = sample['magnitude'].values
        mag_min_v = mag_arr.min()
        rng = (mag_arr.max() - mag_min_v) or 1

        # Calcular eventos cercanos por zona para el tooltip
        for _, row in sample.iterrows():
            norm    = (row['magnitude'] - mag_min_v) / rng
            opacity = 0.08 + norm * 0.18
            color   = '#fbbf24' if norm < 0.33 else ('#f97316' if norm < 0.66 else '#ef4444')

            # Nivel de riesgo
            if norm >= 0.66:
                nivel = "🔴 ALTO"
                nivel_txt = "Alta concentración sísmica"
            elif norm >= 0.33:
                nivel = "🟠 MODERADO"
                nivel_txt = "Actividad sísmica moderada"
            else:
                nivel = "🟡 BAJO"
                nivel_txt = "Actividad sísmica baja"

            # Categoría de magnitud
            if row['magnitude'] >= 6:
                cat = "Fuerte"
            elif row['magnitude'] >= 5:
                cat = "Moderado"
            else:
                cat = "Ligero"

            # Contar eventos históricos en radio ~50km de este punto
            dlat = data['lat'] - row['lat']
            dlon = data['lon'] - row['lon']
            cercanos = int(((dlat**2 + dlon**2) < (bw * 0.9)**2).sum())

            tooltip_html = f"""
            <div style="font-family:sans-serif;min-width:180px;padding:4px">
              <b style="font-size:13px">{nivel}</b><br>
              <span style="color:#666;font-size:11px">{nivel_txt}</span>
              <hr style="margin:6px 0;border-color:#eee">
              <table style="font-size:12px;width:100%">
                <tr><td style="color:#888">Magnitud ref.</td><td><b>{row['magnitude']}</b> ({cat})</td></tr>
                <tr><td style="color:#888">Región</td><td><b>{row['region']}</b></td></tr>
                <tr><td style="color:#888">Último evento</td><td><b>{row['date_str']}</b></td></tr>
                <tr><td style="color:#888">Eventos cercanos</td><td><b>{cercanos}</b></td></tr>
                <tr><td style="color:#888">Densidad KDE</td><td><b>{round(norm, 2)}</b></td></tr>
              </table>
            </div>"""

            folium.Circle(
                location=[row['lat'], row['lon']],
                radius=bw * 55000,
                color=None, fill=True,
                fill_color=color, fill_opacity=opacity,
                tooltip=folium.Tooltip(tooltip_html, sticky=True),
                popup=folium.Popup(tooltip_html, max_width=220)
            ).add_to(m)

        return m, len(data)

    st.markdown(f'<div class="section-title"> Zonas de Riesgo Sísmico &nbsp;<span class="kpi-badge badge-red">Modelo KDE</span></div>', unsafe_allow_html=True)

    with st.spinner("Calculando zonas de riesgo..."):
        m_kde, total_kde = build_kde_map(bandwidth, risk_points, mag_min_kde, region_kde)

    st_folium(m_kde, height=500, use_container_width=True)

    # Tendencia anual usa dk recalculado desde df_all
    dk = df_all[df_all['magnitude'] >= mag_min_kde].copy()
    if region_kde != "Todas":
        dk = dk[dk['region'] == region_kde]
    dk = dk.dropna(subset=['lat','lon','magnitude','date_str'])

    # Info modelo
    st.info(f"🔥 Modelo entrenado con **{total_kde}** eventos históricos.  \n"
            "Las zonas rojas indican mayor probabilidad de actividad sísmica futura "
            "basada en densidad histórica (KDE gaussiano con métrica haversine).")

    # ── Tendencia anual ────────────────────────────────────────────────────
    st.markdown('<div class="section-title"> Tendencia Anual</div>', unsafe_allow_html=True)
    if total_kde:
        dk['year'] = dk['date'].dt.year
        by_year = dk.groupby('year').size().reset_index(name='count')
        mean_y  = by_year['count'].mean()
        thresh  = mean_y * 1.5
        by_year['color'] = by_year['count'].apply(
            lambda c: '#ef4444' if c >= thresh else '#3b82f6'
        )

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=by_year['year'].astype(str),
            y=by_year['count'],
            marker_color=by_year['color'],
            hovertemplate='%{x}: %{y} eventos<extra></extra>',
            showlegend=False
        ))
        # Líneas de referencia
        fig_trend.add_shape(type="line", x0=0, x1=1, xref="paper",
                            y0=mean_y, y1=mean_y,
                            line=dict(color="#eab308", width=2, dash="dot"))
        fig_trend.add_annotation(x=1, xref="paper", y=mean_y,
                                 text="Media", font=dict(color="#eab308", size=10),
                                 showarrow=False, xanchor="left")
        fig_trend.add_shape(type="line", x0=0, x1=1, xref="paper",
                            y0=thresh, y1=thresh,
                            line=dict(color="#ef4444", width=2, dash="dot"))
        fig_trend.add_annotation(x=1, xref="paper", y=thresh,
                                 text="Umbral anomalía", font=dict(color="#ef4444", size=10),
                                 showarrow=False, xanchor="left")
        # Leyenda manual
        fig_trend.add_trace(go.Bar(x=[None], y=[None], marker_color='#3b82f6', name='Normal', showlegend=True))
        fig_trend.add_trace(go.Bar(x=[None], y=[None], marker_color='#ef4444', name='Anomalía', showlegend=True))

        fig_trend.update_layout(
            xaxis_title="Año", yaxis_title="Eventos",
            height=350, plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40, r=120, t=20, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            barmode='overlay'
        )
        st.plotly_chart(fig_trend, use_container_width=True)
