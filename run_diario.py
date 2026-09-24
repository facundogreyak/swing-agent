"""
Punto de entrada que corre GitHub Actions cada día:
  1. Actualiza precios (Etapa 1)
  2. Corre el backtest y la calibración (Etapa 3)
  3. Regenera la página web (docs/index.html)
"""
import runpy
from pathlib import Path
import backtest
import tablero

# La base vieja (precios + diario juntos) se reemplazó por precios.db + diario.db
viejo = Path("data/agente.db")
if viejo.exists():
    viejo.unlink()

print("=== 1. Datos ===")
runpy.run_path("etapa1.py", run_name="__main__")
print("\n=== 2. Backtest y calibración ===")
backtest.main(con_calibracion=True)
print("\n=== 3. Tablero ===")
tablero.main()
