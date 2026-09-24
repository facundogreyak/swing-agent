"""
Punto de entrada que corre GitHub Actions cada día:
  1. Actualiza precios (Etapa 1)
  2. Corre el backtest (Etapa 3)
  3. Regenera la página web (docs/index.html)
"""
import runpy
import backtest
import tablero

print("=== 1. Datos ===")
runpy.run_path("etapa1.py", run_name="__main__")
print("\n=== 2. Backtest ===")
backtest.main()
print("\n=== 3. Tablero ===")
tablero.main()
