"""
contexto.py - Datos de internet que acompañan cada tesis: la empresa, qué opinan los analistas,
cuándo presenta balance y las noticias recientes.

Fuentes (gratis, sin claves):
  - Yahoo Finance (vía yfinance): datos de la empresa, valuación, crecimiento, consenso de
    analistas, próxima fecha de balance y titulares recientes.
  - Google News (RSS): titulares de los últimos días.
Si una fuente no responde, la tesis sale igual y lo dice. Se configura en config.yaml -> tesis.
Las noticias son contexto: el agente NO decide con ellas (las reglas de compra y venta no cambian).
"""
import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import pandas as pd

TIMEOUT = 15
_cache = {}


def _n(v, dec=1):
    if v is None or pd.isna(v):
        return "—"
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(v, dec=0):
    if v is None or pd.isna(v):
        return "—"
    return f"{v:+.{dec}%}".replace(".", ",")


def _fecha(d):
    return pd.Timestamp(d).strftime("%d/%m/%Y")


def _num(x):
    try:
        v = float(x)
        return None if pd.isna(v) else v
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Fuentes
# ---------------------------------------------------------------------------
def _ticker(t):
    import yfinance as yf
    return yf.Ticker(t)


def empresa(t):
    """Datos básicos de la empresa según Yahoo Finance ({} si no responde)."""
    if ("info", t) not in _cache:
        try:
            _cache[("info", t)] = _ticker(t).info or {}
        except Exception as e:
            print(f"  contexto {t}: sin datos de la empresa ({e})")
            _cache[("info", t)] = {}
    return _cache[("info", t)]


def proximo_balance(t, desde):
    """Próxima fecha de presentación de resultados (o None)."""
    if ("bal", t) not in _cache:
        fechas = []
        try:
            cal = _ticker(t).calendar
            if isinstance(cal, dict):
                v = cal.get("Earnings Date") or []
                fechas = list(v) if isinstance(v, (list, tuple)) else [v]
            elif isinstance(cal, pd.DataFrame) and "Earnings Date" in cal.index:
                fechas = list(cal.loc["Earnings Date"].values)
        except Exception as e:
            print(f"  contexto {t}: sin fecha de balance ({e})")
        _cache[("bal", t)] = [pd.Timestamp(f).tz_localize(None) if pd.Timestamp(f).tzinfo else pd.Timestamp(f)
                              for f in fechas if f is not None and not pd.isna(f)]
    futuras = sorted(f for f in _cache[("bal", t)] if f.normalize() >= pd.Timestamp(desde).normalize())
    return futuras[0] if futuras else None


def _noticia_yahoo(a):
    """Normaliza un artículo de yfinance (formato nuevo con 'content' o el viejo plano)."""
    c = a.get("content") if isinstance(a.get("content"), dict) else a
    titulo = c.get("title")
    fecha = c.get("pubDate") or c.get("displayTime")
    if fecha is None and a.get("providerPublishTime"):
        fecha = datetime.fromtimestamp(a["providerPublishTime"], tz=timezone.utc)
    prov = c.get("provider")
    fuente = prov.get("displayName") if isinstance(prov, dict) else a.get("publisher")
    url = None
    for k in ("canonicalUrl", "clickThroughUrl"):
        if isinstance(c.get(k), dict) and c[k].get("url"):
            url = c[k]["url"]
            break
    url = url or a.get("link")
    if not titulo or fecha is None:
        return None
    ts = pd.Timestamp(fecha)
    return {"titulo": titulo.strip(), "fuente": fuente or "Yahoo Finance", "url": url,
            "fecha": ts.tz_convert(None) if ts.tzinfo else ts}


def noticias_yahoo(t):
    if ("ny", t) not in _cache:
        out = []
        try:
            for a in _ticker(t).get_news(count=20) or []:
                n = _noticia_yahoo(a)
                if n:
                    out.append(n)
        except Exception as e:
            print(f"  contexto {t}: sin noticias de Yahoo ({e})")
        _cache[("ny", t)] = out
    return _cache[("ny", t)]


