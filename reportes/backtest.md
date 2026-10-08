# Backtest – v4.1-retroceso-4R

Período: 2017-07-13 → 2026-10-06 · Tickers con datos: 50 de 50 · Capital inicial: USD 10,000

## Configuración actual

| Métrica | Valor |
|---|---|
| operaciones | 621 |
| win_rate | 44.9% |
| r_promedio (expectancy) | 0.17 |
| ganancia_prom_R | 1.57 |
| perdida_prom_R | -0.97 |
| profit_factor | 1.32 |
| dias_prom_en_posicion | 14.17 |
| retorno_total | 144.8% |
| retorno_anual (CAGR) | 10.2% |
| max_drawdown | -23.1% |
| retorno/caida (MAR) | 0.44 |
| exposicion_prom | 69.5% |
| spy_retorno_anual | 15.1% |
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
| 2026 | 5.7% | 15.1% |

## Variantes de riesgo por operación

| Variante | operaciones | win_rate | r_promedio (expectancy) | retorno_anual (CAGR) | max_drawdown | exposicion_prom |
|---|---|---|---|---|---|---|
| efectivo en SPY: sí | 621 | 44.9% | 0.17 | 8.8% | -40.8% | 69.5% |
| riesgo 0.5% | 623 | 44.9% | 0.17 | 5.7% | -12.5% | 40.1% |
| riesgo 1.0% | 621 | 44.9% | 0.17 | 10.2% | -23.1% | 69.5% |
| riesgo 2.0% | 604 | 43.5% | 0.18 | 11.7% | -30.1% | 78.4% |

## Resultado por motivo de salida

| Motivo | Operaciones | R promedio |
|---|---|---|
| FIN PERÍODO | 5 | 0.31 |
| OBJETIVO | 14 | 3.93 |
| OBJETIVO (gap) | 7 | 4.68 |
| STOP | 209 | -1.07 |
| STOP (gap) | 68 | -1.33 |
| TIEMPO | 318 | 1.04 |

## Resultado por sector

| Sector | Operaciones | Win rate | R promedio | PnL USD |
|---|---|---|---|---|
| China | 12 | 42% | 0.38 | 955 |
| Consumo | 131 | 38% | 0.04 | -1,007 |
| Energía / Industria | 61 | 43% | 0.11 | 1,578 |
| Financieras | 85 | 46% | 0.10 | 1,105 |
| Latam / Brasil | 84 | 44% | 0.20 | 1,877 |
| Salud | 67 | 54% | 0.28 | 2,282 |
| Tecnología | 181 | 48% | 0.25 | 7,656 |

## Últimas 10 operaciones

| ticker   | sector              | fecha_entrada   |   precio_entrada |   stop_inicial |   objetivo |   cantidad | fecha_salida   |   precio_salida | motivo_salida   |   dias |   pnl_usd |   r_multiple |
|:---------|:--------------------|:----------------|-----------------:|---------------:|-----------:|-----------:|:---------------|----------------:|:----------------|-------:|----------:|-------------:|
| AVGO     | Tecnología          | 2026-08-28      |          372.921 |       344.64   |   486.045  |     8.8241 | 2026-09-03     |        344.64   | STOP            |      4 |   -259.05 |        -1.04 |
| PYPL     | Tecnología          | 2026-09-03      |           54.675 |        50.8167 |    70.1081 |    64.0085 | 2026-09-10     |         50.8167 | STOP            |      4 |   -257.09 |        -1.04 |
| BAC      | Financieras         | 2026-09-16      |           59.27  |        56.708  |    69.5179 |    95.065  | 2026-09-22     |         56.708  | STOP            |      4 |   -260.09 |        -1.07 |
| BAC      | Financieras         | 2026-09-25      |           56.31  |        53.8468 |    66.1626 |    99.8109 | 2026-10-01     |         53.8468 | STOP            |      4 |   -262.34 |        -1.07 |
| CAT      | Energía / Industria | 2026-09-03      |          796.9   |       739.604  |  1026.08   |     4.3103 | 2026-10-02     |        845.42   | TIEMPO          |     20 |    198.52 |         0.8  |
| LLY      | Salud               | 2026-09-10      |         1126.08  |      1057.46   |  1400.56   |     3.5659 | 2026-10-06     |       1157.49   | FIN PERÍODO     |     18 |     99.79 |         0.41 |
| PYPL     | Tecnología          | 2026-09-11      |           53.31  |        49.3384 |    69.1964 |    61.6487 | 2026-10-06     |         54.61   | FIN PERÍODO     |     17 |     70.16 |         0.29 |
| GOOGL    | Tecnología          | 2026-09-14      |          343.12  |       326.819  |   408.324  |    15.0024 | 2026-10-06     |        347.68   | FIN PERÍODO     |     16 |     52.87 |         0.22 |
| JPM      | Financieras         | 2026-10-02      |          332.342 |       319.141  |   385.145  |    18.152  | 2026-10-06     |        331.28   | FIN PERÍODO     |      2 |    -37.35 |        -0.16 |
| V        | Financieras         | 2026-10-02      |          360.21  |       348.572  |   406.76   |    15.5379 | 2026-10-06     |        370.64   | FIN PERÍODO     |      2 |    145.03 |         0.8  |