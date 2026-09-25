"""
alertas.py - Manda un mail cuando el agente compra o vende, y un resumen todos los viernes.

Usa Gmail con una "contraseña de aplicación" guardada como secrets de GitHub:
  GMAIL_USUARIO  -> tu dirección de Gmail (también es el destinatario)
  GMAIL_CLAVE    -> la contraseña de aplicación de 16 letras
  MAIL_DESTINO   -> (opcional) otra dirección a la que mandar los avisos
Si no están configurados, no hace nada (el agente sigue funcionando igual).

Cada fecha se avisa una sola vez aunque el agente corra varias veces en el día.
Ejecutar:  python alertas.py            (manda si corresponde)
           python alertas.py --prueba   (arma el mail y lo guarda en reportes/mail_prueba.html sin enviarlo)
"""
import json
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import pandas as pd
import yaml

import db

REP = Path("reportes")
WEB = "https://facundogreyak.github.io/swing-agent/"
URL_REPO = f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'facundogreyak/swing-agent')}/blob/main/"
C = {"tx": "#111827", "mu": "#6b7280", "bd": "#e5e7eb", "bg": "#f5f6fa", "ac": "#4f46e5",
     "pos": "#16a34a", "neg": "#dc2626"}


def _pct(v):
    if v is None or pd.isna(v):
        return "—"
    return f"{v:+.2%}".replace(".", ",")


def _pct0(v):
    return "—" if v is None or pd.isna(v) else f"{v:+.0%}"


def _color(v):
    return C["pos"] if (v or 0) > 0 else (C["neg"] if (v or 0) < 0 else C["mu"])


def _usd(v):
    return "USD " + f"{v:,.0f}".replace(",", ".")


def _ars(v):
    return "—" if v is None or pd.isna(v) else "$ " + f"{v:,.0f}".replace(",", ".")


def _fecha(s):
    return pd.Timestamp(s).strftime("%d/%m/%Y")


def _serie(dia, clave):
    return pd.read_sql("SELECT fecha, total FROM equity WHERE version_id=? ORDER BY fecha", dia,
                       params=(clave,)).set_index("fecha")["total"]


