# Backtest – v1-base

Período: 2024-07-11 → 2026-09-24 · Tickers con datos: 50 de 50 · Capital inicial: USD 10,000

## Configuración base

| Métrica | Valor |
|---|---|
| operaciones | 209 |
| win_rate | 45.9% |
| r_promedio (expectancy) | 0.13 |
| ganancia_prom_R | 1.32 |
| perdida_prom_R | -0.88 |
| profit_factor | 1.21 |
| dias_prom_en_posicion | 10.19 |
| retorno_total | 23.4% |
| retorno_anual (CAGR) | 10.0% |
| max_drawdown | -16.4% |
| exposicion_prom | 66.6% |
| spy_retorno_total | 40.9% |
| spy_max_drawdown | -18.8% |

## Variantes de riesgo por operación

| Variante | operaciones | win_rate | r_promedio (expectancy) | retorno_anual (CAGR) | max_drawdown | exposicion_prom |
|---|---|---|---|---|---|---|
| riesgo 0.5% | 209 | 45.9% | 0.13 | 6.1% | -8.5% | 37.3% |
| riesgo 1.0% | 209 | 45.9% | 0.13 | 10.0% | -16.4% | 66.6% |
| riesgo 2.0% | 208 | 46.6% | 0.13 | 11.1% | -22.7% | 79.5% |

## Resultado por motivo de salida

| Motivo | Operaciones | R promedio |
|---|---|---|
| FIN BACKTEST | 5 | -0.17 |
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
| Energía / Industria | 20 | 30% | -0.23 | -557 |
| Financieras | 34 | 56% | 0.29 | 788 |
| Latam / Brasil | 26 | 42% | -0.08 | -390 |
| Salud | 13 | 38% | -0.14 | -127 |
| Tecnología | 71 | 44% | 0.27 | 1,972 |

## Últimas 10 operaciones

| ticker   | sector              | fecha_entrada   |   precio_entrada |      stop |   objetivo |   cantidad | fecha_salida   |   precio_salida | motivo_salida   |   dias |   pnl_usd |   r_multiple |
|:---------|:--------------------|:----------------|-----------------:|----------:|-----------:|-----------:|:---------------|----------------:|:----------------|-------:|----------:|-------------:|
| C        | Financieras         | 2026-07-31      |          132.874 |  125.227  |   148.17   |    15.823  | 2026-08-21     |         131.65  | TIEMPO          |     15 |    -25.65 |        -0.21 |
| AVGO     | Tecnología          | 2026-08-24      |          364.307 |  333.803  |   425.314  |     4.0354 | 2026-09-15     |         338.653 | TIEMPO          |     15 |   -107.78 |        -0.88 |
| C        | Financieras         | 2026-08-24      |          131.39  |  124.884  |   144.402  |    18.9198 | 2026-09-15     |         136.17  | TIEMPO          |     15 |     82.84 |         0.67 |
| INTC     | Tecnología          | 2026-08-28      |           90.27  |   78.6553 |   113.499  |    10.6309 | 2026-09-21     |         116.53  | OBJETIVO (gap)  |     15 |    275.87 |         2.23 |
| BAC      | Financieras         | 2026-09-16      |           59.27  |   56.708  |    64.3939 |    48.3329 | 2026-09-22     |          56.708 | STOP            |      4 |   -132.24 |        -1.07 |
| CAT      | Energía / Industria | 2026-09-03      |          796.9   |  739.604  |   911.492  |     2.1665 | 2026-09-24     |         796.34  | FIN BACKTEST    |     13 |     -6.39 |        -0.05 |
| LLY      | Salud               | 2026-09-10      |         1126.08  | 1057.46   |  1263.32   |     1.8277 | 2026-09-24     |        1192.02  | FIN BACKTEST    |      9 |    114.16 |         0.91 |
| AMZN     | Tecnología          | 2026-09-18      |          252.92  |  240.572  |   277.617  |    10.0976 | 2026-09-24     |         246.531 | FIN BACKTEST    |      4 |    -72.08 |        -0.58 |
| BAC      | Financieras         | 2026-09-22      |           58.1   |   55.5847 |    63.1306 |    49.9057 | 2026-09-24     |          55.955 | FIN BACKTEST    |      2 |   -115.59 |        -0.92 |
| PYPL     | Tecnología          | 2026-09-23      |           52.79  |   49.4652 |    59.4396 |    37.1478 | 2026-09-24     |          52.265 | FIN BACKTEST    |      1 |    -25.36 |        -0.21 |