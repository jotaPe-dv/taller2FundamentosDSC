"""
Utilidades para carga de datos
"""

import pandas as pd
import streamlit as st


@st.cache_data
def cargar_datos():
    """Carga los tres datasets originales."""
    df_inventario = pd.read_csv('inventario_central_v2.csv')
    df_transacciones = pd.read_csv('transacciones_logistica_v2.csv')
    df_feedback = pd.read_csv('feedback_clientes_v2.csv')
    
    return df_inventario, df_transacciones, df_feedback
