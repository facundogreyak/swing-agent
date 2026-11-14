# Backtest – v4.1-retroceso-4R

Período: 2017-07-13 → 2026-11-13 · Tickers con datos: 50 de 50 · Capital inicial: USD 10,000

## Configuración actual

| Métrica | Valor |
|---|---|
| operaciones | 631 |
| win_rate | 45.2% |
| r_promedio (expectancy) | 0.17 |
| ganancia_prom_R | 1.58 |
| perdida_prom_R | -0.98 |
| profit_factor | 1.33 |
| dias_prom_en_posicion | 14.14 |
| retorno_total | 151.9% |
| retorno_anual (CAGR) | 10.4% |
| max_drawdown | -23.1% |
| retorno/caida (MAR) | 0.45 |
| exposicion_prom | 69.6% |
| spy_retorno_anual | 14.6% |
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
| 2026 | 8.8% | 11.5% |

## Variantes de riesgo por operación

| Variante | operaciones | win_rate | r_promedio (expectancy) | retorno_anual (CAGR) | max_drawdown | exposicion_prom |
|---|---|---|---|---|---|---|
| efectivo en SPY: sí | 631 | 45.2% | 0.17 | 8.7% | -40.8% | 69.6% |
| riesgo 0.5% | 633 | 45.2% | 0.18 | 5.8% | -12.5% | 40.1% |
| riesgo 1.0% | 631 | 45.2% | 0.17 | 10.4% | -23.1% | 69.6% |
| riesgo 2.0% | 614 | 43.8% | 0.18 | 11.5% | -30.1% | 78.5% |

## Resultado por motivo de salida

| Motivo | Operaciones | R promedio |
|---|---|---|
| FIN PERÍODO | 4 | 0.93 |
| OBJETIVO | 15 | 3.93 |
| OBJETIVO (gap) | 7 | 4.68 |
| STOP | 212 | -1.07 |
| STOP (gap) | 70 | -1.34 |
| TIEMPO | 323 | 1.04 |

## Resultado por sector

| Sector | Operaciones | Win rate | R promedio | PnL USD |
|---|---|---|---|---|
| China | 12 | 42% | 0.38 | 955 |
| Consumo | 131 | 38% | 0.04 | -1,007 |
| Energía / Industria | 63 | 44% | 0.13 | 1,903 |
| Financieras | 85 | 47% | 0.14 | 1,770 |
| Latam / Brasil | 86 | 43% | 0.17 | 1,363 |
| Salud | 69 | 54% | 0.29 | 2,678 |
| Tecnología | 185 | 48% | 0.24 | 7,500 |

## Últimas 10 operaciones

| ticker   | sector              | fecha_entrada   |   precio_entrada |   stop_inicial |   objetivo |   cantidad | fecha_salida   |   precio_salida | motivo_salida   |   dias |   pnl_usd |   r_multiple |
|:---------|:--------------------|:----------------|-----------------:|---------------:|-----------:|-----------:|:---------------|----------------:|:----------------|-------:|----------:|-------------:|
| JPM      | Financieras         | 2026-10-02      |          332.342 |       319.141  |   385.145  |    18.152  | 2026-10-30     |        337.04   | TIEMPO          |     20 |     67.05 |         0.28 |
| INTC     | Tecnología          | 2026-10-20      |           90.73  |        79.0802 |   137.329  |    21.7232 | 2026-10-30     |         68.36   | STOP (gap)      |      8 |   -491.13 |        -1.94 |
| PBR      | Latam / Brasil      | 2026-11-02      |           21.6   |        19.744  |    29.0239 |   133.09   | 2026-11-04     |         19.744  | STOP            |      2 |   -255.27 |        -1.03 |
| VIST     | Latam / Brasil      | 2026-10-09      |           66.82  |        61.6894 |    87.3422 |    48.67   | 2026-11-05     |         61.6894 | STOP            |     19 |   -259.09 |        -1.04 |
| TSM      | Tecnología          | 2026-10-20      |          416.29  |       391.409  |   515.813  |    10.1713 | 2026-11-05     |        379.75   | STOP (gap)      |     12 |   -383.8  |        -1.52 |
| JNJ      | Salud               | 2026-10-15      |          257.11  |       244.952  |   305.74   |    20.6798 | 2026-11-12     |        283.52   | TIEMPO          |     20 |    529.38 |         2.11 |
| AMZN     | Tecnología          | 2026-11-03      |          248.59  |       233.192  |   310.181  |    16.0088 | 2026-11-13     |        266.66   | FIN PERÍODO     |      8 |    276.91 |         1.12 |
| AMD      | Tecnología          | 2026-11-05      |          452.5   |       390.1    |   702.098  |     3.8793 | 2026-11-13     |        534.06   | FIN PERÍODO     |      6 |    310.65 |         1.28 |
| XOM      | Energía / Industria | 2026-11-09      |          163.82  |       154.34   |   201.739  |    26.089  | 2026-11-13     |        170.59   | FIN PERÍODO     |      4 |    163.54 |         0.66 |
| CVX      | Energía / Industria | 2026-11-11      |          212.32  |       201.613  |   255.147  |    23.2803 | 2026-11-13     |        219.89   | FIN PERÍODO     |      2 |    161.14 |         0.65 |