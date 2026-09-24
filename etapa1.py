"""
ETAPA 1 - Crear la base, registrar los parámetros y bajar los datos.
Ejecutar:  python etapa1.py
"""
import yaml
import db, data

cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
con = db.conectar(cfg["datos"]["base_datos"])

version = db.registrar_version(con, cfg)
print(f"Parámetros registrados -> versión {version} ({cfg['nombre_version']})\n")

print("Descargando precios...")
data.actualizar_todo(con, cfg)

print("\nResumen de la base:")
for t, n, desde, hasta in con.execute(
        "SELECT ticker, COUNT(*), MIN(fecha), MAX(fecha) FROM precios GROUP BY ticker ORDER BY ticker"):
    print(f"  {t:10s} {n:5d} velas  {desde} -> {hasta}")

ejemplo = cfg["universo"][0]["subyacente"]
print(f"\nÚltimas 5 velas de {ejemplo}:")
print(data.cargar_precios(con, ejemplo).tail())
