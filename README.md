# Análisis de Planta Solar Fotovoltaica

Escenario de análisis  de datos sobre una planta solar real. El objetivo principal era detectar qué inversores estaban funcionando por debajo de su rendimiento esperado y estimar cuánta energía se está perdiendo por no repararlos.

## El problema

En este escenario hipotético la empresa notó una bajada en la generación total de la planta durante los últimos meses. Sospechaban que uno o varios inversores estaban fallando, pero no sabían cuáles ni cuánto impacto real tenían en la producción.

## Qué hace el notebook

El análisis sigue una lógica bastante lineal:

1. Se cargan y cruzan los datos de generación con los datos meteorológicos del sensor
2. Se limpian outliers en DC_POWER y se interpolan los huecos temporalmente
3. Se analiza qué variables climáticas correlacionan más con la producción 
4. Se calcula un ratio de rendimiento por inversor (potencia media / irradiación media) y se usan cuartiles para detectar los que están claramente por debajo
5. Se entrena un Random Forest con los inversores sanos para construir un "gemelo digital": dado un contexto meteorológico, ¿cuánto debería generar un inversor en buen estado?
6. Ese modelo se aplica sobre los inversores defectuosos para estimar su potencial real si se reparan
7. El resultado final se presenta en un gráfico comparativo y un calculo monetario pensado para que cualquier stakeholder entienda el impacto económico de la reparación

## Datos

Los datos son públicos y están disponibles en Kaggle:
[Solar Power Generation Data](https://www.kaggle.com/datasets/anikannal/solar-power-generation-data)


## Requisitos

```
pandas
numpy
seaborn
matplotlib
scikit-learn
```


## Resultado

El análisis identificó 2 inversores con un ratio de rendimiento significativamente inferior al resto de la planta. El gemelo digital estimó que repararlos recuperaría una media de 12179 € al año.

## Estructura del proyecto

```
├── README.md
├── analisis_planta_solar.ipynb
├── Plant_1_Generation_Data.csv
└── Plant_1_Weather_Sensor_Data.csv
```

