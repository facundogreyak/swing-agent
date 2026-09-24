"""
indicadores.py - Cálculo de indicadores técnicos sobre velas diarias.
Entrada: DataFrame con columnas open, high, low, close, volume.
"""
import pandas as pd


def sma(serie: pd.Series, n: int) -> pd.Series:
    return serie.rolling(n).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    """RSI de Wilder (el estándar que muestran TradingView y los brokers)."""
    delta = close.diff()
    suba = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    baja = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = suba / baja
    return 100 - 100 / (1 + rs)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """Average True Range: cuánto se mueve el papel por día, en dólares."""
    prev = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"],
                    (df["high"] - prev).abs(),
                    (df["low"] - prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def agregar_indicadores(df: pd.DataFrame, e: dict, r: dict) -> pd.DataFrame:
    df = df.copy()
    df["sma_rapida"] = sma(df["close"], e["sma_rapida"])
    df["sma_lenta"] = sma(df["close"], e["sma_lenta"])
    df["rsi"] = rsi(df["close"], e["rsi_periodo"])
    df["atr"] = atr(df, r["atr_periodo"])
    df["vol_rel"] = df["volume"] / df["volume"].rolling(20).mean()
    return df
