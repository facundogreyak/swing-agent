# Momentum (m4-ampliado-top5-mensual-tope25) – booms del momento

Período: 2017-10-06 → 2026-09-28 · 183 acciones · Parámetros: puntaje=mix, top_n=5, rebalanceo_dias=21, buffer=5, max_por_sector=3, filtro_mercado=False

## Resultado

| Métrica | Valor |
|---|---|
| retorno_anual (CAGR) | 44.2% |
| max_drawdown | -51.7% |
| retorno/caida (MAR) | 0.85 |
| retorno_total | 2568.4% |
| compras_por_anio | 20.94 |
| aciertos | 58.0% |
| retorno_prom_por_posicion | 31.2% |
| dias_prom_en_posicion | 63.17 |
| rotacion_anual | 7.59 |
| pct_en_acciones | 99.3% |
| pct_en_spy | 0.6% |
| spy_retorno_anual | 14.8% |
| spy_max_drawdown | -33.7% |

**Referencia:** las mismas 183 acciones en partes iguales rindieron 19.9% anual (caída máx. -35.3%). La diferencia contra SPY es en gran parte por haber elegido la lista hoy; la ventaja real de la estrategia se mide contra esta referencia.

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
| 2026 | 114.3% | 18.8% | 13.1% |

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
| base | 50 | 27.3% | -39.9% | 24.5% | 32.5% | 21.7% |
| ampliado | 183 | 44.2% | -51.7% | 27.8% | 40.6% | 19.9% |

## Qué pesa más en el resultado

Retorno anual promedio de todas las combinaciones que usan cada valor. 'Dentro' = hasta 2023-01-01 · 'Fuera' = desde 2023-01-01. Un parámetro es confiable si el mejor valor coincide dentro y fuera.

**puntaje** — impacto fuera de muestra: 19.0% (mejor dentro: r126, mejor fuera: r252)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| mix | 30.2% | 42.5% | -38.4% |
| r126 | 53.1% | 59.4% | -36.9% |
| r252 | 36.7% | 61.4% | -36.5% |

**top_n** — impacto fuera de muestra: 12.1% (mejor dentro: 5, mejor fuera: 5)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 10 | 34.2% | 48.8% | -35.9% |
| 5 | 46.2% | 60.9% | -39.1% |
| 8 | 39.5% | 53.6% | -36.9% |

**max_por_sector** — impacto fuera de muestra: 6.0% (mejor dentro: no, mejor fuera: 3)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 3 | 38.7% | 57.4% | -36.5% |
| no | 41.3% | 51.4% | -38.0% |

**rebalanceo_dias** — impacto fuera de muestra: 3.0% (mejor dentro: 21, mejor fuera: 5)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 21 | 41.1% | 52.9% | -37.7% |
| 5 | 38.9% | 55.9% | -36.9% |

**buffer** — impacto fuera de muestra: 1.1% (mejor dentro: 10, mejor fuera: 5)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 10 | 41.1% | 53.9% | -36.6% |
| 5 | 38.8% | 55.0% | -38.0% |

## Top 10 combinaciones (elegidas con datos dentro de muestra)

| puntaje   |   top_n |   rebalanceo_dias |   buffer | max_por_sector   | in_retorno_anual (CAGR)   | in_max_drawdown   | out_retorno_anual (CAGR)   | out_max_drawdown   | out_spy_retorno_anual   |   out_compras_por_anio |
|:----------|--------:|------------------:|---------:|:-----------------|:--------------------------|:------------------|:---------------------------|:-------------------|:------------------------|-----------------------:|
| r126      |       5 |                21 |       10 | no               | 73.4%                     | -38.4%            | 75.6%                      | -37.3%             | 22.1%                   |                  18.48 |
| r126      |       5 |                21 |       10 | 3                | 71.9%                     | -41.3%            | 81.9%                      | -36.5%             | 22.1%                   |                  19.82 |
| r126      |       8 |                21 |       10 | no               | 65.2%                     | -37.5%            | 50.4%                      | -35.1%             | 22.1%                   |                  28.65 |
| r126      |       5 |                 5 |       10 | no               | 67.0%                     | -40.0%            | 57.7%                      | -38.5%             | 22.1%                   |                  23.03 |
| r126      |       8 |                21 |       10 | 3                | 60.2%                     | -38.3%            | 50.7%                      | -33.1%             | 22.1%                   |                  30.79 |
| r126      |       5 |                21 |        5 | no               | 63.9%                     | -41.8%            | 75.0%                      | -39.3%             | 22.1%                   |                  21.15 |
| r126      |       5 |                 5 |       10 | 3                | 61.6%                     | -40.4%            | 65.7%                      | -38.5%             | 22.1%                   |                  25.17 |
| r126      |       5 |                 5 |        5 | no               | 59.1%                     | -40.7%            | 62.0%                      | -42.0%             | 22.1%                   |                  28.92 |
| r126      |       5 |                21 |        5 | 3                | 66.2%                     | -45.9%            | 82.5%                      | -39.3%             | 22.1%                   |                  22.76 |
| r126      |       5 |                 5 |        5 | 3                | 56.8%                     | -39.9%            | 72.4%                      | -38.3%             | 22.1%                   |                  31.87 |

Correlación de ranking dentro vs fuera: **0.51**