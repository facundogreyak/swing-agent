"""
momentum.py - Estrategia "booms del momento": rotación por momentum, 100% invertida.

Idea: en vez de entrar y salir seguido, cada `rebalanceo_dias` ruedas se ordena el universo
por cuánto subió en el período elegido y se mantienen las `top_n` más fuertes.
  - Todo el dinero queda invertido: lo que no va a acciones (por falta de candidatos con
    momentum positivo o por redondeo) se compra en SPY.
  - `buffer`: una acción que ya tenemos se queda mientras siga dentro del puesto top_n + buffer
    (menos rotación = menos comisiones y menos ruido).
  - `max_por_sector`: evita tener todo en un mismo sector (null = sin límite).
  - `filtro_mercado`: si SPY está debajo de su media de 200 ruedas se pasa a efectivo
    (deja de estar 100% invertido en mercados bajistas; se prueba en la calibración).

Puntajes de momentum (`puntaje`):
  r21  -> suba del último mes          (boom de corto plazo)
  r63  -> suba de los últimos 3 meses
  r126 -> suba de 6 meses sin el último mes
  r252 -> suba de 12 meses sin el último mes (el clásico "12-1")
  mix  -> promedio de los rankings de r63, r126 y r252

El MISMO motor (clase Motor) se usa en el backtest y en el paper trading diario,
así los dos siguen exactamente las mismas reglas.

Ejecutar:  python momentum.py            -> backtest + calibración + reporte
Genera:    reportes/momentum.md, reportes/momentum_calibracion.csv, reportes/momentum_equity.csv
"""
import copy
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

import db
import data

REPORTES = Path("reportes")
PUNTAJES = ("r21", "r63", "r126", "r252", "mix")


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
def cargar(con, cfg):
    """Precios alineados al calendario del benchmark. Devuelve un dict con matrices."""
    bench_t = cfg["benchmark"]
    bench = data.cargar_precios(con, bench_t)
    fechas = bench.index
    close, opn, sectores = {}, {}, {}
    for par in cfg["universo"]:
        t = par["subyacente"]
        df = data.cargar_precios(con, t)
        if len(df) < 300:
            continue
        df = df.reindex(fechas)
        close[t], opn[t] = df["close"], df["open"]
        sectores[t] = par.get("sector", "Otros")
    close = pd.DataFrame(close)
    opn = pd.DataFrame(opn)
    return {
        "fechas": fechas,
        "tickers": list(close.columns),
        "sectores": sectores,
        "close": close.ffill(),
        "open": opn.fillna(close.ffill()),     # si falta la apertura se usa el último cierre
        "hay_vela": close.notna(),
        "bench": bench_t,
        "bench_close": bench["close"],
        "bench_open": bench["open"].fillna(bench["close"]),
        "mercado_ok": bench["close"] > bench["close"].rolling(200).mean(),
    }


def calcular_puntajes(close: pd.DataFrame) -> dict:
    """Devuelve {nombre: (puntaje, momentum_absoluto_positivo)} como DataFrames."""
    def ret(n, saltar=0):
        return close.shift(saltar) / close.shift(n) - 1

    r = {"r21": ret(21), "r63": ret(63), "r126": ret(126, 21), "r252": ret(252, 21)}
    salida = {k: (v, v > 0) for k, v in r.items()}
    rangos = [r[k].rank(axis=1, pct=True) for k in ("r63", "r126", "r252")]
    mix = sum(rangos) / 3
    mix[r["r252"].isna() | r["r126"].isna() | r["r63"].isna()] = np.nan
    salida["mix"] = (mix, r["r126"] > 0)
    salida["_crudos"] = r
    return salida


