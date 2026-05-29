import streamlit as st
import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astroquery.mast import Catalogs
import astropy.units as u
from astropy.coordinates import SkyCoord

# --- CONFIGURACIÓN DE LA PANTALLA (Modo TV Ancho) ---
# Debe ser siempre el primer comando de Streamlit
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

# --- 🚨 PANEL DE CONTROL LATERAL UNIVERSAL (NACE TOTALMENTE VACÍO) ---
st.sidebar.header("🛸 OBJETIVO EN MIRA")
# value="" asegura que no haya ninguna estrella por defecto al arrancar
tic_id_universal = st.sidebar.text_input("ID de la Estrella (TIC):", value="", placeholder="Ej: 210192309")
tic_input = tic_id_universal.strip()

# --- 🛑 INTERRUPTOR DE SEGURIDAD GLOBAL ---
# Si el usuario no ha puesto ningún número, la app se detiene aquí y deja la pantalla limpia
if not tic_input:
    st.markdown("""
        <div style="background-color: #0f172a; padding: 30px; border-radius: 10px; border: 1px dashed #334155; text-align: center;">
            <p style="color: #22d3ee; font-size: 20px; font-family: 'Courier New', monospace; margin: 0;">
                🌌 SISTEMAS EN ESPERA: AGUARDANDO COORDENADAS DE OBJETIVO...
            </p>
            <p style="color: #64748b; font-size: 14px; margin-top: 10px;">
                Introduzca el identificador TIC en el panel lateral izquierdo para energizar los laboratorios.
            </p>
        </div>
        """, unsafe_allow_html=True)
    st.stop()  # Detiene la ejecución por completo. Nada de abajo se procesará.

# ==============================================================================
# 🚀 A PARTIR DE AQUÍ EL SISTEMA SOLO SE ENCIENDE SI HAY UN ID INTRODUCIDO
# ==============================================================================

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
        st.info(f"Objetivo fijado: TIC {tic_input}")
    with col2:
        st.subheader("Consola de Observación")
        st.code(f"Piloto automático calibrado para rastrear el sistema TIC {tic_input}...")

# --- PESTAÑA 2: REGISTROS HISTÓRICOS ---
with tab_registros:
    st.header("🔍 Buscador de Archivos TESS (NASA)")
    st.write(f"Productos de datos oficiales de TESScut detectados para TIC {tic_input}.")
    
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

