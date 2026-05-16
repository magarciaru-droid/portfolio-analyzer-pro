import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import sys
import os

# Añadir módulos al path
sys.path.append(os.path.dirname(__file__))

from modules.data_loader import cargar_datos_google_sheets
from modules.price_fetcher import obtener_precios_actuales
from modules.portfolio_analyzer import PortfolioAnalyzer

# ============================================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================================
st.set_page_config(
    page_title="📊 Portfolio Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .gain {color: #28a745;}
    .loss {color: #dc3545;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - CONFIGURACIÓN
# ============================================================================
st.sidebar.title("⚙️ Configuración")
st.sidebar.divider()

# IDs de cartera disponibles
cartera_seleccionada = st.sidebar.text_input(
    "ID de Cartera",
    value="PORT001",
    help="Ingresa el ID de tu cartera (ej: PORT001, PORT002)"
)

# Moneda
moneda = st.sidebar.selectbox(
    "Moneda",
    ["EUR", "USD", "GBP"],
    help="Moneda de tu portafolio"
)

# Tasa libre de riesgo
tasa_libre_riesgo = st.sidebar.slider(
    "Tasa Libre de Riesgo (%)",
    min_value=0.0,
    max_value=5.0,
    value=2.5,
    step=0.1,
    help="Para calcular Sharpe Ratio (típico: 2-3%)"
)

st.sidebar.divider()
st.sidebar.info("""
📌 **Instrucciones:**
1. Ingresa tu ID de Cartera
2. Selecciona la moneda
3. Los datos se actualizarán automáticamente
4. Espera a que se carguen los precios en vivo
""")

# ============================================================================
# CARGAR DATOS
# ============================================================================
st.title("📊 Analizador de Portafolio en Tiempo Real")
st.markdown(f"**Cartera:** {cartera_seleccionada} | **Moneda:** {moneda} | **Última actualización:** {datetime.now().strftime('%H:%M:%S')}")

try:
    # Cargar datos de Google Sheets
    with st.spinner("📥 Cargando datos de Google Sheets..."):
        df_activos = cargar_datos_google_sheets()
    
    # Filtrar por cartera seleccionada
    df_cartera = df_activos[df_activos['ID_Cartera'] == cartera_seleccionada].copy()
    
    if df_cartera.empty:
        st.error(f"❌ No se encontraron activos para la cartera: {cartera_seleccionada}")
        st.stop()
    
    # Obtener precios actuales
    with st.spinner("💹 Actualizando precios en tiempo real..."):
        df_cartera = obtener_precios_actuales(df_cartera)
    
    # Crear analizador
    analyzer = PortfolioAnalyzer(df_cartera, tasa_libre_riesgo)
    resumen = analyzer.calcular_resumen()
    
except Exception as e:
    st.error(f"❌ Error al cargar datos: {str(e)}")
    st.info("💡 Verifica que:")
    st.write("1. Google Sheets está compartida públicamente")
    st.write("2. El ID de Google Sheets está en `config.py`")
    st.write("3. Los tickers son correctos (VANG, MSFT, etc.)")
    st.stop()

# ============================================================================
# MÉTRICAS PRINCIPALES (KPIs)
# ============================================================================
st.subheader("📈 Resumen de Portafolio")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "💰 Valor Total",
        f"{resumen['valor_actual']:.2f} {moneda}",
        delta=f"{resumen['ganancia_perdida']:.2f} {moneda}",
        delta_color="normal"
    )

with col2:
    st.metric(
        "📊 Inversión Total",
        f"{resumen['inversion_total']:.2f} {moneda}",
    )

with col3:
    color_retorno = "normal" if resumen['retorno_porcentaje'] >= 0 else "inverse"
    st.metric(
        "📈 Retorno %",
        f"{resumen['retorno_porcentaje']:.2f}%",
        delta_color=color_retorno
    )

with col4:
    st.metric(
        "📉 Sharpe Ratio",
        f"{resumen['sharpe_ratio']:.2f}",
        help="Mayor es mejor (>1.0 es excelente)"
    )

# ============================================================================
# DETALLES DE ACTIVOS
# ============================================================================
st.divider()
st.subheader("🏦 Detalle de Activos")

# Preparar tabla para mostrar
df_mostrar = df_cartera[[
    'Ticker', 'Tipo_Activo', 'Cantidad', 'Precio_Compra', 
    'Precio_Actual', 'Ganancia_Perdida', 'Retorno_%', 'Valor_Actual'
]].copy()

df_mostrar.columns = ['Ticker', 'Tipo', 'Cantidad', 'P. Compra', 'P. Actual', 'G/P', 'Retorno %', 'Valor $']

# Formatear números
for col in ['P. Compra', 'P. Actual', 'G/P', 'Valor $']:
    df_mostrar[col] = df_mostrar[col].apply(lambda x: f"{x:.2f}")

for col in ['Cantidad', 'Retorno %']:
    df_mostrar[col] = df_mostrar[col].apply(lambda x: f"{x:.2f}" if col == 'Retorno %' else f"{x:.0f}")

st.dataframe(df_mostrar, use_container_width=True)

# ============================================================================
# GRÁFICOS
# ============================================================================
col1, col2 = st.columns(2)

# Gráfico 1: Distribución por Tipo
with col1:
    st.subheader("📊 Distribución por Tipo de Activo")
    distribucion_tipo = df_cartera.groupby('Tipo_Activo')['Valor_Actual'].sum()
    
    fig_tipo = px.pie(
        values=distribucion_tipo.values,
        names=distribucion_tipo.index,
        hole=0.3,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_tipo.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_tipo, use_container_width=True)

# Gráfico 2: Ganancia/Pérdida por Activo
with col2:
    st.subheader("💹 Ganancia/Pérdida por Activo")
    colores = ['green' if x >= 0 else 'red' for x in df_cartera['Ganancia_Perdida']]
    
    fig_barras = go.Figure(data=[
        go.Bar(
            x=df_cartera['Ticker'],
            y=df_cartera['Ganancia_Perdida'],
            marker=dict(color=colores),
            text=df_cartera['Ganancia_Perdida'].apply(lambda x: f"{x:.0f}"),
            textposition='auto'
        )
    ])
    fig_barras.update_layout(
        title="Ganancia/Pérdida por Activo",
        xaxis_title="Activo",
        yaxis_title="Ganancia/Pérdida (€)",
        height=400
    )
    st.plotly_chart(fig_barras, use_container_width=True)

# ============================================================================
# MÉTRICAS DE RIESGO
# ============================================================================
st.divider()
st.subheader("⚠️ Métricas de Riesgo")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📊 Volatilidad",
        f"{resumen['volatilidad']:.2f}%",
        help="Desviación estándar de retornos"
    )

