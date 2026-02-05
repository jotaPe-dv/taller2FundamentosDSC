# 🏭 TechLogistics Colombia - Dashboard de Auditoría y Análisis

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://taller2fundamentosdsc.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Descripción del Proyecto

**TechLogistics Colombia** es una aplicación de análisis de datos diseñada para una empresa de distribución de productos tecnológicos a nivel nacional. El sistema aborda los desafíos críticos de calidad de datos que impactan directamente en la operación logística y la satisfacción del cliente.

### 🎯 Problema de Negocio

La empresa enfrenta múltiples desafíos relacionados con la integridad y calidad de sus datos:

| Problema | Impacto |
|----------|---------|
| **SKUs Huérfanos** | Transacciones con productos no registrados en el inventario maestro |
| **Costos Atípicos** | Valores de costo unitario extremadamente altos ($850,000 USD) distorsionan los análisis de rentabilidad |
| **Tiempos de Entrega 999 días** | Placeholders sin tratamiento que afectan métricas logísticas |
| **Stock Negativo** | Errores de digitación que generan inventarios imposibles |
| **Fechas Inconsistentes** | Múltiples formatos (DD/MM/YYYY, YYYY-MM-DD) y fechas futuras |
| **Edades Imposibles** | Clientes con 195 años en el sistema de feedback |

### 💡 Solución Implementada

Un **Sistema de Auditoría y Transparencia** que:

1. **Calcula un Health Score** antes y después de la limpieza
2. **Documenta cada transformación** con justificaciones de negocio
3. **Conserva datos problemáticos** con flags en lugar de eliminarlos
4. **Genera visualizaciones estratégicas** para responder preguntas de gerencia
5. **Integra IA Generativa** (Llama-3.3) para recomendaciones en tiempo real

---

## 🚀 Demo en Vivo