def _parsear_rss(xml_txt):
    out = []
    raiz = ET.fromstring(xml_txt)
    for it in raiz.iter("item"):
        titulo = it.findtext("title") or ""
        fuente = it.findtext("source") or ""
        if fuente and titulo.endswith(" - " + fuente):          # Google agrega " - Fuente" al título
            titulo = titulo[: -len(fuente) - 3]
        try:
            fecha = pd.Timestamp(pd.to_datetime(it.findtext("pubDate"), utc=True)).tz_convert(None)
        except Exception:
            continue
        out.append({"titulo": html.unescape(titulo.strip()), "fuente": fuente or "Google News",
                    "url": it.findtext("link"), "fecha": fecha})
    return out


def noticias_google(consulta, dias):
    if ("ng", consulta) not in _cache:
        q = urllib.parse.quote(f"{consulta} when:{dias}d")
        url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                _cache[("ng", consulta)] = _parsear_rss(r.read())
        except Exception as e:
            print(f"  contexto: sin noticias de Google para '{consulta}' ({e})")
            _cache[("ng", consulta)] = []
    return _cache[("ng", consulta)]


def _nombre_corto(info, t):
    n = info.get("shortName") or info.get("longName") or t
    n = re.sub(r"[,.]?\s+(Inc|Incorporated|Corporation|Corp|Company|Co|Ltd|Limited|plc|S\.A|SA|N\.V|NV|Holdings?|"
               r"Group|& Co)\b\.?", "", n, flags=re.I)
    return n.strip(" ,.") or t


GENERICAS = {"bank", "banco", "american", "general", "united", "first", "international", "national", "global",
             "digital", "energy", "health", "capital", "financial", "technologies", "systems", "the"}


def _plano(x):
    return re.sub(r"[^a-z0-9]", "", str(x).lower())


def _relevante(titulo, t, info):
    """True si el titular nombra a la empresa (nombre, primera palabra distintiva o ticker)."""
    tp = _plano(titulo)
    nombre = _nombre_corto(info, t)
    claves = {_plano(nombre)}
    primera = nombre.split()[0] if nombre.split() else ""
    if len(_plano(primera)) >= 4 and _plano(primera) not in GENERICAS:
        claves.add(_plano(primera))
    if any(k and k in tp for k in claves):
        return True
    base = t.split("-")[0].split(".")[0]
    patron = rf"\b{re.escape(base)}\b" if len(base) >= 3 else rf"(\${re.escape(base)}\b|\({re.escape(base)}\))"
    return re.search(patron, titulo) is not None


# Páginas de cotización o notas generadas automáticamente: no aportan información
RELLENO = re.compile(r"\bstock (forecasts?|quote|price and news|price today|price,? news)\b|"
                     r"\bstock price \w+ \d{1,2},? \d{4}", re.I)


def _palabras(titulo, excluir=()):
    return {w for w in re.findall(r"[a-z0-9$]+", titulo.lower()) if len(w) > 2 and w not in excluir}


def _parecida(p, vistas):
    """True si el titular (sus palabras, sin el nombre de la empresa) cuenta lo mismo que uno ya elegido:
    la misma nota publicada por otra fuente."""
    return any(len(p & q) >= 3 and len(p & q) / max(1, min(len(p), len(q))) >= 0.5 for q in vistas)


def noticias(t, fecha, dias=7, maximo=5):
    """Titulares de los `dias` anteriores a `fecha` (Yahoo + Google News) que nombran a la empresa,
    sin páginas de cotización ni la misma nota repetida por otra fuente, más nuevos primero."""
    info = empresa(t)
    fin = pd.Timestamp(fecha) + timedelta(days=1)
    ini = fin - timedelta(days=dias + 1)
    todas = noticias_yahoo(t) + noticias_google(f'"{_nombre_corto(info, t)}" stock', dias)
    excluir = _palabras(f"{_nombre_corto(info, t)} {t}")
    vistas, out = [], []
    for n in sorted(todas, key=lambda x: x["fecha"], reverse=True):
        p = _palabras(n["titulo"], excluir)
        if not (ini <= n["fecha"] <= fin) or RELLENO.search(n["titulo"]) or _parecida(p, vistas) \
                or not _relevante(n["titulo"], t, info):
            continue
        vistas.append(p)
        out.append(n)
    return out[:maximo]


