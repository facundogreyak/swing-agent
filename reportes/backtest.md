# Backtest – v4.1-retroceso-4R

Período: 2017-07-13 → 2026-09-25 · Tickers con datos: 50 de 50 · Capital inicial: USD 10,000

## Configuración actual

| Métrica | Valor |
|---|---|
| operaciones | 619 |
| win_rate | 44.7% |
| r_promedio (expectancy) | 0.17 |
| ganancia_prom_R | 1.58 |
| perdida_prom_R | -0.97 |
| profit_factor | 1.32 |
| dias_prom_en_posicion | 14.16 |
| retorno_total | 144.1% |
| retorno_anual (CAGR) | 10.2% |
| max_drawdown | -23.1% |
| retorno/caida (MAR) | 0.44 |
| exposicion_prom | 69.5% |
| spy_retorno_anual | 15.0% |
| spy_max_drawdown | -33.7% |

## Retorno por año

| Año | Agente | SPY |
|---|---|---|
| 2017 | 13.7% | 10.3% |
| 2018 | -9.3% | -4.6% |
| 2019 | 15.5% | 31.2% |
| 2020 | 11.5% | 18.3% |
| 2021 | 0.1% | 28.7% |
| 2022 | 13.4% | -18.2% |
| 2023 | 7.6% | 26.2% |
| 2024 | 22.3% | 24.9% |
| 2025 | 16.8% | 17.7% |
| 2026 | 5.4% | 13.5% |

## Variantes de riesgo por operación

| Variante | operaciones | win_rate | r_promedio (expectancy) | retorno_anual (CAGR) | max_drawdown | exposicion_prom |
|---|---|---|---|---|---|---|
| efectivo en SPY: sí | 619 | 44.7% | 0.17 | 8.8% | -40.8% | 69.4% |
| riesgo 0.5% | 621 | 44.8% | 0.17 | 5.7% | -12.5% | 40.1% |
| riesgo 1.0% | 619 | 44.7% | 0.17 | 10.2% | -23.1% | 69.5% |
| riesgo 2.0% | 602 | 43.4% | 0.18 | 11.6% | -30.1% | 78.3% |

## Resultado por motivo de salida

| Motivo | Operaciones | R promedio |
|---|---|---|
| FIN PERÍODO | 5 | 0.17 |
| OBJETIVO | 14 | 3.93 |
| OBJETIVO (gap) | 7 | 4.68 |
| STOP | 208 | -1.07 |
| STOP (gap) | 68 | -1.33 |
| TIEMPO | 317 | 1.04 |

## Resultado por sector

| Sector | Operaciones | Win rate | R promedio | PnL USD |
|---|---|---|---|---|
| China | 12 | 42% | 0.38 | 955 |
| Consumo | 131 | 38% | 0.04 | -1,007 |
| Energía / Industria | 61 | 43% | 0.11 | 1,436 |
| Financieras | 83 | 46% | 0.10 | 1,220 |
| Latam / Brasil | 84 | 44% | 0.20 | 1,877 |
| Salud | 67 | 54% | 0.28 | 2,314 |
| Tecnología | 181 | 47% | 0.25 | 7,586 |

## Últimas 10 operaciones

| ticker   | sector              | fecha_entrada   |   precio_entrada |   stop_inicial |   objetivo |   cantidad | fecha_salida   |   precio_salida | motivo_salida   |   dias |   pnl_usd |   r_multiple |
|:---------|:--------------------|:----------------|-----------------:|---------------:|-----------:|-----------:|:---------------|----------------:|:----------------|-------:|----------:|-------------:|
| INTC     | Tecnología          | 2026-07-31      |           96.72  |        79.3473 |   166.211  |    14.744  | 2026-08-28     |         89.47   | TIEMPO          |     20 |   -111.01 |        -0.43 |
| C        | Financieras         | 2026-07-31      |          132.874 |       125.227  |   163.465  |    33.4926 | 2026-08-28     |        132.9    | TIEMPO          |     20 |    -12.5  |        -0.05 |
| AVGO     | Tecnología          | 2026-08-28      |          372.921 |       344.64   |   486.045  |     8.8241 | 2026-09-03     |        344.64   | STOP            |      4 |   -259.05 |        -1.04 |
| PYPL     | Tecnología          | 2026-09-03      |           54.675 |        50.8167 |    70.1081 |    64.0085 | 2026-09-10     |         50.8167 | STOP            |      4 |   -257.09 |        -1.04 |
| BAC      | Financieras         | 2026-09-16      |           59.27  |        56.708  |    69.5179 |    95.065  | 2026-09-22     |         56.708  | STOP            |      4 |   -260.09 |        -1.07 |
| CAT      | Energía / Industria | 2026-09-03      |          796.9   |       739.604  |  1026.08   |     4.3103 | 2026-09-25     |        812.315  | FIN PERÍODO     |     15 |     56.04 |         0.23 |
| LLY      | Salud               | 2026-09-10      |         1126.08  |      1057.46   |  1400.56   |     3.5659 | 2026-09-25     |       1166.44   | FIN PERÍODO     |     11 |    131.66 |         0.54 |
| PYPL     | Tecnología          | 2026-09-11      |           53.31  |        49.3384 |    69.1964 |    61.6487 | 2026-09-25     |         54.77   | FIN PERÍODO     |     10 |     80.01 |         0.33 |
| GOOGL    | Tecnología          | 2026-09-14      |          343.12  |       326.819  |   408.324  |    15.0024 | 2026-09-25     |        342.35   | FIN PERÍODO     |      9 |    -26.98 |        -0.11 |
| BAC      | Financieras         | 2026-09-25      |           56.31  |        53.8468 |    66.1626 |    99.2392 | 2026-09-25     |         56.0776 | FIN PERÍODO     |      0 |    -39.79 |        -0.16 |