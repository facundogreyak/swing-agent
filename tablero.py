"""
tablero.py - Genera la página web del agente (docs/index.html) para GitHub Pages.
Se abre desde cualquier computadora o celular.
Ejecutar:  python tablero.py   (lo corre GitHub Actions después de cada corrida)

Secciones:
  1. Booms del momento       -> ranking de momentum de hoy, qué sube en el ranking, sectores en alza
  2. Cartera momentum        -> paper trading 100% invertido (rotación por momentum)
  3. Comparación             -> swing vs momentum vs SPY (backtest) + qué parámetro pesa más
  4. Swing                   -> paper trading y backtest de la estrategia de retroceso
  5. Datos y versiones
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

import db
import momentum as M

REP = Path("reportes")
DOCS = Path("docs")
ACCIONES_SWING = ("COMPRAR", "VENDER", "MANTENER", "NO_OPERAR")


# ---------------------------------------------------------------------------
# Utilidades de HTML
# ---------------------------------------------------------------------------
def _pct(v, dec=1):
    return "—" if v is None or pd.isna(v) else f"{v:+.{dec}%}"


def _tabla(df, columnas, signo=(), nombres=None):
    """Tabla HTML. `signo`: columnas que se pintan verde/rojo según el signo (acepta texto '+x%')."""
    if df is None or df.empty:
        return "<p class='vacio'>Sin datos todavía.</p>"
    nombres = nombres or {}
    h = "".join(f"<th>{nombres.get(c, c)}</th>" for c in columnas)
    filas = ""
    for _, r in df.iterrows():
        celdas = ""
        for c in columnas:
            v = r[c]
            clase = ""
            if c in signo and pd.notna(v) and v != "—":
                num = v if isinstance(v, (int, float, np.floating)) else (-1 if str(v).startswith("-") else 1)
                clase = " class='pos'" if num > 0 else (" class='neg'" if num < 0 else "")
            celdas += f"<td{clase}>{'' if pd.isna(v) else v}</td>"
        filas += f"<tr>{celdas}</tr>"
    return f"<div class='tw'><table><thead><tr>{h}</tr></thead><tbody>{filas}</tbody></table></div>"


def _kpis(pares):
    return "<div class='kpis'>" + "".join(
        f"<div class='kpi'><span>{k}</span><b>{v}</b></div>" for k, v in pares) + "</div>"


def _metricas_curva(s):
    s = s.dropna()
    anios = max((pd.Timestamp(s.index[-1]) - pd.Timestamp(s.index[0])).days / 365.25, 1e-9)
    cagr = (s.iloc[-1] / s.iloc[0]) ** (1 / anios) - 1
    dd = float((s / s.cummax() - 1).min())
    anual = s.copy()
    anual.index = pd.to_datetime(anual.index)
    ra = pd.concat([anual.iloc[[0]], anual.resample("YE").last()]).pct_change().dropna()
    return {"cagr": cagr, "dd": dd, "mar": cagr / abs(dd) if dd < 0 else 0, "peor": ra.min(),
            "mejor": ra.max(), "total": s.iloc[-1] / s.iloc[0] - 1, "anual": ra}


# ---------------------------------------------------------------------------
# Secciones
# ---------------------------------------------------------------------------
def seccion_booms(con, con_diario, cfg):
    P = M.cargar(con, cfg)
    if len(P["fechas"]) < 300:
        return "<p class='vacio'>Hace falta más historia de precios.</p>", {}
    pun = M.calcular_puntajes(P["close"])
    crudos = pun["_crudos"]
    m = cfg["momentum"]
    sc = pun[m["puntaje"]][0]
    hoy, antes = len(P["fechas"]) - 1, len(P["fechas"]) - 6
    rk_hoy = sc.iloc[hoy].rank(ascending=False, method="first")
    rk_antes = sc.iloc[antes].rank(ascending=False, method="first")
    fecha = P["fechas"][hoy].strftime("%d/%m/%Y")

    estado = con_diario.execute("SELECT estado_json FROM estado_motor WHERE nombre='momentum'").fetchone()
    en_cartera = set(json.loads(estado[0]).get("pos", {})) if estado else set()

    df = pd.DataFrame({"puesto": rk_hoy, "antes": rk_antes})
    df = df.dropna(subset=["puesto"]).sort_values("puesto")
    df["ticker"] = df.index
    df["sector"] = df.ticker.map(P["sectores"])
    for c, n in (("r21", "1 mes"), ("r63", "3 meses"), ("r126", "6 meses*"), ("r252", "12 meses*")):
        df[n] = [_pct(crudos[c].iat[hoy, P["tickers"].index(t)], 0) for t in df.ticker]

    def cambio(r):
        if pd.isna(r.antes):
            return "nuevo"
        d = int(r.antes - r.puesto)
        return f"▲{d}" if d > 0 else (f"▼{-d}" if d < 0 else "=")
    df["cambio 1 sem."] = df.apply(cambio, axis=1)
    df["puesto"] = df.puesto.astype(int)
    df["cartera"] = df.ticker.map(lambda t: "●" if t in en_cartera else "")
    top = df.head(15)

    nuevos_top10 = [t for t in df.head(10).ticker if rk_antes.get(t, 99) > 10]
    salen_top10 = [t for t in rk_antes.sort_values().head(10).index if rk_hoy.get(t, 99) > 10]
    subas = df[df["cambio 1 sem."].str.startswith("▲")].copy()
    subas["d"] = subas["cambio 1 sem."].str[1:].astype(int)
    aceleran = subas.sort_values("d", ascending=False).head(5)

    sect = pd.DataFrame({
        "sector": [P["sectores"][t] for t in P["tickers"]],
        "r21": crudos["r21"].iloc[hoy].values, "r63": crudos["r63"].iloc[hoy].values,
        "top10": [1 if rk_hoy.get(t, 99) <= 10 else 0 for t in P["tickers"]],
    }).groupby("sector").agg(acciones=("r21", "size"), prom_1m=("r21", "mean"), prom_3m=("r63", "mean"),
                              en_top10=("top10", "sum")).sort_values("prom_3m", ascending=False).reset_index()
    sect["prom_1m"] = sect.prom_1m.map(lambda v: _pct(v, 1))
    sect["prom_3m"] = sect.prom_3m.map(lambda v: _pct(v, 1))

    resumen = "<div class='chips'>"
    resumen += "<div><span>Nuevos en el top 10</span><b>" + (", ".join(nuevos_top10) or "ninguno") + "</b></div>"
    resumen += "<div><span>Salieron del top 10</span><b>" + (", ".join(salen_top10) or "ninguno") + "</b></div>"
    resumen += "<div><span>Más escalaron en la semana</span><b>" + (
        ", ".join(f"{r.ticker} ({r['cambio 1 sem.']})" for _, r in aceleran.iterrows()) or "—") + "</b></div>"
    resumen += "</div>"

    html = (f"<div class='sub'>Ranking al cierre del {fecha} por puntaje <b>{m['puntaje']}</b>. "
            "● = está en la cartera momentum. *6 y 12 meses sin contar el último mes.</div>"
            + resumen
            + _tabla(top, ["puesto", "cambio 1 sem.", "ticker", "sector", "1 mes", "3 meses", "6 meses*",
                           "12 meses*", "cartera"], signo=("1 mes", "3 meses", "6 meses*", "12 meses*", "cambio 1 sem."))
            + "<h3>Sectores</h3>"
            + _tabla(sect, ["sector", "acciones", "en_top10", "prom_1m", "prom_3m"], signo=("prom_1m", "prom_3m"),
                     nombres={"en_top10": "en el top 10", "prom_1m": "suba prom. 1 mes", "prom_3m": "suba prom. 3 meses"}))
    return html, {"P": P}


def seccion_cartera_momentum(con_diario, cfg, P):
    fila = con_diario.execute("SELECT ultima_fecha, estado_json FROM estado_motor WHERE nombre='momentum'").fetchone()
    if not fila:
        return "<p class='vacio'>La cartera momentum arranca en la próxima corrida.</p>"
    ultima, est = fila[0], json.loads(fila[1])
    cap0 = cfg["riesgo"]["capital_inicial_usd"]
    eqm = pd.read_sql("SELECT fecha, efectivo, invertido, total FROM equity WHERE version_id='momentum' ORDER BY fecha",
                      con_diario)
    total = eqm.total.iloc[-1] if len(eqm) else cap0
    inicio = eqm.fecha.iloc[0] if len(eqm) else ultima
    bench = cfg["benchmark"]
    precios = {t: float(P["close"][t].iloc[-1]) for t in P["tickers"]}
    precios[bench] = float(P["bench_close"].iloc[-1])

    pos = []
    for t, q in est.get("pos", {}).items():
        valor = q * precios.get(t, np.nan)
        costo = est.get("costo", {}).get(t, np.nan)
        pos.append({"ticker": t, "desde": est.get("entrada", {}).get(t, ""), "valor USD": f"{valor:,.0f}",
                    "peso": f"{valor / total:.1%}", "resultado": _pct(valor / costo - 1 if costo else None),
                    "_v": valor})
    pos = pd.DataFrame(pos).sort_values("_v", ascending=False) if pos else pd.DataFrame()
    en_acciones = sum(r["_v"] for _, r in pos.iterrows() if r["ticker"] != bench) if len(pos) else 0
    en_spy = sum(r["_v"] for _, r in pos.iterrows() if r["ticker"] == bench) if len(pos) else 0

    ult_reb = est.get("ult_reb")
    dec = pd.read_sql("SELECT ticker, accion, motivo FROM decisiones WHERE fecha=? AND accion NOT IN "
                      f"{ACCIONES_SWING} ORDER BY CASE accion WHEN 'ENTRA' THEN 0 WHEN 'SALE' THEN 1 ELSE 2 END",
                      con_diario, params=(ult_reb,)) if ult_reb else pd.DataFrame()
    ops = pd.read_sql("SELECT fecha, ticker, lado, monto_usd, motivo, retorno FROM mom_operaciones "
                      "ORDER BY id DESC LIMIT 20", con_diario)
    if len(ops):
        ops["retorno"] = ops.retorno.map(lambda v: _pct(v) if pd.notna(v) else "")
        ops["monto_usd"] = ops.monto_usd.map(lambda v: f"{v:,.0f}")
    prox = None
    if ult_reb:
        k = P["fechas"].get_indexer([pd.Timestamp(ult_reb)])[0]
        faltan = cfg["momentum"]["rebalanceo_dias"] - (len(P["fechas"]) - 1 - k)
        prox = f"en {max(faltan, 0)} ruedas" if faltan > 0 else "en la próxima corrida"

    return (_kpis([("Cartera momentum", f"USD {total:,.0f}"),
                   (f"Retorno desde {inicio}", f"{total / cap0 - 1:+.1%}"),
                   ("En acciones", f"{en_acciones / total:.0%}" if total else "—"),
                   ("En SPY", f"{en_spy / total:.0%}" if total else "—"),
                   ("Último rebalanceo", ult_reb or "—"), ("Próximo", prox or "—")])
            + "<h3>Posiciones</h3>"
            + _tabla(pos, ["ticker", "desde", "valor USD", "peso", "resultado"], signo=("resultado",))
            + (f"<h3>Decisiones del último rebalanceo ({ult_reb})</h3>" + _tabla(dec, ["ticker", "accion", "motivo"])
               if len(dec) else "")
            + "<h3>Últimas operaciones</h3>"
            + _tabla(ops, ["fecha", "ticker", "lado", "monto_usd", "retorno", "motivo"], signo=("retorno",),
                     nombres={"monto_usd": "monto USD"}))


def seccion_comparacion(cfg):
    series = {}
    if (REP / "backtest_equity.csv").exists():
        e = pd.read_csv(REP / "backtest_equity.csv", index_col="fecha")
        series["Swing (retroceso)"] = e.total
        series["SPY"] = e.spy
    if (REP / "momentum_equity.csv").exists():
        e = pd.read_csv(REP / "momentum_equity.csv", index_col="fecha")
        series["Momentum"] = e.total
        series.setdefault("SPY", e.spy)
        if "igual_peso" in e.columns:
            series["50 acciones en partes iguales"] = e.igual_peso
    if len(series) < 2:
        return "<p class='vacio'>Falta correr los backtests.</p>", {"fechas": [], "series": {}}
    df = pd.DataFrame(series).dropna()
    df = df / df.iloc[0] * cfg["riesgo"]["capital_inicial_usd"]
    filas, anual = [], {}
    for n in df.columns:
        mm = _metricas_curva(df[n])
        anual[n] = mm["anual"]
        filas.append({"estrategia": n, "retorno anual": _pct(mm["cagr"]), "peor caída": _pct(mm["dd"]),
                      "retorno / caída": f"{mm['mar']:.2f}", "mejor año": _pct(mm["mejor"]),
                      "peor año": _pct(mm["peor"]), "total": _pct(mm["total"], 0)})
    ta = pd.DataFrame(anual)
    ta.index = ta.index.year
    ta = ta.reset_index().rename(columns={"fecha": "año", "index": "año"})
    for c in ta.columns[1:]:
        ta[c] = ta[c].map(lambda v: _pct(v))
    html = (f"<div class='sub'>Backtest del {df.index[0]} al {df.index[-1]}, mismo capital inicial. "
            "'50 acciones en partes iguales' es la referencia honesta: la lista se armó hoy con ganadores "
            "conocidos, así que la ventaja real de una estrategia es lo que supera a esa línea, no a SPY.</div>"
            + _tabla(pd.DataFrame(filas), list(filas[0].keys()),
                     signo=("retorno anual", "mejor año", "peor año", "total"))
            + "<div class='card' style='margin-top:12px'><canvas id='cmp' height='130'></canvas></div>"
            + "<details><summary>Retorno por año</summary>"
            + _tabla(ta, list(ta.columns), signo=tuple(ta.columns[1:])) + "</details>")
    return html, {"fechas": list(df.index), "series": {k: df[k].round(0).tolist() for k in df.columns}}


def seccion_que_pesa(cfg):
    f = REP / "momentum_calibracion.csv"
    if not f.exists():
        return "<p class='vacio'>Todavía no hay calibración de momentum.</p>"
    df = pd.read_csv(f)
    claves = [k for k in cfg["momentum"].get("grilla", {}) if k in df.columns]
    corte = cfg["backtest"]["inicio_fuera_de_muestra"]
    filas = []
    nombres = {"puntaje": "Período del momentum", "top_n": "Cantidad de acciones", "rebalanceo_dias":
               "Frecuencia de rotación (ruedas)", "buffer": "Margen para no rotar (buffer)",
               "max_por_sector": "Límite por sector", "filtro_mercado": "Filtro de mercado (a efectivo)"}
    for k in claves:
        gi = df.groupby(df[k].astype(str))["in_retorno_anual (CAGR)"].mean()
        go = df.groupby(df[k].astype(str))["out_retorno_anual (CAGR)"].mean()
        filas.append({"decisión": nombres.get(k, k), "impacto": go.max() - go.min(),
                      "mejor antes": f"{gi.idxmax()} ({gi.max():.1%})", "mejor después": f"{go.idxmax()} ({go.max():.1%})",
                      "¿coincide?": "sí" if gi.idxmax() == go.idxmax() else "no",
                      "valores (después)": " · ".join(f"{i}: {v:.1%}" for i, v in go.items())})
    t = pd.DataFrame(filas).sort_values("impacto", ascending=False)
    t["impacto"] = t.impacto.map(lambda v: f"{v:.1%}")
    return (f"<div class='sub'>Cuánto cambia el retorno anual según cada decisión (promedio de todas las combinaciones). "
            f"'Antes' = hasta {corte}, usado para elegir · 'Después' = desde {corte}. "
            "Si el mejor valor coincide antes y después, esa decisión es confiable.</div>"
            + _tabla(t, ["decisión", "impacto", "mejor antes", "mejor después", "¿coincide?", "valores (después)"]))


def seccion_swing(con, con_diario, cfg):
    cuenta = con_diario.execute("SELECT capital_inicial, inicio, ultima_fecha FROM cuenta WHERE id=1").fetchone()
    if not cuenta:
        return "<p class='vacio'>El paper trading swing arranca en la próxima corrida.</p>"
    cap_ini, inicio, ult_paper = cuenta
    eqp = pd.read_sql("SELECT fecha, total FROM equity WHERE version_id='paper' ORDER BY fecha", con_diario)
    abiertas = pd.read_sql("SELECT ticker, fecha_entrada, precio_entrada, stop, objetivo, cantidad, riesgo_usd, "
                           "costo_total, dias FROM operaciones WHERE estado='ABIERTA' ORDER BY fecha_entrada",
                           con_diario)
    cerradas = pd.read_sql("SELECT ticker, fecha_entrada, fecha_salida, motivo_salida, dias, r_multiple, pnl_usd "
                           "FROM operaciones WHERE estado='CERRADA' ORDER BY fecha_salida DESC", con_diario)
    decis = pd.read_sql(f"SELECT ticker, accion, motivo FROM decisiones WHERE fecha=? AND accion IN {ACCIONES_SWING} "
                        "ORDER BY CASE accion WHEN 'COMPRAR' THEN 0 WHEN 'VENDER' THEN 1 "
                        "WHEN 'MANTENER' THEN 2 ELSE 3 END, ticker", con_diario, params=(ult_paper,))
    total = eqp.total.iloc[-1] if len(eqp) else cap_ini
    if len(abiertas):
        ultimos = {r.ticker: con.execute("SELECT close FROM precios WHERE ticker=? ORDER BY fecha DESC LIMIT 1",
                                         (r.ticker,)).fetchone()[0] for r in abiertas.itertuples()}
        abiertas["precio_actual"] = abiertas.ticker.map(ultimos).round(2)
        abiertas["r_multiple"] = ((abiertas.precio_actual * abiertas.cantidad - abiertas.costo_total)
                                  / abiertas.riesgo_usd).round(2)
        for c in ("precio_entrada", "stop", "objetivo"):
            abiertas[c] = abiertas[c].round(2)
    activas = decis[decis.accion != "NO_OPERAR"]
    return (_kpis([("Cartera swing", f"USD {total:,.0f}"), (f"Retorno desde {inicio}", f"{total / cap_ini - 1:+.1%}"),
                   ("Posiciones abiertas", f"{len(abiertas)}"), ("Operaciones cerradas", f"{len(cerradas)}"),
                   ("Aciertos", f"{(cerradas.pnl_usd > 0).mean():.0%}" if len(cerradas) else "—"),
                   ("R promedio", f"{cerradas.r_multiple.mean():.2f}" if len(cerradas) else "—")])
            + f"<h3>Decisiones del {ult_paper}</h3>"
            + (_tabla(activas, ["ticker", "accion", "motivo"]) if len(activas)
               else "<p class='vacio'>Sin compras ni ventas: ningún papel cumplió todas las condiciones.</p>")
            + f"<details><summary>Ver los {len(decis)} papeles analizados</summary>"
            + _tabla(decis, ["ticker", "accion", "motivo"]) + "</details>"
            + "<h3>Posiciones abiertas</h3>"
            + _tabla(abiertas, ["ticker", "fecha_entrada", "dias", "precio_entrada", "precio_actual",
                                "stop", "objetivo", "r_multiple"], signo=("r_multiple",))
            + "<h3>Operaciones cerradas</h3>"
            + _tabla(cerradas.head(20), ["ticker", "fecha_entrada", "fecha_salida", "motivo_salida",
                                         "dias", "r_multiple", "pnl_usd"], signo=("r_multiple", "pnl_usd")))


def seccion_calibracion_swing():
    if not (REP / "calibracion.csv").exists():
        return "<p class='vacio'>Todavía no hay calibración.</p>"
    cal = pd.read_csv(REP / "calibracion.csv").head(8)
    ren = {"entrada": "Entrada", "objetivo_r": "Objetivo (R)", "max_dias_en_posicion": "Días máx.",
           "trailing_atr": "Trailing ATR", "filtro_mercado": "Filtro SPY", "fuerza_relativa_dias": "Fuerza rel.",
           "in_retorno_anual (CAGR)": "CAGR antes", "in_max_drawdown": "Caída antes",
           "out_retorno_anual (CAGR)": "CAGR después", "out_max_drawdown": "Caída después",
           "out_spy_retorno_anual": "SPY después"}
    ren = {k: v for k, v in ren.items() if k in cal.columns}
    cal = cal[list(ren)].rename(columns=ren)
    for c in ["CAGR antes", "Caída antes", "CAGR después", "Caída después", "SPY después"]:
        cal[c] = cal[c].map(lambda v: f"{v:.1%}")
    return _tabla(cal.fillna("no"), list(cal.columns))


# ---------------------------------------------------------------------------
def main():
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    con = db.conectar(cfg["datos"]["base_precios"])
    con_diario = db.conectar(cfg["datos"]["base_diario"])
    DOCS.mkdir(exist_ok=True)
    ahora = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

    estado = pd.read_sql("SELECT ticker, COUNT(*) AS velas, MAX(fecha) AS ultima_fecha FROM precios GROUP BY ticker", con)
    esperados = [cfg["benchmark"]] + [p[k] for p in cfg["universo"] for k in ("subyacente", "cedear")]
    faltan = sorted(set(esperados) - set(estado.ticker))
    ult = estado.ultima_fecha.max() if len(estado) else "—"
    vers = pd.read_sql("SELECT version_id, nombre, creada FROM versiones_params ORDER BY creada DESC", con_diario)

    booms_html, ctx = seccion_booms(con, con_diario, cfg)
    cartera_html = seccion_cartera_momentum(con_diario, cfg, ctx["P"]) if ctx else ""
    comp_html, comp = seccion_comparacion(cfg)
    pesa_html = seccion_que_pesa(cfg)
    swing_html = seccion_swing(con, con_diario, cfg)
    calib_html = seccion_calibracion_swing()
    swing_md = (REP / "backtest.md").read_text(encoding="utf-8") if (REP / "backtest.md").exists() else ""
    m = cfg["momentum"]

    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agente Inversor</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{{--bg:#f7f7f5;--card:#fff;--tx:#1d1d1b;--mu:#6b6b66;--bd:#e4e4df;--pos:#1a7f4b;--neg:#c0392b;
--s1:#2f5bd3;--s2:#d9822b;--s3:#9a9a92;--s4:#2a9d8f}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151514;--card:#1f1f1d;--tx:#ecece8;--mu:#9a9a92;--bd:#33332f;
--pos:#4cc38a;--neg:#ef6f5e;--s1:#7c9cff;--s2:#f0a35e;--s3:#77776f;--s4:#4fc1b4}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--tx);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1040px;margin:0 auto;padding:24px 16px 48px}}
h1{{font-size:22px;margin:0}}h2{{font-size:17px;margin:34px 0 8px;padding-top:8px;border-top:1px solid var(--bd)}}
h3{{font-size:14px;margin:18px 0 8px;color:var(--mu);font-weight:600}}.sub{{color:var(--mu);font-size:13px;margin-bottom:8px}}
nav{{display:flex;gap:14px;flex-wrap:wrap;margin-top:10px;font-size:13px}}nav a{{color:var(--s1);text-decoration:none}}
details{{margin-top:8px}}summary{{cursor:pointer;color:var(--mu);font-size:13px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:10px 0}}
.kpi{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:10px 12px}}
.kpi span{{display:block;color:var(--mu);font-size:12px}}.kpi b{{font-size:18px}}
.chips{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin:10px 0}}
.chips div{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:10px 12px}}
.chips span{{display:block;color:var(--mu);font-size:12px}}.chips b{{font-size:14px;font-weight:600}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:14px}}
.tw{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--bd);white-space:nowrap}}th{{color:var(--mu);font-weight:500}}
.pos{{color:var(--pos)}}.neg{{color:var(--neg)}}.vacio{{color:var(--mu)}}.warn{{color:var(--neg)}}
pre{{white-space:pre-wrap;font-size:12px;background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px;overflow-x:auto}}
</style></head><body><main>
<h1>Agente Inversor · CEDEARs</h1>
<div class="sub">Simulado (paper trading, sin dinero real) · Actualizado {ahora} (hora Argentina) · Datos hasta {ult}</div>
<nav><a href="#booms">Booms del momento</a><a href="#momentum">Cartera momentum</a><a href="#comparacion">Comparación</a>
<a href="#pesa">Qué pesa más</a><a href="#swing">Swing</a><a href="#datos">Datos</a></nav>

<h2 id="booms">Booms del momento</h2>
{booms_html}

<h2 id="momentum">Cartera momentum · 100% invertida</h2>
<div class="sub">Top {m['top_n']} por puntaje {m['puntaje']}, rotación cada {m['rebalanceo_dias']} ruedas,
buffer {m['buffer']}, límite por sector {m['max_por_sector'] or 'no'}. Lo que no va a acciones queda en SPY.</div>
{cartera_html}

<h2 id="comparacion">Comparación de estrategias (backtest)</h2>
{comp_html}

<h2 id="pesa">Qué pesa más en el resultado (momentum)</h2>
{pesa_html}

<h2 id="swing">Swing · retroceso ({cfg['nombre_version']})</h2>
{swing_html}
<details><summary>Backtest y calibración del swing</summary>{calib_html}<pre>{swing_md}</pre></details>

<h2 id="datos">Datos y versiones</h2>
<div class="card">{len(estado)} de {len(esperados)} tickers con precios.
{"<div class='warn'>Sin datos: " + ", ".join(faltan) + "</div>" if faltan else ""}</div>
<h3>Versiones de parámetros</h3>
{_tabla(vers, ["version_id", "nombre", "creada"])}
</main>
<script>
const d={json.dumps(comp)};
const css=getComputedStyle(document.documentElement);
const col=['--s1','--s2','--s4','--s3'].map(v=>css.getPropertyValue(v).trim());
if(window.Chart && d.fechas.length){{
  const orden=Object.keys(d.series).sort((a,b)=>(a==='SPY')-(b==='SPY'));
  new Chart(document.getElementById('cmp'),{{type:'line',
  data:{{labels:d.fechas,datasets:orden.map((k,i)=>({{label:k,data:d.series[k],borderColor:k==='SPY'?col[3]:col[i],
    borderWidth:k==='SPY'?1.5:2,pointRadius:0}}))}},
  options:{{interaction:{{mode:'index',intersect:false}},scales:{{x:{{ticks:{{maxTicksLimit:8}}}},
    y:{{type:'logarithmic',ticks:{{callback:v=>'$'+Math.round(v).toLocaleString('es-AR')}}}}}},
  plugins:{{legend:{{position:'bottom'}}}}}}}});
}}
</script></body></html>"""
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    print(f"Tablero generado: {DOCS / 'index.html'}")


if __name__ == "__main__":
    main()
