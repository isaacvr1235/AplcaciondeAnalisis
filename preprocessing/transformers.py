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
            if self.estrategia == "media":
                self._valores[col] = df[col].mean()
            elif self.estrategia == "mediana":
                self._valores[col] = df[col].median()
            elif self.estrategia == "moda":
                self._valores[col] = df[col].mode().iloc[0] if not df[col].mode().empty else 0
        return self

    def transform(self, dataset):
        df = dataset.get_datos().copy()
        if self.estrategia == "eliminar":
            df = df.dropna(subset=self.columnas).reset_index(drop=True)
        else:
            for col, val in self._valores.items():
                df[col] = df[col].fillna(val)
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
            if self.metodo == "zscore":
                self._params[col] = {"mean": df[col].mean(), "std": df[col].std()}
            elif self.metodo == "minmax":
                self._params[col] = {"min": df[col].min(), "max": df[col].max()}
        return self

    def transform(self, dataset):
        df = dataset.get_datos().copy()
        for col, p in self._params.items():
            if self.metodo == "zscore":
                std = p["std"] if p["std"] != 0 else 1
                df[col] = (df[col] - p["mean"]) / std
            elif self.metodo == "minmax":
                rango = p["max"] - p["min"]
                rango = rango if rango != 0 else 1
                df[col] = (df[col] - p["min"]) / rango
        return Dataset(
            nombre=dataset.nombre,
            datos=df,
            origen=dataset.origen,
            metadata=dataset.metadata
        )
