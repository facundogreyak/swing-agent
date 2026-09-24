"""
Punto de entrada que corre GitHub Actions cada día:
  1. Actualiza precios
  2. Paper trading swing (retroceso) y momentum ("booms del momento")
  3. Backtests y calibraciones de ambas estrategias
  4. Regenera la página web (docs/index.html)
"""
import runpy
from pathlib import Path
import backtest
import momentum
import paper
import tablero

# La base vieja (precios + diario juntos) se reemplazó por precios.db + diario.db
viejo = Path("data/agente.db")
if viejo.exists():
    viejo.unlink()

print("=== 1. Datos ===")
runpy.run_path("etapa1.py", run_name="__main__")
print("\n=== 2a. Paper trading swing ===")
paper.main()
print("\n=== 2b. Paper trading momentum ===")
momentum.paper()
print("\n=== 3a. Backtest y calibración swing ===")
backtest.main(con_calibracion=True)
print("\n=== 3b. Backtest y calibración momentum ===")
momentum.main()
print("\n=== 4. Tablero ===")
tablero.main()
