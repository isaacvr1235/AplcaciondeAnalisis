"""
database/connector.py
Conexión dinámica a bases de datos SQL.
Soporta SQLite, MySQL y PostgreSQL.
"""

import os
import sqlite3
import pandas as pd
from data.data import Dataset
from utils.helpers import (
    titulo_seccion, mostrar_exito, mostrar_error, mostrar_advertencia,
    mostrar_info, pedir_input, pedir_si_no, pedir_opcion, validar_puerto,
    SEPARATOR
)


class ConectorSQL:
    """
    Gestiona conexiones dinámicas a bases de datos SQL.
    Soporta SQLite, MySQL y PostgreSQL.
    """

    MOTORES_SOPORTADOS = {
        "1": {"nombre": "SQLite",     "puerto_default": None},
        "2": {"nombre": "MySQL",      "puerto_default": "3306"},
        "3": {"nombre": "PostgreSQL", "puerto_default": "5432"},
    }

    def __init__(self):
        self.conexion = None
        self.motor = None
        self.config = {}
        self._engine = None  # SQLAlchemy engine (para MySQL/PostgreSQL)

    # ── Conexión interactiva ──────────────────────

    def conectar_interactivo(self):
        """
        Solicita credenciales al usuario y establece la conexión.
        Retorna True si la conexión fue exitosa, False en caso contrario.
        """
        titulo_seccion("Conexión a Base de Datos SQL")

        print("\n  Seleccione el tipo de base de datos:")
        motor_opciones = {k: v["nombre"] for k, v in self.MOTORES_SOPORTADOS.items()}
        motor_opciones["0"] = "Cancelar"
        seleccion = pedir_opcion(motor_opciones, "Tipo de BD")

        if seleccion == "0":
            mostrar_info("Conexión cancelada.")
            return False

        motor_info = self.MOTORES_SOPORTADOS[seleccion]
        self.motor = motor_info["nombre"]

        print(f"\n  Motor seleccionado: {self.motor}")
        print(f"  {'─' * 40}")

        try:
            if self.motor == "SQLite":
                return self._conectar_sqlite()
            elif self.motor == "MySQL":
                return self._conectar_mysql(motor_info["puerto_default"])
            elif self.motor == "PostgreSQL":
                return self._conectar_postgresql(motor_info["puerto_default"])
        except Exception as e:
            mostrar_error(f"Error de conexión: {e}")
            self.conexion = None
            self.motor = None
            return False

    # ── SQLite ────────────────────────────────────

    def _conectar_sqlite(self):
        """Conexión a SQLite: pide ruta del archivo .db"""
        print("\n  Opciones para SQLite:")
        op = pedir_opcion({
            "1": "Usar archivo existente",
            "2": "Crear nueva base de datos",
        }, "Seleccione")

        if op == "1":
            ruta = pedir_input("Ruta del archivo .db")
            if not os.path.isfile(ruta):
                mostrar_error(f"Archivo no encontrado: {ruta}")
                return False
        else:
            ruta = pedir_input("Nombre del archivo a crear (ej: mi_base.db)")
            if not ruta.endswith(".db"):
                ruta += ".db"
            directorio = pedir_input("Directorio donde guardarlo", default="output")
            os.makedirs(directorio, exist_ok=True)
            ruta = os.path.join(directorio, ruta)

        self.conexion = sqlite3.connect(ruta)
        self.config = {"ruta": ruta}
        mostrar_exito(f"Conexión SQLite establecida: {ruta}")
        return True

    # ── MySQL ─────────────────────────────────────

    def _conectar_mysql(self, puerto_default):
        """Conexión a MySQL: pide host, puerto, usuario, contraseña, base de datos."""
        try:
            import pymysql
        except ImportError:
            mostrar_error("El módulo 'pymysql' no está instalado.")
            mostrar_info("Instálelo con: pip install pymysql")
            return False

        config = self._pedir_credenciales(puerto_default)
        if not config:
            return False

        # Intentar conexión
        mostrar_info("Intentando conexión a MySQL...")
        self.conexion = pymysql.connect(
            host=config["host"],
            port=int(config["puerto"]),
            user=config["usuario"],
            password=config["contraseña"],
            database=config["base_datos"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
        )
        self.config = config
        self._crear_engine_sqlalchemy("mysql+pymysql", config)
        mostrar_exito(f"Conexión MySQL establecida → {config['host']}:{config['puerto']}/{config['base_datos']}")
        return True

    # ── PostgreSQL ────────────────────────────────

    def _conectar_postgresql(self, puerto_default):
        """Conexión a PostgreSQL: pide host, puerto, usuario, contraseña, base de datos."""
        try:
            import psycopg2
        except ImportError:
            mostrar_error("El módulo 'psycopg2' no está instalado.")
            mostrar_info("Instálelo con: pip install psycopg2-binary")
            return False

        config = self._pedir_credenciales(puerto_default)
        if not config:
            return False

        mostrar_info("Intentando conexión a PostgreSQL...")
        self.conexion = psycopg2.connect(
            host=config["host"],
            port=int(config["puerto"]),
            user=config["usuario"],
            password=config["contraseña"],
            dbname=config["base_datos"],
            connect_timeout=10,
        )
        self.conexion.autocommit = True
        self.config = config
        self._crear_engine_sqlalchemy("postgresql+psycopg2", config)
        mostrar_exito(f"Conexión PostgreSQL establecida → {config['host']}:{config['puerto']}/{config['base_datos']}")
        return True

    # ── Solicitar credenciales ────────────────────

    def _pedir_credenciales(self, puerto_default):
        """Pide host, puerto, usuario, contraseña y base de datos."""
        print()
        host = pedir_input("Host", default="localhost")
        puerto = pedir_input(f"Puerto", default=puerto_default)
        if not validar_puerto(puerto):
            mostrar_error(f"Puerto inválido: {puerto}")
            return None
        usuario = pedir_input("Usuario")
        import getpass
        try:
            contraseña = getpass.getpass("  Contraseña: ")
        except Exception:
            contraseña = pedir_input("Contraseña")
        base_datos = pedir_input("Nombre de la base de datos")

        return {
            "host": host,
            "puerto": puerto,
            "usuario": usuario,
            "contraseña": contraseña,
            "base_datos": base_datos,
        }

    def _crear_engine_sqlalchemy(self, driver, config):
        """Crea un engine de SQLAlchemy para lectura con pandas."""
        try:
            from sqlalchemy import create_engine
            url = (f"{driver}://{config['usuario']}:{config['contraseña']}"
                   f"@{config['host']}:{config['puerto']}/{config['base_datos']}")
            self._engine = create_engine(url, pool_pre_ping=True)
        except Exception as e:
            mostrar_advertencia(f"SQLAlchemy engine no creado (lectura aún posible): {e}")
            self._engine = None

    # ── Operaciones sobre la BD conectada ─────────

    def esta_conectado(self):
        """Retorna True si hay una conexión activa."""
        return self.conexion is not None

    def cerrar(self):
        """Cierra la conexión actual."""
        if self.conexion:
            try:
                self.conexion.close()
            except Exception:
                pass
            self.conexion = None
            self.motor = None
            self._engine = None
            mostrar_info("Conexión cerrada.")

    def listar_tablas(self):
        """Retorna la lista de tablas de la BD conectada."""
        if not self.esta_conectado():
            mostrar_error("No hay conexión activa.")
            return []

        if self.motor == "SQLite":
            cur = self.conexion.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            tablas = [r[0] for r in cur.fetchall()]

        elif self.motor == "MySQL":
            cur = self.conexion.cursor()
            cur.execute("SHOW TABLES;")
            tablas = [list(r.values())[0] for r in cur.fetchall()]

        elif self.motor == "PostgreSQL":
            cur = self.conexion.cursor()
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' ORDER BY table_name;
            """)
            tablas = [r[0] for r in cur.fetchall()]
        else:
            tablas = []

        return tablas

    def cargar_tabla(self, tabla, nombre=None):
        """Lee una tabla completa y retorna un Dataset."""
        if not self.esta_conectado():
            mostrar_error("No hay conexión activa.")
            return None

        if self._engine:
            df = pd.read_sql_table(tabla, self._engine)
        elif self.motor == "SQLite":
            df = pd.read_sql_query(f"SELECT * FROM [{tabla}]", self.conexion)
        else:
            df = pd.read_sql_query(f"SELECT * FROM \"{tabla}\"", self.conexion)

        nombre = nombre or tabla
        ds = Dataset(
            nombre=nombre,
            datos=df,
            origen=f"{self.motor}:{tabla}",
            metadata={"formato": "SQL", "motor": self.motor, "tabla": tabla}
        )
        mostrar_exito(f"Tabla '{tabla}' cargada  [{df.shape[0]} filas × {df.shape[1]} columnas]")
        return ds

    def ejecutar_query(self, query, nombre="query_result"):
        """Ejecuta una consulta SQL y retorna un Dataset."""
        if not self.esta_conectado():
            mostrar_error("No hay conexión activa.")
            return None

        if self._engine:
            df = pd.read_sql_query(query, self._engine)
        else:
            df = pd.read_sql_query(query, self.conexion)

        ds = Dataset(
            nombre=nombre,
            datos=df,
            origen=f"{self.motor}:query",
            metadata={"formato": "SQL", "motor": self.motor, "query": query}
        )
        mostrar_exito(f"Query ejecutada  [{df.shape[0]} filas × {df.shape[1]} columnas]")
        return ds

    def obtener_esquema(self, tabla):
        """Muestra la estructura/esquema de una tabla."""
        if not self.esta_conectado():
            return

        print(f"\n  Esquema de '{tabla}':")
        print(f"  {'─' * 50}")

        try:
            if self.motor == "SQLite":
                cur = self.conexion.cursor()
                cur.execute(f"PRAGMA table_info([{tabla}]);")
                columnas = cur.fetchall()
                print(f"  {'Columna':<25} {'Tipo':<15} {'Nulo':<6} {'PK'}")
                print(f"  {'─'*25} {'─'*15} {'─'*6} {'─'*3}")
                for col in columnas:
                    print(f"  {col[1]:<25} {col[2]:<15} {'Sí' if col[3]==0 else 'No':<6} {'✔' if col[5] else ''}")

            elif self.motor == "MySQL":
                cur = self.conexion.cursor()
                cur.execute(f"DESCRIBE `{tabla}`;")
                columnas = cur.fetchall()
                print(f"  {'Columna':<25} {'Tipo':<20} {'Nulo':<6} {'Key':<5} {'Default'}")
                print(f"  {'─'*25} {'─'*20} {'─'*6} {'─'*5} {'─'*10}")
                for col in columnas:
                    print(f"  {col['Field']:<25} {col['Type']:<20} {col['Null']:<6} "
                          f"{col['Key']:<5} {col.get('Default', '')}")

            elif self.motor == "PostgreSQL":
                cur = self.conexion.cursor()
                cur.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{tabla}' AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """)
                columnas = cur.fetchall()
                print(f"  {'Columna':<25} {'Tipo':<20} {'Nulo':<6} {'Default'}")
                print(f"  {'─'*25} {'─'*20} {'─'*6} {'─'*15}")
                for col in columnas:
                    print(f"  {col[0]:<25} {col[1]:<20} {col[2]:<6} {col[3] or ''}")

        except Exception as e:
            mostrar_error(f"No se pudo obtener esquema: {e}")

    # ── Exploración interactiva post-conexión ─────

    def explorar_interactivo(self, datasets_cargados=None):
        """
        Después de conectarse, permite explorar la BD interactivamente:
        listar tablas, ver preview, ver esquema, cargar a memoria, ejecutar queries.

        Args:
            datasets_cargados: dict donde almacenar los datasets cargados.
        """
        if not self.esta_conectado():
            mostrar_error("No hay conexión activa.")
            return

        if datasets_cargados is None:
            datasets_cargados = {}

        tablas = self.listar_tablas()
        if not tablas:
            mostrar_advertencia("La base de datos no tiene tablas.")
            return

        mostrar_exito(f"Tablas encontradas: {tablas}")

        opciones_explorar = {
            "1": "Ver vista previa de una tabla",
            "2": "Ver esquema de una tabla",
            "3": "Cargar tabla(s) a memoria para análisis",
            "4": "Ejecutar consulta SQL personalizada",
            "5": "Listar tablas disponibles",
            "0": "Volver al menú principal",
        }

        while True:
            print(f"\n  ── Exploración de BD ({self.motor}) ──")
            op = pedir_opcion(opciones_explorar, "Seleccione")

            if op == "0":
                break

            elif op == "1":
                tabla = self._seleccionar_tabla(tablas)
                if tabla:
                    ds = self.cargar_tabla(tabla)
                    if ds:
                        print(f"\n  Vista previa de '{tabla}':")
                        print(ds.head(10).to_string(index=False))

            elif op == "2":
                tabla = self._seleccionar_tabla(tablas)
                if tabla:
                    self.obtener_esquema(tabla)

            elif op == "3":
                self._cargar_tablas_a_memoria(tablas, datasets_cargados)

            elif op == "4":
                print("\n  Escriba su consulta SQL (termine con ;):")
                lineas = []
                while True:
                    linea = input("  SQL> ").strip()
                    lineas.append(linea)
                    if linea.endswith(";"):
                        break
                query = " ".join(lineas)
                try:
                    ds = self.ejecutar_query(query, nombre="consulta_personalizada")
                    if ds:
                        print(ds.get_datos().to_string(index=False))
                        if pedir_si_no("¿Guardar resultado en memoria?"):
                            clave = pedir_input("Nombre para el dataset", default="query_result")
                            datasets_cargados[clave] = ds
                            mostrar_exito(f"Guardado como '{clave}'")
                except Exception as e:
                    mostrar_error(f"Error en query: {e}")

            elif op == "5":
                tablas = self.listar_tablas()
                print(f"\n  Tablas: {tablas}")

    def _seleccionar_tabla(self, tablas):
        """Presenta las tablas y pide seleccionar una."""
        opciones = {str(i+1): t for i, t in enumerate(tablas)}
        opciones["0"] = "Cancelar"
        print("\n  Tablas disponibles:")
        seleccion = pedir_opcion(opciones, "Seleccione tabla")
        if seleccion == "0":
            return None
        return opciones[seleccion]

    def _cargar_tablas_a_memoria(self, tablas, datasets_cargados):
        """Permite seleccionar tablas para cargar a memoria."""
        print("\n  ¿Qué tablas desea cargar?")
        opciones = {str(i+1): t for i, t in enumerate(tablas)}
        opciones[str(len(tablas)+1)] = "Todas"
        opciones["0"] = "Cancelar"
        seleccion = pedir_opcion(opciones, "Seleccione")

        if seleccion == "0":
            return

        if seleccion == str(len(tablas)+1):
            # Cargar todas
            for tabla in tablas:
                ds = self.cargar_tabla(tabla)
                if ds:
                    clave = f"sql_{tabla}"
                    datasets_cargados[clave] = ds
            mostrar_exito(f"Se cargaron {len(tablas)} tablas a memoria.")
        else:
            tabla = opciones[seleccion]
            ds = self.cargar_tabla(tabla)
            if ds:
                clave = f"sql_{tabla}"
                datasets_cargados[clave] = ds

        # Preguntar si desea EDA
        if pedir_si_no("¿Desea realizar análisis exploratorio (EDA) sobre las tablas cargadas?", default="n"):
            return True  # Señal al menú para lanzar EDA
        return False
