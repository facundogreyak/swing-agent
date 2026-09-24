"""
tablero.py - Genera la página web del agente (docs/index.html) para GitHub Pages.
Se abre desde cualquier computadora o celular.
Ejecutar:  python tablero.py   (lo corre GitHub Actions después de cada corrida)
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
import yaml

import db

REP = Path("reportes")
DOCS = Path("docs")


def _tabla(df, columnas):
    if df is None or df.empty:
        return "<p class='vacio'>Sin datos todavía.</p>"
    h = "".join(f"<th>{c}</th>" for c in columnas)
    filas = ""
    for _, r in df.iterrows():
        celdas = ""
        for c in columnas:
            v = r[c]
            clase = ""
            if c in ("r_multiple", "pnl_usd") and pd.notna(v):
                clase = " class='pos'" if v > 0 else " class='neg'"
            celdas += f"<td{clase}>{v}</td>"
        filas += f"<tr>{celdas}</tr>"
    return f"<div class='tw'><table><thead><tr>{h}</tr></thead><tbody>{filas}</tbody></table></div>"


def main():
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    con = db.conectar(cfg["datos"]["base_datos"])
    DOCS.mkdir(exist_ok=True)
    ahora = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

    eq = pd.read_csv(REP / "backtest_equity.csv") if (REP / "backtest_equity.csv").exists() else None
    ops = pd.read_csv(REP / "backtest_operaciones.csv") if (REP / "backtest_operaciones.csv").exists() else None
    capital0 = cfg["riesgo"]["capital_inicial_usd"]

    kpis = ""
    if ops is not None and len(ops) and eq is not None:
        def dd(s):
            return ((s / s.cummax()) - 1).min()
        datos_kpi = [
            ("Retorno agente", f"{eq.total.iloc[-1] / capital0 - 1:.1%}"),
            ("Retorno SPY", f"{eq.spy.iloc[-1] / capital0 - 1:.1%}"),
            ("Máx. caída agente", f"{dd(eq.total):.1%}"),
            ("Operaciones", f"{len(ops)}"),
            ("Aciertos", f"{(ops.pnl_usd > 0).mean():.0%}"),
            ("R promedio", f"{ops.r_multiple.mean():.2f}"),
        ]
        kpis = "".join(f"<div class='kpi'><span>{k}</span><b>{v}</b></div>" for k, v in datos_kpi)

    # Estado de los datos
    estado = pd.read_sql(
        "SELECT ticker, COUNT(*) AS velas, MAX(fecha) AS ultima_fecha FROM precios GROUP BY ticker", con)
    esperados = [cfg["benchmark"]] + [p[k] for p in cfg["universo"] for k in ("subyacente", "cedear")]
    faltan = sorted(set(esperados) - set(estado.ticker))
    ult = estado.ultima_fecha.max() if len(estado) else "—"

    # Versiones de parámetros
    vers = pd.read_sql("SELECT version_id, nombre, creada FROM versiones_params ORDER BY creada DESC", con)

    serie = {"fechas": [], "agente": [], "spy": []}
    if eq is not None:
        serie = {"fechas": eq.fecha.tolist(), "agente": eq.total.tolist(), "spy": eq.spy.tolist()}

    ultimas = ops.tail(15).iloc[::-1] if ops is not None else None
    cols_ops = ["ticker", "fecha_entrada", "fecha_salida", "motivo_salida", "dias", "r_multiple", "pnl_usd"]

    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agente Swing</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{{--bg:#f7f7f5;--card:#fff;--tx:#1d1d1b;--mu:#6b6b66;--bd:#e4e4df;--pos:#1a7f4b;--neg:#c0392b;--a:#2f5bd3;--b:#9a9a92}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151514;--card:#1f1f1d;--tx:#ecece8;--mu:#9a9a92;--bd:#33332f;--pos:#4cc38a;--neg:#ef6f5e;--a:#7c9cff;--b:#77776f}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--tx);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:24px 16px 48px}}
h1{{font-size:22px;margin:0}}h2{{font-size:16px;margin:28px 0 10px}}.sub{{color:var(--mu);font-size:13px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-top:18px}}
.kpi{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px}}
.kpi span{{display:block;color:var(--mu);font-size:12px}}.kpi b{{font-size:20px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:14px}}
.tw{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--bd);white-space:nowrap}}th{{color:var(--mu);font-weight:500}}
.pos{{color:var(--pos)}}.neg{{color:var(--neg)}}.vacio{{color:var(--mu)}}.warn{{color:var(--neg)}}
</style></head><body><main>
<h1>Agente Swing · CEDEARs</h1>
<div class="sub">Paper trading (simulado) · Actualizado {ahora} (hora Argentina) · Datos hasta {ult} · Versión {cfg['nombre_version']}</div>

<h2>Backtest de la estrategia</h2>
<div class="kpis">{kpis or "<p class='vacio'>Todavía no se corrió el backtest.</p>"}</div>
<div class="card" style="margin-top:12px"><canvas id="eq" height="120"></canvas></div>

<h2>Últimas operaciones del backtest</h2>
{_tabla(ultimas, cols_ops)}

<h2>Estado de los datos</h2>
<div class="card">{len(estado)} de {len(esperados)} tickers con precios.
{"<div class='warn'>Sin datos: " + ", ".join(faltan) + "</div>" if faltan else ""}</div>

<h2>Versiones de parámetros</h2>
{_tabla(vers, ["version_id", "nombre", "creada"])}
</main>
<script>
const d={json.dumps(serie)};
const css=getComputedStyle(document.documentElement);
if(d.fechas.length){{new Chart(document.getElementById('eq'),{{type:'line',
data:{{labels:d.fechas,datasets:[
{{label:'Agente',data:d.agente,borderColor:css.getPropertyValue('--a').trim(),borderWidth:2,pointRadius:0}},
{{label:'SPY (comprar y mantener)',data:d.spy,borderColor:css.getPropertyValue('--b').trim(),borderWidth:1.5,pointRadius:0}}]}},
options:{{interaction:{{mode:'index',intersect:false}},scales:{{x:{{ticks:{{maxTicksLimit:8}}}}}},
plugins:{{legend:{{position:'bottom'}}}}}}}});}}
</script></body></html>"""
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    print(f"Tablero generado: {DOCS / 'index.html'}")


if __name__ == "__main__":
    main()
