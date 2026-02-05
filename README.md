# 🏭 TechLogistics Colombia - Dashboard de Auditoría y Análisis

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://taller2fundamentosdsc-hbzxwpygy4ttrvkamx6rdu.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AI-Assisted](https://img.shields.io/badge/AI--Assisted-Claude%20%2B%20Copilot-blueviolet.svg)](https://github.com/jotaPe-dv/taller2FundamentosDSC#-uso-de-inteligencia-artificial-en-el-desarrollo)

> 🤖 **Proyecto desarrollado con asistencia de IA:** Este trabajo académico utilizó herramientas de IA (Claude Opus/Sonnet, GitHub Copilot) como asistentes de programación bajo supervisión y validación humana completa. Ver [sección de transparencia](#-uso-de-inteligencia-artificial-en-el-desarrollo) para más detalles.

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

**▶️ [Acceder a la Aplicación](https://taller2fundamentosdsc-hbzxwpygy4ttrvkamx6rdu.streamlit.app)**

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

### 📦 Producción (Runtime)
| Tecnología | Uso |
|------------|-----|
| **Streamlit** | Framework de aplicaciones web interactivas |
| **Pandas** | Manipulación y análisis de datos |
| **Plotly** | Visualizaciones interactivas y dashboards |
| **Groq API** | Integración con Llama-3.3-70b para IA generativa |
| **NumPy** | Operaciones numéricas y computación científica |

### 🤖 Desarrollo (Asistencia IA)
| Herramienta | Propósito en el Desarrollo |
|-------------|---------------------------|
| **GitHub Copilot (Antigravity)** | Autocompletado inteligente y generación de código |
| **Claude Opus** | Arquitectura, diseño de sistemas y mejores prácticas |
| **Claude Sonnet** | Refactorización, modularización y optimización |

*Ver sección completa "Uso de Inteligencia Artificial en el Desarrollo" más abajo para detalles.*

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

## 🤖 Uso de Inteligencia Artificial en el Desarrollo

Este proyecto fue desarrollado con el apoyo de herramientas de IA para optimizar el proceso de ingeniería de software:

### 🛠️ Herramientas de IA Utilizadas

| Herramienta | Uso en el Proyecto | Propósito |
|-------------|-------------------|-----------|
| **GitHub Copilot (Antigravity)** | Asistencia en escritura de código | Autocompletado inteligente, generación de funciones y documentación |
| **Claude Opus (Anthropic)** | Arquitectura y diseño | Diseño de arquitectura modular, mejores prácticas de Python |
| **Claude Sonnet (Anthropic)** | Refactorización y optimización | "Carpintería" del código, modularización, optimización de funciones |
| **Llama-3.3-70b (Groq)** | IA Generativa en producción | Análisis estratégico de datos en tiempo real para usuarios finales |

### 📝 Disclaimer sobre el Uso de IA

> ⚠️ **Transparencia en el Desarrollo:**
> 
> - Este proyecto utilizó herramientas de IA como **asistentes de programación**, no como desarrolladores autónomos
> - Todo el código fue **revisado, comprendido y validado** por los autores
> - Las decisiones de arquitectura, diseño y lógica de negocio fueron tomadas por el equipo humano
> - La IA fue utilizada para **acelerar tareas repetitivas** 

### 🎓 Valor Pedagógico

El uso de IA en este proyecto demuestra:
- ✅ Capacidad de aprovechar herramientas modernas de la industria
- ✅ Habilidad para validar y mejorar código generado por IA
- ✅ Comprensión profunda de arquitectura de software
- ✅ Competencia en prompt engineering y dirección de IA
- ✅ Preparación para entornos profesionales modernos

---

## 📚 Referencias y Fuentes

### Datasets
- **Datos sintéticos generados** para propósitos educativos del curso
- Basados en casos reales de empresas de distribución logística
- Fuente: Material del curso Fundamentos de Ciencia de Datos - Universidad EAFIT

### Frameworks y Bibliotecas
- [Streamlit Documentation](https://docs.streamlit.io/) - Framework de aplicaciones web
- [Pandas Documentation](https://pandas.pydata.org/docs/) - Análisis de datos
- [Plotly Python](https://plotly.com/python/) - Visualizaciones interactivas
- [NumPy Documentation](https://numpy.org/doc/) - Computación científica
- [Groq API Documentation](https://console.groq.com/docs) - IA Generativa

### Conceptos y Metodologías
- **Health Score de Datos**: Metodología adaptada de prácticas de Data Quality Management
- **Integridad Referencial**: Principios de bases de datos relacionales
- **Detección de Outliers**: Método IQR (Interquartile Range) - Tukey, J. W. (1977)
- **NPS (Net Promoter Score)**: Reichheld, F. (2003) - Harvard Business Review
- **Arquitectura Modular**: Principios SOLID y Clean Architecture

### Herramientas de Desarrollo
- **Visual Studio Code** con extensiones de Python
- **Git/GitHub** para control de versiones
- **Streamlit Cloud** para deployment
- **Python 3.10+** como lenguaje base

---

## ⚖️ Consideraciones Éticas y Privacidad

### 🔒 Protección de Datos
- Este proyecto utiliza **datos sintéticos ficticios**
- No se procesaron datos personales reales
- Cumple con principios de privacidad por diseño

### 📊 Transparencia en Análisis
- Todas las decisiones de limpieza están **documentadas**
- Los registros excluidos se **conservan con flags** para auditoría
- Las transformaciones son **reversibles y trazables**

### 🤝 Uso Responsable de IA
- La IA se usó como herramienta de **aumentación**, no sustitución
- Se mantiene **responsabilidad humana** en todas las decisiones
- Las recomendaciones de IA incluyen **disclaimers de validación**

---

## 👨‍💻 Autores

**Pedro Saldarriaga**  
**Juan Pablo Mejía**  
**Juan Pablo Rua**

Estudiantes - Fundamentos de Ciencia de Datos  
Universidad EAFIT - 2026

📧 Contacto: [A través del repositorio de GitHub](https://github.com/jotaPe-dv/taller2FundamentosDSC)

---

## 🙏 Agradecimientos

- **Profesores del curso** de Fundamentos de Ciencia de Datos - Universidad EAFIT
- **Groq** por proporcionar acceso a Llama-3.3-70b para IA Generativa
- **Anthropic** por Claude (Opus & Sonnet) utilizados en el desarrollo
- **GitHub** por Copilot/Antigravity
- **Comunidad de Streamlit** por su framework open-source
- **Comunidad Python** por las excelentes bibliotecas de ciencia de datos

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---
