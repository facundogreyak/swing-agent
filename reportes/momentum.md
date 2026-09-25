# Momentum (m4-ampliado-top5-mensual-tope25) – booms del momento

Período: 2017-10-06 → 2026-09-25 · 183 acciones · Parámetros: puntaje=mix, top_n=5, rebalanceo_dias=21, buffer=5, max_por_sector=3, filtro_mercado=False

## Resultado

| Métrica | Valor |
|---|---|
| retorno_anual (CAGR) | 44.1% |
| max_drawdown | -51.7% |
| retorno/caida (MAR) | 0.85 |
| retorno_total | 2545.6% |
| compras_por_anio | 20.96 |
| aciertos | 58.0% |
| retorno_prom_por_posicion | 31.2% |
| dias_prom_en_posicion | 63.17 |
| rotacion_anual | 7.61 |
| pct_en_acciones | 99.4% |
| pct_en_spy | 0.6% |
| spy_retorno_anual | 14.9% |
| spy_max_drawdown | -33.7% |

**Referencia:** las mismas 183 acciones en partes iguales rindieron 20.1% anual (caída máx. -35.3%). La diferencia contra SPY es en gran parte por haber elegido la lista hoy; la ventaja real de la estrategia se mide contra esta referencia.

## Retorno por año

| Año | Momentum | 50 en partes iguales | SPY |
|---|---|---|---|
| 2017 | 6.6% | 6.5% | 5.4% |
| 2018 | -14.3% | -4.0% | -4.6% |
| 2019 | 60.0% | 37.4% | 31.2% |
| 2020 | 248.2% | 39.0% | 18.3% |
| 2021 | -24.9% | 23.4% | 28.7% |
| 2022 | -5.6% | -15.1% | -18.2% |
| 2023 | 20.9% | 37.0% | 26.2% |
| 2024 | 71.3% | 20.5% | 24.9% |
| 2025 | 66.6% | 27.5% | 17.7% |
| 2026 | 112.5% | 19.8% | 13.8% |

## Qué acciones aportaron (posiciones cerradas)

| Ticker | Veces | Retorno promedio |
|---|---|---|
| TSLA | 3.0 | 259.7% |
| NIO | 3.0 | 226.1% |
| PLTR | 8.0 | 204.0% |
| ZM | 1.0 | 141.4% |
| MU | 7.0 | 133.4% |
| INTC | 1.0 | 81.6% |
| COIN | 1.0 | 80.9% |
| SE | 8.0 | 79.2% |
| MSTR | 5.0 | 64.4% |
| LRCX | 2.0 | 59.0% |

## Universo: 50 elegidas hoy vs. todas las que tienen CEDEAR

Misma configuración. 'Ampliado' = 183 acciones con CEDEAR en BYMA y liquidez suficiente. La columna 'partes iguales' muestra cuánto rinde cada lista sin estrategia.

| Universo | Acciones | Retorno anual | Caída máx. | Antes de 2023 | Desde 2023 | Partes iguales |
|---|---|---|---|---|---|---|
| base | 50 | 27.7% | -39.9% | 24.5% | 33.8% | 21.9% |
| ampliado | 183 | 44.1% | -51.7% | 27.8% | 40.9% | 20.1% |

## Qué pesa más en el resultado

Retorno anual promedio de todas las combinaciones que usan cada valor. 'Dentro' = hasta 2023-01-01 · 'Fuera' = desde 2023-01-01. Un parámetro es confiable si el mejor valor coincide dentro y fuera.

**puntaje** — impacto fuera de muestra: 19.9% (mejor dentro: r126, mejor fuera: r252)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| mix | 30.2% | 42.6% | -38.4% |
| r126 | 53.1% | 60.7% | -36.9% |
| r252 | 36.7% | 62.5% | -36.5% |

**top_n** — impacto fuera de muestra: 12.4% (mejor dentro: 5, mejor fuera: 5)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 10 | 34.2% | 49.4% | -35.9% |
| 5 | 46.2% | 61.9% | -39.1% |
| 8 | 39.5% | 54.4% | -36.9% |

**max_por_sector** — impacto fuera de muestra: 5.3% (mejor dentro: no, mejor fuera: 3)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 3 | 38.7% | 57.9% | -36.5% |
| no | 41.3% | 52.6% | -38.0% |

**rebalanceo_dias** — impacto fuera de muestra: 2.8% (mejor dentro: 21, mejor fuera: 5)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 21 | 41.1% | 53.9% | -37.7% |
| 5 | 38.9% | 56.6% | -36.9% |

**buffer** — impacto fuera de muestra: 1.1% (mejor dentro: 10, mejor fuera: 5)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 10 | 41.1% | 54.7% | -36.6% |
| 5 | 38.8% | 55.8% | -38.0% |

## Top 10 combinaciones (elegidas con datos dentro de muestra)

| puntaje   |   top_n |   rebalanceo_dias |   buffer | max_por_sector   | in_retorno_anual (CAGR)   | in_max_drawdown   | out_retorno_anual (CAGR)   | out_max_drawdown   | out_spy_retorno_anual   |   out_compras_por_anio |
|:----------|--------:|------------------:|---------:|:-----------------|:--------------------------|:------------------|:---------------------------|:-------------------|:------------------------|-----------------------:|
| r126      |       5 |                21 |       10 | no               | 73.4%                     | -38.4%            | 78.3%                      | -37.3%             | 22.3%                   |                  18.52 |
| r126      |       5 |                21 |       10 | 3                | 71.9%                     | -41.3%            | 82.9%                      | -36.5%             | 22.3%                   |                  19.86 |
| r126      |       8 |                21 |       10 | no               | 65.2%                     | -37.5%            | 52.0%                      | -35.1%             | 22.3%                   |                  28.72 |
| r126      |       5 |                 5 |       10 | no               | 67.0%                     | -40.0%            | 60.4%                      | -38.5%             | 22.3%                   |                  23.08 |
| r126      |       8 |                21 |       10 | 3                | 60.2%                     | -38.3%            | 51.4%                      | -33.1%             | 22.3%                   |                  30.86 |
| r126      |       5 |                21 |        5 | no               | 63.9%                     | -41.8%            | 77.2%                      | -39.3%             | 22.3%                   |                  21.2  |
| r126      |       5 |                 5 |       10 | 3                | 61.6%                     | -40.4%            | 67.0%                      | -38.5%             | 22.3%                   |                  24.96 |
| r126      |       5 |                 5 |        5 | no               | 59.1%                     | -40.7%            | 64.1%                      | -42.0%             | 22.3%                   |                  28.72 |
| r126      |       5 |                21 |        5 | 3                | 66.2%                     | -45.9%            | 83.8%                      | -39.3%             | 22.3%                   |                  22.81 |
| r126      |       5 |                 5 |        5 | 3                | 56.8%                     | -39.9%            | 73.4%                      | -38.3%             | 22.3%                   |                  31.94 |

Correlación de ranking dentro vs fuera: **0.54**