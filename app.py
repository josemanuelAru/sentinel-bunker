import streamlit as st
import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astroquery.mast import Catalogs
import astropy.units as u
from astropy.coordinates import SkyCoord

# --- CONFIGURACIÓN DE LA PANTALLA (Modo TV Ancho) ---
st.set_page_config(
    page_title="SENTINEL - Exoplanet Command Center",
    page_icon="🪐",
    layout="wide"
)

# Estética visual Modo Búnker (Oscuro con acentos cian)
st.markdown("""
    <style>
    .main { background-color: #020617; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #1e293b; color: #22d3ee; border: 1px solid #22d3ee; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #0f172a; border-radius: 5px 5px 0 0; color: white; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #22d3ee !important; color: #020617 !important; font-weight: bold; }
    div[data-testid="stMetricValue"] { color: #22d3ee !important; font-family: 'Courier New', monospace; font-size: 28px; }
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-size: 14px; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛰️ PROYECTO SENTINEL: Centro de Mando Cloud")
st.write("---")

# --- ARQUITECTURA DE PESTAÑAS ---
tab_radar, tab_registros, tab_mapas, tab_analisis = st.tabs([
    "📡 RADAR AUTÓNOMO", 
    "🗂️ REGISTROS HISTÓRICOS", 
    "🗺️ MAPAS ESTELARES", 
    "📈 ANÁLISIS Y DESCARGAS"
])

# --- PESTAÑA 1: RADAR ---
with tab_radar:
    st.header("🛸 Escáner de Perímetro Automático")
    col1, col2 = st.columns([1, 4])
    with col1:
        st.button("🚀 INICIAR RADAR", key="btn_start")
        st.button("🛑 PARADA DE EMERGENCIA", key="btn_stop")
        st.info("Estado: En espera...")
    with col2:
        st.subheader("Consola de Observación")
        st.code("Esperando activación del Piloto Automático...")

# --- PESTAÑA 2: REGISTROS HISTÓRICOS ---
with tab_registros:
    st.header("🔍 Buscador de Archivos TESS (NASA)")
    st.write("Introduzca la numeración de la estrella para extraer sus productos de datos oficiales de TESScut.")
    
    tic_id_reg = st.text_input("ID de la Estrella (TIC):", placeholder="Ej: 55187830", key="txt_id_reg")
    
    if tic_id_reg.strip():
        tic_input = tic_id_reg.strip()
        with st.spinner(f"Interrogando a los servidores MAST (TESScut) para TIC {tic_input}..."):
            try:
                search_result = lk.search_tesscut(f"TIC {tic_input}")
                if len(search_result) == 0:
                    st.warning(f"⚠️ No se han encontrado recortes de TESScut para la estrella TIC {tic_input}.")
                else:
                    st.success(f"🎯 SearchResult containing {len(search_result)} data products.")
                    exptimes = [int(t.value) if hasattr(t, 'value') else int(t) for t in search_result.exptime]
                    distances = [round(float(d.value), 1) if hasattr(d, 'value') else round(float(d), 1) for d in search_result.distance]
                    years = [int(y) for y in search_result.year]
                    
                    df_registros = pd.DataFrame({
                        "mission": search_result.mission,
                        "year": years,
                        "author": search_result.author,
                        "exptime": exptimes,
                        "target_name": search_result.target_name,
                        "distance": distances
                    })
                    df_registros['sector_num'] = df_registros['mission'].str.extract(r'Sector (\d+)').astype(int)
                    df_registros = df_registros.sort_values(by='sector_num').drop(columns=['sector_num']).reset_index(drop=True)
                    st.dataframe(df_registros, use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error de conexión: {e}")

# --- PESTAÑA 3: MAPAS ESTELARES CON DOSSIER FÍSICO ---
with tab_mapas:
    st.header("🎯 Localización y Análisis de Vecindario Estelar (#NEB)")
    st.write("Introduzca el ID de la estrella para desplegar la auditoría perimetral y sus propiedades físicas.")
    
    tic_id_mapas = st.text_input("ID de la Estrella (TIC):", placeholder="Ej: 55187830", key="txt_id_mapas")
    
    if tic_id_mapas.strip():
        tic_input = tic_id_mapas.strip()
        with st.spinner(f"Escaneando coordenadas y parámetros físicos para TIC {tic_input}..."):
            try:
                # 1. Consultamos los datos de la estrella objetivo en el catálogo TIC
                target_data = Catalogs.query_criteria(catalog="TIC", ID=int(tic_input))
                
                if len(target_data) == 0:
                    st.error(f"❌ La estrella TIC {tic_input} no existe en el catálogo oficial de la misión.")
                else:
                    # Extracción segura de coordenadas y brillo
                    ra_target = target_data['ra'][0]
                    dec_target = target_data['dec'][0]
                    tmag_target = target_data['Tmag'][0]
                    
                    # 🚨 NUEVO: Extracción quirúrgica de parámetros físicos con control de datos nulos (NaN)
                    rad_estelar = target_data['rad'][0] if 'rad' in target_data.colnames and not np.isnan(target_data['rad'][0]) else None
                    masa_estelar = target_data['mass'][0] if 'mass' in target_data.colnames and not np.isnan(target_data['mass'][0]) else None
                    temp_efectiva = target_data['teff'][0] if 'teff' in target_data.colnames and not np.isnan(target_data['teff'][0]) else None
                    distancia_pc = target_data['d'][0] if 'd' in target_data.colnames and not np.isnan(target_data['d'][0]) else None
                    luminosidad = target_data['lum'][0] if 'lum' in target_data.colnames and not np.isnan(target_data['lum'][0]) else None

                    # 📋 DESPLIEGUE DEL DOSSIER FÍSICO (Paneles Superiores)
                    st.markdown("### 📋 Dossier Astrofísico de la Estrella")
                    m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = st.columns(6)
                    
                    m_col1.metric("Radio Estelar", f"{rad_estelar:.2f} R☉" if rad_estelar else "N/D")
                    m_col2.metric("Masa Estelar", f"{masa_estelar:.2f} M☉" if masa_estelar else "N/D")
                    m_col3.metric("Temperatura", f"{int(temp_efectiva)} K" if temp_efectiva else "N/D")
                    m_col4.metric("Distancia", f"{distancia_pc:.1f} pc" if distancia_pc else "N/D")
                    m_col5.metric("Luminosidad", f"{luminosidad:.2f} L☉" if luminosidad else "N/D")
                    m_col6.metric("Brillo TESS", f"{tmag_target:.2f} mag")
                    
                    st.write("---")

                    # 2. Rastreamos el vecindario en un radio de 120 segundos de arco
                    coord_centro = SkyCoord(ra_target, dec_target, unit="deg")
                    stars_table = Catalogs.query_region(coord_centro, radius=120*u.arcsec, catalog="TIC")
                    df_stars = stars_table.to_pandas()
                    df_stars['Tmag'] = df_stars['Tmag'].fillna(20.0)
                    
                    df_stars['offset_ra'] = (df_stars['ra'] - ra_target) * 3600 * np.cos(np.radians(dec_target))
                    df_stars['offset_dec'] = (df_stars['dec'] - dec_target) * 3600
                    
                    vecinas = df_stars[df_stars['ID'].astype(str) != tic_input]
                    
                    # 3. CONSTRUCCIÓN DE LOS 3 GRÁFICOS COMPAÑEROS
                    fig, axes = plt.subplots(1, 3, figsize=(20, 6.5), dpi=100)
                    plt.style.use('dark_background')
                    
                    # Panel 1: Escáner Perímetro
                    axes[0].scatter(vecinas['offset_ra'], vecinas['offset_dec'], 
                                    s=np.maximum(5, (18 - vecinas['Tmag']) * 12), 
                                    color='#475569', alpha=0.7, label='Estrellas Vecinas')
                    axes[0].scatter(0, 0, s=200, color='#e11d48', marker='*', label=f'TIC {tic_input}')
                    axes[0].set_xlim(-130, 130)
                    axes[0].set_ylim(-130, 130)
                    axes[0].set_xlabel("Offset RA (arcsec)", color='#94a3b8')
                    axes[0].set_ylabel("Offset DEC (arcsec)", color='#94a3b8')
                    axes[0].set_title("1. ESCÁNER DE PERÍMETRO", fontsize=12, fontweight='bold', color='#f8fafc')
                    axes[0].grid(True, linestyle='--', alpha=0.2, color='#334155')
                    axes[0].legend(loc='upper right', fontsize=9)
                    
                    # Panel 2: Táctico Visual
                    for r in [30, 60, 90, 120]:
                        circle = plt.Circle((0, 0), r, fill=False, color='#1e293b', linestyle=':', alpha=0.6)
                        axes[1].add_patch(circle)
                    peligrosas = vecinas[vecinas['Tmag'] <= (tmag_target + 2.5)]
                    inofensivas = vecinas[vecinas['Tmag'] > (tmag_target + 2.5)]
                    
                    axes[1].scatter(inofensivas['offset_ra'], inofensivas['offset_dec'], 
                                    s=np.maximum(5, (18 - inofensivas['Tmag']) * 12), 
                                    color='#38bdf8', alpha=0.5, label='Inofensivas')
                    if not peligrosas.empty:
                        axes[1].scatter(peligrosas['offset_ra'], peligrosas['offset_dec'], 
                                        s=np.maximum(10, (18 - peligrosas['Tmag']) * 16), 
                                        color='#f97316', alpha=0.9, edgecolors='#fdba74', label='⚠️ Contaminación')
                        for _, star in peligrosas.iterrows():
                            axes[1].text(star['offset_ra']+4, star['offset_dec']+4, f"Tmag {star['Tmag']:.1f}", 
                                         color='#fdba74', fontsize=8, alpha=0.8)
                    axes[1].scatter(0, 0, s=250, color='#22d3ee', marker='o', edgecolors='white', label='Objetivo')
                    axes[1].set_xlim(-130, 130)
                    axes[1].set_title("2. ESCÁNER TÁCTICO VISUAL", fontsize=12, fontweight='bold', color='#22d3ee')
                    axes[1].grid(True, linestyle=':', alpha=0.1, color='#475569')
                    axes[1].legend(loc='upper right', fontsize=9)
                    
                    # Panel 3: Zoom
                    axes[2].scatter(vecinas['offset_ra'], vecinas['offset_dec'], 
                                    s=np.maximum(10, (18 - vecinas['Tmag']) * 25), 
                                    color='#64748b', alpha=0.8, edgecolors='#94a3b8')
                    for _, star in vecinas[(vecinas['offset_ra'].abs() < 40) & (vecinas['offset_dec'].abs() < 40)].iterrows():
                        axes[2].text(star['offset_ra']+2, star['offset_dec']+2, f"TIC {star['ID']}", color='#94a3b8', fontsize=8)
                    axes[2].scatter(0, 0, s=300, color='#e11d48', marker='X', edgecolors='white', label='Objetivo')
                    axes[2].set_xlim(-45, 45)
                    axes[2].set_ylim(-45, 45)
                    axes[2].set_title("3. ESCÁNER DE ALTA RESOLUCIÓN (ZOOM)", fontsize=12, fontweight='bold', color='#fb7185')
                    axes[2].grid(True, linestyle='--', alpha=0.3, color='#334155')
                    pixel_box = plt.Rectangle((-10.5, -10.5), 21, 21, fill=False, color='#e11d48', linestyle='--', alpha=0.5, label='Píxel TESS')
                    axes[2].add_patch(pixel_box)
                    axes[2].legend(loc='upper right', fontsize=9)
                    
                    plt.suptitle(f"Auditoría Cartográfica Forense - Centro de Sistemas TIC {tic_input}", fontsize=14, y=0.98, color='#f8fafc', fontweight='bold')
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    # Alerta informativa perimetral
                    if not peligrosas.empty:
                        st.warning(f"⚠️ **ALERTA DE SEGURIDAD ESTELAR:** Se han detectado {len(peligrosas)} estrellas con brillo suficiente en el perímetro inmediato para causar una ilusión de tránsito (#NEB).")
                    else:
                        st.success("🟢 **PERÍMETRO LIMPIO:** No hay estrellas brillantes vecinas en un radio de 120 segundos de arco.")
                        
            except Exception as e:
                st.error(f"❌ Error al interrogar los catálogos estelares de la NASA: {e}")

# --- PESTAÑA 4: ANÁLISIS (Esqueleto para fases posteriores) ---
with tab_analisis:
    st.header("📊 Curva de Luz Avanzada con Filtro Orbital")
    st.info("Módulo fotométrico en desarrollo.")
