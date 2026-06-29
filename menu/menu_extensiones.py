"""
menu/menu_extensiones.py
Opciones del menú para las Extensiones B y E del Examen Extraordinario.

  Extensión B — Comparación automática de modelos supervisados
  Extensión E — Clustering (KMeans) y reducción de dimensionalidad (PCA / t-SNE)

Para integrar al menú principal, agrega en menu/menu_principal.py:

    from menu.menu_extensiones import opcion_modelos_supervisados, opcion_no_supervisado

Y en menu_principal() añade las nuevas entradas:
    "7": opcion_modelos_supervisados,
    "8": opcion_no_supervisado,

Y en el texto del menú:
    ║  7. Comparar modelos supervisados (Extensión B)          ║
    ║  8. Clustering y reducción de dimensionalidad (Ext. E)   ║
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DIR)

from models.models import ComparadorModelos
from visualization.analisis_no_supervisado import AnalizadorNoSupervisado
from utils.helpers import (
    titulo_seccion, mostrar_exito, mostrar_error, mostrar_advertencia,
    mostrar_info, pedir_input, pedir_si_no, pedir_opcion, pausar, pedir_entero
)

OUTPUT = os.path.join(DIR, "output")
os.makedirs(OUTPUT, exist_ok=True)


# ══════════════════════════════════════════════════════════════
# EXTENSIÓN B — Comparación de modelos supervisados
# ══════════════════════════════════════════════════════════════

def opcion_modelos_supervisados(datasets_cargados):
    """
    Extensión B: entrena y compara automáticamente 3 modelos de clasificación
    (Árbol de Decisión, Regresión Logística, Random Forest) con métricas completas.
    """
    titulo_seccion("Extensión B — Comparación de Modelos Supervisados")

    # 1. Seleccionar dataset
    if not datasets_cargados:
        mostrar_advertencia("No hay datasets cargados. Cargue datos primero (Opción 1).")
        return

    print("\n  Datasets disponibles:")
    opciones = {}
    for i, (clave, ds) in enumerate(datasets_cargados.items(), 1):
        f, c = ds.get_dimensiones()
        opciones[str(i)] = f"{clave}  ({f} filas × {c} cols)"
    opciones["0"] = "Volver"

    sel = pedir_opcion(opciones, "Seleccione el dataset para entrenar los modelos")
    if sel == "0":
        return

    clave = list(datasets_cargados.keys())[int(sel) - 1]
    ds = datasets_cargados[clave]
    df = ds.get_datos().copy()

    # 2. Seleccionar columna objetivo
    columnas = list(df.columns)
    print(f"\n  Columnas disponibles: {columnas}")
    col_objetivo = pedir_input("Nombre de la columna objetivo (variable a predecir)")

    if col_objetivo not in columnas:
        mostrar_error(f"Columna '{col_objetivo}' no encontrada en el dataset.")
        return

    # 3. Preparar X e y
    try:
        y_raw = df[col_objetivo]
        X_df  = df.drop(columns=[col_objetivo])

        # Codificar la variable objetivo si es categórica
        if y_raw.dtype == object or str(y_raw.dtype) == "category":
            le = LabelEncoder()
            y = le.fit_transform(y_raw.astype(str))
            print(f"\n  Clases codificadas: {dict(zip(le.classes_, le.transform(le.classes_)))}")
        else:
            y = y_raw.values

        # Mantener solo columnas numéricas para X
        X_df_num = X_df.select_dtypes(include="number").dropna(axis=1)

        # Codificar columnas categóricas restantes con get_dummies
        X_df_cat = X_df.select_dtypes(include=["object", "category"])
        if not X_df_cat.empty:
            X_df_cat_encoded = pd.get_dummies(X_df_cat, drop_first=True)
            X_df_final = pd.concat([X_df_num, X_df_cat_encoded], axis=1)
        else:
            X_df_final = X_df_num

        if X_df_final.shape[1] == 0:
            mostrar_error("No se encontraron columnas de entrada válidas para entrenar.")
            return

        X = X_df_final.values
        print(f"\n  Características usadas ({X_df_final.shape[1]}): {list(X_df_final.columns)}")

    except Exception as e:
        mostrar_error(f"Error al preparar los datos: {e}")
        return

    # 4. Split train/test
    test_size_str = pedir_input("Proporción de datos para prueba (ej. 0.2 = 20%)", default="0.2")
    try:
        test_size = float(test_size_str)
        if not (0.05 <= test_size <= 0.5):
            raise ValueError
    except ValueError:
        mostrar_advertencia("Valor inválido. Se usará 0.2 por defecto.")
        test_size = 0.2

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=_stratify_safe(y)
    )
    print(f"\n  Train: {X_train.shape[0]} muestras  |  Test: {X_test.shape[0]} muestras")

    # 5. Entrenar y comparar
    print(f"\n  Entrenando 3 modelos automáticamente...")
    comparador = ComparadorModelos()
    tabla = comparador.comparar(X_train, y_train, X_test, y_test)

    # 6. Mostrar resultados
    if tabla.empty:
        mostrar_error("No se pudo entrenar ningún modelo.")
        return

    print(f"\n{'─'*55}")
    print("  TABLA COMPARATIVA DE MODELOS")
    print(f"{'─'*55}")
    print(tabla.to_string(index=False))

    mejor = comparador.mejor_modelo()
    print(f"\n  🏆 Mejor modelo por F1-Score: {mejor}")

    # 7. Reporte detallado opcional
    if pedir_si_no("\n  ¿Ver reporte detallado por clase de cada modelo?", default="n"):
        comparador.reporte_detallado(y_test)

    # 8. Guardar tabla como CSV
    ruta_csv = os.path.join(OUTPUT, f"{clave}_comparacion_modelos.csv")
    tabla.to_csv(ruta_csv, index=False)
    mostrar_exito(f"Tabla guardada en: {ruta_csv}")


def _stratify_safe(y):
    """Retorna y para stratify solo si cada clase tiene al menos 2 muestras."""
    valores, conteos = np.unique(y, return_counts=True)
    if np.all(conteos >= 2):
        return y
    return None


# ══════════════════════════════════════════════════════════════
# EXTENSIÓN E — Clustering y reducción de dimensionalidad
# ══════════════════════════════════════════════════════════════

def opcion_no_supervisado(datasets_cargados):
    """
    Extensión E: aplica KMeans y visualiza con PCA y t-SNE
    el dataset seleccionado por el usuario.
    """
    titulo_seccion("Extensión E — Clustering y Reducción de Dimensionalidad")

    if not datasets_cargados:
        mostrar_advertencia("No hay datasets cargados. Cargue datos primero (Opción 1).")
        return

    # 1. Seleccionar dataset
    print("\n  Datasets disponibles:")
    opciones = {}
    for i, (clave, ds) in enumerate(datasets_cargados.items(), 1):
        f, c = ds.get_dimensiones()
        opciones[str(i)] = f"{clave}  ({f} filas × {c} cols)"
    opciones["0"] = "Volver"

    sel = pedir_opcion(opciones, "Seleccione el dataset")
    if sel == "0":
        return

    clave = list(datasets_cargados.keys())[int(sel) - 1]
    ds = datasets_cargados[clave]

    # Verificar que tenga columnas numéricas
    df_num = ds.get_datos().select_dtypes(include="number").dropna(axis=1)
    if df_num.shape[1] < 2:
        mostrar_error(
            "El dataset necesita al menos 2 columnas numéricas "
            "para clustering y reducción de dimensionalidad."
        )
        return

    print(f"\n  Columnas numéricas detectadas ({df_num.shape[1]}): {list(df_num.columns)}")

    # 2. Submenú de opciones
    analizador = AnalizadorNoSupervisado(output_dir=OUTPUT)
    prefijo = clave.replace(" ", "_")

    submenu = {
        "1": "Método del codo (elegir número óptimo de clusters)",
        "2": "Clustering con KMeans",
        "3": "Reducción de dimensionalidad con PCA",
        "4": "Reducción de dimensionalidad con t-SNE",
        "5": "Análisis completo (codo + KMeans + PCA + t-SNE)",
        "0": "Volver",
    }

    while True:
        print()
        op = pedir_opcion(submenu, "¿Qué análisis desea ejecutar?")

        if op == "0":
            break

        elif op == "1":
            k_max = pedir_entero("Número máximo de clusters a evaluar", default="10")
            analizador.grafico_codo(ds, k_max=k_max, prefijo=prefijo)
            mostrar_exito("Gráfico del codo guardado en output/")

        elif op == "2":
            k = pedir_entero("Número de clusters (k)", default="3")
            _, sil = analizador.clustering_kmeans(ds, n_clusters=k, prefijo=prefijo)
            mostrar_exito(f"KMeans completado. Silhouette Score: {sil:.4f}")
            mostrar_info("Silhouette entre 0.5 y 1.0 indica buena separación de clusters.")

        elif op == "3":
            analizador.reduccion_pca(ds, prefijo=prefijo)
            mostrar_exito("Gráfico PCA guardado en output/")

        elif op == "4":
            analizador.reduccion_tsne(ds, prefijo=prefijo)
            mostrar_exito("Gráfico t-SNE guardado en output/")

        elif op == "5":
            k = pedir_entero("Número de clusters para KMeans", default="3")
            analizador.analisis_completo(ds, n_clusters=k, prefijo=prefijo)
            mostrar_exito("Análisis completo guardado en output/")

        pausar()
