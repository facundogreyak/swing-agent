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

# ---------------------------------------------------------------------------
# ESTILO de la página. Para cambiar colores, editá las variables de :root.
# (Este bloque NO usa llaves dobles: se puede editar tranquilo.)
# ---------------------------------------------------------------------------
NOMBRE = "Agente Inversor – Facundo"
ESTILO = """
:root{
  --bg:#f5f6fa; --card:#ffffff; --tx:#111827; --mu:#6b7280; --bd:#e5e7eb;
  --acento:#4f46e5; --acento-suave:#eef2ff;
  --pos:#16a34a; --neg:#dc2626;
  --s1:#4f46e5; --s2:#d97706; --s3:#9ca3af; --s4:#0d9488;   /* series: momentum, swing, SPY (referencia), partes iguales */
  --sombra:0 1px 2px rgba(17,24,39,.04), 0 4px 16px rgba(17,24,39,.06);
  --radio:16px;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:110px}
body{margin:0;background:var(--bg);color:var(--tx);
  font:15px/1.5 'Inter',system-ui,-apple-system,'Segoe UI',sans-serif;font-variant-numeric:tabular-nums}
header{position:sticky;top:0;z-index:10;background:rgba(245,246,250,.92);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--bd)}
.barra{max-width:1080px;margin:0 auto;padding:14px 16px 0}
.marca{display:flex;align-items:center;gap:10px}
.logo{width:34px;height:34px;border-radius:10px;background:var(--acento);color:#fff;display:grid;place-items:center;
  font-weight:700;font-size:15px;letter-spacing:-.5px;flex:none}
.marca h1{font-size:18px;margin:0;font-weight:700;letter-spacing:-.3px}
.marca .sub{margin:0}
nav{display:flex;gap:6px;overflow-x:auto;padding:12px 0 12px;scrollbar-width:none}
nav::-webkit-scrollbar{display:none}
nav a{flex:none;color:var(--mu);text-decoration:none;font-size:13px;font-weight:500;padding:6px 12px;border-radius:999px;
  background:var(--card);border:1px solid var(--bd)}
nav a:hover{color:var(--acento);border-color:var(--acento)}
main{max-width:1080px;margin:0 auto;padding:16px 16px 56px}
section{background:var(--card);border-radius:var(--radio);box-shadow:var(--sombra);padding:20px;margin:16px 0}
h2{font-size:18px;margin:0 0 4px;font-weight:700;letter-spacing:-.3px}
h3{font-size:13px;margin:22px 0 8px;color:var(--mu);font-weight:600;text-transform:uppercase;letter-spacing:.04em}
.sub{color:var(--mu);font-size:13px;margin-bottom:10px}
.etiqueta{display:inline-block;font-size:11px;font-weight:600;color:var(--acento);background:var(--acento-suave);
  padding:2px 8px;border-radius:999px;margin-left:6px;vertical-align:middle}
details{margin-top:12px}summary{cursor:pointer;color:var(--acento);font-size:13px;font-weight:500}
.resumen{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin:16px 0 8px}
.resumen-card{display:block;text-decoration:none;color:var(--tx);background:var(--card);border-radius:var(--radio);
  box-shadow:var(--sombra);padding:18px 20px;border-top:4px solid var(--acento)}
.resumen-card:nth-child(2){border-top-color:var(--s2)}
.resumen-card:nth-child(3){border-top-color:var(--s3)}
.evo{height:260px;margin-top:6px}
.resumen-card:hover{box-shadow:0 2px 4px rgba(17,24,39,.06),0 8px 24px rgba(17,24,39,.10)}
.rc-titulo{font-size:13px;color:var(--mu);font-weight:600}
.rc-valor{font-size:30px;font-weight:700;letter-spacing:-.8px;margin:2px 0 10px}
.rc-datos{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.rc-datos span{display:block;font-size:11px;color:var(--mu)}.rc-datos b{font-size:15px;font-weight:600}
.rc-detalle{margin-top:10px;font-size:12px;color:var(--mu)}
.rc-esperado{margin-top:10px;padding-top:10px;border-top:1px solid var(--bd);font-size:11px;color:var(--mu);line-height:1.6}
.resumen-pie{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px;color:var(--mu);padding:4px 4px 0}
.resumen-pie b{font-weight:600}
.rk-controles{display:flex;align-items:center;gap:6px;margin:6px 0 4px;font-size:12px;color:var(--mu)}
.rk-controles button,.ver-todos{font:inherit;font-size:12px;font-weight:500;border:1px solid var(--bd);background:var(--card);
  color:var(--mu);padding:4px 12px;border-radius:999px;cursor:pointer}
.rk-controles button.activo{background:var(--acento);border-color:var(--acento);color:#fff}
.en-cartera{color:var(--acento);font-size:10px;vertical-align:middle}
.ver-todos{margin-top:10px;color:var(--acento);border-color:var(--acento)}
.ranking .sp{display:none;vertical-align:middle}
.ranking[data-p="21"] .sp-21,.ranking[data-p="63"] .sp-63,.ranking[data-p="126"] .sp-126{display:inline}
.ranking tr.extra{display:none}.ranking.todos tr.extra{display:table-row}.ranking.todos .ver-todos{display:none}
.pesos{display:flex;flex-direction:column;gap:12px;margin-top:6px}
.peso-fila{display:grid;grid-template-columns:120px 1fr 90px 70px;align-items:center;gap:12px}
.peso-tk b{display:block;font-size:14px}.peso-tk span,.peso-num span{display:block;font-size:11px;color:var(--mu)}
.peso-barra{height:12px;background:var(--bg);border-radius:4px;overflow:hidden}
.peso-barra i{display:block;height:100%;background:var(--s1);border-radius:0 4px 4px 0}
.peso-spy .peso-barra i{background:var(--s3)}
.peso-num{text-align:right}.peso-num b{font-size:14px}
.peso-res{text-align:right;font-size:14px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0}
.kpi{background:var(--bg);border-radius:12px;padding:12px 14px}
.kpi span{display:block;color:var(--mu);font-size:12px}.kpi b{font-size:19px;font-weight:700;letter-spacing:-.3px}
.chips{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin:12px 0}
.chips div{background:var(--bg);border-radius:12px;padding:12px 14px}
.chips span{display:block;color:var(--mu);font-size:12px}.chips b{font-size:14px;font-weight:600}
.card{background:var(--bg);border-radius:12px;padding:14px}
.tw{overflow-x:auto;margin:0 -4px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:left;padding:9px 8px;border-bottom:1px solid var(--bd);white-space:nowrap}
th{color:var(--mu);font-weight:500;font-size:12px}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:#fafafe}
.badge{display:inline-block;font-size:11px;font-weight:600;padding:2px 9px;border-radius:999px;white-space:nowrap}
.badge::first-letter{text-transform:uppercase}
.b-pos{background:#dcfce7;color:#15803d}.b-neg{background:#fee2e2;color:#b91c1c}
.b-neu{background:var(--acento-suave);color:var(--acento)}.b-gris{background:#f3f4f6;color:#6b7280}
.pos{color:var(--pos);font-weight:500}.neg{color:var(--neg);font-weight:500}.vacio{color:var(--mu)}.warn{color:var(--neg)}
pre{white-space:pre-wrap;font-size:12px;background:var(--bg);border-radius:12px;padding:12px;overflow-x:auto}
footer{max-width:1080px;margin:0 auto;padding:0 16px 40px;color:var(--mu);font-size:12px}
/* Celular: menos columnas, todo más compacto */
@media (max-width:640px){
  .opt{display:none}
  section{padding:16px;border-radius:14px;margin:12px 0}
  main{padding:8px 12px 40px}
  .marca h1{font-size:16px}
  .kpis{grid-template-columns:1fr 1fr}
  .kpi b{font-size:17px}
  th,td{padding:8px 6px}
  td{white-space:normal}
  .ranking .sp{width:58px}
  .ranking th,.ranking td{padding:8px 4px}
  .peso-fila{grid-template-columns:64px 1fr 58px 58px;gap:8px}
  .peso-tk span,.peso-num span{display:none}
  .resumen{grid-template-columns:1fr;gap:10px;margin-top:10px}
  .rc-valor{font-size:26px}
  .resumen-card:nth-child(3){padding:14px 20px}
  .resumen-card:nth-child(3) .rc-valor{font-size:20px;margin-bottom:6px}
  .marca .sub{font-size:12px}
}
"""

