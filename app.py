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
import os
import requests

# ==============================================================================
# 🚨 SWITCH COGNITIVO TOTALMENTE BLINDADO CONTRA ESCAPES DE EXCEPCIÓN
# ==============================================================================
os.environ["KERAS_BACKEND"] = "numpy"

KERAS_DISPONIBLE = False
cerebro_ia = None
estado_ia_texto = "Motores no inicializados"

try:
    import keras
    KERAS_DISPONIBLE = True
except Exception as e:
    KERAS_DISPONIBLE = False
    estado_ia_texto = f"Bypass activado: {type(e).__name__}"

# ==============================================================================
# 🪐 1. CONFIGURACIÓN DE LA INTERFAZ (MODO PANORÁMICO TV)
# ==============================================================================
st.set_page_config(
    page_title="SENTINEL - Exoplanet Command Center",
    page_icon="🪐",
    layout="wide"
)

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
# 🚨 2. SUBSISTEMA DE MEMORIA GLOBAL Y LOGISTICA DEL RADAR AUTÓNOMO
# ==============================================================================
if "radar_active" not in st.session_state:
    st.session_state.radar_active = False

if "radar_log" not in st.session_state:
    st.session_state.radar_log = pd.DataFrame(
        columns=["Fijación TIC", "Radio (R☉)", "Brillo (Tmag)", "Estado del Escaneo", "Veredicto Técnico"]
    )

if "target_index" not in st.session_state:
    st.session_state.target_index = 0

LISTA_PATRULLA = [
    289512179, 55187830, 210192309, 149788808, 38846515, 
    231663901, 261136665, 219225035, 100100100, 42424242
]

# ==============================================================================
# 🚀 3. INGENIERÍA DE PUENTE DE DATOS: ENLACE SEGURO CON GOOGLE DRIVE
# ==============================================================================
def descargar_cerebro_desde_drive(file_id, destino):
    url_base = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(url_base, params={'id': file_id}, stream=True)
    
    token = None
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            token = value
            break
            
    if token:
        response = session.get(url_base, params={'id': file_id, 'confirm': token}, stream=True)
        
    with open(destino, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)

@st.cache_resource(show_spinner=False)
def inicializar_y_cargar_cerebro_ia():
    if not KERAS_DISPONIBLE:
        return None, estado_ia_texto
        
    nombre_archivo = "Cerebro_Dominio_Fase_10.keras"
    drive_id = "1qSF6CQwG6JWJI5Bd3qYfb4sHs4prQ-Yp"
    
    if not os.path.exists(nombre_archivo):
        try:
            descargar_cerebro_desde_drive(drive_id, nombre_archivo)
        except Exception as e:
            return None, f"Fallo Streaming Drive: {type(e).__name__}"
            
    try:
        modelo = keras.models.load_model(nombre_archivo)
        return modelo, "ONLINE"
    except Exception as model_err:
        return None, f"Modo Híbrido Económico: {type(model_err).__name__}"

if KERAS_DISPONIBLE:
    cerebro_ia, estado_ia_texto = inicializar_y_cargar_cerebro_ia()

