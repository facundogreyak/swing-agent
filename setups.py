"""
setups.py - Screener de "setups" de swing trading que usan traders conocidos, y cuánto rindieron.

Setups (reglas públicas, adaptadas a datos diarios):
  RS Rating (estilo IBD / Minervini): fuerza relativa 1-99 contra todo el universo.
      puntaje = 2 x retorno 3 meses + retorno 6 + retorno 9 + retorno 12 meses  -> percentil.
  Trend Template (Mark Minervini): acción en "etapa 2" (tendencia alcista sana):
      precio > SMA50 > SMA150 > SMA200 · SMA200 subiendo hace 1 mes · >= 30% arriba del mínimo de 52 semanas
      · a menos de 25% del máximo de 52 semanas · RS Rating >= 70.
  Breakout (Kristjan Kullamägi, "Qullamaggie"):
      subió >= 30% en 1-3 meses · consolidación ajustada (rango de las últimas 10 ruedas < 2,5 x ADR)
      · precio sobre SMA10 y SMA20 · rompe hoy el máximo de las 10 ruedas previas · ADR >= 2%.
  Episodic Pivot (Qullamaggie): gap de apertura >= 8% con volumen >= 2 x promedio, después de
      3-6 meses "dormida" (retorno de 6 meses entre -20% y +20%).
  Ruptura de máximo de 52 semanas con tendencia (clásico de trend-following / Darvas).

Para cada setup se mide qué pasó después de cada señal en los últimos 10 años
(comprando en la apertura siguiente): retorno a 5, 10 y 20 ruedas, % de aciertos y
diferencia contra SPY. Se separa antes/después de 2023 para ver si es consistente.

Ejecutar:  python setups.py
Genera:    reportes/setups_hoy.csv, reportes/setups_estadistica.csv, reportes/setups.md
"""
from pathlib import Path

import pandas as pd
import yaml

import data
import db

REPORTES = Path("reportes")
HORIZONTES = (5, 10, 20)
NOMBRES = {
    "trend_template": "Trend Template (Minervini)",
    "breakout_q": "Breakout (Qullamaggie)",
    "episodic_pivot": "Episodic Pivot (Qullamaggie)",
    "max_52s": "Máximo de 52 semanas",
    "rs_90": "RS Rating ≥ 90",
}


def cargar_ohlcv(con, cfg):
    pares = data.universo_ampliado(cfg) if cfg.get("momentum", {}).get("universo") == "ampliado" else cfg["universo"]
    bench = data.cargar_precios(con, cfg["benchmark"])
    fechas = bench.index
    campos = {k: {} for k in ("open", "high", "low", "close", "volume")}
    sectores = {}
    for par in pares:
        df = data.cargar_precios(con, par["subyacente"])
        if len(df) < 300:
            continue
        df = df.reindex(fechas)
        for k in campos:
            campos[k][par["subyacente"]] = df[k]
        sectores[par["subyacente"]] = par.get("sector", "")
    M = {k: pd.DataFrame(v) for k, v in campos.items()}
    M["close"] = M["close"].ffill()
    return M, bench, sectores


def calcular_senales(M):
    c, h, l, o, v = M["close"], M["high"], M["low"], M["open"], M["volume"]
    sma = {n: c.rolling(n, min_periods=int(n * 0.8)).mean() for n in (10, 20, 50, 150, 200)}
    r = {n: c / c.shift(n) - 1 for n in (21, 63, 126, 189, 252)}
    # RS Rating estilo IBD (percentil 1-99 dentro del universo, cada día)
    rs_raw = 2 * r[63] + r[126] + r[189] + r[252]
    rs = (rs_raw.rank(axis=1, pct=True) * 99).clip(1, 99)
    max52, min52 = c.rolling(252, min_periods=200).max(), c.rolling(252, min_periods=200).min()
    adr = ((h / l) - 1).rolling(20, min_periods=15).mean()
    vol_prom = v.rolling(50, min_periods=20).mean()

    tt = ((c > sma[50]) & (sma[50] > sma[150]) & (sma[150] > sma[200]) & (sma[200] > sma[200].shift(21))
          & (c >= 1.30 * min52) & (c >= 0.75 * max52) & (rs >= 70))
    subio = (r[21] >= 0.30) | (r[63] >= 0.30)
    rango10 = h.rolling(10).max().shift(1) / l.rolling(10).min().shift(1) - 1
    ajustada = rango10 < 2.5 * adr
    rompe = c > h.rolling(10).max().shift(1)
    bq = subio.shift(1, fill_value=False) & ajustada & (c > sma[10]) & (c > sma[20]) & rompe & (adr >= 0.02)
    gap = o / c.shift(1) - 1
    ep = (gap >= 0.08) & (v >= 2 * vol_prom) & (r[126].shift(1).abs() <= 0.20)
    m52 = (c >= c.rolling(252, min_periods=200).max()) & (c.shift(1) < c.shift(1).rolling(252, min_periods=200).max()) \
        & (sma[50] > sma[200])
    senales = {"trend_template": tt, "breakout_q": bq, "episodic_pivot": ep, "max_52s": m52, "rs_90": rs >= 90}
    extra = {"rs": rs, "adr": adr, "r21": r[21], "r63": r[63], "dist_max52": c / max52 - 1}
    return {k: s.fillna(False).astype(bool) for k, s in senales.items()}, extra