ACCIONES_SWING = ("COMPRAR", "VENDER", "MANTENER", "NO_OPERAR")


# ---------------------------------------------------------------------------
# Utilidades de HTML
# ---------------------------------------------------------------------------
def _pct(v, dec=1):
    if v is None or pd.isna(v):
        return "—"
    if abs(v) < 0.5 * 10 ** -(dec + 2):          # evita "-0%" / "+0.0%"
        return f"{0:.{dec}%}".replace(".", ",")
    return f"{v:+.{dec}%}".replace(".", ",")      # formato argentino: coma decimal


def _usd(v):
    """10231.4 -> 'USD 10.231' (punto de miles, formato argentino)"""
    return "USD " + f"{v:,.0f}".replace(",", ".")


def _fecha(s):
    """'2026-09-23' -> '23/09/2026'"""
    try:
        return pd.Timestamp(s).strftime("%d/%m/%Y")
    except Exception:
        return s or "—"


BADGES = {"ENTRA": "b-pos", "COMPRAR": "b-pos", "COMPRA": "b-pos", "SALE": "b-neg", "VENDER": "b-neg",
          "VENTA": "b-neg", "SE_QUEDA": "b-neu", "MANTENER": "b-neu", "NO_OPERAR": "b-gris", "A_EFECTIVO": "b-neg"}


def _tabla(df, columnas, signo=(), nombres=None, opcionales=()):
    """Tabla HTML.
    `signo`: columnas que se pintan verde/rojo según el signo (acepta texto '+x%').
    `opcionales`: columnas que se ocultan en pantallas chicas (celular)."""
    if df is None or df.empty:
        return "<p class='vacio'>Sin datos todavía.</p>"
    nombres = nombres or {}

    def cls(c, extra=""):
        clases = (["opt"] if c in opcionales else []) + ([extra] if extra else [])
        return f" class='{' '.join(clases)}'" if clases else ""

    h = "".join(f"<th{cls(c)}>{nombres.get(c, c)}</th>" for c in columnas)
    filas = ""
    for _, r in df.iterrows():
        celdas = ""
        for c in columnas:
            v = r[c]
            color = ""
            if c in signo and pd.notna(v) and v != "—":
                num = v if isinstance(v, (int, float, np.floating)) else (-1 if str(v).startswith("-") else 1)
                color = "pos" if num > 0 else ("neg" if num < 0 else "")
            txt = '' if pd.isna(v) else v
            if c in ("accion", "lado") and txt in BADGES:
                txt = f"<span class='badge {BADGES[txt]}'>{str(txt).replace('_', ' ').lower()}</span>"
            celdas += f"<td{cls(c, color)}>{txt}</td>"
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
PERIODOS_SPARK = ((21, "1 mes"), (63, "3 meses"), (126, "6 meses"))


