# ==============================================================================
# CONFIGURACIÓN PRINCIPAL — Portfolio Analyzer (versión EUR)
# ==============================================================================
# ⚠️  ÚNICA LÍNEA QUE DEBES CAMBIAR AL PRINCIPIO:
GOOGLE_SHEETS_ID = "Um2c6WYvR3zBaNNtIYU4bXx8hYo8"
# Ejemplo: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
# Lo encuentras en la URL: docs.google.com/spreadsheets/d/ESTE_TROZO/edit

# Nombres exactos de las hojas (deben coincidir con Google Sheets)
HOJA_ACTIVOS           = "Activos"
HOJA_RENDIMIENTO       = "Rendimiento_Cuentas"

# Moneda base
MONEDA_BASE            = "EUR"
SIMBOLO_MONEDA         = "€"

# Mercado europeo: añadir .MC (Madrid), .PA (París), .DE (Frankfurt) según el activo
# Ejemplos de tickers válidos en Yahoo Finance:
#   BBVA.MC   → BBVA en Bolsa de Madrid
#   SAN.MC    → Santander en Madrid
#   VUSA.L    → Vanguard S&P500 en Londres
#   EQQQ.L    → Invesco QQQ en Londres
#   MSFT      → Microsoft en NASDAQ (cotiza en USD)
#   BRK.B     → Berkshire Hathaway (USD)
MERCADO_POR_DEFECTO    = "MC"  # Madrid

# Tipos de activo reconocidos por la app
TIPOS_ACTIVOS_VALIDOS  = ["ETF", "Accion", "Fondo", "Cuenta_Remunerada"]

# Cálculos de riesgo
TASA_LIBRE_RIESGO_EUR  = 0.035   # ~3.5 % (euríbor/deuda alemana 2024)
DIAS_MERCADO_ANYO      = 252     # días hábiles de mercado

# Caché de precios (segundos). 300 = refresca cada 5 minutos
CACHE_PRECIOS_SEG      = 300

# ==============================================================================
# CLAUDE IA — desactivado por defecto; actívalo en Fase 2
# ==============================================================================
USAR_CLAUDE_IA         = False   # Cambia a True cuando tengas la API key
MODELO_CLAUDE          = "claude-sonnet-4-20250514"
MAX_TOKENS_ANALISIS    = 1500
