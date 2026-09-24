"""
estrategia.py - Reglas de entrada del agente (Etapa 2).

Idea: "comprar el retroceso dentro de una tendencia alcista".
  1. Tendencia:  precio > SMA lenta  y  SMA rápida > SMA lenta
  2. Retroceso:  el RSI estuvo por debajo de `rsi_entrada_max` en las últimas 3 ruedas
  3. Rebote:     hoy el RSI sube y el cierre supera al de ayer (si rsi_confirmacion)
  4. Volumen:    volumen de hoy >= volumen_min_rel x promedio de 20 ruedas

La señal se calcula con el CIERRE del día; la compra se simula en la
APERTURA del día siguiente (así no usamos información del futuro).
"""
import pandas as pd
from indicadores import agregar_indicadores


def evaluar(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    e, r = cfg["estrategia"], cfg["riesgo"]
    d = agregar_indicadores(df, e, r)

    d["c_tendencia"] = (d["close"] > d["sma_lenta"]) & (d["sma_rapida"] > d["sma_lenta"])
    d["c_retroceso"] = (d["rsi"].rolling(3).min() < e["rsi_entrada_max"])
    if e.get("rsi_confirmacion", True):
        d["c_rebote"] = (d["rsi"] > d["rsi"].shift(1)) & (d["close"] > d["close"].shift(1))
    else:
        d["c_rebote"] = True
    d["c_volumen"] = d["vol_rel"] >= e["volumen_min_rel"]

    d["senal_compra"] = d[["c_tendencia", "c_retroceso", "c_rebote", "c_volumen"]].all(axis=1)
    # Stop y objetivo de referencia (se recalculan con el precio real de entrada)
    d["stop_ref"] = d["close"] - r["stop_atr"] * d["atr"]
    return d


def motivo(fila) -> str:
    """Texto legible para el diario de decisiones."""
    partes = [
        ("tendencia alcista" if fila.c_tendencia else "sin tendencia alcista"),
        (f"RSI retrocedió ({fila.rsi:.0f})" if fila.c_retroceso else f"sin retroceso (RSI {fila.rsi:.0f})"),
        ("rebote confirmado" if fila.c_rebote else "sin rebote"),
        (f"volumen {fila.vol_rel:.1f}x" if fila.c_volumen else f"volumen bajo ({fila.vol_rel:.1f}x)"),
    ]
    return "; ".join(partes)


def tamano_posicion(capital, entrada, stop, riesgo_pct, efectivo, max_pct_posicion):
    """Cantidad (en acciones del subyacente; admite fracciones porque un CEDEAR
    es una fracción de la acción) para que, si toca el stop, se pierda
    `riesgo_pct` del capital. Topes: el efectivo disponible y el % máximo por posición."""
    riesgo_por_accion = entrada - stop
    if riesgo_por_accion <= 0 or entrada <= 0:
        return 0.0
    cantidad = capital * riesgo_pct / riesgo_por_accion
    cantidad = min(cantidad, capital * max_pct_posicion / entrada, efectivo / entrada)
    return round(max(cantidad, 0.0), 4)
