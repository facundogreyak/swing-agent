# Momentum (m2-mix-top5-mensual) – booms del momento

Período: 2017-10-06 → 2026-09-24 · 50 acciones · Parámetros: puntaje=mix, top_n=5, rebalanceo_dias=21, buffer=5, max_por_sector=3, filtro_mercado=False

## Resultado

| Métrica | Valor |
|---|---|
| retorno_anual (CAGR) | 34.3% |
| max_drawdown | -37.2% |
| retorno/caida (MAR) | 0.92 |
| retorno_total | 1302.8% |
| compras_por_anio | 14.16 |
| aciertos | 54.1% |
| retorno_prom_por_posicion | 14.1% |
| dias_prom_en_posicion | 93.14 |
| rotacion_anual | 5.02 |
| pct_en_acciones | 98.6% |
| pct_en_spy | 1.3% |
| spy_retorno_anual | 14.8% |
| spy_max_drawdown | -33.7% |

**Referencia:** las mismas 50 acciones en partes iguales rindieron 21.9% anual (caída máx. -34.3%). La diferencia contra SPY es en gran parte por haber elegido la lista hoy; la ventaja real de la estrategia se mide contra esta referencia.

## Retorno por año

| Año | Momentum | 50 en partes iguales | SPY |
|---|---|---|---|
| 2017 | 6.4% | 7.3% | 5.4% |
| 2018 | 2.2% | 7.4% | -4.6% |
| 2019 | 26.9% | 35.9% | 31.2% |
| 2020 | 132.5% | 37.4% | 18.3% |
| 2021 | 6.4% | 27.2% | 28.7% |
| 2022 | 10.9% | -19.1% | -18.2% |
| 2023 | 53.8% | 50.8% | 26.2% |
| 2024 | 58.8% | 29.2% | 24.9% |
| 2025 | -4.9% | 20.3% | 17.7% |
| 2026 | 59.6% | 14.1% | 13.3% |

## Qué acciones aportaron (posiciones cerradas)

| Ticker | Veces | Retorno promedio |
|---|---|---|
| AAPL | 1.0 | 87.4% |
| NVDA | 5.0 | 82.2% |
| TSLA | 6.0 | 69.1% |
| VIST | 4.0 | 49.9% |
| BA | 1.0 | 35.9% |
| XOM | 2.0 | 32.0% |
| MSTR | 6.0 | 26.8% |
| META | 2.0 | 22.6% |
| CVX | 1.0 | 22.1% |
| GLOB | 5.0 | 21.0% |

## Qué pesa más en el resultado

Retorno anual promedio de todas las combinaciones que usan cada valor. 'Dentro' = hasta 2023-01-01 · 'Fuera' = desde 2023-01-01. Un parámetro es confiable si el mejor valor coincide dentro y fuera.

**puntaje** — impacto fuera de muestra: 16.2% (mejor dentro: r126, mejor fuera: r252)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| mix | 26.9% | 37.0% | -33.1% |
| r126 | 30.9% | 36.5% | -36.6% |
| r252 | 30.2% | 52.8% | -36.0% |

**top_n** — impacto fuera de muestra: 6.6% (mejor dentro: 5, mejor fuera: 5)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 10 | 24.8% | 39.2% | -32.3% |
| 5 | 34.9% | 45.9% | -38.9% |
| 8 | 28.3% | 41.2% | -34.5% |

**buffer** — impacto fuera de muestra: 2.1% (mejor dentro: 5, mejor fuera: 10)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 10 | 28.7% | 43.1% | -35.2% |
| 5 | 30.0% | 41.1% | -35.2% |

**max_por_sector** — impacto fuera de muestra: 1.8% (mejor dentro: no, mejor fuera: no)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 3 | 27.3% | 41.2% | -35.3% |
| no | 31.4% | 43.0% | -35.2% |

**rebalanceo_dias** — impacto fuera de muestra: 1.3% (mejor dentro: 21, mejor fuera: 5)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 21 | 29.8% | 41.5% | -35.9% |
| 5 | 28.9% | 42.8% | -34.5% |

## Top 10 combinaciones (elegidas con datos dentro de muestra)

| puntaje   |   top_n |   rebalanceo_dias |   buffer | max_por_sector   | in_retorno_anual (CAGR)   | in_max_drawdown   | out_retorno_anual (CAGR)   | out_max_drawdown   | out_spy_retorno_anual   |   out_compras_por_anio |
|:----------|--------:|------------------:|---------:|:-----------------|:--------------------------|:------------------|:---------------------------|:-------------------|:------------------------|-----------------------:|
| r126      |       5 |                 5 |        5 | no               | 48.0%                     | -40.6%            | 37.9%                      | -40.0%             | 22.2%                   |                  25.25 |
| mix       |       5 |                21 |       10 | no               | 37.5%                     | -32.5%            | 38.4%                      | -34.8%             | 22.2%                   |                  10.74 |
| r126      |       5 |                21 |        5 | no               | 46.6%                     | -40.5%            | 34.5%                      | -42.3%             | 22.2%                   |                  17.99 |
| r252      |       5 |                21 |        5 | 3                | 37.7%                     | -35.5%            | 62.0%                      | -37.2%             | 22.2%                   |                   9.4  |
| r126      |       5 |                21 |        5 | 3                | 42.1%                     | -39.7%            | 33.7%                      | -42.3%             | 22.2%                   |                  18.26 |
| r126      |       5 |                 5 |       10 | no               | 40.9%                     | -40.0%            | 41.3%                      | -44.2%             | 22.2%                   |                  17.46 |
| r252      |       5 |                 5 |        5 | 3                | 36.7%                     | -36.2%            | 62.0%                      | -35.6%             | 22.2%                   |                  12.62 |
| r252      |       5 |                21 |       10 | no               | 36.0%                     | -35.5%            | 61.4%                      | -47.0%             | 22.2%                   |                   6.45 |
| r252      |       5 |                21 |        5 | no               | 36.9%                     | -37.5%            | 59.2%                      | -33.7%             | 22.2%                   |                   8.59 |
| r252      |       8 |                 5 |       10 | no               | 33.4%                     | -34.0%            | 45.7%                      | -34.7%             | 22.2%                   |                  11.28 |

Correlación de ranking dentro vs fuera: **0.17**