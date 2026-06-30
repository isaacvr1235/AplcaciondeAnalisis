"""
data/api_loader.py
Extensión D del Examen Extraordinario: integración de una nueva fuente
de datos (API REST externa) incorporada al flujo existente de la aplicación.

La clase APILoader consulta un endpoint HTTP, interpreta la respuesta JSON
(sea un objeto único, una lista de objetos, o un objeto con una lista anidada)
y la convierte en un Dataset, exactamente igual que DataLoader lo hace
para CSV/TSV/Excel/JSON/SQL.
"""

import requests
import pandas as pd
from data.data import Dataset


class APILoader:
    """Obtiene datos desde una API REST y los convierte en un Dataset."""

    def __init__(self, timeout=15):
        self.timeout = timeout
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "AplicacionAnalisisDatos/1.0 (+examen-extraordinario)"
        }

    # ── Paso 1: consultar el endpoint ──────────────────

    def consultar_api(self, url, params=None, headers=None):
        """
        Hace un GET al endpoint indicado y devuelve el JSON ya parseado.
        Lanza excepciones controladas con mensajes claros ante:
        errores de red, timeout, status HTTP de error, o respuesta no-JSON.
        """
        hdrs = {**self.headers, **(headers or {})}

        try:
            print(f"  Consultando API: {url}")
            respuesta = requests.get(url, params=params, headers=hdrs, timeout=self.timeout)
        except requests.exceptions.Timeout:
            raise ConnectionError(f"La API no respondió en {self.timeout}s (timeout).")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"No se pudo conectar con la API: {url}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error de red al consultar la API: {e}")

        if respuesta.status_code != 200:
            raise ValueError(
                f"La API respondió con código {respuesta.status_code}: "
                f"{respuesta.text[:200]}"
            )

        try:
            data = respuesta.json()
        except ValueError:
            raise ValueError("La respuesta de la API no es un JSON válido.")

        print(f"  ✔ Respuesta recibida ({len(respuesta.content):,} bytes)")
        return data

    # ── Paso 2: aplanar el JSON a DataFrame ────────────

    def json_a_dataframe(self, data, ruta_registros=None):
        """
        Convierte el JSON de respuesta en un DataFrame.

        ruta_registros : nombre (o nombres separados por '.') de la clave
                          donde viven los registros, si la API envuelve la
                          lista dentro de un objeto. Ej: 'results' o
                          'data.items'. Si es None, se intenta detectar
                          automáticamente.
        """
        # Si nos indicaron una ruta explícita, navegamos hasta ella
        if ruta_registros:
            nodo = data
            for clave in ruta_registros.split("."):
                if isinstance(nodo, dict) and clave in nodo:
                    nodo = nodo[clave]
                else:
                    raise KeyError(
                        f"La ruta '{ruta_registros}' no existe en el JSON "
                        f"(falló en la clave '{clave}')."
                    )
            data = nodo

        # Detección automática: si es un dict, buscar la primera lista dentro
        if isinstance(data, dict):
            lista_candidata = None
            for v in data.values():
                if isinstance(v, list):
                    lista_candidata = v
                    break
            data = lista_candidata if lista_candidata is not None else [data]

        if not isinstance(data, list):
            data = [data]

        if len(data) == 0:
            raise ValueError("La API no devolvió registros (lista vacía).")

        try:
            df = pd.json_normalize(data)
        except Exception as e:
            raise ValueError(f"No se pudo normalizar el JSON a tabla: {e}")

        if df.empty:
            raise ValueError("El DataFrame resultante está vacío.")

        df = self._aplanar_celdas_complejas(df)

        return df

    @staticmethod
    def _aplanar_celdas_complejas(df):
        """
        Defensa: algunas APIs devuelven campos que son listas o diccionarios
        dentro de una celda (ej. 'capital': ['Mexico City'] en REST Countries).
        Esos valores no son "hasheables", por lo que rompen operaciones
        posteriores como value_counts() durante el EDA. Aquí se convierten
        a texto plano para que el resto del flujo (EDA, modelos, clustering)
        los trate como cualquier columna categórica normal.
        """
        for col in df.columns:
            tiene_complejos = df[col].apply(lambda v: isinstance(v, (list, dict))).any()
            if tiene_complejos:
                df[col] = df[col].apply(APILoader._valor_a_texto)
        return df

    @staticmethod
    def _valor_a_texto(valor):
        if isinstance(valor, list):
            return ", ".join(str(v) for v in valor) if valor else None
        if isinstance(valor, dict):
            return ", ".join(f"{k}={v}" for k, v in valor.items()) if valor else None
        return valor

    # ── Paso 3: combinar todo en un Dataset ────────────

    def cargar_api(self, url, params=None, headers=None, ruta_registros=None, nombre=None):
        """
        Consulta la API y devuelve un Dataset listo para usarse en el
        resto del flujo (EDA, modelos, clustering, etc.), igual que
        cualquier otra fuente cargada por DataLoader.
        """
        data = self.consultar_api(url, params=params, headers=headers)
        df = self.json_a_dataframe(data, ruta_registros=ruta_registros)

        nombre = nombre or "API_dataset"
        ds = Dataset(
            nombre=nombre,
            datos=df,
            origen=url,
            metadata={
                "formato": "API",
                "url": url,
                "params": params,
                "ruta_registros": ruta_registros,
            }
        )
        print(f"  ✔ API cargada: '{nombre}'  [{df.shape[0]} filas x {df.shape[1]} columnas]")
        return ds
