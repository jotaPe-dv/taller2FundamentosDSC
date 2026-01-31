import pandas as pd
import numpy as np

def analyze_data():
    print("Loading data...")
    try:
        df_trans = pd.read_csv('transacciones_logistica_v2.csv')
        df_inv = pd.read_csv('inventario_central_v2.csv')
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    print(f"\nTotal transactions: {len(df_trans)}")
    
    # 1. Referential Integrity (SKUs in transactions not in inventory)
    skus_trans = set(df_trans['SKU_ID'].unique())
    skus_inv = set(df_inv['SKU_ID'].unique())
    missing_skus = skus_trans - skus_inv
    print(f"\n1. Referential Integrity:")
    print(f"   - Unique SKUs in Transactions: {len(skus_trans)}")
    print(f"   - Unique SKUs in Inventory: {len(skus_inv)}")
    print(f"   - SKUs in Transactions MISSING from Inventory: {len(missing_skus)}")
    
    # 2. Date Formats (Fecha_Venta)
    print(f"\n2. Date Formats (Fecha_Venta):")
    # Attempt to sniff formats
    df_trans['Fecha_Parsed'] = pd.to_datetime(df_trans['Fecha_Venta'], errors='coerce', dayfirst=True) # Assuming many might be DD/MM/YYYY
    invalid_dates = df_trans['Fecha_Parsed'].isnull().sum()
    print(f"   - Total rows: {len(df_trans)}")
    print(f"   - Rows with parseable dates (assuming standard formats): {len(df_trans) - invalid_dates}")
    print(f"   - Rows with unparseable/invalid dates: {invalid_dates}")
    print(f"   - Sample of raw dates:\n{df_trans['Fecha_Venta'].sample(10).tolist()}")

    # 3. Delivery Time Outliers (Tiempo_Entrega_Real)
    print(f"\n3. Delivery Time Outliers (Tiempo_Entrega_Real):")
    delivery_times = pd.to_numeric(df_trans['Tiempo_Entrega_Real'], errors='coerce')
    print(f"   - Stats:\n{delivery_times.describe()}")
    outliers_999 = (delivery_times >= 999).sum()
    print(f"   - Records with >= 999 days: {outliers_999}")
    
    # Check for other potential outliers using IQR
    Q1 = delivery_times.quantile(0.25)
    Q3 = delivery_times.quantile(0.75)
    IQR = Q3 - Q1
    upper_bound = Q3 + 1.5 * IQR
    print(f"   - IQR Upper Bound for outliers: {upper_bound:.2f}")
    iqr_outliers = (delivery_times > upper_bound).sum()
    print(f"   - Total outliers > {upper_bound:.2f}: {iqr_outliers}")

if __name__ == "__main__":
    analyze_data()
