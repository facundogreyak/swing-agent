"""
ETAPA 1 - Registrar los parámetros y actualizar los precios.
Ejecutar:  python etapa1.py

Usa dos bases:
  data/precios.db -> velas diarias (se reconstruye/actualiza sola, no se sube a GitHub)
  data/diario.db  -> versiones de parámetros, decisiones y operaciones (se sube a GitHub)
"""
import yaml
import db, data

cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
con_diario = db.conectar(cfg["datos"]["base_diario"])
con = db.conectar(cfg["datos"]["base_precios"])

version = db.registrar_version(con_diario, cfg)
print(f"Parámetros registrados -> versión {version} ({cfg['nombre_version']})\n")

print("Descargando precios...")
data.actualizar_todo(con, cfg)

print("\nResumen de la base:")
for t, n, desde, hasta in con.execute(
        "SELECT ticker, COUNT(*), MIN(fecha), MAX(fecha) FROM precios GROUP BY ticker ORDER BY ticker"):
    marca = "  <-- revisar" if n < 200 else ""
    print(f"  {t:10s} {n:5d} velas  {desde} -> {hasta}{marca}")
