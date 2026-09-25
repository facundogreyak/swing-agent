"""
publicar.py - Lleva las tesis y las revisiones semanales a la página web y arma el PDF semanal.

  1. Web: convierte los .md de reportes/tesis/ y reportes/revision_semanal/ en páginas HTML dentro de
     docs/ (el sitio de GitHub Pages, junto al tablero), con el mismo estilo y listas para imprimir.
       docs/tesis/index.html                  -> todas las tesis
       docs/tesis/<cartera>/<fecha>_<T>.html  -> cada tesis
       docs/revision_semanal/index.html       -> todas las revisiones (con su PDF)
       docs/revision_semanal/<AAAA-Sxx>.html  -> cada revisión
  2. PDF: por cada revisión semanal, un PDF con la revisión + las tesis que se abrieron o cerraron
     esa semana (docs/revision_semanal/<AAAA-Sxx>.pdf). Se hace una sola vez por semana con el Chrome
     que ya trae el servidor de GitHub (o el que indique la variable CHROME). El mail de los viernes
     lo manda adjunto.

Ejecutar:  python publicar.py
"""
import html
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import markdown
import pandas as pd

REP = Path("reportes")
DOCS = Path("docs")
WEB = "https://facundogreyak.github.io/swing-agent/"
NOMBRE = "Agente Inversor – Facundo"

ESTILO = """
:root{--bg:#f5f6fa;--card:#fff;--tx:#111827;--mu:#6b7280;--bd:#e5e7eb;--ac:#4f46e5;--ac2:#eef2ff;
  --pos:#16a34a;--neg:#dc2626}
@media (prefers-color-scheme: dark){:root{--bg:#0f1117;--card:#171a22;--tx:#e5e7eb;--mu:#9ca3af;--bd:#2a2f3a;
  --ac:#818cf8;--ac2:#1e2140}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.6 Inter,system-ui,-apple-system,"Segoe UI",Arial,sans-serif}
header{max-width:860px;margin:0 auto;padding:18px 16px 0;font-size:13px;color:var(--mu)}
header a{color:var(--ac);text-decoration:none;margin-right:14px}
main{max-width:860px;margin:10px auto 40px;padding:24px 22px;background:var(--card);border-radius:16px;
  box-shadow:0 1px 2px rgba(17,24,39,.04),0 4px 16px rgba(17,24,39,.06)}
h1{font-size:24px;line-height:1.25;margin:0 0 8px}
h2{font-size:18px;margin:28px 0 8px;padding-top:14px;border-top:1px solid var(--bd)}
h3{font-size:15px;margin:20px 0 6px}
a{color:var(--ac)}
blockquote{margin:12px 0;padding:10px 14px;background:var(--ac2);border-radius:10px;color:var(--mu);font-size:13px}
blockquote p{margin:0}
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:14px;margin:8px 0}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--bd);vertical-align:top}
th{color:var(--mu);font-weight:600;font-size:12px}
ul{padding-left:20px}li{margin:3px 0}
details{margin:10px 0}summary{cursor:pointer;color:var(--mu)}
.pie{max-width:860px;margin:0 auto 30px;padding:0 16px;font-size:12px;color:var(--mu)}
.boton{display:inline-block;background:var(--ac);color:#fff!important;text-decoration:none;padding:6px 14px;
  border-radius:999px;font-weight:600;font-size:13px}
.salto{page-break-before:always;break-before:page}
@media (max-width:600px){main{padding:16px 14px;border-radius:0;margin:6px 0 30px}h1{font-size:20px}
  table{font-size:13px}th,td{padding:6px 6px}}
@media print{
  @page{size:A4;margin:14mm 12mm}
  :root{--bg:#fff;--card:#fff;--tx:#111827;--mu:#4b5563;--bd:#d1d5db;--ac:#3730a3;--ac2:#f3f4f6}
  body{font-size:11pt;background:#fff}
  header,.pie,.no-imprimir{display:none}
  main{box-shadow:none;margin:0;padding:0;max-width:none}
  a{color:inherit;text-decoration:none}
  tr,li,blockquote{break-inside:avoid}
  h2,h3{break-after:avoid}
  .tw{overflow:visible}
}
"""


