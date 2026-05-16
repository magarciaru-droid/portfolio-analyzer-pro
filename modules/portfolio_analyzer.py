"""
portfolio_analyzer.py
Calcula métricas financieras profesionales sobre la cartera.
"""

import numpy as np
import pandas as pd

from config import TASA_LIBRE_RIESGO_EUR, SIMBOLO_MONEDA


class PortfolioAnalyzer:
    """
    Dado un DataFrame con precios ya descargados, calcula:
      - KPIs de rentabilidad (valor total, G/P, retorno)
      - Métricas de riesgo (Sharpe, volatilidad, drawdown, concentración)
      - Distribución por tipo de activo
    """

    def __init__(self, df: pd.DataFrame, tasa_rf: float | None = None):
        self.df = df.copy()
        self.tasa_rf = tasa_rf if tasa_rf is not None else TASA_LIBRE_RIESGO_EUR

    # ── Valores base ──────────────────────────────────────────────────────────

    @property
    def valor_actual(self) -> float:
        return float(self.df["Valor_Actual"].sum())

    @property
    def inversion_total(self) -> float:
        return float((self.df["Cantidad"] * self.df["Precio_Compra"]).sum())

    @property
    def ganancia_total(self) -> float:
        return float(self.df["Ganancia_Perdida"].sum())

    @property
    def retorno_pct(self) -> float:
        if self.inversion_total == 0:
            return 0.0
        return self.ganancia_total / self.inversion_total * 100

    # ── Pesos de cartera ──────────────────────────────────────────────────────

    def _pesos(self) -> pd.Series:
        total = self.valor_actual
        if total == 0:
            return pd.Series(0.0, index=self.df.index)
        return self.df["Valor_Actual"] / total

    # ── Riesgo ────────────────────────────────────────────────────────────────

    @property
    def volatilidad(self) -> float:
        """Volatilidad media ponderada de la cartera (% anual)."""
        return float((self.df["Volatilidad_%"].fillna(0) * self._pesos()).sum())

    @property
    def sharpe(self) -> float:
        """
        Sharpe Ratio simplificado con retorno total y volatilidad ponderada.
        Interpretación:
          > 1.5  → excelente
          1-1.5  → muy bueno
          0.5-1  → aceptable
          < 0.5  → optimizar
        """
        vol = self.volatilidad / 100
        if vol == 0:
            return 0.0
        ret = self.retorno_pct / 100
        return round((ret - self.tasa_rf) / vol, 2)

    @property
    def drawdown_maximo(self) -> float:
        """
        Drawdown aproximado: caída desde el coste de compra al valor actual.
        Si la cartera está en positivo devuelve 0.
        """
        if self.valor_actual >= self.inversion_total:
            return 0.0
        dd = (self.inversion_total - self.valor_actual) / self.inversion_total * 100
        return round(min(dd, 100.0), 2)

    @property
    def concentracion(self) -> float:
        """
        Índice Herfindahl-Hirschman (HHI) normalizado a 0-100.
        Mide concentración: a mayor valor, menor diversificación.
        """
        pesos_pct = self._pesos() * 100
        hhi = float((pesos_pct ** 2).sum()) / 100
        return round(hhi, 2)

    # ── Distribución ──────────────────────────────────────────────────────────

    def distribucion_tipo(self) -> pd.DataFrame:
        """DataFrame con Tipo, Valor y % del total."""
        g = self.df.groupby("Tipo_Activo").agg(
            Valor=("Valor_Actual", "sum"),
            Ganancia=("Ganancia_Perdida", "sum"),
            Num_Activos=("Ticker", "count"),
        ).reset_index()
        g["Porcentaje_%"] = (g["Valor"] / g["Valor"].sum() * 100).round(2)
        return g.sort_values("Valor", ascending=False)

    # ── Resumen completo ──────────────────────────────────────────────────────

    def resumen(self) -> dict:
        return {
            "valor_actual":     self.valor_actual,
            "inversion_total":  self.inversion_total,
            "ganancia_total":   self.ganancia_total,
            "retorno_pct":      self.retorno_pct,
            "sharpe":           self.sharpe,
            "volatilidad":      self.volatilidad,
            "drawdown":         self.drawdown_maximo,
            "concentracion":    self.concentracion,
            "num_activos":      len(self.df),
        }

    # ── Recomendaciones automáticas ───────────────────────────────────────────

    def alertas(self) -> list[dict]:
        """
        Devuelve lista de dicts con 'nivel' (info/warning/error) y 'texto'.
        """
        alertas = []
        res = self.resumen()

        # Diversificación
        if res["concentracion"] > 40:
            alertas.append({"nivel": "error",
                             "texto": f"⛔ Concentración muy alta ({res['concentracion']:.1f}). Considera añadir más activos."})
        elif res["concentracion"] > 25:
            alertas.append({"nivel": "warning",
                             "texto": f"⚠️ Concentración moderada ({res['concentracion']:.1f}). Buena idea seguir diversificando."})
        else:
            alertas.append({"nivel": "info",
                             "texto": f"✅ Buena diversificación (HHI {res['concentracion']:.1f})."})

        # Sharpe
        if res["sharpe"] < 0.5:
            alertas.append({"nivel": "warning",
                             "texto": f"⚠️ Sharpe Ratio bajo ({res['sharpe']}). El retorno no compensa bien el riesgo asumido."})
        elif res["sharpe"] > 1.0:
            alertas.append({"nivel": "info",
                             "texto": f"✅ Sharpe Ratio excelente ({res['sharpe']}). Buena relación riesgo/retorno."})

        # Volatilidad
        if res["volatilidad"] > 25:
            alertas.append({"nivel": "warning",
                             "texto": f"⚠️ Volatilidad alta ({res['volatilidad']:.1f}%). La cartera puede tener oscilaciones fuertes."})

        # Activo más pesado
        if len(self.df) > 0:
            top = self.df.loc[self.df["Valor_Actual"].idxmax()]
            peso_top = top["Valor_Actual"] / self.valor_actual * 100 if self.valor_actual > 0 else 0
            if peso_top > 35:
                alertas.append({"nivel": "warning",
                                 "texto": f"⚠️ {top['Ticker']} representa el {peso_top:.1f}% de la cartera. Mucho peso en un solo activo."})

        return alertas

    # ── Formato moneda ────────────────────────────────────────────────────────

    @staticmethod
    def fmt(valor: float) -> str:
        return f"{SIMBOLO_MONEDA}{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
