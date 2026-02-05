"""
Funciones para generar dashboards estratégicos con Plotly
"""

import pandas as pd
import streamlit as st
import plotly.express as px


def generar_dashboard_estrategico(df_trans, df_inv, df_feed):
    """
    Genera gráficas estratégicas para responder 5 preguntas de negocio.
    """
    # Pre-procesamiento para uniones
    # 1. Join Transacciones + Inventario
    df_full = df_trans.merge(df_inv, on='SKU_ID', how='left')
    
    # 2. Join con Feedback
    if 'Transaccion_ID' in df_feed.columns and 'Transaccion_ID' in df_trans.columns:
        df_full = df_full.merge(df_feed, on='Transaccion_ID', how='left')
    else:
        st.error("No se puede unir Feedback: Falta Transaccion_ID")
        return

    # -------------------------------------------------------------------------
    # 1. FUGA DE CAPITAL (Margen Negativo)
    # -------------------------------------------------------------------------
    st.subheader("1. 💸 Fuga de Capital y Rentabilidad")
    
    # Calcular Margen (excluyendo outliers de costo)
    if 'Costo_Unitario_USD' in df_full.columns:
        # Filtrar outliers de costo usando IQR
        Q1_costo = df_full['Costo_Unitario_USD'].quantile(0.25)
        Q3_costo = df_full['Costo_Unitario_USD'].quantile(0.75)
        IQR_costo = Q3_costo - Q1_costo
        limite_superior_costo = Q3_costo + 1.5 * IQR_costo
        
        # Crear copia filtrada para análisis de margen
        df_margen = df_full[df_full['Costo_Unitario_USD'] <= limite_superior_costo].copy()
        outliers_excluidos = len(df_full) - len(df_margen)
        
        df_margen['COGS'] = df_margen['Costo_Unitario_USD'] * df_margen['Cantidad_Vendida']
        df_margen['Margen_Total'] = df_margen['Precio_Venta_Final'] - df_margen['COGS']
        df_margen['Margen_Pct'] = (df_margen['Margen_Total'] / df_margen['Precio_Venta_Final']) * 100
        
        ventas_negativas = df_margen[df_margen['Margen_Total'] < 0].copy()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_margen = px.scatter(
                df_margen.dropna(subset=['Margen_Total']),
                x='Cantidad_Vendida',
                y='Margen_Total',
                color='Categoria',
                title=f'Distribución de Márgenes por Venta (Excluidos {outliers_excluidos} outliers de costo)',
                hover_data=['SKU_ID', 'Precio_Venta_Final', 'Costo_Unitario_USD'],
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_margen.add_hline(y=0, line_dash="dash", line_color="red")
            st.plotly_chart(fig_margen, use_container_width=True)
            
        with col2:
            st.metric("Total Ventas con Pérdida", f"{len(ventas_negativas):,}")
            st.metric("Pérdida Total Acumulada", f"${ventas_negativas['Margen_Total'].sum():,.2f}")
            st.caption(f"ℹ️ Se excluyeron {outliers_excluidos} registros con costo > ${limite_superior_costo:,.0f}")
            
            top_loss_skus = ventas_negativas.groupby('SKU_ID')['Margen_Total'].sum().nsmallest(5).reset_index()
            st.write("Top 5 SKUs con Mayor Pérdida:")
            st.dataframe(top_loss_skus, hide_index=True)

    else:
        st.warning("No se puede calcular margen: Costo_Unitario_USD nulo.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 2. CRISIS LOGÍSTICA (Tiempo Entrega vs NPS)
    # -------------------------------------------------------------------------
    st.subheader("2. 🚚 Crisis Logística: Correlación NPS vs Tiempos")
    
    if 'Satisfaccion_NPS' in df_full.columns:
        # Agrupar por Ciudad y Bodega
        df_logistica = df_full.groupby(['Ciudad_Destino', 'Bodega_Origen']).agg({
            'Tiempo_Entrega_Real': 'mean',
            'Satisfaccion_NPS': 'mean',
            'Transaccion_ID': 'count'
        }).reset_index()
        
        fig_logistica = px.scatter(
            df_logistica,
            x='Tiempo_Entrega_Real',
            y='Satisfaccion_NPS',
            size='Transaccion_ID',
            color='Bodega_Origen',
            text='Ciudad_Destino',
            title='Correlación Tiempo Entrega vs NPS (Por Ruta)',
            labels={'Tiempo_Entrega_Real': 'Tiempo Promedio (Días)', 'Satisfaccion_NPS': 'NPS Promedio'},
            color_discrete_sequence=px.colors.qualitative.T10
        )
        st.plotly_chart(fig_logistica, use_container_width=True)
        
        st.caption("Tamaño de burbuja = Volumen de envíos. Busque burbujas abajo a la derecha (Lento + Bajo NPS).")
    
    st.markdown("---")

    # -------------------------------------------------------------------------
    # 3. VENTA INVISIBLE (SKUs sin Catálogo)
    # -------------------------------------------------------------------------
    st.subheader("3. 👻 Análisis de Venta Invisible")
    
    if 'Sin_Catalogo' in df_full.columns:
        df_invisible = df_full.groupby('Sin_Catalogo')['Precio_Venta_Final'].sum().reset_index()
        df_invisible['Tipo'] = df_invisible['Sin_Catalogo'].map({True: 'Sin Catálogo (Invisible)', False: 'En Catálogo (Visible)'})
        
        col3, col4 = st.columns(2)
        
        with col3:
            fig_pie = px.pie(
                df_invisible, 
                values='Precio_Venta_Final', 
                names='Tipo', 
                title='Proporción de Ingresos: Visible vs Invisible',
                color='Tipo',
                color_discrete_map={'Sin Catálogo (Invisible)': 'red', 'En Catálogo (Visible)': 'lightgrey'}
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col4:
            monto_invisible = df_invisible[df_invisible['Sin_Catalogo'] == True]['Precio_Venta_Final'].sum() if not df_invisible[df_invisible['Sin_Catalogo'] == True].empty else 0
            pct_invisible = (monto_invisible / df_invisible['Precio_Venta_Final'].sum()) * 100
            
            st.metric("Impacto Financiero (Riesgo)", f"${monto_invisible:,.2f}")
            st.metric("% del Ingreso Total", f"{pct_invisible:.2f}%")
            st.info("Este capital ingresa pero no tiene trazabilidad de costos ni reposición automática.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 4. DIAGNÓSTICO DE FIDELIDAD (Stock vs Sentiment - Paradoja)
    # -------------------------------------------------------------------------
    st.subheader("4. ❤️ Diagnóstico de Fidelidad: Disponibilidad vs Satisfacción")
    
    # Agrupar por Categoría
    if 'Stock_Actual' in df_full.columns:
        df_cat = df_full.groupby('Categoria').agg({
            'Stock_Actual': 'mean',
            'Rating_Producto': 'mean',
            'SKU_ID': 'nunique'
        }).reset_index()
        
        fig_paradox = px.scatter(
            df_cat,
            x='Stock_Actual',
            y='Rating_Producto',
            text='Categoria',
            size='SKU_ID',
            title='Matriz Fidelidad: Stock Promedio vs Rating Producto',
            labels={'Stock_Actual': 'Stock Promedio (Unidades)', 'Rating_Producto': 'Rating Promedio (1-5)'}
        )
        
        # Cuadrantes
        mediana_stock = df_cat['Stock_Actual'].median()
        mediana_rating = df_cat['Rating_Producto'].median()
        
        fig_paradox.add_vline(x=mediana_stock, line_dash="dot", annotation_text="Mediana Stock")
        fig_paradox.add_hline(y=mediana_rating, line_dash="dot", annotation_text="Mediana Rating")
        
        st.plotly_chart(fig_paradox, use_container_width=True)
        st.caption("Cuadrante Inferior-Derecha: PARADOJA (Mucho Stock, Mala Calidad).")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 5. RIESGO OPERATIVO (Antigüedad Revision vs Tickets)
    # -------------------------------------------------------------------------
    st.subheader("5. ⚠️ Riesgo Operativo: Ceguera de Inventario vs Quejas")
    
    if 'Ultima_Revision' in df_full.columns and 'Ticket_Soporte_Abierto' in df_full.columns:
        # Calcular antigüedad de revisión
        df_full['Ultima_Revision_DT'] = pd.to_datetime(df_full['Ultima_Revision'], errors='coerce')
        fecha_ref = pd.Timestamp('2026-01-31')
        df_full['Dias_Sin_Revisar'] = (fecha_ref - df_full['Ultima_Revision_DT']).dt.days
        
        # Convertir tickets a numérico
        df_full['Ticket_Numerico'] = df_full['Ticket_Soporte_Abierto'].fillna(False).astype(int)
        
        # Agrupar por Bodega
        df_riesgo = df_full.groupby('Bodega_Origen').agg({
            'Dias_Sin_Revisar': 'mean',
            'Ticket_Numerico': 'mean',
            'Transaccion_ID': 'count'
        }).reset_index()
        
        df_riesgo['Tasa_Tickets_Pct'] = df_riesgo['Ticket_Numerico'] * 100
        
        col_r1, col_r2 = st.columns([2, 1])
        
        with col_r1:
            fig_riesgo = px.bar(
                df_riesgo,
                x='Bodega_Origen',
                y='Dias_Sin_Revisar',
                color='Tasa_Tickets_Pct',
                text=df_riesgo['Tasa_Tickets_Pct'].round(1).astype(str) + '%',
                title='Antigüedad de Revisión vs Tasa de Tickets (Color)',
                labels={'Dias_Sin_Revisar': 'Días Promedio Sin Revisar Stock', 'Tasa_Tickets_Pct': '% Tickets Soporte'},
                color_continuous_scale='RdYlGn_r'
            )
            fig_riesgo.update_traces(textposition='outside')
            st.plotly_chart(fig_riesgo, use_container_width=True)
        
        with col_r2:
            st.dataframe(df_riesgo[['Bodega_Origen', 'Dias_Sin_Revisar', 'Tasa_Tickets_Pct']].round(2), hide_index=True)
            
        st.info("Barras altas = Inventario desactualizado. Color Rojo = Muchos reclamos. La combinación es crítica.")
