"""
app_pro.py — Portfolio Analyzer PRO
Versión con imports robustos para Streamlit Cloud.
"""

import sys
import os

# ── FIX: Añadir la raíz del proyecto al path de Python ──────────────────────
# En Streamlit Cloud el working directory puede variar; esta línea lo resuelve.
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# ────────────────────────────────────────────────────────────────────────────

import streamlit as st

# Verificación rápida de estructura antes de importar
def _verificar_estructura():
    modulos_requeridos = [
        "modules/__init__.py",
        "modules/data_loader.py",
        "modules/price_fetcher.py",
        "modules/portfolio_analyzer.py",
    ]
    faltantes = [m for m in modulos_requeridos if not os.path.exists(os.path.join(ROOT, m))]
    if faltantes:
        st.error("❌ Faltan archivos en el repositorio:")
        for f in faltantes:
            st.code(f)
        st.info(
            "**Solución:**\n"
            "1. Comprueba que la carpeta `modules/` esté en la raíz de tu repositorio GitHub\n"
            "2. Comprueba que `modules/__init__.py` existe (puede estar vacío)\n"
            "3. Haz un nuevo commit con todos los archivos"
        )
        st.stop()

_verificar_estructura()

# ── Imports de módulos propios (ya seguros tras la verificación) ────────────
from modules.data_loader        import cargar_datos_google_sheets, cargar_rendimiento_cuentas, obtener_carteras_disponibles
from modules.price_fetcher      import obtener_precios_actuales
from modules.portfolio_analyzer import PortfolioAnalyzer

# Config
try:
    from config import (
        SIMBOLO_MONEDA, MONEDA_BASE,
        TASA_LIBRE_RIESGO_EUR, USAR_CLAUDE_IA,
    )
except ModuleNotFoundError:
    st.error("❌ No se encuentra `config.py`. Asegúrate de que está en la raíz del repositorio.")
    st.stop()

if USAR_CLAUDE_IA:
    try:
        from modules.claude_analyzer import analizar_cartera
    except ImportError as e:
        st.warning(f"⚠️ Claude IA activado pero no se pudo cargar: {e}")
        USAR_CLAUDE_IA = False

