"""
claude_analyzer.py
Análisis inteligente de cartera usando Claude.

CÓMO ACTIVARLO (Fase 2):
  1. Obtén tu API key en https://console.anthropic.com
  2. En Streamlit Cloud → Settings → Secrets, añade:
       CLAUDE_API_KEY = "sk-ant-api03-..."
  3. En config.py, cambia USAR_CLAUDE_IA = True
  4. Haz commit y la app se actualiza automáticamente.
"""

import streamlit as st
import anthropic
import json


def _cliente_claude():
    """Devuelve el cliente Anthropic usando la API key de Streamlit Secrets."""
    if "CLAUDE_API_KEY" not in st.secrets:
        raise EnvironmentError(
            "No encontré CLAUDE_API_KEY en Streamlit Secrets. "
            "Ve a Settings → Secrets en tu app y añade la clave."
        )
    return anthropic.Anthropic(api_key=st.secrets["CLAUDE_API_KEY"])


def analizar_cartera(resumen: dict, df_activos, distribucion) -> str:
    """
    Solicita a Claude un análisis financiero de la cartera.

    Args:
        resumen:       dict con KPIs (de PortfolioAnalyzer.resumen())
        df_activos:    DataFrame con activos y precios
        distribucion:  DataFrame de distribucion_tipo()

    Returns:
        str con el análisis en texto plano con formato Markdown.
    """
    cliente = _cliente_claude()

    # Preparar contexto conciso para el modelo
    activos_txt = df_activos[["Ticker", "Tipo_Activo", "Cantidad",
                               "Precio_Compra", "Precio_Actual",
                               "Retorno_%", "Valor_Actual"]].to_string(index=False)

    dist_txt = distribucion[["Tipo_Activo", "Porcentaje_%"]].to_string(index=False)

    prompt = f"""
Eres un asesor financiero independiente especializado en carteras minoristas europeas.
Analiza la siguiente cartera de inversión en EUR y proporciona un informe claro, 
estructurado y accionable. NO des consejos de inversión personales ni garantices rentabilidad.

## MÉTRICAS DE LA CARTERA
- Valor actual:       €{resumen['valor_actual']:,.2f}
- Inversión total:    €{resumen['inversion_total']:,.2f}
- Ganancia/Pérdida:   €{resumen['ganancia_total']:,.2f}  ({resumen['retorno_pct']:.2f}%)
- Sharpe Ratio:       {resumen['sharpe']}
- Volatilidad anual:  {resumen['volatilidad']:.1f}%
- Drawdown máximo:    {resumen['drawdown']:.1f}%
- Concentración HHI:  {resumen['concentracion']:.1f}

## ACTIVOS EN CARTERA
{activos_txt}

## DISTRIBUCIÓN POR TIPO
{dist_txt}

## TU INFORME DEBE INCLUIR (en español, en Markdown):

### 1. Diagnóstico general (3-4 frases)
Qué perfil de riesgo refleja esta cartera y si es coherente.

### 2. Puntos fuertes ✅
2-3 cosas que la cartera hace bien.

### 3. Puntos de mejora ⚠️
2-3 aspectos concretos a revisar, con ejemplos de activos o sectores.

### 4. Recomendaciones de rebalanceo 🔄
Sugerencias específicas (sin nombrar fondos concretos), por ejemplo:
  - Reducir peso en X si supera el 40%
  - Añadir exposición a Y para diversificar

### 5. Semáforo de riesgo 🚦
Evalúa de 1 a 5 (1 = muy bajo riesgo, 5 = muy alto) con una línea de justificación.

Sé conciso pero útil. Usa emojis con moderación. Evita jerga innecesaria.
"""

    mensaje = cliente.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    return mensaje.content[0].text


def generar_resumen_rapido(activo: dict) -> str:
    """
    Mini-análisis de un activo individual (para el tooltip de la tabla).

    activo: dict con Ticker, Tipo_Activo, Retorno_%, Volatilidad_%
    """
    cliente = _cliente_claude()

    prompt = (
        f"En máximo 3 frases, explica qué es '{activo['Ticker']}' "
        f"(tipo: {activo['Tipo_Activo']}), cómo ha rentado ({activo['Retorno_%']:.1f}%) "
        f"y si su volatilidad ({activo['Volatilidad_%']:.1f}%) es alta o baja. "
        "Responde en español, sin tecnicismos excesivos."
    )

    res = cliente.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return res.content[0].text
