# Agente Swing Trading – CEDEARs (paper trading)

Corre solo en GitHub Actions de lunes a viernes a las 18:30 (hora Argentina).
Tablero: GitHub Pages (carpeta `docs/`). Reportes: carpeta `reportes/`.

## Archivos
- `config.yaml`   → todos los parámetros (universo, entrada, riesgo, grilla de calibración)
- `etapa1.py` / `data.py` → bajan precios a `data/precios.db` (caché, no se sube)
- `indicadores.py` / `estrategia.py` → reglas de entrada (retroceso o ruptura), stop y tamaño
- `paper.py`      → paper trading diario del swing: órdenes, operaciones y decisiones en `data/diario.db`
- `momentum.py`   → "booms del momento": rotación por momentum 100% invertida (backtest, calibración,
                    análisis de qué pesa más y paper trading con el mismo motor)
- `backtest.py`   → backtest + calibración dentro/fuera de muestra → `reportes/`
- `cedears.py`    → pasa la cartera a CEDEARs en pesos: ratios, dólar CCL implícito, caros/baratos
- `tesis.py`      → cada compra (swing y momentum) escrita como tesis de inversión en `reportes/tesis/`:
                    la idea, por qué ahora, el plan, qué la invalida y qué esperar según el backtest (se congela
                    el día de la decisión), y después ejecución, seguimiento y cierre con veredicto.
                    Cada semana escribe la revisión de la cartera en `reportes/revision_semanal/`
- `alertas.py`    → mail con compras/ventas y resumen de los viernes (secrets GMAIL_USUARIO y GMAIL_CLAVE)
- `universo_ampliado.csv` → ~140 acciones más con CEDEAR, para comparar con la lista de 50
- `tablero.py`    → página web `docs/index.html`
- `run_diario.py` → lo que ejecuta GitHub cada día

## Reglas del paper trading
Idénticas al backtest: señal al cierre → compra en la apertura siguiente; salida por stop,
objetivo o tiempo; máx. posiciones y por sector; comisión en cada lado.
Cada decisión y operación guarda la versión de parámetros con la que se tomó.

## Hoja de ruta
1. Datos ✔  2. Señales ✔  3. Backtest y calibración ✔  4. Paper trading ✔ (swing + momentum)
5. Métricas por versión de parámetros  6. Alertas ✔  7. Tesis de inversión y revisión semanal ✔
