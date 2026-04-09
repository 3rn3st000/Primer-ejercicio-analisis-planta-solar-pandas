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
datosUnidos = datosUnidos.sort_values(by=['SOURCE_KEY_y', 'DATE_TIME'])
datosUnidos = datosUnidos.set_index('DATE_TIME')
print(datosUnidos.shape)
print(datosMeteorologia.shape)


# %% [markdown]
# Eliminamos una de las columnas de id de las plantas al estar duplicadas

# %%
datosUnidos = datosUnidos.drop(columns=['PLANT_ID_x'])


# %% [markdown]
# En primer lugar hacemos una funcion para detectar outliers y mediante una interpolación temporal hacemos que los NaN se rellenen automáticamente

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
datosUnidos['DC_POWER'] = datosUnidos.groupby('SOURCE_KEY_y')['DC_POWER'].transform(
    lambda x: x.interpolate(method='time')
)

# %% [markdown]
# Contamos cuantas mediciones se han hecho por hora

# %%
datosUnidos['TRAMO_HORARIO'] = datosUnidos.index.floor('h') 
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
# Ahora vamos a ver la relación entre la producción y la irradiación solar. Como nota debemos subrayar que los datos "extraños" que observamos en el eje vertical izquierdo del gráfico de disperión en los que la radiación solar es mayor a 0 pero no se genera potencia no se han eliminado al ser muy útiles para encontrar fallos operativos en los inversores

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
datosUnidos['HORA']= datosUnidos.index.hour
irrHora = datosUnidos.groupby('HORA')['IRRADIATION'].median().reset_index()
sns.barplot(data=irrHora,x= 'HORA', y = 'IRRADIATION')
indice_max_irr = irrHora['IRRADIATION'].idxmax()
fila_maxima = irrHora.loc[indice_max_irr]
print(f"La irradiación máxima promedio es de  {fila_maxima['IRRADIATION']} y se da a las {fila_maxima['HORA']}")

# %% [markdown]
# Desde la empresa nos comunican que ha bajado la potencia mucho en los últimos meses, seguramente provocado por el deterioro o fallo de alguno de los inversores, nos piden localizar los inversores defectuosos para poder repararlos.
# 
# Usaremos un ratio de rendimiento calculado sobre la radiación solar para identificar los outliers a la baja que son los que están causando este fallo

# %%
# Creamos el resumen por inversor
irrDCComb = datosUnidos.groupby('SOURCE_KEY_y').agg({
    'DC_POWER': 'mean',
    'IRRADIATION': 'mean'
}).reset_index()

irrDCComb['RATIOPROD'] = irrDCComb['DC_POWER'] / irrDCComb['IRRADIATION']
mediana = abs(irrDCComb['RATIOPROD'].median())
Q1 = irrDCComb['RATIOPROD'].quantile(0.25)
Q3 = irrDCComb['RATIOPROD'].quantile(0.75)
IQR = Q3 - Q1
limite_inferior = Q1 - 1.5 * IQR
inversores_fallando = irrDCComb[irrDCComb['RATIOPROD'] < limite_inferior]
ids_defectuosos = inversores_fallando['SOURCE_KEY_y'].tolist()
print(f"Inversores defectuosos \n {inversores_fallando}")
print(f"La mediana de ratio es de {mediana}")

# %% [markdown]
# La empresa desea conocer si la restauración de estas plantas sería óptimo o, si en cambio el restaurarlas resultaria en una pérdida de dinero. Para ello nos han pedido una simulación de la generación si se restauran las plantas, sobretodo inquiriendo en que debe ser expuesta de forma muy visual.

# %%
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

datosUnidos_ml = datosUnidos.dropna(subset=['AMBIENT_TEMPERATURE', 'IRRADIATION', 'DC_POWER'])  
datos_entrenamiento = datosUnidos_ml[~datosUnidos_ml['SOURCE_KEY_y'].isin(ids_defectuosos)]
X = datos_entrenamiento[['AMBIENT_TEMPERATURE','IRRADIATION']]
y = datos_entrenamiento['DC_POWER']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
modelo_inversor = RandomForestRegressor(n_estimators=100, random_state=42)
modelo_inversor.fit(X_train, y_train)
predicciones = modelo_inversor.predict(X_test)
error = mean_absolute_error(y_test, predicciones)
print(f"El error medio de mi Gemelo Digital es de: {error:.2f} kW")




# %% [markdown]
# Ahora aplicamos el GD y estimamos la potencia generada

# %%
datos_test = datosUnidos.loc[
    datosUnidos['SOURCE_KEY_y'].isin(ids_defectuosos), 
    ['SOURCE_KEY_y', 'AMBIENT_TEMPERATURE', 'IRRADIATION']
].dropna()
Kw_restauracion = modelo_inversor.predict(
    datos_test[['AMBIENT_TEMPERATURE', 'IRRADIATION']]
)
datos_test['DC_POWER_TEORICO'] = Kw_restauracion

# 3. Prints Corregidos
print("--- Media Teórica por Inversor Defectuoso ---")
print(datos_test.groupby('SOURCE_KEY_y')['DC_POWER_TEORICO'].mean())

print("\n--- Media Real de Toda la Planta (Referencia) ---")
print(datosUnidos['DC_POWER'].mean())

# %% [markdown]
# Ahora lo representamos para los stake holders

# %%
# 1. Calculamos las tres medias principales
media_plant_sana = datosUnidos.loc[~datosUnidos['SOURCE_KEY_y'].isin(ids_defectuosos), 'DC_POWER'].mean()
media_actual_defectuosos = datosUnidos.loc[datosUnidos['SOURCE_KEY_y'].isin(ids_defectuosos), 'DC_POWER'].mean()
media_potencial_defectuosos = datos_test['DC_POWER_TEORICO'].mean()

# 2. Creamos una tablita rápida para graficar
datos_grafico = {
    'Estado': ['Rendimiento Actual (Rotos)', 'Promedio Resto Planta', 'Potencial tras Reparar'],
    'Potencia (kW)': [media_actual_defectuosos, media_plant_sana, media_potencial_defectuosos]
}

# 3. Dibujamos
plt.figure(figsize=(10, 6))
sns.barplot(x='Estado', y='Potencia (kW)', data=datos_grafico, palette=['red', 'gray', 'green'])
plt.title('¿Cuánto estamos perdiendo por no reparar?')
plt.show()


