# %%
import pandas as pd
import numpy as np
datosGeneracion = pd.read_csv(r"/home/ernesto/trabajo/Datasets/datos/solar/Plant_1_Generation_Data.csv")
datosMeteorologia = pd.read_csv(r"/home/ernesto/trabajo/Datasets/datos/solar/Plant_1_Weather_Sensor_Data.csv")


# %% [markdown]
# Una vez cargadas, visualizamos la info de los dos csv para poder juntarlos

# %%
print(datosGeneracion.info())
print(datosMeteorologia.info())

# %% [markdown]
# En primer lugar transformamos todas las fechas a formato DATE_TIME

# %%
datosGeneracion['DATE_TIME'] = pd.to_datetime(datosGeneracion['DATE_TIME'])
datosMeteorologia['DATE_TIME'] = pd.to_datetime(datosMeteorologia['DATE_TIME'])

# %% [markdown]
# Luego cruzamos las tablas

# %%
datosUnidos= pd.merge(datosMeteorologia,datosGeneracion,on='DATE_TIME',how = 'inner')
print(datosUnidos.shape)
print(datosMeteorologia.shape)

# %% [markdown]
# Eliminamos una de las columnas de id de las plantas al estar duplicadas

# %%
datosUnidos = datosUnidos.drop(columns=['PLANT_ID_x'])


# %% [markdown]
# En primer lugar hacemos una funcion para detectar outliers

# %%
def fueraRango(valor, min_val, max_val):
    if valor < min_val or valor > max_val:
        return np.nan
    return valor
        
datosUnidos['DC_POWER'] = datosUnidos['DC_POWER'].apply(
    fueraRango, 
    min_val=0, 
    max_val=15000
)

# %% [markdown]
# Contamos cuantas mediciones se han hecho por hora

# %%
datosUnidos['TRAMO_HORARIO'] = datosUnidos['DATE_TIME'].dt.floor('h')
ranking_tramos = datosUnidos['TRAMO_HORARIO'].value_counts().reset_index(name='frecuencia')
print(ranking_tramos)

# %% [markdown]
# Buscamos las que más y menos generan

# %%
datosUnidos.groupby('SOURCE_KEY_y')['DC_POWER'].mean().sort_values(ascending=False)

# %% [markdown]
# Ahora vamos a ver la relación entre la producción y la irradiación solar

# %%
correlacionIrradiacion = datosUnidos['DC_POWER'].corr(datosUnidos['IRRADIATION'])

print (correlacionIrradiacion)

# %% [markdown]
# ¿Qué es más importante para la generación, la temperatura del modulo, la ambiente o la irradiación?

# %%
correlacionTempAmb = datosUnidos['DC_POWER'].corr(datosUnidos['AMBIENT_TEMPERATURE'])
corrrelacionTempMod = datosUnidos['DC_POWER'].corr(datosUnidos['MODULE_TEMPERATURE'])

lista_corr = [
    ("Irradiación", correlacionIrradiacion),
    ("Temp. Ambiente", correlacionTempAmb),
    ("Temp. Módulo", corrrelacionTempMod)
]

lista_corr.sort(key=lambda x: x[1], reverse=True)

for nombre, valor in lista_corr:
    print(f"{nombre} : {valor:.4f}")


