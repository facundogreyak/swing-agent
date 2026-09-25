"""
cedears.py - Pasa las decisiones del agente (en dólares, sobre la acción de EE.UU.) a CEDEARs en pesos.

Conceptos:
  ratio          -> cuántos CEDEARs equivalen a 1 acción (config.yaml)
  CCL implícito  -> dólar que "pagás" al comprar un CEDEAR:  precio_ars x ratio / precio_usd
                    (porque precio_ars = precio_usd x CCL / ratio)
  CCL de mercado -> mediana de los CCL implícitos de todos los CEDEARs con precio al día
  prima          -> CCL implícito / CCL de mercado - 1
                    > 0: el CEDEAR está CARO (pagás más pesos por cada dólar de acción)
                    < 0: está BARATO

Genera reportes/cedears.csv (una fila por CEDEAR) y reportes/ordenes_cedears.csv
(cartera momentum y órdenes de la próxima revisión, en cantidad de CEDEARs y pesos).
Ejecutar:  python cedears.py
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

import data
import db

REPORTES = Path("reportes")


def _ultimo(con, ticker):
    """Último cierre y su fecha; None si no hay o si es muy viejo."""
    fila = con.execute("SELECT fecha, close FROM precios WHERE ticker=? AND close>0 ORDER BY fecha DESC LIMIT 1",
                       (ticker,)).fetchone()
    if not fila:
        return None, None
    return fila[1], fila[0]


def tabla_cedears(con, cfg):
    """CCL implícito, prima y estado de cada CEDEAR del universo (+ SPY)."""
    p = cfg.get("cedears", {})
    dias_max = p.get("dias_max_precio", 5)
    base = data.universo_ampliado(cfg) if cfg.get("momentum", {}).get("universo") == "ampliado" else cfg["universo"]
    pares = list(base) + [{"subyacente": cfg["benchmark"], **cfg.get("benchmark_cedear", {}),
                                      "sector": "Índice"}]
    ult_usd = con.execute("SELECT MAX(fecha) FROM precios WHERE ticker=?", (cfg["benchmark"],)).fetchone()[0]
    filas = []
    for par in pares:
        t, ced, ratio = par["subyacente"], par.get("cedear"), par.get("ratio")
        usd, f_usd = _ultimo(con, t)
        ars, f_ars = _ultimo(con, ced) if ced else (None, None)
        for alt in par.get("cedear_alternativos", []) or []:      # símbolos alternativos en Yahoo
            a_ars, a_f = _ultimo(con, alt)
            n_alt = con.execute("SELECT COUNT(*) FROM precios WHERE ticker=?", (alt,)).fetchone()[0]
            n_act = con.execute("SELECT COUNT(*) FROM precios WHERE ticker=?", (ced,)).fetchone()[0]
            # se queda con el símbolo que tenga el dato más reciente y más historia
            if a_ars and (f_ars is None or (a_f, n_alt) > (f_ars, n_act)):
                ars, f_ars, ced = a_ars, a_f, alt
        fila = {"ticker": t, "cedear": (ced or "").replace(".BA", ""), "sector": par.get("sector", ""),
                "ratio": ratio, "precio_usd": usd, "precio_ars": ars, "fecha_ars": f_ars, "ccl_implicito": None,
                "estado": ""}
        if not ratio or usd is None:
            fila["estado"] = "sin ratio o sin precio en USD"
        elif ars is None:
            fila["estado"] = "sin precio en pesos"
        elif ult_usd and (pd.Timestamp(ult_usd) - pd.Timestamp(f_ars)).days > dias_max:
            fila["estado"] = f"precio en pesos viejo ({f_ars})"
        else:
            fila["ccl_implicito"] = ars * ratio / usd
        filas.append(fila)
    df = pd.DataFrame(filas)
    validos = df.ccl_implicito.dropna()
    ccl = float(validos.median()) if len(validos) else float("nan")
    # descartar los que se alejan demasiado (ratio cambiado o precio erróneo) y recalcular la mediana
    lejos = (df.ccl_implicito / ccl - 1).abs() > p.get("desvio_revisar", 0.10)
    df.loc[lejos, "estado"] = "ratio o precio a revisar"
    ccl = float(df.loc[~lejos, "ccl_implicito"].dropna().median()) if (~lejos).any() else ccl
    df["prima"] = np.where(df.estado == "", df.ccl_implicito / ccl - 1, np.nan)

    def clasif(r):
        if r.estado:
            return r.estado
        if r.prima >= p.get("prima_caro", 0.015):
            return "caro"
        if r.prima <= p.get("prima_barato", -0.015):
            return "barato"
        return "normal"
    df["estado"] = df.apply(clasif, axis=1)
    return df, ccl


def cantidad_cedears(monto_usd, fila, ccl):
    """Cuántos CEDEARs comprar con `monto_usd` (entero hacia abajo) y cuánto cuesta en pesos."""
    if fila is None or pd.isna(fila.get("precio_ars")) or not fila.get("ratio"):
        return None, None
    ars = monto_usd * ccl
    cant = math.floor(ars / fila["precio_ars"])
    return cant, cant * fila["precio_ars"]


def ordenes_momentum(con_diario, cfg, df, ccl, precios_usd):
    """Cartera momentum actual y órdenes pendientes traducidas a CEDEARs."""
    fila = con_diario.execute("SELECT estado_json FROM estado_motor WHERE nombre='momentum'").fetchone()
    if not fila:
        return pd.DataFrame()
    est = json.loads(fila[0])
    por_ticker = {r.ticker: r._asdict() for r in df.itertuples(index=False)}
    total_usd = est.get("efectivo", 0) + sum(q * precios_usd.get(t, 0) for t, q in est.get("pos", {}).items())
    filas = []
    for t, q in est.get("pos", {}).items():
        r = por_ticker.get(t)
        valor = q * precios_usd.get(t, 0)
        filas.append({"tipo": "EN CARTERA", "ticker": t, "cedear": r["cedear"] if r else "",
                      "cantidad": round(q * r["ratio"]) if r and r["ratio"] else None,
                      "precio_ars": r["precio_ars"] if r else None,
                      "monto_ars": valor * ccl if not math.isnan(ccl) else None,
                      "monto_usd": valor, "estado_precio": r["estado"] if r else "", "motivo": ""})
    pend = est.get("pendiente") or {}
    nombres = pend.get("nombres", [])
    motivos = pend.get("motivos", {})
    cupo = total_usd / cfg["momentum"]["top_n"] if cfg["momentum"]["top_n"] else 0
    for t in nombres:
        if t in est.get("pos", {}):
            continue
        r = por_ticker.get(t)
        cant, ars = cantidad_cedears(cupo, r, ccl) if r else (None, None)
        filas.append({"tipo": "COMPRAR", "ticker": t, "cedear": r["cedear"] if r else "", "cantidad": cant,
                      "precio_ars": r["precio_ars"] if r else None, "monto_ars": ars, "monto_usd": cupo,
                      "estado_precio": r["estado"] if r else "", "motivo": motivos.get(t, "")})
    for t in est.get("pos", {}):
        if t != cfg["benchmark"] and nombres and t not in nombres:
            r = por_ticker.get(t)
            q = est["pos"][t]
            filas.append({"tipo": "VENDER", "ticker": t, "cedear": r["cedear"] if r else "",
                          "cantidad": round(q * r["ratio"]) if r and r["ratio"] else None,
                          "precio_ars": r["precio_ars"] if r else None,
                          "monto_ars": q * precios_usd.get(t, 0) * ccl, "monto_usd": q * precios_usd.get(t, 0),
                          "estado_precio": r["estado"] if r else "", "motivo": motivos.get(t, "")})
    return pd.DataFrame(filas)


def main():
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    con = db.conectar(cfg["datos"]["base_precios"])
    dia = db.conectar(cfg["datos"]["base_diario"])
    REPORTES.mkdir(exist_ok=True)
    df, ccl = tabla_cedears(con, cfg)
    df.to_csv(REPORTES / "cedears.csv", index=False)
    precios_usd = dict(zip(df.ticker, df.precio_usd))
    ords = ordenes_momentum(dia, cfg, df, ccl, precios_usd)
    ords.to_csv(REPORTES / "ordenes_cedears.csv", index=False)
    (REPORTES / "ccl.json").write_text(json.dumps({"ccl": ccl, "validos": int(df.prima.notna().sum())}))
    print(f"CCL implícito (mediana de {int(df.prima.notna().sum())} CEDEARs): {ccl:,.2f}")
    print(df.estado.value_counts().to_string())
    revisar = df[df.estado.str.contains("revisar|sin|viejo")]
    if len(revisar):
        print("A revisar:", ", ".join(f"{r.cedear} ({r.estado})" for r in revisar.itertuples()))


if __name__ == "__main__":
    main()
