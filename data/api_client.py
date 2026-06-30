"""
api_client.py
Extensión D — Integración de una nueva fuente de datos: API pública (REST/JSON).

Consume la API pública de Universidades (Hipolabs Universities API,
http://universities.hipolabs.com), que no requiere API key, y la
incorpora al flujo existente de la aplicación devolviendo objetos
Dataset, igual que DataLoader y WebScraper.
"""

import requests
import pandas as pd
from data.data import Dataset


class APIClient:
    """
    Cliente genérico para consumir APIs públicas (REST/JSON) y
    convertir las respuestas en objetos Dataset.
    """

    BASE_UNIVERSIDADES = "http://universities.hipolabs.com/search"

    def __init__(self, timeout=15):
        self.timeout = timeout

    # ── Consulta genérica ─────────────────────

    def consultar(self, url, params=None):
        """Hace un GET a una API REST y devuelve el JSON ya parseado."""
        print(f"  Consultando API: {url}  params={params}")
        resp = requests.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        n = len(data) if isinstance(data, list) else 1
        print(f"  ✔ Respuesta recibida ({n} elementos)")
        return data

    def json_a_dataframe(self, data):
        """Convierte una respuesta JSON (lista de objetos o un único objeto) en DataFrame."""
        if isinstance(data, dict):
            data = [data]
        return pd.json_normalize(data)

    def obtener_dataset(self, url, params=None, nombre="API_dataset"):
        """Consulta una API y devuelve el resultado envuelto en un Dataset."""
        data = self.consultar(url, params)
        df = self.json_a_dataframe(data)
        ds = Dataset(
            nombre=nombre,
            datos=df,
            origen=url,
            metadata={"formato": "API", "endpoint": url, "params": params or {}}
        )
        print(f"  ✔ Dataset desde API: '{nombre}'  [{df.shape[0]} filas x {df.shape[1]} columnas]")
        return ds

    # ── Endpoint específico: Universidades por país ──

    def obtener_universidades(self, pais="Mexico", nombre=None):
        """
        Consulta la API pública de Universidades (Hipolabs) filtrando por país
        y devuelve un Dataset listo para usarse en el resto de la aplicación.
        """
        params = {"country": pais}
        nombre = nombre or f"Universidades_{pais}"
        ds = self.obtener_dataset(self.BASE_UNIVERSIDADES, params=params, nombre=nombre)

        # Las columnas 'web_pages' y 'domains' llegan como listas: se aplanan
        # a texto para que sean utilizables en EDA, modelos y clustering.
        for col in ("web_pages", "domains"):
            if col in ds.datos.columns:
                ds.datos[col] = ds.datos[col].apply(
                    lambda x: ", ".join(x) if isinstance(x, list) else x
                )

        return ds