**▶️ [Acceder a la Aplicación](https://taller2fundamentosdsc.streamlit.app)**

---

## 🛠️ Instalación Local

### Prerrequisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/jotaPe-dv/taller2FundamentosDSC.git
cd taller2FundamentosDSC

# 2. Crear entorno virtual (recomendado)
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación modular
streamlit run main.py
```

La aplicación estará disponible en `http://localhost:8501`

---

## 📁 Estructura del Proyecto (Modularizada ✨)

```
taller2FundamentosDSC/
│
├── main.py                      # ⭐ Aplicación principal (MODULAR - refactorizada)
├── main_backup.py               # Versión monolítica original (backup)
├── requirements.txt             # Dependencias del proyecto
├── README.md                    # Este archivo
│
├── src/                         # 📦 Paquete modular organizado
│   ├── __init__.py
│   │
│   ├── data_cleaning/          # 🧹 Módulo de limpieza de datos
│   │   ├── __init__.py
│   │   ├── cleaner.py          # Funciones de limpieza (inventario, transacciones, feedback)
│   │   └── utils.py            # Utilidades de carga de datos
│   │
│   ├── analytics/              # 📊 Módulo de análisis y métricas
│   │   ├── __init__.py
│   │   ├── metrics.py          # Health Score y métricas de calidad
│   │   └── validation.py       # Validaciones de integridad y reportes
│   │
│   ├── visualizations/         # 📈 Módulo de visualizaciones
│   │   ├── __init__.py
│   │   └── dashboards.py       # Dashboards estratégicos con Plotly
│   │
│   ├── ai/                     # 🤖 Módulo de IA Generativa
│   │   ├── __init__.py
│   │   └── groq_integration.py # Integración con Llama-3.3 (Groq API)
│   │
│   └── ui/                     # 🎨 Módulo de interfaz Streamlit
│       ├── __init__.py
│       └── auditoria.py        # Tab de auditoría con documentación
│
├── inventario_central_v2.csv    # Dataset de inventario
├── transacciones_logistica_v2.csv # Dataset de transacciones
├── feedback_clientes_v2.csv     # Dataset de feedback de clientes
│
├── analyze_data.py              # Script de análisis inicial
└── clean_transactions_task.py   # Script de limpieza auxiliar
```

### 🎯 Ventajas de la Arquitectura Modular

| Ventaja | Descripción |
|---------|-------------|
| 🎯 **Separación de responsabilidades** | Cada módulo tiene una función específica y bien definida |
| ♻️ **Reutilización de código** | Los módulos pueden importarse independientemente |
| 🔧 **Mantenibilidad** | Más fácil de actualizar y debuggear código aislado |
| ✅ **Testabilidad** | Cada módulo puede probarse de forma independiente |
| 📈 **Escalabilidad** | Fácil añadir nuevas funcionalidades sin modificar el core |
| 📚 **Legibilidad** | Código organizado y fácil de navegar |

### 📦 Descripción de Módulos

#### `src/data_cleaning/`
Responsable de toda la lógica de limpieza y preprocesamiento de datos.
- **cleaner.py**: Funciones `limpiar_inventario()`, `limpiar_transacciones()`, `limpiar_feedback()`
- **utils.py**: Función `cargar_datos()` con caché de Streamlit

#### `src/analytics/`
Contiene toda la lógica de cálculo de métricas y validaciones.
- **metrics.py**: `calcular_health_score()`, `calcular_metricas_calidad()`, `detectar_outliers_score()`
- **validation.py**: `validar_integridad()`, `ejecutar_limpieza_completa()`, `generar_reporte_limpieza()`

#### `src/visualizations/`
Generación de dashboards y gráficos interactivos.
- **dashboards.py**: `generar_dashboard_estrategico()` con 5 análisis de negocio

#### `src/ai/`
Integración con modelos de lenguaje para análisis inteligente.
- **groq_integration.py**: `generar_analisis_ia()` usando Llama-3.3-70b

#### `src/ui/`
Componentes de interfaz de usuario de Streamlit.
- **auditoria.py**: `mostrar_tab_auditoria()` con todas las secciones de auditoría

---

## 📊 Módulos de la Aplicación

### 🔍 Auditoría
- **Health Score**: Métricas de calidad de datos antes/después
- **Validaciones**: Tests de integridad referencial
- **Datos Limpios**: Vista previa y descarga de datasets procesados
- **Resumen**: Documentación de decisiones tomadas

### 🚚 Operaciones
- **Rentabilidad**: Análisis de márgenes y fuga de capital
- **Logística**: Correlación NPS vs tiempos de entrega
- **Venta Invisible**: SKUs sin catálogo generando ingresos

### 👥 Cliente
- **Ratings**: Distribución de calificaciones de producto/logística
- **NPS**: Net Promoter Score y análisis de promotores
- **Tickets Soporte**: Tasa de reclamos por segmento

### 🤖 Insights IA
- Análisis estratégico generado por **Llama-3.3** (Groq)
- Requiere API Key de [console.groq.com](https://console.groq.com)

---

## 🔧 Tecnologías Utilizadas

| Tecnología | Uso |
|------------|-----|
| **Streamlit** | Framework de aplicaciones web |
| **Pandas** | Manipulación y análisis de datos |
| **Plotly** | Visualizaciones interactivas |
| **Groq API** | Integración con Llama-3.3 para IA generativa |
| **NumPy** | Operaciones numéricas |

---

## 📈 Decisiones de Limpieza Documentadas

| Problema | Decisión | Justificación |
|----------|----------|---------------|
| Stock Negativo | Cambio de signo | Error de digitación, valores absolutos coherentes |
| SKUs Huérfanos | Flag `Sin_Catalogo` | Representan ingresos reales |
| Tiempos 999 días | Imputación mediana por ciudad | Placeholder evidente |
| Costos Atípicos | Flag + filtro IQR | Requieren validación manual |
| Edades Imposibles | Imputación mediana | Error de captura evidente |

---

## 👨‍💻 Autor

**Pedro Saldarriaga**  
Estudiante - Fundamentos de Ciencia de Datos  
Universidad [Tu Universidad]

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---

## 🙏 Agradecimientos

- Profesores del curso de Fundamentos de Ciencia de Datos
- Groq por proporcionar acceso a Llama-3.3
- Comunidad de Streamlit