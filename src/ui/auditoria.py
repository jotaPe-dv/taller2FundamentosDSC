"""
Tab de Auditoría - Muestra métricas de calidad de datos
"""

import pandas as pd
import streamlit as st


def mostrar_tab_auditoria(resultados):
    """
    Muestra el tab de Auditoría en Streamlit.
    """
    st.header("🔍 Auditoría de Calidad de Datos")
    st.markdown("---")
    
    # =========================================================================
    # SECCIÓN 1: HEALTH SCORE COMPARATIVO
    # =========================================================================
    st.subheader("📊 Health Score - Comparación Antes vs Después")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🏭 Inventario",
            value=f"{resultados['health_despues']['inventario']:.1f}",
            delta=f"+{resultados['mejora']['inventario']:.1f} pts"
        )
        st.caption(f"Antes: {resultados['health_antes']['inventario']:.1f}")
    
    with col2:
        st.metric(
            label="📦 Transacciones",
            value=f"{resultados['health_despues']['transacciones']:.1f}",
            delta=f"+{resultados['mejora']['transacciones']:.1f} pts"
        )
        st.caption(f"Antes: {resultados['health_antes']['transacciones']:.1f}")
    
    with col3:
        st.metric(
            label="💬 Feedback",
            value=f"{resultados['health_despues']['feedback']:.1f}",
            delta=f"+{resultados['mejora']['feedback']:.1f} pts"
        )
        st.caption(f"Antes: {resultados['health_antes']['feedback']:.1f}")
    
    st.markdown("---")
    
    # =========================================================================
    # SECCIÓN 2: TABLA ANTES VS DESPUÉS
    # =========================================================================
    st.subheader("📋 Métricas de Calidad - Antes vs Después")
    
    col_antes, col_despues = st.columns(2)
    
    with col_antes:
        st.markdown("### 🔴 ANTES de Limpieza")
        df_antes = pd.DataFrame([
            {
                'Dataset': ds.capitalize(),
                'Registros': resultados['metricas_antes'][ds]['total_registros'],
                'Nulos Totales': resultados['metricas_antes'][ds]['total_nulos'],
                'Duplicados': resultados['metricas_antes'][ds]['registros_duplicados'],
                'Health Score': resultados['health_antes'][ds]
            }
            for ds in ['inventario', 'transacciones', 'feedback']
        ])
        st.dataframe(df_antes, use_container_width=True)
    
    with col_despues:
        st.markdown("### 🟢 DESPUÉS de Limpieza")
        df_despues = pd.DataFrame([
            {
                'Dataset': ds.capitalize(),
                'Registros': resultados['metricas_despues'][ds]['total_registros'],
                'Nulos Totales': resultados['metricas_despues'][ds]['total_nulos'],
                'Duplicados': resultados['metricas_despues'][ds]['registros_duplicados'],
                'Health Score': resultados['health_despues'][ds]
            }
            for ds in ['inventario', 'transacciones', 'feedback']
        ])
        st.dataframe(df_despues, use_container_width=True)
    
    st.markdown("---")
    
    # =========================================================================
    # SECCIÓN 3: DECISIONES CRÍTICAS DOCUMENTADAS
    # =========================================================================
    st.subheader("⚖️ Decisiones Éticas y Justificaciones")
    
    # SKUs Huérfanos (Decisión más importante)
    with st.expander("🔴 CRÍTICO: Tratamiento de SKUs Huérfanos", expanded=True):
        st.markdown(resultados['registros']['transacciones']['skus_huerfanos_decision'])
    
    # Imputaciones de Inventario
    with st.expander("📦 Imputaciones - Dataset Inventario"):
        for imputacion in resultados['registros']['inventario']['valores_imputados']:
            st.info(f"""
            **Campo:** {imputacion['campo']}  
            **Cantidad afectada:** {imputacion['cantidad']}  
            **Método:** {imputacion['metodo']}  
            **Valor imputado:** {imputacion['valor_imputado']}  
            **Justificación:** {imputacion['justificacion']}
            """)
    
    # Imputaciones de Transacciones
    with st.expander("🚚 Imputaciones - Dataset Transacciones"):
        for imputacion in resultados['registros']['transacciones']['valores_imputados']:
            st.info(f"""
            **Campo:** {imputacion['campo']}  
            **Cantidad afectada:** {imputacion['cantidad']}  
            **Método:** {imputacion['metodo']}  
            **Valor imputado:** {imputacion['valor_imputado']}  
            **Justificación:** {imputacion['justificacion']}
            """)
    
    # Imputaciones de Feedback
    with st.expander("💬 Imputaciones - Dataset Feedback"):
        for imputacion in resultados['registros']['feedback']['valores_imputados']:
            st.info(f"""
            **Campo:** {imputacion['campo']}  
            **Cantidad afectada:** {imputacion['cantidad']}  
            **Método:** {imputacion['metodo']}  
            **Valor imputado:** {imputacion['valor_imputado']}  
            **Justificación:** {imputacion['justificacion']}
            """)
    
    st.markdown("---")
    
    # =========================================================================
    # SECCIÓN 4: TRANSFORMACIONES REALIZADAS
    # =========================================================================
    st.subheader("🔄 Transformaciones Realizadas")
    
    todas_transformaciones = []
    for ds in ['inventario', 'transacciones', 'feedback']:
        for trans in resultados['registros'][ds]['transformaciones']:
            todas_transformaciones.append({
                'Dataset': ds.capitalize(),
                'Campo': trans['campo'],
                'Tipo': trans['tipo'],
                'Antes': trans['antes'],
                'Después': trans['despues'],
                'Justificación': trans['justificacion']
            })
    
    if todas_transformaciones:
        df_transformaciones = pd.DataFrame(todas_transformaciones)
        st.dataframe(df_transformaciones, use_container_width=True, height=400)
    
    st.markdown("---")
    
    # =========================================================================
    # SECCIÓN 5: REGISTROS EXCLUIDOS
    # =========================================================================
    st.subheader("🚨 Registros Excluidos/Modificados")
    
    # Mostrar outliers de costo si existen
    if 'Costo_Atipico' in resultados['dataframes']['inventario'].columns:
        outliers_costo = resultados['dataframes']['inventario'][
            resultados['dataframes']['inventario']['Costo_Atipico'] == True
        ]
        
        if st.checkbox(f"📍 Ver SKUs con costos atípicos ({len(outliers_costo)} productos)"):
            st.dataframe(
                outliers_costo[['SKU_ID', 'Categoria', 'Costo_Unitario_USD', 'Stock_Actual']],
                use_container_width=True
            )
            st.caption("⚠️ Estos registros fueron CONSERVADOS pero marcados para revisión manual.")
    
    # Mostrar SKUs huérfanos
    if 'Sin_Catalogo' in resultados['dataframes']['transacciones'].columns:
        ventas_huerfanas = resultados['dataframes']['transacciones'][
            resultados['dataframes']['transacciones']['Sin_Catalogo'] == True
        ]
        
        if st.checkbox(f"📍 Ver ventas de SKUs sin catálogo ({len(ventas_huerfanas)} transacciones)"):
            st.dataframe(
                ventas_huerfanas[['Transaccion_ID', 'SKU_ID', 'Fecha_Venta', 'Precio_Venta_Final', 'Ciudad_Destino']].head(100),
                use_container_width=True
            )
            st.caption("⚠️ Estas ventas fueron CONSERVADAS pero marcadas como 'Sin_Catalogo'.")
    
    st.markdown("---")
    
    # =========================================================================
    # SECCIÓN 6: DESCARGA DEL REPORTE
    # =========================================================================
    from ..analytics import generar_reporte_limpieza
    
    st.subheader("📥 Descargar Reportes")
    
    col_download1, col_download2 = st.columns(2)
    
    with col_download1:
        df_reporte = generar_reporte_limpieza(resultados)
        st.download_button(
            label="📊 Descargar Reporte de Limpieza (CSV)",
            data=df_reporte.to_csv(index=False).encode('utf-8'),
            file_name='reporte_limpieza_techlogistics.csv',
            mime='text/csv',
            use_container_width=True
        )
    
    with col_download2:
        # Generar reporte detallado de justificaciones
        justificaciones = []
        for ds in ['inventario', 'transacciones', 'feedback']:
            for imp in resultados['registros'][ds]['valores_imputados']:
                justificaciones.append({
                    'Dataset': ds,
                    'Campo': imp['campo'],
                    'Cantidad': imp['cantidad'],
                    'Metodo': imp['metodo'],
                    'Justificacion': imp['justificacion']
                })
        
        df_justificaciones = pd.DataFrame(justificaciones)
        st.download_button(
            label="📝 Descargar Justificaciones (CSV)",
            data=df_justificaciones.to_csv(index=False).encode('utf-8'),
            file_name='justificaciones_limpieza.csv',
            mime='text/csv',
            use_container_width=True
        )