def armar(cfg, dia, con, fecha, semanal):
    """Devuelve (asunto, html) o (None, None) si no hay nada para avisar."""
    cap0 = cfg["riesgo"]["capital_inicial_usd"]
    novedades = pd.read_sql(
        "SELECT ticker, accion, motivo FROM decisiones WHERE fecha=? AND accion IN "
        "('ENTRA','SALE','COMPRAR','VENDER','A_EFECTIVO') ORDER BY accion", dia, params=(fecha,))
    ejecutadas = pd.read_sql("SELECT ticker, lado, monto_usd, motivo, retorno FROM mom_operaciones "
                             "WHERE fecha=? AND ticker != ?", dia, params=(fecha, cfg["benchmark"]))
    sw_abiertas = pd.read_sql("SELECT ticker, precio_entrada FROM operaciones WHERE fecha_entrada=?", dia,
                              params=(fecha,))
    sw_cerradas = pd.read_sql("SELECT ticker, motivo_salida, r_multiple FROM operaciones WHERE fecha_salida=?",
                              dia, params=(fecha,))
    hay_algo = len(novedades) or len(ejecutadas) or len(sw_abiertas) or len(sw_cerradas)
    if not hay_algo and not semanal:
        return None, None

    # --- tarjetas de resumen
    filas = ""
    spy = pd.read_sql("SELECT fecha, close FROM precios WHERE ticker=? ORDER BY fecha", con,
                      params=(cfg["benchmark"],)).set_index("fecha")["close"]
    for nombre, clave in (("Momentum", "momentum"), ("Swing", "paper")):
        s = _serie(dia, clave)
        if not len(s):
            continue
        v = s.iloc[-1]
        hoy = v / s.iloc[-2] - 1 if len(s) > 1 else None
        sem = v / s.iloc[-6] - 1 if len(s) > 5 else v / cap0 - 1
        filas += (f"<tr><td style='padding:8px 0'><b>{nombre}</b></td><td align='right'>{_usd(v)}</td>"
                  f"<td align='right' style='color:{_color(hoy)}'>{_pct(hoy)}</td>"
                  f"<td align='right' style='color:{_color(sem)}'>{_pct(sem)}</td>"
                  f"<td align='right' style='color:{_color(v / cap0 - 1)}'>{_pct(v / cap0 - 1)}</td></tr>")
    s0 = _serie(dia, "momentum")
    if len(s0) and len(spy):
        base = spy[spy.index >= s0.index[0]]
        if len(base) > 1:
            v = base.iloc[-1] / base.iloc[0] * cap0
            hoy = base.iloc[-1] / base.iloc[-2] - 1
            sem = base.iloc[-1] / base.iloc[-6] - 1 if len(base) > 5 else v / cap0 - 1
            filas += (f"<tr><td style='padding:8px 0;color:{C['mu']}'>SPY (referencia)</td>"
                      f"<td align='right' style='color:{C['mu']}'>{_usd(v)}</td>"
                      f"<td align='right' style='color:{_color(hoy)}'>{_pct(hoy)}</td>"
                      f"<td align='right' style='color:{_color(sem)}'>{_pct(sem)}</td>"
                      f"<td align='right' style='color:{_color(v / cap0 - 1)}'>{_pct(v / cap0 - 1)}</td></tr>")
    tabla = (f"<table width='100%' style='border-collapse:collapse;font-size:14px'>"
             f"<tr style='color:{C['mu']};font-size:12px'><td></td><td align='right'>Valor</td>"
             f"<td align='right'>Hoy</td><td align='right'>Semana</td><td align='right'>Desde inicio</td></tr>"
             f"{filas}</table>")

    # --- novedades en lenguaje simple, con la orden en CEDEARs cuando la hay
    ordenes = pd.read_csv(REP / "ordenes_cedears.csv") if (REP / "ordenes_cedears.csv").exists() \
        and (REP / "ordenes_cedears.csv").stat().st_size > 1 else pd.DataFrame()
    ord_por = {(r.tipo, r.ticker): r for r in ordenes.itertuples()} if len(ordenes) else {}
    items = []
    for r in novedades.itertuples():
        extra = ""
        o = ord_por.get(({"ENTRA": "COMPRAR", "SALE": "VENDER"}.get(r.accion, ""), r.ticker))
        if o is not None and not pd.isna(o.cantidad):
            extra = f" · <b>{int(o.cantidad)} CEDEARs {o.cedear}</b> (≈ {_ars(o.monto_ars)}, precio hoy: {o.estado_precio})"
        quien = "Momentum" if r.accion in ("ENTRA", "SALE", "A_EFECTIVO") else "Swing"
        verbo = {"ENTRA": "compra mañana", "SALE": "vende mañana", "COMPRAR": "compra mañana",
                 "VENDER": "vendió", "A_EFECTIVO": "pasa a efectivo"}[r.accion]
        cartera = "momentum" if quien == "Momentum" else "swing"
        tesis_md = REP / "tesis" / cartera / f"{fecha}_{r.ticker}.md"
        if r.accion in ("ENTRA", "COMPRAR") and tesis_md.exists():
            extra += (f" · <a href='{URL_REPO}{tesis_md.as_posix()}' style='color:{C['ac']}'>leer la tesis</a>")
        items.append(f"<li style='margin-bottom:8px'><b>{quien} {verbo} {r.ticker}</b>{extra}<br>"
                     f"<span style='color:{C['mu']};font-size:12px'>{r.motivo}</span></li>")
    for r in ejecutadas.itertuples():
        res = f" ({_pct(r.retorno)})" if not pd.isna(r.retorno) else ""
        items.append(f"<li>Momentum ejecutó: {r.lado.lower()} {r.ticker} por {_usd(r.monto_usd)}{res}</li>")
    for r in sw_abiertas.itertuples():
        items.append(f"<li>Swing compró {r.ticker} a USD {r.precio_entrada:.2f}</li>")
    ya = set(novedades.ticker)
    for r in sw_cerradas.itertuples():
        if r.ticker in ya:
            continue
        items.append(f"<li>Swing cerró {r.ticker}: {r.motivo_salida} ({r.r_multiple:+.2f}R)</li>")
    nov_html = (f"<ul style='padding-left:18px;margin:8px 0;font-size:14px'>{''.join(items)}</ul>" if items
                else f"<p style='color:{C['mu']}'>Sin compras ni ventas esta vez.</p>")

    # --- booms (top 5 del ranking)
    rk = pd.read_sql("SELECT ticker, puesto, r21, r63 FROM ranking WHERE fecha=(SELECT MAX(fecha) FROM ranking) "
                     "ORDER BY puesto LIMIT 5", dia)
    booms = "".join(f"<tr><td style='padding:4px 0'>#{r.puesto} <b>{r.ticker}</b></td>"
                    f"<td align='right' style='color:{_color(r.r21)}'>{_pct0(r.r21)} en 1 mes</td>"
                    f"<td align='right' style='color:{_color(r.r63)}'>{_pct0(r.r63)} en 3 meses</td></tr>"
                    for r in rk.itertuples())

    titulo = "Resumen semanal" if semanal and not hay_algo else ("Novedades y resumen semanal" if semanal
                                                                  else "Novedades del agente")
    if len(novedades):
        partes = []
        for cartera, acc_c, acc_v in (("Momentum", "ENTRA", "SALE"), ("Swing", "COMPRAR", "VENDER")):
            c = [r.ticker for r in novedades.itertuples() if r.accion == acc_c]
            v = [r.ticker for r in novedades.itertuples() if r.accion == acc_v]
            detalle = ([f"compra {', '.join(c)}"] if c else []) + ([f"vende {', '.join(v)}"] if v else [])
            if detalle:
                partes.append(f"{cartera} {' y '.join(detalle)}")
        asunto = f"Agente Inversor · {_fecha(fecha)}: {' · '.join(partes)}"
    else:
        asunto = f"Agente Inversor · {titulo} {_fecha(fecha)}"

    revision = ""
    semana = REP / "revision_semanal" / f"{pd.Timestamp(fecha).strftime('%G-S%V')}.md"
    if semanal and semana.exists():
        revision = (f"<h3 style='font-size:13px;color:{C['mu']};text-transform:uppercase;margin:20px 0 4px'>"
                    f"Revisión semanal</h3><p style='font-size:14px;margin:4px 0'>Resultados, estado de cada tesis y "
                    f"qué mirar la semana que viene: <a href='{URL_REPO}{semana.as_posix()}' style='color:{C['ac']}'>"
                    f"leer la revisión {semana.stem}</a></p>")

    html = f"""<div style="font-family:Inter,Segoe UI,Arial,sans-serif;background:{C['bg']};padding:20px">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:14px;padding:22px;color:{C['tx']}">
<div style="font-size:12px;color:{C['mu']}">Agente Inversor – Facundo · simulado, sin dinero real</div>
<h2 style="margin:4px 0 14px;font-size:20px">{titulo} · {_fecha(fecha)}</h2>
{tabla}
<h3 style="font-size:13px;color:{C['mu']};text-transform:uppercase;margin:20px 0 4px">Qué hizo el agente</h3>
{nov_html}
<h3 style="font-size:13px;color:{C['mu']};text-transform:uppercase;margin:20px 0 4px">Booms del momento</h3>
<table width="100%" style="font-size:14px">{booms}</table>
{revision}<p style="margin:22px 0 6px"><a href="{WEB}" style="background:{C['ac']};color:#fff;text-decoration:none;
padding:10px 18px;border-radius:999px;font-weight:600;font-size:14px">Ver el tablero completo</a></p>
<p style="font-size:11px;color:{C['mu']};margin-top:18px">Herramienta de análisis y simulación. No es
asesoramiento financiero. Antes de operar verificá precios y ratios en tu broker.</p>
</div></div>"""
    return asunto, html