# ---------------------------------------------------------------------------
# Motor (un día por vez)
# ---------------------------------------------------------------------------
class Motor:
    def __init__(self, P, pun, m, comision, capital=10000.0, estado=None):
        self.P, self.m, self.com = P, m, comision
        self.score, self.absoluto = (x.values for x in pun[m["puntaje"]])
        self.tickers = P["tickers"]
        self.ti = {t: j for j, t in enumerate(self.tickers)}
        self.C, self.O = P["close"].values, P["open"].values
        self.BC, self.BO = P["bench_close"].values, P["bench_open"].values
        self.MOK = P["mercado_ok"].values
        e = estado or {}
        self.efectivo = e.get("efectivo", capital)
        self.pos = e.get("pos", {})              # ticker -> cantidad (incluye el benchmark)
        self.costo = e.get("costo", {})          # ticker -> costo total (para el retorno)
        self.entrada = e.get("entrada", {})      # ticker -> fecha de compra
        self.pendiente = e.get("pendiente")      # {"nombres": [...], "efectivo": bool, "motivos": {...}}
        self.ult_reb = e.get("ult_reb")          # fecha del último rebalanceo (str)
        self.log = []                            # operaciones del período
        self.curva = []

    def estado(self):
        return {"efectivo": self.efectivo, "pos": self.pos, "costo": self.costo, "entrada": self.entrada,
                "pendiente": self.pendiente, "ult_reb": self.ult_reb}

    # --- precios
    def _px(self, t, i, apertura):
        if t == self.P["bench"]:
            return float(self.BO[i] if apertura else self.BC[i])
        return float(self.O[i, self.ti[t]] if apertura else self.C[i, self.ti[t]])

    def valor(self, i, apertura=False):
        return self.efectivo + sum(q * self._px(t, i, apertura) for t, q in self.pos.items())

    # --- operaciones
    def _vender(self, t, q, i, fecha, motivo):
        px = self._px(t, i, True)
        neto = q * px * (1 - self.com)
        total_q = self.pos[t]
        costo_parte = self.costo.get(t, 0) * q / total_q
        ret = neto / costo_parte - 1 if costo_parte else 0.0
        self.efectivo += neto
        self.pos[t] = total_q - q
        self.costo[t] = self.costo.get(t, 0) - costo_parte
        if self.pos[t] <= 1e-9:
            self.pos.pop(t); self.costo.pop(t, None)
            dias = None
            if t in self.entrada:
                dias = int(np.busday_count(self.entrada.pop(t), fecha)) if t != self.P["bench"] else None
        else:
            dias = None
        self.log.append({"fecha": fecha, "ticker": t, "lado": "VENTA", "cantidad": round(q, 6),
                         "precio": round(px, 4), "monto_usd": round(neto, 2), "motivo": motivo,
                         "retorno": round(ret, 4), "dias": dias})

    def _comprar(self, t, monto, i, fecha, motivo):
        if monto <= 1:
            return
        px = self._px(t, i, True)
        q = monto / (1 + self.com) / px
        self.efectivo -= monto
        self.pos[t] = self.pos.get(t, 0) + q
        self.costo[t] = self.costo.get(t, 0) + monto
        self.entrada.setdefault(t, fecha)
        self.log.append({"fecha": fecha, "ticker": t, "lado": "COMPRA", "cantidad": round(q, 6),
                         "precio": round(px, 4), "monto_usd": round(monto, 2), "motivo": motivo,
                         "retorno": None, "dias": None})

    def _ejecutar(self, i, fecha):
        """Ejecuta en la apertura la cartera objetivo decidida al cierre anterior."""
        obj = self.pendiente
        self.pendiente = None
        bench = self.P["bench"]
        nombres = obj["nombres"]
        motivos = obj.get("motivos", {})
        # 1) vender lo que sale
        for t in [x for x in self.pos if x != bench and x not in nombres]:
            self._vender(t, self.pos[t], i, fecha, motivos.get(t, "sale del ranking"))
        if obj.get("efectivo"):
            if bench in self.pos:
                self._vender(bench, self.pos[bench], i, fecha, "filtro de mercado: SPY bajo su media")
            return
        # 2) comprar lo que entra (cada una con 1/top_n del capital)
        nuevos = [t for t in nombres if t not in self.pos]
        if nuevos:
            cupo = self.valor(i, apertura=True) / self.m["top_n"]
            falta = cupo * len(nuevos) - self.efectivo
            if falta > 0 and bench in self.pos:           # fondear vendiendo SPY
                q = min(self.pos[bench], falta / (self._px(bench, i, True) * (1 - self.com)))
                self._vender(bench, q, i, fecha, "fondea compras")
            for k, t in enumerate(nuevos):
                monto = min(cupo, self.efectivo / (len(nuevos) - k))
                self._comprar(t, monto, i, fecha, motivos.get(t, "entra al ranking"))
        # 3) el resto a SPY -> 100% invertido
        if self.efectivo > 0.005 * self.valor(i, apertura=True):
            self._comprar(bench, self.efectivo, i, fecha, "resto a SPY (100% invertido)")

    def _decidir(self, i, fecha):
        """Al cierre: arma el ranking y define la cartera objetivo para la próxima apertura."""
        m = self.m
        sc, ab = self.score[i], self.absoluto[i]
        validos = [j for j in np.argsort(-np.nan_to_num(sc, nan=-np.inf)) if not np.isnan(sc[j])]
        puesto = {self.tickers[j]: k + 1 for k, j in enumerate(validos)}
        if m.get("filtro_mercado") and not bool(self.MOK[i]):
            self.pendiente = {"nombres": [], "efectivo": True, "motivos": {
                t: "filtro de mercado: SPY bajo su media" for t in self.pos}}
            return puesto
        n, buf = m["top_n"], m.get("buffer", 0)
        cap = m.get("max_por_sector")
        sect = self.P["sectores"]
        elegidos, motivos, por_sector = [], {}, {}

        def cabe(t):
            return cap is None or por_sector.get(sect[t], 0) < cap

        # a) se quedan las que ya tenemos si siguen dentro de top_n + buffer y con momentum positivo
        actuales = sorted([t for t in self.pos if t in puesto], key=lambda t: puesto[t])
        for t in actuales:
            j = self.ti[t]
            if puesto[t] <= n + buf and bool(ab[j]) and len(elegidos) < n and cabe(t):
                elegidos.append(t); por_sector[sect[t]] = por_sector.get(sect[t], 0) + 1
        # b) se completan con las mejores del ranking
        for j in validos:
            t = self.tickers[j]
            if len(elegidos) >= n:
                break
            if t in elegidos or not bool(ab[j]) or not cabe(t):
                continue
            elegidos.append(t); por_sector[sect[t]] = por_sector.get(sect[t], 0) + 1
            motivos[t] = f"entra: puesto #{puesto[t]}"
        for t in self.pos:
            if t != self.P["bench"] and t not in elegidos:
                if t not in puesto:
                    motivos[t] = "sale: sin datos"
                elif not bool(ab[self.ti[t]]):
                    motivos[t] = f"sale: momentum negativo (puesto #{puesto[t]})"
                elif puesto[t] > n + buf:
                    motivos[t] = f"sale: cayó al puesto #{puesto[t]}"
                else:
                    motivos[t] = f"sale: límite por sector (puesto #{puesto[t]})"
        self.pendiente = {"nombres": elegidos, "efectivo": False, "motivos": motivos}
        return puesto

    def paso(self, i, fecha, es_rebalanceo):
        """Procesa la rueda i: ejecuta en la apertura, valúa al cierre y (si toca) decide."""
        if self.pendiente is not None:
            self._ejecutar(i, fecha)
        total = self.valor(i)
        en_spy = self.pos.get(self.P["bench"], 0) * self._px(self.P["bench"], i, False)
        self.curva.append((fecha, round(self.efectivo, 2), round(total - self.efectivo - en_spy, 2),
                           round(en_spy, 2), round(total, 2), sum(1 for t in self.pos if t != self.P["bench"])))
        puesto = None
        if es_rebalanceo:
            puesto = self._decidir(i, fecha)
            self.ult_reb = fecha
        return puesto