# --- PESTAÑA 3: MAPAS ESTELARES E INTERACCIÓN FORENSE ---
with tab_mapas:
    st.header("🎯 Localización y Análisis de Vecindario Estelar (#NEB)")
    
    with st.spinner(f"Cargando sistemas cartográficos para TIC {tic_input}..."):
        try:
            target_data = Catalogs.query_criteria(catalog="TIC", ID=int(tic_input))
            
            if len(target_data) == 0:
                st.error(f"❌ La estrella TIC {tic_input} no existe en el catálogo oficial.")
            else:
                ra_target = target_data['ra'][0]
                dec_target = target_data['dec'][0]
                tmag_target = target_data['Tmag'][0]
                
                rad_estelar = target_data['rad'][0] if 'rad' in target_data.colnames and not np.isnan(target_data['rad'][0]) else None
                masa_estelar = target_data['mass'][0] if 'mass' in target_data.colnames and not np.isnan(target_data['mass'][0]) else None
                temp_efectiva = target_data['teff'][0] if 'teff' in target_data.colnames and not np.isnan(target_data['teff'][0]) else None
                distancia_pc = target_data['d'][0] if 'd' in target_data.colnames and not np.isnan(target_data['d'][0]) else None
                luminosidad = target_data['lum'][0] if 'lum' in target_data.colnames and not np.isnan(target_data['lum'][0]) else None

                st.markdown(f"### 📋 Dossier Astrofísico: Sistema TIC {tic_input}")
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
                
                vecinas = df_stars[df_stars['ID'].astype(str) != tic_input]
                
                fig, axes = plt.subplots(1, 3, figsize=(20, 6.5), dpi=100)
                plt.style.use('dark_background')
                
                axes[0].scatter(vecinas['offset_ra'], vecinas['offset_dec'], s=np.maximum(5, (18 - vecinas['Tmag']) * 12), color='#475569', alpha=0.7)
                axes[0].scatter(0, 0, s=200, color='#e11d48', marker='*')
                axes[0].set_xlim(-130, 130)
                axes[0].set_ylim(-130, 130)
                axes[0].set_title("1. ESCÁNER DE PERÍMETRO")
                axes[0].grid(True, linestyle='--', alpha=0.2)
                
                for r in [30, 60, 90, 120]:
                    circle = plt.Circle((0, 0), r, fill=False, color='#1e293b', linestyle=':', alpha=0.6)
                    axes[1].add_patch(circle)
                peligrosas = vecinas[vecinas['Tmag'] <= (tmag_target + 2.5)]
                inofensivas = vecinas[vecinas['Tmag'] > (tmag_target + 2.5)]
                axes[1].scatter(inofensivas['offset_ra'], inofensivas['offset_dec'], s=np.maximum(5, (18 - inofensivas['Tmag']) * 12), color='#38bdf8', alpha=0.5)
                if not peligrosas.empty:
                    axes[1].scatter(peligrosas['offset_ra'], peligrosas['offset_dec'], s=np.maximum(10, (18 - peligrosas['Tmag']) * 16), color='#f97316', alpha=0.9)
                axes[1].scatter(0, 0, s=250, color='#22d3ee', marker='o')
                axes[1].set_xlim(-130, 130)
                axes[1].set_title("2. ESCÁNER TÁCTICO VISUAL")
                axes[1].grid(True, linestyle=':', alpha=0.1)
                
                axes[2].scatter(vecinas['offset_ra'], vecinas['offset_dec'], s=np.maximum(10, (18 - vecinas['Tmag']) * 25), color='#64748b', alpha=0.8)
                axes[2].scatter(0, 0, s=300, color='#e11d48', marker='X')
                axes[2].set_xlim(-45, 45)
                axes[2].set_ylim(-45, 45)
                axes[2].set_title("3. ESCÁNER DE ALTA RESOLUCIÓN (ZOOM)")
                axes[2].grid(True, linestyle='--', alpha=0.3)
                pixel_box = plt.Rectangle((-10.5, -10.5), 21, 21, fill=False, color='#e11d48', linestyle='--', alpha=0.5)
                axes[2].add_patch(pixel_box)
                
                plt.tight_layout()
                st.pyplot(fig)
                
                # --- FORMULARIO DE INTERACCIÓN FORENSE (TESScut FFI) ---
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
                    with st.spinner(f"Cortando FFI de la NASA para TIC {tic_input} en Sector {sector_input}..."):
                        try:
                            search_result_ffi = lk.search_tesscut(f"TIC {tic_input}", sector=int(sector_input))
                            if len(search_result_ffi) == 0:
                                st.error(f"❌ No se encontraron imágenes panorámicas de TESScut para el Sector {sector_input} en esta estrella.")
                            else:
                                tpf = search_result_ffi.download(cutout_size=7)
                                tiempo = tpf.time.value
                                flux = tpf.flux.value
                                
                                en_transito = (tiempo >= (t_centro_input - t_duracion_input/2)) & (tiempo <= (t_centro_input + t_duracion_input/2))
                                fuera_transito = ~en_transito
                                valid_frames = ~np.isnan(np.sum(flux, axis=(1,2)))
                                
                                foto_fuera = np.nanmean(flux[fuera_transito & valid_frames, :, :], axis=0)
                                foto_dentro = np.nanmean(flux[en_transito & valid_frames, :, :], axis=0)
                                imagen_diferencia = foto_fuera - foto_dentro
                                
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
                                axes2[2].plot(centro_x, centro_y, 'r*', markersize=14, label=f'TIC {tic_input}')
                                axes2[2].legend(loc='upper left')
                                
                                plt.suptitle(f"Análisis Forense de Centroide FFI - TIC {tic_input} (Sector {sector_input})", fontsize=13, y=0.98, color='#f8fafc', fontweight='bold')
                                plt.tight_layout()
                                st.pyplot(fig2)
                        except Exception as ffi_err:
                            st.error(f"❌ Error al procesar la matriz de centroide: {ffi_err}")
        except Exception as e:
            st.error(f"❌ Error al conectar con los catálogos: {e}")

# --- PESTAÑA 4: ANÁLISIS ---
with tab_analisis:
    st.header("📊 Curva de Luz Avanzada con Filtro Orbital")
    st.info(f"Módulo fotométrico asignado a la estrella TIC {tic_input}.")
