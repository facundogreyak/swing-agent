"""
paper.py - Etapa 4: paper trading diario (operaciones simuladas con datos reales).

Cada corrida procesa las velas nuevas desde la última vez, con las MISMAS reglas del backtest:
  1. Salidas de las posiciones abiertas (stop, objetivo, tiempo) con la vela del día.
  2. Ejecuta en la APERTURA las órdenes generadas por señales del cierre anterior.
  3. Registra el valor de la cartera al cierre.
  4. Evalúa cada ticker al cierre y anota una DECISIÓN con su motivo:
       COMPRAR (queda una orden para la apertura siguiente), MANTENER, VENDER o NO_OPERAR.

Todo queda en data/diario.db, asociado a la versión de parámetros vigente.
Ejecutar:  python paper.py
"""
from datetime import datetime, time
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yaml

import db
import data
from backtest import preparar_panel
from estrategia import evaluar, motivo, tamano_posicion


def _fechas_a_procesar(fechas, ultima):
    """Velas nuevas. Excluye la de hoy si el mercado de EE.UU. todavía no cerró."""
    ny = datetime.now(ZoneInfo("America/New_York"))
    if len(fechas) and fechas[-1].date() == ny.date() and ny.time() < time(16, 30):
        fechas = fechas[:-1]
    if ultima is None:
        return fechas[-1:]                      # primera corrida: solo generar señales de hoy
    return fechas[fechas > pd.Timestamp(ultima)]