# ---------------------------------------------------------------------------
# Texto para las tesis
# ---------------------------------------------------------------------------
def lineas_noticias(lista):
    return [f"- {_fecha(n['fecha'])} · [{n['titulo'].replace('[', '(').replace(']', ')')}]({n['url']}) "
            f"— _{n['fuente']}_" if n.get("url") else f"- {_fecha(n['fecha'])} · {n['titulo']} — _{n['fuente']}_"
            for n in lista]


def seccion(t, fecha, precio, fin_plazo, cfg_t, que_plazo="la salida"):
    """Markdown con la empresa, analistas, próximo balance y noticias.
    Devuelve (markdown, alertas) donde alertas son frases para '¿qué invalidaría la tesis?'."""
    dias, maximo = cfg_t.get("dias_noticias", 7), cfg_t.get("max_noticias", 5)
    info = empresa(t)
    L, alertas = [], []

    # La empresa
    nombre = info.get("longName") or info.get("shortName")
    if nombre:
        partes = [f"**{nombre}**"]
        if info.get("industry"):
            partes.append(info["industry"])
        if _num(info.get("marketCap")):
            partes.append(f"capitalización USD {_n(info['marketCap'] / 1e9, 0)} mil millones")
        L.append("- " + " · ".join(partes) + ".")
        val = []
        pe, fpe = _num(info.get("trailingPE")), _num(info.get("forwardPE"))
        if pe:
            val.append(f"P/E {_n(pe)}")
        if fpe:
            val.append(f"P/E estimado {_n(fpe)}" + (" (se esperan más ganancias)" if pe and fpe < pe * 0.95 else
                                                    " (se esperan menos ganancias)" if pe and fpe > pe * 1.05 else ""))
        rg, eg, mg = _num(info.get("revenueGrowth")), _num(info.get("earningsGrowth")), _num(info.get("profitMargins"))
        if rg is not None:
            val.append(f"ventas {_pct(rg)} interanual")
        if eg is not None:
            val.append(f"ganancias {_pct(eg)} interanual")
        if mg is not None:
            val.append(f"margen neto {_pct(mg).lstrip('+')}")
        if _num(info.get("beta")):
            val.append(f"beta {_n(info['beta'], 2)}")
        if val:
            L.append("- Números: " + " · ".join(val) + ".")
        if (rg is not None and rg < 0) and (eg is not None and eg < 0):
            alertas.append("ventas y ganancias vienen cayendo: la suba se apoya más en el precio que en el negocio")

    # Analistas
    obj, n_an = _num(info.get("targetMeanPrice")), _num(info.get("numberOfAnalystOpinions"))
    rec = {"strong_buy": "compra fuerte", "buy": "compra", "hold": "mantener", "underperform": "bajo rendimiento",
           "sell": "venta", "strong_sell": "venta fuerte"}.get(info.get("recommendationKey"), None)
    if obj and precio:
        pot = obj / precio - 1
        L.append(f"- Analistas: precio objetivo promedio USD {_n(obj, 2)} ({_pct(pot)} desde acá)"
                 + (f", {int(n_an)} analistas" if n_an else "") + (f", recomendación: {rec}" if rec else "") + ".")
        if pot < 0:
            alertas.append(f"el precio ya está {_pct(-pot).lstrip('+')} arriba del objetivo promedio de los analistas")
    elif rec:
        L.append(f"- Analistas: recomendación {rec}.")

    # Próximo balance
    bal = proximo_balance(t, fecha)
    if bal is not None:
        dentro = fin_plazo is not None and bal <= pd.Timestamp(fin_plazo)
        L.append(f"- Próximo balance: {_fecha(bal)}" + (f" — **antes de {que_plazo}**." if dentro else "."))
        if dentro:
            alertas.append(f"presenta balance el {_fecha(bal)}, antes de {que_plazo}: el precio puede "
                           f"saltar para cualquier lado")

    # Noticias
    lista = noticias(t, fecha, dias, maximo)
    if not L and not lista:
        return (f"_No se pudieron obtener datos ni noticias de internet para {t} "
                f"(Yahoo Finance / Google News no respondieron)._", [])
    L += ["", f"**Noticias de los últimos {dias} días**", ""]
    L += lineas_noticias(lista) if lista else ["- Sin titulares relevantes en esos días."]
    return "\n".join(L), alertas
