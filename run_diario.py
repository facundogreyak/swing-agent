"""
Punto de entrada que corre GitHub Actions cada día:
  1. Actualiza precios
  2. Paper trading swing (retroceso) y momentum ("booms del momento")
  3. Backtests y calibraciones de ambas estrategias
  4. Traduce la cartera a CEDEARs en pesos (CCL implícito, caros/baratos)
     y escribe la tesis de cada compra + la revisión semanal (tesis.py)
  5. Regenera la página web (docs/index.html)
  6. Manda un mail si hubo compras/ventas (y el resumen de los viernes)
"""
import runpy
from pathlib import Path
import backtest
import alertas
import cedears
import momentum
import paper
import setups
import tablero
import tesis

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
print("\n=== 3c. Setups de swing (screener) ===")
setups.main()
print("\n=== 4. CEDEARs en pesos ===")
cedears.main()
print("\n=== 4b. Tesis de inversión y revisión semanal ===")
try:
    tesis.main()
except Exception as e:                      # un problema con las tesis no debe frenar al tablero ni al mail
    print("Tesis: no se pudieron escribir:", repr(e))
print("\n=== 5. Tablero ===")
tablero.main()
print("\n=== 6. Alertas por mail ===")
try:
    alertas.main()
except Exception as e:                      # un problema con el mail no debe frenar al agente
    print("Alertas: no se pudo enviar el mail:", e)
