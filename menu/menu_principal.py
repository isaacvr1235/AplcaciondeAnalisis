"""
menu/menu_principal.py
Menú interactivo principal de la aplicación.
Orquesta todas las funcionalidades delegando a cada módulo.
Todo es dinámico: el usuario elige rutas, archivos y configuraciones.
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore")

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DIR)

from data.data import DataLoader, Dataset
from visualization.visualizador import Visualizador
from data.nosql_simulator import SimuladorNoSQL
from database.connector import ConectorSQL
from menu.scraping_menu import wizard_scraping
from utils.helpers import (
    titulo_seccion, mostrar_exito, mostrar_error, mostrar_advertencia,
    mostrar_info, pedir_input, pedir_si_no, pedir_opcion, pausar,
    validar_ruta_archivo, SEPARATOR, pedir_entero
)
from utils.helpers import (
    titulo_seccion, mostrar_exito, mostrar_error, mostrar_advertencia,
    mostrar_info, pedir_input, pedir_si_no, pedir_opcion, pausar,
    validar_ruta_archivo, SEPARATOR

)

OUTPUT = os.path.join(DIR, "output")
os.makedirs(OUTPUT, exist_ok=True)

viz    = Visualizador(output_dir=OUTPUT)
loader = DataLoader()

EXTENSIONES_VALIDAS = {".csv", ".tsv", ".txt", ".xlsx", ".xls", ".json"}

# ── Almacén global ────────────────────────────────────
datasets_cargados = {}
conector_sql = ConectorSQL()


# ══════════════════════════════════════════════════════════════
# 1. CARGA DE ARCHIVOS (dinámica)
# ══════════════════════════════════════════════════════════════

def opcion_cargar_archivo():
    """Carga cualquier archivo de datos pidiendo la ruta al usuario."""
    titulo_seccion("Carga de archivo de datos")

    print(f"\n  Formatos soportados: {', '.join(sorted(EXTENSIONES_VALIDAS))}")
    print(f"  Puede usar rutas absolutas o relativas.\n")

    ruta = pedir_input("Ruta del archivo")

    # Validar existencia y extensión
    valido, msg = validar_ruta_archivo(ruta, EXTENSIONES_VALIDAS)
    if not valido:
        mostrar_error(msg)
        return

    # Si es Excel con múltiples hojas, dejar que el usuario elija
    ext = os.path.splitext(ruta)[1].lower()
    hoja = None
    if ext in (".xlsx", ".xls"):
        try:
            import pandas as pd
            xls = pd.ExcelFile(ruta)
            hojas = xls.sheet_names
        except ValueError:
            mostrar_error("El archivo parece estar corrupto o no tiene un formato de Excel válido.")
            return
        except ImportError:
            mostrar_error("Falta la librería openpyxl o pandas para leer archivos Excel.")
            return
        except Exception as e:
            mostrar_error(f"Error al inspeccionar el archivo Excel: {e}")
            return
            
        if len(hojas) > 1:
            
            print(f"\n  El archivo tiene {len(hojas)} hojas: {hojas}")
            opciones_hojas = {str(i+1): h for i, h in enumerate(hojas)}
            opciones_hojas[str(len(hojas)+1)] = "Cargar todas las hojas por separado"
            
            # Iniciamos el bucle infinito para obligar a una respuesta válida
            while True:
                sel = pedir_opcion(opciones_hojas, "¿Qué hoja desea cargar?")

                if sel == str(len(hojas)+1):
                    # Cargar todas
                    for h in hojas:
                        ds = loader.cargar_excel(ruta, hoja=h)
                        clave = _generar_clave(ds.nombre)
                        datasets_cargados[clave] = ds
                        ds.info()
                        print(f"  Vista previa de '{h}':")
                        print(ds.head(5).to_string(index=False))
                        print()
                    mostrar_exito(f"Se cargaron {len(hojas)} hojas a memoria.")
                    _preguntar_eda_post_carga()
                    return
                else:
                    hoja = opciones_hojas.get(sel)
                    if hoja:
                        # Si la hoja es válida, rompemos el bucle y continuamos con la carga abajo
                        break 
                    else:
                        mostrar_error("Opción de hoja no válida. Por favor, intente de nuevo.")

    # Cargar archivo
    try:
        if hoja:
            ds = loader.cargar_excel(ruta, hoja=hoja)
        else:
            ds = loader.cargar(ruta)
    except Exception as e:
        mostrar_error(f"No se pudo cargar el archivo: {e}")
        return

    # Asignar nombre y guardar
    nombre_sugerido = os.path.splitext(os.path.basename(ruta))[0]
    nombre = pedir_input("Nombre para este dataset", default=nombre_sugerido)
    clave = _generar_clave(nombre)
    datasets_cargados[clave] = ds

    # Mostrar info y preview
    ds.info()
    print("  Vista previa (primeras 5 filas):")
    print(ds.head(5).to_string(index=False))
    mostrar_exito(f"Dataset almacenado como '{clave}'")

    _preguntar_eda_post_carga(clave)


def _generar_clave(nombre):
    """Genera una clave única para el diccionario de datasets."""
    clave = nombre.lower().replace(" ", "_")
    if clave in datasets_cargados:
        i = 2
        while f"{clave}_{i}" in datasets_cargados:
            i += 1
        clave = f"{clave}_{i}"
    return clave


def _preguntar_eda_post_carga(clave=None):
    """Después de cargar datos, pregunta si quiere hacer EDA."""
    if pedir_si_no("¿Desea realizar análisis exploratorio (EDA) sobre estos datos?", default="n"):
        if clave and clave in datasets_cargados:
            _ejecutar_eda_sobre_dataset(clave)
        else:
            opcion_eda()


# ══════════════════════════════════════════════════════════════
# 2. CONEXIÓN SQL (dinámica)
# ══════════════════════════════════════════════════════════════

def opcion_conexion_sql():
    """Conexión dinámica a base de datos SQL (SQLite / MySQL / PostgreSQL)."""
    global conector_sql

    if conector_sql.esta_conectado():
        mostrar_info(f"Ya existe una conexión activa ({conector_sql.motor}).")
        op = pedir_opcion({
            "1": "Explorar la conexión actual",
            "2": "Cerrar y conectar a otra BD",
            "0": "Volver",
        }, "¿Qué desea hacer?")

        if op == "0":
            return
        elif op == "1":
            lanzar_eda = conector_sql.explorar_interactivo(datasets_cargados)
            if lanzar_eda:
                opcion_eda()
            return
        else:
            conector_sql.cerrar()

    exito = conector_sql.conectar_interactivo()
    if not exito:
        return

    if pedir_si_no("¿Desea visualizar información de la base de datos?"):
        lanzar_eda = conector_sql.explorar_interactivo(datasets_cargados)
        if lanzar_eda:
            opcion_eda()


# ══════════════════════════════════════════════════════════════
# 3. EDA (dinámico)
# ══════════════════════════════════════════════════════════════

def opcion_eda():
    """Análisis Exploratorio de Datos — completamente dinámico."""
    titulo_seccion("Análisis Exploratorio de Datos (EDA)")

    if not datasets_cargados:
        mostrar_advertencia("No hay datasets cargados en memoria.")
        mostrar_info("Primero cargue datos con la opción 1 (Archivo), 2 (SQL), 4 (NoSQL) o 5 (Web Scraping).")
        return

    while True:
        print("\n  ¿Sobre cuál dataset desea ejecutar el EDA?")

        # Construir menú dinámico con los datasets disponibles
        opciones = {}
        for i, (clave, ds) in enumerate(datasets_cargados.items(), 1):
            filas, cols = ds.get_dimensiones()
            opciones[str(i)] = f"{clave}  ({filas} filas × {cols} cols) [{ds.origen}]"

        n = len(opciones)
        opciones[str(n + 1)] = "EDA sobre TODOS los datasets cargados"
        opciones["0"] = "Volver al menú principal"

        op = pedir_opcion(opciones, "Seleccione dataset")

        if op == "0":
            break

        elif op == str(n + 1):
            # EDA sobre todos
            for clave in datasets_cargados:
                _ejecutar_eda_sobre_dataset(clave)

        else:
            # EDA sobre uno específico
            clave = list(datasets_cargados.keys())[int(op) - 1]
            _ejecutar_eda_sobre_dataset(clave)


def _ejecutar_eda_sobre_dataset(clave):
    """Ejecuta EDA sobre un dataset específico."""
    ds = datasets_cargados[clave]
    print(f"\n  [EDA] {ds.nombre} ({clave})")

    prefijo = clave.replace(" ", "_")
    viz.eda_completo(ds, prefijo=prefijo)
    mostrar_exito(f"EDA completado para '{clave}'. Gráficos guardados en: {OUTPUT}")


# ══════════════════════════════════════════════════════════════
# 4. NOSQL (simulación)
# ══════════════════════════════════════════════════════════════

def opcion_nosql():
    """Simulación de datos NoSQL."""
    titulo_seccion("Simulación de datos con estructura NoSQL")

  # Permitir configurar la cantidad de documentos forzando números enteros
    n_est = pedir_entero("¿Cuántos documentos de estudiantes generar?", default="15")
    n_cur = pedir_entero("¿Cuántos documentos de cursos generar?", default="12")
    seed = pedir_entero("Semilla aleatoria (para reproducibilidad)", default="42")
    
    sim = SimuladorNoSQL(seed=seed)

    print(f"\n  Generando {n_est} estudiantes y {n_cur} cursos...\n")
    docs_est = sim.generar_estudiantes(n_est)
    docs_cur = sim.generar_cursos(n_cur)

    # Guardar JSON
    import json
    os.makedirs(OUTPUT, exist_ok=True)
    ruta_est = os.path.join(OUTPUT, "nosql_estudiantes.json")
    ruta_cur = os.path.join(OUTPUT, "nosql_cursos.json")
    with open(ruta_est, "w", encoding="utf-8") as f:
        json.dump(docs_est, f, ensure_ascii=False, indent=2)
    with open(ruta_cur, "w", encoding="utf-8") as f:
        json.dump(docs_cur, f, ensure_ascii=False, indent=2)
    mostrar_exito(f"JSON guardados en: {OUTPUT}")

    # Mostrar ejemplos
    print("\n  ── Ejemplo de documento (estudiante) ──")
    sim.mostrar_ejemplo_documento(docs_est[0])

    print("\n  ── Ejemplo de documento (curso) ──")
    sim.mostrar_ejemplo_documento(docs_cur[0])

    # Aplanar a DataFrames
    df_est = sim.aplanar_estudiantes(docs_est)
    df_cur = sim.aplanar_cursos(docs_cur)

    ds_est = Dataset(
        nombre="NoSQL_Estudiantes", datos=df_est,
        origen="Simulación NoSQL",
        metadata={"formato": "NoSQL/JSON", "n_documentos": len(docs_est)}
    )
    ds_cur = Dataset(
        nombre="NoSQL_Cursos", datos=df_cur,
        origen="Simulación NoSQL",
        metadata={"formato": "NoSQL/JSON", "n_documentos": len(docs_cur)}
    )

    print("\n  ── DataFrame: Estudiantes (aplanado) ──")
    ds_est.info()
    print(ds_est.head(5).to_string(index=False))

    print("\n  ── DataFrame: Cursos (aplanado) ──")
    ds_cur.info()
    print(ds_cur.head(5).to_string(index=False))

    datasets_cargados["nosql_estudiantes"] = ds_est
    datasets_cargados["nosql_cursos"] = ds_cur

    # Preguntar EDA — nunca automático
    if pedir_si_no("¿Desea realizar análisis exploratorio de los datos NoSQL?", default="n"):
        _ejecutar_eda_sobre_dataset("nosql_estudiantes")
        _ejecutar_eda_sobre_dataset("nosql_cursos")
    else:
        mostrar_info("EDA omitido. Puede ejecutarlo después desde la opción 3.")


# ══════════════════════════════════════════════════════════════
# 5. WEB SCRAPING
# ══════════════════════════════════════════════════════════════

def opcion_webscraping():
    """Web Scraping interactivo — wizard paso a paso."""
    resultado = wizard_scraping(datasets_cargados, output_dir=OUTPUT)

    # Si el wizard retorna datasets y el usuario pidió EDA
    if resultado:
        for clave in resultado:
            if clave in datasets_cargados:
                _ejecutar_eda_sobre_dataset(clave)


# ══════════════════════════════════════════════════════════════
# 6. VER DATASETS
# ══════════════════════════════════════════════════════════════

def opcion_ver_datasets():
    """Muestra los datasets actualmente cargados en memoria."""
    titulo_seccion("Datasets cargados en memoria")

    if not datasets_cargados:
        print("\n  (Sin datasets cargados. Ejecute alguna opción primero.)\n")
        return

    for clave, ds in datasets_cargados.items():
        filas, cols = ds.get_dimensiones()
        print(f"  • {clave:30s}  →  {filas:>5} filas × {cols} columnas  [{ds.origen}]")
    print()

    if pedir_si_no("¿Desea ver detalle de algún dataset?", default="n"):
        opciones = {str(i+1): c for i, c in enumerate(datasets_cargados.keys())}
        opciones["0"] = "Volver"
        sel = pedir_opcion(opciones, "Seleccione dataset")
        if sel != "0":
            clave = opciones[sel]
            ds = datasets_cargados[clave]
            ds.info()
            n = pedir_input("¿Cuántas filas mostrar?", default="10")
            try:
                n = int(n)
            except ValueError:
                n = 10
            print(ds.head(n).to_string(index=False))


# ══════════════════════════════════════════════════════════════
# MENÚ PRINCIPAL
# ══════════════════════════════════════════════════════════════

def menu_principal():
    menu_texto = """
╔══════════════════════════════════════════════════════════╗
║     APLICACIÓN DE ANÁLISIS DE DATOS — IPN / ESCOM       ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  1. Cargar archivo (CSV, TSV, Excel, JSON)               ║
║  2. Conexión a base de datos SQL                         ║
║  3. Análisis Exploratorio de Datos (EDA)                 ║
║  4. Simulación de datos NoSQL                            ║
║  5. Web Scraping (datos no estructurados)                ║
║  6. Ver datasets cargados                                ║
║  0. Salir                                                ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
    opciones = {
        "1": opcion_cargar_archivo,
        "2": opcion_conexion_sql,
        "3": opcion_eda,
        "4": opcion_nosql,
        "5": opcion_webscraping,
        "6": opcion_ver_datasets,
    }

    while True:
        print(menu_texto)
        opcion = input("  Seleccione una opción [0-6]: ").strip()

        if opcion == "0":
            print("\n  ¡Hasta luego!\n")
            break
        elif opcion in opciones:
            try:
                opciones[opcion]()
            except Exception as e:
                mostrar_error(f"Error: {e}")
        else:
            mostrar_advertencia("Opción no válida. Intente de nuevo.")

        pausar()
