# Momentum (m3-mix-top5-mensual-tope25) – booms del momento

Período: 2017-10-06 → 2026-09-24 · 50 acciones · Parámetros: puntaje=mix, top_n=5, rebalanceo_dias=21, buffer=5, max_por_sector=3, filtro_mercado=False

## Resultado

| Métrica | Valor |
|---|---|
| retorno_anual (CAGR) | 27.8% |
| max_drawdown | -39.9% |
| retorno/caida (MAR) | 0.70 |
| retorno_total | 799.5% |
| compras_por_anio | 14.94 |
| aciertos | 59.7% |
| retorno_prom_por_posicion | 28.9% |
| dias_prom_en_posicion | 88.09 |
| rotacion_anual | 5.57 |
| pct_en_acciones | 98.2% |
| pct_en_spy | 1.8% |
| spy_retorno_anual | 14.9% |
| spy_max_drawdown | -33.7% |

**Referencia:** las mismas 50 acciones en partes iguales rindieron 21.9% anual (caída máx. -34.3%). La diferencia contra SPY es en gran parte por haber elegido la lista hoy; la ventaja real de la estrategia se mide contra esta referencia.

## Retorno por año

| Año | Momentum | 50 en partes iguales | SPY |
|---|---|---|---|
| 2017 | 6.4% | 7.3% | 5.4% |
| 2018 | 3.2% | 7.4% | -4.6% |
| 2019 | 20.7% | 35.9% | 31.2% |
| 2020 | 106.4% | 37.4% | 18.3% |
| 2021 | 10.4% | 27.2% | 28.7% |
| 2022 | 4.5% | -19.1% | -18.2% |
| 2023 | 26.7% | 50.8% | 26.2% |
| 2024 | 45.9% | 29.2% | 24.9% |
| 2025 | -2.6% | 20.3% | 17.7% |
| 2026 | 58.4% | 14.2% | 13.4% |

## Qué acciones aportaron (posiciones cerradas)

| Ticker | Veces | Retorno promedio |
|---|---|---|
| TSLA | 10.0 | 193.6% |
| INTC | 3.0 | 171.7% |
| AAPL | 1.0 | 87.4% |
| NVDA | 10.0 | 65.3% |
| MSTR | 8.0 | 59.6% |
| META | 1.0 | 55.9% |
| MSFT | 1.0 | 53.3% |
| XOM | 2.0 | 32.0% |
| NFLX | 6.0 | 25.0% |
| PG | 1.0 | 19.9% |

## Universo: 50 elegidas hoy vs. todas las que tienen CEDEAR

Misma configuración. 'Ampliado' = 183 acciones con CEDEAR en BYMA y liquidez suficiente. La columna 'partes iguales' muestra cuánto rinde cada lista sin estrategia.

| Universo | Acciones | Retorno anual | Caída máx. | Antes de 2023 | Desde 2023 | Partes iguales |
|---|---|---|---|---|---|---|
| base | 50 | 27.8% | -39.9% | 24.5% | 33.8% | 21.9% |
| ampliado | 183 | 44.1% | -51.7% | 27.8% | 40.6% | 20.1% |

## Qué pesa más en el resultado

Retorno anual promedio de todas las combinaciones que usan cada valor. 'Dentro' = hasta 2023-01-01 · 'Fuera' = desde 2023-01-01. Un parámetro es confiable si el mejor valor coincide dentro y fuera.

**puntaje** — impacto fuera de muestra: 19.8% (mejor dentro: r126, mejor fuera: r252)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| mix | 21.3% | 33.6% | -33.6% |
| r126 | 25.4% | 35.3% | -36.1% |
| r252 | 23.0% | 53.4% | -33.1% |

**top_n** — impacto fuera de muestra: 5.3% (mejor dentro: 5, mejor fuera: 5)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 10 | 20.1% | 38.3% | -31.3% |
| 5 | 27.5% | 43.6% | -37.6% |
| 8 | 22.2% | 40.5% | -33.9% |

**max_por_sector** — impacto fuera de muestra: 3.3% (mejor dentro: no, mejor fuera: no)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 3 | 21.6% | 39.1% | -34.1% |
| no | 24.9% | 42.4% | -34.4% |

**buffer** — impacto fuera de muestra: 1.3% (mejor dentro: 5, mejor fuera: 10)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 10 | 22.6% | 41.4% | -34.0% |
| 5 | 23.9% | 40.1% | -34.5% |

**rebalanceo_dias** — impacto fuera de muestra: 0.5% (mejor dentro: 21, mejor fuera: 5)

| Valor | CAGR dentro | CAGR fuera | Caída fuera |
|---|---|---|---|
| 21 | 23.6% | 40.5% | -34.3% |
| 5 | 22.9% | 41.0% | -34.2% |

## Top 10 combinaciones (elegidas con datos dentro de muestra)

| puntaje   |   top_n |   rebalanceo_dias |   buffer | max_por_sector   | in_retorno_anual (CAGR)   | in_max_drawdown   | out_retorno_anual (CAGR)   | out_max_drawdown   | out_spy_retorno_anual   |   out_compras_por_anio |
|:----------|--------:|------------------:|---------:|:-----------------|:--------------------------|:------------------|:---------------------------|:-------------------|:------------------------|-----------------------:|
| mix       |       5 |                21 |       10 | no               | 31.5%                     | -29.9%            | 26.9%                      | -38.6%             | 22.2%                   |                  11.28 |
| mix       |       5 |                21 |        5 | no               | 32.3%                     | -33.9%            | 33.9%                      | -41.5%             | 22.2%                   |                  15.58 |
| r126      |       5 |                 5 |        5 | no               | 35.1%                     | -37.4%            | 40.8%                      | -40.4%             | 22.2%                   |                  24.98 |
| r252      |       5 |                21 |        5 | 3                | 32.2%                     | -35.2%            | 54.9%                      | -34.9%             | 22.2%                   |                   9.94 |
| r126      |       5 |                21 |        5 | no               | 35.7%                     | -41.6%            | 36.4%                      | -39.2%             | 22.2%                   |                  17.73 |
| r126      |       5 |                 5 |       10 | no               | 34.3%                     | -40.5%            | 37.7%                      | -42.1%             | 22.2%                   |                  17.73 |
| r126      |       8 |                21 |        5 | 3                | 30.0%                     | -38.4%            | 30.8%                      | -35.7%             | 22.2%                   |                  27.93 |
| mix       |      10 |                 5 |        5 | no               | 27.4%                     | -35.2%            | 32.7%                      | -31.7%             | 22.2%                   |                  34.38 |
| mix       |       8 |                 5 |        5 | no               | 26.7%                     | -34.4%            | 31.6%                      | -34.4%             | 22.2%                   |                  31.42 |
| r252      |       8 |                21 |       10 | no               | 25.2%                     | -33.3%            | 57.0%                      | -32.7%             | 22.2%                   |                   9.13 |

Correlación de ranking dentro vs fuera: **-0.04**