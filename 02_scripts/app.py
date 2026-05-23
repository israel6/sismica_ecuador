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
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "01_datos_procesados", "sismos_procesados.parquet")
    
    df = pd.read_parquet(path)
    df.columns = df.columns.str.strip()

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

    if 'magnitude' not in df.columns:
        m_val = df['magnitude_value_M'] if 'magnitude_value_M' in df.columns else None
        p_val = df['magnitude_value_P'] if 'magnitude_value_P' in df.columns else None
        
        if m_val is not None and p_val is not None:
            df['magnitude'] = pd.to_numeric(m_val.fillna(p_val), errors='coerce')
        elif m_val is not None:
            df['magnitude'] = pd.to_numeric(m_val, errors='coerce')

    def asignar_region(lat: float) -> str:
        if pd.isna(lat): return 'Desconocida'
        if lat >= 0:    return 'Norte'
        if lat >= -2:   return 'Centro'
        return 'Sur'
    
    if 'lat' in df.columns:
        df['region'] = df['lat'].apply(asignar_region)

    columnas_criticas = ['lat', 'lon', 'depth', 'magnitude', 'date']
    df = df.dropna(subset=[col for col in columnas_criticas if col in df.columns]).copy()
    
    if 'date' in df.columns:
        df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')

    return df

df_all = load_data()

@st.cache_resource
def load_rf_model():
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
            m = folium.Map(location=[CENTRO_MAPA_LAT, CENTRO_MAPA_LON], zoom_start=ZOOM_INICIAL,
                           tiles="CartoDB positron")
            for lat, lon, mag, dep, dt, reg in zip(lats, lons, mags, depths, dates, regions):
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
        st_folium(m, height=460, use_container_width=True, key="dashboard_map")

    with col_chart:
        st.markdown('<div class="section-title"> Distribución de Magnitudes</div>', unsafe_allow_html=True)
        if total:
            df['mag_bin'] = (np.floor(df['magnitude'] * 10) / 10).round(1)
            bins = df.groupby('mag_bin').size().reset_index(name='count')
            bins['color'] = bins['mag_bin'].apply(
                lambda m: '#ef4444' if m >= 6 else ('#f97316' if m >= 5 else '#3b82f6')
            )
            fig_dist = go.Figure(go.Bar(
                x=bins['mag_bin'].astype(str),
                y=bins['count'],
                marker_color=bins['color'],
                hovertemplate='Mag %{x}: %{y} eventos<extra></extra>'
            ))
            fig_dist.add_shape(type="line",
                x0='5.0', x1='5.0', y0=0, y1=1, yref="paper",
                line=dict(color="#f97316", width=2, dash="dot"))
            fig_dist.add_annotation(x='5.0', y=1, yref="paper",
                text="Moderado", font=dict(color="#f97316", size=10),
                showarrow=False, yanchor="bottom")
            fig_dist.add_shape(type="line",
                x0='6.0', x1='6.0', y0=0, y1=1, yref="paper",
                line=dict(color="#ef4444", width=2, dash="dot"))
            fig_dist.add_annotation(x='6.0', y=1, yref="paper",
                text="Fuerte", font=dict(color="#ef4444", size=10),
                showarrow=False, yanchor="bottom")
            fig_dist.update_layout(
                xaxis_title="Magnitud", yaxis_title="Eventos",
                showlegend=False, height=460,
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=40, r=20, t=20, b=40),
                xaxis=dict(tickangle=0)
            )
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("Sin datos para los filtros seleccionados.")

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

    dp = df_all.copy()
    dp = dp[(dp['hour'] >= h_start) & (dp['hour'] <= h_end)]
    if reg_patron != "Todas":
        dp = dp[dp['region'] == reg_patron]
    dp = dp[dp['magnitude'] >= mag_min_patron]

    total_patron = len(dp)
    
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

    col_map_p, col_dist_p = st.columns([1.5, 1])

    with col_map_p:
        st.markdown(f'<div class="section-title">📍 Distribución Espacial del Patrón ({h_start}:00 - {h_end}:00)</div>', unsafe_allow_html=True)
        
        m_patron = folium.Map(location=[-1.83, -78.18], zoom_start=6, tiles="CartoDB positron")
        sample_p = dp.sample(min(MAX_PUNTOS_MAPA, len(dp)), random_state=42) if len(dp) > MAX_PUNTOS_MAPA else dp
        
        for _, row in sample_p.iterrows():
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=row['magnitude'] * 1.2,
                color="#6366f1", weight=1, fill=True, fill_opacity=0.4,
                tooltip=f"Hora: {row['hour']}:00 | Mag: {row['magnitude']}"
            ).add_to(m_patron)
        
        st_folium(m_patron, height=400, use_container_width=True, key="patterns_map")

    with col_dist_p:
        st.markdown('<div class="section-title">📊 Histograma Horario Detallado</div>', unsafe_allow_html=True)
        if total_patron:
            by_hour = dp.groupby('hour').size().reset_index(name='count')
            fig_h = px.bar(by_hour, x='hour', y='count', 
                          labels={'hour':'Hora', 'count':'Eventos'},
                          color_discrete_sequence=['#6366f1'])
            fig_h.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20),
                                xaxis=dict(tickmode='linear', tick0=0, dtick=1))
            st.plotly_chart(fig_h, use_container_width=True)

    st.info(f"💡 Este análisis permite ver si en la zona **{reg_patron}**, durante el intervalo **{h_start}:00 - {h_end}:00**, existe una acumulación inusual de eventos en comparación con otros horarios.")

