from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from data.data import Dataset


class Transformacion(ABC):
    """Clase abstracta base para todas las transformaciones de datos."""

    @abstractmethod
    def fit(self, dataset):
        pass

    @abstractmethod
    def transform(self, dataset):
        pass

    def fit_transform(self, dataset):
        self.fit(dataset)
        return self.transform(dataset)


class LimpiadorNulos(Transformacion):
    """Limpia valores nulos de un Dataset usando la estrategia indicada."""

    def __init__(self, estrategia="media", columnas=None):
        """
        estrategia : 'media', 'mediana', 'moda' o 'eliminar'
        columnas   : lista de columnas a tratar (None = todas las numéricas)
        """
        self.estrategia = estrategia
        self.columnas = columnas
        self._valores = {}

    def fit(self, dataset):
        df = dataset.get_datos()
        cols = self.columnas or df.select_dtypes(include="number").columns.tolist()
        
        for col in cols:
            if col not in df.columns:
                continue
                
            # Defensa 1: Verificar que la columna sea verdaderamente numérica para promedios
            if not pd.api.types.is_numeric_dtype(df[col]) and self.estrategia in ["media", "mediana"]:
                print(f"  [Advertencia] Se omitió '{col}' para {self.estrategia} porque no es numérica.")
                continue

            try:
                if self.estrategia == "media":
                    self._valores[col] = df[col].mean()
                elif self.estrategia == "mediana":
                    self._valores[col] = df[col].median()
                elif self.estrategia == "moda":
                    self._valores[col] = df[col].mode().iloc[0] if not df[col].mode().empty else 0
            except Exception as e:
                print(f"  [Advertencia] No se pudo calcular {self.estrategia} para la columna '{col}'. Detalle: {e}")
                
        return self

    def transform(self, dataset):
        df = dataset.get_datos().copy()
        
        try:
            if self.estrategia == "eliminar":
                # Si columnas es None, aplicar dropna a todo para evitar comportamientos inesperados
                subset = self.columnas if self.columnas else df.columns
                df = df.dropna(subset=subset).reset_index(drop=True)
            else:
                for col, val in self._valores.items():
                    # Defensa 2: Prevenir rellenar con NaN si el cálculo matemático falló
                    if pd.notna(val):
                        df[col] = df[col].fillna(val)
        except Exception as e:
            print(f"  [Error] Falló la transformación de nulos: {e}")

        return Dataset(
            nombre=dataset.nombre,
            datos=df,
            origen=dataset.origen,
            metadata=dataset.metadata
        )


class Scaler(Transformacion):
    """Escala columnas numéricas usando estandarización (z-score) o min-max."""

    def __init__(self, metodo="zscore", columnas=None):
        """
        metodo   : 'zscore' o 'minmax'
        columnas : lista de columnas a escalar (None = todas las numéricas)
        """
        self.metodo = metodo
        self.columnas = columnas
        self._params = {}

    def fit(self, dataset):
        df = dataset.get_datos()
        cols = self.columnas or df.select_dtypes(include="number").columns.tolist()
        
        for col in cols:
            if col not in df.columns:
                continue
                
            # Defensa 1: El escalamiento es estrictamente matemático
            if not pd.api.types.is_numeric_dtype(df[col]):
                print(f"  [Advertencia] Se omitió '{col}' en el Scaler porque no es numérica.")
                continue

            try:
                if self.metodo == "zscore":
                    self._params[col] = {"mean": df[col].mean(), "std": df[col].std()}
                elif self.metodo == "minmax":
                    self._params[col] = {"min": df[col].min(), "max": df[col].max()}
            except Exception as e:
                print(f"  [Advertencia] No se pudieron calcular parámetros de escalado para '{col}'. Detalle: {e}")
                
        return self

    def transform(self, dataset):
        df = dataset.get_datos().copy()
        
        for col, p in self._params.items():
            try:
                if self.metodo == "zscore":
                    # Defensa 2: Evitar división por cero y manejar desviaciones estándar nulas
                    std = p["std"] if pd.notna(p["std"]) and p["std"] != 0 else 1
                    mean = p["mean"] if pd.notna(p["mean"]) else 0
                    df[col] = (df[col] - mean) / std
                    
                elif self.metodo == "minmax":
                    # Defensa 3: Evitar división por cero si max y min son iguales
                    rango = p["max"] - p["min"]
                    rango = rango if pd.notna(rango) and rango != 0 else 1
                    min_val = p["min"] if pd.notna(p["min"]) else 0
                    df[col] = (df[col] - min_val) / rango
            except Exception as e:
                print(f"  [Error] Falló la transformación de escala en la columna '{col}': {e}")
                
        return Dataset(
            nombre=dataset.nombre,
            datos=df,
            origen=dataset.origen,
            metadata=dataset.metadata
        )
