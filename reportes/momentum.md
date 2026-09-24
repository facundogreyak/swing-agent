# Momentum (m1-mix-top8) – booms del momento

Período: 2017-10-06 → 2026-09-24 · 50 acciones · Parámetros: puntaje=mix, top_n=8, rebalanceo_dias=21, buffer=5, max_por_sector=3, filtro_mercado=False

## Resultado

| Métrica | Valor |
|---|---|
| retorno_anual (CAGR) | 27.7% |
| max_drawdown | -30.7% |
| retorno/caida (MAR) | 0.90 |
| retorno_total | 794.3% |
| compras_por_anio | 23.53 |
| aciertos | 54.7% |
| retorno_prom_por_posicion | 11.3% |
| dias_prom_en_posicion | 90.36 |
| rotacion_anual | 5.11 |
| pct_en_acciones | 99.1% |
| pct_en_spy | 0.8% |
| spy_retorno_anual | 14.8% |
| spy_max_drawdown | -33.7% |

## Retorno por año

| Año | Momentum | SPY |
|---|---|---|
| 2017 | 7.6% | 5.4% |
| 2018 | -8.1% | -4.6% |
| 2019 | 23.9% | 31.2% |
| 2020 | 93.7% | 18.3% |
| 2021 | 17.7% | 28.7% |
| 2022 | 25.4% | -18.2% |
| 2023 | 42.5% | 26.2% |
| 2024 | 34.8% | 24.9% |
| 2025 | 2.8% | 17.7% |
| 2026 | 29.3% | 12.8% |

## Qué acciones aportaron (posiciones cerradas)

| Ticker | Veces | Retorno promedio |
|---|---|---|
| NVDA | 5.0 | 121.2% |
| AAPL | 1.0 | 112.5% |
| META | 1.0 | 55.9% |
| VIST | 5.0 | 53.8% |
| MSTR | 6.0 | 52.2% |
| MSFT | 1.0 | 50.5% |
| PG | 1.0 | 37.2% |
| COIN | 3.0 | 23.4% |
| ADBE | 2.0 | 21.7% |
| MELI | 9.0 | 20.3% |

## Qué pesa más en el resultado

Retorno anual promedio de todas las combinaciones que usan cada valor. 'Dentro' = hasta 2023-01-01 · 'Fuera' = desde 2023-01-01. Un parámetro es confiable si el mejor valor coincide dentro y fuera.

**puntaje** — impacto fuera de muestra: 29.5% (mejor dentro: r126, mejor fuera: r252)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| mix | 21.5% | 29.0% | -31.7% |
| r126 | 25.1% | 27.9% | -35.6% |
| r21 | 19.3% | 37.7% | -24.3% |
| r252 | 21.9% | 48.5% | -35.0% |
| r63 | 23.3% | 19.0% | -34.4% |

**filtro_mercado** — impacto fuera de muestra: 8.4% (mejor dentro: no, mejor fuera: no)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| no | 27.3% | 36.6% | -34.3% |
| sí | 17.1% | 28.2% | -30.0% |

**top_n** — impacto fuera de muestra: 5.0% (mejor dentro: 5, mejor fuera: 5)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 10 | 18.7% | 29.9% | -28.1% |
| 5 | 25.8% | 34.9% | -36.3% |

**buffer** — impacto fuera de muestra: 2.3% (mejor dentro: 5, mejor fuera: 5)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 0 | 21.9% | 31.2% | -32.3% |
| 5 | 22.5% | 33.6% | -32.1% |

**rebalanceo_dias** — impacto fuera de muestra: 2.0% (mejor dentro: 5, mejor fuera: 5)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 21 | 21.1% | 31.4% | -34.4% |
| 5 | 23.3% | 33.4% | -30.0% |

**max_por_sector** — impacto fuera de muestra: 0.8% (mejor dentro: no, mejor fuera: no)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 3 | 21.4% | 32.0% | -32.1% |
| no | 23.0% | 32.8% | -32.3% |

## Top 10 combinaciones (elegidas con datos dentro de muestra)

| puntaje   |   top_n |   rebalanceo_dias |   buffer | max_por_sector   | filtro_mercado   | in_retorno_anual (CAGR)   | in_max_drawdown   | out_retorno_anual (CAGR)   | out_max_drawdown   | out_spy_retorno_anual   |   out_compras_por_anio |
|:----------|--------:|------------------:|---------:|:-----------------|:-----------------|:--------------------------|:------------------|:---------------------------|:-------------------|:------------------------|-----------------------:|
| r126      |       5 |                 5 |        5 | no               | no               | 48.0%                     | -40.6%            | 37.6%                      | -40.0%             | 22.1%                   |                  25.25 |
| r126      |       5 |                21 |        5 | no               | no               | 46.6%                     | -40.5%            | 34.1%                      | -42.3%             | 22.1%                   |                  17.99 |
| r126      |       5 |                21 |        0 | no               | no               | 44.8%                     | -39.4%            | 35.0%                      | -41.6%             | 22.1%                   |                  27.39 |
| r126      |       5 |                21 |        0 | 3                | no               | 43.8%                     | -38.7%            | 39.1%                      | -43.4%             | 22.1%                   |                  26.32 |
| r252      |       5 |                21 |        5 | 3                | no               | 37.7%                     | -35.5%            | 61.7%                      | -37.2%             | 22.1%                   |                   9.4  |
| r126      |       5 |                21 |        5 | 3                | no               | 42.1%                     | -39.7%            | 33.3%                      | -42.3%             | 22.1%                   |                  18.26 |
| r252      |       5 |                 5 |        5 | 3                | no               | 36.7%                     | -36.2%            | 61.5%                      | -35.6%             | 22.1%                   |                  12.62 |
| r252      |       5 |                21 |        5 | no               | no               | 36.9%                     | -37.5%            | 58.8%                      | -33.7%             | 22.1%                   |                   8.59 |
| r63       |      10 |                 5 |        0 | no               | sí               | 24.0%                     | -24.7%            | 18.4%                      | -22.7%             | 22.1%                   |                 110.65 |
| r252      |       5 |                 5 |        5 | no               | no               | 36.0%                     | -37.7%            | 62.1%                      | -35.6%             | 22.1%                   |                  12.62 |

Correlación de ranking dentro vs fuera: **0.05**