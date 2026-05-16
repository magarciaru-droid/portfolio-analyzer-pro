# ============================================================================
# CONFIGURACIÓN PRINCIPAL DE LA APP
# ============================================================================

# ⚠️ IMPORTANTE: Actualiza esto con tus datos
GOOGLE_SHEETS_ID = "1MvoQriR5I-u3KF-Um2c6WYvR3zBaNNtIYU4bXx8hYo8"
# Extrae de la URL: https://docs.google.com/spreadsheets/d/1MvoQriR5I-u3KF-Um2c6WYvR3zBaNNtIYU4bXx8hYo8/edit

# Nombres de las hojas en tu Google Sheet
HOJA_ACTIVOS = "Activos"
HOJA_RENDIMIENTO = "Rendimiento_Cuentas"

# Configuración de Yahoo Finance
TIMEOUT_YFINANCE = 30  # segundos

# Configuración de cálculos
TASA_LIBRE_RIESGO_DEFECTO = 0.025  # 2.5%
DIAS_HISTORICO = 252  # Días de mercado en un año

# ============================================================================
# MONEDAS SOPORTADAS
# ============================================================================
MONEDAS_SOPORTADAS = {
    "EUR": "€",
    "USD": "$",
    "GBP": "£"
}

# ============================================================================
# TIPOS DE ACTIVOS
# ============================================================================
TIPOS_ACTIVOS_VALIDOS = [
    "ETF",
    "Accion",
    "Fondo",
    "Cuenta_Remunerada"
]

# ============================================================================
# CONFIGURACIÓN PARA CLAUDE IA (OPCIONAL)
# ============================================================================
# Si quieres usar análisis con IA, obtén tu API key en:
# https://console.anthropic.com
USAR_CLAUDE_IA = False  # Cambia a True cuando tengas la API key
CLAUDE_API_KEY = None  # Se cargará de Streamlit Secrets en producción

# ============================================================================
# COLORES PARA GRÁFICOS
# ============================================================================
COLOR_GANANCIA = "#28a745"
COLOR_PERDIDA = "#dc3545"
COLOR_NEUTRAL = "#6c757d"
