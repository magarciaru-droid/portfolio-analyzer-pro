"""
data_loader.py
Lee los datos de cartera desde Google Sheets.
Soporta dos modos de autenticación:
  1. Streamlit Secrets (producción en Streamlit Cloud)
  2. Hoja pública por URL CSV (modo sencillo sin credenciales)
"""

import pandas as pd
import streamlit as st
from config import GOOGLE_SHEETS_ID, HOJA_ACTIVOS, HOJA_RENDIMIENTO, TIPOS_ACTIVOS_VALIDOS


# ── Helpers ──────────────────────────────────────────────────────────────────

def _url_csv(sheet_id: str, hoja: str) -> str:
    """Devuelve la URL de exportación CSV de una hoja concreta."""
    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        f"/gviz/tq?tqx=out:csv&sheet={hoja}"
    )


def _leer_csv_publico(sheet_id: str, hoja: str) -> pd.DataFrame:
    """Lee una hoja pública directamente como CSV (sin credenciales)."""
    url = _url_csv(sheet_id, hoja)
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        raise ConnectionError(
            f"No se pudo leer la hoja «{hoja}».\n"
            f"¿Está compartida públicamente? URL intentada: {url}\n"
            f"Error: {e}"
        )


def _leer_con_gspread(sheet_id: str, hoja: str) -> pd.DataFrame:
    """Lee usando credenciales de Streamlit Secrets (para hojas privadas)."""
    import gspread
    from google.oauth2.service_account import Credentials

    creds_dict = dict(st.secrets["GOOGLE_SHEETS_CREDENTIALS"])
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(sheet_id).worksheet(hoja)
    data = ws.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
    return df


# ── Función principal ─────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def cargar_datos_google_sheets() -> pd.DataFrame:
    """
    Devuelve un DataFrame con la hoja «Activos».

    Columnas esperadas:
      ID_Cartera | Ticker | Cantidad | Precio_Compra | Tipo_Activo | Fecha_Compra

    Intenta primero lectura pública (CSV), luego gspread si falla.
    """
    # — Intentar lectura pública (la más sencilla para principiantes)
    try:
        df = _leer_csv_publico(GOOGLE_SHEETS_ID, HOJA_ACTIVOS)
    except ConnectionError:
        # — Fallback: credenciales en Secrets
        if "GOOGLE_SHEETS_CREDENTIALS" not in st.secrets:
            raise ConnectionError(
                "No se pudo leer la hoja en modo público y tampoco hay "
                "credenciales en Streamlit Secrets. "
                "Asegúrate de compartir la hoja con 'Cualquiera con el enlace'."
            )
        df = _leer_con_gspread(GOOGLE_SHEETS_ID, HOJA_ACTIVOS)

    # — Validar columnas mínimas
    columnas_requeridas = [
        "ID_Cartera", "Ticker", "Cantidad", "Precio_Compra", "Tipo_Activo"
    ]
    for col in columnas_requeridas:
        if col not in df.columns:
            raise ValueError(
                f"Falta la columna «{col}» en la hoja Activos. "
                f"Columnas encontradas: {list(df.columns)}"
            )

    # — Limpieza y tipado
    df["Cantidad"]      = pd.to_numeric(df["Cantidad"],      errors="coerce").fillna(0)
    df["Precio_Compra"] = pd.to_numeric(df["Precio_Compra"], errors="coerce").fillna(0)

    # Normalizar tipo de activo (mayúsculas / espacios)
    df["Tipo_Activo"] = df["Tipo_Activo"].str.strip()

    # Filtrar filas vacías
    df = df[df["Ticker"].astype(str).str.strip() != ""]
    df = df[df["Cantidad"] > 0]

    if df.empty:
        raise ValueError("La hoja «Activos» no tiene filas con datos válidos.")

    return df.reset_index(drop=True)


@st.cache_data(ttl=300, show_spinner=False)
def cargar_rendimiento_cuentas() -> pd.DataFrame:
    """
    Devuelve la hoja «Rendimiento_Cuentas» o un DataFrame vacío si no existe.
    """
    try:
        df = _leer_csv_publico(GOOGLE_SHEETS_ID, HOJA_RENDIMIENTO)
        df["Saldo_Inicial"]      = pd.to_numeric(df.get("Saldo_Inicial", 0),      errors="coerce").fillna(0)
        df["Rendimiento_Fijo_%"] = pd.to_numeric(df.get("Rendimiento_Fijo_%", 0), errors="coerce").fillna(0)
        return df
    except Exception:
        return pd.DataFrame()


def obtener_carteras_disponibles(df: pd.DataFrame) -> list:
    """Devuelve la lista de IDs de cartera únicos."""
    return sorted(df["ID_Cartera"].unique().tolist())
