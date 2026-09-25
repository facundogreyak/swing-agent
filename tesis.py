"""
tesis.py - Cada movimiento de las carteras documentado por escrito como una tesis de inversión,
y una revisión semanal de la cartera.

Tesis (reportes/tesis/<cartera>/<fecha>_<TICKER>.md), una por cada decisión de compra:
  1-5. La idea, por qué ahora, el plan, qué la confirmaría o invalidaría y qué se puede esperar
       según el backtest. Se escribe el día de la decisión y queda CONGELADA (se guarda en la
       tabla `tesis` de data/diario.db): no se reescribe con lo que pasó después.
  6. Ejecución: a cuánto se compró en la apertura siguiente (o por qué no se compró).
  7. Seguimiento: se actualiza en cada corrida mientras la posición está abierta.
  8. Cierre: resultado, comparación con SPY y si la tesis se cumplió o no.

Revisión semanal (reportes/revision_semanal/AAAA-Sxx.md): se escribe una vez por semana, con la
última rueda de la semana (normalmente el viernes). Resume resultados, movimientos, el estado de
cada tesis abierta y qué mirar la semana siguiente.

Todo sale de los datos del agente (precios, reglas y backtest): no usa noticias ni balances.
Ejecutar:  python tesis.py
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

import data
import db
import momentum as M
from estrategia import evaluar

REP = Path("reportes")
DIR_TESIS = REP / "tesis"
DIR_SEMANAL = REP / "revision_semanal"
REPO = os.environ.get("GITHUB_REPOSITORY", "facundogreyak/swing-agent")
URL_REPO = f"https://github.com/{REPO}/blob/main/"

PLAZOS = (("1 mes", 21, 0), ("3 meses", 63, 0), ("6 meses", 126, 0), ("12 meses", 252, 0))


# ---------------------------------------------------------------------------
# Formato (argentino: coma decimal, punto de miles)
# ---------------------------------------------------------------------------
def _n(v, dec=2):
    if v is None or pd.isna(v):
        return "—"
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(v, dec=1, signo=True):
    if v is None or pd.isna(v):
        return "—"
    if abs(v) < 0.5 * 10 ** -(dec + 2):
        v = 0.0
    return (f"{v:+.{dec}%}" if signo else f"{v:.{dec}%}").replace(".", ",")


def _usd(v, dec=0):
    return "—" if v is None or pd.isna(v) else f"USD {_n(v, dec)}"


def _fecha(s):
    try:
        return pd.Timestamp(s).strftime("%d/%m/%Y")
    except Exception:
        return s or "—"


def _habiles(fecha, n):
    """Fecha aproximada n ruedas después (días hábiles, sin feriados)."""
    return str(np.busday_offset(pd.Timestamp(fecha).date(), n, roll="forward"))


def _tabla(filas, encabezado):
    L = ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(encabezado)]
    L += ["| " + " | ".join(str(x) for x in f) + " |" for f in filas]
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Datos con caché (todo "al cierre de" una fecha: nunca mira el futuro)
# ---------------------------------------------------------------------------
class Datos:
    def __init__(self, con, cfg):
        self.con, self.cfg = con, cfg
        self._px, self._ev, self._rk = {}, {}, None
        self.bench = cfg["benchmark"]

    def px(self, t):
        if t not in self._px:
            self._px[t] = data.cargar_precios(self.con, t)
        return self._px[t]

    def ev(self, t):
        if t not in self._ev:
            self._ev[t] = evaluar(self.px(t), self.cfg)
        return self._ev[t]

    def cierres(self, t, fecha):
        return self.px(t)["close"].loc[:pd.Timestamp(fecha)].dropna()

    def cierre(self, t, fecha):
        c = self.cierres(t, fecha)
        return float(c.iloc[-1]) if len(c) else None

    def apertura(self, t, fecha):
        df = self.px(t)
        f = pd.Timestamp(fecha)
        return float(df.at[f, "open"]) if f in df.index and not pd.isna(df.at[f, "open"]) else self.cierre(t, fecha)

    def retorno(self, t, fecha, n, saltar=0):
        c = self.cierres(t, fecha)
        if len(c) <= n:
            return None
        return float(c.iloc[-1 - saltar] / c.iloc[-1 - n] - 1)

    def entre(self, t, desde, hasta, apertura=True):
        """Variación de t entre dos fechas (por defecto de apertura a apertura, como se opera)."""
        a = self.apertura(t, desde) if apertura else self.cierre(t, desde)
        b = self.apertura(t, hasta) if apertura else self.cierre(t, hasta)
        return b / a - 1 if a and b else None

    def perfil(self, t, fecha):
        c = self.cierres(t, fecha)
        u = c.iloc[-252:]
        return {"max52": float(u.max()) if len(u) else None,
                "dist_max52": float(c.iloc[-1] / u.max() - 1) if len(u) else None,
                "vol_anual": float(c.pct_change().iloc[-63:].std() * np.sqrt(252)) if len(c) > 63 else None,
                "peor_caida_12m": float((u / u.cummax() - 1).min()) if len(u) else None}

    def ranking(self):
        """Ranking de momentum tal como lo arma el motor (con el filtro de liquidez)."""
        if self._rk is None:
            m = self.cfg["momentum"]
            P = M.cargar(self.con, self.cfg)
            pun = M.calcular_puntajes(P["close"])
            liq = m.get("liquidez_min_usd")
            self._rk = {"P": P, "score": pun[m["puntaje"]][0], "abs": pun[m["puntaje"]][1],
                        "liq": (P["dolar_vol"] >= liq) if liq else None}
        return self._rk

    def puestos(self, fecha):
        rk = self.ranking()
        sc = rk["score"].loc[:pd.Timestamp(fecha)]
        if not len(sc):
            return {}, {}
        f = sc.index[-1]
        fila = sc.loc[f].values                     # mismo orden que Motor._decidir (incluso en empates)
        liq = rk["liq"].loc[f].values if rk["liq"] is not None else None
        orden = [j for j in np.argsort(-np.nan_to_num(fila, nan=-np.inf)) if not np.isnan(fila[j])
                 and (liq is None or bool(liq[j]))]
        tickers = sc.columns
        positivo = rk["abs"].loc[f].fillna(False).astype(bool).to_dict()
        return {tickers[j]: k + 1 for k, j in enumerate(orden)}, positivo


def _leer_csv(nombre):
    f = REP / nombre
    return pd.read_csv(f) if f.exists() and f.stat().st_size > 5 else pd.DataFrame()


def _cedear_hoy(t, fecha):
    """Precio del CEDEAR en pesos, si el dato de cedears.csv es del mismo momento que la decisión."""
    c = _leer_csv("cedears.csv")
    if not len(c) or t not in set(c.ticker):
        return None
    r = c[c.ticker == t].iloc[0]
    if pd.isna(r.get("fecha_ars")) or abs((pd.Timestamp(r.fecha_ars) - pd.Timestamp(fecha)).days) > 5:
        return None
    return r


def _mercado(D, fecha):
    c = D.cierres(D.bench, fecha)
    sma = c.rolling(200).mean().iloc[-1] if len(c) >= 200 else None
    if sma is None or pd.isna(sma):
        return "sin datos suficientes de SPY"
    d = c.iloc[-1] / sma - 1
    return (f"SPY está {_pct(abs(d), signo=False)} {'por encima' if d >= 0 else 'por debajo'} de su media de "
            f"200 ruedas ({'mercado alcista' if d >= 0 else 'mercado bajista: más riesgo de que las subas no sigan'}).")


def _tabla_retornos(D, t, fecha):
    filas = []
    for nombre, n, saltar in PLAZOS:
        a, b = D.retorno(t, fecha, n, saltar), D.retorno(D.bench, fecha, n, saltar)
        filas.append((nombre, _pct(a), _pct(b), _pct(a - b) if a is not None and b is not None else "—"))
    return _tabla(filas, ["Plazo", t, "SPY", "Diferencia"])


# ---------------------------------------------------------------------------
# Secciones 1-5 (se congelan el día de la decisión)
# ---------------------------------------------------------------------------
def idea_swing(D, dia, cfg, t, fecha, sector, cedear, ratio):
    e, r = cfg["estrategia"], cfg["riesgo"]
    ev = D.ev(t).loc[:pd.Timestamp(fecha)]
    f, ayer = ev.iloc[-1], ev.iloc[-2]
    rsi_min = float(ev["rsi"].iloc[-3:].min())
    close, atr = float(f.close), float(f.atr)
    stop = close - r["stop_atr"] * atr
    obj = close + r["objetivo_r"] * (close - stop)
    limite = _habiles(fecha, r["max_dias_en_posicion"] + 1)
    eq = dia.execute("SELECT efectivo, total FROM equity WHERE version_id='paper' AND fecha<=? "
                     "ORDER BY fecha DESC LIMIT 1", (fecha,)).fetchone()
    efectivo, capital = eq if eq else (r["capital_inicial_usd"], r["capital_inicial_usd"])
    riesgo_usd = capital * r["riesgo_por_operacion"]
    cant = max(min(riesgo_usd / (close - stop), capital * r["max_pct_posicion"] / close, efectivo / close), 0)
    mismo_sector = [x for (x,) in dia.execute(
        "SELECT ticker FROM operaciones WHERE sector=? AND fecha_entrada<=? AND (fecha_salida IS NULL OR "
        "fecha_salida>?)", (sector, fecha, fecha))]
    pf = D.perfil(t, fecha)

    L = ["## 1. La idea", "",
         f"Comprar un **retroceso dentro de una tendencia alcista**. {t} viene en tendencia de suba "
         f"(precio arriba de sus medias de {e['sma_rapida']} y {e['sma_lenta']} ruedas), en los últimos días "
         f"corrigió (el RSI bajó a {rsi_min:.0f}) y hoy rebotó con volumen. La apuesta es que la corrección "
         f"fue una pausa y que la tendencia de fondo retoma en las próximas semanas.", "",
         f"## 2. Por qué ahora (datos al cierre del {_fecha(fecha)})", "",
         _tabla([
             ("Precio", f"USD {_n(close)}", ""),
             ("Tendencia", f"precio {_pct(close / f.sma_lenta - 1)} vs. media de {e['sma_lenta']}; media de "
                           f"{e['sma_rapida']} {_pct(f.sma_rapida / f.sma_lenta - 1)} vs. la de {e['sma_lenta']}",
              "✔" if f.c_tendencia else "✘"),
             ("Retroceso", f"RSI mínimo de las últimas 3 ruedas: {rsi_min:.0f} (tiene que ser < {e['rsi_entrada_max']})",
              "✔" if f.c_retroceso else "✘"),
             ("Rebote", f"RSI {ayer.rsi:.0f} → {f.rsi:.0f}; cierre {_pct(close / ayer.close - 1)} vs. ayer",
              "✔" if f.c_rebote else "✘"),
             ("Volumen", f"{_n(f.vol_rel, 1)}x su promedio de 20 ruedas (mínimo {_n(e['volumen_min_rel'], 1)}x)",
              "✔" if f.c_volumen else "✘"),
             ("Volatilidad", f"se mueve ~USD {_n(atr)} por día (ATR {r['atr_periodo']}) = {_pct(atr / close, signo=False)} "
                             f"del precio", ""),
             ("Máximo de 52 semanas", f"USD {_n(pf['max52'])} ({_pct(pf['dist_max52'])} desde ahí)", ""),
         ], ["", "Dato", "Regla"]), "",
         "**Contexto: cuánto subió contra el mercado**", "", _tabla_retornos(D, t, fecha), "",
         f"- Mercado: {_mercado(D, fecha)}" + (" El filtro de mercado está apagado." if not e.get("filtro_mercado") else ""),
         f"- Sector: {sector}." + (f" Ya hay posiciones abiertas del mismo sector: {', '.join(mismo_sector)} "
                                   f"(máximo {r['max_por_sector']})." if mismo_sector else ""), "",
         "## 3. El plan", "",
         f"- **Entrada:** en la apertura de la rueda siguiente (referencia: cierre de USD {_n(close)}).",
         f"- **Stop (si sale mal):** entrada − {_n(r['stop_atr'], 1)} × ATR ≈ **USD {_n(stop)}** ({_pct(stop / close - 1)}).",
         f"- **Objetivo (si sale bien):** {_n(r['objetivo_r'], 1)} veces lo arriesgado ({_n(r['objetivo_r'], 0)}R) ≈ "
         f"**USD {_n(obj)}** ({_pct(obj / close - 1)}).",
         f"- **Salida por tiempo:** si en {r['max_dias_en_posicion']} ruedas no tocó ni el stop ni el objetivo, se vende "
         f"(≈ {_fecha(limite)}).",
         f"- **Tamaño:** se arriesga {_pct(r['riesgo_por_operacion'], 0, False)} del capital (≈ {_usd(riesgo_usd)}) → "
         f"≈ {_n(cant, 2)} acciones ≈ {_usd(cant * close)} ({_pct(cant * close / capital, 0, False)} de la cartera, "
         f"tope {_pct(r['max_pct_posicion'], 0, False)}).",
         ]
    ced = _cedear_hoy(t, fecha)
    linea = f"- **En BYMA:** CEDEAR {cedear or '—'} (ratio {ratio or '—'}:1)"
    if ratio:
        linea += f" ≈ {int(cant * ratio)} CEDEARs"
    if ced is not None and not pd.isna(ced.precio_ars):
        linea += (f"; hoy a ARS {_n(ced.precio_ars, 0)} (CCL implícito {_n(ced.ccl_implicito, 0)}, "
                  f"{ced.estado})")
    L += [linea + ".", "",
          "## 4. Qué confirmaría o invalidaría la tesis", "",
          f"- ✔ **Se confirma** si toca el objetivo (USD {_n(obj)}) antes de ≈ {_fecha(limite)}.",
          f"- ✘ **Se invalida** si toca el stop (USD {_n(stop)}): el retroceso no era una pausa sino el "
          f"comienzo de una baja. La pérdida queda acotada a ~1R ({_usd(riesgo_usd)}), salvo que abra con un salto.",
          f"- ⚠ **Señales de alerta** en el seguimiento: cierre debajo de la media de {e['sma_rapida']} "
          f"(hoy USD {_n(f.sma_rapida)}) o de la de {e['sma_lenta']} (USD {_n(f.sma_lenta)}). El agente no vende por "
          f"eso (solo por stop, objetivo o tiempo), pero la tesis pierde fuerza.", ""]

    L += ["## 5. Qué se puede esperar (backtest de esta configuración)", ""]
    bt = _leer_csv("backtest_operaciones.csv")
    if len(bt):
        mot = bt.motivo_salida.str.split(" ").str[0].value_counts(normalize=True)
        gan, per = bt[bt.r_multiple > 0], bt[bt.r_multiple <= 0]
        L += [f"- {len(bt)} operaciones con esta misma regla desde {_fecha(bt.fecha_entrada.min())}: "
              f"gana el **{_pct(len(gan) / len(bt), 0, False)}**, resultado promedio **{_n(bt.r_multiple.mean())}R** "
              f"por operación, {_n(bt.dias.mean(), 0)} ruedas en promedio.",
              f"- Cómo terminaron: objetivo {_pct(mot.get('OBJETIVO', 0), 0, False)}, stop "
              f"{_pct(mot.get('STOP', 0), 0, False)}, tiempo {_pct(mot.get('TIEMPO', 0), 0, False)}.",
              f"- Las ganadoras dejan en promedio {_n(gan.r_multiple.mean())}R y las perdedoras "
              f"{_n(per.r_multiple.mean())}R: se pierde más seguido de lo que se gana, la ventaja está en que "
              f"las ganadoras son más grandes."]
        propias = bt[bt.ticker == t]
        if len(propias) >= 3:
            L.append(f"- En {t}: {len(propias)} operaciones, ganó el {_pct((propias.r_multiple > 0).mean(), 0, False)}, "
                     f"promedio {_n(propias.r_multiple.mean())}R.")
        else:
            L.append(f"- En {t} hubo {len(propias)} operaciones en el backtest: muy pocas para sacar conclusiones.")
    else:
        L.append("- Todavía no hay backtest para comparar.")
    L += ["", "**Riesgos a tener en cuenta:** un salto en la apertura (resultados, noticias) puede saltar el stop; "
              "la tesis se basa solo en precio y volumen, no mira balances ni noticias.", ""]
    return "\n".join(L)


def idea_momentum(D, dia, cfg, t, fecha, sector, cedear, ratio, motivo_txt):
    m = cfg["momentum"]
    rk = D.ranking()
    puestos, _ = D.puestos(fecha)
    puesto, total_rk = puestos.get(t), len(puestos)
    pf = D.perfil(t, fecha)
    P = rk["P"]
    liq = P["dolar_vol"][t].loc[:pd.Timestamp(fecha)].iloc[-1] if t in P["dolar_vol"] else None
    eq = dia.execute("SELECT total FROM equity WHERE version_id='momentum' AND fecha<=? ORDER BY fecha DESC LIMIT 1",
                     (fecha,)).fetchone()
    capital = eq[0] if eq else cfg["riesgo"]["capital_inicial_usd"]
    cupo = capital / m["top_n"]
    lim = m["top_n"] + m.get("buffer", 0)
    prox = _habiles(fecha, m["rebalanceo_dias"])
    otros = [x for (x,) in dia.execute(
        "SELECT ticker FROM decisiones WHERE fecha=? AND accion IN ('ENTRA','SE_QUEDA') AND ticker!=?",
        (fecha, t))]
    mismo_sector = [x for x in otros if P["sectores"].get(x) == sector]
    nombres_puntaje = {"mix": "combina las subas de 3, 6 y 12 meses", "r21": "suba del último mes",
                       "r63": "suba de 3 meses", "r126": "suba de 6 meses sin el último mes",
                       "r252": "suba de 12 meses sin el último mes"}

    L = ["## 1. La idea", "",
         f"Seguir a las que más suben (**momentum**). {t} quedó en el **puesto #{puesto or '—'}** del ranking de "
         f"{total_rk} acciones líquidas (puntaje `{m['puntaje']}`: {nombres_puntaje.get(m['puntaje'], m['puntaje'])}). "
         f"La estrategia tiene siempre las {m['top_n']} más fuertes y las mantiene mientras sigan arriba: las acciones "
         f"que vienen subiendo con fuerza tienden a seguir haciéndolo durante algunos meses.", "",
         f"## 2. Por qué ahora (datos al cierre del {_fecha(fecha)})", "",
         f"Motivo del agente: _{motivo_txt}_", "",
         _tabla_retornos(D, t, fecha), "",
         f"- Precio: USD {_n(D.cierre(t, fecha))} · máximo de 52 semanas USD {_n(pf['max52'])} "
         f"({_pct(pf['dist_max52'])} desde ahí).",
         f"- Volatilidad: {_pct(pf['vol_anual'], 0, False)} anual (últimos 3 meses) · peor caída de los últimos 12 "
         f"meses: {_pct(pf['peor_caida_12m'], 0)}.",
         f"- Liquidez: ~USD {_n(liq / 1e6, 0)} M operados por día (mínimo exigido USD "
         f"{_n((m.get('liquidez_min_usd') or 0) / 1e6, 0)} M)." if liq and not pd.isna(liq) else "- Liquidez: —",
         f"- Mercado: {_mercado(D, fecha)}",
         f"- Sector: {sector}." + (f" En la cartera objetivo también: {', '.join(mismo_sector)} (máximo "
                                   f"{m['max_por_sector']})." if mismo_sector else ""), "",
         "## 3. El plan", "",
         f"- **Entrada:** en la apertura de la rueda siguiente, con ~1/{m['top_n']} de la cartera (≈ {_usd(cupo)}).",
         f"- **Se mantiene** mientras en cada revisión (cada {m['rebalanceo_dias']} ruedas; la próxima ≈ "
         f"{_fecha(prox)}) siga dentro del puesto #{lim} ({m['top_n']} + margen de {m.get('buffer', 0)}) y con "
         f"suba positiva.",
         f"- **Tope de peso:** si sube tanto que pasa el {_pct(m.get('max_peso') or 1, 0, False)} de la cartera, se "
         f"vende el excedente." if m.get("max_peso") else "- Sin tope de peso por acción.",
         "- **Sin stop por precio:** la salida la decide el ranking, no una caída puntual."]
    oc = _leer_csv("ordenes_cedears.csv")
    o = oc[(oc.tipo == "COMPRAR") & (oc.ticker == t)] if len(oc) else oc
    if len(o) and not pd.isna(o.iloc[0].cantidad):
        o = o.iloc[0]
        L.append(f"- **En BYMA:** {int(o.cantidad)} CEDEARs {o.cedear} (ratio {ratio}:1) ≈ ARS {_n(o.monto_ars, 0)} "
                 f"(precio del CEDEAR: {o.estado_precio}).")
    elif cedear:
        L.append(f"- **En BYMA:** CEDEAR {cedear} (ratio {ratio}:1).")
    L += ["", "## 4. Qué confirmaría o invalidaría la tesis", "",
          "- ✔ **Se confirma** si en las próximas revisiones sigue entre las primeras y le gana a SPY.",
          f"- ✘ **Se invalida** si cae más abajo del puesto #{lim} o su suba se vuelve negativa: en ese caso "
          f"se vende en la revisión siguiente.",
          "- ⚠ **Riesgo propio de la estrategia:** cuando el mercado gira, las acciones que más subieron suelen "
          "ser las que más caen, y la estrategia recién reacciona en la revisión.", "",
          "## 5. Qué se puede esperar (backtest de esta configuración)", ""]
    ops, eqb = _leer_csv("momentum_operaciones.csv"), _leer_csv("momentum_equity.csv")
    if len(ops):
        cerr = ops[(ops.lado == "VENTA") & ops.dias.notna() & (ops.ticker != cfg["benchmark"])]
        if len(cerr):
            L.append(f"- {len(cerr)} posiciones cerradas en el backtest: ganaron el "
                     f"**{_pct((cerr.retorno > 0).mean(), 0, False)}**, resultado mediano **{_pct(cerr.retorno.median())}**, "
                     f"promedio {_pct(cerr.retorno.mean())}, ~{_n(cerr.dias.mean(), 0)} días hábiles de tenencia.")
            L.append(f"- Pocas ganadoras grandes explican la mayor parte: el 10% mejor dejó más de "
                     f"{_pct(cerr.retorno.quantile(0.9), 0)}, el 10% peor perdió más de {_pct(cerr.retorno.quantile(0.1), 0)}.")
    if len(eqb) > 250:
        eqb = eqb.set_index("fecha")
        anios = len(eqb) / 252
        cagr = (eqb.total.iloc[-1] / eqb.total.iloc[0]) ** (1 / anios) - 1
        cagr_spy = (eqb.spy.iloc[-1] / eqb.spy.iloc[0]) ** (1 / anios) - 1
        dd = (eqb.total / eqb.total.cummax() - 1).min()
        L.append(f"- La estrategia completa: {_pct(cagr)} anual vs. {_pct(cagr_spy)} de SPY, con una caída máxima "
                 f"de {_pct(dd, 0)}.")
    if not len(ops):
        L.append("- Todavía no hay backtest para comparar.")
    L += ["", "**Riesgos a tener en cuenta:** la tesis se basa solo en cómo se movió el precio; no mira balances, "
              "valuación ni noticias.", ""]
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Secciones 6-8 (se recalculan en cada corrida con lo que efectivamente pasó)
# ---------------------------------------------------------------------------
def seguimiento_swing(D, dia, cfg, t, fecha_dec, hasta):
    """Devuelve (estado, markdown, resumen) de las secciones 6-8."""
    r, e = cfg["riesgo"], cfg["estrategia"]
    orden = dia.execute("SELECT estado, detalle FROM ordenes WHERE ticker=? AND fecha_senal=? ORDER BY id DESC",
                        (t, fecha_dec)).fetchone()
    op = dia.execute("SELECT fecha_entrada, precio_entrada, precio_entrada_cedear_ars, cantidad, stop, stop_inicial, "
                     "objetivo, riesgo_usd, costo_total, fecha_salida, precio_salida, motivo_salida, pnl_usd, "
                     "r_multiple, dias, estado FROM operaciones WHERE ticker=? AND fecha_entrada>? AND fecha_entrada<=? "
                     "ORDER BY fecha_entrada LIMIT 1", (t, fecha_dec, hasta)).fetchone()
    L = ["## 6. Ejecución", ""]
    if orden is None or orden[0] == "PENDIENTE" or (orden[0] == "EJECUTADA" and op is None):
        L.append("Orden pendiente: se compra en la próxima apertura.")
        return "PENDIENTE", "\n".join(L), {}
    if orden[0] == "DESCARTADA":
        L.append(f"**No se ejecutó:** {orden[1]}. La tesis queda registrada pero no se operó.")
        return "NO EJECUTADA", "\n".join(L), {"motivo_no": orden[1]}
    (fe, pe, pars, cant, stop, stop0, obj, riesgo, costo, fs, ps, mot, pnl, rm, dias, estado) = op
    L.append(f"Se compró el {_fecha(fe)} en la apertura a **USD {_n(pe)}** ({_pct(pe / D.cierre(t, fecha_dec) - 1)} "
             f"vs. el cierre de la señal): {_n(cant, 4)} acciones = {_usd(costo)} con comisión. "
             f"Stop USD {_n(stop0)}, objetivo USD {_n(obj)}, riesgo {_usd(riesgo)} (1R)."
             + (f" CEDEAR en la apertura: ARS {_n(pars, 0)}." if pars else ""))
    L.append("")
    if estado == "ABIERTA":
        c = D.cierre(t, hasta)
        ev = D.ev(t).loc[:pd.Timestamp(hasta)].iloc[-1]
        r_act = (c - pe) / (pe - stop0) if pe > stop0 else None
        alertas = []
        if c < ev.sma_lenta:
            alertas.append(f"cerró debajo de la media de {e['sma_lenta']}")
        elif c < ev.sma_rapida:
            alertas.append(f"cerró debajo de la media de {e['sma_rapida']}")
        if r_act is not None and r_act < -0.66:
            alertas.append("está cerca del stop")
        L += [f"## 7. Seguimiento (al {_fecha(hasta)})", "",
              _tabla([("Precio", f"USD {_n(c)}"), ("Resultado", f"{_pct(c / pe - 1)} ({_n(r_act)}R)"),
                      ("Ruedas", f"{dias} de {r['max_dias_en_posicion']}"),
                      ("Hasta el stop", f"{_pct(stop / c - 1)} (USD {_n(stop)})"),
                      ("Hasta el objetivo", f"{_pct(obj / c - 1)} (USD {_n(obj)})"),
                      ("RSI", f"{ev.rsi:.0f}"),
                      ("Tendencia", "intacta" if ev.c_tendencia else "debilitada")], ["", ""]), "",
              "Estado de la tesis: " + ("⚠ " + "; ".join(alertas) + "." if alertas else
                                        ("✔ a favor." if (r_act or 0) >= 1 else "en curso, sin alertas.")), ""]
        return "ABIERTA", "\n".join(L), {"resultado": c / pe - 1, "r": r_act, "ruedas": dias, "stop": stop,
                                          "objetivo": obj, "precio": c, "alertas": alertas, "desde": fe}
    spy = D.entre(D.bench, fe, fs)
    ret = ps / pe - 1
    base = mot.split(" ")[0]
    veredicto = {"OBJETIVO": "✔ **Tesis confirmada:** llegó al objetivo.",
                 "STOP": "✘ **Tesis invalidada:** tocó el stop" + (" (abrió debajo, con un salto)." if "gap" in mot
                                                                    else "; la pérdida quedó en lo planeado."),
                 "TRAILING": f"{'✔' if rm > 0 else '✘'} Salió por el stop móvil con {_n(rm)}R.",
                 "TIEMPO": f"◐ **No se materializó a tiempo:** se vendió por plazo con {_n(rm)}R "
                           f"({'a favor' if rm > 0 else 'en contra'})."}.get(base, mot)
    L += ["## 8. Cierre", "",
          _tabla([("Salida", f"{_fecha(fs)} · {mot} a USD {_n(ps)}"),
                  ("Resultado", f"{_pct(ret)} · {_usd(pnl)} · **{_n(rm)}R** (con comisiones)"),
                  ("Duración", f"{dias} ruedas"),
                  ("SPY en el mismo período", _pct(spy)),
                  ("Contra SPY", _pct(ret - spy) if spy is not None else "—")], ["", ""]), "",
          veredicto, ""]
    return "CERRADA", "\n".join(L), {"resultado": ret, "r": rm, "motivo": mot, "veredicto": veredicto,
                                     "fecha_salida": fs, "desde": fe, "vs_spy": ret - spy if spy is not None else None}


def seguimiento_momentum(D, dia, cfg, t, fecha_dec, hasta):
    m = cfg["momentum"]
    lim = m["top_n"] + m.get("buffer", 0)
    sig = dia.execute("SELECT MIN(fecha) FROM equity WHERE version_id='momentum' AND fecha>? AND fecha<=?",
                      (fecha_dec, hasta)).fetchone()[0]
    L = ["## 6. Ejecución", ""]
    if sig is None:
        L.append("Orden pendiente: se compra en la próxima apertura.")
        return "PENDIENTE", "\n".join(L), {}
    compras = dia.execute("SELECT precio, monto_usd, cantidad FROM mom_operaciones WHERE ticker=? AND fecha=? "
                          "AND lado='COMPRA'", (t, sig)).fetchall()
    if not compras:
        L.append(f"**No se ejecutó** el {_fecha(sig)}: la orden se reemplazó antes de la apertura (por ejemplo, "
                 f"por un cambio de parámetros) o no alcanzó el efectivo.")
        return "NO EJECUTADA", "\n".join(L), {"motivo_no": "la orden se reemplazó antes de la apertura"}
    pe, monto, cant = compras[0]
    L += [f"Se compró el {_fecha(sig)} en la apertura a **USD {_n(pe)}**: {_n(cant, 4)} acciones = {_usd(monto)}.", ""]
    ventas = dia.execute("SELECT fecha, precio, monto_usd, motivo, retorno, cantidad FROM mom_operaciones WHERE "
                         "ticker=? AND lado='VENTA' AND fecha>? AND fecha<=? ORDER BY id", (t, sig, hasta)).fetchall()
    recortes = [v for v in ventas if v[3].startswith("recorte")]
    salida = next((v for v in ventas if not v[3].startswith("recorte")), None)
    recortes = [v for v in recortes if salida is None or v[0] <= salida[0]]
    txt_rec = "".join(f"- {_fecha(v[0])}: {v[3]} → se vendieron {_usd(v[2])} a USD {_n(v[1])} ({_pct(v[4])}).\n"
                      for v in recortes)
    if salida is None:
        c = D.cierre(t, hasta)
        puestos, positivo = D.puestos(hasta)
        p = puestos.get(t)
        q = cant - sum(v[5] for v in recortes)
        tot = dia.execute("SELECT total FROM equity WHERE version_id='momentum' AND fecha<=? ORDER BY fecha DESC "
                          "LIMIT 1", (hasta,)).fetchone()
        peso = q * c / tot[0] if tot else None
        a, b = D.apertura(D.bench, sig), D.cierre(D.bench, hasta)
        spy = b / a - 1 if a and b else None
        if p is None:
            estado_t = "⚠ sin datos en el ranking: se vende en la próxima revisión."
        elif not positivo.get(t, True):
            estado_t = "⚠ su suba se volvió negativa: si sigue así, sale en la próxima revisión."
        elif p <= m["top_n"]:
            estado_t = "✔ firme: sigue entre las primeras."
        elif p <= lim:
            estado_t = f"◐ en zona de margen (puesto #{p}): se queda, pero perdió fuerza."
        else:
            estado_t = f"⚠ cayó al puesto #{p}: si sigue así, sale en la próxima revisión."
        L += [f"## 7. Seguimiento (al {_fecha(hasta)})", "",
              _tabla([("Precio", f"USD {_n(c)}"), ("Resultado", _pct(c / pe - 1)),
                      ("SPY en el mismo período", _pct(spy)),
                      ("Puesto en el ranking hoy", f"#{p}" if p else "—"),
                      ("Peso en la cartera", _pct(peso, 1, False))], ["", ""]), "",
              ("Recortes por tope de peso:\n" + txt_rec if txt_rec else ""),
              f"Estado de la tesis: {estado_t}", ""]
        return "ABIERTA", "\n".join(L), {"resultado": c / pe - 1, "puesto": p, "estado_t": estado_t, "peso": peso,
                                          "precio": c, "desde": sig, "vs_spy": (c / pe - 1) - spy if spy is not None else None}
    fs, ps, _, mot, ret, _ = salida
    spy = D.entre(D.bench, sig, fs)
    if ret > 0 and spy is not None and ret > spy:
        veredicto = "✔ **Tesis cumplida:** ganó y le ganó a SPY."
    elif ret > 0:
        veredicto = "◐ **A medias:** ganó, pero menos que SPY en el mismo período."
    else:
        veredicto = "✘ **Tesis fallida:** perdió plata."
    dias = int(np.busday_count(pd.Timestamp(sig).date(), pd.Timestamp(fs).date()))
    L += [("Recortes por tope de peso:\n" + txt_rec if txt_rec else ""),
          "## 8. Cierre", "",
          _tabla([("Salida", f"{_fecha(fs)} a USD {_n(ps)} · {mot}"),
                  ("Resultado", f"**{_pct(ret)}** (con comisiones)"),
                  ("Duración", f"{dias} días hábiles"),
                  ("SPY en el mismo período", _pct(spy)),
                  ("Contra SPY", _pct(ret - spy) if spy is not None else "—")], ["", ""]), "",
          veredicto, ""]
    return "CERRADA", "\n".join(L), {"resultado": ret, "motivo": mot, "veredicto": veredicto, "fecha_salida": fs,
                                     "desde": sig, "vs_spy": ret - spy if spy is not None else None}


# ---------------------------------------------------------------------------
# Armado de las tesis
# ---------------------------------------------------------------------------
def _info_universo(cfg):
    return {p["subyacente"]: p for p in data.universo_ampliado(cfg)}


def _versiones(dia, cfg):
    sw = db.registrar_version(dia, cfg)
    m = cfg["momentum"]
    mo = db.registrar_version(dia, {"momentum": {k: v for k, v in m.items() if k != "grilla"}},
                              claves=("momentum",), nombre="momentum " + m.get("nombre", ""))
    return sw, mo


def crear_tesis_nuevas(D, dia, cfg):
    """Congela las secciones 1-5 de cada decisión de compra que todavía no tiene tesis."""
    sw, mo = _versiones(dia, cfg)
    info = _info_universo(cfg)
    pend = dia.execute(
        "SELECT d.fecha, d.ticker, d.accion, d.motivo, d.version_id FROM decisiones d "
        "WHERE ((d.accion='COMPRAR' AND d.version_id=?) OR (d.accion='ENTRA' AND d.version_id=?)) "
        "AND NOT EXISTS (SELECT 1 FROM tesis x WHERE x.ticker=d.ticker AND x.fecha_decision=d.fecha AND "
        "x.cartera = CASE d.accion WHEN 'COMPRAR' THEN 'swing' ELSE 'momentum' END) ORDER BY d.fecha, d.id",
        (sw, mo)).fetchall()
    nuevas = 0
    for fecha, t, accion, motivo_txt, version in pend:
        p = info.get(t, {})
        sector, cedear, ratio = p.get("sector", "Otros"), p.get("cedear", ""), p.get("ratio")
        cedear = str(cedear).replace(".BA", "")
        try:
            if accion == "COMPRAR":
                cartera, idea = "swing", idea_swing(D, dia, cfg, t, fecha, sector, cedear, ratio)
            else:
                cartera, idea = "momentum", idea_momentum(D, dia, cfg, t, fecha, sector, cedear, ratio, motivo_txt)
        except Exception as ex:                    # una tesis que no se puede armar no frena al resto
            print(f"  Tesis {t} {fecha}: no se pudo armar ({ex})")
            continue
        archivo = f"tesis/{cartera}/{fecha}_{t}.md"
        dia.execute("INSERT INTO tesis (cartera, ticker, fecha_decision, version_id, archivo, idea_md) "
                    "VALUES (?,?,?,?,?,?)", (cartera, t, fecha, version, archivo, idea))
        nuevas += 1
    dia.commit()
    return nuevas


def estado_tesis(D, dia, cfg, hasta):
    """Todas las tesis con su estado al cierre de `hasta` (sin mirar después)."""
    filas = []
    for (tid, cartera, t, fecha, archivo, idea) in dia.execute(
            "SELECT id, cartera, ticker, fecha_decision, archivo, idea_md FROM tesis WHERE fecha_decision<=? "
            "ORDER BY fecha_decision, id", (hasta,)).fetchall():
        fn = seguimiento_swing if cartera == "swing" else seguimiento_momentum
        try:
            estado, md, res = fn(D, dia, cfg, t, fecha, hasta)
        except Exception as ex:
            estado, md, res = "SIN DATOS", f"No se pudo calcular el seguimiento ({ex}).", {}
        filas.append({"id": tid, "cartera": cartera, "ticker": t, "fecha": fecha, "archivo": archivo,
                      "idea": idea, "estado": estado, "md": md, **res})
    return filas


def escribir_tesis(filas, cfg):
    info = _info_universo(cfg)
    for f in filas:
        ruta = REP / f["archivo"]
        if f["estado"] == "NO EJECUTADA":           # no fue un movimiento de la cartera: queda solo en el índice
            ruta.unlink(missing_ok=True)
            continue
        p = info.get(f["ticker"], {})
        titulo = {"swing": "Swing · retroceso", "momentum": "Momentum · booms del momento"}[f["cartera"]]
        doc = "\n".join([
            f"# Tesis de inversión · {f['ticker']} · {titulo}", "",
            f"Decisión: **compra** al cierre del {_fecha(f['fecha'])} · Sector: {p.get('sector', '—')} · "
            f"Estado: **{f['estado']}**", "",
            "> Escrita por el agente con sus propios datos (precio, volumen, ranking y backtest) el día de la "
            "decisión. Las secciones 1 a 5 no se modifican después; la 6 a 8 se actualizan con lo que pasó. "
            "Simulado, sin dinero real. No es asesoramiento financiero.", "",
            f["idea"], f["md"].replace("\n\n\n", "\n\n"), "", "[← Todas las tesis](../README.md)", ""])
        ruta.parent.mkdir(parents=True, exist_ok=True)
        if not ruta.exists() or ruta.read_text(encoding="utf-8") != doc:
            ruta.write_text(doc, encoding="utf-8")


def _nota(f):
    """Una línea con cómo está (o cómo terminó) la tesis."""
    if f.get("veredicto"):
        return f["veredicto"].replace("**", "")
    if f.get("estado_t"):
        return f["estado_t"]
    if f["estado"] == "ABIERTA" and f["cartera"] == "swing":
        return ("⚠ " + "; ".join(f["alertas"]) + ".") if f.get("alertas") else "en curso, sin alertas."
    return f.get("motivo_no") or ""


def escribir_indice(filas):
    L = ["# Tesis de inversión", "",
         "Cada compra del agente, documentada el día de la decisión y seguida hasta el cierre. "
         "Revisiones semanales: [revision_semanal/](../revision_semanal/).", ""]
    for cartera, nombre in (("momentum", "Momentum"), ("swing", "Swing")):
        fs = [f for f in filas if f["cartera"] == cartera and f["estado"] != "NO EJECUTADA"]
        no_ej = [f for f in filas if f["cartera"] == cartera and f["estado"] == "NO EJECUTADA"]
        L += [f"## {nombre}", ""]
        if not fs:
            L += ["Todavía no hay tesis.", ""]
            continue
        tab = []
        for f in sorted(fs, key=lambda x: x["fecha"], reverse=True):
            res = _pct(f.get("resultado")) if f.get("resultado") is not None else ""
            if cartera == "swing" and f.get("r") is not None:
                res += f" ({_n(f['r'])}R)"
            tab.append((_fecha(f["fecha"]), f"[{f['ticker']}]({f['archivo'].split('/', 1)[1]})", f["estado"], res,
                        _nota(f)))
        L += [_tabla(tab, ["Decisión", "Acción", "Estado", "Resultado", "Veredicto"]), ""]
        if no_ej:
            L += [f"<details><summary>Señales que no se operaron ({len(no_ej)})</summary>", "",
                  _tabla([(_fecha(f["fecha"]), f["ticker"], f.get("motivo_no", "")) for f in sorted(no_ej, key=lambda x: x["fecha"], reverse=True)],
                         ["Decisión", "Acción", "Motivo"]), "", "</details>", ""]
    (DIR_TESIS / "README.md").write_text("\n".join(L), encoding="utf-8")


# ---------------------------------------------------------------------------
# Revisión semanal
# ---------------------------------------------------------------------------
def _semanas_completas(dia):
    fechas = sorted({f for (f,) in dia.execute("SELECT DISTINCT fecha FROM equity")})
    if not fechas:
        return []
    s = pd.Series(pd.to_datetime(fechas))
    sem = s.dt.strftime("%G-S%V")
    out = []
    for clave, g in s.groupby(sem):
        fin = g.max()
        if fin.weekday() == 4 or fin < s.max():            # terminó el viernes o ya hay datos posteriores
            out.append((clave, g.min(), fin))
    return out


def _cartera_momentum_al(dia, hasta):
    """Tenencias de la cartera momentum reconstruidas con las operaciones hasta `hasta`."""
    pos, costo = {}, {}
    for t, lado, q, monto in dia.execute("SELECT ticker, lado, cantidad, monto_usd FROM mom_operaciones "
                                         "WHERE fecha<=? ORDER BY id", (hasta,)):
        if lado == "COMPRA":
            pos[t] = pos.get(t, 0) + q
            costo[t] = costo.get(t, 0) + monto
        else:
            tot = pos.get(t, 0)
            if tot > 0:
                costo[t] = costo.get(t, 0) * (1 - q / tot)
            pos[t] = tot - q
            if pos[t] <= 1e-9:
                pos.pop(t, None); costo.pop(t, None)
    return pos, costo


def revision_semanal(D, dia, cfg, clave, ini, fin):
    ini_s, fin_s = ini.strftime("%Y-%m-%d"), fin.strftime("%Y-%m-%d")
    cap0 = cfg["riesgo"]["capital_inicial_usd"]
    m = cfg["momentum"]
    filas = estado_tesis(D, dia, cfg, fin_s)
    link = lambda f: f["ticker"] if f["estado"] == "NO EJECUTADA" else f"[{f['ticker']}](../{f['archivo']})"

    # 1) Resumen de resultados
    res = []
    spy_ini = None
    for nombre, v in (("Momentum", "momentum"), ("Swing", "paper")):
        s = pd.read_sql("SELECT fecha, total FROM equity WHERE version_id=? AND fecha<=? ORDER BY fecha", dia,
                        params=(v, fin_s)).set_index("fecha")["total"]
        if not len(s):
            continue
        antes = s[s.index < ini_s]
        base_sem = antes.iloc[-1] if len(antes) else cap0
        res.append((f"**{nombre}**", _usd(s.iloc[-1]), _pct(s.iloc[-1] / base_sem - 1), _pct(s.iloc[-1] / cap0 - 1)))
        spy_ini = spy_ini or s.index[0]
    if spy_ini:
        b = D.cierres(D.bench, fin_s)
        antes = b[b.index < pd.Timestamp(ini_s)]
        desde = b[b.index >= pd.Timestamp(spy_ini)]
        if len(antes) and len(desde):
            res.append(("SPY (referencia)", _usd(cap0 * b.iloc[-1] / desde.iloc[0]), _pct(b.iloc[-1] / antes.iloc[-1] - 1),
                        _pct(b.iloc[-1] / desde.iloc[0] - 1)))

    L = [f"# Revisión semanal · {clave}", "",
         f"Semana del {_fecha(ini_s)} al {_fecha(fin_s)} · datos al cierre del {_fecha(fin_s)} · simulado, sin dinero real.",
         "", "## 1. Resultados", "",
         _tabla(res, ["Cartera", "Valor", "Semana", f"Desde el inicio ({_fecha(spy_ini)})"]) if res else "Sin datos.", ""]

    # 2) Movimientos de la semana
    mov = []
    for f in filas:
        if ini_s <= f["fecha"] <= fin_s:
            quien = "Momentum" if f["cartera"] == "momentum" else "Swing"
            mov.append((f["fecha"], f"{_fecha(f['fecha'])} · {quien}: decisión de compra de {link(f)} → {f['estado'].lower()}"))
        if f.get("fecha_salida") and ini_s <= f["fecha_salida"] <= fin_s:
            quien = "Momentum" if f["cartera"] == "momentum" else "Swing"
            extra = f" ({_n(f['r'])}R)" if f["cartera"] == "swing" else ""
            mov.append((f["fecha_salida"], f"{_fecha(f['fecha_salida'])} · {quien}: vendió {link(f)}: {f['motivo']} → "
                                           f"{_pct(f['resultado'])}{extra}. {f['veredicto'].replace('**', '')}"))
    for fe, t, lado, monto, mot in dia.execute(
            "SELECT fecha, ticker, lado, monto_usd, motivo FROM mom_operaciones WHERE fecha BETWEEN ? AND ? AND "
            "(ticker=? OR motivo LIKE 'recorte%')", (ini_s, fin_s, cfg["benchmark"])):
        mov.append((fe, f"{_fecha(fe)} · Momentum: {lado.lower()} {t} por {_usd(monto)} ({mot})"))
    L += ["## 2. Movimientos de la semana", ""]
    L += [f"- {x}" for _, x in sorted(mov)] if mov else ["Sin compras ni ventas esta semana."]
    L.append("")

    # 3) Cartera y estado de cada tesis
    L += ["## 3. Cartera y estado de cada tesis", "", "### Momentum", ""]
    abiertas_m = [f for f in filas if f["cartera"] == "momentum" and f["estado"] == "ABIERTA"]
    pos, _ = _cartera_momentum_al(dia, fin_s)
    tot = dia.execute("SELECT total FROM equity WHERE version_id='momentum' AND fecha<=? ORDER BY fecha DESC LIMIT 1",
                      (fin_s,)).fetchone()
    if abiertas_m:
        L.append(_tabla([(link(f), _fecha(f["desde"]), _pct(f["resultado"]), _pct(f.get("vs_spy")),
                          f"#{f['puesto']}" if f.get("puesto") else "—", _pct(f.get("peso"), 1, False),
                          f["estado_t"])
                         for f in abiertas_m],
                        ["Acción", "Desde", "Resultado", "vs. SPY", "Puesto", "Peso", "Tesis"]))
    else:
        L.append("Sin posiciones en acciones.")
    if cfg["benchmark"] in pos and tot:
        L.append(f"\nEn SPY (lo no asignado, para estar 100% invertido): "
                 f"{_pct(pos[cfg['benchmark']] * D.cierre(D.bench, fin_s) / tot[0], 0, False)} de la cartera.")
    L += ["", "### Swing", ""]
    abiertas_s = [f for f in filas if f["cartera"] == "swing" and f["estado"] == "ABIERTA"]
    if abiertas_s:
        L.append(_tabla([(link(f), _fecha(f["desde"]), _pct(f["resultado"]), f"{_n(f['r'])}R",
                          f"{f['ruedas']}/{cfg['riesgo']['max_dias_en_posicion']}", f"USD {_n(f['stop'])}",
                          f"USD {_n(f['objetivo'])}", "⚠ " + "; ".join(f["alertas"]) if f["alertas"] else "en curso")
                         for f in abiertas_s],
                        ["Acción", "Desde", "Resultado", "En R", "Ruedas", "Stop", "Objetivo", "Tesis"]))
    else:
        L.append("Sin posiciones abiertas.")
    L.append("")

    # 4) Tesis cerradas en la semana y acumulado
    cerradas = [f for f in filas if f["estado"] == "CERRADA"]
    sem = [f for f in cerradas if ini_s <= f["fecha_salida"] <= fin_s]
    L += ["## 4. Tesis cerradas", ""]
    if sem:
        L.append(_tabla([(f["cartera"].capitalize(), link(f), _pct(f["resultado"]), _pct(f.get("vs_spy")),
                          f["veredicto"].replace("**", "")) for f in sem],
                        ["Cartera", "Acción", "Resultado", "vs. SPY", "Veredicto"]))
    else:
        L.append("Ninguna esta semana.")
    L.append("")
    for cartera, nombre in (("swing", "Swing"), ("momentum", "Momentum")):
        c = [f for f in cerradas if f["cartera"] == cartera]
        if not c:
            continue
        gan = sum(1 for f in c if f["resultado"] > 0)
        linea = f"- {nombre}, acumulado: {len(c)} tesis cerradas, ganaron {gan} ({_pct(gan / len(c), 0, False)})"
        if cartera == "swing":
            bt = _leer_csv("backtest_operaciones.csv")
            prom = np.mean([f["r"] for f in c])
            linea += f", promedio {_n(prom)}R" + (f" (backtest: {_n(bt.r_multiple.mean())}R)" if len(bt) else "")
        else:
            linea += f", resultado mediano {_pct(float(np.median([f['resultado'] for f in c])))}"
        L.append(linea + ".")
    no_ej = [f for f in filas if f["estado"] == "NO EJECUTADA" and ini_s <= f["fecha"] <= fin_s]
    if no_ej:
        L.append("\nDecisiones que no se ejecutaron: " + ", ".join(link(f) for f in no_ej) + ".")
    L.append("")

    # 5) Qué mirar la semana que viene
    L += ["## 5. Qué mirar la semana que viene", ""]
    ult_reb = dia.execute("SELECT MAX(fecha) FROM decisiones WHERE fecha<=? AND accion IN "
                          "('ENTRA','SALE','SE_QUEDA','A_EFECTIVO')", (fin_s,)).fetchone()[0]
    if ult_reb:
        cal = D.cierres(D.bench, fin_s).index
        k = cal.get_indexer([pd.Timestamp(ult_reb)])[0]
        faltan = m["rebalanceo_dias"] - (len(cal) - 1 - k) if k >= 0 else None
        if faltan is not None:
            cuando = _fecha(_habiles(fin_s, max(faltan, 1)))
            L.append(f"- Momentum: próxima revisión del ranking ≈ {cuando} (en {max(faltan, 0)} ruedas). "
                     f"Última: {_fecha(ult_reb)}.")
    riesgo = [f for f in abiertas_m if "⚠" in f["estado_t"]]
    if riesgo:
        L.append("- Momentum: tesis debilitadas, candidatas a salir en la revisión: "
                 + ", ".join(link(f) for f in riesgo) + ".")
    pend = [f for f in filas if f["estado"] == "PENDIENTE"]
    if pend:
        L.append("- Órdenes pendientes para la próxima apertura: " + ", ".join(
            f"{link(f)} ({f['cartera']})" for f in pend) + ".")
    for f in abiertas_s:
        faltan = cfg["riesgo"]["max_dias_en_posicion"] - f["ruedas"]
        partes = ([f"vence por tiempo en {faltan} ruedas si no toca stop ni objetivo"] if faltan <= 5 else []) \
            + f["alertas"]
        if partes:
            L.append(f"- Swing: {link(f)} {'; '.join(partes)}.")
    puestos, _ = D.puestos(fin_s)
    tenidas = set(pos)
    top = [t for t, p in sorted(puestos.items(), key=lambda x: x[1]) if t not in tenidas][:5]
    if top:
        L.append("- Booms que no están en la cartera (top del ranking hoy): " + ", ".join(
            f"#{puestos[t]} {t}" for t in top) + ".")
    su = _leer_csv("setups_hoy.csv")
    if len(su) and fin_s == dia.execute("SELECT MAX(fecha) FROM equity").fetchone()[0]:
        nuevos = su[su.nuevos_hoy.notna()] if "nuevos_hoy" in su else su.iloc[0:0]
        if len(nuevos):
            L.append("- Screener de setups (no opera, solo para mirar): señales nuevas en "
                     + ", ".join(nuevos.ticker.head(8)) + ".")
    if L[-1] == "":
        L.append("Nada en particular.")
    L += ["", "---", "[Todas las tesis](../tesis/README.md) · Herramienta de análisis y simulación. "
                     "No es asesoramiento financiero.", ""]
    return "\n".join(L)


def main():
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    con = db.conectar(cfg["datos"]["base_precios"])
    dia = db.conectar(cfg["datos"]["base_diario"])
    hasta = dia.execute("SELECT MAX(fecha) FROM equity").fetchone()[0]
    if not hasta:
        print("Tesis: todavía no hay datos.")
        return
    D = Datos(con, cfg)
    nuevas = crear_tesis_nuevas(D, dia, cfg)
    filas = estado_tesis(D, dia, cfg, hasta)
    DIR_TESIS.mkdir(parents=True, exist_ok=True)
    escribir_tesis(filas, cfg)
    escribir_indice(filas)
    pd.DataFrame([{k: f.get(k) for k in ("cartera", "ticker", "fecha", "estado", "resultado", "r", "vs_spy",
                                         "fecha_salida", "archivo")} | {"nota": _nota(f)} for f in filas]
                 ).to_csv(DIR_TESIS / "estado.csv", index=False)
    print(f"Tesis: {nuevas} nuevas · {len(filas)} en total "
          f"({sum(f['estado'] == 'ABIERTA' for f in filas)} abiertas, {sum(f['estado'] == 'CERRADA' for f in filas)} cerradas)")

    DIR_SEMANAL.mkdir(parents=True, exist_ok=True)
    for clave, ini, fin in _semanas_completas(dia):
        ruta = DIR_SEMANAL / f"{clave}.md"
        if ruta.exists():                          # cada revisión es una foto de su semana: no se reescribe
            continue
        ruta.write_text(revision_semanal(D, dia, cfg, clave, ini, fin), encoding="utf-8")
        print(f"Revisión semanal escrita: {ruta}")


if __name__ == "__main__":
    main()