def _sparkline(serie, clase, ancho=96, alto=26):
    """Minigráfico SVG de una serie de precios (verde si subió en el período, rojo si bajó)."""
    s = serie.dropna()
    if len(s) < 3:
        return f"<span class='sp {clase}'></span>"
    lo, hi = float(s.min()), float(s.max())
    rango = (hi - lo) or 1.0
    xs = np.linspace(2, ancho - 4, len(s))
    ys = alto - 3 - (s.values - lo) / rango * (alto - 6)
    puntos = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    color = "var(--pos)" if s.iloc[-1] >= s.iloc[0] else "var(--neg)"
    return (f"<svg class='sp {clase}' width='{ancho}' height='{alto}' viewBox='0 0 {ancho} {alto}' aria-hidden='true'>"
            f"<polyline points='{puntos}' fill='none' stroke='{color}' stroke-width='1.6' stroke-linejoin='round' "
            f"stroke-linecap='round'/><circle cx='{xs[-1]:.1f}' cy='{ys[-1]:.1f}' r='2.2' fill='{color}'/></svg>")


def _tabla_ranking(df, visibles=15):
    """Ranking completo con minigráficos. Muestra las primeras `visibles` filas y el resto con un botón."""
    cols = [("puesto", "#", ""), ("cambio 1 sem.", "semana", ""), ("ticker", "ticker", ""), ("sector", "sector", "opt"),
            ("spark", "evolución", ""), ("1 mes", "1 mes", ""), ("3 meses", "3 meses", ""),
            ("6 meses*", "6 meses*", "opt"), ("12 meses*", "12 meses*", "opt")]
    signo = {"1 mes", "3 meses", "6 meses*", "12 meses*", "cambio 1 sem."}
    h = "".join(f"<th class='{c}'>{n}</th>" for _, n, c in cols)
    filas = ""
    for k, (_, r) in enumerate(df.iterrows()):
        celdas = ""
        for col, _, c in cols:
            v = r[col]
            color = ""
            if col in signo and isinstance(v, str) and v not in ("—", "=", "nuevo"):
                color = "neg" if v.startswith(("-", "▼")) else "pos"
            clases = " ".join(x for x in (c, color) if x)
            celdas += f"<td class='{clases}'>{v}</td>"
        filas += f"<tr class='{'extra' if k >= visibles else ''}'>{celdas}</tr>"
    botones = "".join(f"<button type='button' data-p='{n}' class='{'activo' if n == 63 else ''}'>{etq}</button>"
                      for n, etq in PERIODOS_SPARK)
    return (f"<div class='ranking' data-p='63'>"
            f"<div class='rk-controles'><span>Evolución:</span>{botones}</div>"
            f"<div class='tw'><table><thead><tr>{h}</tr></thead><tbody>{filas}</tbody></table></div>"
            + (f"<button type='button' class='ver-todos'>Ver las {len(df)} acciones</button>" if len(df) > visibles else "")
            + "</div>")


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
    df["ticker"] = [f"<b>{tk}</b>" + (" <span class='en-cartera' title='En la cartera momentum'>●</span>"
                                       if tk in en_cartera else "") for tk in df.index]
    df["spark"] = [
        "".join(_sparkline(P["close"][tk].iloc[-n - 1:], f"sp-{n}") for n, _ in PERIODOS_SPARK)
        for tk in df.index]

    nuevos_top10 = [t for t in df.head(10).index if rk_antes.get(t, 99) > 10]
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
        ", ".join(f"{tk} ({r['cambio 1 sem.']})" for tk, r in aceleran.iterrows()) or "—") + "</b></div>"
    resumen += "</div>"

    html = (f"<div class='sub'>Ranking de las {len(df)} acciones al cierre del {fecha} por puntaje <b>{m['puntaje']}</b>. "
            "<span class='en-cartera'>●</span> = está en la cartera momentum. *6 y 12 meses sin contar el último mes.</div>"
            + resumen
            + _tabla_ranking(df)
            + "<h3>Sectores</h3>"
            + _tabla(sect, ["sector", "acciones", "en_top10", "prom_1m", "prom_3m"], signo=("prom_1m", "prom_3m"),
                     opcionales=("acciones",),
                     nombres={"en_top10": "en el top 10", "prom_1m": "suba prom. 1 mes", "prom_3m": "suba prom. 3 meses"}))
    return html, {"P": P}


def _proxima_revision(ult_reb, P, cfg):
    if not ult_reb:
        return "en la próxima corrida"
    k = P["fechas"].get_indexer([pd.Timestamp(ult_reb)])[0]
    faltan = cfg["momentum"]["rebalanceo_dias"] - (len(P["fechas"]) - 1 - k)
    return f"en {faltan} ruedas" if faltan > 1 else ("mañana" if faltan == 1 else "en la próxima corrida")


def _variaciones(serie, base_inicial):
    """Valor, variación del último día, del mes en curso y desde el inicio."""
    if serie is None or not len(serie):
        return base_inicial, None, None, 0.0
    s = serie.copy()
    s.index = pd.to_datetime(s.index)
    valor = float(s.iloc[-1])
    hoy = valor / float(s.iloc[-2]) - 1 if len(s) > 1 else None
    previo = s[s.index < s.index[-1].to_period("M").start_time]
    base_mes = float(previo.iloc[-1]) if len(previo) else base_inicial
    return valor, hoy, valor / base_mes - 1, valor / base_inicial - 1


