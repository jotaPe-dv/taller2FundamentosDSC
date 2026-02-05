"""
Métricas de calidad de datos y Health Score
"""

import numpy as np
import pandas as pd


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