def md_a_html(texto):
    cuerpo = markdown.markdown(texto, extensions=["tables", "sane_lists", "md_in_html"])
    cuerpo = cuerpo.replace("<table>", "<div class='tw'><table>").replace("</table>", "</table></div>")
    # links entre documentos: .md -> .html, README -> index
    return re.sub(r'href="([^"#:]+?)(README)?\.md(#[^"]*)?"',
                  lambda m: f'href="{m.group(1)}{"index" if m.group(2) else ""}.html{m.group(3) or ""}"', cuerpo)


def pagina(titulo, cuerpo, raiz, extra_header=""):
    """raiz: ruta relativa hasta docs/ (p. ej. '../../')."""
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(titulo)} · {NOMBRE}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>{ESTILO}</style></head><body>
<header><a href="{raiz}index.html">← Tablero</a><a href="{raiz}tesis/index.html">Tesis</a>
<a href="{raiz}revision_semanal/index.html">Revisiones semanales</a>{extra_header}</header>
<main>{cuerpo}</main>
<div class="pie">{NOMBRE} · Simulado, sin dinero real. Herramienta de análisis: no es asesoramiento financiero.
Para guardarlo en PDF: Imprimir → Guardar como PDF.</div>
</body></html>"""


def _titulo(md):
    m = re.search(r"^# (.+)$", md, re.M)
    return m.group(1).strip() if m else "Documento"


def publicar_web():
    """Convierte todos los .md de tesis y revisiones a HTML en docs/ (solo reescribe si cambió)."""
    escritos = 0
    for origen in list((REP / "tesis").rglob("*.md")) + list((REP / "revision_semanal").glob("*.md")):
        rel = origen.relative_to(REP)
        destino = DOCS / rel.with_name("index.html" if origen.name == "README.md" else origen.stem + ".html")
        raiz = "../" * (len(rel.parts) - 1)
        md = origen.read_text(encoding="utf-8")
        extra = ""
        if origen.parent.name == "revision_semanal" and (DOCS / "revision_semanal" / f"{origen.stem}.pdf").exists():
            extra = f"<a href='{origen.stem}.pdf'>Descargar PDF</a>"
        doc = pagina(_titulo(md), md_a_html(md), raiz, extra)
        destino.parent.mkdir(parents=True, exist_ok=True)
        if not destino.exists() or destino.read_text(encoding="utf-8") != doc:
            destino.write_text(doc, encoding="utf-8")
            escritos += 1
    # tesis que ya no tienen .md (p. ej. señales que no se operaron): se borra su página
    if (DOCS / "tesis").exists():
        for h in (DOCS / "tesis").rglob("*.html"):
            if h.name != "index.html" and not (REP / h.relative_to(DOCS)).with_suffix(".md").exists():
                h.unlink()
    indice_semanal()
    return escritos


def indice_semanal():
    semanas = sorted((REP / "revision_semanal").glob("*.md"), reverse=True)
    filas = []
    for s in semanas:
        md = s.read_text(encoding="utf-8")
        m = re.search(r"Semana del ([\d/]+) al ([\d/]+)", md)
        pdf = (DOCS / "revision_semanal" / f"{s.stem}.pdf").exists()
        filas.append(f"<tr><td><a href='{s.stem}.html'><b>{s.stem}</b></a></td>"
                     f"<td>{m.group(1) + ' al ' + m.group(2) if m else ''}</td>"
                     f"<td>{f'<a href={chr(39)}{s.stem}.pdf{chr(39)}>PDF</a>' if pdf else ''}</td></tr>")
    cuerpo = ("<h1>Revisiones semanales</h1><p>Una por semana, con la última rueda: resultados, movimientos, "
              "estado de cada tesis, noticias de la cartera y qué mirar la semana siguiente. El PDF incluye además "
              "las tesis que se abrieron o cerraron esa semana.</p>"
              + (f"<div class='tw'><table><thead><tr><th>Semana</th><th>Fechas</th><th></th></tr></thead>"
                 f"<tbody>{''.join(filas)}</tbody></table></div>" if filas else "<p>Todavía no hay revisiones.</p>"))
    destino = DOCS / "revision_semanal" / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(pagina("Revisiones semanales", cuerpo, "../"), encoding="utf-8")


# ---------------------------------------------------------------------------
# PDF semanal
# ---------------------------------------------------------------------------
def _chrome():
    for c in (os.environ.get("CHROME"), "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        if c and (shutil.which(c) or Path(c).exists()):
            return shutil.which(c) or c
    return None


def _absolutos(cuerpo, ruta_rel):
    """Links relativos -> absolutos al sitio (en el PDF no hay 'carpetas')."""
    base = WEB + ruta_rel
    from urllib.parse import urljoin
    return re.sub(r'href="(?!https?:|mailto:|#)([^"]+)"', lambda m: f'href="{urljoin(base, m.group(1))}"', cuerpo)


def tesis_de_la_semana(md_semana):
    """Tesis que se abrieron o cerraron en la semana (según las fechas de la revisión)."""
    m = re.search(r"Semana del ([\d/]+) al ([\d/]+)", md_semana)
    f = REP / "tesis" / "estado.csv"
    if not m or not f.exists():
        return []
    ini, fin = (pd.to_datetime(x, dayfirst=True).strftime("%Y-%m-%d") for x in m.groups())
    d = pd.read_csv(f)
    d = d[d.estado != "NO EJECUTADA"]
    sel = d[d.fecha.between(ini, fin) | d.fecha_salida.fillna("").between(ini, fin)]
    return [REP / a for a in sel.sort_values("fecha").archivo if (REP / a).exists()]


def pdf_semanal(clave, chrome):
    md_sem = (REP / "revision_semanal" / f"{clave}.md").read_text(encoding="utf-8")
    partes = [_absolutos(md_a_html(md_sem), f"revision_semanal/{clave}.html")]
    tesis = tesis_de_la_semana(md_sem)
    if tesis:
        partes.append("<h1 class='salto'>Tesis de la semana</h1><p>Las tesis que se abrieron o se cerraron esta "
                      "semana, completas. Las que siguen abiertas están en la web con su seguimiento al día.</p><ul>"
                      + "".join(f"<li>{html.escape(_titulo(t.read_text(encoding='utf-8')))}</li>" for t in tesis)
                      + "</ul>")
    for t in tesis:
        rel = t.relative_to(REP).with_suffix(".html").as_posix()
        partes.append("<div class='salto'></div>" + _absolutos(md_a_html(t.read_text(encoding="utf-8")), rel))
    doc = pagina(f"Revisión semanal {clave}", "\n".join(partes), WEB)
    destino = DOCS / "revision_semanal" / f"{clave}.pdf"
    with tempfile.TemporaryDirectory() as tmp:
        fuente = Path(tmp) / "semana.html"
        fuente.write_text(doc, encoding="utf-8")
        subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={destino.resolve()}", "--virtual-time-budget=8000", fuente.as_uri()],
                       check=True, capture_output=True, timeout=180)
    return destino


def main():
    n = publicar_web()
    print(f"Publicar: {n} páginas actualizadas en docs/")
    faltan = [s.stem for s in sorted((REP / "revision_semanal").glob("*.md"))
              if not (DOCS / "revision_semanal" / f"{s.stem}.pdf").exists()]
    if not faltan:
        return
    chrome = _chrome()
    if not chrome:
        print("Publicar: no hay Chrome/Chromium en este equipo; el PDF semanal queda para la próxima corrida.")
        return
    for clave in faltan:
        try:
            print("Publicar: PDF semanal ->", pdf_semanal(clave, chrome))
        except Exception as e:
            print(f"Publicar: no se pudo armar el PDF de {clave}: {e}")
    publicar_web()                                 # agrega el link "Descargar PDF" a las revisiones


if __name__ == "__main__":
    main()