def _banda_esperada(archivo, n):
    """Rango de resultados que dio el backtest en todas las ventanas de `n` ruedas (percentiles 10-50-90)."""
    f = REP / archivo
    if n < 1 or not f.exists():
        return None
    s = pd.read_csv(f, index_col="fecha")["total"]
    r = (s.shift(-n) / s - 1).dropna()
    if len(r) < 50:
        return None
    return r.quantile(0.10), r.quantile(0.50), r.quantile(0.90)


def _veredicto(real, banda):
    if banda is None or real is None:
        return ""
    lo, med, hi = banda
    if real < lo:
        est, clase = "por debajo de lo esperado", "b-neg"
    elif real > hi:
        est, clase = "por encima de lo esperado", "b-pos"
    else:
        est, clase = "dentro de lo esperado", "b-neu"
    return (f"<div class='rc-esperado'><span class='badge {clase}'>{est}</span> "
            f"<span>el backtest daba entre {_pct(lo)} y {_pct(hi)} (típico {_pct(med)}) para este plazo</span></div>")


def seccion_resumen(con, con_diario, cfg, P):
    """Bloque de arriba: cómo vienen las carteras, SPY y qué pasó en la última corrida."""
    cap0 = cfg["riesgo"]["capital_inicial_usd"]
    tarjetas = ""
    est = con_diario.execute("SELECT estado_json FROM estado_motor WHERE nombre='momentum'").fetchone()
    est = json.loads(est[0]) if est else {}
    n_acc = sum(1 for t in est.get("pos", {}) if t != cfg["benchmark"])
    for nombre, clave, ancla, detalle, archivo in (
            ("Cartera momentum", "momentum", "#momentum",
             f"{n_acc} acciones · próxima revisión {_proxima_revision(est.get('ult_reb'), P, cfg)}",
             "momentum_equity.csv"),
            ("Cartera swing", "paper", "#swing", None, "backtest_equity.csv")):
        eq = pd.read_sql("SELECT fecha, total FROM equity WHERE version_id=? ORDER BY fecha", con_diario,
                         params=(clave,)).set_index("fecha")["total"]
        valor, hoy, mes, total = _variaciones(eq, cap0)
        if detalle is None:
            n = con_diario.execute("SELECT COUNT(*) FROM operaciones WHERE estado='ABIERTA'").fetchone()[0]
            detalle = f"{n} posiciones abiertas · opera cuando aparece una señal"

        def dato(etq, v):
            c = "" if v is None or abs(v) < 5e-5 else ("pos" if v > 0 else "neg")
            return f"<div><span>{etq}</span><b class='{c}'>{_pct(v, 2) if v is not None else '—'}</b></div>"
        tarjetas += (f"<a class='resumen-card' href='{ancla}'><div class='rc-titulo'>{nombre}</div>"
                     f"<div class='rc-valor'>{_usd(valor)}</div>"
                     f"<div class='rc-datos'>{dato('Hoy', hoy)}{dato('Mes', mes)}{dato('Desde inicio', total)}</div>"
                     f"<div class='rc-detalle'>{detalle}</div>"
                     f"{_veredicto(total, _banda_esperada(archivo, len(eq) - 1))}</a>")

    # SPY como referencia: USD 10.000 invertidos el mismo día que arrancaron las carteras
    eqs = pd.read_sql("SELECT version_id, fecha, total FROM equity WHERE version_id IN ('momentum','paper') "
                      "ORDER BY fecha", con_diario)
    inicio = eqs.fecha.min() if len(eqs) else P["fechas"][-1].strftime("%Y-%m-%d")
    spy = P["bench_close"].dropna()
    spy.index = spy.index.strftime("%Y-%m-%d")
    spy_c = spy[spy.index >= inicio]
    spy_c = spy_c / spy_c.iloc[0] * cap0
    valor, s_hoy, s_mes, s_total = _variaciones(spy_c, cap0)

    def dato(etq, v):
        c = "" if v is None or abs(v) < 5e-5 else ("pos" if v > 0 else "neg")
        return f"<div><span>{etq}</span><b class='{c}'>{_pct(v, 2) if v is not None else '—'}</b></div>"
    tarjetas += (f"<a class='resumen-card' href='#comparacion'><div class='rc-titulo'>SPY · referencia</div>"
                 f"<div class='rc-valor'>{_usd(valor)}</div>"
                 f"<div class='rc-datos'>{dato('Hoy', s_hoy)}{dato('Mes', s_mes)}{dato('Desde inicio', s_total)}</div>"
                 f"<div class='rc-detalle'>USD 10.000 puestos en SPY el {_fecha(inicio)}</div></a>")

    # Evolución desde el inicio (gráfico): las tres curvas sobre las mismas fechas
    piv = eqs.pivot(index="fecha", columns="version_id", values="total") if len(eqs) else pd.DataFrame()
    evo = {"fechas": [], "series": {}}
    if len(piv) >= 2:
        piv["SPY"] = spy_c.reindex(piv.index).ffill()
        piv = piv.ffill().fillna(cap0)
        evo = {"fechas": list(piv.index),
               "series": {"Momentum": piv.get("momentum", pd.Series(dtype=float)).round(0).tolist(),
                          "Swing": piv.get("paper", pd.Series(dtype=float)).round(0).tolist(),
                          "SPY": piv["SPY"].round(0).tolist()}}
    ult = con_diario.execute("SELECT MAX(fecha) FROM decisiones").fetchone()[0]
    nov = pd.read_sql("SELECT ticker, accion FROM decisiones WHERE fecha=? AND accion IN "
                      "('ENTRA','SALE','COMPRAR','VENDER','A_EFECTIVO')", con_diario, params=(ult,)) if ult else pd.DataFrame()
    if len(nov):
        grupos = []
        for acc, etq in (("ENTRA", "Momentum compra"), ("SALE", "Momentum vende"),
                         ("COMPRAR", "Swing compra"), ("VENDER", "Swing vende")):
            ts = nov[nov.accion == acc].ticker.tolist()
            if ts:
                grupos.append(f"<b>{etq}:</b> {', '.join(ts)}")
        novedades = " · ".join(grupos)
    else:
        novedades = "Sin compras ni ventas: las carteras siguen igual."
    grafico = ("<section><h2>Evolución desde el inicio</h2>"
               f"<div class='sub'>Valor de cada cartera simulada desde el {_fecha(inicio)}, "
               "comparado con haber puesto lo mismo en SPY.</div>"
               + ("<div class='evo'><canvas id='evo'></canvas></div>" if evo["fechas"] else
                  "<p class='vacio'>El gráfico aparece a partir del segundo día de operación.</p>")
               + "</section>")
    return (f"<div class='resumen'>{tarjetas}</div>"
            f"<div class='resumen-pie'><span>Última corrida ({_fecha(ult)}): {novedades}</span></div>"
            + grafico), evo


