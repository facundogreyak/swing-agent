"""
backtest.py - Etapa 3: simula la estrategia sobre la historia guardada en la base.

Reglas de simulación (conservadoras a propósito):
  - La señal se detecta al cierre; se compra en la APERTURA del día siguiente.
  - Si la apertura ya abre por debajo del stop, se vende a la apertura (gap).
  - Si en el mismo día se tocan stop y objetivo, se asume el STOP (peor caso).
  - Salida por tiempo al cierre del día `max_dias_en_posicion`.
  - Comisión en cada compra y cada venta.

Ejecutar:  python backtest.py
Genera:    reportes/backtest.md, reportes/backtest_operaciones.csv, reportes/backtest_equity.csv
"""
import copy
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

import db
import data
from estrategia import evaluar, tamano_posicion

REPORTES = Path("reportes")


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
def cargar_universo(con, cfg):
    series, sectores = {}, {}
    for par in cfg["universo"]:
        t = par["subyacente"]
        df = data.cargar_precios(con, t)
        if len(df) < cfg["estrategia"]["sma_lenta"] + 20:
            continue
        series[t] = evaluar(df, cfg)
        sectores[t] = par.get("sector", "Otros")
    bench = data.cargar_precios(con, cfg["benchmark"])
    return series, sectores, bench


# ---------------------------------------------------------------------------
# Simulación
# ---------------------------------------------------------------------------
def simular(series, sectores, bench, cfg):
    r = cfg["riesgo"]
    com = r["comision_pct"]
    capital0 = r["capital_inicial_usd"]
    efectivo = capital0
    abiertas = {}            # ticker -> dict posición
    cerradas, curva = [], []
    pendientes = []          # señales del cierre anterior (se ejecutan hoy en la apertura)

    inicio = max(s.dropna(subset=["sma_lenta", "atr"]).index.min() for s in series.values())
    fechas = bench.index[bench.index >= inicio]

    def cerrar(t, pos, fecha, precio, motivo):
        nonlocal efectivo
        bruto = pos["cantidad"] * precio
        comision = bruto * com
        efectivo += bruto - comision
        pnl = bruto - comision - pos["costo_total"]
        cerradas.append({
            "ticker": t, "sector": sectores[t],
            "fecha_entrada": pos["fecha"].date(), "precio_entrada": round(pos["entrada"], 4),
            "stop": round(pos["stop"], 4), "objetivo": round(pos["objetivo"], 4),
            "cantidad": pos["cantidad"], "fecha_salida": fecha.date(),
            "precio_salida": round(precio, 4), "motivo_salida": motivo,
            "dias": pos["dias"], "pnl_usd": round(pnl, 2),
            "r_multiple": round(pnl / pos["riesgo_usd"], 2) if pos["riesgo_usd"] else 0,
        })

    for fecha in fechas:
        # 1) Gestionar posiciones abiertas con la vela de hoy
        for t in list(abiertas):
            s = series[t]
            if fecha not in s.index:
                continue
            v, pos = s.loc[fecha], abiertas[t]
            pos["dias"] += 1
            if v.open <= pos["stop"]:
                cerrar(t, pos, fecha, v.open, "STOP (gap)")
            elif v.low <= pos["stop"]:
                cerrar(t, pos, fecha, pos["stop"], "STOP")
            elif v.open >= pos["objetivo"]:
                cerrar(t, pos, fecha, v.open, "OBJETIVO (gap)")
            elif v.high >= pos["objetivo"]:
                cerrar(t, pos, fecha, pos["objetivo"], "OBJETIVO")
            elif pos["dias"] >= r["max_dias_en_posicion"]:
                cerrar(t, pos, fecha, v.close, "TIEMPO")
            else:
                continue
            del abiertas[t]

        # 2) Ejecutar las señales de ayer en la apertura de hoy
        valor_abiertas = sum(p["cantidad"] * series[t].loc[:fecha].close.iloc[-1] for t, p in abiertas.items())
        capital = efectivo + valor_abiertas
        for cand in pendientes:
            t = cand["ticker"]
            if len(abiertas) >= r["max_posiciones"]:
                break
            if t in abiertas or fecha not in series[t].index:
                continue
            if sum(1 for x in abiertas if sectores[x] == sectores[t]) >= r["max_por_sector"]:
                continue
            entrada = series[t].loc[fecha].open
            stop = entrada - r["stop_atr"] * cand["atr"]
            cant = tamano_posicion(capital, entrada, stop, r["riesgo_por_operacion"],
                                   efectivo / (1 + com), r.get("max_pct_posicion", 1.0))
            if cant <= 0:
                continue
            costo = cant * entrada * (1 + com)
            efectivo -= costo
            abiertas[t] = {
                "fecha": fecha, "entrada": entrada, "stop": stop,
                "objetivo": entrada + r["objetivo_r"] * (entrada - stop),
                "cantidad": cant, "costo_total": costo, "dias": 0,
                "riesgo_usd": cant * (entrada - stop),
            }

        # 3) Valuación al cierre
        valor_abiertas = sum(p["cantidad"] * series[t].loc[:fecha].close.iloc[-1] for t, p in abiertas.items())
        curva.append({"fecha": fecha.date(), "efectivo": round(efectivo, 2),
                      "invertido": round(valor_abiertas, 2),
                      "total": round(efectivo + valor_abiertas, 2),
                      "posiciones": len(abiertas)})

        # 4) Detectar señales al cierre de hoy (se ejecutan mañana)
        pendientes = []
        for t, s in series.items():
            if fecha in s.index and bool(s.loc[fecha, "senal_compra"]):
                v = s.loc[fecha]
                pendientes.append({"ticker": t, "atr": v.atr, "rsi": v.rsi})
        pendientes.sort(key=lambda c: c["rsi"])     # prioridad: retroceso más profundo

    # Cerrar lo que quede abierto al último precio (solo para medir)
    ultima = fechas[-1]
    for t, pos in list(abiertas.items()):
        cerrar(t, pos, ultima, series[t].loc[:ultima].close.iloc[-1], "FIN BACKTEST")

    eq = pd.DataFrame(curva).set_index("fecha")
    bench_eq = bench.loc[fechas, "close"]
    eq["spy"] = (bench_eq / bench_eq.iloc[0] * capital0).round(2).values
    return pd.DataFrame(cerradas), eq


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------
def max_drawdown(serie):
    pico = serie.cummax()
    return float(((serie / pico) - 1).min())


