# Calibración de parámetros

Dentro de muestra: hasta 2023-01-01 (se usa para elegir). Fuera de muestra: desde 2023-01-01 (verificación con datos no usados).

Orden: por retorno/caída (MAR) **dentro de muestra**. Si el ranking fuera de muestra se parece, el resultado es más confiable.

Configuración actual: entrada=retroceso, objetivo_r=4.0, max_dias_en_posicion=20, filtro_mercado=False

## Top 10

| entrada    |   objetivo_r |   max_dias_en_posicion | filtro_mercado   |   in_operaciones |   in_r_promedio (expectancy) | in_retorno_anual (CAGR)   | in_max_drawdown   |   in_retorno/caida (MAR) |   out_r_promedio (expectancy) | out_retorno_anual (CAGR)   | out_max_drawdown   |   out_retorno/caida (MAR) | out_spy_retorno_anual   |
|:-----------|-------------:|-----------------------:|:-----------------|-----------------:|-----------------------------:|:--------------------------|:------------------|-------------------------:|------------------------------:|:---------------------------|:-------------------|--------------------------:|:------------------------|
| ruptura_20 |            5 |                     20 | sí               |              345 |                         0.2  | 8.4%                      | -18.3%            |                     0.46 |                          0.15 | 10.8%                      | -18.4%             |                      0.59 | 20.9%                   |
| ruptura_55 |            3 |                     40 | no               |              290 |                         0.22 | 8.2%                      | -19.1%            |                     0.43 |                          0.09 | 4.6%                       | -18.9%             |                      0.24 | 20.9%                   |
| ruptura_55 |            5 |                     40 | no               |              259 |                         0.21 | 8.0%                      | -18.9%            |                     0.43 |                          0.2  | 7.6%                       | -19.4%             |                      0.39 | 20.9%                   |
| ruptura_55 |            5 |                     40 | sí               |              230 |                         0.22 | 8.2%                      | -20.6%            |                     0.4  |                          0.13 | 4.3%                       | -14.8%             |                      0.29 | 20.9%                   |
| retroceso  |            3 |                     40 | no               |              272 |                         0.22 | 8.3%                      | -21.3%            |                     0.39 |                          0.18 | 10.8%                      | -18.4%             |                      0.58 | 20.9%                   |
| ruptura_20 |            5 |                     40 | no               |              275 |                         0.29 | 10.6%                     | -27.3%            |                     0.39 |                          0.23 | 8.2%                       | -22.4%             |                      0.37 | 20.9%                   |
| ruptura_55 |            5 |                     20 | sí               |              326 |                         0.17 | 6.9%                      | -19.1%            |                     0.36 |                          0.09 | 6.1%                       | -16.1%             |                      0.38 | 20.9%                   |
| retroceso  |            5 |                     40 | no               |              250 |                         0.22 | 7.9%                      | -22.3%            |                     0.35 |                          0.25 | 10.8%                      | -17.1%             |                      0.63 | 20.9%                   |
| ruptura_55 |            3 |                     40 | sí               |              263 |                         0.22 | 8.1%                      | -23.6%            |                     0.34 |                          0.14 | 7.2%                       | -13.3%             |                      0.54 | 20.9%                   |
| retroceso  |            3 |                     40 | sí               |              218 |                         0.22 | 6.7%                      | -19.5%            |                     0.34 |                          0.17 | 9.0%                       | -16.0%             |                      0.56 | 20.9%                   |

## Mejor combinación de cada tipo de entrada

Elegida solo con datos dentro de muestra; las columnas 'fuera' muestran cómo le fue después.

| Entrada | Parámetros | CAGR dentro | Caída dentro | CAGR fuera | Caída fuera | SPY fuera |
|---|---|---|---|---|---|---|
| ruptura_20 | objetivo_r=5.0, max_dias_en_posicion=20, filtro_mercado=sí | 8.4% | -18.3% | 10.8% | -18.4% | 20.9% |
| ruptura_55 | objetivo_r=3.0, max_dias_en_posicion=40, filtro_mercado=no | 8.2% | -19.1% | 4.6% | -18.9% | 20.9% |
| retroceso | objetivo_r=3.0, max_dias_en_posicion=40, filtro_mercado=no | 8.3% | -21.3% | 10.8% | -18.4% | 20.9% |

Correlación de ranking dentro vs fuera de muestra (Spearman): **0.03** (cerca de 1 = los parámetros que funcionaron antes siguieron funcionando después).