# ── Resto de imports estándar ────────────────────────────────────────────────
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Portfolio Analyzer · EUR",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  #MainMenu {visibility: hidden;}
  footer    {visibility: hidden;}
  .block-container {padding-top: 1.5rem;}
  [data-testid="stMetricDeltaIcon-Up"]   { color: #2ecc71 !important; }
  [data-testid="stMetricDeltaIcon-Down"] { color: #e74c3c !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("⚙️ Portfolio Analyzer")
    st.caption(f"Moneda base: {MONEDA_BASE}")
    st.divider()

    try:
        with st.spinner("Leyendo Google Sheets…"):
            df_raw     = cargar_datos_google_sheets()
            df_cuentas = cargar_rendimiento_cuentas()
        carteras = obtener_carteras_disponibles(df_raw)
    except ConnectionError as e:
        st.error(f"❌ No se puede leer Google Sheets:\n\n{e}")
        st.info(
            "**Pistas rápidas:**\n"
            "1. ¿Está la hoja compartida con 'Cualquiera con el enlace'?\n"
            "2. ¿Es correcto el `GOOGLE_SHEETS_ID` en `config.py`?\n"
            "3. ¿Los nombres de las hojas son exactamente «Activos» y «Rendimiento_Cuentas»?"
        )
        st.stop()
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")
        st.stop()

    cartera_id = st.selectbox("🗂️ Cartera", carteras)

    tasa_rf = st.slider(
        "Tasa libre de riesgo (%)",
        0.0, 6.0,
        value=float(TASA_LIBRE_RIESGO_EUR * 100),
        step=0.1,
    )

    st.divider()
    if st.button("🔄 Actualizar precios", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"Actualizado: {datetime.now().strftime('%H:%M:%S')}")

    with st.expander("ℹ️ Tickers válidos"):
        st.markdown("""
| Mercado | Ejemplo |
|---|---|
| Madrid | `BBVA.MC` `SAN.MC` |
| Londres | `VUSA.L` `VWRL.L` |
| NASDAQ | `MSFT` `AAPL` |
| Cuenta | cualquier nombre |
        """)


# ══════════════════════════════════════════════════════════════════════════════
# DATOS
# ══════════════════════════════════════════════════════════════════════════════

df_cartera = df_raw[df_raw["ID_Cartera"] == cartera_id].copy()
if df_cartera.empty:
    st.warning(f"La cartera **{cartera_id}** no tiene activos. Añádelos en Google Sheets.")
    st.stop()

with st.spinner("💹 Descargando precios…"):
    df_cartera = obtener_precios_actuales(df_cartera, df_cuentas)

analyzer = PortfolioAnalyzer(df_cartera, tasa_rf=tasa_rf / 100)
res      = analyzer.resumen()
dist     = analyzer.distribucion_tipo()
alertas  = analyzer.alertas()


# ══════════════════════════════════════════════════════════════════════════════
# CABECERA
# ══════════════════════════════════════════════════════════════════════════════

st.title(f"📊 Cartera: {cartera_id}")
st.caption(
    f"{len(df_cartera)} activos · "
    f"{MONEDA_BASE} · "
    f"Cotización: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
)

for a in alertas:
    getattr(st, a["nivel"] if a["nivel"] != "error" else "error")(a["texto"])


# ══════════════════════════════════════════════════════════════════════════════
# KPIs
# ══════════════════════════════════════════════════════════════════════════════

st.subheader("📈 Rentabilidad")
c1, c2, c3, c4 = st.columns(4)
c1.metric("💼 Valor actual",   f"{SIMBOLO_MONEDA}{res['valor_actual']:,.2f}",
          delta=f"{SIMBOLO_MONEDA}{res['ganancia_total']:,.2f}")
c2.metric("📥 Inversión",      f"{SIMBOLO_MONEDA}{res['inversion_total']:,.2f}")
c3.metric("📊 Retorno total",  f"{res['retorno_pct']:+.2f}%")
c4.metric("⚖️ Sharpe Ratio",   f"{res['sharpe']:.2f}",
          help="> 1 = excelente")

st.subheader("⚠️ Riesgo")
r1, r2, r3, r4 = st.columns(4)
r1.metric("📉 Volatilidad",    f"{res['volatilidad']:.1f}%")
r2.metric("🕳️ Drawdown máx.",  f"{res['drawdown']:.1f}%")
r3.metric("🎯 Concentración",  f"{res['concentracion']:.1f}")
r4.metric("🔢 Activos",        str(res["num_activos"]))


# ══════════════════════════════════════════════════════════════════════════════
# DETALLE
# ══════════════════════════════════════════════════════════════════════════════

st.divider()
st.subheader("📋 Detalle de activos")

df_vista = df_cartera[[
    "Ticker", "Tipo_Activo", "Cantidad",
    "Precio_Compra", "Precio_Actual",
    "Ganancia_Perdida", "Retorno_%", "Valor_Actual",
]].rename(columns={
    "Tipo_Activo":     "Tipo",
    "Precio_Compra":   "P. Compra",
    "Precio_Actual":   "P. Actual",
    "Ganancia_Perdida":"G/P (€)",
    "Retorno_%":       "Ret. %",
    "Valor_Actual":    "Valor (€)",
})

def _color_gp(v):
    try:
        c = "#2ecc71" if float(v) >= 0 else "#e74c3c"
        return f"color:{c};font-weight:600"
    except Exception:
        return ""

st.dataframe(
    df_vista.style
        .format({"P. Compra": "{:.2f}", "P. Actual": "{:.2f}",
                 "G/P (€)": "{:+.2f}", "Ret. %": "{:+.2f}",
                 "Valor (€)": "{:,.2f}", "Cantidad": "{:.0f}"})
        .applymap(_color_gp, subset=["G/P (€)", "Ret. %"]),
    use_container_width=True,
    hide_index=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# GRÁFICOS
# ══════════════════════════════════════════════════════════════════════════════

st.divider()
st.subheader("📊 Visualizaciones")

g1, g2 = st.columns(2)

with g1:
    st.caption("**Peso por tipo de activo**")
    fig = px.pie(dist, values="Valor", names="Tipo_Activo", hole=0.45,
                 color_discrete_sequence=px.colors.qualitative.Safe)
    fig.update_traces(textposition="inside", texttemplate="%{label}<br>%{percent:.1%}")
    fig.update_layout(showlegend=False, margin=dict(t=5,b=5,l=5,r=5), height=300)
    st.plotly_chart(fig, use_container_width=True)

with g2:
    st.caption("**Ganancia / Pérdida por activo (€)**")
    dbar = df_cartera.sort_values("Ganancia_Perdida")
    fig2 = go.Figure(go.Bar(
        x=dbar["Ganancia_Perdida"], y=dbar["Ticker"], orientation="h",
        marker_color=["#2ecc71" if v >= 0 else "#e74c3c" for v in dbar["Ganancia_Perdida"]],
        text=dbar["Ganancia_Perdida"].apply(lambda v: f"€{v:+,.2f}"),
        textposition="outside",
    ))
    fig2.update_layout(xaxis_title="G/P (€)", yaxis_title="",
                       margin=dict(t=5,b=5,l=5,r=60), height=300)
    st.plotly_chart(fig2, use_container_width=True)

st.caption("**Peso de cada activo (%)**")
dpeso = df_cartera.copy()
dpeso["Peso_%"] = (dpeso["Valor_Actual"] / dpeso["Valor_Actual"].sum() * 100).round(2)
fig3 = px.bar(dpeso.sort_values("Peso_%", ascending=False),
              x="Ticker", y="Peso_%", color="Tipo_Activo",
              text="Peso_%", color_discrete_sequence=px.colors.qualitative.Safe)
fig3.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig3.update_layout(yaxis_title="Peso (%)", xaxis_title="",
                   margin=dict(t=5,b=5), height=300)
st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# CLAUDE IA
# ══════════════════════════════════════════════════════════════════════════════

st.divider()
if USAR_CLAUDE_IA:
    st.subheader("🤖 Análisis con Claude")
    if st.button("✨ Generar análisis IA", use_container_width=True):
        with st.spinner("Claude analizando tu cartera…"):
            try:
                st.markdown(analizar_cartera(res, df_cartera, dist))
            except Exception as e:
                st.error(f"Error llamando a Claude: {e}")
else:
    st.info(
        "🤖 **Análisis con Claude IA — Fase 2.**  \n"
        "Cuando tengas tu API key: añádela en Streamlit Secrets y cambia "
        "`USAR_CLAUDE_IA = True` en `config.py`."
    )

with st.expander("📚 Glosario"):
    st.markdown("""
| Métrica | Qué mide | Referencia |
|---|---|---|
| **Sharpe Ratio** | Retorno por unidad de riesgo | > 1.0 = excelente |
| **Volatilidad** | Oscilación anual de precios | 10-20% = equilibrada |
| **Drawdown máx.** | Caída desde precio de compra | Menor = mejor |
| **Concentración HHI** | Riesgo de concentración | < 15 = diversificada |

*Aplicación educativa. No constituye asesoramiento financiero.*
    """)

st.caption(
    f"Portfolio Analyzer · Yahoo Finance · Google Sheets · {MONEDA_BASE} · "
    "Precios con ~15 min de retraso en mercados diferidos."
)
