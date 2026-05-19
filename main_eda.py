import os
import sys
import sqlite3
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)

from data.data import DataLoader, Dataset
from visualization.visualizador import Visualizador
from data.nosql_simulator import SimuladorNoSQL
from data.web_scraper import WebScraper

OUTPUT = os.path.join(DIR, "output")
os.makedirs(OUTPUT, exist_ok=True)

viz    = Visualizador(output_dir=OUTPUT)
loader = DataLoader()

SEPARATOR = "\n" + "=" * 60

# ── Variables globales para almacenar datasets cargados ──
datasets_cargados = {}
DB_PATH = os.path.join(OUTPUT, "universidad.db")


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE CADA OPCIÓN
# ══════════════════════════════════════════════════════════════

def opcion_cargar_csv():
    """PUNTO 1 — Carga exitosa de archivos .csv"""
    print(SEPARATOR)
    print("  PUNTO 1 — Carga de archivos CSV")
    print("=" * 60)

    ruta = os.path.join(DIR, "estudiantes.csv")
    ds = loader.cargar_csv(ruta, nombre="Estudiantes")
    ds.info()
    print("  Vista previa (head):")
    print(ds.head(5).to_string(index=False))
    datasets_cargados["csv_estudiantes"] = ds
    print("\n  ✔ Dataset almacenado como 'csv_estudiantes'")


def opcion_cargar_tsv():
    """PUNTO 2 — Carga exitosa de archivos .tsv"""
    print(SEPARATOR)
    print("  PUNTO 2 — Carga de archivos TSV")
    print("=" * 60)

    ruta = os.path.join(DIR, "calificaciones.tsv")
    ds = loader.cargar_tsv(ruta, nombre="Calificaciones")
    ds.info()
    print("  Vista previa (head):")
    print(ds.head(5).to_string(index=False))
    datasets_cargados["tsv_calificaciones"] = ds
    print("\n  ✔ Dataset almacenado como 'tsv_calificaciones'")


def opcion_conexion_sql():
    """PUNTO 3 — Conexión a base de datos SQL y PUNTO 4 — Visualización de tablas"""
    print(SEPARATOR)
    print("  PUNTO 3 — Conexión a base de datos SQL (SQLite)")
    print("=" * 60)

    # Asegurar que existan los datasets fuente
    if "csv_estudiantes" not in datasets_cargados:
        print("  ⚠ Primero cargando CSV de estudiantes...")
        ruta_csv = os.path.join(DIR, "estudiantes.csv")
        datasets_cargados["csv_estudiantes"] = loader.cargar_csv(ruta_csv, nombre="Estudiantes")

    if "tsv_calificaciones" not in datasets_cargados:
        print("  ⚠ Primero cargando TSV de calificaciones...")
        ruta_tsv = os.path.join(DIR, "calificaciones.tsv")
        datasets_cargados["tsv_calificaciones"] = loader.cargar_tsv(ruta_tsv, nombre="Calificaciones")

    # Crear y poblar la BD
    conn_build = sqlite3.connect(DB_PATH)
    datasets_cargados["csv_estudiantes"].get_datos().to_sql(
        "estudiantes", conn_build, if_exists="replace", index=False
    )

    df_cal = datasets_cargados["tsv_calificaciones"].get_datos().copy()
    for col in ["Parcial1", "Parcial2", "Final"]:
        df_cal[col] = pd.to_numeric(df_cal[col], errors="coerce")
    df_cal.to_sql("calificaciones", conn_build, if_exists="replace", index=False)
    conn_build.commit()
    conn_build.close()

    # Conectar y visualizar
    conn = loader.conectar_sqlite(DB_PATH)
    print(f"\n  Conexión activa: {DB_PATH}")

    print(SEPARATOR)
    print("  PUNTO 4 — Visualización de tablas SQL")
    print("=" * 60)

    tablas = loader.listar_tablas_sql(conn)
    print(f"\n  Tablas disponibles: {tablas}\n")

    for tabla in tablas:
        ds_sql = loader.cargar_tabla_sql(conn, tabla)
        ds_sql.info()
        print(f"  Muestra de '{tabla}':")
        print(ds_sql.head(3).to_string(index=False))
        print()
        datasets_cargados[f"sql_{tabla}"] = ds_sql

    # Consulta SQL de ejemplo
    print("  Consulta SQL: promedio de calificación final por curso")
    ds_query = loader.ejecutar_query_sql(
        conn,
        """
        SELECT Curso,
               ROUND(AVG(Final), 2) AS Promedio_Final,
               COUNT(*) AS Registros
        FROM calificaciones
        GROUP BY Curso
        ORDER BY Promedio_Final DESC
        """,
        nombre="Promedio_por_Curso"
    )
    print(ds_query.get_datos().to_string(index=False))
    conn.close()


