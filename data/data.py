import pandas as pd
import os

class Dataset:
    def __init__(self, data: pd.DataFrame, nombre_fuente: str):
        self.data = data
        self.nombre_fuente = nombre_fuente
        self.n_filas, self.n_columnas = data.shape

    def head(self, n=5):
        return self.data.head(n)

class DataLoader:
    def __init__(self):
        pass

    def cargar_csv(self, ruta_archivo: str) -> Dataset:
        if not os.path.exists(ruta_archivo):
            raise FileNotFoundError(f"Error: El archivo {ruta_archivo} no existe.")
        
        try:
            df = pd.read_csv(ruta_archivo)
            nombre_archivo = os.path.basename(ruta_archivo)
            
            print(f"Exito: Archivo '{nombre_archivo}' cargado correctamente.")
            return Dataset(data=df, nombre_fuente=nombre_archivo)
            
        except Exception as e:
            raise RuntimeError(f"Ocurrió un error al leer el archivo CSV: {e}")
