"""
backtest.py - Etapa 3: simula la estrategia sobre la historia guardada.

Reglas de simulación (conservadoras a propósito):
  - La señal se detecta al cierre; se compra en la APERTURA del día siguiente.
  - Si la apertura ya abre por debajo del stop, se vende a la apertura (gap).
  - Si en el mismo día se tocan stop y objetivo, se asume el STOP (peor caso).
  - Trailing stop opcional: al cierre, el stop sube a (máximo desde la entrada - k x ATR).
  - Salida por tiempo al cierre del día `max_dias_en_posicion`.
  - Comisión en cada compra y cada venta.

Ejecutar:  python backtest.py            -> backtest de la configuración actual
           python backtest.py calibrar   -> además prueba la grilla de parámetros
Genera:    reportes/backtest.md, reportes/backtest_operaciones.csv,
           reportes/backtest_equity.csv, reportes/calibracion.md, reportes/calibracion.csv
"""
import copy
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

import db
import data
from estrategia import evaluar, tamano_posicion, regimen_mercado, entradas_usadas

REPORTES = Path("reportes")


# ---------------------------------------------------------------------------
# Carga y alineación de datos (todas las series sobre el calendario del SPY)
# ---------------------------------------------------------------------------
def preparar_panel(con, cfg):
    bench = data.cargar_precios(con, cfg["benchmark"])
    fechas = bench.index
    tipos = entradas_usadas(cfg)
    cols = {k: {} for k in ["open", "high", "low", "close", "atr", "rsi"]
            + [f"senal_{t}" for t in tipos] + [f"prio_{t}" for t in tipos]}
    sectores = {}
    for par in cfg["universo"]:
        t = par["subyacente"]
        df = data.cargar_precios(con, t)
        if len(df) < cfg["estrategia"]["sma_lenta"] + 20:
            continue
        ev = evaluar(df, cfg).reindex(fechas)
        for k in ("open", "high", "low", "atr", "rsi"):
            cols[k][t] = ev[k]
        cols["close"][t] = ev["close"]
        for tipo in tipos:
            cols[f"senal_{tipo}"][t] = ev[f"senal_{tipo}"].fillna(False).astype(bool)
            cols[f"prio_{tipo}"][t] = ev[f"prio_{tipo}"]
        sectores[t] = par.get("sector", "Otros")
    panel = {k: pd.DataFrame(v) for k, v in cols.items()}
    panel["close_ffill"] = panel["close"].ffill()
    panel["mercado_ok"] = regimen_mercado(bench, cfg["estrategia"].get("sma_mercado", 200))
    panel["bench"] = bench["close"]
    # Fuerza relativa: retorno de n ruedas del papel menos el del SPY (para cada n que se use)
    ns = {cfg["estrategia"].get("fuerza_relativa_dias")}
    ns |= set(cfg.get("backtest", {}).get("grilla", {}).get("fuerza_relativa_dias", []))
    for n in {x for x in ns if x}:
        rb = bench["close"].pct_change(n)
        panel[f"fr_{n}"] = panel["close_ffill"].pct_change(n, fill_method=None).sub(rb, axis=0)
    return panel, sectores


