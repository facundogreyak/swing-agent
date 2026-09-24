"""
estrategia.py - Reglas de entrada del agente.

Se elige con `estrategia.entrada` en config.yaml:

"retroceso"  -> comprar el retroceso dentro de una tendencia alcista
  1. Tendencia:  precio > SMA lenta  y  SMA rápida > SMA lenta
  2. Retroceso:  el RSI estuvo por debajo de `rsi_entrada_max` en las últimas 3 ruedas
  3. Rebote:     hoy el RSI sube y el cierre supera al de ayer (si rsi_confirmacion)
  4. Volumen:    volumen de hoy >= volumen_min_rel x promedio de 20 ruedas

"ruptura_N"  -> comprar cuando el precio rompe su máximo de N ruedas (ej. ruptura_20, ruptura_55)
  1. Tendencia:  igual que arriba
  2. Ruptura:    cierre de hoy > máximo de las N ruedas anteriores
  3. Volumen:    igual que arriba

La señal se calcula con el CIERRE del día; la compra se simula en la
APERTURA del día siguiente (así no usamos información del futuro).
"""
import pandas as pd
from indicadores import agregar_indicadores


def entradas_usadas(cfg: dict) -> set:
    """Tipos de entrada que hay que calcular (la configurada + las de la grilla de calibración)."""
    tipos = {cfg["estrategia"].get("entrada", "retroceso")}
    tipos |= set(cfg.get("backtest", {}).get("grilla", {}).get("entrada", []))
    return tipos


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

    d["senal_retroceso"] = d[["c_tendencia", "c_retroceso", "c_rebote", "c_volumen"]].all(axis=1)
    d["prio_retroceso"] = d["rsi"]                        # menor RSI = retroceso más profundo = primero
    for tipo in entradas_usadas(cfg):
        if tipo.startswith("ruptura_"):
            n = int(tipo.split("_")[1])
            d[f"maximo_{n}"] = d["high"].shift(1).rolling(n).max()
            d[f"c_{tipo}"] = d["close"] > d[f"maximo_{n}"]
            d[f"senal_{tipo}"] = d["c_tendencia"] & d[f"c_{tipo}"] & d["c_volumen"]
            d[f"prio_{tipo}"] = -d["vol_rel"]              # mayor volumen relativo = primero
    tipo = e.get("entrada", "retroceso")
    d["senal_compra"] = d[f"senal_{tipo}"]
    # Stop y objetivo de referencia (se recalculan con el precio real de entrada)
    d["stop_ref"] = d["close"] - r["stop_atr"] * d["atr"]
    return d


def motivo(fila, entrada: str = "retroceso") -> str:
    """Texto legible para el diario de decisiones."""
    partes = ["tendencia alcista" if fila.c_tendencia else "sin tendencia alcista"]
    if entrada == "retroceso":
        partes += [
            f"RSI retrocedió ({fila.rsi:.0f})" if fila.c_retroceso else f"sin retroceso (RSI {fila.rsi:.0f})",
            "rebote confirmado" if fila.c_rebote else "sin rebote",
        ]
    else:
        n = int(entrada.split("_")[1])
        maximo = getattr(fila, f"maximo_{n}")
        partes.append(f"rompió máximo de {n} ruedas ({maximo:.2f})" if getattr(fila, f"c_{entrada}")
                      else f"debajo del máximo de {n} ruedas ({maximo:.2f})")
    partes.append(f"volumen {fila.vol_rel:.1f}x" if fila.c_volumen else f"volumen bajo ({fila.vol_rel:.1f}x)")
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


def regimen_mercado(bench: pd.DataFrame, n: int = 200) -> pd.Series:
    """True los días en que el benchmark (SPY) cierra por encima de su media de n ruedas."""
    return bench["close"] > bench["close"].rolling(n).mean()
