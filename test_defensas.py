import pandas as pd
import numpy as np
from data.data import Dataset
from pipeline.pipeline import Pipeline
from preprocessing.transformers import LimpiadorNulos, Scaler 
# Nota: Ajusta 'preprocessing.transformers' si tus clases están en otro archivo dentro de preprocessing

print("--- INICIANDO PRUEBA DE ESTRÉS AL PIPELINE ---")

# 1. Crear un DataFrame "Venenoso"
df_trampa = pd.DataFrame({
    "Normal": [10.0, 20.0, np.nan, 40.0],
    "Columna_Texto": ["Isaac", "Manuel", "Félix", "Eduardo"], # Trampa 1: Texto donde debería ir número
    "Columna_Constante": [5, 5, 5, 5],                       # Trampa 2: Varianza 0 (rompe el Scaler)
    "Columna_Vacia": [np.nan, np.nan, np.nan, np.nan]        # Trampa 3: Todo nulo
})

# Envolverlo en tu clase Dataset
dataset_prueba = Dataset(nombre="Dataset_Veneno", datos=df_trampa, origen="Prueba")

# 2. Configurar el Pipeline con nuestras clases blindadas
mi_pipeline = Pipeline()

# Le pedimos a propósito que intente sacar la 'media' de la columna de texto
mi_pipeline.agregar_paso(LimpiadorNulos(estrategia="media", columnas=["Normal", "Columna_Texto", "Columna_Constante"]))
# Le pedimos que escale todo (intentará dividir por cero en la columna constante)
mi_pipeline.agregar_paso(Scaler(metodo="zscore"))

# 3. Ejecutar y observar la magia
print("\n[Ejecutando Pipeline...]")
mi_pipeline.ejecutar(dataset_prueba)

print("\n--- PRUEBA FINALIZADA ---")
print("Si estás leyendo esto, ¡tu programa sobrevivió y no crasheó!")