# ---------------------------------------------------------------------------
# Simulación
# ---------------------------------------------------------------------------
def simular(panel, sectores, cfg, desde=None, hasta=None):
    r, e = cfg["riesgo"], cfg["estrategia"]
    com = r["comision_pct"]
    capital0 = r["capital_inicial_usd"]
    trailing = r.get("trailing_atr")
    usar_filtro = e.get("filtro_mercado", False)
    fr_n = e.get("fuerza_relativa_dias")
    FR = panel[f"fr_{fr_n}"].values if fr_n else None

    tickers = list(panel["close"].columns)
    ti = {t: i for i, t in enumerate(tickers)}
    O, H, L = panel["open"].values, panel["high"].values, panel["low"].values
    C, CF = panel["close"].values, panel["close_ffill"].values
    tipo = e.get("entrada", "retroceso")
    ATR, SEN, PRIO = panel["atr"].values, panel[f"senal_{tipo}"].values, panel[f"prio_{tipo}"].values
    MOK = panel["mercado_ok"].values
    todas = panel["close"].index

    # Primer día con indicadores completos (hacen falta `sma_lenta` ruedas de historia)
    primer = todas[min(e["sma_lenta"], len(todas) - 1)]
    mask = todas >= max(pd.Timestamp(desde), primer) if desde else todas >= primer
    if hasta:
        mask &= todas < pd.Timestamp(hasta)
    idx = np.where(mask)[0]
    if len(idx) < 20:
        raise ValueError("Período demasiado corto para simular")

    efectivo, abiertas, cerradas, curva, pendientes = capital0, {}, [], [], []
    # 100% invertido: el efectivo ocioso se mantiene en el benchmark (SPY) y rinde lo que rinde SPY.
    # Cada compra de acciones "vende SPY" y cada venta "compra SPY" (se cobra comisión en esos pasos).
    en_spy = bool(r.get("efectivo_en_spy", False))
    cs = com if en_spy else 0.0
    BCL = panel["bench"].values

    def valor_abiertas(i):
        return sum(p["cantidad"] * CF[i, ti[t]] for t, p in abiertas.items())

    def cerrar(t, pos, i, precio, motivo):
        nonlocal efectivo
        bruto = pos["cantidad"] * precio
        efectivo += bruto * (1 - com) * (1 - cs)
        pnl = bruto * (1 - com) - pos["costo_total"]
        cerradas.append({
            "ticker": t, "sector": sectores[t],
            "fecha_entrada": todas[pos["i"]].date(), "precio_entrada": round(pos["entrada"], 4),
            "stop_inicial": round(pos["stop0"], 4), "objetivo": round(pos["objetivo"], 4),
            "cantidad": pos["cantidad"], "fecha_salida": todas[i].date(),
            "precio_salida": round(precio, 4), "motivo_salida": motivo, "dias": pos["dias"],
            "pnl_usd": round(pnl, 2),
            "r_multiple": round(pnl / pos["riesgo_usd"], 2) if pos["riesgo_usd"] else 0.0,
        })

    for i in idx:
        # 1) Gestionar posiciones abiertas con la vela de hoy
        for t in list(abiertas):
            j, pos = ti[t], abiertas[t]
            if np.isnan(C[i, j]):
                continue
            pos["dias"] += 1
            o, h, l, c = O[i, j], H[i, j], L[i, j], C[i, j]
            if o <= pos["stop"]:
                cerrar(t, pos, i, o, "STOP (gap)")
            elif l <= pos["stop"]:
                cerrar(t, pos, i, pos["stop"], "STOP" if pos["stop"] <= pos["stop0"] + 1e-9 else "TRAILING")
            elif o >= pos["objetivo"]:
                cerrar(t, pos, i, o, "OBJETIVO (gap)")
            elif h >= pos["objetivo"]:
                cerrar(t, pos, i, pos["objetivo"], "OBJETIVO")
            elif pos["dias"] >= r["max_dias_en_posicion"]:
                cerrar(t, pos, i, c, "TIEMPO")
            else:
                pos["maximo"] = max(pos["maximo"], h)
                if trailing and not np.isnan(ATR[i, j]):
                    pos["stop"] = max(pos["stop"], pos["maximo"] - trailing * ATR[i, j])
                continue
            del abiertas[t]

        # 2) Ejecutar en la apertura las señales de ayer
        capital = efectivo + valor_abiertas(i)
        for cand in pendientes:
            t = cand["ticker"]
            j = ti[t]
            if len(abiertas) >= r["max_posiciones"]:
                break
            if t in abiertas or np.isnan(O[i, j]):
                continue
            if sum(1 for x in abiertas if sectores[x] == sectores[t]) >= r["max_por_sector"]:
                continue
            entrada = O[i, j]
            stop = entrada - r["stop_atr"] * cand["atr"]
            cant = tamano_posicion(capital, entrada, stop, r["riesgo_por_operacion"],
                                   efectivo / (1 + com) / (1 + cs), r.get("max_pct_posicion", 1.0))
            if cant <= 0:
                continue
            costo = cant * entrada * (1 + com)
            efectivo -= costo * (1 + cs)
            abiertas[t] = {"i": i, "entrada": entrada, "stop": stop, "stop0": stop,
                           "objetivo": entrada + r["objetivo_r"] * (entrada - stop),
                           "cantidad": cant, "costo_total": costo, "dias": 0,
                           "riesgo_usd": cant * (entrada - stop), "maximo": entrada}

        # 3) Valuación al cierre (el efectivo en SPY acompaña la variación del día)
        if en_spy and i > 0 and not np.isnan(BCL[i]) and not np.isnan(BCL[i - 1]):
            efectivo *= BCL[i] / BCL[i - 1]
        inv = valor_abiertas(i)
        curva.append((todas[i].date(), round(efectivo, 2), round(inv, 2), round(efectivo + inv, 2), len(abiertas)))

        # 4) Señales al cierre de hoy (se ejecutan mañana)
        pendientes = []
        if not usar_filtro or bool(MOK[i]):
            candidatos = SEN[i] & (FR[i] > 0) if FR is not None else SEN[i]
            for j in np.where(candidatos)[0]:
                if tickers[j] in abiertas:          # ya está en cartera: no se duplica
                    continue
                pendientes.append({"ticker": tickers[j], "atr": ATR[i, j], "prio": PRIO[i, j]})
            pendientes.sort(key=lambda x: x["prio"])     # retroceso: menor RSI · ruptura: mayor volumen

    # Cerrar lo que quede abierto al último precio (solo para medir)
    if len(idx):
        ult = idx[-1]
        for t, pos in list(abiertas.items()):
            cerrar(t, pos, ult, CF[ult, ti[t]], "FIN PERÍODO")

    eq = pd.DataFrame(curva, columns=["fecha", "efectivo", "invertido", "total", "posiciones"]).set_index("fecha")
    b = panel["bench"].iloc[idx]
    eq["spy"] = (b / b.iloc[0] * capital0).round(2).values
    return pd.DataFrame(cerradas), eq


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------
def max_drawdown(serie):
    return float(((serie / serie.cummax()) - 1).min())


