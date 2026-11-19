# Calibración de parámetros

Dentro de muestra: hasta 2023-01-01 (se usa para elegir). Fuera de muestra: desde 2023-01-01 (verificación con datos no usados).

Orden: por retorno/caída (MAR) **dentro de muestra**. Si el ranking fuera de muestra se parece, el resultado es más confiable.

Configuración actual: entrada=retroceso, objetivo_r=4.0, max_dias_en_posicion=20, filtro_mercado=False

## Top 10

| entrada    |   objetivo_r |   max_dias_en_posicion | filtro_mercado   |   in_operaciones |   in_r_promedio (expectancy) | in_retorno_anual (CAGR)   | in_max_drawdown   |   in_retorno/caida (MAR) |   out_r_promedio (expectancy) | out_retorno_anual (CAGR)   | out_max_drawdown   |   out_retorno/caida (MAR) | out_spy_retorno_anual   |
|:-----------|-------------:|-----------------------:|:-----------------|-----------------:|-----------------------------:|:--------------------------|:------------------|-------------------------:|------------------------------:|:---------------------------|:-------------------|--------------------------:|:------------------------|
| ruptura_20 |            5 |                     20 | sí               |              345 |                         0.2  | 8.4%                      | -18.3%            |                     0.46 |                          0.13 | 9.4%                       | -18.4%             |                      0.51 | 19.8%                   |
| ruptura_55 |            3 |                     40 | no               |              290 |                         0.22 | 8.2%                      | -19.1%            |                     0.43 |                          0.06 | 2.9%                       | -19.0%             |                      0.15 | 19.8%                   |
| ruptura_55 |            5 |                     40 | no               |              259 |                         0.21 | 8.0%                      | -18.9%            |                     0.43 |                          0.15 | 5.8%                       | -19.9%             |                      0.29 | 19.8%                   |
| ruptura_55 |            5 |                     40 | sí               |              230 |                         0.22 | 8.2%                      | -20.6%            |                     0.4  |                          0.08 | 2.6%                       | -19.8%             |                      0.13 | 19.8%                   |
| retroceso  |            3 |                     40 | no               |              272 |                         0.22 | 8.3%                      | -21.3%            |                     0.39 |                          0.16 | 9.7%                       | -18.4%             |                      0.53 | 19.8%                   |
| ruptura_20 |            5 |                     40 | no               |              275 |                         0.29 | 10.6%                     | -27.3%            |                     0.39 |                          0.22 | 7.8%                       | -22.4%             |                      0.35 | 19.8%                   |
| ruptura_55 |            5 |                     20 | sí               |              326 |                         0.17 | 6.9%                      | -19.1%            |                     0.36 |                          0.06 | 4.6%                       | -16.1%             |                      0.28 | 19.8%                   |
| retroceso  |            5 |                     40 | no               |              250 |                         0.22 | 7.9%                      | -22.3%            |                     0.35 |                          0.22 | 9.2%                       | -17.1%             |                      0.54 | 19.8%                   |
| ruptura_55 |            3 |                     40 | sí               |              263 |                         0.22 | 8.1%                      | -23.6%            |                     0.34 |                          0.11 | 5.5%                       | -17.5%             |                      0.31 | 19.8%                   |
| retroceso  |            3 |                     40 | sí               |              218 |                         0.22 | 6.7%                      | -19.5%            |                     0.34 |                          0.15 | 8.0%                       | -16.0%             |                      0.5  | 19.8%                   |

## Mejor combinación de cada tipo de entrada

Elegida solo con datos dentro de muestra; las columnas 'fuera' muestran cómo le fue después.

| Entrada | Parámetros | CAGR dentro | Caída dentro | CAGR fuera | Caída fuera | SPY fuera |
|---|---|---|---|---|---|---|
| ruptura_20 | objetivo_r=5.0, max_dias_en_posicion=20, filtro_mercado=sí | 8.4% | -18.3% | 9.4% | -18.4% | 19.8% |
| ruptura_55 | objetivo_r=3.0, max_dias_en_posicion=40, filtro_mercado=no | 8.2% | -19.1% | 2.9% | -19.0% | 19.8% |
| retroceso | objetivo_r=3.0, max_dias_en_posicion=40, filtro_mercado=no | 8.3% | -21.3% | 9.7% | -18.4% | 19.8% |

Correlación de ranking dentro vs fuera de muestra (Spearman): **-0.04** (cerca de 1 = los parámetros que funcionaron antes siguieron funcionando después).