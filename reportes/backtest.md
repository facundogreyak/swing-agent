# Backtest – v3-3R-20dias

Período: 2017-07-13 → 2026-09-24 · Tickers con datos: 50 de 50 · Capital inicial: USD 10,000

## Configuración actual

| Métrica | Valor |
|---|---|
| operaciones | 558 |
| win_rate | 44.1% |
| r_promedio (expectancy) | 0.15 |
| ganancia_prom_R | 1.57 |
| perdida_prom_R | -0.97 |
| profit_factor | 1.24 |
| dias_prom_en_posicion | 13.42 |
| retorno_total | 93.6% |
| retorno_anual (CAGR) | 7.4% |
| max_drawdown | -21.7% |
| retorno/caida (MAR) | 0.34 |
| exposicion_prom | 60.1% |
| spy_retorno_anual | 15.0% |
| spy_max_drawdown | -33.7% |

## Retorno por año

| Año | Agente | SPY |
|---|---|---|
| 2017 | 12.9% | 10.3% |
| 2018 | -11.5% | -4.6% |
| 2019 | 18.5% | 31.2% |
| 2020 | 6.4% | 18.3% |
| 2021 | 5.5% | 28.7% |
| 2022 | 2.9% | -18.2% |
| 2023 | 7.3% | 26.2% |
| 2024 | 22.5% | 24.9% |
| 2025 | 10.0% | 17.7% |
| 2026 | -2.1% | 12.8% |

## Variantes de riesgo por operación

| Variante | operaciones | win_rate | r_promedio (expectancy) | retorno_anual (CAGR) | max_drawdown | exposicion_prom |
|---|---|---|---|---|---|---|
| riesgo 0.5% | 558 | 44.3% | 0.15 | 4.5% | -12.3% | 35.2% |
| riesgo 1.0% | 558 | 44.1% | 0.15 | 7.4% | -21.7% | 60.1% |
| riesgo 2.0% | 546 | 42.3% | 0.14 | 8.8% | -24.0% | 66.8% |

## Resultado por motivo de salida

| Motivo | Operaciones | R promedio |
|---|---|---|
| FIN PERÍODO | 4 | 0.03 |
| OBJETIVO | 43 | 2.93 |
| OBJETIVO (gap) | 9 | 3.88 |
| STOP | 194 | -1.07 |
| STOP (gap) | 58 | -1.35 |
| TIEMPO | 250 | 0.83 |

## Resultado por sector

| Sector | Operaciones | Win rate | R promedio | PnL USD |
|---|---|---|---|---|
| China | 10 | 30% | 0.23 | 538 |
| Consumo | 120 | 42% | 0.08 | -582 |
| Energía / Industria | 54 | 37% | -0.06 | -6 |
| Financieras | 73 | 48% | 0.12 | 1,399 |
| Latam / Brasil | 81 | 41% | 0.13 | 678 |
| Salud | 54 | 48% | 0.12 | 823 |
| Tecnología | 166 | 48% | 0.29 | 6,495 |

## Últimas 10 operaciones

| ticker   | sector              | fecha_entrada   |   precio_entrada |   stop_inicial |   objetivo |   cantidad | fecha_salida   |   precio_salida | motivo_salida   |   dias |   pnl_usd |   r_multiple |
|:---------|:--------------------|:----------------|-----------------:|---------------:|-----------:|-----------:|:---------------|----------------:|:----------------|-------:|----------:|-------------:|
| GOOGL    | Tecnología          | 2026-07-28      |          327.689 |       304.194  |   398.176  |     8.4553 | 2026-08-25     |        346.737  | TIEMPO          |     20 |    152.5  |         0.77 |
| CAT      | Energía / Industria | 2026-07-31      |          843.39  |       759.87   |  1093.95   |     2.4121 | 2026-08-28     |        800.25   | TIEMPO          |     20 |   -110    |        -0.55 |
| NVDA     | Tecnología          | 2026-08-03      |          197.469 |       182.538  |   242.261  |    13.416  | 2026-08-31     |        220.533  | TIEMPO          |     20 |    301.02 |         1.5  |
| AVGO     | Tecnología          | 2026-08-28      |          372.921 |       344.64   |   457.764  |     6.9752 | 2026-09-03     |        344.64   | STOP            |      4 |   -204.77 |        -1.04 |
| PYPL     | Tecnología          | 2026-09-03      |           54.675 |        50.8167 |    66.2498 |    51.1069 | 2026-09-10     |         50.8167 | STOP            |      4 |   -205.27 |        -1.04 |
| C        | Financieras         | 2026-08-24      |          131.39  |       124.884  |   150.908  |    30.1377 | 2026-09-23     |        131.93   | TIEMPO          |     20 |      4.37 |         0.02 |
| CAT      | Energía / Industria | 2026-09-03      |          796.9   |       739.604  |   968.788  |     3.4415 | 2026-09-24     |        795.23   | FIN PERÍODO     |     13 |    -13.97 |        -0.07 |
| LLY      | Salud               | 2026-09-10      |         1126.08  |      1057.46   |  1331.94   |     2.8487 | 2026-09-24     |       1192.98   | FIN PERÍODO     |      9 |    180.67 |         0.92 |
| PYPL     | Tecnología          | 2026-09-11      |           53.31  |        49.3384 |    65.2248 |    49.2743 | 2026-09-24     |         52.2    | FIN PERÍODO     |      9 |    -62.49 |        -0.32 |
| GOOGL    | Tecnología          | 2026-09-14      |          343.12  |       326.819  |   392.023  |    11.9423 | 2026-09-24     |        337.52   | FIN PERÍODO     |      8 |    -79.07 |        -0.41 |