def enviar(asunto, html):
    usuario, clave = os.environ.get("GMAIL_USUARIO"), os.environ.get("GMAIL_CLAVE")
    destino = os.environ.get("MAIL_DESTINO") or usuario
    msg = MIMEMultipart("alternative")
    msg["Subject"], msg["From"], msg["To"] = asunto, f"Agente Inversor <{usuario}>", destino
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
        s.login(usuario, clave.replace(" ", ""))
        s.sendmail(usuario, [destino], msg.as_string())


def main(prueba=False):
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    dia = db.conectar(cfg["datos"]["base_diario"])
    con = db.conectar(cfg["datos"]["base_precios"])
    fecha = dia.execute("SELECT MAX(fecha) FROM equity").fetchone()[0]
    if not fecha:
        print("Alertas: todavía no hay datos.")
        return
    fila = dia.execute("SELECT ultima_fecha FROM estado_motor WHERE nombre='alertas'").fetchone()
    if fila and fila[0] == fecha and not prueba:
        print(f"Alertas: ya se avisó lo del {fecha}.")
        return
    semanal = pd.Timestamp(fecha).weekday() == 4          # viernes
    asunto, html = armar(cfg, dia, con, fecha, semanal or prueba)
    if prueba:
        REP.mkdir(exist_ok=True)
        (REP / "mail_prueba.html").write_text(html or "", encoding="utf-8")
        print("Mail de prueba:", asunto)
        return
    if asunto is None:
        print("Alertas: sin novedades hoy.")
    elif not (os.environ.get("GMAIL_USUARIO") and os.environ.get("GMAIL_CLAVE")):
        print("Alertas: faltan los secrets GMAIL_USUARIO / GMAIL_CLAVE; no se envía.")
        return
    else:
        enviar(asunto, html)
        print("Alertas: mail enviado ->", asunto)
    dia.execute("INSERT OR REPLACE INTO estado_motor VALUES ('alertas', ?, ?)", (fecha, json.dumps({})))
    dia.commit()


if __name__ == "__main__":
    main(prueba="--prueba" in sys.argv)
