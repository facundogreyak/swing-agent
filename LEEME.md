# Agente Swing Trading – CEDEARs (paper trading)

Corre solo en GitHub Actions de lunes a viernes a las 18:30 (hora Argentina).
Resultados: pestaña **Actions** del repo, carpeta `reportes/` y la página web (GitHub Pages, carpeta `docs/`).

## Archivos
- `config.yaml`   → todos los parámetros (universo, estrategia, riesgo)
- `etapa1.py`     → baja precios y los guarda en `data/agente.db`
- `estrategia.py` / `indicadores.py` → reglas de entrada, stop y tamaño de posición
- `backtest.py`   → simula la estrategia sobre la historia → `reportes/backtest.md`
- `tablero.py`    → genera la página web `docs/index.html`
- `run_diario.py` → lo que ejecuta GitHub cada día

## Hoja de ruta
1. Datos + base SQLite ✔
2. Señales ✔
3. Backtest ✔ (falta revisar resultados con datos reales)
4. Paper trading diario con diario de decisiones
5. Métricas por versión de parámetros
6. Alertas
