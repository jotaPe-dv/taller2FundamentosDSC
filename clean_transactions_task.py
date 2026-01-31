import pandas as pd
import numpy as np

def clean_transactions():
    print("Cargando datos...")
    # Cargar datos
    df_trans = pd.read_csv('transacciones_logistica_v2.csv')
    df_inv = pd.read_csv('inventario_central_v2.csv')
    
    print(f"Transacciones originales: {len(df_trans)} registros")
    
    # =========================================================================
    # 1. INTEGRIDAD REFERENCIAL (SKUs Huérfanos)
    # =========================================================================
    print("\n--- 1. Analizando Integridad Referencial ---")
    skus_inv = set(df_inv['SKU_ID'].unique())
    skus_trans = set(df_trans['SKU_ID'].unique())
    skus_huerfanos = skus_trans - skus_inv
    
    # Marcar huérfanos con flag
    df_trans['Sin_Catalogo'] = df_trans['SKU_ID'].isin(skus_huerfanos)
    num_huerfanos = df_trans['Sin_Catalogo'].sum()
    
    # Calcular impacto económico
    ingresos_huerfanos = df_trans.loc[df_trans['Sin_Catalogo'], 'Precio_Venta_Final'].sum()
    
    print(f"SKUs únicos en transacciones no encontrados en inventario: {len(skus_huerfanos)}")
    print(f"Total de registros afectados (Ventas Huérfanas): {num_huerfanos}")
    print(f"Ingresos asociados a ventas huérfanas: ${ingresos_huerfanos:,.2f}")
    print("ACCIÓN: Se ha creado la columna 'Sin_Catalogo' (True/False) para identificar estos registros sin eliminarlos.")

    # =========================================================================
    # 2. FORMATO DE FECHAS
    # =========================================================================
    print("\n--- 2. Normalizando Fechas ---")
    # Convertir a datetime
    df_trans['Fecha_Venta_Format'] = pd.to_datetime(df_trans['Fecha_Venta'], format='%d/%m/%Y', errors='coerce')
    
    # Verificar si hubo fallos
    fallos_fecha = df_trans['Fecha_Venta_Format'].isnull().sum()
    print(f"Fechas convertidas al formato estándar (YYYY-MM-DD).")
    if fallos_fecha > 0:
        print(f"ADVERTENCIA: {fallos_fecha} fechas no pudieron ser convertidas.")
    else:
        print("ÉXITO: Todas las fechas fueron procesadas correctamente.")
        
    # Reemplazar columna original
    df_trans['Fecha_Venta'] = df_trans['Fecha_Venta_Format']
    df_trans.drop(columns=['Fecha_Venta_Format'], inplace=True)

    # =========================================================================
    # 3. OUTLIERS TIEMPOS DE ENTREGA (999 días)
    # =========================================================================
    print("\n--- 3. Tratando Outliers de Tiempos de Entrega ---")
    outliers_mask = df_trans['Tiempo_Entrega_Real'] >= 999
    num_outliers = outliers_mask.sum()
    
    print(f"Registros con Tiempo_Entrega_Real >= 999: {num_outliers}")
    
    if num_outliers > 0:
        # Calcular mediana por ciudad (excluyendo los outliers para el cálculo)
        data_valida = df_trans[~outliers_mask]
        mediana_global = data_valida['Tiempo_Entrega_Real'].median()
        
        # Imputar
        # Para simplificar en este script demostrativo, usamos mapeo directo si existe ciudad, sino global
        medianas_ciudad = data_valida.groupby('Ciudad_Destino')['Tiempo_Entrega_Real'].median()
        
        def imputar_tiempo(row):
            if row['Tiempo_Entrega_Real'] >= 999:
                return medianas_ciudad.get(row['Ciudad_Destino'], mediana_global)
            return row['Tiempo_Entrega_Real']
            
        df_trans['Tiempo_Entrega_Real_Imputado'] = df_trans.apply(imputar_tiempo, axis=1)
        
        # Verificación
        print(f"ACCIÓN: Se imputaron los {num_outliers} valores usando la mediana por ciudad de destino.")
        print(f"Estadísticas antes de corrección (max): {df_trans['Tiempo_Entrega_Real'].max()}")
        print(f"Estadísticas después de corrección (max): {df_trans['Tiempo_Entrega_Real_Imputado'].max()}")
        
        # Actualizar columna
        df_trans['Tiempo_Entrega_Real'] = df_trans['Tiempo_Entrega_Real_Imputado']
        df_trans.drop(columns=['Tiempo_Entrega_Real_Imputado'], inplace=True)

    # =========================================================================
    # GUARDAR RESULTADO
    # =========================================================================
    output_file = 'transacciones_logistica_limpio.csv'
    df_trans.to_csv(output_file, index=False)
    print(f"\nArchivo limpio guardado como: {output_file}")
    
    # Mostrar muestra final
    print("\nMuestra de datos procesados (primeras 3 filas):")
    print(df_trans[['SKU_ID', 'Fecha_Venta', 'Tiempo_Entrega_Real', 'Sin_Catalogo']].head(3).to_string())

if __name__ == "__main__":
    clean_transactions()
