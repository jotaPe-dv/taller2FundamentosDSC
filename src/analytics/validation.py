"""
Funciones de validación y generación de reportes
"""

import pandas as pd
from .metrics import calcular_health_score, calcular_metricas_calidad
from ..data_cleaning.cleaner import limpiar_inventario, limpiar_transacciones, limpiar_feedback


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
