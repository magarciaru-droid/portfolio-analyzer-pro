"""
price_fetcher.py
Descarga precios actuales e históricos de Yahoo Finance.
Pensado para carteras en EUR con activos de bolsas europeas y americanas.
"""

import time
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta

from config import CACHE_PRECIOS_SEG


# ── Precio actual ──────────────────────────────────────────────────────────────

def _precio_yahoo(ticker: str) -> dict:
    """
    Descarga el precio de cierre más reciente de Yahoo Finance.
    Devuelve dict con 'precio', 'moneda', 'error'.
    """
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")   # 5 días para evitar festivos
        if hist.empty:
            return {"precio": None, "moneda": "EUR", "error": f"Sin datos para {ticker}"}
        precio = float(hist["Close"].iloc[-1])
        try:
            moneda = t.info.get("currency", "EUR")
        except Exception:
            moneda = "EUR"
        return {"precio": precio, "moneda": moneda, "error": None}
    except Exception as e:
        return {"precio": None, "moneda": "EUR", "error": str(e)}


def precio_cuenta_remunerada(saldo: float, rendimiento_pct: float,
                              fecha_apertura: str) -> dict:
    """
    Calcula el valor actual de una cuenta remunerada con interés simple.
    Rendimiento_Fijo_% = TAE anual (ej: 3.5 para 3,5 %).
    """
    try:
        apertura = pd.to_datetime(fecha_apertura)
        dias = (datetime.now() - apertura).days
        tae  = rendimiento_pct / 100
        valor_actual = saldo * (1 + tae * dias / 365)
        return {"precio": valor_actual / max(saldo, 1), "moneda": "EUR", "error": None}
    except Exception:
        return {"precio": 1.0, "moneda": "EUR", "error": None}


# ── Histórico (para métricas de riesgo) ───────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)   # refresca cada hora
def historico_retornos(ticker: str, periodo: str = "1y") -> pd.Series:
    """
    Devuelve la serie de retornos diarios del último año.
    Devuelve Series vacía si falla.
    """
    if ticker.startswith("CUENTA_"):
        return pd.Series(dtype=float)
    try:
        hist = yf.download(ticker, period=periodo, progress=False, auto_adjust=True)
        if hist.empty:
            return pd.Series(dtype=float)
        return hist["Close"].pct_change().dropna()
    except Exception:
        return pd.Series(dtype=float)


# ── Función principal ─────────────────────────────────────────────────────────

def obtener_precios_actuales(df_cartera: pd.DataFrame,
                             df_cuentas: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Enriquece df_cartera con columnas calculadas:
      Precio_Actual | Valor_Actual | Ganancia_Perdida | Retorno_% | Volatilidad_%

    df_cuentas: hoja Rendimiento_Cuentas (para calcular interés real en cuentas).
    """
    df = df_cartera.copy()

    # Columnas nuevas
    for col in ["Precio_Actual", "Valor_Actual", "Ganancia_Perdida",
                "Retorno_%", "Volatilidad_%"]:
        df[col] = 0.0

    barra = st.progress(0, text="Descargando precios…")

    for i, (idx, row) in enumerate(df.iterrows()):
        ticker  = str(row["Ticker"]).strip()
        tipo    = str(row["Tipo_Activo"]).strip()
        cant    = float(row["Cantidad"])
        p_comp  = float(row["Precio_Compra"])

        # ── Precio actual según tipo
        if tipo == "Cuenta_Remunerada":
            rend = 0.0
            if df_cuentas is not None and not df_cuentas.empty:
                fila = df_cuentas[df_cuentas["Nombre_Cuenta"] == ticker]
                if not fila.empty:
                    rend = float(fila.iloc[0].get("Rendimiento_Fijo_%", 0))
            fecha_ap = str(row.get("Fecha_Compra", datetime.now().date()))
            res = precio_cuenta_remunerada(cant * p_comp, rend, fecha_ap)
        else:
            res = _precio_yahoo(ticker)
            time.sleep(0.15)   # cortesía con Yahoo

        if res["error"]:
            st.warning(f"⚠️ {ticker}: {res['error']} — usando precio de compra como referencia.")
            p_actual = p_comp
        else:
            p_actual = res["precio"]

        # ── Cálculos financieros
        valor_actual    = cant * p_actual
        ganancia        = valor_actual - (cant * p_comp)
        retorno_pct     = (ganancia / (cant * p_comp) * 100) if p_comp > 0 else 0.0

        # Volatilidad histórica anualizada
        ret_hist = historico_retornos(ticker if tipo != "Cuenta_Remunerada" else "CUENTA_")
        volatilidad = float(ret_hist.std() * np.sqrt(252) * 100) if len(ret_hist) > 20 else 0.0

        df.at[idx, "Precio_Actual"]   = p_actual
        df.at[idx, "Valor_Actual"]    = valor_actual
        df.at[idx, "Ganancia_Perdida"] = ganancia
        df.at[idx, "Retorno_%"]       = retorno_pct
        df.at[idx, "Volatilidad_%"]   = volatilidad

        barra.progress((i + 1) / len(df), text=f"Cargando {ticker}…")

    barra.empty()
    return df
