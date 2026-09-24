"""
data.py - Descarga precios diarios con yfinance y los guarda en la base.
La primera vez baja N años; después solo baja lo que falta.
"""
from datetime import date, timedelta
import pandas as pd
import yfinance as yf
import db


def _rango(con, ticker):
    return con.execute("SELECT MIN(fecha), MAX(fecha) FROM precios WHERE ticker=?", (ticker,)).fetchone()


def actualizar_ticker(con, ticker: str, anios: int) -> int:
    inicio_deseado = date.today() - timedelta(days=365 * anios)
    primera, ultima = _rango(con, ticker)
    # Si ya tenemos la historia completa, bajar solo lo que falta.
    # Si falta historia (p. ej. se amplió historia_anios), bajar todo de nuevo.
    if ultima and pd.Timestamp(primera).date() <= inicio_deseado + timedelta(days=15):
        desde = (pd.Timestamp(ultima) - timedelta(days=5)).date()   # pequeño solapamiento
    else:
        desde = inicio_deseado
    df = yf.download(ticker, start=desde, progress=False, auto_adjust=True)
    if df is None or df.empty:
        return 0
    if isinstance(df.columns, pd.MultiIndex):        # yfinance nuevo devuelve 2 niveles
        df.columns = df.columns.get_level_values(0)
    df = df.dropna(subset=["Close"])
    return db.guardar_precios(con, ticker, df)


def actualizar_todo(con, cfg: dict):
    anios = cfg["datos"]["historia_anios"]
    tickers = [cfg["benchmark"]]
    for par in cfg["universo"]:
        tickers += [par["subyacente"], par["cedear"]]
    resumen = []
    for t in tickers:
        try:
            n = actualizar_ticker(con, t, anios)
            resumen.append((t, n, "OK" if n else "SIN DATOS"))
        except Exception as e:
            resumen.append((t, 0, f"ERROR: {e}"))
        print(f"  {t:10s} {resumen[-1][2]:10s} {resumen[-1][1]} velas")
    return resumen


def cargar_precios(con, ticker: str) -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM precios WHERE ticker=? ORDER BY fecha", con,
                     params=(ticker,), parse_dates=["fecha"])
    return df.set_index("fecha")
