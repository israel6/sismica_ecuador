import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

# ── Configuración de página ────────────────────────────────────────────────
st.set_page_config(
    page_title="Monitor Sísmico | IG-EPN Ecuador",
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
def load_data():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "data", "raw", "cat_origen_2012_2025.txt")
    df = pd.read_csv(path, comment='#', skipinitialspace=True)
    df.columns = df.columns.str.strip()
    df['date']      = pd.to_datetime(df['time_value'], errors='coerce')
    df['lat']       = pd.to_numeric(df['latitude_value'],  errors='coerce')
    df['lon']       = pd.to_numeric(df['longitude_value'], errors='coerce')
    df['depth']     = pd.to_numeric(df['depth_value'],     errors='coerce')
    df['magnitude'] = pd.to_numeric(
        df['magnitude_value_M'].fillna(df['magnitude_value_P']), errors='coerce'
    )
    def region(lat):
        if pd.isna(lat): return 'Desconocida'
        if lat >= 0:     return 'Norte'
        if lat >= -2:    return 'Centro'
        return 'Sur'
    df['region'] = df['lat'].apply(region)
    df = df.dropna(subset=['lat','lon','depth','magnitude','date']).copy()
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
    return df

df_all = load_data()

# ── Cabecera ───────────────────────────────────────────────────────────────
col_logo, col_tabs, col_space = st.columns([2, 3, 1])
with col_logo:
    st.markdown("###  Monitor Sísmico\n<small style='color:#888'>IG-EPN · ECUADOR</small>", unsafe_allow_html=True)
with col_tabs:
    tab_sel = st.radio("Vista", ["Dashboard", "Predicciones"],
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
            date_from = st.date_input("DESDE", value=pd.to_datetime("2024-04-24"))
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
            m = folium.Map(location=[-1.83, -78.18], zoom_start=6,
                           tiles="CartoDB positron")
            for lat, lon, mag, dep, dt, reg in zip(lats, lons, mags, depths, dates, regions):
                color = "#4ade80"
                if mag >= 6:   color = "#ef4444"
                elif mag >= 5: color = "#f97316"

                if mag >= 6:
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
#  PREDICCIONES
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("##### PARÁMETROS DEL MODELO")
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
    def build_kde_map(bw, n_risk, mag_min_k, reg):
        data = df_all[df_all['magnitude'] >= mag_min_k].copy()
        if reg != "Todas":
            data = data[data['region'] == reg]
        data = data.dropna(subset=['lat','lon','magnitude','date_str'])

        m = folium.Map(location=[-1.83, -78.18], zoom_start=7,
                       tiles="CartoDB positron")

        # Puntos históricos — máximo 300
        hist = data.sample(min(300, len(data)), random_state=1)
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