def metricas(ops, eq, capital0):
    anios = max((pd.Timestamp(eq.index[-1]) - pd.Timestamp(eq.index[0])).days / 365.25, 1e-9)
    final = eq["total"].iloc[-1]
    n = len(ops)
    gan, per = ops[ops.pnl_usd > 0], ops[ops.pnl_usd <= 0]
    cagr = (final / capital0) ** (1 / anios) - 1
    mdd = max_drawdown(eq["total"])
    spy_cagr = (eq["spy"].iloc[-1] / capital0) ** (1 / anios) - 1
    return {
        "operaciones": n,
        "win_rate": float((ops.pnl_usd > 0).mean()) if n else 0.0,
        "r_promedio (expectancy)": float(ops.r_multiple.mean()) if n else 0.0,
        "ganancia_prom_R": float(gan.r_multiple.mean()) if len(gan) else 0.0,
        "perdida_prom_R": float(per.r_multiple.mean()) if len(per) else 0.0,
        "profit_factor": float(gan.pnl_usd.sum() / -per.pnl_usd.sum()) if per.pnl_usd.sum() < 0 else float("inf"),
        "dias_prom_en_posicion": float(ops.dias.mean()) if n else 0.0,
        "retorno_total": final / capital0 - 1,
        "retorno_anual (CAGR)": cagr,
        "max_drawdown": mdd,
        "retorno/caida (MAR)": cagr / abs(mdd) if mdd < 0 else 0.0,
        "exposicion_prom": float((eq["invertido"] / eq["total"]).mean()),
        "spy_retorno_anual": spy_cagr,
        "spy_max_drawdown": max_drawdown(eq["spy"]),
    }


def fmt(k, v):
    if any(x in k for x in ("rate", "retorno_", "retorno ", "drawdown", "exposicion")) and "MAR" not in k:
        return f"{v:.1%}"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def tabla_md(filas, claves, primera="Variante"):
    L = [f"| {primera} | " + " | ".join(claves) + " |", "|---" * (len(claves) + 1) + "|"]
    for nombre, m in filas:
        L.append(f"| {nombre} | " + " | ".join(fmt(k, m[k]) for k in claves) + " |")
    return L


