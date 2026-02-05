# =============================================================================
# TECHLOGISTICS COLOMBIA - APLICACIÓN MODULAR DE AUDITORÍA Y ANÁLISIS
# Sistema de Auditoría y Transparencia de Datos Logísticos
# =============================================================================

import pandas as pd
import streamlit as st
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')

# Importar módulos propios
from src.data_cleaning import cargar_datos
from src.analytics import ejecutar_limpieza_completa, validar_integridad
from src.visualizations import generar_dashboard_estrategico
from src.ai import generar_analisis_ia
from src.ui import mostrar_tab_auditoria

# =============================================================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# =============================================================================
st.set_page_config(
    page_title="TechLogistics - Auditoría de Datos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# APLICACIÓN PRINCIPAL
# =============================================================================

def main():
    # =========================================================================
    # CARGAR DATOS ORIGINALES
    # =========================================================================
    try:
        df_inventario_original, df_transacciones_original, df_feedback_original = cargar_datos()
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        st.stop()
    
    # =========================================================================
    # EJECUTAR LIMPIEZA (CACHEADO)
    # =========================================================================
    @st.cache_data
    def ejecutar_pipeline_limpieza():
        return ejecutar_limpieza_completa(
            df_inventario_original.copy(),
            df_transacciones_original.copy(),
            df_feedback_original.copy()
        )
    
    resultados = ejecutar_pipeline_limpieza()
    
    # =========================================================================
    # SIDEBAR NAVIGATION
    # =========================================================================
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/warehouse.png", width=80)
        st.title("🏭 TechLogistics")
        st.markdown("---")
        
        # Navegación
        pagina = st.radio(
            "📌 Navegación",
            [
                "🔍 Auditoría",
                "🚚 Operaciones",
                "👥 Cliente",
                "🤖 Insights IA"
            ],
            key="nav_radio"
        )
        
        st.markdown("---")
        st.markdown("### 📊 Health Score Global")
        
        # Mostrar Health Score promedio
        health_promedio = sum(resultados['health_despues'].values()) / len(resultados['health_despues'])
        st.metric("Calidad de Datos", f"{health_promedio:.1f}/100")
        
        st.markdown("---")
        st.caption("✨ **Módulos Activos:**")
        st.caption("✅ Limpieza de Datos")
        st.caption("✅ Análisis y Métricas")
        st.caption("✅ Visualizaciones")
        st.caption("✅ IA Generativa (Llama-3.3)")
        
        st.markdown("---")
        st.caption("👨‍💻 Desarrollado por Pedro Saldarriaga")
        st.caption("📚 Fundamentos de Ciencia de Datos")
    
    # =========================================================================
    # CONTENIDO PRINCIPAL POR PÁGINA
    # =========================================================================
    
    if pagina == "🔍 Auditoría":
        # Tab de Auditoría con sub-tabs
        tab_aud1, tab_aud2, tab_aud3, tab_aud4 = st.tabs([
            "📊 Health Score",
            "✅ Validaciones",
            "📋 Datos Limpios",
            "📈 Resumen"
        ])
        
        with tab_aud1:
            mostrar_tab_auditoria(resultados)
        
        with tab_aud2:
            st.subheader("✅ Validaciones de Integridad")
            df_validaciones = validar_integridad(
                resultados['dataframes']['transacciones'],
                resultados['dataframes']['inventario'],
                df_transacciones_original
            )
            st.dataframe(df_validaciones, use_container_width=True)
            
            passed = df_validaciones['estado'].str.contains('PASS|DOCUMENTADO').sum()
            total = len(df_validaciones)
            if passed == total:
                st.success(f"🎉 Todas las validaciones pasaron ({passed}/{total})")
            else:
                st.warning(f"⚠️ {passed}/{total} validaciones pasaron.")
        
        with tab_aud3:
            st.subheader("📋 Vista Previa de Datos Limpios")
            dataset_seleccionado = st.selectbox(
                "Seleccionar dataset:",
                ['inventario', 'transacciones', 'feedback'],
                key="dataset_selector_aud"
            )
            df_mostrar = resultados['dataframes'][dataset_seleccionado]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Registros", f"{len(df_mostrar):,}")
            with col2:
                st.metric("Columnas", len(df_mostrar.columns))
            with col3:
                st.metric("Health Score", f"{resultados['health_despues'][dataset_seleccionado]:.1f}")
            
            st.dataframe(df_mostrar.head(100), use_container_width=True)
            st.download_button(
                label=f"📥 Descargar {dataset_seleccionado}_limpio.csv",
                data=df_mostrar.to_csv(index=False).encode('utf-8'),
                file_name=f'{dataset_seleccionado}_limpio.csv',
                mime='text/csv',
                key="download_clean_aud"
            )
        
        with tab_aud4:
            from src.analytics import generar_reporte_limpieza
            
            st.subheader("📈 Resumen de Decisiones")
            df_reporte = generar_reporte_limpieza(resultados)
            st.dataframe(df_reporte, use_container_width=True)
            
            with st.expander("Ver Decisiones Clave"):
                st.markdown("""
                **1. Stock Negativo:** Cambio de signo (error de digitación).
                **2. SKUs Huérfanos:** Conservados con flag `Sin_Catalogo`.
                **3. Tiempos 999 días:** Imputados con mediana por ciudad.
                **4. Costos Atípicos:** Marcados para revisión manual.
                **5. Edades Imposibles:** Imputadas con mediana.
                """)
    
    elif pagina == "🚚 Operaciones":
        st.header("🚚 Dashboard de Operaciones Logísticas")
        
        # Sub-tabs dentro de Operaciones
        tab_op1, tab_op2, tab_op3 = st.tabs([
            "💸 Rentabilidad",
            "🚛 Logística",
            "👻 Venta Invisible"
        ])
        
        with tab_op1:
            # Dashboard estratégico
            generar_dashboard_estrategico(
                resultados['dataframes']['transacciones'],
                resultados['dataframes']['inventario'],
                resultados['dataframes']['feedback']
            )
    
    elif pagina == "👥 Cliente":
        st.header("👥 Análisis de Experiencia del Cliente")
        
        df_feedback = resultados['dataframes']['feedback']
        df_trans = resultados['dataframes']['transacciones']
        
        # Sub-tabs dentro de Cliente
        tab_cli1, tab_cli2, tab_cli3 = st.tabs([
            "⭐ Ratings",
            "📊 NPS",
            "🎫 Tickets Soporte"
        ])
        
        with tab_cli1:
            st.subheader("⭐ Análisis de Ratings")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Rating Producto (Promedio)", f"{df_feedback['Rating_Producto'].mean():.2f} / 5")
            with col2:
                st.metric("Rating Logística (Promedio)", f"{df_feedback['Rating_Logistica'].mean():.2f} / 5")
            
            # Distribución de ratings
            fig_rating = px.histogram(
                df_feedback,
                x='Rating_Producto',
                nbins=5,
                title='Distribución de Rating de Producto',
                color_discrete_sequence=['#636EFA']
            )
            st.plotly_chart(fig_rating, use_container_width=True)
        
        with tab_cli2:
            st.subheader("📊 Net Promoter Score (NPS)")
            
            nps_promedio = df_feedback['Satisfaccion_NPS'].mean()
            
            # Clasificar NPS
            df_feedback['NPS_Categoria'] = pd.cut(
                df_feedback['Satisfaccion_NPS'],
                bins=[-101, -50, 0, 50, 101],
                labels=['Detractores', 'Pasivos Negativos', 'Pasivos Positivos', 'Promotores']
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("NPS Promedio", f"{nps_promedio:.1f}")
            with col2:
                promotores_pct = (df_feedback['Satisfaccion_NPS'] > 50).mean() * 100
                st.metric("% Promotores (NPS > 50)", f"{promotores_pct:.1f}%")
            
            fig_nps = px.histogram(
                df_feedback,
                x='Satisfaccion_NPS',
                nbins=20,
                title='Distribución de NPS',
                color_discrete_sequence=['#00CC96']
            )
            fig_nps.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Neutral")
            st.plotly_chart(fig_nps, use_container_width=True)
        
        with tab_cli3:
            st.subheader("🎫 Tickets de Soporte")
            
            # Tasa de tickets
            tasa_tickets = df_feedback['Ticket_Soporte_Abierto'].mean() * 100
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tasa de Tickets Abiertos", f"{tasa_tickets:.1f}%")
            with col2:
                total_tickets = df_feedback['Ticket_Soporte_Abierto'].sum()
                st.metric("Total Tickets Abiertos", f"{total_tickets:,}")
            
            # Tickets por recomendación
            tickets_recomendacion = df_feedback.groupby('Recomienda_Marca')['Ticket_Soporte_Abierto'].mean().reset_index()
            tickets_recomendacion['Tasa_Tickets'] = tickets_recomendacion['Ticket_Soporte_Abierto'] * 100
            
            fig_tickets = px.bar(
                tickets_recomendacion,
                x='Recomienda_Marca',
                y='Tasa_Tickets',
                title='Tasa de Tickets según Recomendación de Marca',
                color='Tasa_Tickets',
                color_continuous_scale='RdYlGn_r'
            )
            st.plotly_chart(fig_tickets, use_container_width=True)
    
    elif pagina == "🤖 Insights IA":
        st.header("🤖 Insights Generados por IA (Llama-3.3)")
        st.markdown("---")
        
        st.markdown("""
        Esta sección utiliza **Inteligencia Artificial Generativa** para analizar las estadísticas de tus datos
        y proveer recomendaciones estratégicas en tiempo real.
        """)
        
        # Gestión de API Key
        api_key = None
        
        # Intentar obtener de st.secrets
        try:
            api_key = st.secrets.get("GROQ_API_KEY", None)
            if api_key:
                st.success("✅ API Key cargada desde secrets de Streamlit.")
        except Exception:
            pass
        
        # Si no hay secret, permitir input manual
        if not api_key:
            api_key = st.text_input(
                "🔑 Ingresa tu API Key de Groq:", 
                type="password", 
                help="En producción, configura GROQ_API_KEY en Settings > Secrets de Streamlit Cloud.",
                key="api_key_input"
            )
            if not api_key:
                st.warning("⚠️ Necesitas ingresar una API Key o configurarla en Secrets.")
        
        st.markdown("---")
        
        col_sel1, col_sel2 = st.columns(2)
        
        with col_sel1:
            dataset_ia = st.selectbox(
                "Selecciona el dataset a analizar:",
                ['inventario', 'transacciones', 'feedback'],
                format_func=lambda x: x.capitalize(),
                key="ia_dataset_selector"
            )
            df_ia = resultados['dataframes'][dataset_ia]
            
        with col_sel2:
            st.info(f"Analizando **{len(df_ia):,}** registros de {dataset_ia.capitalize()}.")
            
        with st.expander("Ver estadísticas que analizará la IA"):
            st.dataframe(df_ia.describe(), use_container_width=True)
            
        if st.button("🚀 Generar Recomendaciones Estratégicas", type="primary", disabled=not api_key, key="generate_ia"):
            with st.spinner("🤖 Llama-3.3 está analizando tus datos..."):
                recomendacion = generar_analisis_ia(api_key, df_ia, dataset_ia)
                st.session_state['ultima_recomendacion'] = recomendacion
                
        if 'ultima_recomendacion' in st.session_state:
            st.markdown("### 🧠 Análisis Estratégico Generado")
            st.success("Análisis completado exitosamente.")
            st.markdown(st.session_state['ultima_recomendacion'])
            st.caption("Nota: Este análisis es generado por un modelo de IA y debe ser validado por expertos.")


if __name__ == "__main__":
    main()
