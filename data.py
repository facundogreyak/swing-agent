"""
data.py - Descarga precios diarios con yfinance y los guarda en la base.
La primera vez baja N años; después solo baja lo que falta.
"""
from datetime import date, timedelta
import pandas as pd
import yfinance as yf
import db


def _ultima_fecha(con, ticker):
    fila = con.execute("SELECT MAX(fecha) FROM precios WHERE ticker=?", (ticker,)).fetchone()
    return fila[0]


def actualizar_ticker(con, ticker: str, anios: int) -> int:
    ultima = _ultima_fecha(con, ticker)
    if ultima:
        desde = (pd.Timestamp(ultima) - timedelta(days=5)).date()   # pequeño solapamiento
    else:
        desde = date.today() - timedelta(days=365 * anios)
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
