# Backtest – v1-base

Período: 2024-07-11 → 2026-09-24 · Tickers con datos: 50 de 50 · Capital inicial: USD 10,000

## Configuración base

| Métrica | Valor |
|---|---|
| operaciones | 209 |
| win_rate | 46.4% |
| r_promedio (expectancy) | 0.13 |
| ganancia_prom_R | 1.31 |
| perdida_prom_R | -0.88 |
| profit_factor | 1.21 |
| dias_prom_en_posicion | 10.19 |
| retorno_total | 23.9% |
| retorno_anual (CAGR) | 10.2% |
| max_drawdown | -16.4% |
| exposicion_prom | 66.6% |
| spy_retorno_total | 41.3% |
| spy_max_drawdown | -18.8% |

## Variantes de riesgo por operación

| Variante | operaciones | win_rate | r_promedio (expectancy) | retorno_anual (CAGR) | max_drawdown | exposicion_prom |
|---|---|---|---|---|---|---|
| riesgo 0.5% | 209 | 46.4% | 0.13 | 6.2% | -8.5% | 37.3% |
| riesgo 1.0% | 209 | 46.4% | 0.13 | 10.2% | -16.4% | 66.6% |
| riesgo 2.0% | 208 | 47.1% | 0.13 | 11.3% | -22.7% | 79.5% |

## Resultado por motivo de salida

| Motivo | Operaciones | R promedio |
|---|---|---|
| FIN BACKTEST | 5 | -0.10 |
| OBJETIVO | 31 | 1.94 |
| OBJETIVO (gap) | 9 | 2.92 |
| STOP | 65 | -1.06 |
| STOP (gap) | 15 | -1.25 |
| TIEMPO | 84 | 0.35 |

## Resultado por sector

| Sector | Operaciones | Win rate | R promedio | PnL USD |
|---|---|---|---|---|
| China | 7 | 86% | 0.42 | 276 |
| Consumo | 38 | 47% | 0.11 | 361 |
| Energía / Industria | 20 | 35% | -0.23 | -548 |
| Financieras | 34 | 56% | 0.30 | 813 |
| Latam / Brasil | 26 | 42% | -0.08 | -390 |
| Salud | 13 | 38% | -0.14 | -120 |
| Tecnología | 71 | 44% | 0.27 | 1,976 |

## Últimas 10 operaciones

| ticker   | sector              | fecha_entrada   |   precio_entrada |      stop |   objetivo |   cantidad | fecha_salida   |   precio_salida | motivo_salida   |   dias |   pnl_usd |   r_multiple |
|:---------|:--------------------|:----------------|-----------------:|----------:|-----------:|-----------:|:---------------|----------------:|:----------------|-------:|----------:|-------------:|
| C        | Financieras         | 2026-07-31      |          132.874 |  125.227  |   148.17   |    15.823  | 2026-08-21     |         131.65  | TIEMPO          |     15 |    -25.65 |        -0.21 |
| AVGO     | Tecnología          | 2026-08-24      |          364.307 |  333.803  |   425.314  |     4.0354 | 2026-09-15     |         338.653 | TIEMPO          |     15 |   -107.78 |        -0.88 |
| C        | Financieras         | 2026-08-24      |          131.39  |  124.884  |   144.402  |    18.9198 | 2026-09-15     |         136.17  | TIEMPO          |     15 |     82.84 |         0.67 |
| INTC     | Tecnología          | 2026-08-28      |           90.27  |   78.6553 |   113.499  |    10.6309 | 2026-09-21     |         116.53  | OBJETIVO (gap)  |     15 |    275.87 |         2.23 |
| BAC      | Financieras         | 2026-09-16      |           59.27  |   56.708  |    64.3939 |    48.3329 | 2026-09-22     |          56.708 | STOP            |      4 |   -132.24 |        -1.07 |
| CAT      | Energía / Industria | 2026-09-03      |          796.9   |  739.604  |   911.492  |     2.1665 | 2026-09-24     |         800.49  | FIN BACKTEST    |     13 |      2.59 |         0.02 |
| LLY      | Salud               | 2026-09-10      |         1126.08  | 1057.46   |  1263.32   |     1.8277 | 2026-09-24     |        1196.27  | FIN BACKTEST    |      9 |    121.92 |         0.97 |
| AMZN     | Tecnología          | 2026-09-18      |          252.92  |  240.572  |   277.617  |    10.0976 | 2026-09-24     |         246.425 | FIN BACKTEST    |      4 |    -73.15 |        -0.59 |
| BAC      | Financieras         | 2026-09-22      |           58.1   |   55.5847 |    63.1306 |    49.9057 | 2026-09-24     |          56.455 | FIN BACKTEST    |      2 |    -90.67 |        -0.72 |
| PYPL     | Tecnología          | 2026-09-23      |           52.79  |   49.4652 |    59.4396 |    37.1478 | 2026-09-24     |          52.415 | FIN BACKTEST    |      1 |    -19.79 |        -0.16 |