def opcion_eda():
    """PUNTO 5 — Análisis Exploratorio de Datos (EDA)"""
    print(SEPARATOR)
    print("  PUNTO 5 — EDA por fuente de datos")
    print("=" * 60)

    # Cargar datos si no existen
    if "csv_estudiantes" not in datasets_cargados:
        ruta_csv = os.path.join(DIR, "estudiantes.csv")
        datasets_cargados["csv_estudiantes"] = loader.cargar_csv(ruta_csv, nombre="Estudiantes")

    if "tsv_calificaciones" not in datasets_cargados:
        ruta_tsv = os.path.join(DIR, "calificaciones.tsv")
        datasets_cargados["tsv_calificaciones"] = loader.cargar_tsv(ruta_tsv, nombre="Calificaciones")

    sub_menu = """
  ¿Sobre cuál fuente desea ejecutar el EDA?
  1. CSV  — Estudiantes
  2. TSV  — Calificaciones
  3. SQL  — Tablas de la BD
  4. Todos los anteriores
  5. Volver al menú principal
"""
    while True:
        print(sub_menu)
        op = input("  Seleccione opción [1-5]: ").strip()

        if op == "1":
            print("\n  [EDA] Estudiantes (CSV)")
            viz.eda_completo(datasets_cargados["csv_estudiantes"], prefijo="csv_estudiantes")

        elif op == "2":
            print("\n  [EDA] Calificaciones (TSV)")
            viz.eda_completo(datasets_cargados["tsv_calificaciones"], prefijo="tsv_calificaciones")

        elif op == "3":
            if not os.path.exists(DB_PATH):
                print("  ⚠ Primero debe ejecutar la opción 3 (Conexión SQL).")
                continue
            conn2 = loader.conectar_sqlite(DB_PATH)
            ds_sql_est = loader.cargar_tabla_sql(conn2, "estudiantes", nombre="SQL_Estudiantes")
            ds_sql_cal = loader.cargar_tabla_sql(conn2, "calificaciones", nombre="SQL_Calificaciones")
            conn2.close()
            print("\n  [EDA] Tabla SQL: estudiantes")
            viz.eda_completo(ds_sql_est, prefijo="sql_estudiantes")
            print("\n  [EDA] Tabla SQL: calificaciones")
            viz.eda_completo(ds_sql_cal, prefijo="sql_calificaciones")

        elif op == "4":
            print("\n  [EDA] CSV — Estudiantes")
            viz.eda_completo(datasets_cargados["csv_estudiantes"], prefijo="csv_estudiantes")
            print("\n  [EDA] TSV — Calificaciones")
            viz.eda_completo(datasets_cargados["tsv_calificaciones"], prefijo="tsv_calificaciones")

            if os.path.exists(DB_PATH):
                conn2 = loader.conectar_sqlite(DB_PATH)
                ds_sql_est = loader.cargar_tabla_sql(conn2, "estudiantes", nombre="SQL_Estudiantes")
                ds_sql_cal = loader.cargar_tabla_sql(conn2, "calificaciones", nombre="SQL_Calificaciones")
                conn2.close()
                print("\n  [EDA] SQL: estudiantes")
                viz.eda_completo(ds_sql_est, prefijo="sql_estudiantes")
                print("\n  [EDA] SQL: calificaciones")
                viz.eda_completo(ds_sql_cal, prefijo="sql_calificaciones")
            else:
                print("  ⚠ BD SQL no creada aún. Ejecute opción 3 primero.")

            # Gráficos adicionales
            print("\n  [Gráficos adicionales]")
            viz.top_estudiantes(
                datasets_cargados["tsv_calificaciones"].get_datos(),
                datasets_cargados["csv_estudiantes"].get_datos()
            )
            viz.promedio_por_curso(datasets_cargados["tsv_calificaciones"].get_datos())

        elif op == "5":
            break
        else:
            print("  ⚠ Opción no válida.")


