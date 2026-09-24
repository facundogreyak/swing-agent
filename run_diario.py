"""
Punto de entrada que corre GitHub Actions cada día:
  1. Actualiza precios (Etapa 1)
  2. Paper trading: procesa el día y anota las decisiones (Etapa 4)
  3. Backtest y calibración (Etapa 3)
  4. Regenera la página web (docs/index.html)
"""
import runpy
from pathlib import Path
import backtest
import paper
import tablero

# La base vieja (precios + diario juntos) se reemplazó por precios.db + diario.db
viejo = Path("data/agente.db")
if viejo.exists():
    viejo.unlink()

print("=== 1. Datos ===")
runpy.run_path("etapa1.py", run_name="__main__")
print("\n=== 2. Paper trading ===")
paper.main()
print("\n=== 3. Backtest y calibración ===")
backtest.main(con_calibracion=True)
print("\n=== 4. Tablero ===")
tablero.main()