def _barras_peso(pos, total, bench):
    """Barras horizontales: peso de cada posición (ancho) + valor y resultado en texto."""
    if pos is None or not len(pos):
        return "<p class='vacio'>Sin posiciones todavía: las compras se hacen en la apertura siguiente a la revisión.</p>"
    maximo = max(pos["_v"].max() / total, 1e-9)
    filas = ""
    for _, r in pos.iterrows():
        peso = r["_v"] / total
        clase_res = "pos" if str(r["resultado"]).startswith("+") else ("neg" if str(r["resultado"]).startswith("-") else "")
        es_spy = r["ticker"] == bench
        filas += (f"<div class='peso-fila{' peso-spy' if es_spy else ''}'>"
                  f"<div class='peso-tk'><b>{r['ticker']}</b><span>{'resto a SPY' if es_spy else 'desde ' + r['desde']}</span></div>"
                  f"<div class='peso-barra' title='{peso:.1%}'><i style='width:{peso / maximo * 100:.1f}%'></i></div>"
                  f"<div class='peso-num'><b>{f'{peso:.1%}'.replace('.', ',')}</b><span>USD {r['valor USD']}</span></div>"
                  f"<div class='peso-res {clase_res}'>{r['resultado']}</div></div>")
    return f"<div class='pesos'>{filas}</div>"


def _ars(v, dec=0):
    if v is None or pd.isna(v):
        return "—"
    s = f"{v:,.{dec}f}"
    return "$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def seccion_byma(cfg):
    """Cartera y órdenes traducidas a CEDEARs en pesos + CEDEARs caros/baratos según el CCL implícito."""
    f_c, f_o, f_j = REP / "cedears.csv", REP / "ordenes_cedears.csv", REP / "ccl.json"
    if not f_c.exists():
        return "<p class='vacio'>Se calcula en la próxima corrida.</p>"
    ced = pd.read_csv(f_c)
    ccl = json.loads(f_j.read_text())["ccl"] if f_j.exists() else float("nan")
    ords = pd.read_csv(f_o) if f_o.exists() and f_o.stat().st_size > 1 else pd.DataFrame()

    def badge(e):
        cls = {"caro": "b-neg", "barato": "b-pos", "normal": "b-gris"}.get(e, "b-gris")
        txt = e if e in ("caro", "barato", "normal") else "revisar"
        return f"<span class='badge {cls}' title='{e}'>{txt}</span>"

    cartera = ords[ords.tipo == "EN CARTERA"].copy() if len(ords) else pd.DataFrame()
    total_ars = cartera.monto_ars.sum() if len(cartera) else 0
    validos = ced[ced.prima.notna()]
    kp = _kpis([("Dólar CCL implícito", _ars(ccl, 2)),
                ("Cartera momentum en pesos", _ars(total_ars) if total_ars else "—"),
                ("CEDEARs caros hoy", f"{(ced.estado == 'caro').sum()}"),
                ("CEDEARs baratos hoy", f"{(ced.estado == 'barato').sum()}")])

    def tabla_ordenes(df):
        d = df.copy()
        d["CEDEAR"] = d.cedear
        d["cantidad"] = d.cantidad.map(lambda v: "—" if pd.isna(v) else f"{int(v):,}".replace(",", "."))
        d["precio"] = d.precio_ars.map(_ars)
        d["monto"] = d.monto_ars.map(_ars)
        d["precio hoy"] = d.estado_precio.map(badge)
        return _tabla(d, ["CEDEAR", "cantidad", "precio", "monto", "precio hoy"], opcionales=("precio",))

    html = kp
    html += ("<h3>Cartera momentum expresada en CEDEARs</h3>" + tabla_ordenes(cartera) if len(cartera)
             else "<p class='vacio'>Todavía no hay posiciones.</p>")
    prox = ords[ords.tipo.isin(["COMPRAR", "VENDER"])] if len(ords) else pd.DataFrame()
    if len(prox):
        p2 = prox.copy()
        p2["accion"] = p2.tipo.map({"COMPRAR": "ENTRA", "VENDER": "SALE"})
        html += "<h3>Órdenes para la próxima apertura</h3>"
        p2["CEDEAR"] = p2.cedear
        p2["cantidad"] = p2.cantidad.map(lambda v: "—" if pd.isna(v) else f"{int(v):,}".replace(",", "."))
        p2["monto"] = p2.monto_ars.map(_ars)
        p2["precio hoy"] = p2.estado_precio.map(badge)
        html += _tabla(p2, ["accion", "CEDEAR", "cantidad", "monto", "precio hoy"])
    orden = validos.sort_values("prima")
    extremos = pd.concat([orden.head(5), orden.tail(5)]).drop_duplicates()
    extremos = extremos.sort_values("prima", ascending=False)

    def tabla_prima(df):
        d = df.copy()
        d["CEDEAR"] = d.cedear
        d["precio"] = d.precio_ars.map(_ars)
        d["CCL implícito"] = d.ccl_implicito.map(lambda v: _ars(v, 2))
        d["vs. CCL"] = d.prima.map(lambda v: _pct(v, 1))
        d["estado "] = d.estado.map(badge)
        return _tabla(d, ["CEDEAR", "precio", "CCL implícito", "vs. CCL", "estado "], signo=(),
                      opcionales=("precio",))
    html += ("<h3>Más caros y más baratos hoy</h3>"
             "<div class='sub'>Un CEDEAR está caro cuando su dólar implícito supera al del resto: pagás más pesos "
             "por la misma acción. Conviene evitar comprar caro y vender barato.</div>" + tabla_prima(extremos))
    html += (f"<details><summary>Ver los {len(ced)} CEDEARs</summary>"
             + tabla_prima(ced.sort_values("prima", ascending=False, na_position="last")) + "</details>")
    revisar = ced[ced.prima.isna()]
    if len(revisar):
        html += ("<div class='sub' style='margin-top:10px'>Sin dato confiable en pesos: "
                 + ", ".join(f"{r.cedear} ({r.estado})" for r in revisar.itertuples()) + "</div>")
    html += ("<div class='sub' style='margin-top:10px'>Cantidades para la cartera simulada de USD "
             f"{cfg['riesgo']['capital_inicial_usd']:,.0f}".replace(",", ".")
             + " al CCL implícito, redondeadas hacia abajo. Precios de cierre de Yahoo Finance: son referencia; "
               "antes de operar verificá precio y ratio en tu broker. No es recomendación de inversión.</div>")
    return html


