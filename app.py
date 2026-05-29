import streamlit as st
import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# --- 1. CONFIGURACIÓN DE LA PANTALLA (Modo TV) ---
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

# --- 2. ARQUITECTURA DE PESTAÑAS ---
tab_radar, tab_registros, tab_mapas, tab_analisis = st.tabs([
    "📡 RADAR AUTÓNOMO", 
    "🗂️ REGISTROS HISTÓRICOS", 
    "🗺️ MAPAS ESTELARES", 
    "📈 ANÁLISIS Y DESCARGAS"
])

# --- PESTAÑA 1: RADAR (Esqueleto para la Fase 4) ---
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

# --- PESTAÑA 2: REGISTROS HISTÓRICOS (¡YA FUNCIONAL!) ---
with tab_registros:
    st.header("🔍 Buscador de Archivos TESS (NASA)")
    st.write("Introduzca el identificador de la estrella para comprobar cuántas veces la ha fotografiado el satélite.")
    
    tic_id = st.text_input("ID de la Estrella (Solo los números del TIC):", placeholder="Ej: 210192309")
    
    if tic_input := tic_id.strip():
        with st.spinner(f"Interrogando a los servidores MAST para TIC {tic_input}..."):
            try:
                # Buscamos todas las curvas de luz disponibles en la base de datos de la NASA
                search_result = lk.search_lightcurve(f"TIC {tic_input}", mission="TESS")
                
                if len(search_result) == 0:
                    st.warning(f"⚠️ No se han encontrado registros públicos para la estrella TIC {tic_input}.")
                else:
                    st.success(f"🎯 ¡Conexión establecida! Se han detectado {len(search_result)} registros disponibles.")
                    
                    # Extraemos los datos de los sectores para mostrárselos ordenados en su TV
                    sectores = search_result.table['sequence_number'].tolist()
                    autores = search_result.table['author'].tolist()
                    tiempos_exposicion = search_result.table['exptime'].tolist()
                    
                    # Creamos un mapa de datos limpio (Dataframe)
                    df_registros = pd.DataFrame({
                        "Sector Disponible": sectores,
                        "Procesado Por": autores,
                        "Cadencia (Segundos)": tiempos_exposicion
                    })
                    
                    # Ordenamos por sector para llevar un orden cronológico
                    df_registros = df_registros.sort_values(by="Sector Disponible").reset_index(drop=True)
                    
                    # Desplegamos la tabla en pantalla gigante
                    st.subheader("📋 Historial de Observaciones del Satélite")
                    st.dataframe(df_registros, use_container_width=True)
                    
            except Exception as e:
                st.error(f"❌ Error de conexión con el servidor de la NASA: {e}")

# --- PESTAÑA 3: MAPAS (Esqueleto para la Fase 3) ---
with tab_mapas:
    st.header("🎯 Localización Estelar y Centroides")
    st.info("Módulo cartográfico en desarrollo. Próxima fase.")

# --- PESTAÑA 4: ANÁLISIS (Esqueleto para la Fase 2) ---
with tab_analisis:
    st.header("📊 Curva de Luz Avanzada con Filtro Orbital")
    st.info("Módulo fotométrico en desarrollo. Pendiente de integración de filtro.")