def es_dia_de_rebalanceo(fechas, i, ult_reb, cada):
    if ult_reb is None:
        return True
    k = fechas.get_indexer([pd.Timestamp(ult_reb)])[0]
    return k < 0 or (i - k) >= cada


# ---------------------------------------------------------------------------
# Backtest
# ---------------------------------------------------------------------------
def simular(P, pun, cfg, m=None, desde=None, hasta=None):
    m = m or cfg["momentum"]
    fechas = P["fechas"]
    primer = fechas[260]                         # hace falta ~1 año para el momentum de 12 meses
    mask = fechas >= max(pd.Timestamp(desde), primer) if desde else fechas >= primer
    if hasta:
        mask &= fechas < pd.Timestamp(hasta)
    idx = np.where(mask)[0]
    mot = Motor(P, pun, m, cfg["riesgo"]["comision_pct"], cfg["riesgo"]["capital_inicial_usd"])
    for i in idx:
        f = fechas[i].strftime("%Y-%m-%d")
        mot.paso(i, f, es_dia_de_rebalanceo(fechas, i, mot.ult_reb, m["rebalanceo_dias"]))
    eq = pd.DataFrame(mot.curva, columns=["fecha", "efectivo", "acciones", "spy_en_cartera", "total", "posiciones"])
    eq = eq.set_index("fecha")
    cap0 = cfg["riesgo"]["capital_inicial_usd"]
    b = P["bench_close"].iloc[idx]
    eq["spy"] = (b / b.iloc[0] * cap0).round(2).values
    eq["igual_peso"] = (igual_peso(P, idx) * cap0).round(2)
    return pd.DataFrame(mot.log), eq


