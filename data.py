"""
data.py - Descarga precios diarios con yfinance y los guarda en la base.
La primera vez baja N años; después solo baja lo que falta.
"""
from datetime import date, timedelta
from pathlib import Path
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


def universo_ampliado(cfg: dict) -> list:
    """Universo base + las acciones de universo_ampliado.csv (todas con CEDEAR en BYMA)."""
    base = list(cfg["universo"])
    archivo = Path("universo_ampliado.csv")
    if not archivo.exists():
        return base
    ya = {p["subyacente"] for p in base}
    extra = pd.read_csv(archivo).to_dict("records")
    return base + [p for p in extra if p["subyacente"] not in ya]


def actualizar_todo(con, cfg: dict):
    anios = cfg["datos"]["historia_anios"]
    tickers = [cfg["benchmark"], cfg.get("benchmark_cedear", {}).get("cedear")]
    for par in cfg["universo"]:
        tickers += [par["subyacente"], par["cedear"]]
    # universo ampliado: el subyacente siempre (para comparar en el backtest); el CEDEAR solo si se usa
    usa_ampliado = cfg.get("momentum", {}).get("universo") == "ampliado"
    for par in universo_ampliado(cfg)[len(cfg["universo"]):]:
        tickers += [par["subyacente"]] + ([par["cedear"]] if usa_ampliado else [])
    # CEDEARs con símbolo dudoso en Yahoo: se prueban alternativas y se usa la que tenga datos
    for par in cfg["universo"]:
        tickers += par.get("cedear_alternativos", [])
    tickers = [t for t in dict.fromkeys(tickers) if t]
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
