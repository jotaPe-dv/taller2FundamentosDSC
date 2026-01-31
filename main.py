# =============================================================================
# BLOQUE 1: CALIDAD DEL PREPROCESO Y TRANSPARENCIA
# TechLogistics Colombia - Módulo de Auditoría y Limpieza de Datos
# Valor: 30% de la nota total
# =============================================================================

import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
from groq import Groq
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')



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
# FUNCIONES DE CÁLCULO DE HEALTH SCORE
# =============================================================================

def detectar_outliers_score(df):
    """
    Detecta outliers en columnas numéricas usando IQR y retorna
    un score de penalización (máximo 30 puntos).
    """
    columnas_numericas = df.select_dtypes(include=[np.number]).columns
    
    if len(columnas_numericas) == 0:
        return 0
    
    total_outliers = 0
    total_valores = 0
    
    for col in columnas_numericas:
        datos = df[col].dropna()
        if len(datos) == 0:
            continue
            
        Q1 = datos.quantile(0.25)
        Q3 = datos.quantile(0.75)
        IQR = Q3 - Q1
        
        limite_inferior = Q1 - 1.5 * IQR
        limite_superior = Q3 + 1.5 * IQR
        
        outliers = ((datos < limite_inferior) | (datos > limite_superior)).sum()
        total_outliers += outliers
        total_valores += len(datos)
    
    if total_valores == 0:
        return 0
    
    porcentaje_outliers = (total_outliers / total_valores) * 100
    penalizacion = min(porcentaje_outliers * 3, 30)  # Máximo 30 puntos
    
    return penalizacion


def calcular_health_score(df):
    """
    Health Score = 100 - penalizaciones
    
    Penalizaciones:
    - Nulidad promedio global: pesa 40%
    - Duplicados: pesa 30%
    - Outliers extremos: pesa 30%
    """
    # Penalización por nulidad (máximo 40 puntos)
    total_celdas = len(df) * len(df.columns)
    total_nulos = df.isnull().sum().sum()
    nulidad_promedio = (total_nulos / total_celdas) * 100 if total_celdas > 0 else 0
    penalizacion_nulos = min(nulidad_promedio * 4, 40)  # Escalar para que sea más sensible
    
    # Penalización por duplicados (máximo 30 puntos)
    duplicados_pct = (df.duplicated().sum() / len(df)) * 100 if len(df) > 0 else 0
    penalizacion_duplicados = min(duplicados_pct, 30)
    
    # Penalización por outliers (máximo 30 puntos)
    penalizacion_outliers = detectar_outliers_score(df)
    
    health_score = 100 - (penalizacion_nulos + penalizacion_duplicados + penalizacion_outliers)
    
    return max(0, round(health_score, 2))


