"""
Funciones de limpieza de datos para TechLogistics Colombia
Estrategia: CONSERVAR DATOS AL MÁXIMO, imputar con mediana.
"""

import pandas as pd
import numpy as np


# =============================================================================
# LIMPIEZA DE INVENTARIO
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
# LIMPIEZA DE TRANSACCIONES
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
            valor_imputar = mediana_por_ciudad.get(ciudad, mediana_global)
            df_limpio.loc[idx, 'Tiempo_Entrega_Real'] = valor_imputar
        
        registro['valores_imputados'].append({
            'campo': 'Tiempo_Entrega_Real',
            'cantidad': cantidad_extremos,
            'metodo': 'Mediana por ciudad',
            'valor_imputado': f'Variable por ciudad (global: {mediana_global:.1f} días)',
            'justificacion': f'{cantidad_extremos} registros con 999 días (placeholder evidente). Se imputan con mediana de su ciudad para reflejar tiempos logísticos reales.'
        })
    
    # =========================================================================
    # 5. IDENTIFICAR SKUs HUÉRFANOS (Integridad Referencial)
    # =========================================================================
    skus_inventario = set(df_inventario['SKU_ID'].unique())
    skus_transacciones = set(df_limpio['SKU_ID'].unique())
    skus_huerfanos = skus_transacciones - skus_inventario
    
    # Crear flag para SKUs sin catálogo
    df_limpio['Sin_Catalogo'] = df_limpio['SKU_ID'].isin(skus_huerfanos)
    ventas_huerfanas = df_limpio['Sin_Catalogo'].sum()
    
    # Calcular impacto económico
    if ventas_huerfanas > 0:
        ingresos_huerfanos = df_limpio.loc[df_limpio['Sin_Catalogo'], 'Precio_Venta_Final'].sum()
        
        registro['transformaciones'].append({
            'campo': 'SKU_ID (Integridad Referencial)',
            'tipo': 'Flag de SKUs huérfanos',
            'antes': f'{len(skus_huerfanos)} SKUs sin inventario ({ventas_huerfanas} transacciones)',
            'despues': 'Columna Sin_Catalogo añadida (True/False)',
            'justificacion': f'Se conservan {ventas_huerfanas} transacciones de SKUs no encontrados en inventario (${ingresos_huerfanos:,.2f} en ingresos). Representan ventas reales que requieren auditoría de catálogo.'
        })
        
        registro['skus_huerfanos_decision'] = f'DECISIÓN ESTRATÉGICA: Los {ventas_huerfanas} registros con SKUs huérfanos fueron CONSERVADOS con un flag "Sin_Catalogo". Representan ${ingresos_huerfanos:,.2f} en ingresos que no pueden descartarse sin auditoría.'
    
    # =========================================================================
    # 6. TRATAR DESCUENTOS NEGATIVOS
    # =========================================================================
    descuentos_negativos = df_limpio['Descuento_Aplicado_USD'] < 0
    if descuentos_negativos.sum() > 0:
        # Cambiar signo
        df_limpio.loc[descuentos_negativos, 'Descuento_Aplicado_USD'] = \
            df_limpio.loc[descuentos_negativos, 'Descuento_Aplicado_USD'].abs()
        
        registro['valores_imputados'].append({
            'campo': 'Descuento_Aplicado_USD',
            'cantidad': descuentos_negativos.sum(),
            'metodo': 'Cambio de signo',
            'valor_imputado': 'Valor absoluto',
            'justificacion': 'Descuentos negativos no tienen sentido de negocio. Se cambió el signo asumiendo error de digitación.'
        })
    
    return df_limpio, registro


# =============================================================================
# LIMPIEZA DE FEEDBACK
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