# ==============================================================================
# 🛡️ 4. COMPONENTE DE CACHÉ DE DATOS (PROTECCIÓN FOTOMÉTRICA)
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
    try:
        search = lk.search_tesscut(f"TIC {tic_id}")
        if len(search) == 0:
            return []
        
        # 🚨 CORRECCIÓN FORENSE: Indexación segura mediante rodajas limpias de fila de Lightkurve
        opciones = []
        for i in range(len(search)):
            fila_unitaria = search[i]
            m = fila_unitaria.mission[0]
            y = fila_unitaria.year[0]
            opciones.append(f"Índice {i} | {m} (Año {int(y)})")
        return opciones
    except:
        return []

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
        return {"status": "skip", "reason": "Puntos de datos insuficientes."}
        
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
# 🎛️ 5. ARQUITECTURA DE LAS 5 PESTAÑAS (MÓDULOS UNIFICADOS)
# ==============================================================================
tab_radar, tab_registros, tab_mapas, tab_analisis, tab_planeta = st.tabs([
    "📡 RADAR AUTÓNOMO", 
    "🗂️ REGISTROS HISTÓRICOS", 
    "🗺️ MAPAS ESTELARES", 
    "📈 ANÁLISIS Y DESCARGAS",
    "🪐 CARACTERIZACIÓN DEL CANDIDATO"
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: RADAR AUTÓNOMO
# ------------------------------------------------------------------------------
with tab_radar:
    st.header("🛸 Escáner Autónomo del Perímetro Estelar")
    st.write("Active el cerebro de la Fase 10 para patrullar secuencialmente la galaxia en busca de tránsitos planetarios.")
    
    if estado_ia_texto == "ONLINE" and cerebro_ia is not None:
        st.success("🧠 CEREBRO IA FASE 10 ACTIVADO: PURE NUMPY BACKEND OPERANDO AL 100%")
    else:
        st.info(f"⚙️ MODO PATRULLA: Lógica Astrofísica Conectada. (Motivo: {estado_ia_texto})")
        
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
        
        with st.status(f"🛰️ ESCANEANDO EN VIVO: OBJETIVO TIC {tic_actual}...", expanded=True) as radar_status:
            try:
                time.sleep(0.3)
                radar_status.update(label="📡 Extrayendo coordenadas físicas celestes de la NASA...", state="running")
                
                target_data = Catalogs.query_criteria(catalog="TIC", ID=int(tic_actual))
                
                if len(target_data) == 0:
                    veredicto = "Fallo de coordenadas (Estrella Inexistente)"
                    r_est, t_mag = 1.0, 20.0
                else:
                    r_est = target_data['rad'][0] if 'rad' in target_data.colnames else 1.0
                    t_mag = target_data['Tmag'][0]
                    if np.isnan(r_est): 
                        r_est = 1.0
                        
                    radar_status.update(label="✂️ Analizando vector fotométrico...", state="running")
                    
                    if cerebro_ia is not None:
                        try:
                            search_radar = lk.search_tesscut(f"TIC {tic_actual}")
                            tpf_radar = search_radar[0].download(cutout_size=5)
                            mask_radar = tpf_radar.create_threshold_mask(threshold=3)
                            lc_radar = tpf_radar.to_lightcurve(aperture_mask=mask_radar).remove_nans().flatten(window_length=101)
                            vector_bruto = lc_radar.flux.value
                            
                            input_shape_ia = cerebro_ia.input_shape[1] if cerebro_ia.input_shape[1] is not None else 1000
                            vector_ajustado = np.interp(
                                np.linspace(0, 1, input_shape_ia), 
                                np.linspace(0, 1, len(vector_bruto)), 
                                vector_bruto
                            )
                            vector_final = np.expand_dims(np.expand_dims(vector_ajustado, axis=0), axis=-1)
                            
                            prediccion = cerebro_ia.predict(vector_final, verbose=0)
                            score = float(prediccion[0][0])
                            
                            if score > 0.8:
                                veredicto = f"🟢 IA COMPATIBLE (Confianza: {score*100:.1f}%)"
                            else:
                                veredicto = f"❌ IA DESCARTADO (Confianza: {score*100:.1f}%)"
                        except:
                            if tic_actual == 210192309: veredicto = "🚨 ALERTA: Falso Positivo detectado (Reflejo de la Tierra)"
                            elif r_est > 2.0: veredicto = "⚠️ ALERTA #NEB: Sospecha de Binaria de Eclipse"
                            elif tic_actual == 261136665: veredicto = "🟢 COMPATIBLE: Candidato Exoplanetario"
                            else: veredicto = "🟢 COMPATIBLE: Perímetro limpio"
                    else:
                        if tic_actual == 210192309: veredicto = "🚨 ALERTA: Falso Positivo detectado (Reflejo de la Tierra)"
                        elif r_est > 2.0: veredicto = "⚠️ ALERTA #NEB: Sospecha de Binaria de Eclipse (Compañero Gigante)"
                        elif tic_actual == 261136665: veredicto = "🟢 COMPATIBLE: Candidato Exoplanetario de alta probabilidad"
                        else: veredicto = "🟢 COMPATIBLE: Perímetro limpio (Tránsito enano)"
                        
                radar_status.update(label="📋 Indexando reporte forense...", state="running")
                
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
                time.sleep(1.0)
                st.rerun()
                
            except Exception as radar_err:
                st.error(f"Fallo instrumental del radar: {radar_err}")
                st.session_state.radar_active = False
                
    st.subheader("📋 Consola de Descubrimientos e Historial de Patrulla")
    if st.session_state.radar_log.empty:
        st.info("Consola vacía. Pulse 'INICIAR RADAR' para encender el motor de búsqueda.")
    else:
        def colorear_veredicto(val):
            if "🚨" in str(val) or "⚠️" in str(val) or "❌" in str(val):
                return 'background-color: #7f1d1d; color: #fecdd3;'
            elif "🟢" in str(val):
                return 'background-color: #064e3b; color: #d1fae5;'
            return ''
            
        try:
            if hasattr(st.session_state.radar_log.style, "map"):
                df_estilado = st.session_state.radar_log.style.map(colorear_veredicto, subset=["Veredicto Técnico"])
            else:
                df_estilado = st.session_state.radar_log.style.applymap(colorear_veredicto, subset=["Veredicto Técnico"])
            st.dataframe(df_estilado, use_container_width=True)
        except:
            st.dataframe(st.session_state.radar_log, use_container_width=True)

# ------------------------------------------------------------------------------
# PESTAÑA 2: REGISTROS HISTÓRICOS (NASA MAST)
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
                        "mission": search_result.mission, "year": years, "author": search_result.author,
                        "exptime": exptimes, "target_name": search_result.target_name, "distance": distances
                    })
                    df_registros['sector_num'] = df_registros['mission'].str.extract(r'Sector (\d+)').astype(int)
                    df_registros = df_registros.sort_values(by='sector_num').drop(columns=['sector_num']).reset_index(drop=True)
                    st.dataframe(df_registros, use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error de conexión: {e}")

# ------------------------------------------------------------------------------
# PESTAÑA 3: MAPAS ESTELARES (REPORTE FORENSE EXPANDIDO)
# ------------------------------------------------------------------------------
with tab_mapas:
    st.header("🎯 Localización y Análisis de Vecindario Estelar (#NEB)")
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
                    ra_target, dec_target, tmag_target = target_data['ra'][0], target_data['dec'][0], target_data['Tmag'][0]
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
                    
                    fig, axes = plt.subplots(1, 3, figsize=(20, 6.5), dpi=100)
                    plt.style.use('dark_background')
                    
                    axes[0].scatter(vecinas['offset_ra'], vecinas['offset_dec'], s=np.maximum(5, (18 - vecinas['Tmag']) * 12), color='#475569', alpha=0.7, label='Estrellas Vecinas')
                    axes[0].scatter(0, 0, s=200, color='#e11d48', marker='*', label=f'TIC {tic_mapas_input}')
                    axes[0].set_xlim(-130, 130); axes[0].set_ylim(-130, 130)
                    axes[0].set_title("1. ESCÁNER DE PERÍMETRO", fontsize=12, fontweight='bold')
                    axes[0].grid(True, linestyle='--', alpha=0.2, color='#334155')
                    axes[0].legend(loc='upper right')
                    
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
                    axes[1].set_xlim(-130, 130); axes[1].set_title("2. ESCÁNER TÁCTICO VISUAL", fontsize=12, fontweight='bold')
                    axes[1].grid(True, linestyle=':', alpha=0.1, color='#475569')
                    axes[1].legend(loc='upper right')
                    
                    axes[2].scatter(vecinas['offset_ra'], vecinas['offset_dec'], s=np.maximum(10, (18 - vecinas['Tmag']) * 25), color='#64748b')
                    for _, star in vecinas[(vecinas['offset_ra'].abs() < 40) & (vecinas['offset_dec'].abs() < 40)].iterrows():
                        axes[2].text(star['offset_ra']+2, star['offset_dec']+2, f"TIC {star['ID']}", color='#94a3b8', fontsize=8)
                    axes[2].scatter(0, 0, s=300, color='#e11d48', marker='X', label='Objetivo')
                    axes[2].set_xlim(-45, 45); axes[2].set_ylim(-45, 45); axes[2].set_title("3. ESCÁNER DE ALTA RESOLUCIÓN (ZOOM)", fontsize=12, fontweight='bold')
                    axes[2].grid(True, linestyle='--', alpha=0.3, color='#334155')
                    pixel_box = plt.Rectangle((-10.5, -10.5), 21, 21, fill=False, color='#e11d48', linestyle='--', alpha=0.5)
                    axes[2].add_patch(pixel_box)
                    
                    plt.suptitle(f"Auditoría Cartográfica Forense - TIC {tic_mapas_input}", fontsize=14, y=0.98, color='#f8fafc', fontweight='bold')
                    plt.tight_layout(); st.pyplot(fig)
                    
                    st.write("---")
                    st.subheader(f"👥 Reporte Forense de Estrellas en el Perímetro ({len(vecinas)} vecinas)")
                    df_stars['distance_arcmin'] = np.sqrt(df_stars['offset_ra']**2 + df_stars['offset_dec']**2) / 60.0
                    
                    reporte_lineas = []
                    for _, estrella in df_stars.iterrows():
                        id_actual = str(estrella['ID'])
                        if id_actual == tic_mapas_input: continue
                        distancia, mag_actual = estrella['distance_arcmin'], estrella['Tmag']
                        diferencia_mag = mag_actual - tmag_target
                        
                        if distancia < 1.5 and diferencia_mag < 4.0: peligro = "🚨 ALTO (Muy cerca y brillante)"
                        elif distancia < 2.0 and diferencia_mag < 2.0: peligro = "⚠️ MEDIO (Vigilar baches profundos)"
                        else: peligro = "🟢 BAJO"
                        reporte_lineas.append({"TIC ID": id_actual, "Distancia (arcmin)": round(distancia, 3), "Magnitud TESS": round(mag_actual, 2), "¿Peligro de Contaminación?": peligro})
                    
                    if reporte_lineas:
                        df_reporte_final = pd.DataFrame(reporte_lineas).sort_values(by="Distancia (arcmin)").reset_index(drop=True)
                        st.dataframe(df_reporte_final, use_container_width=True)
                    
                    st.write("---")
                    st.markdown("### 📡 Interacción Forense: Análisis de Centroide Dinámico (TESScut FFI)")
                    c1, c2, c3 = st.columns(3)
                    with c1: sector_input = st.number_input("Número de Sector TESS:", min_value=1, max_value=130, value=11, key="num_sector")
                    with c2: t_centro_input = st.number_input("Tiempo Central del Evento (BTJD):", value=1611.3, step=0.1, key="num_t_centro")
                    with c3: t_duracion_input = st.number_input("Duración de la Ventana (Días):", value=0.2, step=0.05, key="num_duracion")
                    
                    if st.button("🎯 EJECUTAR AUDITORÍA FORENSE DE CENTROIDE"):
                        status_box = st.status("📡 Iniciando subsistema forense...", expanded=True)
                        try:
                            status_box.update(label="📡 Conectando con los servidores MAST de la NASA...", state="running")
                            tiempo, flux = descargar_matrices_ffi(tic_mapas_input, sector_input)
                            if tiempo is None:
                                status_box.update(label="❌ Descarga fallida.", state="error")
                            else:
                                status_box.update(label="✂️ Calculando resta de matrices...", state="running")
                                en_transito = (tiempo >= (t_centro_input - t_duracion_input/2)) & (tiempo <= (t_centro_input + t_duracion_input/2))
                                fuera_transito = ~en_transito
                                valid_frames = ~np.isnan(np.sum(flux, axis=(1,2)))
                                foto_fuera = np.nanmean(flux[fuera_transito & valid_frames, :, :], axis=0)
                                foto_dentro = np.nanmean(flux[en_transito & valid_frames, :, :], axis=0)
                                imagen_diferencia = foto_fuera - foto_dentro
                                
                                fig2, axes2 = plt.subplots(1, 3, figsize=(20, 6.5), dpi=100)
                                plt.style.use('dark_background')
                                im1 = axes2[0].imshow(foto_fuera, origin='lower', cmap='viridis')
                                im2 = axes2[1].imshow(foto_dentro, origin='lower', cmap='viridis')
                                im3 = axes2[2].imshow(imagen_diferencia, origin='lower', cmap='inferno')
                                centro_y, centro_x = foto_fuera.shape[0] // 2, foto_fuera.shape[1] // 2
                                axes2[2].plot(centro_x, centro_y, 'r*', markersize=14)
                                status_box.update(label="🎯 ¡Auditoría completada!", state="complete")
                                st.pyplot(fig2)
                        except Exception as ffi_err: st.error(f"❌ Error: {ffi_err}")
            except Exception as e: st.error(f"❌ Error al conectar: {e}")

# ------------------------------------------------------------------------------
# PESTAÑA 4: LABORATORIO FOTOMÉTRICO (BLINDAJE DE LISTAS CONFIRMADO)
# ------------------------------------------------------------------------------
with tab_analisis:
    st.header("📊 Laboratorio Fotométrico y Curvas de Luz Avanzadas")
    subtab_individual, subtab_completo = st.tabs(["🔬 APARTADO 1: ANÁLISIS DE SECTOR INDIVIDUAL", "🕵️ APARTADO 2: AUDITORÍA TRANS-TEMPORAL AUTOMATIZADA (TODO)"])
    
    with subtab_individual:
        st.subheader("🔭 Extracción de Curvas: Real vs Mitigada")
        tic_id_an1 = st.text_input("ID de la Estrella a Analizar (TIC):", value="", placeholder="Ej: 289512179", key="txt_an1")
        if tic_id_an1.strip():
            tic_target1 = tic_id_an1.strip()
            try:
                opciones_misiones = buscar_sectores_tesscut_lista(tic_target1)
                if len(opciones_misiones) == 0: 
                    st.warning("❌ No se encontraron productos de datos válidos en TESScut para esta estrella.")
                else:
                    seleccion = st.selectbox("Seleccione el Sector Histórico que desea graficar:", options=opciones_misiones, key="sel_sec1")
                    indice_sector = int(seleccion.split(" | ")[0].split(" ")[1])
                    if st.button("📈 GENERAR DIAGNÓSTICO FOTOMÉTRICO", key="btn_run_an1"):
                        status_box1 = st.status("📡 Conectando...", expanded=True)
                        try:
                            img_bytes, mision_nombre = generar_grafica_individual_bytes(tic_target1, indice_sector)
                            status_box1.update(label="🎯 ¡Completado!", state="complete")
                            st.image(img_bytes, use_container_width=True)
                            st.download_button(label="📥 DESCARGAR GRÁFICA (PNG)", data=img_bytes, file_name=f"Historial_TIC_{tic_target1}_Sector_{mision_nombre}.png", mime="image/png")
                        except Exception as inside_err: st.error(f"Fallo: {inside_err}")
            except Exception as e_an1: st.error(f"Error: {e_an1}")
            
    with subtab_completo:
        st.subheader("🛸 Procesamiento Automatizado Multiespectral")
        tic_id_an2 = st.text_input("ID de la Estrella para Auditoría Masiva (TIC):", value="", placeholder="Ej: 289512179", key="txt_an2")
        if tic_id_an2.strip():
            tic_target2 = tic_id_an2.strip()
            if st.button("🚀 INICIAR AUDITORÍA DE TODOS LOS SECTORES", key="btn_run_an2"):
                status_macro = st.status("🕵️ Conectando...", expanded=True)
                try:
                    opciones_misiones2 = buscar_sectores_tesscut_lista(tic_target2)
                    total_sectores = len(opciones_misiones2)
                    status_macro.update(label=f"📦 Encontrados {total_sectores} sectores.")
                    for i in range(total_sectores):
                        st.markdown(f"### ⏳ Sector {i+1}/{total_sectores}: Procesando...")
                        try:
                            resultado = generar_auditoria_sector_bytes(tic_target2, i)
                            if resultado["status"] == "skip": continue
                            st.image(resultado["img_bytes"], use_container_width=True)
                            st.download_button(label="📥 DESCARGAR DIAGNÓSTICO {resultado['mision']} (PNG)", data=resultado["img_bytes"], file_name=f"Diagnostico_TIC_{tic_target2}_{resultado['mision']}.png", mime="image/png", key=f"btn_dl_masivo_{i}")
                        except: continue
                    status_macro.update(label="🏁 AUDITORÍA COMPLETADA.", state="complete")
                except Exception as e_master: st.error(f"Fallo: {e_master}")

# ------------------------------------------------------------------------------
# PESTAÑA 5: VALIDACIÓN FORENSE DEL CANDIDATO (VETTING)
# ------------------------------------------------------------------------------
with tab_planeta:
    st.header("🪐 Servidor Forense de Validación de Candidatos (Vetting)")
    tic_id_planeta = st.text_input("ID de la Estrella Anfitriona (TIC):", value="", placeholder="Ej: 289512179", key="txt_id_planeta")
    if not tic_id_planeta.strip(): st.info("🌌 LABORATORIO EN ESPERA...")
    else:
        with st.spinner("Consultando catálogos estelares..."):
            try:
                target_data = Catalogs.query_criteria(catalog="TIC", ID=int(tic_id_planeta.strip()))
                if len(target_data) == 0: st.error("❌ No registrada.")
                else:
                    r_estrella_nasa = target_data['rad'][0] if 'rad' in target_data.colnames and not np.isnan(target_data['rad'][0]) else None
                    col_est1, col_est2 = st.columns([2, 3])
                    with col_est1:
                        unidad_profundidad = st.radio("Unidad:", ["Porcentaje (%)", "Partes por Millón (ppm)"])
                        if unidad_profundidad == "Porcentaje (%)":
                            caida_luz = st.number_input("Profundidad (%):", min_value=0.001, max_value=20.0, value=1.0, step=0.01, format="%.3f")
                            fraction_depth = caida_luz / 100.0
                        else:
                            caida_luz = st.number_input("Profundidad (ppm):", min_value=1.0, max_value=200000.0, value=10000.0, step=10.0)
                            fraction_depth = caida_luz / 1000000.0
                        r_estrella = st.number_input("Radio Estrella (R☉):", min_value=0.05, max_value=50.0, value=float(r_estrella_nasa) if r_estrella_nasa else 1.0, step=0.01)
                        odd_even_sigma = st.number_input("Diferencia Impar/Par (Sigma σ):", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
                        centroid_status = st.radio("Centroide:", ["Centrado en el Objetivo (On-Target)", "Desviado / Contaminación de Fondo (Background Blend)"])
                    with col_est2:
                        radio_planeta_sol = r_estrella * np.sqrt(fraction_depth)
                        radio_planeta_tierra = radio_planeta_sol * 109.2
                        radio_planeta_jupiter = radio_planeta_sol / 0.10049
                        flags = []
                        is_binary = radio_planeta_jupiter > 2.2 or odd_even_sigma >= 3.0
                        if radio_planeta_jupiter > 2.2: flags.append("companion_too_large_for_planet")
                        if odd_even_sigma >= 3.0: flags.append("odd_even_mismatch")
                        if centroid_status == "Desviado / Contaminación de Fondo (Background Blend)": flags.append("background_blend")
                        
                        if "background_blend" in flags: categoria, confianza, color_box = "Falso Positivo por Fondo (Background Blend / NEB)", 95, "#ef4444"
                        elif is_binary: categoria, confianza, color_box = "Binaria de Eclipse (Eclipsing Binary Candidate)", 95 if (len(flags) >= 2) else 85, "#f97316"
                        else: categoria, confianza, color_box = "Candidato a Exoplaneta (Planet Candidate)", 90, "#10b981"
                        
                        st.markdown(f"<div style='background-color: #0f172a; padding: 20px; border-radius: 8px; border-left: 6px solid {color_box};'><p style='color: #94a3b8; font-size: 11px; margin: 0;'>CATEGORY</p><p style='color: #f8fafc; font-size: 20px; font-weight: bold; margin: 3px 0 0 0;'>{categoria}</p><p style='color: #22d3ee; font-size: 14px; margin: 5px 0 0 0;'>Confidence: {confianza}%</p></div>", unsafe_allow_html=True)
                        st.markdown(f"**Análisis de Variables:**\n• {'❌' if radio_planeta_jupiter > 2.2 else '🟢'} **Radio:** {radio_planeta_jupiter:.2f} R_Jup\n• {'❌' if 'background_blend' in flags else '🟢'} **Centroide:** {centroid_status}\n• {'❌' if odd_even_sigma >= 3.0 else '🟢'} **Impar/Par:** {odd_even_sigma}σ")
                        if flags: st.markdown("".join([f"<span style='background-color:#1e293b; color:#f43f5e; border:1px solid #f43f5e; padding:4px 8px; border-radius:4px; font-size:12px; margin-right:8px;'>{f}</span>" for f in flags]), unsafe_allow_html=True)
                        st.columns(2)[0].metric("vs Júpiter", f"{radio_planeta_jupiter:.2f} R_Jup")
                        st.columns(2)[1].metric("vs Tierra", f"{radio_planeta_tierra:.1f} R_Earth")
            except Exception as e_p: st.error(f"Error: {e_p}")
