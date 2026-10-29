# Backtest – v4.1-retroceso-4R

Período: 2017-07-13 → 2026-10-27 · Tickers con datos: 50 de 50 · Capital inicial: USD 10,000

## Configuración actual

| Métrica | Valor |
|---|---|
| operaciones | 626 |
| win_rate | 45.4% |
| r_promedio (expectancy) | 0.18 |
| ganancia_prom_R | 1.57 |
| perdida_prom_R | -0.98 |
| profit_factor | 1.35 |
| dias_prom_en_posicion | 14.17 |
| retorno_total | 158.2% |
| retorno_anual (CAGR) | 10.7% |
| max_drawdown | -23.1% |
| retorno/caida (MAR) | 0.47 |
| exposicion_prom | 69.6% |
| spy_retorno_anual | 14.9% |
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
| 2026 | 11.5% | 13.7% |

## Variantes de riesgo por operación

| Variante | operaciones | win_rate | r_promedio (expectancy) | retorno_anual (CAGR) | max_drawdown | exposicion_prom |
|---|---|---|---|---|---|---|
| efectivo en SPY: sí | 626 | 45.4% | 0.18 | 9.3% | -40.8% | 69.6% |
| riesgo 0.5% | 628 | 45.4% | 0.18 | 6.0% | -12.5% | 40.2% |
| riesgo 1.0% | 626 | 45.4% | 0.18 | 10.7% | -23.1% | 69.6% |
| riesgo 2.0% | 609 | 44.0% | 0.19 | 12.1% | -30.1% | 78.4% |

## Resultado por motivo de salida

| Motivo | Operaciones | R promedio |
|---|---|---|
| FIN PERÍODO | 5 | 0.59 |
| OBJETIVO | 15 | 3.93 |
| OBJETIVO (gap) | 7 | 4.68 |
| STOP | 210 | -1.07 |
| STOP (gap) | 68 | -1.33 |
| TIEMPO | 321 | 1.03 |

## Resultado por sector

| Sector | Operaciones | Win rate | R promedio | PnL USD |
|---|---|---|---|---|
| China | 12 | 42% | 0.38 | 955 |
| Consumo | 131 | 38% | 0.04 | -1,007 |
| Energía / Industria | 61 | 43% | 0.11 | 1,578 |
| Financieras | 85 | 47% | 0.14 | 1,747 |
| Latam / Brasil | 85 | 45% | 0.21 | 2,096 |
| Salud | 69 | 54% | 0.27 | 2,373 |
| Tecnología | 183 | 48% | 0.26 | 8,043 |

## Últimas 10 operaciones

| ticker   | sector         | fecha_entrada   |   precio_entrada |   stop_inicial |   objetivo |   cantidad | fecha_salida   |   precio_salida | motivo_salida   |   dias |   pnl_usd |   r_multiple |
|:---------|:---------------|:----------------|-----------------:|---------------:|-----------:|-----------:|:---------------|----------------:|:----------------|-------:|----------:|-------------:|
| LLY      | Salud          | 2026-09-10      |         1126.08  |      1057.46   |  1400.56   |     3.5659 | 2026-10-08     |        1169.6   | TIEMPO          |     20 |    142.91 |         0.58 |
| PYPL     | Tecnología     | 2026-09-11      |           53.31  |        49.3384 |    69.1964 |    61.6487 | 2026-10-09     |          55.53  | TIEMPO          |     20 |    126.8  |         0.52 |
| GOOGL    | Tecnología     | 2026-09-14      |          343.12  |       326.819  |   408.324  |    15.0024 | 2026-10-12     |         352.72  | TIEMPO          |     20 |    128.36 |         0.52 |
| JNJ      | Salud          | 2026-10-08      |          256.22  |       246.116  |   296.637  |    16.229  | 2026-10-13     |         246.116 | STOP            |      3 |   -176.21 |        -1.07 |
| V        | Financieras    | 2026-10-02      |          360.21  |       348.572  |   406.76   |    15.5379 | 2026-10-20     |         406.76  | OBJETIVO        |     12 |    705.41 |         3.9  |
| JPM      | Financieras    | 2026-10-02      |          332.342 |       319.141  |   385.145  |    18.152  | 2026-10-27     |         335.79  | FIN PERÍODO     |     17 |     44.4  |         0.19 |
| VIST     | Latam / Brasil | 2026-10-09      |           66.82  |        61.6894 |    87.3422 |    48.67   | 2026-10-27     |          71.53  | FIN PERÍODO     |     12 |    219.14 |         0.88 |
| JNJ      | Salud          | 2026-10-15      |          257.11  |       244.952  |   305.74   |    20.6798 | 2026-10-27     |         268.73  | FIN PERÍODO     |      8 |    223.99 |         0.89 |
| INTC     | Tecnología     | 2026-10-20      |           90.73  |        79.0802 |   137.329  |    21.7232 | 2026-10-27     |          93.74  | FIN PERÍODO     |      5 |     59.38 |         0.23 |
| TSM      | Tecnología     | 2026-10-20      |          416.29  |       391.409  |   515.813  |    10.1713 | 2026-10-27     |         436.87  | FIN PERÍODO     |      5 |    196.31 |         0.78 |