def seccion_cartera_momentum(con_diario, cfg, P):
    fila = con_diario.execute("SELECT ultima_fecha, estado_json FROM estado_motor WHERE nombre='momentum'").fetchone()
    if not fila:
        return "<p class='vacio'>La cartera momentum arranca en la próxima corrida.</p>"
    est = json.loads(fila[1])
    cap0 = cfg["riesgo"]["capital_inicial_usd"]
    eqm = pd.read_sql("SELECT fecha, efectivo, invertido, total FROM equity WHERE version_id='momentum' ORDER BY fecha",
                      con_diario)
    total = eqm.total.iloc[-1] if len(eqm) else cap0
    bench = cfg["benchmark"]
    precios = {t: float(P["close"][t].iloc[-1]) for t in P["tickers"]}
    precios[bench] = float(P["bench_close"].iloc[-1])

    pos = []
    for t, q in est.get("pos", {}).items():
        valor = q * precios.get(t, np.nan)
        costo = est.get("costo", {}).get(t, np.nan)
        pos.append({"ticker": t, "desde": _fecha(est.get("entrada", {}).get(t, "")), "valor USD": _usd(valor)[4:],
                    "peso": f"{valor / total:.1%}".replace(".", ","), "resultado": _pct(valor / costo - 1 if costo else None),
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
        ops["monto_usd"] = ops.monto_usd.map(lambda v: _usd(v)[4:])
        ops["fecha"] = ops.fecha.map(_fecha)
    prox = _proxima_revision(ult_reb, P, cfg)

    return (_kpis([("En acciones", f"{en_acciones / total:.0%}" if total else "—"),
                   ("En SPY", f"{en_spy / total:.0%}" if total else "—"),
                   ("Última revisión", _fecha(ult_reb)), ("Próxima revisión", prox or "—")])
            + "<h3>Posiciones y peso en la cartera</h3>"
            + _barras_peso(pos, total, bench)
            + (f"<h3>Decisiones de la última revisión ({_fecha(ult_reb)})</h3>" + _tabla(dec, ["ticker", "accion", "motivo"])
               if len(dec) else "")
            + "<h3>Últimas operaciones</h3>"
            + _tabla(ops, ["fecha", "ticker", "lado", "monto_usd", "retorno", "motivo"], signo=("retorno",),
                     nombres={"monto_usd": "monto USD"}, opcionales=("monto_usd", "motivo")))


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
    if (REP / "momentum_equity_ampliado.csv").exists():
        e = pd.read_csv(REP / "momentum_equity_ampliado.csv", index_col="fecha")
        series["Momentum (universo ampliado)"] = e.total
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
                     signo=("retorno anual", "mejor año", "peor año", "total"),
                     opcionales=("mejor año", "peor año", "total"))
            + "<div class='card' style='margin-top:12px;height:320px'><canvas id='cmp'></canvas></div>"
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
            + _tabla(t, ["decisión", "impacto", "mejor antes", "mejor después", "¿coincide?", "valores (después)"],
                     opcionales=("mejor antes", "mejor después", "valores (después)")))