def opcion_nosql():
    """PUNTO 6 — Simulación de datos NoSQL"""
    print(SEPARATOR)
    print("  PUNTO 6 — Simulación de datos con estructura NoSQL")
    print("=" * 60)

    sim = SimuladorNoSQL(seed=42)

    print("\n  Generando colecciones de documentos tipo NoSQL...\n")
    docs_est, docs_cur, ds_est, ds_cur = sim.generar_y_convertir(output_dir=OUTPUT)

    # Mostrar ejemplo de documento
    print("\n  ── Ejemplo de documento (estudiante) ──")
    sim.mostrar_ejemplo_documento(docs_est[0])

    print("\n  ── Ejemplo de documento (curso) ──")
    sim.mostrar_ejemplo_documento(docs_cur[0])

    # Mostrar DataFrames resultantes
    print("\n  ── DataFrame: Estudiantes (aplanado) ──")
    ds_est.info()
    print(ds_est.head(5).to_string(index=False))

    print("\n  ── DataFrame: Cursos (aplanado) ──")
    ds_cur.info()
    print(ds_cur.head(5).to_string(index=False))

    datasets_cargados["nosql_estudiantes"] = ds_est
    datasets_cargados["nosql_cursos"] = ds_cur

    # EDA de los datos NoSQL
    print("\n  ── EDA de datos NoSQL ──")
    viz.eda_completo(ds_est, prefijo="nosql_estudiantes")
    viz.eda_completo(ds_cur, prefijo="nosql_cursos")


def opcion_webscraping():
    """PUNTO 7 — Web Scraping de datos no estructurados"""
    print(SEPARATOR)
    print("  PUNTO 7 — Web Scraping de datos no estructurados")
    print("=" * 60)

    scraper = WebScraper()

    # GitHub Trending: datos no estructurados (HTML) → DataFrame
    url = "https://github.com/trending"

    print(f"\n  Fuente: {url}\n")

    try:
        resultado = scraper.scraping_completo(url, nombre="GitHub_Trending")

        # Mostrar repositorios trending extraídos
        if resultado["repos"]:
            print("\n  ── Repositorios trending (datos no estructurados → DataFrame) ──")
            resultado["repos"].info()
            print(resultado["repos"].head(10).to_string(index=False))
            datasets_cargados["ws_repos_trending"] = resultado["repos"]

        # Mostrar texto estructurado
        if resultado["encabezados"]:
            print("\n  ── Encabezados extraídos (como DataFrame) ──")
            resultado["encabezados"].info()
            print(resultado["encabezados"].head(10).to_string(index=False))
            datasets_cargados["ws_encabezados"] = resultado["encabezados"]

        if resultado["parrafos"]:
            print("\n  ── Párrafos extraídos (como DataFrame) ──")
            resultado["parrafos"].info()
            print(resultado["parrafos"].head(5).to_string(index=False))
            datasets_cargados["ws_parrafos"] = resultado["parrafos"]

        print(SEPARATOR)
        print("  ✔ Datos no estructurados convertidos a DataFrames exitosamente.")

    except Exception as e:
        print(f"\n  ✖ Error durante el web scraping: {e}")
        print("  Verifique su conexión a internet e intente nuevamente.")


def opcion_ver_datasets():
    """Muestra los datasets actualmente cargados en memoria."""
    print(SEPARATOR)
    print("  Datasets cargados en memoria")
    print("=" * 60)

    if not datasets_cargados:
        print("\n  (Sin datasets cargados. Ejecute alguna opción primero.)\n")
        return

    for clave, ds in datasets_cargados.items():
        filas, cols = ds.get_dimensiones()
        print(f"  • {clave:30s}  →  {filas:>5} filas × {cols} columnas  [{ds.origen}]")
    print()


# ══════════════════════════════════════════════════════════════
# MENÚ PRINCIPAL
# ══════════════════════════════════════════════════════════════

def menu_principal():
    menu = """
╔══════════════════════════════════════════════════════════╗
║     APLICACIÓN DE ANÁLISIS DE DATOS — IPN / ESCOM       ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  1. Cargar archivo CSV                                   ║
║  2. Cargar archivo TSV                                   ║
║  3. Conexión SQL + Visualización de tablas                ║
║  4. Análisis Exploratorio de Datos (EDA)                 ║
║  5. Simulación de datos NoSQL                            ║
║  6. Web Scraping (datos no estructurados)                ║
║  7. Ver datasets cargados                                ║
║  0. Salir                                                ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
    opciones = {
        "1": opcion_cargar_csv,
        "2": opcion_cargar_tsv,
        "3": opcion_conexion_sql,
        "4": opcion_eda,
        "5": opcion_nosql,
        "6": opcion_webscraping,
        "7": opcion_ver_datasets,
    }

    while True:
        print(menu)
        opcion = input("  Seleccione una opción [0-7]: ").strip()

        if opcion == "0":
            print("\n  ¡Hasta luego!\n")
            break
        elif opcion in opciones:
            try:
                opciones[opcion]()
            except Exception as e:
                print(f"\n  ✖ Error: {e}\n")
        else:
            print("\n  ⚠ Opción no válida. Intente de nuevo.")

        input("\n  Presione ENTER para continuar...")


# ══════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    menu_principal()