def main():
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    r, e = cfg["riesgo"], cfg["estrategia"]
    com = r["comision_pct"]
    entrada_tipo = e.get("entrada", "retroceso")
    con = db.conectar(cfg["datos"]["base_precios"])
    dia = db.conectar(cfg["datos"]["base_diario"])
    version = db.registrar_version(dia, cfg)

    panel, sectores = preparar_panel(con, cfg)
    fechas = panel["close"].index
    cedears = {p["subyacente"]: p["cedear"] for p in cfg["universo"]}
    evs = {t: evaluar(data.cargar_precios(con, t), cfg).reindex(fechas) for t in sectores}
    fr_n = e.get("fuerza_relativa_dias")

    cuenta = dia.execute("SELECT efectivo, ultima_fecha FROM cuenta WHERE id=1").fetchone()
    if cuenta is None:
        dia.execute("INSERT INTO cuenta VALUES (1, ?, ?, ?, NULL)",
                    (r["capital_inicial_usd"], r["capital_inicial_usd"], datetime.now().date().isoformat()))
        dia.commit()
        cuenta = (r["capital_inicial_usd"], None)
    efectivo, ultima = cuenta

    en_spy = bool(r.get("efectivo_en_spy", False))
    cs = com if en_spy else 0.0        # comisión de mover el efectivo desde/hacia SPY
    bench_c = panel["bench"]
    a_procesar = _fechas_a_procesar(fechas, ultima)
    if len(a_procesar) == 0:
        print("Paper trading: no hay velas nuevas para procesar.")
        return

    def precio(tipo, t, f):
        v = panel[tipo].at[f, t]
        return None if pd.isna(v) else float(v)

    def precio_cedear(f, t):
        fila = con.execute("SELECT open FROM precios WHERE ticker=? AND fecha=?",
                           (cedears.get(t), f.strftime("%Y-%m-%d"))).fetchone()
        return fila[0] if fila else None

    for f in a_procesar:
        fs = f.strftime("%Y-%m-%d")
        vendidas_hoy = {}

        # 1) Salidas
        abiertas = dia.execute("SELECT id, ticker, stop, stop_inicial, objetivo, cantidad, costo_total, "
                               "riesgo_usd, dias, maximo FROM operaciones WHERE estado='ABIERTA'").fetchall()
        for (oid, t, stop, stop0, obj, cant, costo, riesgo, dias, maximo) in abiertas:
            o, h, l, c = (precio(k, t, f) for k in ("open", "high", "low", "close"))
            if c is None:
                continue
            dias += 1
            salida = None
            if o <= stop:
                salida = (o, "STOP (gap)")
            elif l <= stop:
                salida = (stop, "STOP" if stop <= stop0 + 1e-9 else "TRAILING")
            elif o >= obj:
                salida = (o, "OBJETIVO (gap)")
            elif h >= obj:
                salida = (obj, "OBJETIVO")
            elif dias >= r["max_dias_en_posicion"]:
                salida = (c, "TIEMPO")
            if salida:
                px, mot = salida
                bruto = cant * px
                pnl = bruto * (1 - com) - costo
                efectivo += bruto * (1 - com) * (1 - cs)
                dia.execute("UPDATE operaciones SET estado='CERRADA', fecha_salida=?, precio_salida=?, "
                            "motivo_salida=?, pnl_usd=?, r_multiple=?, dias=? WHERE id=?",
                            (fs, round(px, 4), mot, round(pnl, 2), round(pnl / riesgo, 2) if riesgo else 0, dias, oid))
                vendidas_hoy[t] = f"{mot} a {px:.2f} ({pnl / riesgo:+.2f}R)" if riesgo else mot
            else:
                maximo = max(maximo or h, h)
                if r.get("trailing_atr") and not np.isnan(evs[t].at[f, "atr"]):
                    stop = max(stop, maximo - r["trailing_atr"] * evs[t].at[f, "atr"])
                dia.execute("UPDATE operaciones SET dias=?, maximo=?, stop=? WHERE id=?", (dias, maximo, stop, oid))

        # 2) Ejecutar órdenes pendientes en la apertura
        abiertas = {row[0]: row[1] for row in dia.execute(
            "SELECT ticker, cantidad FROM operaciones WHERE estado='ABIERTA'")}
        valor = sum(q * (precio("close_ffill", t, f) or 0) for t, q in abiertas.items())
        capital = efectivo + valor
        pendientes = dia.execute("SELECT id, ticker, atr FROM ordenes WHERE estado='PENDIENTE' AND fecha_senal < ? "
                                 "ORDER BY prioridad", (fs,)).fetchall()
        for (oid, t, atr) in pendientes:
            motivo_desc = None
            entrada = precio("open", t, f)
            if len(abiertas) >= r["max_posiciones"]:
                motivo_desc = f"cartera llena ({r['max_posiciones']} posiciones)"
            elif t in abiertas:
                motivo_desc = "ya hay una posición abierta"
            elif sum(1 for x in abiertas if sectores[x] == sectores[t]) >= r["max_por_sector"]:
                motivo_desc = f"máximo por sector ({sectores[t]})"
            elif entrada is None:
                motivo_desc = "sin precio de apertura"
            if motivo_desc is None:
                stop = entrada - r["stop_atr"] * atr
                cant = tamano_posicion(capital, entrada, stop, r["riesgo_por_operacion"],
                                       efectivo / (1 + com) / (1 + cs), r.get("max_pct_posicion", 1.0))
                if cant <= 0:
                    motivo_desc = "sin efectivo suficiente"
            if motivo_desc:
                dia.execute("UPDATE ordenes SET estado='DESCARTADA', detalle=? WHERE id=?", (motivo_desc, oid))
                continue
            costo = cant * entrada * (1 + com)
            efectivo -= costo * (1 + cs)
            dia.execute(
                "INSERT INTO operaciones (ticker, cedear, sector, version_id, fecha_entrada, precio_entrada, "
                "precio_entrada_cedear_ars, cantidad, stop, stop_inicial, objetivo, riesgo_usd, costo_total, "
                "dias, maximo, estado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0,?,'ABIERTA')",
                (t, cedears.get(t), sectores[t], version, fs, round(entrada, 4), precio_cedear(f, t), cant,
                 stop, stop, entrada + r["objetivo_r"] * (entrada - stop), cant * (entrada - stop), costo, entrada))
            dia.execute("UPDATE ordenes SET estado='EJECUTADA', detalle=? WHERE id=?",
                        (f"compra {cant} a {entrada:.2f}", oid))
            abiertas[t] = cant

        # 3) Valor de la cartera al cierre (el efectivo en SPY acompaña la variación del día)
        k = fechas.get_loc(f)
        if en_spy and k > 0 and not pd.isna(bench_c.iloc[k]) and not pd.isna(bench_c.iloc[k - 1]):
            efectivo *= float(bench_c.iloc[k] / bench_c.iloc[k - 1])
        abiertas_q = dict(dia.execute("SELECT ticker, cantidad FROM operaciones WHERE estado='ABIERTA'").fetchall())
        invertido = sum(q * (precio("close_ffill", t, f) or 0) for t, q in abiertas_q.items())
        dia.execute("INSERT OR REPLACE INTO equity VALUES (?,?,?,?,?)",
                    (fs, "paper", round(efectivo, 2), round(invertido, 2), round(efectivo + invertido, 2)))

        # 4) Decisiones al cierre (una por ticker)
        mercado_ok = bool(panel["mercado_ok"].at[f]) if e.get("filtro_mercado") else True
        abiertas_info = {row[0]: row[1:] for row in dia.execute(
            "SELECT ticker, stop, objetivo, dias FROM operaciones WHERE estado='ABIERTA'")}
        for t in sectores:
            fila = evs[t].loc[f]
            if pd.isna(fila.close):
                continue
            datos = {k: (None if pd.isna(fila[k]) else round(float(fila[k]), 4))
                     for k in ("close", "sma_rapida", "sma_lenta", "rsi", "atr", "vol_rel")}
            if t in abiertas_info:
                stop, obj, dias = abiertas_info[t]
                accion, texto = "MANTENER", f"día {dias}/{r['max_dias_en_posicion']}; stop {stop:.2f}; objetivo {obj:.2f}"
            else:
                senal = bool(fila[f"senal_{entrada_tipo}"])
                fr_ok = True
                if fr_n:
                    v = panel[f"fr_{fr_n}"].at[f, t]
                    fr_ok = bool(v > 0) if not pd.isna(v) else False
                texto = motivo(fila, entrada_tipo)
                if senal and mercado_ok and fr_ok:
                    accion = "COMPRAR"
                    texto += " -> orden para la próxima apertura"
                    dia.execute("INSERT INTO ordenes (fecha_senal, ticker, atr, prioridad, version_id) VALUES (?,?,?,?,?)",
                                (fs, t, float(fila.atr), float(fila[f"prio_{entrada_tipo}"]), version))
                else:
                    accion = "NO_OPERAR"
                    if senal and not mercado_ok:
                        texto += "; señal anulada: SPY debajo de su media"
                    if senal and not fr_ok:
                        texto += "; señal anulada: más débil que SPY"
                if t in vendidas_hoy:                 # se cerró hoy: la decisión principal es la venta
                    texto = f"{vendidas_hoy[t]}" + (" · nueva señal de compra -> orden para la próxima apertura"
                                                    if accion == "COMPRAR" else "")
                    accion = "VENDER"
            dia.execute("INSERT INTO decisiones (fecha, ticker, accion, motivo, datos_json, version_id) "
                        "VALUES (?,?,?,?,?,?)", (fs, t, accion, texto, pd.Series(datos).to_json(), version))

        dia.execute("UPDATE cuenta SET efectivo=?, ultima_fecha=? WHERE id=1", (efectivo, fs))
        dia.commit()
        resumen = dict(dia.execute("SELECT accion, COUNT(*) FROM decisiones WHERE fecha=? GROUP BY accion", (fs,)).fetchall())
        print(f"  {fs}: {resumen} · cartera USD {efectivo + invertido:,.2f}")

    print("Paper trading actualizado.")


if __name__ == "__main__":
    main()