# ---------------------------------------------------------------------------
# Calibración: grilla dentro de muestra + verificación fuera de muestra
# ---------------------------------------------------------------------------
UBICACION = {"objetivo_r": "riesgo", "max_dias_en_posicion": "riesgo", "trailing_atr": "riesgo",
             "stop_atr": "riesgo", "riesgo_por_operacion": "riesgo", "filtro_mercado": "estrategia",
             "rsi_entrada_max": "estrategia", "fuerza_relativa_dias": "estrategia", "entrada": "estrategia"}


def calibrar(panel, sectores, cfg, capital0):
    bt = cfg["backtest"]
    corte = bt["inicio_fuera_de_muestra"]
    grilla = bt["grilla"]
    claves = list(grilla)
    filas = []
    fechas = panel["close"].index
    if fechas[min(cfg["estrategia"]["sma_lenta"], len(fechas) - 1)] + pd.Timedelta(days=365) > pd.Timestamp(corte):
        print("Calibración omitida: hace falta al menos 1 año de datos antes de", corte)
        return
    for combo in itertools.product(*grilla.values()):
        c2 = copy.deepcopy(cfg)
        for k, v in zip(claves, combo):
            c2[UBICACION[k]][k] = v
        o_in, e_in = simular(panel, sectores, c2, hasta=corte)
        o_out, e_out = simular(panel, sectores, c2, desde=corte)
        m_in, m_out = metricas(o_in, e_in, capital0), metricas(o_out, e_out, capital0)
        fila = {k: ("no" if v is None else ("sí" if v is True else ("no" if v is False else v)))
                for k, v in zip(claves, combo)}
        for pref, m in (("in", m_in), ("out", m_out)):
            for k in ("operaciones", "r_promedio (expectancy)", "retorno_anual (CAGR)", "max_drawdown",
                      "retorno/caida (MAR)", "spy_retorno_anual"):
                fila[f"{pref}_{k}"] = m[k]
        filas.append(fila)
    df = pd.DataFrame(filas)
    df = df.sort_values("in_retorno/caida (MAR)", ascending=False)   # se elige SOLO con datos in-sample
    df.to_csv(REPORTES / "calibracion.csv", index=False)

    actual = {k: cfg[UBICACION[k]].get(k) for k in claves}
    L = ["# Calibración de parámetros", "",
         f"Dentro de muestra: hasta {corte} (se usa para elegir). "
         f"Fuera de muestra: desde {corte} (verificación con datos no usados).", "",
         "Orden: por retorno/caída (MAR) **dentro de muestra**. Si el ranking fuera de muestra "
         "se parece, el resultado es más confiable.", "",
         "Configuración actual: " + ", ".join(f"{k}={v}" for k, v in actual.items()), "",
         "## Top 10", ""]
    cols = claves + ["in_operaciones", "in_r_promedio (expectancy)", "in_retorno_anual (CAGR)",
                     "in_max_drawdown", "in_retorno/caida (MAR)",
                     "out_r_promedio (expectancy)", "out_retorno_anual (CAGR)", "out_max_drawdown",
                     "out_retorno/caida (MAR)", "out_spy_retorno_anual"]
    top = df.head(10)[cols].copy()
    for col in cols:
        if col in claves:
            continue
        top[col] = [fmt(col.split("_", 1)[1], v) for v in top[col]]
    L.append(top.to_markdown(index=False))
    corr = df["in_retorno/caida (MAR)"].rank().corr(df["out_retorno/caida (MAR)"].rank())   # Spearman sin scipy
    if "entrada" in claves:
        L += ["", "## Mejor combinación de cada tipo de entrada", "",
              "Elegida solo con datos dentro de muestra; las columnas 'fuera' muestran cómo le fue después.", "",
              "| Entrada | Parámetros | CAGR dentro | Caída dentro | CAGR fuera | Caída fuera | SPY fuera |",
              "|---|---|---|---|---|---|---|"]
        for tipo, g in df.groupby("entrada", sort=False):
            m = g.iloc[0]
            params = ", ".join(f"{k}={m[k]}" for k in claves if k != "entrada")
            L.append(f"| {tipo} | {params} | {m['in_retorno_anual (CAGR)']:.1%} | {m['in_max_drawdown']:.1%} | "
                     f"{m['out_retorno_anual (CAGR)']:.1%} | {m['out_max_drawdown']:.1%} | {m['out_spy_retorno_anual']:.1%} |")
    L += ["", f"Correlación de ranking dentro vs fuera de muestra (Spearman): **{corr:.2f}** "
              "(cerca de 1 = los parámetros que funcionaron antes siguieron funcionando después)."]
    (REPORTES / "calibracion.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


# ---------------------------------------------------------------------------
# Principal
# ---------------------------------------------------------------------------
def main(con_calibracion=False):
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    con = db.conectar(cfg["datos"]["base_precios"])
    panel, sectores = preparar_panel(con, cfg)
    if panel["close"].empty:
        print("No hay datos suficientes para el backtest. Corré primero etapa1.py")
        return
    REPORTES.mkdir(exist_ok=True)
    capital0 = cfg["riesgo"]["capital_inicial_usd"]

    ops, eq = simular(panel, sectores, cfg)
    base = metricas(ops, eq, capital0)
    ops.to_csv(REPORTES / "backtest_operaciones.csv", index=False)
    eq.to_csv(REPORTES / "backtest_equity.csv")

    # Por año
    eq_idx = eq.copy()
    eq_idx.index = pd.to_datetime(eq_idx.index)
    anual = eq_idx[["total", "spy"]].resample("YE").last()
    anual = pd.concat([eq_idx[["total", "spy"]].iloc[[0]], anual]).pct_change().dropna()

    variantes = []
    c2 = copy.deepcopy(cfg)
    c2["riesgo"]["efectivo_en_spy"] = not cfg["riesgo"].get("efectivo_en_spy", False)
    o2, e2 = simular(panel, sectores, c2)
    variantes.append(("efectivo en SPY: " + ("sí" if c2["riesgo"]["efectivo_en_spy"] else "no"),
                      metricas(o2, e2, capital0)))
    for rv in cfg.get("backtest", {}).get("variantes_riesgo", []):
        c2 = copy.deepcopy(cfg)
        c2["riesgo"]["riesgo_por_operacion"] = rv
        o2, e2 = simular(panel, sectores, c2)
        variantes.append((f"riesgo {rv:.1%}", metricas(o2, e2, capital0)))

    L = [f"# Backtest – {cfg['nombre_version']}", "",
         f"Período: {eq.index[0]} → {eq.index[-1]} · Tickers con datos: {len(sectores)} de {len(cfg['universo'])} · "
         f"Capital inicial: USD {capital0:,.0f}", "", "## Configuración actual", "", "| Métrica | Valor |", "|---|---|"]
    L += [f"| {k} | {fmt(k, v)} |" for k, v in base.items()]
    L += ["", "## Retorno por año", "", "| Año | Agente | SPY |", "|---|---|---|"]
    L += [f"| {f.year} | {a:.1%} | {s:.1%} |" for f, a, s in zip(anual.index, anual.total, anual.spy)]
    if variantes:
        L += ["", "## Variantes de riesgo por operación", ""]
        L += tabla_md(variantes, ["operaciones", "win_rate", "r_promedio (expectancy)",
                                  "retorno_anual (CAGR)", "max_drawdown", "exposicion_prom"])
    if len(ops):
        L += ["", "## Resultado por motivo de salida", "", "| Motivo | Operaciones | R promedio |", "|---|---|---|"]
        for mot, g in ops.groupby("motivo_salida"):
            L.append(f"| {mot} | {len(g)} | {g.r_multiple.mean():.2f} |")
        L += ["", "## Resultado por sector", "", "| Sector | Operaciones | Win rate | R promedio | PnL USD |",
              "|---|---|---|---|---|"]
        for sec, g in ops.groupby("sector"):
            L.append(f"| {sec} | {len(g)} | {(g.pnl_usd > 0).mean():.0%} | {g.r_multiple.mean():.2f} | {g.pnl_usd.sum():,.0f} |")
        L += ["", "## Últimas 10 operaciones", "", ops.tail(10).to_markdown(index=False)]
    faltan = [p["subyacente"] for p in cfg["universo"] if p["subyacente"] not in sectores]
    if faltan:
        L += ["", f"**Sin datos suficientes:** {', '.join(faltan)}"]
    (REPORTES / "backtest.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:45]))

    if con_calibracion:
        print("\n=== Calibración ===")
        calibrar(panel, sectores, cfg, capital0)


if __name__ == "__main__":
    main(con_calibracion="calibrar" in sys.argv)