# ══════════════════════════════════════════════════════════════════════════════
#  PREDICCIONES (INTEGRACIÓN MARCADOR ARRASTRABLE BIDIRECCIONAL)
# ══════════════════════════════════════════════════════════════════════════════
else:
    rf_model = load_rf_model()
    
    st.markdown("### 🔮 Predicción y Análisis de Riesgo Sísmico")
    st.caption("Esta sección combina dos modelos: la predicción de magnitudes mediante Random Forest y la estimación geoespacial con KDE.")
    
    if rf_model is not None:
        st.markdown('<div class="section-title">1. Simulador de Magnitud Dinámico (Random Forest)</div>', unsafe_allow_html=True)
        st.markdown("""
        **Interactividad en mapa:** Arrastra el marcador azul por el territorio nacional (ej. de Cuenca a Pedernales). 
        Las coordenadas se capturarán automáticamente y reevaluarán el modelo matemático al instante.
        """)
        
        # Inicializar el estado de sesión para las coordenadas de simulación
        if "rf_lat_sim" not in st.session_state:
            st.session_state.rf_lat_sim = CENTRO_MAPA_LAT
        if "rf_lon_sim" not in st.session_state:
            st.session_state.rf_lon_sim = CENTRO_MAPA_LON

        col_rf_inputs, col_rf_outputs = st.columns([1.2, 1.8])
        
        with col_rf_inputs:
            # Mapa bidireccional interactivo
            m_interactivo = folium.Map(
                location=[st.session_state.rf_lat_sim, st.session_state.rf_lon_sim], 
                zoom_start=7, 
                tiles="CartoDB positron"
            )
            
            # Marcador ARRASTRABLE
            marcador_movible = folium.Marker(
                location=[st.session_state.rf_lat_sim, st.session_state.rf_lon_sim],
                popup="Arrastra este pin al epicentro simulado",
                tooltip="¡Arrástrame para cambiar coordenadas!",
                draggable=True,
                icon=folium.Icon(color="blue", icon="info-sign")
            )
            marcador_movible.add_to(m_interactivo)
            
            # Renderizar y capturar datos en caliente
            output_mapa_interactivo = st_folium(m_interactivo, height=340, use_container_width=True, key="mapa_arrastrable_rf")
            
            # Detectar el evento de soltar el marcador (DragEnd)
            if output_mapa_interactivo and output_mapa_interactivo.get("last_marker") is not None:
                nueva_lat = round(output_mapa_interactivo["last_marker"]["lat"], 4)