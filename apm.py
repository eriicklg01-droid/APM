import streamlit as st
import pandas as pd
from conexion_api import obtener_equipos_aeropuerto

# Configuración visual de la consola
st.set_page_config(
    page_title="APM Dictionary Auditor",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Consola de Diccionarios Operativos: APM API")
st.markdown("Extracción automatizada y auditoría de datos maestros de infraestructura aeronáutica en tiempo real.")
st.divider()

# --- BARRA LATERAL ---
st.sidebar.header("🛠️ Configuración de Consulta")
st.sidebar.info("Filtrando automáticamente por el endpoint verificado: `airport-equipments/values`")

st.sidebar.divider()
st.sidebar.caption("🔒 Seguridad: **OAuth2 + Basic Auth**")
st.sidebar.caption("🌐 Servidor: **restapi-masair.apm.ch**")

if st.sidebar.button("🔄 Forzar Sincronización API"):
    st.cache_data.clear()
    st.toast("Caché eliminada. Consultando directo al servidor...", icon="🔄")

# --- PROCESAMIENTO Y CONSUMO REAL ---
@st.cache_data(ttl=120) # Almacena en memoria por 2 minutos para optimizar
def cargar_equipamientos_reales():
    return obtener_equipos_aeropuerto()

# Loader visual mientras se procesa la petición HTTP
with st.spinner("Consumiendo endpoint e integrando catálogo maestro de equipos..."):
    df_equipos = cargar_equipamientos_reales()

# --- VALIDACIÓN Y RENDERIZADO DE INTERFAZ ---
if df_equipos is not None and not df_equipos.empty and "Error" not in df_equipos.columns:
    
    # 1. BLOQUE DE MÉTRICAS REALES
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Registros de Equipos Encontrados", value=len(df_equipos))
    with col2:
        st.metric(label="HTTP Status Code", value="200 OK", delta="Conexión Exitosa")
    with col3:
        # Cuenta cuántos tipos de ítems únicos hay si existe una columna 'name' o 'description'
        items_unicos = df_equipos['name'].nunique() if 'name' in df_equipos.columns else len(df_equipos)
        st.metric(label="Modelos/Claves Únicas", value=items_unicos)
        
    st.divider()
    
    # 2. TABLA DE DATOS INTERACTIVA
    st.subheader("📋 Catálogo Maestro de Equipamientos (Datos Reales de Base de Datos)")
    
    # Desplegar las columnas reales que regresó el servidor de forma adaptada a la pantalla
    st.dataframe(df_equipos, use_container_width=True)
    
    # 3. EXPORTADOR LOCAL DE DATOS REALES
    st.markdown("### 📥 Descarga e Integridad de Reportes")
    csv = df_equipos.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar Catálogo Maestro en CSV",
        data=csv,
        file_name="APM_Catalogo_Equipamientos.csv",
        mime="text/csv",
        help="Exporta las filas reales extraídas de la API de forma local inmediata."
    )

elif "Error" in df_equipos.columns:
    st.error(f"🚨 Error técnico en la conexión: {df_equipos['Error'].iloc[0]}")
    st.info("Por favor, verifica tus credenciales maestros `CLIENT_ID` y `CLIENT_SECRET` en el archivo backend.")
else:
    st.warning("⚠️ El endpoint respondió con éxito, pero la estructura del JSON no contenía colecciones de datos legibles.")