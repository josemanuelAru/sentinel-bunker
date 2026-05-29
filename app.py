import streamlit as st
import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# --- CONFIGURACIÓN DE LA PANTALLA (Modo TV) ---
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

# --- PESTAÑA 2: REGISTROS HISTÓRICOS (Sincronizado con tu Colab) ---
with tab_registros:
    st.header("🔍 Buscador de Archivos TESS (NASA)")
    st.write("Introduzca la numeración de la estrella para extraer sus productos de datos oficiales de TESScut.")
    
    tic_id = st.text_input("ID de la Estrella (TIC):", placeholder="Ej: 55187830")
    
    if tic_id.strip():
        tic_input = tic_id.strip()
        with st.spinner(f"Interrogando a los servidores MAST (TESScut) para TIC {tic_input}..."):
            try:
                # 🚨 CORRECCIÓN CLAVE: Activamos search_tesscut en lugar de search_lightcurve
                search_result = lk.search_tesscut(f"TIC {tic_input}")
                
                if len(search_result) == 0:
                    st.warning(f"⚠️ No se han encontrado recortes de TESScut para la estrella TIC {tic_input}.")
                else:
                    st.success(f"🎯 SearchResult containing {len(search_result)} data products.")
                    
                    # Extraemos los datos exactos limpiando las unidades físicas para que la tabla sea idéntica
                    exptimes = [int(t.value) if hasattr(t, 'value') else int(t) for t in search_result.exptime]
                    distances = [round(float(d.value), 1) if hasattr(d, 'value') else round(float(d), 1) for d in search_result.distance]
                    years = [int(y) for y in search_result.year]
                    
                    # Construimos la tabla con los nombres exactos de las columnas de tu Colab
                    df_registros = pd.DataFrame({
                        "mission": search_result.mission,
                        "year": years,
                        "author": search_result.author,
                        "exptime": exptimes,
                        "target_name": search_result.target_name,
                        "distance": distances
                    })
                    
                    # Ordenamos cronológicamente por número de Sector para que quede perfecto en la tele
                    df_registros['sector_num'] = df_registros['mission'].str.extract(r'Sector (\d+)').astype(int)
                    df_registros = df_registros.sort_values(by='sector_num').drop(columns=['sector_num']).reset_index(drop=True)
                    
                    # Desplegamos la tabla a pantalla completa
                    st.dataframe(df_registros, use_container_width=True)
                    
            except Exception as e:
                st.error(f"❌ Error de conexión con el servidor de la NASA: {e}")

# --- PESTAÑA 3: MAPAS ---
with tab_mapas:
    st.header("🎯 Localización Estelar y Centroides")
    st.info("Módulo cartográfico en desarrollo.")

# --- PESTAÑA 4: ANÁLISIS ---
with tab_analisis:
    st.header("📊 Curva de Luz Avanzada con Filtro Orbital")
    st.info("Módulo fotométrico en desarrollo.")
