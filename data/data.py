import os
import pandas as pd
import sqlite3
from datetime import datetime
 
 
# ──────────────────────────────────────────────
# Dataset
# ──────────────────────────────────────────────
 
class Dataset:
    """Encapsula un DataFrame junto con sus metadatos."""
 
    def __init__(self, nombre=None, datos=None, origen=None,
                 fecha_carga=None, metadata=None):
        self.nombre      = nombre
        self.datos       = datos          # pd.DataFrame
        self.origen      = origen
        self.fecha_carga = fecha_carga or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.metadata    = metadata or {}
 
    # ── Propiedades de inspección ──────────────
 
    def get_dimensiones(self):
        if self.datos is None:
            return (0, 0)
        return self.datos.shape
 
    def get_columnas(self):
        if self.datos is None:
            return []
        return list(self.datos.columns)
 
    def get_datos(self):
        return self.datos
 
    def info(self):
        filas, cols = self.get_dimensiones()
        print(f"\n{'─'*45}")
        print(f"  Dataset : {self.nombre}")
        print(f"  Origen  : {self.origen}")
        print(f"  Cargado : {self.fecha_carga}")
        print(f"  Filas   : {filas}   Columnas: {cols}")
        nulos = self.datos.isnull().sum().sum() if self.datos is not None else 0
        print(f"  Nulos   : {nulos}")
        print(f"  Columnas: {self.get_columnas()}")
        print(f"{'─'*45}\n")
 
    def head(self, n=5):
        if self.datos is None:
            return None
        return self.datos.head(n)
 
    def guardar(self, ruta):
        if self.datos is not None:
            ext = os.path.splitext(ruta)[1].lower()
            if ext == ".csv":
                self.datos.to_csv(ruta, index=False, encoding="utf-8-sig")
            elif ext in (".tsv", ".txt"):
                self.datos.to_csv(ruta, index=False, sep="\t", encoding="utf-8-sig")
            else:
                self.datos.to_csv(ruta, index=False, encoding="utf-8-sig")
            print(f"  ✔ Dataset guardado en: {ruta}")
 
    def __repr__(self):
        f, c = self.get_dimensiones()
        return f"<Dataset '{self.nombre}' [{f}x{c}] desde '{self.origen}'>"
 
 
# ──────────────────────────────────────────────
# DataLoader
# ──────────────────────────────────────────────
 
class DataLoader:
    """Carga datos desde CSV, TSV y SQLite."""
 
    # ── CSV ───────────────────────────────────
 
    def cargar_csv(self, ruta, nombre=None, **kwargs):
        """Carga un archivo .csv y devuelve un Dataset."""
        if not os.path.exists(ruta):
            raise FileNotFoundError(f"Archivo no encontrado: {ruta}")
        df = pd.read_csv(ruta, encoding="utf-8-sig", **kwargs)
        nombre = nombre or os.path.basename(ruta)
        ds = Dataset(
            nombre=nombre,
            datos=df,
            origen=ruta,
            metadata={"formato": "CSV", "ruta_absoluta": os.path.abspath(ruta)}
        )
        print(f"  ✔ CSV cargado: '{nombre}'  [{df.shape[0]} filas x {df.shape[1]} columnas]")
        return ds
 
    # ── TSV ───────────────────────────────────
 
    def cargar_tsv(self, ruta, nombre=None, **kwargs):
        """Carga un archivo .tsv (separado por tabulador) y devuelve un Dataset."""
        if not os.path.exists(ruta):
            raise FileNotFoundError(f"Archivo no encontrado: {ruta}")
        df = pd.read_csv(ruta, sep="\t", encoding="utf-8-sig", **kwargs)
        nombre = nombre or os.path.basename(ruta)
        ds = Dataset(
            nombre=nombre,
            datos=df,
            origen=ruta,
            metadata={"formato": "TSV", "ruta_absoluta": os.path.abspath(ruta)}
        )
        print(f"  ✔ TSV cargado: '{nombre}'  [{df.shape[0]} filas x {df.shape[1]} columnas]")
        return ds
 
    # ── SQL / SQLite ──────────────────────────
 
    def conectar_sqlite(self, ruta_db):
        """Abre y devuelve una conexión SQLite."""
        conn = sqlite3.connect(ruta_db)
        print(f"  ✔ Conexión SQLite establecida: {ruta_db}")
        return conn
 
    def listar_tablas_sql(self, conn):
        """Devuelve la lista de tablas de una BD SQLite."""
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tablas = [r[0] for r in cur.fetchall()]
        print(f"  ✔ Tablas encontradas: {tablas}")
        return tablas
 
    def cargar_tabla_sql(self, conn, tabla, nombre=None):
        """Lee una tabla SQL completa y devuelve un Dataset."""
        df = pd.read_sql_query(f"SELECT * FROM {tabla}", conn)
        nombre = nombre or tabla
        ds = Dataset(
            nombre=nombre,
            datos=df,
            origen=f"SQLite:{tabla}",
            metadata={"formato": "SQL", "tabla": tabla}
        )
        print(f"  ✔ Tabla SQL '{tabla}' cargada  [{df.shape[0]} filas x {df.shape[1]} columnas]")
        return ds
 
    def ejecutar_query_sql(self, conn, query, nombre="query_result"):
        """Ejecuta una consulta SQL y devuelve un Dataset."""
        df = pd.read_sql_query(query, conn)
        ds = Dataset(
            nombre=nombre,
            datos=df,
            origen="SQLite:query",
            metadata={"formato": "SQL", "query": query}
        )
        print(f"  ✔ Query ejecutada  [{df.shape[0]} filas x {df.shape[1]} columnas]")
        return ds
 
    # ── Genérico ──────────────────────────────
 
    def cargar(self, ruta, **kwargs):
        """Detecta el formato por extensión y delega al método correcto."""
        ext = os.path.splitext(ruta)[1].lower()
        if ext == ".csv":
            return self.cargar_csv(ruta, **kwargs)
        elif ext == ".tsv":
            return self.cargar_tsv(ruta, **kwargs)
        else:
            raise ValueError(f"Formato no soportado: '{ext}'. Use .csv, .tsv o los métodos SQL.")
 
 
# ──────────────────────────────────────────────
# DatasetSplit / DataSplitter
# ──────────────────────────────────────────────
 
class DatasetSplit:
    """Contiene los subconjuntos train y test."""
 
    def __init__(self, train, test):
        self.train = train
        self.test  = test
 
    def __repr__(self):
        return (f"<DatasetSplit  train={self.train.get_dimensiones()}  "
                f"test={self.test.get_dimensiones()}>")
 
 
class DataSplitter:
    """Divide un Dataset en subconjuntos de entrenamiento y prueba."""
 
    def __init__(self, test_size=0.2, random_state=42):
        self.test_size    = test_size
        self.random_state = random_state
 
    def split(self, dataset):
        from sklearn.model_selection import train_test_split
 
        df = dataset.get_datos()
        df_train, df_test = train_test_split(
            df, test_size=self.test_size,
            random_state=self.random_state
        )
        ds_train = Dataset(
            nombre=f"{dataset.nombre}_train",
            datos=df_train.reset_index(drop=True),
            origen=dataset.origen
        )
        ds_test = Dataset(
            nombre=f"{dataset.nombre}_test",
            datos=df_test.reset_index(drop=True),
            origen=dataset.origen
        )
        print(f"  ✔ Split: train={ds_train.get_dimensiones()}  test={ds_test.get_dimensiones()}")
        return DatasetSplit(ds_train, ds_test)
    