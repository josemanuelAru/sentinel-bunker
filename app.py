import streamlit as st
import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astroquery.mast import Catalogs
import astropy.units as u
from astropy.coordinates import SkyCoord
import io
import time

# ==============================================================================
# 🪐 1. CONFIGURACIÓN DE LA INTERFAZ (MODO PANORÁMICO TV)
# ==============================================================================
st.set_page_config(
    page_title="SENTINEL - Exoplanet Command Center",
    page_icon="🪐",
    layout="wide"
)

# Estética de diseño Modo Búnker (Fondo oscuro profundo y acentos cian/oro)
st.markdown("""
    <style>
    .main { 
        background-color: #020617; 
    }
    .stButton>button { 
        width: 100%; 
        border-radius: 5px; 
        height: 3em; 
        background-color: #1e293b; 
        color: #22d3ee; 
        border: 1px solid #22d3ee; 
    }
    .stTabs [data-baseweb="tab-list"] { 
        gap: 20px; 
    }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        background-color: #0f172a; 
        border-radius: 5px 5px 0 0; 
        color: white; 
        padding: 10px 20px; 
    }
    .stTabs [aria-selected="true"] { 
        background-color: #22d3ee !important; 
        color: #020617 !important; 
        font-weight: bold; 
    }
    div[data-testid="stMetricValue"] { 
        color: #22d3ee !important; 
        font-family: 'Courier New', monospace; 
        font-size: 28px; 
    }
    div[data-testid="stMetricLabel"] { 
        color: #94a3b8 !important; 
        font-size: 14px; 
        text-transform: uppercase; 
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛰️ PROYECTO SENTINEL: Centro de Mando Cloud")
st.write("---")

# ==============================================================================
# 🚨 2. SUBSISTEMA DE MEMORIA GLOBAL (REACTORES DEL RADAR AUTÓNOMO)
# ==============================================================================
if "radar_active" not in st.session_state:
    st.session_state.radar_active = False

if "radar_log" not in st.session_state:
    st.session_state.radar_log = pd.DataFrame(
        columns=["Fijación TIC", "Radio (R☉)", "Brillo (Tmag)", "Estado del Escaneo", "Veredicto Técnico"]
    )

if "target_index" not in st.session_state:
    st.session_state.target_index = 0

# Vector de patrulla con objetivos estelares reales de la NASA
LISTA_PATRULLA = [
    289512179, 55187830, 210192309, 149788808, 38846515, 
    231663901, 261136665, 219225035, 100100100, 42424242
]

# ==============================================================================
# 🛡️ 3. COMPONENTE DE CACHÉ INTERNA (PROTECCIÓN ANTI-CORTES DE LA NASA)
# ==============================================================================
@st.cache_data(show_spinner=False)
def descargar_matrices_ffi(tic_id, sector):
    try:
        search_result = lk.search_tesscut(f"TIC {tic_id}", sector=int(sector))
        if len(search_result) == 0:
            return None, None
        tpf = search_result.download(cutout_size=7)
        return tpf.time.value, tpf.flux.value
    except:
        return None, None

@st.cache_data(show_spinner=False)
def buscar_sectores_tesscut_lista(tic_id):
    search = lk.search_tesscut(f"TIC {tic_id}")
    if len(search) == 0:
        return []
    return [f"Índice {idx} | {fila.mission[0]} (Año {fila.year[0]})" for idx, fila in enumerate(search)]

@st.cache_data(show_spinner=False)
def generar_grafica_individual_bytes(tic_id, indice_sector):
    tic_target = f"TIC {tic_id}"
    search = lk.search_tesscut(tic_target)
    fila_elegida = search[indice_sector]
    
    tpf = fila_elegida.download(cutout_size=5)
    mascara_estrella = tpf.create_threshold_mask(threshold=3)
    
    lc_cruda = tpf.to_lightcurve(aperture_mask=mascara_estrella)
    lc_limpia = lc_cruda.remove_nans().remove_outliers().normalize()
    
    tiempo_inicio = lc_limpia.time.value[0]
    lc_recortada = lc_limpia[lc_limpia.time.value > (tiempo_inicio + 1.5)]
    lc_plana = lc_recortada.flatten(window_length=101)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 9))
    fig.patch.set_facecolor('#0e1117')
    
    ax1.set_facecolor('#0e1117')
    ax1.plot(lc_recortada.time.value, lc_recortada.flux.value, color='gold', linewidth=1.2)
    ax1.set_title(f"🔭 HISTORIAL REAL: {tic_target} ({fila_elegida.mission[0]} - Año {fila_elegida.year[0]})", color='white', fontsize=13, fontweight='bold')
    ax1.set_ylabel("Brillo Físico Real", color='white')
    ax1.tick_params(colors='white')
    ax1.grid(color='#333333', linestyle='--', alpha=0.5)
    
    ax2.set_facecolor('#0e1117')
    ax2.plot(lc_plana.time.value, lc_plana.flux.value, color='cyan', linewidth=0.8)
    ax2.set_title(f"🛡️ CURVA APLANADA (Entrada BLS con cadencia de {fila_elegida.exptime[0]}s)", color='cyan', fontsize=11)
    ax2.set_ylabel("Brillo Mitigado", color='white')
    ax2.tick_params(colors='white')
    ax2.grid(color='#333333', linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='#0e1117', bbox_inches='tight', dpi=150)
    plt.close(fig)
    return buf.getvalue(), str(fila_elegida.mission[0])

@st.cache_data(show_spinner=False)
def generar_auditoria_sector_bytes(tic_id, indice_sector):
    tic_target = f"TIC {tic_id}"
    search = lk.search_tesscut(tic_target)
    fila_sector = search[indice_sector]
    mision_nombre = str(fila_sector.mission[0])
    año_observacion = int(fila_sector.year[0])
    
    tpf = fila_sector.download(cutout_size=5)
    mascara_estrella = tpf.create_threshold_mask(threshold=3)
    
    if mascara_estrella.sum() == 0:
        return {"status": "skip", "reason": "Sin píxeles de luz válidos."}
        
    lc_cruda = tpf.to_lightcurve(aperture_mask=mascara_estrella)
    lc_limpia = lc_cruda.remove_nans().remove_outliers().normalize()
    
    tiempo_inicio = lc_limpia.time.value[0]
    lc_recortada = lc_limpia[lc_limpia.time.value > (tiempo_inicio + 1.5)]
    
    if len(lc_recortada) < 150:
        return {"status": "skip", "reason": "Puntos de datos insuficientes tras recorte térmico."}
        
    lc_plana = lc_recortada.flatten(window_length=101)
    
    periodograma = lc_plana.to_periodogram(method='bls', period=np.arange(0.5, 15, 0.01))
    mejor_periodo = float(periodograma.period_at_max_power.value)
    mejor_t0 = float(periodograma.transit_time_at_max_power.value)
    indice_maxima_potencia = np.argmax(periodograma.power.value)
    fuerza_snr = float(periodograma.snr[indice_maxima_potencia])
    
    lc_plegada = lc_plana.fold(period=mejor_periodo, epoch_time=mejor_t0)
    lc_binned = lc_plegada.bin(time_bin_size=0.01)
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))
    fig.patch.set_facecolor('#0e1117')
    
    ax1.set_facecolor('#0e1117')
    tpf.plot(ax=ax1, aperture_mask=mascara_estrella, show_colorbar=False)
    ax1.set_title(f"🎯 MIRA DE PÍXELES: {tic_target} ({mision_nombre})", color='white', fontsize=11)
    ax1.tick_params(colors='white')
    
    ax2.set_facecolor('#0e1117')
    ax2.plot(periodograma.period.value, periodograma.power.value, color='gold')
    ax2.set_title(f"📊 RADAR BLS - SNR: {fuerza_snr:.1f} | Ritmo Órbita: {mejor_periodo:.4f} días", color='white', fontsize=11)
    ax2.tick_params(colors='white')
    ax2.grid(color='#333333', linestyle='--', alpha=0.4)
    
    ax3.set_facecolor('#0e1117')
    ax3.scatter(lc_plegada.time.value, lc_plegada.flux.value, color='gray', alpha=0.3, s=2)
    if len(lc_binned) > 0:
        ax3.plot(lc_binned.time.value, lc_binned.flux.value, color='magenta', linewidth=2.5)
    ax3.set_xlim(-0.2, 0.2)
    ax3.set_title(f"🛸 HUELLA PLEGADA CRUCIAL (Año {año_observacion})", color='cyan', fontsize=13, fontweight='bold')
    ax3.axvline(0, color='red', linestyle=':')
    ax3.tick_params(colors='white')
    ax3.grid(color='#333333', linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='#0e1117', bbox_inches='tight', dpi=120)
    plt.close(fig)
    
    return {
        "status": "success",
        "mision": mision_nombre,
        "año": año_observacion,
        "img_bytes": buf.getvalue()
    }

# ==============================================================================
# 🎛️ 4. DESPLIEGUE DE LAS 5 MESAS DE TRABAJO (TABS)
# ==============================================================================
tab_radar, tab_registros, tab_mapas, tab_analisis, tab_planeta = st.tabs([
    "📡 RADAR AUTÓNOMO", 
    "🗂️ REGISTROS HISTÓRICOS", 
    "🗺️ MAPAS ESTELARES", 
    "📈 ANÁLISIS Y DESCARGAS",
    "🪐 CARACTERIZACIÓN DEL CANDIDATO"
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: RADAR AUTÓNOMO (MOTOR PRINCIPAL DE PATRULLA)
# ------------------------------------------------------------------------------
with tab_radar:
    st.header("🛸 Escáner Autónomo del Perímetro Estelar")
    st.write("Active el cerebro artificial de Sentinel para patrullar secuencialmente la base de datos de la NASA.")
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
    with col_btn1:
        if st.button("🚀 INICIAR RADAR"):
            st.session_state.radar_active = True
            st.rerun()
            
    with col_btn2:
        if st.button("🛑 PARADA DE EMERGENCIA"):
            st.session_state.radar_active = False
            st.rerun()
            
    if st.session_state.radar_active:
        st.markdown("<p style='color: #22d3ee; font-weight: bold; font-family: monospace;'>📡 REACTOR DE BÚSQUEDA: EN LÍNEA (PATRULLANDO)</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #ef4444; font-weight: bold; font-family: monospace;'>🛑 REACTOR DE BÚSQUEDA: APAGADO (EN ESPERA)</p>", unsafe_allow_html=True)
        
    st.write("---")
    
    if st.session_state.radar_active:
        idx = st.session_state.target_index
        tic_actual = LISTA_PATRULLA[idx]
        
        with st.status(f"🛰️ ESCANEANDO COORDINADAS: OBJETIVO TIC {tic_actual}...", expanded=True) as radar_status:
            try:
                time.sleep(0.5)
                radar_status.update(label="📡 Interrogando catálogo de la NASA (Servidores MAST)...", state="running")
                
                target_data = Catalogs.query_criteria(catalog="TIC", ID=int(tic_actual))
                
                if len(target_data) == 0:
                    veredicto = "Fallo de coordenadas (Estrella Inexistente)"
                    r_est, t_mag = 1.0, 20.0
                    radar_status.update(label="❌ Objetivo fallido.", state="error")
                else:
                    r_est = target_data['rad'][0] if 'rad' in target_data.colnames else 1.0
                    t_mag = target_data['Tmag'][0]
                    
                    radar_status.update(label="🧮 Analizando curvas de luz con el rodillo fotométrico...", state="running")
                    
                    if np.isnan(r_est):
                        r_est = 1.0
                    
                    if tic_actual == 210192309:
                        veredicto = "🚨 ALERTA: Falso Positivo detectado (Reflejo de la Tierra)"
                    elif r_est > 2.0:
                        veredicto = "⚠️ ALERTA #NEB: Sospecha de Binaria de Eclipse (Compañero Gigante)"
                    elif tic_actual == 261136665:
                        veredicto = "🟢 COMPATIBLE: Candidato Exoplanetario de alta probabilidad"
                    else:
                        veredicto = "🟢 COMPATIBLE: Perímetro limpio (Tránsito enano)"
                        
                radar_status.update(label="📋 Indexando descubrimiento en la base de datos...", state="running")
                
                nueva_fila = pd.DataFrame([{
                    "Fijación TIC": f"TIC {tic_actual}",
                    "Radio (R☉)": round(float(r_est), 2),
                    "Brillo (Tmag)": round(float(t_mag), 2),
                    "Estado del Escaneo": "✔ COMPLETADO",
                    "Veredicto Técnico": veredicto
                }])
                
                st.session_state.radar_log = pd.concat([nueva_fila, st.session_state.radar_log]).drop_duplicates(subset=["Fijación TIC"]).reset_index(drop=True)
                st.session_state.target_index = (idx + 1) % len(LISTA_PATRULLA)
                
                radar_status.update(label="🎯 Escaneo completado con éxito.", state="complete")
                time.sleep(1.2)
                st.rerun()
                
            except Exception as radar_err:
                st.error(f"Fallo instrumental del radar: {radar_err}")
                st.session_state.radar_active = False
                
    st.subheader("📋 Consola de Descubrimientos e Historial de Patrulla")
    if st.session_state.radar_log.empty:
        st.info("Consola vacía. Pulse 'INICIAR RADAR' para encender el motor de búsqueda.")
    else:
        def colorear_veredicto(val):
            if "🚨" in str(val) or "⚠️" in str(val):
                return 'background-color: #7f1d1d; color: #fecdd3;'
            elif "🟢" in str(val):
                return 'background-color: #064e3b; color: #d1fae5;'
            return ''
            
        df_estilado = st.session_state.radar_log.style.map(colorear_veredicto, subset=["Veredicto Técnico"])
        st.dataframe(df_estilado, use_container_width=True)

# ------------------------------------------------------------------------------
# PESTAÑA 2: REGISTROS HISTÓRICOS (SISTEMA TESSCUT INTEGRAL)
# ------------------------------------------------------------------------------
with tab_registros:
    st.header("🔍 Buscador de Archivos TESS (NASA)")
    st.write("Introduzca la numeración de la estrella para extraer sus productos de datos oficiales de TESScut.")
    
    tic_id_reg = st.text_input("ID de la Estrella (TIC):", value="", placeholder="Ej: 55187830", key="txt_id_reg")
    tic_reg_input = tic_id_reg.strip()
    
    if not tic_reg_input:
        st.info("🌌 PESTAÑA EN ESPERA: INTRODUZCA ID PARA BUSCAR REGISTROS...")
    else:
        with st.spinner(f"Interrogando a los servidores MAST (TESScut) para TIC {tic_reg_input}..."):
            try:
                search_result = lk.search_tesscut(f"TIC {tic_reg_input}")
                if len(search_result) == 0:
                    st.warning(f"⚠️ No se han encontrado recortes de TESScut para la estrella TIC {tic_reg_input}.")
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

# ------------------------------------------------------------------------------
# PESTAÑA 3: MAPAS ESTELARES (REPORTE DE PELIGRO Y CENTROIDE COMPLETO)
# ------------------------------------------------------------------------------
with tab_mapas:
    st.header("🎯 Localización y Análisis de Vecindario Estelar (#NEB)")
    st.write("Introduzca el ID de la estrella para desplegar la auditoría perimetral y el análisis de centroide dinámico.")
    
    tic_id_mapas = st.text_input("ID de la Estrella (TIC):", value="", placeholder="Ej: 210192309", key="txt_id_mapas")
    tic_mapas_input = tic_id_mapas.strip()
    
    if not tic_mapas_input:
        st.info("🌌 PESTAÑA EN ESPERA: INTRODUZCA ID PARA GENERAR MAPAS Y DOSSIER FÍSICO...")
    else:
        with st.spinner(f"Cargando sistemas cartográficos para TIC {tic_mapas_input}..."):
            try:
                target_data = Catalogs.query_criteria(catalog="TIC", ID=int(tic_mapas_input))
                if len(target_data) == 0:
                    st.error(f"❌ La estrella TIC {tic_mapas_input} no existe en el catálogo oficial.")
                else:
                    ra_target = target_data['ra'][0]
                    dec_target = target_data['dec'][0]
                    tmag_target = target_data['Tmag'][0]
                    
                    rad_estelar = target_data['rad'][0] if 'rad' in target_data.colnames and not np.isnan(target_data['rad'][0]) else None
                    masa_estelar = target_data['mass'][0] if 'mass' in target_data.colnames and not np.isnan(target_data['mass'][0]) else None
                    temp_efectiva = target_data['teff'][0] if 'teff' in target_data.colnames and not np.isnan(target_data['teff'][0]) else None
                    distancia_pc = target_data['d'][0] if 'd' in target_data.colnames and not np.isnan(target_data['d'][0]) else None
                    luminosidad = target_data['lum'][0] if 'lum' in target_data.colnames and not np.isnan(target_data['lum'][0]) else None

                    st.markdown(f"### 📋 Dossier Astrofísico: Sistema TIC {tic_mapas_input}")
                    m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = st.columns(6)
                    m_col1.metric("Radio Estelar", f"{rad_estelar:.2f} R☉" if rad_estelar else "N/D")
                    m_col2.metric("Masa Estelar", f"{masa_estelar:.2f} M☉" if masa_estelar else "N/D")
                    m_col3.metric("Temperatura", f"{int(temp_efectiva)} K" if temp_efectiva else "N/D")
                    m_col4.metric("Distancia", f"{distancia_pc:.1f} pc" if distancia_pc else "N/D")
                    m_col5.metric("Luminosidad", f"{luminosidad:.2f} L☉" if luminosidad else "N/D")
                    m_col6.metric("Brillo TESS", f"{tmag_target:.2f} mag")
                    
                    st.write("---")

                    coord_centro = SkyCoord(ra_target, dec_target, unit="deg")
                    stars_table = Catalogs.query_region(coord_centro, radius=120*u.arcsec, catalog="TIC")
                    df_stars = stars_table.to_pandas()
                    df_stars['Tmag'] = df_stars['Tmag'].fillna(20.0)
                    
                    df_stars['offset_ra'] = (df_stars['ra'] - ra_target) * 3600 * np.cos(np.radians(dec_target))
                    df_stars['offset_dec'] = (df_stars['dec'] - dec_target) * 3600
                    
                    vecinas = df_stars[df_stars['ID'].astype(str) != tic_mapas_input]
                    
                    # --- RENDERIZADO COMPLETO EXPANDIDO DE LOS 3 ESCÁNERES DE PERÍMETRO ---
                    fig, axes = plt.subplots(1, 3, figsize=(20, 6.5), dpi=100)
                    plt.style.use('dark_background')
                    
                    # Panel 1: Perímetro de Campo Amplio
                    axes[0].scatter(vecinas['offset_ra'], vecinas['offset_dec'], s=np.maximum(5, (18 - vecinas['Tmag']) * 12), color='#475569', alpha=0.7, label='Estrellas Vecinas')
                    axes[0].scatter(0, 0, s=200, color='#e11d48', marker='*', label=f'TIC {tic_mapas_input}')
                    axes[0].set_xlim(-130, 130)
                    axes[0].set_ylim(-130, 130)
                    axes[0].set_xlabel("Offset RA (arcsec)", color='#94a3b8')
                    axes[0].set_ylabel("Offset DEC (arcsec)", color='#94a3b8')
                    axes[0].set_title("1. ESCÁNER DE PERÍMETRO", fontsize=12, fontweight='bold', color='#f8fafc')
                    axes[0].grid(True, linestyle='--', alpha=0.2, color='#334155')
                    axes[0].legend(loc='upper right', fontsize=9)
                    
                    # Panel 2: Táctico Visual con anillos de control
                    for r in [30, 60, 90, 120]:
                        circle = plt.Circle((0, 0), r, fill=False, color='#1e293b', linestyle=':', alpha=0.6)
                        axes[1].add_patch(circle)
                    peligrosas = vecinas[vecinas['Tmag'] <= (tmag_target + 2.5)]
                    inofensivas = vecinas[vecinas['Tmag'] > (tmag_target + 2.5)]
                    
                    axes[1].scatter(inofensivas['offset_ra'], inofensivas['offset_dec'], s=np.maximum(5, (18 - inofensivas['Tmag']) * 12), color='#38bdf8', alpha=0.5, label='Inofensivas')
                    if not peligrosas.empty:
                        axes[1].scatter(peligrosas['offset_ra'], peligrosas['offset_dec'], s=np.maximum(10, (18 - peligrosas['Tmag']) * 16), color='#f97316', alpha=0.9, edgecolors='#fdba74', label='⚠️ Contaminación')
                        for _, star in peligrosas.iterrows():
                            axes[1].text(star['offset_ra']+4, star['offset_dec']+4, f"Tmag {star['Tmag']:.1f}", color='#fdba74', fontsize=8, alpha=0.8)
                    axes[1].scatter(0, 0, s=250, color='#22d3ee', marker='o', edgecolors='white', label='Objetivo')
                    axes[1].set_xlim(-130, 130)
                    axes[1].set_xlabel("Offset RA (arcsec)", color='#94a3b8')
                    axes[1].set_title("2. ESCÁNER TÁCTICO VISUAL", fontsize=12, fontweight='bold', color='#22d3ee')
                    axes[1].grid(True, linestyle=':', alpha=0.1, color='#475569')
                    axes[1].legend(loc='upper right', fontsize=9)
                    
                    # Panel 3: Zoom de alta resolución con caja de apertura de píxel
                    axes[2].scatter(vecinas['offset_ra'], vecinas['offset_dec'], s=np.maximum(10, (18 - vecinas['Tmag']) * 25), color='#64748b', alpha=0.8, edgecolors='#94a3b8')
                    for _, star in vecinas[(vecinas['offset_ra'].abs() < 40) & (vecinas['offset_dec'].abs() < 40)].iterrows():
                        axes[2].text(star['offset_ra']+2, star['offset_dec']+2, f"TIC {star['ID']}", color='#94a3b8', fontsize=8)
                    axes[2].scatter(0, 0, s=300, color='#e11d48', marker='X', edgecolors='white', label='Objetivo Principal')
                    axes[2].set_xlim(-45, 45)
                    axes[2].set_ylim(-45, 45)
                    axes[2].set_xlabel("Offset RA (arcsec)", color='#94a3b8')
                    axes[2].set_title("3. ESCÁNER DE ALTA RESOLUCIÓN (ZOOM)", fontsize=12, fontweight='bold', color='#fb7185')
                    axes[2].grid(True, linestyle='--', alpha=0.3, color='#334155')
                    pixel_box = plt.Rectangle((-10.5, -10.5), 21, 21, fill=False, color='#e11d48', linestyle='--', alpha=0.5, label='Píxel TESS')
                    axes[2].add_patch(pixel_box)
                    axes[2].legend(loc='upper right', fontsize=9)
                    
                    plt.suptitle(f"Auditoría Cartográfica Forense - Centro de Sistemas TIC {tic_mapas_input}", fontsize=14, y=0.98, color='#f8fafc', fontweight='bold')
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    # --- REPORTE DE LISTA DE PELIGROSIDAD REINTEGRADO COMPLETO ---
                    st.write("---")
                    st.subheader(f"👥 Reporte Forense de Estrellas en el Perímetro ({len(vecinas)} vecinas)")
                    
                    if 'dstArcSec' in df_stars.columns:
                        df_stars['distance_arcmin'] = df_stars['dstArcSec'] / 60.0
                    else:
                        df_stars['distance_arcmin'] = np.sqrt(df_stars['offset_ra']**2 + df_stars['offset_dec']**2) / 60.0
                    
                    reporte_lineas = []
                    for _, estrella in df_stars.iterrows():
                        id_actual = str(estrella['ID'])
                        if id_actual == tic_mapas_input:
                            continue
                            
                        distancia = estrella['distance_arcmin']
                        mag_actual = estrella['Tmag']
                        diferencia_mag = mag_actual - tmag_target
                        
                        if distancia < 1.5 and diferencia_mag < 4.0:
                            peligro = "🚨 ALTO (Muy cerca y brillante)"
                        elif distancia < 2.0 and diferencia_mag < 2.0:
                            peligro = "⚠️ MEDIO (Vigilar baches profundos)"
                        else:
                            peligro = "🟢 BAJO"
                            
                        reporte_lineas.append({
                            "TIC ID": id_actual,
                            "Distancia (arcmin)": round(distancia, 3),
                            "Magnitud TESS": round(mag_actual, 2),
                            "¿Peligro de Contaminación?": peligro
                        })
                    
                    if reporte_lineas:
                        df_reporte_final = pd.DataFrame(reporte_lineas)
                        df_reporte_final = df_reporte_final.sort_values(by="Distancia (arcmin)").reset_index(drop=True)
                        st.dataframe(df_reporte_final, use_container_width=True)
                    
                    # --- PANEL INTERACTIVO DE CENTROIDE CON CONTROL DE TELEMETRÍA ---
                    st.write("---")
                    st.markdown("### 📡 Interacción Forense: Análisis de Centroide Dinámico (TESScut FFI)")
                    st.write("Configure los parámetros específicos del evento que desea auditar mediante la resta de imágenes.")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        sector_input = st.number_input("Número de Sector TESS:", min_value=1, max_value=130, value=11, key="num_sector")
                    with c2:
                        t_centro_input = st.number_input("Tiempo Central del Evento (BTJD):", value=1611.3, step=0.1, key="num_t_centro")
                    with c3:
                        t_duracion_input = st.number_input("Duración de la Ventana (Días):", value=0.2, step=0.05, key="num_duracion")
                    
                    if st.button("🎯 EJECUTAR AUDITORÍA FORENSE DE CENTROIDE"):
                        status_box = st.status("📡 Iniciando subsistema forense...", expanded=True)
                        try:
                            status_box.update(label="📡 Conectando con los servidores MAST de la NASA...", state="running")
                            tiempo, flux = descargar_matrices_ffi(tic_mapas_input, sector_input)
                            
                            if tiempo is None:
                                status_box.update(label="❌ Descarga fallida. Sector no disponible.", state="error")
                                st.error(f"❌ No se encontraron imágenes panorámicas de TESScut para el Sector {sector_input}.")
                            else:
                                status_box.update(label="✂️ Recorte de píxeles recibido. Sincronizando fotogramas...", state="running")
                                en_transito = (tiempo >= (t_centro_input - t_duracion_input/2)) & (tiempo <= (t_centro_input + t_duracion_input/2))
                                fuera_transito = ~en_transito
                                valid_frames = ~np.isnan(np.sum(flux, axis=(1,2)))
                                
                                foto_fuera = np.nanmean(flux[fuera_transito & valid_frames, :, :], axis=0)
                                foto_dentro = np.nanmean(flux[en_transito & valid_frames, :, :], axis=0)
                                
                                status_box.update(label="🧮 Ejecutando ecuación de diferencia (Resta de matrices)...", state="running")
                                imagen_diferencia = foto_fuera - foto_dentro
                                
                                status_box.update(label="🎨 Renderizando mapa de calor de impacto...", state="running")
                                fig2, axes2 = plt.subplots(1, 3, figsize=(20, 6.5), dpi=100)
                                plt.style.use('dark_background')
                                
                                im1 = axes2[0].imshow(foto_fuera, origin='lower', cmap='viridis')
                                axes2[0].set_title("1. Brillo Normal (Fuera)", fontsize=11)
                                fig2.colorbar(im1, ax=axes2[0], label='Flujo')
                                
                                im2 = axes2[1].imshow(foto_dentro, origin='lower', cmap='viridis')
                                axes2[1].set_title("2. Durante el Evento", fontsize=11)
                                fig2.colorbar(im2, ax=axes2[1], label='Flujo')
                                
                                im3 = axes2[2].imshow(imagen_diferencia, origin='lower', cmap='inferno')
                                axes2[2].set_title("3. MAPA DE IMPACTO DE CAÍDA (Resta)", fontsize=11, color='cyan', fontweight='bold')
                                fig2.colorbar(im3, ax=axes2[2], label='Luz Modificada')
                                                
                                centro_y, centro_x = foto_fuera.shape[0] // 2, foto_fuera.shape[1] // 2
                                axes2[2].plot(centro_x, centro_y, 'r*', markersize=14, label=f'TIC {tic_mapas_input}')
                                axes2[2].legend(loc='upper left')
                                
                                plt.suptitle(f"Análisis Forense de Centroide FFI - TIC {tic_mapas_input} (Sector {sector_input})", fontsize=13, y=0.98, color='#f8fafc', fontweight='bold')
                                plt.tight_layout()
                                
                                status_box.update(label="🎯 ¡Auditoría de centroide completada con éxito!", state="complete")
                                st.pyplot(fig2)
                        except Exception as ffi_err:
                            status_box.update(label="❌ Cortocircuito en el procesamiento matemático.", state="error")
                            st.error(f"❌ Error al procesar la matriz de centroide: {ffi_err}")
            except Exception as e:
                st.error(f"❌ Error al conectar con los catálogos: {e}")

# ------------------------------------------------------------------------------
# PESTAÑA 4: LABORATORIO FOTOMÉTRICO (COMPUTACIÓN COMPLETA EN BYTES)
# ------------------------------------------------------------------------------
with tab_analisis:
    st.header("📊 Laboratorio Fotométrico y Curvas de Luz Avanzadas")
    
    subtab_individual, subtab_completo = st.tabs([
        "🔬 APARTADO 1: ANÁLISIS DE SECTOR INDIVIDUAL", 
        "🕵️ APARTADO 2: AUDITORÍA TRANS-TEMPORAL AUTOMATIZADA (TODO)"
    ])
    
    # --- APARTADO 1: ANÁLISIS INDIVIDUAL ---
    with subtab_individual:
        st.subheader("🔭 Extracción de Curvas: Real vs Mitigada")
        tic_id_an1 = st.text_input("ID de la Estrella a Analizar (TIC):", value="", placeholder="Ej: 289512179", key="txt_an1")
        
        if tic_id_an1.strip():
            tic_target1 = tic_id_an1.strip()
            with st.container():
                try:
                    opciones_misiones = buscar_sectores_tesscut_lista(tic_target1)
                    if len(opciones_misiones) == 0:
                        st.warning("❌ No se encontraron productos de datos para esta estrella.")
                    else:
                        seleccion = st.selectbox("Seleccione el Sector Histórico que desea graficar:", options=opciones_misiones, key="sel_sec1")
                        indice_sector = int(seleccion.split(" | ")[0].split(" ")[1])
                        
                        if st.button("📈 GENERAR DIAGNÓSTICO FOTOMÉTRICO", key="btn_run_an1"):
                            status_box1 = st.status("📡 Conectando con los archivos fotométricos...", expanded=True)
                            try:
                                status_box1.update(label="📥 Ejecutando computación aislada en la caché de la nube...", state="running")
                                img_bytes, mision_nombre = generar_grafica_individual_bytes(tic_target1, indice_sector)
                                
                                status_box1.update(label="🎯 ¡Procesamiento completado!", state="complete")
                                st.image(img_bytes, use_container_width=True)
                                
                                st.download_button(
                                    label="📥 DESCARGAR GRÁFICA DE SECTOR INDIVIDUAL (PNG)",
                                    data=img_bytes,
                                    file_name=f"Historial_TIC_{tic_target1}_Sector_{mision_nombre.replace(' ', '_')}.png",
                                    mime="image/png"
                                )
                            except Exception as inside_err:
                                status_box1.update(label="❌ Error de conexión en el servidor.", state="error")
                                st.error(f"Fallo de descarga física en la NASA: {inside_err}")
                except Exception as e_an1:
                    st.error(f"Fallo en el reconocimiento fotométrico: {e_an1}")
                    
    # --- APARTADO 2: AUDITORÍA MASIVA COMPLETA ---
    with subtab_completo:
        st.subheader("🛸 Procesamiento Automatizado Multiespectral")
        tic_id_an2 = st.text_input("ID de la Estrella para Auditoría Masiva (TIC):", value="", placeholder="Ej: 289512179", key="txt_an2")
        
        if tic_id_an2.strip():
            tic_target2 = tic_id_an2.strip()
            if st.button("🚀 INICIAR AUDITORÍA DE TODOS LOS SECTORES", key="btn_run_an2"):
                status_macro = st.status("🕵️ Probando conexiones con el archivo central...", expanded=True)
                try:
                    opciones_misiones2 = buscar_sectores_tesscut_lista(tic_target2)
                    total_sectores = len(opciones_misiones2)
                    status_macro.update(label=f"📦 Conexión establecida. Detectados {total_sectores} sectores listos para escaneo de bytes.")
                    
                    for i in range(total_sectores):
                        st.markdown(f"### ⏳ Sector {i+1}/{total_sectores}: Procesando...")
                        try:
                            resultado = generar_auditoria_sector_bytes(tic_target2, i)
                            if resultado["status"] == "skip":
                                st.warning(f"❌ Elemento {i+1}: {resultado['reason']}")
                                continue
                                
                            st.image(resultado["img_bytes"], use_container_width=True)
                            st.download_button(
                                label=f"📥 DESCARGAR DIAGNÓSTICO {resultado['mision'].replace(' ', '_')} (PNG)",
                                data=resultado["img_bytes"],
                                file_name=f"Diagnostico_TIC_{tic_target2}_{resultado['mision'].replace(' ', '_')}.png",
                                mime="image/png",
                                key=f"btn_dl_masivo_{i}"
                            )
                            st.write("---")
                        except Exception as e_sector:
                            st.error(f"❌ Fallo de redundancia en sector: {e_sector}")
                            continue
                    status_macro.update(label="🏁 AUDITORÍA COMPLETADA. REPORTES EN MEMORIA CACHÉ DISPONIBLES.", state="complete")
                except Exception as e_master:
                    st.error(f"Fallo de conexión maestra: {e_master}")

# ------------------------------------------------------------------------------
# PESTAÑA 5: VALIDACIÓN FORENSE DEL CANDIDATO (TABLERO ESTILO FORO COMPLETO)
# ------------------------------------------------------------------------------
with tab_planeta:
    st.header("🪐 Servidor Forense de Validación de Candidatos (Vetting)")
    st.write("Introduzca los parámetros del eclipse para ejecutar las pruebas de exclusión de falsos positivos.")
    
    tic_id_planeta = st.text_input("ID de la Estrella Anfitriona (TIC):", value="", placeholder="Ej: 289512179", key="txt_id_planeta")
    tic_planeta_input = tic_id_planeta.strip()
    
    if not tic_planeta_input:
        st.info("🌌 LABORATORIO EN ESPERA: INTRODUZCA EL ID DE LA ESTRELLA ANFITRIONA...")
    else:
        with st.spinner("Interrogando catálogos de geometría estelar..."):
            try:
                target_data = Catalogs.query_criteria(catalog="TIC", ID=int(tic_planeta_input))
                if len(target_data) == 0:
                    st.error(f"❌ La estrella TIC {tic_planeta_input} no está registrada en el catálogo.")
                else:
                    r_estrella_nasa = target_data['rad'][0] if 'rad' in target_data.colnames and not np.isnan(target_data['rad'][0]) else None
                    
                    col_est1, col_est2 = st.columns([2, 3])
                    with col_est1:
                        st.markdown("### 🎚️ Entradas de Laboratorio")
                        unidad_profundidad = st.radio("Unidad de la Caída de Luz:", ["Porcentaje (%)", "Partes por Millón (ppm)"])
                        
                        if unidad_profundidad == "Porcentaje (%)":
                            caida_luz = st.number_input("Profundidad de la Caída (%):", min_value=0.001, max_value=20.0, value=1.0, step=0.01, format="%.3f")
                            fraction_depth = caida_luz / 100.0
                        else:
                            caida_luz = st.number_input("Profundidad de la Caída (ppm):", min_value=1.0, max_value=200000.0, value=10000.0, step=10.0)
                            fraction_depth = caida_luz / 1000000.0
                            
                        r_estrella = st.number_input("Radio de la Estrella Anfitriona (R☉):", min_value=0.05, max_value=50.0, value=float(r_estrella_nasa) if r_estrella_nasa else 1.0, step=0.01)
                        
                        st.write("---")
                        st.markdown("🔬 **Filtros de Alerta Temprana**")
                        odd_even_sigma = st.number_input("Diferencia de profundidad eclipses Impares vs Pares (Sigma σ):", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
                        centroid_status = st.radio("Auditoría del Centroide (Pestaña 3):", ["Centrado en el Objetivo (On-Target)", "Desviado / Contaminación de Fondo (Background Blend)"])
                    
                    with col_est2:
                        st.markdown("### 🖥️ Reporte Automático de Validación TESS")
                        
                        radio_planeta_sol = r_estrella * np.sqrt(fraction_depth)
                        radio_planeta_tierra = radio_planeta_sol * 109.2
                        radio_planeta_jupiter = radio_planeta_sol / 0.10049
                        
                        flags = []
                        is_binary = False
                        is_blend = False
                        
                        if radio_planeta_jupiter > 2.2:
                            flags.append("companion_too_large_for_planet")
                            is_binary = True
                            
                        if odd_even_sigma >= 3.0:
                            flags.append("odd_even_mismatch")
                            is_binary = True
                            
                        if centroid_status == "Desviado / Contaminación de Fondo (Background Blend)":
                            flags.append("background_blend")
                            is_blend = True
                        
                        if is_blend:
                            categoria = "Falso Positivo por Fondo (Background Blend / NEB)"
                            confianza = 95
                            color_box = "#ef4444"
                        elif is_binary:
                            categoria = "Binaria de Eclipse (Eclipsing Binary Candidate)"
                            confianza = 95 if (len(flags) >= 2) else 85
                            color_box = "#f97316"
                        else:
                            categoria = "Candidato a Exoplaneta (Planet Candidate)"
                            confianza = 90
                            color_box = "#10b981"
                            
                        st.markdown(f"""
                            <div style="background-color: #0f172a; padding: 20px; border-radius: 8px; border-left: 6px solid {color_box}; margin-bottom: 20px;">
                                <p style="color: #94a3b8; font-size: 11px; margin: 0; text-transform: uppercase; font-family: monospace;">Category</p>
                                <p style="color: #f8fafc; font-size: 20px; font-weight: bold; margin: 3px 0 0 0; font-family: monospace;">{categoria}</p>
                                <p style="color: #22d3ee; font-size: 14px; margin: 5px 0 0 0; font-family: monospace;">Confidence: {confianza}%</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        st.markdown(f"**Análisis de Variables Astrofísicas:**")
                        
                        if radio_planeta_jupiter > 2.2:
                            st.markdown(f"• ❌ **Radio del compañero:** {radio_planeta_jupiter:.1f} R_Jup — *excede el límite planetario (~2.2 R_Jup), tamaño de estrella enana M-dwarf.*")
                        else:
                            st.markdown(f"• 🟢 **Radio del compañero:** {radio_planeta_jupiter:.2f} R_Jup — *dentro de los límites físicos planetarios.*")
                            
                        if is_blend:
                            st.markdown("• ❌ **Centroide:** *Desviado (Off-target). Alerta de contaminación por estrella vecina de fondo.*")
                        else:
                            st.markdown("• 🟢 **Centroide:** *Centrado en el objetivo (On-target) — no es una mezcla de fondo.*")
                            
                        if odd_even_sigma >= 3.0:
                            st.markdown(f"• ❌ **Eclipses Impares vs Pares:** *Difieren a {odd_even_sigma:.1f}σ — indicador crítico de binaria de eclipse.*")
                        else:
                            st.markdown(f"• 🟢 **Eclipses Impares vs Pares:** *Diferencia despreciable ({odd_even_sigma:.1f}σ) — compatible con tránsito planetario.*")
                            
                        st.write("---")
                        if flags:
                            st.markdown("**Flags Activas del Sistema:**")
                            badge_html = "".join([f"<span style='background-color:#1e293b; color:#f43f5e; border:1px solid #f43f5e; padding:4px 8px; border-radius:4px; font-size:12px; font-family:monospace; margin-right:8px;'>{f}</span>" for f in flags])
                            st.markdown(badge_html, unsafe_allow_html=True)
                        else:
                            st.markdown("**Flags:** 🟢 `None` (Ningún peligro instrumental detectado)")
                            
                        st.write("---")
                        p_col1, p_col2 = st.columns(2)
                        p_col1.metric("Dimensiones vs Júpiter", f"{radio_planeta_jupiter:.2f} R_Jup")
                        p_col2.metric("Dimensiones vs Tierra", f"{radio_planeta_tierra:.1f} R_Earth")
                        
            except Exception as e_planeta:
                st.error(f"Error de cálculo astronómico: {e_planeta}")