def seccion_swing(con, con_diario, cfg):
    cuenta = con_diario.execute("SELECT capital_inicial, inicio, ultima_fecha FROM cuenta WHERE id=1").fetchone()
    if not cuenta:
        return "<p class='vacio'>El paper trading swing arranca en la próxima corrida.</p>"
    ult_paper = cuenta[2]
    abiertas = pd.read_sql("SELECT ticker, fecha_entrada, precio_entrada, stop, objetivo, cantidad, riesgo_usd, "
                           "costo_total, dias FROM operaciones WHERE estado='ABIERTA' ORDER BY fecha_entrada",
                           con_diario)
    cerradas = pd.read_sql("SELECT ticker, fecha_entrada, fecha_salida, motivo_salida, dias, r_multiple, pnl_usd "
                           "FROM operaciones WHERE estado='CERRADA' ORDER BY fecha_salida DESC", con_diario)
    decis = pd.read_sql(f"SELECT ticker, accion, motivo FROM decisiones WHERE fecha=? AND accion IN {ACCIONES_SWING} "
                        "ORDER BY CASE accion WHEN 'COMPRAR' THEN 0 WHEN 'VENDER' THEN 1 "
                        "WHEN 'MANTENER' THEN 2 ELSE 3 END, ticker", con_diario, params=(ult_paper,))
    if len(abiertas):
        ultimos = {r.ticker: con.execute("SELECT close FROM precios WHERE ticker=? ORDER BY fecha DESC LIMIT 1",
                                         (r.ticker,)).fetchone()[0] for r in abiertas.itertuples()}
        abiertas["precio_actual"] = abiertas.ticker.map(ultimos).round(2)
        abiertas["r_multiple"] = ((abiertas.precio_actual * abiertas.cantidad - abiertas.costo_total)
                                  / abiertas.riesgo_usd).round(2)
        for c in ("precio_entrada", "stop", "objetivo"):
            abiertas[c] = abiertas[c].round(2)
    activas = decis[decis.accion != "NO_OPERAR"]
    return (_kpis([("Posiciones abiertas", f"{len(abiertas)}"), ("Operaciones cerradas", f"{len(cerradas)}"),
                   ("Aciertos", f"{(cerradas.pnl_usd > 0).mean():.0%}" if len(cerradas) else "—"),
                   ("R promedio", f"{cerradas.r_multiple.mean():.2f}" if len(cerradas) else "—")])
            + f"<h3>Decisiones del {_fecha(ult_paper)}</h3>"
            + (_tabla(activas, ["ticker", "accion", "motivo"]) if len(activas)
               else "<p class='vacio'>Sin compras ni ventas: ningún papel cumplió todas las condiciones.</p>")
            + f"<details><summary>Ver los {len(decis)} papeles analizados</summary>"
            + _tabla(decis, ["ticker", "accion", "motivo"]) + "</details>"
            + "<h3>Posiciones abiertas</h3>"
            + _tabla(abiertas, ["ticker", "fecha_entrada", "dias", "precio_entrada", "precio_actual",
                                "stop", "objetivo", "r_multiple"], signo=("r_multiple",),
                     opcionales=("fecha_entrada", "precio_entrada", "stop", "objetivo"))
            + "<h3>Operaciones cerradas</h3>"
            + _tabla(cerradas.head(20), ["ticker", "fecha_entrada", "fecha_salida", "motivo_salida",
                                         "dias", "r_multiple", "pnl_usd"], signo=("r_multiple", "pnl_usd"),
                     opcionales=("fecha_entrada", "dias", "pnl_usd")))


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
    ahora = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m %H:%M")

    estado = pd.read_sql("SELECT ticker, COUNT(*) AS velas, MAX(fecha) AS ultima_fecha FROM precios GROUP BY ticker", con)
    esperados = [cfg["benchmark"]] + [p[k] for p in cfg["universo"] for k in ("subyacente", "cedear")]
    faltan = sorted(set(esperados) - set(estado.ticker))
    ult = estado.ultima_fecha.max() if len(estado) else "—"
    vers = pd.read_sql("SELECT version_id, nombre, creada FROM versiones_params ORDER BY creada DESC", con_diario)

    booms_html, ctx = seccion_booms(con, con_diario, cfg)
    cartera_html = seccion_cartera_momentum(con_diario, cfg, ctx["P"]) if ctx else ""
    resumen_html, evo = seccion_resumen(con, con_diario, cfg, ctx["P"]) if ctx else ("", {"fechas": [], "series": {}})
    comp_html, comp = seccion_comparacion(cfg)
    byma_html = seccion_byma(cfg)
    pesa_html = seccion_que_pesa(cfg)
    swing_html = seccion_swing(con, con_diario, cfg)
    calib_html = seccion_calibracion_swing()
    swing_md = (REP / "backtest.md").read_text(encoding="utf-8") if (REP / "backtest.md").exists() else ""
    m = cfg["momentum"]
    cap0 = cfg["riesgo"]["capital_inicial_usd"]

    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{NOMBRE}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>{ESTILO}</style></head><body>
<header><div class="barra">
  <div class="marca"><div><h1>{NOMBRE}</h1>
  <div class="sub">Simulado, sin dinero real · <span class="opt">Actualizado </span>{ahora}<span class="opt"> · Datos al {_fecha(ult)}</span></div></div></div>
  <nav><a href="#momentum">Cartera</a><a href="#byma">En pesos</a><a href="#booms">Booms</a><a href="#comparacion">Comparación</a>
  <a href="#pesa">Qué pesa más</a><a href="#swing">Swing</a><a href="#datos">Datos</a></nav>
</div></header>
<main>

{resumen_html}

<section id="momentum">
<h2>Cartera momentum <span class="etiqueta">100% invertida</span></h2>
<div class="sub">Las {m['top_n']} acciones más fuertes (puntaje {m['puntaje']}), revisión cada {m['rebalanceo_dias']} ruedas,
margen {m['buffer']} puestos, máx. {m['max_por_sector'] or '—'} por sector. Lo que no va a acciones queda en SPY.</div>
{cartera_html}
</section>