def calcular_metricas_calidad(df, nombre_dataset):
    """
    Calcula métricas de calidad completas para un DataFrame.
    """
    metricas = {
        'dataset': nombre_dataset,
        'total_registros': len(df),
        'total_columnas': len(df.columns),
        'nulos_por_columna': df.isnull().sum().to_dict(),
        'porcentaje_nulidad_por_columna': (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
        'columnas_con_nulos': df.columns[df.isnull().any()].tolist(),
        'total_nulos': df.isnull().sum().sum(),
        'registros_duplicados': df.duplicated().sum(),
        'porcentaje_duplicados': round((df.duplicated().sum() / len(df) * 100), 2),
        'health_score': calcular_health_score(df)
    }
    return metricas


# =============================================================================
# FUNCIONES DE CARGA DE DATOS
# =============================================================================

@st.cache_data
def cargar_datos():
    """Carga los tres datasets originales."""
    df_inventario = pd.read_csv('inventario_central_v2.csv')
    df_transacciones = pd.read_csv('transacciones_logistica_v2.csv')
    df_feedback = pd.read_csv('feedback_clientes_v2.csv')
    
    return df_inventario, df_transacciones, df_feedback


# =============================================================================
# FUNCIONES DE LIMPIEZA - INVENTARIO
# =============================================================================

def limpiar_inventario(df, registro):
    """
    Limpia el dataset de inventario con decisiones justificadas.
    Estrategia: CONSERVAR DATOS AL MÁXIMO, imputar con mediana.
    """
    df_limpio = df.copy()
    
    # =========================================================================
    # 1. NORMALIZAR CATEGORÍAS
    # =========================================================================
    mapeo_categorias = {
        'smart-phone': 'Smartphones',
        'LAPTOP': 'Laptops',
        '???': 'Sin_Categoria'
    }
    
    categorias_antes = df_limpio['Categoria'].nunique()
    df_limpio['Categoria'] = df_limpio['Categoria'].replace(mapeo_categorias)
    categorias_despues = df_limpio['Categoria'].nunique()
    
    registro['transformaciones'].append({
        'campo': 'Categoria',
        'tipo': 'Normalización',
        'antes': f'{categorias_antes} categorías únicas',
        'despues': f'{categorias_despues} categorías únicas',
        'justificacion': 'Se unificaron variantes (smart-phone → Smartphones, LAPTOP → Laptops) y se etiquetaron valores desconocidos (??? → Sin_Categoria) para mantener trazabilidad.'
    })
    
    # =========================================================================
    # 2. NORMALIZAR BODEGAS
    # =========================================================================
    mapeo_bodegas = {
        'norte': 'Norte',
        'ZONA_FRANCA': 'Zona_Franca',
        'BOD-EXT-99': 'Bodega_Externa'
    }
    
    df_limpio['Bodega_Origen'] = df_limpio['Bodega_Origen'].replace(mapeo_bodegas)
    
    registro['transformaciones'].append({
        'campo': 'Bodega_Origen',
        'tipo': 'Normalización',
        'antes': 'Valores inconsistentes (norte, ZONA_FRANCA, BOD-EXT-99)',
        'despues': 'Valores estandarizados (Norte, Zona_Franca, Bodega_Externa)',
        'justificacion': 'Estandarización para permitir agrupaciones correctas en análisis por bodega.'
    })
    
    # =========================================================================
    # 3. TRATAR LEAD_TIME_DIAS (convertir a numérico)
    # =========================================================================
    # Mapear valores de texto a numéricos
    mapeo_lead_time = {
        '25-30 días': 27.5,  # Promedio del rango
        'Inmediato': 1,
        'nan': np.nan
    }
    
    # Convertir a string primero para manejar todos los casos
    df_limpio['Lead_Time_Dias'] = df_limpio['Lead_Time_Dias'].astype(str)
    df_limpio['Lead_Time_Dias'] = df_limpio['Lead_Time_Dias'].replace(mapeo_lead_time)
    
    # Convertir a numérico
    df_limpio['Lead_Time_Dias'] = pd.to_numeric(df_limpio['Lead_Time_Dias'], errors='coerce')
    
    # Imputar nulos con mediana
    mediana_lead_time = df_limpio['Lead_Time_Dias'].median()
    nulos_lead_time = df_limpio['Lead_Time_Dias'].isnull().sum()
    df_limpio['Lead_Time_Dias'] = df_limpio['Lead_Time_Dias'].fillna(mediana_lead_time)
    
    registro['valores_imputados'].append({
        'campo': 'Lead_Time_Dias',
        'cantidad': nulos_lead_time,
        'metodo': 'Mediana',
        'valor_imputado': round(mediana_lead_time, 1),
        'justificacion': f'Lead Time tiene distribución asimétrica (valores como "25-30 días", "Inmediato"). Se usa mediana ({round(mediana_lead_time, 1)} días) para no sesgar por outliers.'
    })
    
    # =========================================================================
    # 4. TRATAR STOCK_ACTUAL NEGATIVO
    # =========================================================================
    # Verificar si los valores negativos tienen sentido (cambiar signo)
    stock_negativos = df_limpio[df_limpio['Stock_Actual'] < 0].copy()
    cantidad_negativos = len(stock_negativos)
    
    if cantidad_negativos > 0:
        # Estrategia: Cambiar el signo (asumiendo error de digitación)
        df_limpio.loc[df_limpio['Stock_Actual'] < 0, 'Stock_Actual'] = \
            df_limpio.loc[df_limpio['Stock_Actual'] < 0, 'Stock_Actual'].abs()
        
        registro['valores_imputados'].append({
            'campo': 'Stock_Actual',
            'cantidad': cantidad_negativos,
            'metodo': 'Cambio de signo',
            'valor_imputado': 'Valor absoluto',
            'justificacion': f'Stock negativo es físicamente imposible. Se cambió el signo de {cantidad_negativos} registros asumiendo error de digitación (el valor absoluto es coherente con el promedio de la categoría).'
        })
    
    # Imputar Stock_Actual nulos con mediana por categoría
    nulos_stock = df_limpio['Stock_Actual'].isnull().sum()
    if nulos_stock > 0:
        for categoria in df_limpio['Categoria'].unique():
            mask = (df_limpio['Stock_Actual'].isnull()) & (df_limpio['Categoria'] == categoria)
            mediana_cat = df_limpio.loc[df_limpio['Categoria'] == categoria, 'Stock_Actual'].median()
            if pd.notna(mediana_cat):
                df_limpio.loc[mask, 'Stock_Actual'] = mediana_cat
        
        # Si aún quedan nulos, usar mediana global
        mediana_global = df_limpio['Stock_Actual'].median()
        df_limpio['Stock_Actual'] = df_limpio['Stock_Actual'].fillna(mediana_global)
        
        registro['valores_imputados'].append({
            'campo': 'Stock_Actual',
            'cantidad': nulos_stock,
            'metodo': 'Mediana por categoría',
            'valor_imputado': 'Variable por categoría',
            'justificacion': 'Se imputan stocks nulos con la mediana de su categoría para mantener coherencia con el comportamiento del grupo de productos similar.'
        })
    
    # =========================================================================
    # 5. TRATAR COSTOS ATÍPICOS (pero conservar con flag)
    # =========================================================================
    Q1 = df_limpio['Costo_Unitario_USD'].quantile(0.25)
    Q3 = df_limpio['Costo_Unitario_USD'].quantile(0.75)
    IQR = Q3 - Q1
    limite_inferior = max(0.01, Q1 - 1.5 * IQR)  # No puede ser negativo
    limite_superior = Q3 + 1.5 * IQR
    
    # Crear flag para outliers en lugar de eliminar
    df_limpio['Costo_Atipico'] = (
        (df_limpio['Costo_Unitario_USD'] < limite_inferior) | 
        (df_limpio['Costo_Unitario_USD'] > limite_superior)
    )
    
    outliers_costo = df_limpio['Costo_Atipico'].sum()
    
    # Tratar costos extremadamente bajos (posibles errores)
    costos_muy_bajos = df_limpio['Costo_Unitario_USD'] < 1
    if costos_muy_bajos.sum() > 0:
        mediana_costo = df_limpio.loc[~costos_muy_bajos, 'Costo_Unitario_USD'].median()
        df_limpio.loc[costos_muy_bajos, 'Costo_Unitario_USD'] = mediana_costo
        
        registro['valores_imputados'].append({
            'campo': 'Costo_Unitario_USD',
            'cantidad': costos_muy_bajos.sum(),
            'metodo': 'Imputación con mediana',
            'valor_imputado': round(mediana_costo, 2),
            'justificacion': f'Costos < $1 USD son claramente errores de captura. Se imputan con mediana (${round(mediana_costo, 2)}) para mantener el registro pero con valor realista.'
        })
    
    registro['transformaciones'].append({
        'campo': 'Costo_Unitario_USD',
        'tipo': 'Flag de outliers',
        'antes': f'{outliers_costo} outliers detectados',
        'despues': 'Columna Costo_Atipico añadida (True/False)',
        'justificacion': f'Se conservan los {outliers_costo} registros con costos atípicos pero se marcan con flag para análisis posterior. Límites IQR: ${limite_inferior:.2f} - ${limite_superior:.2f}'
    })
    
    # =========================================================================
    # 6. VALIDAR FECHAS (Ultima_Revision)
    # =========================================================================
    df_limpio['Ultima_Revision'] = pd.to_datetime(df_limpio['Ultima_Revision'], errors='coerce')
    fecha_actual = pd.Timestamp('2026-01-31')
    
    # Identificar fechas futuras
    fechas_futuras = df_limpio['Ultima_Revision'] > fecha_actual
    cantidad_futuras = fechas_futuras.sum()
    
    if cantidad_futuras > 0:
        # Imputar fechas futuras con fecha actual (en lugar de eliminar)
        df_limpio.loc[fechas_futuras, 'Ultima_Revision'] = fecha_actual
        
        registro['valores_imputados'].append({
            'campo': 'Ultima_Revision',
            'cantidad': cantidad_futuras,
            'metodo': 'Imputación con fecha actual',
            'valor_imputado': str(fecha_actual.date()),
            'justificacion': f'{cantidad_futuras} registros tenían fechas futuras (error de sistema). Se imputan con fecha actual para conservar los registros.'
        })
    
    return df_limpio, registro


# =============================================================================
# FUNCIONES DE LIMPIEZA - TRANSACCIONES
# =============================================================================

def limpiar_transacciones(df, df_inventario, registro):
    """
    Limpia el dataset de transacciones con decisiones justificadas.
    Estrategia: CONSERVAR DATOS AL MÁXIMO, imputar con mediana.
    """
    df_limpio = df.copy()
    
    # =========================================================================
    # 1. CONVERTIR FECHA_VENTA
    # =========================================================================
    df_limpio['Fecha_Venta'] = pd.to_datetime(df_limpio['Fecha_Venta'], format='%d/%m/%Y', errors='coerce')
    
    fechas_invalidas = df_limpio['Fecha_Venta'].isnull().sum()
    if fechas_invalidas > 0:
        registro['transformaciones'].append({
            'campo': 'Fecha_Venta',
            'tipo': 'Conversión de formato',
            'antes': f'{fechas_invalidas} fechas no parseables',
            'despues': 'Formato datetime estandarizado',
            'justificacion': 'Conversión necesaria para análisis temporal.'
        })
    
    # =========================================================================
    # 2. NORMALIZAR CIUDADES
    # =========================================================================
    ciudades_antes = df_limpio['Ciudad_Destino'].nunique()
    
    mapeo_ciudades = {
        'MED': 'Medellín',
        'med': 'Medellín',
        'Medellin': 'Medellín',
        'MEDELLIN': 'Medellín',
        'BOG': 'Bogotá',
        'bog': 'Bogotá',
        'Bogota': 'Bogotá',
        'BOGOTA': 'Bogotá',
        'Ventas_Web': 'Ventas_Web'  # Mantener como canal especial
    }
    
    df_limpio['Ciudad_Destino'] = df_limpio['Ciudad_Destino'].replace(mapeo_ciudades)
    ciudades_despues = df_limpio['Ciudad_Destino'].nunique()
    
    registro['transformaciones'].append({
        'campo': 'Ciudad_Destino',
        'tipo': 'Normalización',
        'antes': f'{ciudades_antes} ciudades únicas',
        'despues': f'{ciudades_despues} ciudades únicas',
        'justificacion': 'Unificación de variantes de nombres (MED→Medellín, BOG→Bogotá) para análisis geográfico correcto.'
    })
    
    # =========================================================================
    # 3. TRATAR CANTIDAD_VENDIDA NEGATIVA
    # =========================================================================
    cantidades_negativas = df_limpio['Cantidad_Vendida'] < 0
    cantidad_neg = cantidades_negativas.sum()
    
    if cantidad_neg > 0:
        # Estrategia: Cambiar signo (probablemente error de digitación)
        df_limpio.loc[cantidades_negativas, 'Cantidad_Vendida'] = \
            df_limpio.loc[cantidades_negativas, 'Cantidad_Vendida'].abs()
        
        registro['valores_imputados'].append({
            'campo': 'Cantidad_Vendida',
            'cantidad': cantidad_neg,
            'metodo': 'Cambio de signo',
            'valor_imputado': 'Valor absoluto',
            'justificacion': f'{cantidad_neg} registros con cantidad negativa. El valor absoluto es coherente con los promedios de venta, sugiriendo error de digitación. Se conserva el registro cambiando el signo.'
        })
    
    # =========================================================================
    # 4. TRATAR TIEMPO_ENTREGA_REAL OUTLIERS (999 días)
    # =========================================================================
    tiempos_extremos = df_limpio['Tiempo_Entrega_Real'] >= 999
    cantidad_extremos = tiempos_extremos.sum()
    
    if cantidad_extremos > 0:
        # Calcular mediana por ciudad para imputación inteligente
        mediana_por_ciudad = df_limpio[df_limpio['Tiempo_Entrega_Real'] < 999].groupby('Ciudad_Destino')['Tiempo_Entrega_Real'].median()
        mediana_global = df_limpio[df_limpio['Tiempo_Entrega_Real'] < 999]['Tiempo_Entrega_Real'].median()
        
        for idx in df_limpio[tiempos_extremos].index:
            ciudad = df_limpio.loc[idx, 'Ciudad_Destino']
            if ciudad in mediana_por_ciudad.index:
                df_limpio.loc[idx, 'Tiempo_Entrega_Real'] = mediana_por_ciudad[ciudad]
            else:
                df_limpio.loc[idx, 'Tiempo_Entrega_Real'] = mediana_global
        
        registro['valores_imputados'].append({
            'campo': 'Tiempo_Entrega_Real',
            'cantidad': cantidad_extremos,
            'metodo': 'Mediana por ciudad',
            'valor_imputado': f'Variable (global: {mediana_global:.0f} días)',
            'justificacion': f'{cantidad_extremos} registros con 999 días (valor placeholder). Se imputan con mediana de la ciudad de destino para reflejar tiempos realistas de esa ruta.'
        })
    
    # =========================================================================
    # 5. IMPUTAR COSTO_ENVIO NULOS
    # =========================================================================
    nulos_costo_envio = df_limpio['Costo_Envio'].isnull().sum()
    
    if nulos_costo_envio > 0:
        # Imputar con mediana por ciudad
        mediana_envio_ciudad = df_limpio.groupby('Ciudad_Destino')['Costo_Envio'].transform('median')
        df_limpio['Costo_Envio'] = df_limpio['Costo_Envio'].fillna(mediana_envio_ciudad)
        
        # Si aún quedan nulos, usar mediana global
        mediana_global_envio = df_limpio['Costo_Envio'].median()
        df_limpio['Costo_Envio'] = df_limpio['Costo_Envio'].fillna(mediana_global_envio)
        
        registro['valores_imputados'].append({
            'campo': 'Costo_Envio',
            'cantidad': nulos_costo_envio,
            'metodo': 'Mediana por ciudad',
            'valor_imputado': f'Variable (global: ${mediana_global_envio:.2f})',
            'justificacion': f'{nulos_costo_envio} registros sin costo de envío. Se imputa con mediana de la ciudad de destino (costos de envío varían por ruta).'
        })
    
    # =========================================================================
    # 6. IMPUTAR ESTADO_ENVIO NULOS
    # =========================================================================
    nulos_estado = df_limpio['Estado_Envio'].isnull().sum() + (df_limpio['Estado_Envio'] == '').sum()
    
    if nulos_estado > 0:
        # Imputar con moda (valor más frecuente)
        moda_estado = df_limpio['Estado_Envio'].mode()[0] if len(df_limpio['Estado_Envio'].mode()) > 0 else 'Desconocido'
        df_limpio['Estado_Envio'] = df_limpio['Estado_Envio'].fillna('Pendiente')
        df_limpio['Estado_Envio'] = df_limpio['Estado_Envio'].replace('', 'Pendiente')
        
        registro['valores_imputados'].append({
            'campo': 'Estado_Envio',
            'cantidad': nulos_estado,
            'metodo': 'Valor por defecto',
            'valor_imputado': 'Pendiente',
            'justificacion': f'{nulos_estado} registros sin estado de envío. Se asigna "Pendiente" como estado conservador que no asume entrega ni pérdida.'
        })
    
    # =========================================================================
    # 7. IDENTIFICAR SKUs HUÉRFANOS (DECISIÓN CRÍTICA)
    # =========================================================================
    skus_inventario = set(df_inventario['SKU_ID'].unique())
    skus_transacciones = set(df_limpio['SKU_ID'].unique())
    skus_huerfanos = skus_transacciones - skus_inventario
    
    # Crear flag en lugar de eliminar
    df_limpio['Sin_Catalogo'] = df_limpio['SKU_ID'].isin(skus_huerfanos)
    
    ventas_huerfanas = df_limpio['Sin_Catalogo'].sum()
    ingresos_huerfanos = df_limpio.loc[df_limpio['Sin_Catalogo'], 'Precio_Venta_Final'].sum()
    ingresos_totales = df_limpio['Precio_Venta_Final'].sum()
    porcentaje_ingresos = (ingresos_huerfanos / ingresos_totales * 100) if ingresos_totales > 0 else 0
    
    registro['skus_huerfanos_decision'] = f"""
DECISIÓN: Mantener ventas de SKUs huérfanos con flag 'Sin_Catalogo = True'

JUSTIFICACIÓN DETALLADA:
━━━━━━━━━━━━━━━━━━━━━━━━
• SKUs únicos sin catálogo: {len(skus_huerfanos)}
• Transacciones afectadas: {ventas_huerfanas} ({ventas_huerfanas/len(df_limpio)*100:.2f}% del total)
• Impacto financiero: ${ingresos_huerfanos:,.2f} USD ({porcentaje_ingresos:.2f}% del ingreso total)

ANÁLISIS DE OPCIONES:
─────────────────────
❌ OPCIÓN A (Eliminar): Perdería ${ingresos_huerfanos:,.2f} de visibilidad de ingresos reales.
✅ OPCIÓN B (Mantener con flag): Permite análisis de "Venta Invisible" y cálculo de impacto.
❌ OPCIÓN C (Crear dummies): Falsearía el maestro de inventario.

IMPLICACIÓN EN CÁLCULOS:
────────────────────────
• Estas ventas NO pueden calcular margen (sin costo unitario)
• Se reportarán como 'Ingreso sin margen verificable'
• Útil para identificar problemas de catalogación en el negocio
"""
    
    registro['transformaciones'].append({
        'campo': 'SKU_ID',
        'tipo': 'Flag de SKUs huérfanos',
        'antes': f'{ventas_huerfanas} ventas sin catálogo',
        'despues': 'Columna Sin_Catalogo añadida (True/False)',
        'justificacion': f'Se conservan las {ventas_huerfanas} ventas (${ingresos_huerfanos:,.2f}) marcándolas para análisis de "Venta Invisible".'
    })
    
    return df_limpio, registro


# =============================================================================
# FUNCIONES DE LIMPIEZA - FEEDBACK
# =============================================================================

def limpiar_feedback(df, registro):
    """
    Limpia el dataset de feedback con decisiones justificadas.
    Estrategia: CONSERVAR DATOS AL MÁXIMO, imputar con mediana.
    """
    df_limpio = df.copy()
    
    # =========================================================================
    # 1. TRATAR RATING_PRODUCTO FUERA DE RANGO
    # =========================================================================
    ratings_invalidos = (df_limpio['Rating_Producto'] < 1) | (df_limpio['Rating_Producto'] > 5)
    cantidad_invalidos = ratings_invalidos.sum()
    
    if cantidad_invalidos > 0:
        # Los valores >5 (como 99) parecen ser errores
        # Estrategia: Si es >5, podría ser escala diferente o error
        # Si es 99, claramente es un placeholder/error
        
        # Para valores muy altos (>10), imputar con mediana
        muy_altos = df_limpio['Rating_Producto'] > 10
        mediana_rating = df_limpio.loc[~muy_altos, 'Rating_Producto'].median()
        df_limpio.loc[muy_altos, 'Rating_Producto'] = mediana_rating
        
        # Normalizar valores entre 1-5
        df_limpio['Rating_Producto'] = df_limpio['Rating_Producto'].clip(1, 5)
        
        registro['valores_imputados'].append({
            'campo': 'Rating_Producto',
            'cantidad': cantidad_invalidos,
            'metodo': 'Clipping + Mediana',
            'valor_imputado': f'{mediana_rating:.1f}',
            'justificacion': f'{cantidad_invalidos} ratings fuera de rango 1-5. Valores extremos (>10) se imputan con mediana. Resto se ajusta al rango válido.'
        })
    
    # =========================================================================
    # 2. TRATAR RATING_LOGISTICA FUERA DE RANGO
    # =========================================================================
    ratings_log_invalidos = (df_limpio['Rating_Logistica'] < 1) | (df_limpio['Rating_Logistica'] > 5)
    
    if ratings_log_invalidos.sum() > 0:
        df_limpio['Rating_Logistica'] = df_limpio['Rating_Logistica'].clip(1, 5)
        
        registro['transformaciones'].append({
            'campo': 'Rating_Logistica',
            'tipo': 'Normalización de escala',
            'antes': f'{ratings_log_invalidos.sum()} valores fuera de rango',
            'despues': 'Valores ajustados al rango 1-5',
            'justificacion': 'Escala de rating debe estar entre 1-5. Se ajustan valores extremos.'
        })
    
    # =========================================================================
    # 3. TRATAR EDAD_CLIENTE IMPOSIBLES
    # =========================================================================
    edades_invalidas = (df_limpio['Edad_Cliente'] < 18) | (df_limpio['Edad_Cliente'] > 100)
    cantidad_edades_inv = edades_invalidas.sum()
    
    if cantidad_edades_inv > 0:
        # Para edades imposibles (como 195), imputar con mediana
        mediana_edad = df_limpio.loc[~edades_invalidas, 'Edad_Cliente'].median()
        df_limpio.loc[edades_invalidas, 'Edad_Cliente'] = mediana_edad
        
        registro['valores_imputados'].append({
            'campo': 'Edad_Cliente',
            'cantidad': cantidad_edades_inv,
            'metodo': 'Mediana',
            'valor_imputado': f'{mediana_edad:.0f} años',
            'justificacion': f'{cantidad_edades_inv} edades fuera de rango realista (18-100). Se imputan con mediana ({mediana_edad:.0f} años) para mantener el registro de feedback.'
        })
    
    # =========================================================================
    # 4. NORMALIZAR RECOMIENDA_MARCA
    # =========================================================================
    mapeo_recomienda = {
        'SI': 'Sí',
        'Si': 'Sí',
        'si': 'Sí',
        'NO': 'No',
        'no': 'No',
        'Maybe': 'Tal vez',
        'maybe': 'Tal vez',
        'N/A': 'No responde'
    }
    
    df_limpio['Recomienda_Marca'] = df_limpio['Recomienda_Marca'].replace(mapeo_recomienda)
    
    registro['transformaciones'].append({
        'campo': 'Recomienda_Marca',
        'tipo': 'Normalización',
        'antes': 'Valores inconsistentes (SI, Maybe, N/A)',
        'despues': 'Valores estandarizados (Sí, No, Tal vez, No responde)',
        'justificacion': 'Estandarización para análisis de satisfacción y recomendación.'
    })
    
    # =========================================================================
    # 5. NORMALIZAR TICKET_SOPORTE_ABIERTO
    # =========================================================================
    mapeo_ticket = {
        'Sí': True,
        'Si': True,
        'SI': True,
        '1': True,
        1: True,
        'No': False,
        'NO': False,
        '0': False,
        0: False
    }
    
    df_limpio['Ticket_Soporte_Abierto'] = df_limpio['Ticket_Soporte_Abierto'].replace(mapeo_ticket)
    # Convertir a booleano
    df_limpio['Ticket_Soporte_Abierto'] = df_limpio['Ticket_Soporte_Abierto'].map(
        lambda x: True if x in [True, 'Sí', 'Si', 'SI', '1', 1] else False
    )
    
    registro['transformaciones'].append({
        'campo': 'Ticket_Soporte_Abierto',
        'tipo': 'Conversión a booleano',
        'antes': 'Valores mixtos (Sí/No/1/0)',
        'despues': 'Booleano (True/False)',
        'justificacion': 'Estandarización para análisis de tickets de soporte.'
    })
    
    # =========================================================================
    # 6. TRATAR DUPLICADOS
    # =========================================================================
    duplicados = df_limpio.duplicated(keep='first')
    cantidad_duplicados = duplicados.sum()
    
    if cantidad_duplicados > 0:
        # Conservar el primero de cada duplicado
        df_limpio = df_limpio.drop_duplicates(keep='first')
        
        registro['registros_eliminados'].append({
            'motivo': 'Duplicados exactos',
            'cantidad': cantidad_duplicados,
            'accion': 'Eliminados (conservando el primero)',
            'justificacion': f'{cantidad_duplicados} registros duplicados exactos. Se conserva el primer registro de cada grupo de duplicados.'
        })
    
    # =========================================================================
    # 7. VALIDAR SATISFACCION_NPS (ya está en escala -100 a 100)
    # =========================================================================
    nps_stats = df_limpio['Satisfaccion_NPS'].describe()
    
    registro['transformaciones'].append({
        'campo': 'Satisfaccion_NPS',
        'tipo': 'Validación',
        'antes': f'Rango: {nps_stats["min"]:.1f} a {nps_stats["max"]:.1f}',
        'despues': 'Escala -100 a 100 validada',
        'justificacion': 'NPS ya está en escala estándar (-100 a 100). No requiere transformación.'
    })
    
    return df_limpio, registro


# =============================================================================
# FUNCIÓN PRINCIPAL DE LIMPIEZA
# =============================================================================

def ejecutar_limpieza_completa(df_inventario, df_transacciones, df_feedback):
    """
    Ejecuta la limpieza completa de los 3 datasets y genera el registro.
    """
    # Inicializar registros
    registro_inventario = {
        'registros_eliminados': [],
        'valores_imputados': [],
        'transformaciones': [],
        'justificaciones': []
    }
    
    registro_transacciones = {
        'registros_eliminados': [],
        'valores_imputados': [],
        'transformaciones': [],
        'justificaciones': [],
        'skus_huerfanos_decision': ''
    }
    
    registro_feedback = {
        'registros_eliminados': [],
        'valores_imputados': [],
        'transformaciones': [],
        'justificaciones': []
    }
    
    # Calcular Health Score ANTES
    health_antes = {
        'inventario': calcular_health_score(df_inventario),
        'transacciones': calcular_health_score(df_transacciones),
        'feedback': calcular_health_score(df_feedback)
    }
    
    metricas_antes = {
        'inventario': calcular_metricas_calidad(df_inventario, 'inventario'),
        'transacciones': calcular_metricas_calidad(df_transacciones, 'transacciones'),
        'feedback': calcular_metricas_calidad(df_feedback, 'feedback')
    }
    
    # Ejecutar limpieza
    df_inventario_limpio, registro_inventario = limpiar_inventario(df_inventario, registro_inventario)
    df_transacciones_limpio, registro_transacciones = limpiar_transacciones(
        df_transacciones, df_inventario_limpio, registro_transacciones
    )
    df_feedback_limpio, registro_feedback = limpiar_feedback(df_feedback, registro_feedback)
    
    # Calcular Health Score DESPUÉS
    health_despues = {
        'inventario': calcular_health_score(df_inventario_limpio),
        'transacciones': calcular_health_score(df_transacciones_limpio),
        'feedback': calcular_health_score(df_feedback_limpio)
    }
    
    metricas_despues = {
        'inventario': calcular_metricas_calidad(df_inventario_limpio, 'inventario'),
        'transacciones': calcular_metricas_calidad(df_transacciones_limpio, 'transacciones'),
        'feedback': calcular_metricas_calidad(df_feedback_limpio, 'feedback')
    }
    
    # Calcular mejora
    mejora = {
        'inventario': health_despues['inventario'] - health_antes['inventario'],
        'transacciones': health_despues['transacciones'] - health_antes['transacciones'],
        'feedback': health_despues['feedback'] - health_antes['feedback']
    }
    
    return {
        'dataframes': {
            'inventario': df_inventario_limpio,
            'transacciones': df_transacciones_limpio,
            'feedback': df_feedback_limpio
        },
        'registros': {
            'inventario': registro_inventario,
            'transacciones': registro_transacciones,
            'feedback': registro_feedback
        },
        'health_antes': health_antes,
        'health_despues': health_despues,
        'mejora': mejora,
        'metricas_antes': metricas_antes,
        'metricas_despues': metricas_despues
    }


# =============================================================================
# FUNCIÓN PARA GENERAR REPORTE DESCARGABLE
# =============================================================================

def generar_reporte_limpieza(resultados):
    """
    Genera un DataFrame resumen para descarga.
    """
    registros_originales = {
        'inventario': resultados['metricas_antes']['inventario']['total_registros'],
        'transacciones': resultados['metricas_antes']['transacciones']['total_registros'],
        'feedback': resultados['metricas_antes']['feedback']['total_registros']
    }
    
    registros_finales = {
        'inventario': resultados['metricas_despues']['inventario']['total_registros'],
        'transacciones': resultados['metricas_despues']['transacciones']['total_registros'],
        'feedback': resultados['metricas_despues']['feedback']['total_registros']
    }
    
    reporte = []
    for dataset in ['inventario', 'transacciones', 'feedback']:
        nulos_antes = resultados['metricas_antes'][dataset]['total_nulos']
        nulos_despues = resultados['metricas_despues'][dataset]['total_nulos']
        
        reporte.append({
            'Dataset': dataset.capitalize(),
            'Registros_Originales': registros_originales[dataset],
            'Registros_Finales': registros_finales[dataset],
            'Registros_Eliminados': registros_originales[dataset] - registros_finales[dataset],
            'Nulos_Antes': nulos_antes,
            'Nulos_Despues': nulos_despues,
            'Nulos_Tratados': nulos_antes - nulos_despues,
            'Duplicados_Eliminados': resultados['metricas_antes'][dataset]['registros_duplicados'],
            'Health_Score_Inicial': resultados['health_antes'][dataset],
            'Health_Score_Final': resultados['health_despues'][dataset],
            'Mejora_Puntos': resultados['mejora'][dataset]
        })
    
    return pd.DataFrame(reporte)


# =============================================================================
# INTERFAZ STREAMLIT - TAB AUDITORÍA
# =============================================================================

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


# =============================================================================
# VALIDACIONES DE INTEGRIDAD
# =============================================================================

def validar_integridad(df_transacciones, df_inventario, df_transacciones_original):
    """
    Ejecuta las validaciones de integridad post-limpieza.
    """
    validaciones = []
    
    # Validación 1: Integridad de Merge (no perder ingresos)
    ingresos_original = df_transacciones_original['Precio_Venta_Final'].sum()
    ingresos_post = df_transacciones['Precio_Venta_Final'].sum()
    
    validaciones.append({
        'test': 'Integridad de Ingresos',
        'esperado': f'${ingresos_original:,.2f}',
        'obtenido': f'${ingresos_post:,.2f}',
        'diferencia': f'${abs(ingresos_original - ingresos_post):,.2f}',
        'estado': '✅ PASS' if abs(ingresos_original - ingresos_post) < 0.01 else '⚠️ REVISAR'
    })
    
    # Validación 2: Merge con inventario
    df_merged = df_transacciones.merge(df_inventario, on='SKU_ID', how='left', indicator=True)
    ventas_con_catalogo = (df_merged['_merge'] == 'both').sum()
    ventas_sin_catalogo = (df_merged['_merge'] == 'left_only').sum()
    
    validaciones.append({
        'test': 'Ventas CON catálogo',
        'esperado': 'Mayoría',
        'obtenido': f'{ventas_con_catalogo} ({ventas_con_catalogo/len(df_merged)*100:.1f}%)',
        'diferencia': '-',
        'estado': '✅ PASS' if ventas_con_catalogo > ventas_sin_catalogo else '⚠️ REVISAR'
    })
    
    validaciones.append({
        'test': 'Ventas SIN catálogo (flag)',
        'esperado': 'Marcadas correctamente',
        'obtenido': f'{ventas_sin_catalogo} transacciones',
        'diferencia': '-',
        'estado': '✅ DOCUMENTADO'
    })
    
    # Validación 3: No hay fechas futuras
    fecha_actual = pd.Timestamp('2026-01-31')
    fechas_futuras = (df_transacciones['Fecha_Venta'] > fecha_actual).sum()
    
    validaciones.append({
        'test': 'Sin fechas futuras',
        'esperado': '0',
        'obtenido': str(fechas_futuras),
        'diferencia': '-',
        'estado': '✅ PASS' if fechas_futuras == 0 else '❌ FAIL'
    })
    
    # Validación 4: No hay cantidades negativas
    cantidades_negativas = (df_transacciones['Cantidad_Vendida'] < 0).sum()
    
    validaciones.append({
        'test': 'Sin cantidades negativas',
        'esperado': '0',
        'obtenido': str(cantidades_negativas),
        'diferencia': '-',
        'estado': '✅ PASS' if cantidades_negativas == 0 else '❌ FAIL'
    })
    
    # Validación 5: No hay tiempos de entrega extremos
    tiempos_extremos = (df_transacciones['Tiempo_Entrega_Real'] >= 999).sum()
    
    validaciones.append({
        'test': 'Sin tiempos entrega 999',
        'esperado': '0',
        'obtenido': str(tiempos_extremos),
        'diferencia': '-',
        'estado': '✅ PASS' if tiempos_extremos == 0 else '❌ FAIL'
    })
    
    return pd.DataFrame(validaciones)


# =============================================================================
# DASHBOARD ESTRATÉGICO (PLOTLY)
# =============================================================================

def generar_dashboard_estrategico(df_trans, df_inv, df_feed):
    """
    Genera gráficas estratégicas para responder 5 preguntas de negocio.
    """
    # Pre-procesamiento para uniones
    # 1. Join Transacciones + Inventario
    df_full = df_trans.merge(df_inv, on='SKU_ID', how='left')
    
    # 2. Join con Feedback
    # Feedback se une por Transaccion_ID? Vamos a asumir que si, o verificar si hay SKU.
    # df_feedback tiene Transaccion_ID.
    # Nota: Si Feedback no tiene Transaccion_ID, revisar estructura.
    # Asumimos que Feedback -> Transaccion_ID es la llave.
    
    # Verificar columnas de feedback para el merge
    if 'Transaccion_ID' in df_feed.columns and 'Transaccion_ID' in df_trans.columns:
        df_full = df_full.merge(df_feed, on='Transaccion_ID', how='left')
    else:
        st.error("No se puede unir Feedback: Falta Transaccion_ID")
        return

    # -------------------------------------------------------------------------
    # 1. FUGA DE CAPITAL (Margen Negativo)
    # -------------------------------------------------------------------------
    st.subheader("1. 💸 Fuga de Capital y Rentabilidad")
    
    # Calcular Margen
    # Asumimos Precio_Venta_Final es el total de la venta.
    # COGS = Costo_Unitario * Cantidad
    if 'Costo_Unitario_USD' in df_full.columns:
        df_full['COGS'] = df_full['Costo_Unitario_USD'] * df_full['Cantidad_Vendida']
        df_full['Margen_Total'] = df_full['Precio_Venta_Final'] - df_full['COGS']
        df_full['Margen_Pct'] = (df_full['Margen_Total'] / df_full['Precio_Venta_Final']) * 100
        
        ventas_negativas = df_full[df_full['Margen_Total'] < 0].copy()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_margen = px.scatter(
                df_full.dropna(subset=['Margen_Total']),
                x='Cantidad_Vendida',
                y='Margen_Total',
                color='Categoria',
                title='Distribución de Márgenes por Venta',
                hover_data=['SKU_ID', 'Precio_Venta_Final', 'Costo_Unitario_USD'],
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            # Agregar linea de cero
            fig_margen.add_hline(y=0, line_dash="dash", line_color="red")
            st.plotly_chart(fig_margen, use_container_width=True)
            
        with col2:
            st.metric("Total Ventas con Pérdida", f"{len(ventas_negativas):,}")
            st.metric("Pérdida Total Acumulada", f"${ventas_negativas['Margen_Total'].sum():,.2f}")
            
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
            'Rating_Producto': 'mean', # Usamos Rating 1-5 que es más directo para producto que NPS
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
        df_full['Ultima_Revision_DT'] = pd.to_datetime(df_full['Ultima_Revision'])
        fecha_ref = pd.Timestamp('2026-01-31') # Fecha actual simulada
        df_full['Dias_Sin_Revisar'] = (fecha_ref - df_full['Ultima_Revision_DT']).dt.days
        
        # Agrupar por Bodega
        df_riesgo = df_full.groupby('Bodega_Origen').agg({
            'Dias_Sin_Revisar': 'mean',
            'Ticket_Soporte_Abierto': lambda x: (sum(x) / len(x)) * 100, # Tasa de tickets %
            'Transaccion_ID': 'count'
        }).reset_index()
        
        df_riesgo.rename(columns={'Ticket_Soporte_Abierto': 'Tasa_Tickets_Pct'}, inplace=True)
        
        fig_riesgo = px.bar(
            df_riesgo,
            x='Bodega_Origen',
            y='Dias_Sin_Revisar',
            color='Tasa_Tickets_Pct',
            title='Antigüedad de Revisión vs Tasa de Tickets (Color)',
            labels={'Dias_Sin_Revisar': 'Días Promedio Sin Revisar Stock', 'Tasa_Tickets_Pct': '% Tickets Soporte'},
            color_continuous_scale='RdYlGn_r' # Rojo es alto ticket rate
        )
        
        st.plotly_chart(fig_riesgo, use_container_width=True)
        st.info("Barras altas = Inventario desactualizado. Color Rojo = Muchos reclamos. La combinación es crítica.")


# =============================================================================
# FUNCIÓN DE ANÁLISIS CON IA (GROQ / LLAMA 3)
# =============================================================================

def generar_analisis_ia(api_key, df, dataset_nombre):
    """
    Genera un análisis estratégico usando Llama 3 via Groq.
    Analiza el resumen estadístico de los datos.
    """
    if not api_key:
        return "⚠️ Por favor ingresa tu API Key de Groq para continuar."
    
    try:
        # Generar resumen estadístico para el prompt
        resumen = df.describe().to_string()
        
        # Limitar longitud si es muy largo (aunque describe() suele ser corto)
        if len(resumen) > 6000:
            resumen = resumen[:6000] + "..."
            
        client = Groq(api_key=api_key)
        
        prompt = f"""
        Actúa como un Consultor Senior de Logística y Data Science.
        Analiza el siguiente resumen estadístico del dataset '{dataset_nombre}':
        
        {resumen}
        
        Genera 3 párrafos de recomendación estratégica EN TIEMPO REAL basándote en estos números.
        Estructura tu respuesta así:
        
        1. **Diagnóstico General**: Qué nos dicen los números sobre la salud de esta área (dispersión, promedios, máximos).
        2. **Oportunidades de Eficiencia**: Dónde se puede mejorar (ej. reducir tiempos, optimizar stock).
        3. **Acciones Inmediatas**: Pasos concretos a seguir basado en los datos.
        
        Mantén un tono profesional, directo y orientado a negocio.
        """
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en análisis de datos logísticos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error al conectar con la IA: {str(e)}"


# =============================================================================
# APLICACIÓN PRINCIPAL
# =============================================================================

def main():
    # =========================================================================
    # SIDEBAR NAVIGATION
    # =========================================================================
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/warehouse.png", width=80)
        st.title("🏭 TechLogistics")
        st.markdown("---")
        
        pagina = st.radio(
            "📌 Navegación",
            [
                "🔍 Auditoría",
                "✅ Validaciones",
                "📊 Datos Limpios",
                "📈 Resumen Ejecutivo",
                "📊 Dashboard Estratégico",
                "🤖 Asistente IA"
            ],
            key="nav_radio"
        )
        
        st.markdown("---")
        st.caption("Sistema de Auditoría y Limpieza de Datos v2.0")
    
    # =========================================================================
    # CARGAR DATOS (con cache)
    # =========================================================================
    try:
        df_inventario_original, df_transacciones_original, df_feedback_original = cargar_datos()
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        st.stop()
    
    # =========================================================================
    # EJECUTAR LIMPIEZA (con cache en session_state)
    # =========================================================================
    if 'resultados_auditoria' not in st.session_state:
        with st.spinner("🔄 Ejecutando auditoría y limpieza de datos..."):
            resultados = ejecutar_limpieza_completa(
                df_inventario_original.copy(),
                df_transacciones_original.copy(),
                df_feedback_original.copy()
            )
            st.session_state['resultados_auditoria'] = resultados
            st.session_state['df_inventario_limpio'] = resultados['dataframes']['inventario']
            st.session_state['df_transacciones_limpio'] = resultados['dataframes']['transacciones']
            st.session_state['df_feedback_limpio'] = resultados['dataframes']['feedback']
    
    resultados = st.session_state['resultados_auditoria']
    
    # =========================================================================
    # CONTENIDO SEGÚN PÁGINA SELECCIONADA
    # =========================================================================
    
    if pagina == "🔍 Auditoría":
        mostrar_tab_auditoria(resultados)
    
    elif pagina == "✅ Validaciones":
        st.header("✅ Validaciones de Integridad")
        st.markdown("---")
        
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
            st.warning(f"⚠️ {passed}/{total} validaciones pasaron. Revisar las marcadas.")
    
    elif pagina == "📊 Datos Limpios":
        st.header("📊 Vista Previa de Datos Limpios")
        st.markdown("---")
        
        dataset_seleccionado = st.selectbox(
            "Seleccionar dataset:",
            ['inventario', 'transacciones', 'feedback'],
            key="dataset_selector"
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
            key="download_clean"
        )
    
    elif pagina == "📈 Resumen Ejecutivo":
        st.header("📈 Resumen Ejecutivo")
        st.markdown("---")
        
        st.markdown("""
        ## 🎯 Objetivo del Bloque 1
        
        Crear un módulo de **Auditoría y Transparencia** que documenta TODO el proceso
        de transformación de datos con decisiones justificadas.
        
        ---
        
        ## 📊 Resultados de la Limpieza
        """)
        
        df_reporte = generar_reporte_limpieza(resultados)
        st.dataframe(df_reporte, use_container_width=True)
        
        st.markdown("""
        ---
        
        ## 🔑 Decisiones Clave Tomadas
        
        ### 1. **Stock Negativo (Inventario)**
        - **Decisión:** Cambiar signo en lugar de eliminar
        - **Justificación:** Los valores absolutos son coherentes con promedios de categoría
        
        ### 2. **SKUs Huérfanos (Transacciones)**
        - **Decisión:** Mantener con flag `Sin_Catalogo = True`
        - **Justificación:** Representan ingresos reales que no deben perderse
        
        ### 3. **Tiempos de Entrega 999 días**
        - **Decisión:** Imputar con mediana por ciudad
        - **Justificación:** 999 es claramente un placeholder, no dato real
        
        ### 4. **Costos Atípicos**
        - **Decisión:** Marcar con flag pero conservar
        - **Justificación:** Requieren validación manual del negocio
        
        ### 5. **Edades Imposibles (Feedback)**
        - **Decisión:** Imputar con mediana
        - **Justificación:** 195 años es error de captura evidente
        """)
    
    elif pagina == "📊 Dashboard Estratégico":
        st.header("📊 Dashboard Estratégico de Negocio")
        st.markdown("Respuestas visuales a las 5 preguntas clave de la gerencia.")
        st.markdown("---")
        
        generar_dashboard_estrategico(
            resultados['dataframes']['transacciones'],
            resultados['dataframes']['inventario'],
            resultados['dataframes']['feedback']
        )
    
    elif pagina == "🤖 Asistente IA":
        st.header("🤖 Asistente Inteligente logístico (Llama-3.3)")
        st.markdown("---")
        
        st.markdown("""
        Esta sección utiliza Inteligencia Artificial Generativa para analizar las estadísticas de tus datos
        y proveer recomendaciones estratégicas en tiempo real.
        """)
        
        api_key = st.text_input("🔑 Ingresa tu API Key de Groq:", type="password", help="Necesitas una key de console.groq.com", key="api_key_input")
        
        if not api_key:
            st.warning("⚠️ Necesitas ingresar una API Key para usar el asistente.")
        
        st.markdown("---")
        
        col_sel1, col_sel2 = st.columns(2)
        
        with col_sel1:
            dataset_ia = st.selectbox(
                "Selecciona el dataset a analizar:",
                ['dataframes_inventario', 'dataframes_transacciones', 'dataframes_feedback'],
                format_func=lambda x: x.split('_')[1].capitalize(),
                key="ia_dataset_selector"
            )
            key_map = {
                'dataframes_inventario': 'inventario',
                'dataframes_transacciones': 'transacciones',
                'dataframes_feedback': 'feedback'
            }
            df_ia = resultados['dataframes'][key_map[dataset_ia]]
            
        with col_sel2:
            st.info(f"Analizando **{len(df_ia):,}** registros de {key_map[dataset_ia].capitalize()}.")
            
        with st.expander("Ver estadísticas que analizará la IA"):
            st.dataframe(df_ia.describe(), use_container_width=True)
            
        if st.button("🚀 Generar Recomendaciones Estratégicas", type="primary", disabled=not api_key, key="generate_ia"):
            with st.spinner("🤖 Llama-3.3 está analizando tus datos..."):
                recomendacion = generar_analisis_ia(api_key, df_ia, key_map[dataset_ia])
                
                st.session_state['ultima_recomendacion'] = recomendacion
                
        if 'ultima_recomendacion' in st.session_state:
            st.markdown("### 🧠 Análisis Estratégico Generado")
            st.success("Análisis completado exitosamente.")
            st.markdown(st.session_state['ultima_recomendacion'])
            st.caption("Nota: Este análisis es generado por un modelo de IA y debe ser validado por expertos.")


if __name__ == "__main__":
    main()

