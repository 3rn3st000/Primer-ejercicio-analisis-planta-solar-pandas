# %%
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
datosGeneracion = pd.read_csv(r"Plant_1_Generation_Data.csv")
datosMeteorologia = pd.read_csv(r"Plant_1_Weather_Sensor_Data.csv")


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
    min_val=1, 
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

dU_promedio = datosUnidos.groupby('SOURCE_KEY_y')['DC_POWER'].mean().sort_values(ascending=False).reset_index()
sns.set_theme(style="whitegrid") 
plt.figure(figsize=(12, 6))
plot = sns.barplot(
    data=dU_promedio, 
    x='SOURCE_KEY_y', 
    y='DC_POWER', 
)
plt.title('Promedio de DC POWER por Fuente (Inversor)', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Source Key (Inversor)', fontsize=12)
plt.ylabel('Promedio DC Power (kW)', fontsize=12)
plt.xticks(rotation=45, ha='right')
sns.despine(left=True, bottom=True)

plt.tight_layout() 
plt.show()

# %% [markdown]
# Ahora vamos a ver la relación entre la producción y la irradiación solar

# %%
correlacionIrradiacion = datosUnidos['DC_POWER'].corr(datosUnidos['IRRADIATION'])
sns.regplot(data=datosUnidos,x='DC_POWER',y= 'IRRADIATION',scatter_kws={'alpha':0.3},line_kws={'color':'red'})
print (f"La correlación entre las dos variables es de {correlacionIrradiacion} lo que indica alta correlación")

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
df_LCorr = pd.DataFrame(lista_corr,columns=['VARIABLE','COEFICIENTE'])
sns.barplot(data=df_LCorr,x='COEFICIENTE',y='VARIABLE')

# %% [markdown]
# Sabiendo ya la importancia de la irradiación, buscaremos las horas donde teóricamente obtendremos más generación

# %%
datosUnidos['HORA']= datosUnidos.DATE_TIME.dt.hour
irrHora = datosUnidos.groupby('HORA')['IRRADIATION'].median().reset_index()
sns.barplot(data=irrHora,x= 'HORA', y = 'IRRADIATION')
indice_max_irr = irrHora['IRRADIATION'].idxmax()
fila_maxima = irrHora.loc[indice_max_irr]
print(f"La irradiación máxima promedio es de  {fila_maxima['IRRADIATION']} y se da a las {fila_maxima['HORA']}")