def igual_peso(P, idx):
    """Referencia honesta: las mismas acciones del universo en partes iguales, rebalanceo mensual.
    Como el universo se eligió hoy (con ganadores conocidos), esta curva muestra cuánto del
    resultado viene de la lista de acciones y no de la estrategia."""
    c = P["close"].iloc[idx]
    r = c.pct_change().fillna(0.0).values
    meses = c.index.to_period("M")
    valor, pos, vals = 1.0, None, []
    for k in range(len(c)):
        if k == 0 or meses[k] != meses[k - 1]:
            validos = ~np.isnan(c.values[k])
            pos = np.where(validos, valor / validos.sum(), 0.0)
        pos = pos * (1 + r[k]) if k > 0 else pos
        valor = pos.sum()
        vals.append(valor)
    return np.array(vals)



def max_dd(s):
    return float((s / s.cummax() - 1).min())


def metricas(ops, eq, capital0, bench):
    anios = max((pd.Timestamp(eq.index[-1]) - pd.Timestamp(eq.index[0])).days / 365.25, 1e-9)
    cagr = (eq.total.iloc[-1] / capital0) ** (1 / anios) - 1
    mdd = max_dd(eq.total)
    ventas = ops[(ops.lado == "VENTA") & (ops.ticker != bench)] if len(ops) else ops
    compras = ops[(ops.lado == "COMPRA") & (ops.ticker != bench)] if len(ops) else ops
    rotacion = (ops.monto_usd.sum() / eq.total.mean() / anios) if len(ops) else 0.0
    return {
        "retorno_anual (CAGR)": cagr,
        "max_drawdown": mdd,
        "retorno/caida (MAR)": cagr / abs(mdd) if mdd < 0 else 0.0,
        "retorno_total": eq.total.iloc[-1] / capital0 - 1,
        "compras_por_anio": len(compras) / anios,
        "aciertos": float((ventas.retorno > 0).mean()) if len(ventas) else 0.0,
        "retorno_prom_por_posicion": float(ventas.retorno.mean()) if len(ventas) else 0.0,
        "dias_prom_en_posicion": float(ventas.dias.dropna().mean()) if len(ventas) else 0.0,
        "rotacion_anual": rotacion,
        "pct_en_acciones": float((eq.acciones / eq.total).mean()),
        "pct_en_spy": float((eq.spy_en_cartera / eq.total).mean()),
        "spy_retorno_anual": (eq.spy.iloc[-1] / capital0) ** (1 / anios) - 1,
        "spy_max_drawdown": max_dd(eq.spy),
    }


def fmt(k, v):
    if isinstance(v, float) and any(x in k for x in ("retorno", "drawdown", "aciertos", "pct_", "caida")) \
            and "MAR" not in k:
        return f"{v:.1%}"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def por_anio(eq):
    e = eq.copy()
    e.index = pd.to_datetime(e.index)
    a = e[["total", "spy"]].resample("YE").last()
    return pd.concat([e[["total", "spy"]].iloc[[0]], a]).pct_change().dropna()


# ---------------------------------------------------------------------------
# Calibración + "qué pesa más"
# ---------------------------------------------------------------------------
def _etiqueta(v):
    """Texto legible para los valores de la grilla (None/True/False -> no/sí)."""
    if v is None or v is False:
        return "no"
    if v is True:
        return "sí"
    return str(v)


