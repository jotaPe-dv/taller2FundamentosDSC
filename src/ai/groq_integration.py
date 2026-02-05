"""
Integración con Groq API para análisis con IA Generativa
"""

from groq import Groq


def generar_analisis_ia(api_key, df, dataset_nombre):
    """
    Genera un análisis estratégico usando Llama 3 via Groq.
    Analiza el resumen estadístico de los datos.
    
    Args:
        api_key (str): API key de Groq
        df (pd.DataFrame): DataFrame a analizar
        dataset_nombre (str): Nombre del dataset (inventario, transacciones, feedback)
        
    Returns:
        str: Análisis generado por IA o mensaje de error
    """
    if not api_key:
        return "⚠️ Por favor ingresa tu API Key de Groq para continuar."
    
    try:
        # Generar resumen estadístico para el prompt
        resumen = df.describe().to_string()
        
        # Limitar longitud si es muy largo
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