def estadistica(M, bench, senales, corte):
    """Retorno después de cada señal (entrada en la apertura siguiente) vs SPY en la misma ventana."""
    o, c = M["open"].ffill(), M["close"]
    b_o = bench["open"].reindex(c.index).ffill()
    b_c = bench["close"].reindex(c.index).ffill()
    filas = []
    for nombre, s in senales.items():
        # solo la PRIMERA señal de una racha (un setup nuevo, no todos los días que se cumple)
        nuevas = s & ~s.shift(1, fill_value=False)
        for n in HORIZONTES:
            ent = o.shift(-1)
            sal = c.shift(-n)
            ret = (sal / ent - 1)[nuevas]
            ret_b = (b_c.shift(-n) / b_o.shift(-1) - 1)
            exc = ret.sub(ret_b, axis=0)[nuevas]
            for periodo, mask in (("todo", None), ("antes", "antes"), ("después", "despues")):
                rr, ee = ret, exc
                if mask:
                    idx = rr.index < pd.Timestamp(corte) if mask == "antes" else rr.index >= pd.Timestamp(corte)
                    rr, ee = rr[idx], ee[idx]
                vals = rr.stack().dropna()
                exv = ee.stack().dropna()
                if not len(vals):
                    continue
                filas.append({"setup": nombre, "ruedas": n, "periodo": periodo, "senales": len(vals),
                              "retorno_prom": vals.mean(), "retorno_mediano": vals.median(),
                              "aciertos": (vals > 0).mean(), "vs_spy_prom": exv.mean(),
                              "le_gana_a_spy": (exv > 0).mean()})
    return pd.DataFrame(filas)


def main():
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    con = db.conectar(cfg["datos"]["base_precios"])
    M, bench, sectores = cargar_ohlcv(con, cfg)
    if M["close"].shape[1] == 0:
        print("Setups: sin datos.")
        return
    REPORTES.mkdir(exist_ok=True)
    senales, extra = calcular_senales(M)
    corte = cfg["backtest"]["inicio_fuera_de_muestra"]

    # --- quiénes cumplen hoy
    hoy = M["close"].index[-1]
    filas = []
    for t in M["close"].columns:
        activos = [k for k, s in senales.items() if bool(s.at[hoy, t])]
        nuevo = [k for k, s in senales.items() if bool(s.at[hoy, t]) and not bool(s[t].iloc[-2])]
        if activos:
            filas.append({"ticker": t, "sector": sectores.get(t, ""), "setups": ",".join(activos),
                          "nuevos_hoy": ",".join(nuevo), "rs": round(float(extra["rs"].at[hoy, t]), 0),
                          "r21": extra["r21"].at[hoy, t], "r63": extra["r63"].at[hoy, t],
                          "adr": extra["adr"].at[hoy, t], "dist_max52": extra["dist_max52"].at[hoy, t]})
    hoy_df = pd.DataFrame(filas)
    if len(hoy_df):
        hoy_df["n"] = hoy_df.setups.str.count(",") + 1
        hoy_df = hoy_df.sort_values(["n", "rs"], ascending=False).drop(columns="n")
    hoy_df.to_csv(REPORTES / "setups_hoy.csv", index=False)

    # --- estadística histórica
    est = estadistica(M, bench, senales, corte)
    est.to_csv(REPORTES / "setups_estadistica.csv", index=False)

    L = [f"# Setups de swing trading · {hoy.date()}", "",
         f"Universo: {M['close'].shape[1]} acciones. Entrada en la apertura siguiente a la señal.", "",
         "## Qué rindió cada setup a 10 ruedas", "",
         "| Setup | Período | Señales | Retorno prom. | Mediana | Aciertos | vs SPY | Le gana a SPY |",
         "|---|---|---|---|---|---|---|---|"]
    for _, r in est[est.ruedas == 10].iterrows():
        L.append(f"| {NOMBRES[r.setup]} | {r.periodo} | {r.senales} | {r.retorno_prom:.2%} | {r.retorno_mediano:.2%} | "
                 f"{r.aciertos:.0%} | {r.vs_spy_prom:+.2%} | {r.le_gana_a_spy:.0%} |")
    L += ["", f"## Hoy: {len(hoy_df)} acciones cumplen algún setup", ""]
    if len(hoy_df):
        L.append(hoy_df.head(25).to_markdown(index=False))
    (REPORTES / "setups.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:20]))


if __name__ == "__main__":
    main()