def calibrar(P, pun, cfg):
    g = cfg["momentum"]["grilla"]
    corte = cfg["backtest"]["inicio_fuera_de_muestra"]
    claves = list(g)
    cap0, bench = cfg["riesgo"]["capital_inicial_usd"], cfg["benchmark"]
    filas = []
    for combo in itertools.product(*g.values()):
        m = copy.deepcopy(cfg["momentum"])
        m.update(dict(zip(claves, combo)))
        o1, e1 = simular(P, pun, cfg, m, hasta=corte)
        o2, e2 = simular(P, pun, cfg, m, desde=corte)
        a, b = metricas(o1, e1, cap0, bench), metricas(o2, e2, cap0, bench)
        fila = {k: _etiqueta(v) for k, v in zip(claves, combo)}
        for pref, mm in (("in", a), ("out", b)):
            for k in ("retorno_anual (CAGR)", "max_drawdown", "retorno/caida (MAR)", "compras_por_anio",
                      "spy_retorno_anual"):
                fila[f"{pref}_{k}"] = mm[k]
        filas.append(fila)
    df = pd.DataFrame(filas)
    df = df.sort_values("in_retorno/caida (MAR)", ascending=False)
    df.to_csv(REPORTES / "momentum_calibracion.csv", index=False)

    # Importancia: cuánto cambia el retorno fuera de muestra según cada parámetro
    imp = []
    for k in claves:
        gi = df.groupby(k)["in_retorno_anual (CAGR)"].mean()
        go = df.groupby(k)["out_retorno_anual (CAGR)"].mean()
        gd = df.groupby(k)["out_max_drawdown"].mean()
        imp.append({"parametro": k, "impacto_fuera": go.max() - go.min(), "mejor_fuera": go.idxmax(),
                    "mejor_dentro": gi.idxmax(), "detalle": go, "detalle_in": gi, "dd": gd})
    imp.sort(key=lambda x: -x["impacto_fuera"])
    return df, imp, claves


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------
def main():
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    con = db.conectar(cfg["datos"]["base_precios"])
    P = cargar(con, cfg)
    if len(P["fechas"]) < 400 or not P["tickers"]:
        print("Momentum: no hay historia suficiente.")
        return
    REPORTES.mkdir(exist_ok=True)
    pun = calcular_puntajes(P["close"])
    cap0, bench = cfg["riesgo"]["capital_inicial_usd"], cfg["benchmark"]
    m = cfg["momentum"]

    # Copia de los cierres históricos para poder analizarlos fuera de GitHub (se escribe una sola vez)
    hist = REPORTES / "historico_cierres.csv.gz"
    if not hist.exists():
        h = P["close"].copy()
        h[bench] = P["bench_close"]
        h.round(4).to_csv(hist, compression="gzip")

    ops, eq = simular(P, pun, cfg)
    base = metricas(ops, eq, cap0, bench)
    eq.to_csv(REPORTES / "momentum_equity.csv")
    ops.to_csv(REPORTES / "momentum_operaciones.csv", index=False)

    params = ", ".join(f"{k}={m[k]}" for k in ("puntaje", "top_n", "rebalanceo_dias", "buffer",
                                                 "max_por_sector", "filtro_mercado"))
    L = [f"# Momentum ({m.get('nombre', '')}) – booms del momento", "",
         f"Período: {eq.index[0]} → {eq.index[-1]} · {len(P['tickers'])} acciones · Parámetros: {params}", "",
         "## Resultado", "", "| Métrica | Valor |", "|---|---|"]
    L += [f"| {k} | {fmt(k, v)} |" for k, v in base.items()]
    ew = eq["igual_peso"]
    anios = (pd.Timestamp(eq.index[-1]) - pd.Timestamp(eq.index[0])).days / 365.25
    L += ["", f"**Referencia:** las mismas {len(P['tickers'])} acciones en partes iguales rindieron "
              f"{(ew.iloc[-1] / ew.iloc[0]) ** (1 / anios) - 1:.1%} anual (caída máx. {max_dd(ew):.1%}). "
              "La diferencia contra SPY es en gran parte por haber elegido la lista hoy; "
              "la ventaja real de la estrategia se mide contra esta referencia."]
    e2 = eq.copy()
    e2.index = pd.to_datetime(e2.index)
    an = e2[["total", "igual_peso", "spy"]].resample("YE").last()
    an = pd.concat([e2[["total", "igual_peso", "spy"]].iloc[[0]], an]).pct_change().dropna()
    L += ["", "## Retorno por año", "", "| Año | Momentum | 50 en partes iguales | SPY |", "|---|---|---|---|"]
    L += [f"| {f.year} | {r.total:.1%} | {r.igual_peso:.1%} | {r.spy:.1%} |" for f, r in an.iterrows()]

    ventas = ops[(ops.lado == "VENTA") & (ops.ticker != bench)] if len(ops) else ops
    if len(ventas):
        top = ventas.groupby("ticker").agg(veces=("retorno", "size"), retorno_prom=("retorno", "mean")) \
            .sort_values("retorno_prom", ascending=False)
        L += ["", "## Qué acciones aportaron (posiciones cerradas)", "",
              "| Ticker | Veces | Retorno promedio |", "|---|---|---|"]
        L += [f"| {t} | {r.veces} | {r.retorno_prom:.1%} |" for t, r in top.head(10).iterrows()]

    corte = pd.Timestamp(cfg["backtest"]["inicio_fuera_de_muestra"])
    if m.get("grilla") and P["fechas"][260] + pd.Timedelta(days=365) > corte:
        L += ["", f"_Calibración omitida: hace falta al menos 1 año de datos antes de {corte.date()}._"]
    elif m.get("grilla"):
        df, imp, claves = calibrar(P, pun, cfg)
        corte = cfg["backtest"]["inicio_fuera_de_muestra"]
        L += ["", "## Qué pesa más en el resultado", "",
              f"Retorno anual promedio de todas las combinaciones que usan cada valor. "
              f"'Dentro' = hasta {corte} · 'Fuera' = desde {corte}. "
              "Un parámetro es confiable si el mejor valor coincide dentro y fuera.", ""]
        for x in imp:
            L.append(f"**{x['parametro']}** — impacto fuera de muestra: {x['impacto_fuera']:.1%} "
                     f"(mejor dentro: {x['mejor_dentro']}, mejor fuera: {x['mejor_fuera']})")
            L.append("")
            L.append("| Valor | CAGR dentro | CAGR fuera | Caída fuera |")
            L.append("|---|---|---|---|")
            for v in x["detalle"].index:
                L.append(f"| {v} | {x['detalle_in'][v]:.1%} | {x['detalle'][v]:.1%} | {x['dd'][v]:.1%} |")
            L.append("")
        cols = claves + ["in_retorno_anual (CAGR)", "in_max_drawdown", "out_retorno_anual (CAGR)",
                         "out_max_drawdown", "out_spy_retorno_anual", "out_compras_por_anio"]
        top = df.head(10)[cols].copy()
        for c in cols[len(claves):]:
            top[c] = [fmt(c, v) for v in top[c]]
        L += ["## Top 10 combinaciones (elegidas con datos dentro de muestra)", "", top.to_markdown(index=False)]
        corr = df["in_retorno/caida (MAR)"].rank().corr(df["out_retorno/caida (MAR)"].rank())
        L += ["", f"Correlación de ranking dentro vs fuera: **{corr:.2f}**"]

    (REPORTES / "momentum.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:60]))


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Paper trading diario (usa el mismo Motor que el backtest)
# ---------------------------------------------------------------------------
def paper():
    from paper import _fechas_a_procesar          # misma regla: no procesar velas sin cerrar
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    m = cfg["momentum"]
    con = db.conectar(cfg["datos"]["base_precios"])
    dia = db.conectar(cfg["datos"]["base_diario"])
    version = db.registrar_version(dia, {"momentum": {k: v for k, v in m.items() if k != "grilla"}},
                                   claves=("momentum",), nombre="momentum " + m.get("nombre", ""))
    P = cargar(con, cfg)
    pun = calcular_puntajes(P["close"])
    crudos = pun["_crudos"]
    score = pun[m["puntaje"]][0]
    fechas = P["fechas"]

    fila = dia.execute("SELECT ultima_fecha, estado_json FROM estado_motor WHERE nombre='momentum'").fetchone()
    ultima, estado = (fila[0], json.loads(fila[1])) if fila else (None, None)
    a_procesar = _fechas_a_procesar(fechas, ultima)
    if len(a_procesar) == 0:
        print("Momentum: no hay velas nuevas para procesar.")
        return

    if estado and estado.get("version") != version:
        # Cambiaron los parámetros: se descarta la orden pendiente (armada con los viejos)
        # y se vuelve a armar el ranking con los nuevos en la próxima vela.
        print(f"Momentum: nueva versión de parámetros ({version}); se rearma la cartera objetivo.")
        estado["pendiente"], estado["ult_reb"] = None, None
    mot = Motor(P, pun, m, cfg["riesgo"]["comision_pct"], cfg["riesgo"]["capital_inicial_usd"], estado)
    for f in a_procesar:
        i = fechas.get_loc(f)
        fs = f.strftime("%Y-%m-%d")
        n_log = len(mot.log)
        rebalanceo = es_dia_de_rebalanceo(fechas, i, mot.ult_reb, m["rebalanceo_dias"])
        tenencias_antes = set(mot.pos)
        puesto = mot.paso(i, fs, rebalanceo)

        for op in mot.log[n_log:]:
            dia.execute("INSERT INTO mom_operaciones (fecha, ticker, lado, cantidad, precio, monto_usd, motivo, "
                        "retorno, version_id) VALUES (?,?,?,?,?,?,?,?,?)",
                        (op["fecha"], op["ticker"], op["lado"], op["cantidad"], op["precio"], op["monto_usd"],
                         op["motivo"], op["retorno"], version))
        _, efectivo, acciones, en_spy, total, _ = mot.curva[-1]
        dia.execute("INSERT OR REPLACE INTO equity VALUES (?,?,?,?,?)",
                    (fs, "momentum", efectivo, round(acciones + en_spy, 2), total))

        # Ranking del día (para ver los "booms", se rebalancee o no)
        fila_sc = score.iloc[i].dropna().sort_values(ascending=False)
        for k, (t, v) in enumerate(fila_sc.items(), start=1):
            dia.execute("INSERT OR REPLACE INTO ranking VALUES (?,?,?,?,?,?,?,?,?)",
                        (fs, t, P["sectores"][t], k, float(v),
                         *[None if pd.isna(crudos[c].iat[i, P["tickers"].index(t)])
                           else float(crudos[c].iat[i, P["tickers"].index(t)]) for c in ("r21", "r63", "r126", "r252")]))

        # Decisiones (solo los días de rebalanceo)
        if rebalanceo and mot.pendiente is not None:
            obj = mot.pendiente
            if obj.get("efectivo"):
                dia.execute("INSERT INTO decisiones (fecha, ticker, accion, motivo, datos_json, version_id) "
                            "VALUES (?,?,?,?,?,?)", (fs, "CARTERA", "A_EFECTIVO",
                                                     "filtro de mercado: SPY debajo de su media de 200", "{}", version))
            for t in sorted(set(obj["nombres"]) | (tenencias_antes - {P["bench"]}), key=lambda x: puesto.get(x, 999)):
                if t in obj["nombres"] and t in tenencias_antes:
                    accion, texto = "SE_QUEDA", f"sigue fuerte: puesto #{puesto.get(t)}"
                elif t in obj["nombres"]:
                    accion, texto = "ENTRA", obj["motivos"].get(t, f"puesto #{puesto.get(t)}") + \
                        " -> se compra en la próxima apertura"
                else:
                    accion, texto = "SALE", obj["motivos"].get(t, "sale") + " -> se vende en la próxima apertura"
                j = P["tickers"].index(t)
                datos = {c: (None if pd.isna(crudos[c].iat[i, j]) else round(float(crudos[c].iat[i, j]), 4))
                         for c in ("r21", "r63", "r126", "r252")}
                dia.execute("INSERT INTO decisiones (fecha, ticker, accion, motivo, datos_json, version_id) "
                            "VALUES (?,?,?,?,?,?)", (fs, t, accion, texto, json.dumps(datos), version))
        print(f"  {fs}: {'REBALANCEO' if rebalanceo else 'seguimiento'} · cartera USD {total:,.2f} "
              f"· posiciones {sum(1 for t in mot.pos if t != P['bench'])}")

    est = mot.estado()
    est["version"] = version
    dia.execute("INSERT OR REPLACE INTO estado_motor VALUES ('momentum', ?, ?)",
                (a_procesar[-1].strftime("%Y-%m-%d"), json.dumps(est)))
    dia.commit()
    print("Momentum: paper trading actualizado.")