def metricas(ops, eq, capital0):
    anios = max((pd.Timestamp(eq.index[-1]) - pd.Timestamp(eq.index[0])).days / 365.25, 1e-9)
    final = eq["total"].iloc[-1]
    m = {
        "operaciones": len(ops),
        "win_rate": float((ops.pnl_usd > 0).mean()) if len(ops) else 0.0,
        "r_promedio (expectancy)": float(ops.r_multiple.mean()) if len(ops) else 0.0,
        "ganancia_prom_R": float(ops[ops.r_multiple > 0].r_multiple.mean()) if (ops.r_multiple > 0).any() else 0.0,
        "perdida_prom_R": float(ops[ops.r_multiple <= 0].r_multiple.mean()) if (ops.r_multiple <= 0).any() else 0.0,
        "profit_factor": float(ops[ops.pnl_usd > 0].pnl_usd.sum() / -ops[ops.pnl_usd < 0].pnl_usd.sum())
                         if (ops.pnl_usd < 0).any() else float("inf"),
        "dias_prom_en_posicion": float(ops.dias.mean()) if len(ops) else 0.0,
        "retorno_total": final / capital0 - 1,
        "retorno_anual (CAGR)": (final / capital0) ** (1 / anios) - 1,
        "max_drawdown": max_drawdown(eq["total"]),
        "exposicion_prom": float((eq["invertido"] / eq["total"]).mean()),
        "spy_retorno_total": eq["spy"].iloc[-1] / capital0 - 1,
        "spy_max_drawdown": max_drawdown(eq["spy"]),
    }
    return m


def fmt(k, v):
    if any(x in k for x in ("rate", "retorno", "drawdown", "exposicion")):
        return f"{v:.1%}"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


# ---------------------------------------------------------------------------
# Principal
# ---------------------------------------------------------------------------
def main():
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    con = db.conectar(cfg["datos"]["base_datos"])
    series, sectores, bench = cargar_universo(con, cfg)
    if not series or bench.empty:
        print("No hay datos suficientes para el backtest. Corré primero etapa1.py")
        return
    REPORTES.mkdir(exist_ok=True)
    capital0 = cfg["riesgo"]["capital_inicial_usd"]

    # Base
    ops, eq = simular(series, sectores, bench, cfg)
    base = metricas(ops, eq, capital0)
    ops.to_csv(REPORTES / "backtest_operaciones.csv", index=False)
    eq.to_csv(REPORTES / "backtest_equity.csv")

    # Variantes de riesgo por operación
    variantes = {}
    for rv in cfg.get("backtest", {}).get("variantes_riesgo", []):
        c2 = copy.deepcopy(cfg)
        c2["riesgo"]["riesgo_por_operacion"] = rv
        o2, e2 = simular(series, sectores, bench, c2)
        variantes[f"riesgo {rv:.1%}"] = metricas(o2, e2, capital0)

    # Reporte
    L = [f"# Backtest – {cfg['nombre_version']}",
         "",
         f"Período: {eq.index[0]} → {eq.index[-1]} · Tickers con datos: {len(series)} de {len(cfg['universo'])} · "
         f"Capital inicial: USD {capital0:,.0f}",
         "", "## Configuración base", "", "| Métrica | Valor |", "|---|---|"]
    L += [f"| {k} | {fmt(k, v)} |" for k, v in base.items()]

    if variantes:
        claves = ["operaciones", "win_rate", "r_promedio (expectancy)", "retorno_anual (CAGR)",
                  "max_drawdown", "exposicion_prom"]
        L += ["", "## Variantes de riesgo por operación", "",
              "| Variante | " + " | ".join(claves) + " |", "|---" * (len(claves) + 1) + "|"]
        for nombre, m in variantes.items():
            L.append(f"| {nombre} | " + " | ".join(fmt(k, m[k]) for k in claves) + " |")

    if len(ops):
        L += ["", "## Resultado por motivo de salida", "", "| Motivo | Operaciones | R promedio |", "|---|---|---|"]
        for mot, g in ops.groupby("motivo_salida"):
            L.append(f"| {mot} | {len(g)} | {g.r_multiple.mean():.2f} |")
        L += ["", "## Resultado por sector", "", "| Sector | Operaciones | Win rate | R promedio | PnL USD |",
              "|---|---|---|---|---|"]
        for sec, g in ops.groupby("sector"):
            L.append(f"| {sec} | {len(g)} | {(g.pnl_usd > 0).mean():.0%} | {g.r_multiple.mean():.2f} | {g.pnl_usd.sum():,.0f} |")
        L += ["", "## Últimas 10 operaciones", "", ops.tail(10).to_markdown(index=False)]

    faltan = [p["subyacente"] for p in cfg["universo"] if p["subyacente"] not in series]
    if faltan:
        L += ["", f"**Sin datos suficientes:** {', '.join(faltan)}"]

    (REPORTES / "backtest.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:40]))


if __name__ == "__main__":
    main()