with col2:
    st.metric(
        "📉 Drawdown Máx.",
        f"{resumen['drawdown_maximo']:.2f}%",
        help="Caída máxima desde pico histórico"
    )

with col3:
    st.metric(
        "🎯 Concentración",
        f"{resumen['concentracion']:.2f}%",
        help="Mayor = menos diversificado"
    )

with col4:
    st.metric(
        "✅ Activos",
        f"{len(df_cartera)}",
        help="Número de inversiones"
    )

# ============================================================================
# RECOMENDACIONES BÁSICAS
# ============================================================================
st.divider()
st.subheader("💡 Recomendaciones")

# Diversificación
if resumen['concentracion'] > 40:
    st.warning("⚠️ **Baja Diversificación**: Tu cartera está muy concentrada. Considera diversificar.")
else:
    st.success("✅ **Buena Diversificación**: Tu cartera está bien distribuida.")

# Rentabilidad
if resumen['sharpe_ratio'] > 1.0:
    st.success("✅ **Excelente Ratio de Sharpe**: Tu riesgo vs retorno es óptimo.")
elif resumen['sharpe_ratio'] > 0.5:
    st.info("ℹ️ **Ratio de Sharpe Aceptable**: Considera optimizar.")
else:
    st.warning("⚠️ **Bajo Ratio de Sharpe**: Tu retorno no compensa el riesgo.")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
---
**📌 Nota importante:** Esta aplicación es educativa. No es asesoramiento financiero.
Consulta a un asesor profesional antes de tomar decisiones de inversión.

**🔄 Actualización:** Los precios se actualizan cada vez que recargas la página.
""")
