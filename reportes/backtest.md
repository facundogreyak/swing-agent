# Backtest – v2-filtro-mercado

Período: 2017-07-13 → 2026-09-24 · Tickers con datos: 50 de 50 · Capital inicial: USD 10,000

## Configuración actual

| Métrica | Valor |
|---|---|
| operaciones | 664 |
| win_rate | 45.8% |
| r_promedio (expectancy) | 0.04 |
| ganancia_prom_R | 1.19 |
| perdida_prom_R | -0.92 |
| profit_factor | 1.05 |
| dias_prom_en_posicion | 10.34 |
| retorno_total | 14.1% |
| retorno_anual (CAGR) | 1.4% |
| max_drawdown | -26.6% |
| retorno/caida (MAR) | 0.05 |
| exposicion_prom | 55.2% |
| spy_retorno_anual | 15.0% |
| spy_max_drawdown | -33.7% |

## Retorno por año

| Año | Agente | SPY |
|---|---|---|
| 2017 | 9.8% | 10.3% |
| 2018 | -19.2% | -4.6% |
| 2019 | 11.0% | 31.2% |
| 2020 | -2.8% | 18.3% |
| 2021 | -1.1% | 28.7% |
| 2022 | 3.5% | -18.2% |
| 2023 | -0.2% | 26.2% |
| 2024 | 13.1% | 24.9% |
| 2025 | 13.3% | 17.7% |
| 2026 | -9.0% | 13.0% |

## Variantes de riesgo por operación

| Variante | operaciones | win_rate | r_promedio (expectancy) | retorno_anual (CAGR) | max_drawdown | exposicion_prom |
|---|---|---|---|---|---|---|
| riesgo 0.5% | 664 | 45.8% | 0.05 | 1.4% | -13.8% | 32.2% |
| riesgo 1.0% | 664 | 45.8% | 0.04 | 1.4% | -26.6% | 55.2% |
| riesgo 2.0% | 650 | 45.5% | 0.06 | 1.7% | -30.6% | 62.4% |

## Resultado por motivo de salida

| Motivo | Operaciones | R promedio |
|---|---|---|
| FIN PERÍODO | 5 | -0.17 |
| OBJETIVO | 86 | 1.93 |
| OBJETIVO (gap) | 23 | 2.55 |
| STOP | 204 | -1.07 |
| STOP (gap) | 61 | -1.32 |
| TIEMPO | 285 | 0.36 |

## Resultado por sector

| Sector | Operaciones | Win rate | R promedio | PnL USD |
|---|---|---|---|---|
| China | 14 | 57% | -0.24 | -358 |
| Consumo | 136 | 43% | -0.01 | -633 |
| Energía / Industria | 61 | 36% | -0.25 | -1,549 |
| Financieras | 99 | 45% | 0.08 | 518 |
| Latam / Brasil | 89 | 46% | -0.05 | -620 |
| Salud | 63 | 52% | 0.20 | 1,066 |
| Tecnología | 202 | 48% | 0.17 | 2,969 |

## Últimas 10 operaciones

| ticker   | sector              | fecha_entrada   |   precio_entrada |   stop_inicial |   objetivo |   cantidad | fecha_salida   |   precio_salida | motivo_salida   |   dias |   pnl_usd |   r_multiple |
|:---------|:--------------------|:----------------|-----------------:|---------------:|-----------:|-----------:|:---------------|----------------:|:----------------|-------:|----------:|-------------:|
| C        | Financieras         | 2026-07-31      |          132.874 |       125.227  |   148.17   |    14.6314 | 2026-08-21     |         131.65  | TIEMPO          |     15 |    -23.72 |        -0.21 |
| AVGO     | Tecnología          | 2026-08-24      |          364.307 |       333.803  |   425.314  |     3.7315 | 2026-09-15     |         338.653 | TIEMPO          |     15 |    -99.66 |        -0.88 |
| C        | Financieras         | 2026-08-24      |          131.39  |       124.884  |   144.402  |    17.495  | 2026-09-15     |         136.17  | TIEMPO          |     15 |     76.6  |         0.67 |
| INTC     | Tecnología          | 2026-08-28      |           90.27  |        78.6553 |   113.499  |     9.8303 | 2026-09-21     |         116.53  | OBJETIVO (gap)  |     15 |    255.09 |         2.23 |
| BAC      | Financieras         | 2026-09-16      |           59.27  |        56.708  |    64.3939 |    44.6931 | 2026-09-22     |          56.708 | STOP            |      4 |   -122.28 |        -1.07 |
| CAT      | Energía / Industria | 2026-09-03      |          796.9   |       739.604  |   911.492  |     2.0034 | 2026-09-24     |         796.105 | FIN PERÍODO     |     13 |     -6.38 |        -0.06 |
| LLY      | Salud               | 2026-09-10      |         1126.08  |      1057.46   |  1263.32   |     1.6901 | 2026-09-24     |        1192.2   | FIN PERÍODO     |      9 |    105.88 |         0.91 |
| AMZN     | Tecnología          | 2026-09-18      |          252.92  |       240.572  |   277.617  |     9.3371 | 2026-09-24     |         246.53  | FIN PERÍODO     |      4 |    -66.66 |        -0.58 |
| BAC      | Financieras         | 2026-09-22      |           58.1   |        55.5847 |    63.1306 |    46.1474 | 2026-09-24     |          55.935 | FIN PERÍODO     |      2 |   -107.8  |        -0.93 |
| PYPL     | Tecnología          | 2026-09-23      |           52.79  |        49.4652 |    59.4396 |    34.3503 | 2026-09-24     |          52.24  | FIN PERÍODO     |      1 |    -24.3  |        -0.21 |