<section id="byma">
<h2>Operar en BYMA <span class="etiqueta">CEDEARs en pesos</span></h2>
{byma_html}
</section>

<section id="booms">
<h2>Booms del momento</h2>
{booms_html}
</section>

<section id="comparacion">
<h2>Comparación de estrategias <span class="etiqueta">backtest</span></h2>
{comp_html}
</section>

<section id="pesa">
<h2>Qué pesa más en el resultado</h2>
{pesa_html}
</section>

<section id="swing">
<h2>Swing · retroceso <span class="etiqueta">{cfg['nombre_version']}</span></h2>
{swing_html}
<details><summary>Backtest y calibración del swing</summary>{calib_html}<pre>{swing_md}</pre></details>
</section>

<section id="datos">
<h2>Datos y versiones</h2>
<div class="card">{len(estado)} de {len(esperados)} tickers con precios.
{"<div class='warn'>Sin datos: " + ", ".join(faltan) + "</div>" if faltan else ""}</div>
<h3>Versiones de parámetros</h3>
{_tabla(vers, ["version_id", "nombre", "creada"], opcionales=("version_id",))}
</section>
</main>
<footer>{NOMBRE} · Herramienta de análisis y simulación. No es asesoramiento financiero.</footer>
<script>
document.querySelectorAll('.ranking').forEach(rk=>{{
  rk.querySelectorAll('.rk-controles button').forEach(b=>b.addEventListener('click',()=>{{
    rk.dataset.p=b.dataset.p; rk.querySelectorAll('.rk-controles button').forEach(x=>x.classList.toggle('activo',x===b));}}));
  const vt=rk.querySelector('.ver-todos'); if(vt) vt.addEventListener('click',()=>rk.classList.add('todos'));
}});
const d={json.dumps(comp)};
const evo={json.dumps(evo)};
const css=getComputedStyle(document.documentElement);
const v=n=>css.getPropertyValue(n).trim();
const colores={{'Momentum':v('--s1'),'Momentum (universo ampliado)':v('--s1'),'Swing (retroceso)':v('--s2'),'SPY':v('--s3'),'50 acciones en partes iguales':v('--s4')}};
if(window.Chart){{ Chart.defaults.font.family="'Inter',system-ui,sans-serif"; Chart.defaults.color=v('--mu'); }}
const usd=x=>'USD '+Math.round(x).toLocaleString('es-AR');
const fechaCorta=s=>s.slice(8,10)+'/'+s.slice(5,7);
if(window.Chart && evo.fechas.length){{
  const col={{'Momentum':v('--s1'),'Swing':v('--s2'),'SPY':v('--s3')}};
  new Chart(document.getElementById('evo'),{{type:'line',
    data:{{labels:evo.fechas,datasets:Object.keys(evo.series).map(k=>({{label:k,data:evo.series[k],
      borderColor:col[k],backgroundColor:col[k],borderWidth:k==='SPY'?1.5:2,borderDash:k==='SPY'?[5,4]:[],
      pointRadius:0,pointHoverRadius:4,tension:.15}})).concat([{{label:'inicio',data:evo.fechas.map(()=>{cap0}),
      borderColor:v('--mu'),borderWidth:1,borderDash:[2,3],pointRadius:0,pointHoverRadius:0}}])}},
    options:{{maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
      scales:{{x:{{grid:{{display:false}},ticks:{{maxTicksLimit:6,callback:function(val){{return fechaCorta(this.getLabelForValue(val));}}}}}},
               y:{{grid:{{color:v('--bd')}},ticks:{{callback:x=>innerWidth<640?(x/1000).toLocaleString('es-AR',{{maximumFractionDigits:1}})+'k':usd(x)}}}}}},
      plugins:{{legend:{{position:'bottom',labels:{{usePointStyle:true,pointStyle:'line',boxWidth:18,filter:i=>i.text!=='inicio'}}}},
        tooltip:{{filter:i=>i.dataset.label!=='inicio',callbacks:{{title:it=>fechaCorta(it[0].label),label:c=>' '+c.dataset.label+': '+usd(c.parsed.y)}}}}}}}}}});
}}
if(window.Chart && d.fechas.length){{
  const orden=Object.keys(d.series).sort((a,b)=>(a==='SPY')-(b==='SPY'));
  new Chart(document.getElementById('cmp'),{{type:'line',
  data:{{labels:d.fechas,datasets:orden.map(k=>({{label:k,data:d.series[k],borderColor:colores[k]||v('--s3'),
    borderWidth:k==='Momentum'?2.5:1.5,pointRadius:0,borderDash:k==='SPY'?[4,3]:(k.includes('ampliado')?[7,4]:[])}}))}},
  options:{{maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
    scales:{{x:{{ticks:{{maxTicksLimit:6,callback:function(val){{const s=this.getLabelForValue(val);const m=['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];return m[+s.slice(5,7)-1]+' '+s.slice(0,4);}}}},grid:{{display:false}}}},
    y:{{type:'logarithmic',grid:{{color:v('--bd')}},ticks:{{callback:x=>'$'+Math.round(x).toLocaleString('es-AR')}}}}}},
  plugins:{{legend:{{position:'bottom',labels:{{boxWidth:12,usePointStyle:true}}}}}}}}}});
}}
</script></body></html>"""
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    print(f"Tablero generado: {DOCS / 'index.html'}")


if __name__ == "__main__":
    main()
