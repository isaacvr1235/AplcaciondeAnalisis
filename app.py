"""
app.py — Interfaz Web con Streamlit
Aplicación de Análisis de Datos — IPN / ESCOM

Corre con:  streamlit run app.py
"""

import os
import sys
import warnings
import io
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score

# ── Agregar el proyecto al path ────────────────────────────
DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
from data.data import Dataset, DataLoader
from data.api_client import APIClient

# ══════════════════════════════════════════════════════════
# Configuración de página
# ══════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Análisis de Datos — IPN / ESCOM",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos ────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .header-banner {
        background: linear-gradient(135deg, #1F4E79 0%, #2E75B6 100%);
        border-radius: 12px;
        padding: 28px 36px;
        margin-bottom: 24px;
        color: white;
    }
    .header-banner h1 { margin: 0; font-size: 1.8rem; font-weight: 700; }
    .header-banner p  { margin: 6px 0 0; font-size: 0.95rem; opacity: 0.85; }

    .ext-badge {
        display: inline-block;
        background: #C55A11;
        color: white;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        letter-spacing: 0.06em;
        margin-bottom: 10px;
    }

    .metric-card {
        background: #16293F;
        border-left: 4px solid #2E75B6;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .metric-card .label { font-size: 0.78rem; color: #9AAEC2; font-weight: 600; text-transform: uppercase; }
    .metric-card .value { font-size: 1.7rem; font-weight: 700; color: #6FA8DC; }

    .winner-card {
        background: linear-gradient(135deg, #375623, #507A33);
        color: white;
        border-radius: 10px;
        padding: 18px 22px;
        text-align: center;
        margin-top: 16px;
    }
    .winner-card .trophy { font-size: 2rem; }
    .winner-card .label  { font-size: 0.82rem; opacity: 0.85; }
    .winner-card .name   { font-size: 1.3rem; font-weight: 700; }

    .info-box {
        background: #16293F;
        border-left: 4px solid #2E75B6;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 0.88rem;
        color: #C7DCF0;
        margin-top: 10px;
    }

    div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
    div[data-testid="stSelectbox"] > div { border-radius: 6px; }

    /* Forzar tema oscuro en tablas con estilo pandas (.highlight_max, etc) */
    div[data-testid="stDataFrame"] table {
        background-color: #1A1F29 !important;
        color: #E8EAED !important;
    }
    div[data-testid="stDataFrame"] th {
        background-color: #11151C !important;
        color: #E8EAED !important;
        border-color: #2A2F3A !important;
    }
    div[data-testid="stDataFrame"] td {
        background-color: #1A1F29 !important;
        color: #E8EAED !important;
        border-color: #2A2F3A !important;
    }
    /* Override de pandas Styler.highlight_max: usar azul oscuro en vez de blanco/celeste claro */
    div[data-testid="stDataFrame"] td[style*="background-color"] {
        background-color: #2E75B6 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# Header
# ══════════════════════════════════════════════════════════

st.markdown("""
<div class="header-banner">
    <h1>Aplicación de Análisis de Datos</h1>
    <p>Instituto Politécnico Nacional — Escuela Superior de Cómputo &nbsp;|&nbsp; Examen Extraordinario A26</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# Sidebar — carga de datos
# ══════════════════════════════════════════════════════════

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/IPN_logo.svg/120px-IPN_logo.svg.png", width=80)
    st.markdown("### Cargar datos")

    fuente = st.radio("Fuente de datos", ["Archivo del proyecto", "Subir archivo propio"])

    loader = DataLoader()
    dataset = None

    if fuente == "Archivo del proyecto":
        archivos_proyecto = {
            "estudiantes.csv":        os.path.join(DIR, "estudiantes.csv"),
            "calificaciones.tsv":     os.path.join(DIR, "calificaciones.tsv"),
            "datos_universidad.xlsx":  os.path.join(DIR, "datos_universidad.xlsx"),
        }
        sel = st.selectbox("Selecciona archivo", list(archivos_proyecto.keys()))
        ruta = archivos_proyecto[sel]

        hoja_sel = None
        if ruta.lower().endswith((".xlsx", ".xls")):
            try:
                hojas = pd.ExcelFile(ruta).sheet_names
                hoja_sel = st.selectbox("Selecciona hoja del Excel", hojas, index=min(1, len(hojas) - 1))
            except Exception as e:
                st.warning(f"No se pudieron leer las hojas: {e}")

        if st.button("Cargar", use_container_width=True):
            try:
                if hoja_sel:
                    ds = loader.cargar(ruta, hoja=hoja_sel)
                else:
                    ds = loader.cargar(ruta)
                st.session_state["dataset"] = ds
                st.session_state["nombre_ds"] = f"{sel}[{hoja_sel}]" if hoja_sel else sel
                st.success(f"Cargado: {ds.get_dimensiones()[0]} filas x {ds.get_dimensiones()[1]} cols")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        archivo = st.file_uploader("Sube tu archivo", type=["csv", "tsv", "xlsx", "xls", "json"])

        hoja_sel = None
        if archivo and archivo.name.lower().endswith((".xlsx", ".xls")):
            try:
                hojas = pd.ExcelFile(archivo).sheet_names
                hoja_sel = st.selectbox("Selecciona hoja del Excel", hojas, index=min(1, len(hojas) - 1))
                archivo.seek(0)
            except Exception as e:
                st.warning(f"No se pudieron leer las hojas: {e}")

        if archivo:
            tmp = os.path.join(DIR, archivo.name)
            with open(tmp, "wb") as f:
                f.write(archivo.read())
            try:
                if hoja_sel:
                    ds = loader.cargar(tmp, hoja=hoja_sel)
                else:
                    ds = loader.cargar(tmp)
                st.session_state["dataset"] = ds
                st.session_state["nombre_ds"] = f"{archivo.name}[{hoja_sel}]" if hoja_sel else archivo.name
                st.success(f"Cargado: {ds.get_dimensiones()[0]} filas x {ds.get_dimensiones()[1]} cols")
            except Exception as e:
                st.error(f"Error: {e}")

    if "dataset" in st.session_state:
        ds = st.session_state["dataset"]
        f, c = ds.get_dimensiones()
        st.markdown(f"""
        <div style="background:#1F4E79;color:white;border-radius:8px;padding:12px 14px;margin-top:12px;font-size:0.85rem;">
            <b>{st.session_state['nombre_ds']}</b><br>
            {f} filas &nbsp;×&nbsp; {c} columnas
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Navegación**")
    pagina = st.radio("", [
        "Inicio",
        "Vista del dataset",
        "Ext. B — Modelos supervisados",
        "Ext. D — Nueva fuente (API pública)",
        "Ext. E — Clustering y PCA/t-SNE",
    ], label_visibility="collapsed")

# ══════════════════════════════════════════════════════════
# Página: Inicio
# ══════════════════════════════════════════════════════════

if pagina == "Inicio":
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<span class="ext-badge">EXTENSIÓN B</span>', unsafe_allow_html=True)
        st.markdown("### Comparación de modelos supervisados")
        st.markdown("""
        Entrena y compara automáticamente **3 modelos de clasificación**:
        - Árbol de Decisión
        - Regresión Logística
        - Random Forest

        Métricas: Accuracy, Precision, Recall y F1-Score.
        """)

    with col2:
        st.markdown('<span class="ext-badge">EXTENSIÓN D</span>', unsafe_allow_html=True)
        st.markdown("### Nueva fuente de datos — API pública")
        st.markdown("""
        Integra una **API REST pública** (Universidades — Hipolabs) al
        flujo existente:
        - Consulta en vivo por país
        - JSON → DataFrame estructurado
        - Se incorpora como dataset principal de la app
        """)

    with col3:
        st.markdown('<span class="ext-badge">EXTENSIÓN E</span>', unsafe_allow_html=True)
        st.markdown("### Clustering y reducción de dimensionalidad")
        st.markdown("""
        Agrupa y visualiza datos con técnicas no supervisadas:
        - **KMeans** con Silhouette Score
        - **PCA** — varianza explicada en 2D
        - **t-SNE** — estructuras no lineales en 2D
        """)

    st.info("Carga un dataset desde la barra lateral para comenzar.")

    st.markdown("---")
    st.markdown("**Equipo:** Chávez Torres Alejandro · Tavera Chamorro Manuel Alejandro · Valle Ramírez José Isaac")

# ══════════════════════════════════════════════════════════
# Página: Vista del dataset
# ══════════════════════════════════════════════════════════

elif pagina == "Vista del dataset":
    st.markdown("## Vista del dataset")

    if "dataset" not in st.session_state:
        st.warning("Primero carga un dataset desde la barra lateral.")
    else:
        ds = st.session_state["dataset"]
        df = ds.get_datos()
        f, c = ds.get_dimensiones()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Filas", f)
        col2.metric("Columnas", c)
        col3.metric("Valores nulos", int(df.isnull().sum().sum()))
        col4.metric("Columnas numéricas", len(df.select_dtypes(include="number").columns))

        st.markdown("### Primeras filas")
        n = st.slider("Número de filas a mostrar", 5, min(50, f), 10)
        st.dataframe(df.head(n), use_container_width=True)

        st.markdown("### Estadísticas descriptivas")
        st.dataframe(df.describe().round(3), use_container_width=True)

        st.markdown("### Tipos de columnas")
        tipos = pd.DataFrame({
            "Columna": df.columns,
            "Tipo": df.dtypes.values,
            "Nulos": df.isnull().sum().values,
            "Únicos": df.nunique().values,
        })
        st.dataframe(tipos, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════
# Página: Extensión B
# ══════════════════════════════════════════════════════════

elif pagina == "Ext. B — Modelos supervisados":
    st.markdown('<span class="ext-badge">EXTENSIÓN B</span>', unsafe_allow_html=True)
    st.markdown("## Comparación automática de modelos supervisados")

    if "dataset" not in st.session_state:
        st.warning("Primero carga un dataset desde la barra lateral.")
        st.stop()

    ds  = st.session_state["dataset"]
    df  = ds.get_datos().copy()

    # ── Ayuda para crear una columna objetivo con relación real ──
    with st.expander("Tip: crear una columna objetivo con relación real a tus datos"):
        st.markdown(
            "Si eliges una columna como objetivo que no tiene relación lógica con las "
            "demás (por ejemplo, predecir la Carrera usando solo la Edad), los resultados "
            "serán bajos porque no hay nada que aprender. Aqui puedes crear una columna "
            "nueva derivada de una numerica existente (por ejemplo, Aprobado/Reprobado a "
            "partir de una calificacion), que si tendra relacion con las demas columnas "
            "numericas del dataset."
        )

        cols_numericas = list(df.select_dtypes(include="number").columns)
        if cols_numericas:
            col1_fe, col2_fe, col3_fe = st.columns([2, 1, 1])
            with col1_fe:
                col_base = st.selectbox("Columna numérica base", cols_numericas, key="col_base_fe")
            with col2_fe:
                # La key incluye col_base para forzar que el valor se recalcule
                # automáticamente cada vez que cambia la columna seleccionada.
                umbral_default = float(df[col_base].median())
                umbral = st.number_input(
                    "Umbral (aprueba si es >=)",
                    value=umbral_default,
                    key=f"umbral_fe_{col_base}",
                )
            with col3_fe:
                nombre_nueva = st.text_input("Nombre columna nueva", value="Aprobado", key="nombre_fe")

            st.caption(
                f"Rango de '{col_base}': mínimo {df[col_base].min():.2f}, "
                f"máximo {df[col_base].max():.2f}, mediana {df[col_base].median():.2f}. "
                f"El umbral debe estar dentro de este rango."
            )

            if st.button("Crear columna derivada", key="crear_fe"):
                df[nombre_nueva] = (df[col_base] >= umbral).astype(int)
                st.session_state["dataset"].datos[nombre_nueva] = df[nombre_nueva]
                conteo = df[nombre_nueva].value_counts().sort_index()

                if conteo.shape[0] < 2:
                    st.error(
                        f"El umbral {umbral:.1f} dejó todos los registros en una sola clase "
                        f"(todos 0 o todos 1). Elige un umbral dentro del rango mostrado arriba, "
                        f"idealmente cerca de la mediana."
                    )
                else:
                    st.success(
                        f"Columna '{nombre_nueva}' creada: "
                        f"{conteo.get(1, 0)} registros con valor 1 (cumple >= {umbral:.1f}), "
                        f"{conteo.get(0, 0)} registros con valor 0 (no cumple)."
                    )
                    st.info(
                        "Ahora selecciona esta nueva columna como objetivo abajo. "
                        "Importante: no incluyas la columna base (la que usaste para crearla) "
                        "como característica de entrada, porque eso sería 'hacer trampa' "
                        "(el modelo vería directamente la respuesta)."
                    )
                df = ds.get_datos().copy()
        else:
            st.warning("Este dataset no tiene columnas numéricas para usar como base.")

    st.markdown("### Configuración")

    # Solo mostrar columnas útiles como objetivo (pocas clases únicas)
    n_filas = len(df)
    cols_utiles = [
        c for c in df.columns
        if df[c].nunique() <= max(20, n_filas * 0.1)
    ]
    if not cols_utiles:
        cols_utiles = list(df.columns)

    col1, col2 = st.columns(2)
    with col1:
        col_objetivo = st.selectbox(
            "Columna objetivo (variable a predecir)",
            cols_utiles,
            help="Solo columnas con pocas categorías únicas, aptas para clasificación."
        )
    with col2:
        test_size = st.slider("Proporción para prueba (%)", 10, 40, 20) / 100

    columnas_restantes = [c for c in df.columns if c != col_objetivo]
    cols_excluir_manual = st.multiselect(
        "Excluir columnas adicionales de las características (opcional)",
        columnas_restantes,
        help=(
            "Excluye aqui cualquier columna que se haya usado para construir la columna "
            "objetivo (por ejemplo, si creaste 'Aprobado' a partir de 'Final', excluye 'Final' "
            "aqui para evitar que el modelo haga trampa viendo la respuesta directamente)."
        )
    )

    if st.button("Entrenar y comparar modelos", use_container_width=True, type="primary"):
        with st.spinner("Entrenando 3 modelos..."):
            try:
                # Preparar X e y
                y_raw = df[col_objetivo]
                X_df  = df.drop(columns=[col_objetivo])

                # Excluir columnas elegidas manualmente por el usuario (evitar data leakage)
                if cols_excluir_manual:
                    X_df = X_df.drop(columns=[c for c in cols_excluir_manual if c in X_df.columns])

                if y_raw.dtype == object or str(y_raw.dtype) in ("category", "string", "str"):
                    le = LabelEncoder()
                    y  = le.fit_transform(np.array(y_raw.astype(str).tolist()))
                    clases = list(le.classes_)
                else:
                    le = None
                    y = np.array(y_raw.tolist(), dtype=float)
                    clases = None

                # Excluir columnas de texto con alta cardinalidad o que sean IDs/nombres
                def es_texto(serie):
                    return serie.dtype == object or str(serie.dtype) in ("string", "str")

                cols_a_excluir = [
                    c for c in X_df.columns
                    if es_texto(X_df[c]) and (
                        X_df[c].nunique() > max(20, n_filas * 0.1)
                        or c.lower() in ("id", "nombre", "name", "index")
                    )
                ]
                if cols_a_excluir:
                    st.info(f"Columnas excluidas (texto/ID): {cols_a_excluir}")
                    X_df = X_df.drop(columns=cols_a_excluir)

                X_num = X_df.select_dtypes(include="number").dropna(axis=1)
                X_cat = X_df.select_dtypes(include=["object", "category", "string"])
                if not X_cat.empty:
                    X_enc = pd.get_dummies(X_cat, drop_first=True)
                    X_final = pd.concat([X_num, X_enc], axis=1)
                else:
                    X_final = X_num

                if X_final.shape[1] == 0:
                    st.error("No hay columnas numéricas de entrada para entrenar.")
                    st.stop()

                X = np.array(X_final.astype(float).values, dtype=float)

                # Stratify seguro — forzar numpy puro
                y = np.asarray(y)
                vals, cnts = np.unique(y, return_counts=True)

                if len(vals) < 2:
                    st.error(
                        f"La columna objetivo '{col_objetivo}' solo tiene un valor único "
                        f"en los datos ({vals[0]}). Se necesitan al menos 2 clases distintas "
                        f"para entrenar un modelo de clasificación. Revisa el umbral usado "
                        f"si creaste esta columna, o elige otra columna objetivo."
                    )
                    st.stop()

                strat = y if np.all(cnts >= 2) else None

                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=42, stratify=strat
                )

                # Entrenar modelos
                modelos = {
                    "Árbol de Decisión":   DecisionTreeClassifier(max_depth=5, random_state=42),
                    "Regresión Logística": LogisticRegression(max_iter=1000, random_state=42),
                    "Random Forest":       RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42),
                }

                resultados = []
                predicciones = {}
                for nombre, modelo in modelos.items():
                    modelo.fit(X_train, y_train)
                    y_pred = modelo.predict(X_test)
                    predicciones[nombre] = y_pred
                    resultados.append({
                        "Modelo":    nombre,
                        "Accuracy":  round(accuracy_score(y_test, y_pred), 4),
                        "Precision": round(precision_score(y_test, y_pred, average="weighted", zero_division=0), 4),
                        "Recall":    round(recall_score(y_test, y_pred, average="weighted", zero_division=0), 4),
                        "F1-Score":  round(f1_score(y_test, y_pred, average="weighted", zero_division=0), 4),
                    })

                tabla = pd.DataFrame(resultados).sort_values("F1-Score", ascending=False).reset_index(drop=True)
                st.session_state["tabla_b"]   = tabla
                st.session_state["preds_b"]   = predicciones
                st.session_state["y_test_b"]  = y_test
                st.session_state["clases_b"]  = clases
                st.session_state["features_b"] = list(X_final.columns)

            except Exception as e:
                import traceback
                st.error(f"Error durante el entrenamiento: {e}")
                st.code(traceback.format_exc())
                st.stop()

    # ── Resultados ──────────────────────────────────────────
    if "tabla_b" in st.session_state:
        tabla = st.session_state["tabla_b"]
        mejor = tabla.iloc[0]["Modelo"]

        st.markdown("---")
        st.markdown("### Resultados comparativos")

        # Métricas del mejor modelo
        fila_mejor = tabla.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Accuracy",  f"{fila_mejor['Accuracy']:.2%}")
        c2.metric("Precision", f"{fila_mejor['Precision']:.2%}")
        c3.metric("Recall",    f"{fila_mejor['Recall']:.2%}")
        c4.metric("F1-Score",  f"{fila_mejor['F1-Score']:.2%}")

        # Tabla comparativa
        estilo_tabla = tabla.style.highlight_max(
            subset=["Accuracy", "Precision", "Recall", "F1-Score"],
            props="background-color: #2E75B6; color: #FFFFFF; font-weight: 700;"
        ).set_properties(**{
            "background-color": "#1A1F29",
            "color": "#E8EAED",
        }).set_table_styles([
            {"selector": "th", "props": [("background-color", "#11151C"), ("color", "#E8EAED")]}
        ])
        st.dataframe(estilo_tabla, use_container_width=True, hide_index=True)

        # Ganador
        st.markdown(f"""
        <div class="winner-card">
            <div class="trophy"></div>
            <div class="label">MEJOR MODELO POR F1-SCORE</div>
            <div class="name">{mejor}</div>
        </div>
        """, unsafe_allow_html=True)

        # Gráfico de barras comparativo
        st.markdown("### Comparación visual")
        fig, ax = plt.subplots(figsize=(9, 4))
        metricas = ["Accuracy", "Precision", "Recall", "F1-Score"]
        x = np.arange(len(metricas))
        ancho = 0.22
        colores = ["#1F4E79", "#C55A11", "#375623"]
        for i, (_, fila) in enumerate(tabla.iterrows()):
            vals = [fila[m] for m in metricas]
            bars = ax.bar(x + i * ancho, vals, ancho,
                          label=fila["Modelo"], color=colores[i], alpha=0.88)
            for bar in bars:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.005,
                        f"{bar.get_height():.3f}",
                        ha="center", va="bottom", fontsize=7.5, fontweight="bold")

        ax.set_xticks(x + ancho)
        ax.set_xticklabels(metricas, fontsize=10)
        ax.set_ylim(0, 1.12)
        ax.set_ylabel("Valor de la métrica")
        ax.set_title("Comparación de métricas por modelo", fontsize=11, fontweight="bold", color="#1F4E79")
        ax.legend(fontsize=9)
        ax.spines[["top","right"]].set_visible(False)
        fig.patch.set_facecolor("#F7F9FC")
        ax.set_facecolor("#F7F9FC")
        st.pyplot(fig)
        plt.close(fig)

        # Reporte detallado opcional
        with st.expander("Ver reporte detallado por clase"):
            for nombre, y_pred in st.session_state["preds_b"].items():
                st.markdown(f"**{nombre}**")
                clases_rep = st.session_state["clases_b"]
                labels_en_test = np.unique(st.session_state["y_test_b"])
                if clases_rep and len(clases_rep) == len(labels_en_test):
                    reporte = classification_report(
                        st.session_state["y_test_b"], y_pred,
                        target_names=clases_rep,
                        zero_division=0
                    )
                else:
                    reporte = classification_report(
                        st.session_state["y_test_b"], y_pred,
                        zero_division=0
                    )
                st.code(reporte)

        st.markdown(f"""
        <div class="info-box">
            <b>Columnas usadas como características:</b><br>
            {', '.join(st.session_state['features_b'])}
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# Página: Extensión E
# ══════════════════════════════════════════════════════════

elif pagina == "Ext. D — Nueva fuente (API pública)":
    st.markdown('<span class="ext-badge">EXTENSIÓN D</span>', unsafe_allow_html=True)
    st.markdown("### Integración de una nueva fuente de datos — API pública")
    st.markdown("""
    Esta sección consume la **API pública de Universidades** (Hipolabs Universities
    API — `universities.hipolabs.com`, sin necesidad de API key) y la incorpora al
    flujo existente de la aplicación: el resultado es un `Dataset`, el mismo objeto
    que produce `DataLoader` para CSV/TSV/Excel, por lo que puede usarse directamente
    en **Vista del dataset**, **Ext. B** y **Ext. E**.
    """)

    st.markdown("""
    <div class="info-box">
        <b>Fuente:</b> http://universities.hipolabs.com/search?country=&lt;país&gt;<br>
        <b>Formato original:</b> JSON (datos semiestructurados, con campos anidados tipo lista)<br>
        <b>Transformación:</b> <code>pandas.json_normalize</code> + aplanado de listas → DataFrame tabular
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    paises = ["Mexico", "United States", "Spain", "Colombia",
              "Argentina", "Chile", "Brazil", "Canada", "Peru", "Germany"]
    pais = st.selectbox("País a consultar", paises, index=0)

    if st.button("Consultar API", use_container_width=True):
        with st.spinner(f"Consultando universidades de {pais}..."):
            try:
                cliente = APIClient()
                ds_api = cliente.obtener_universidades(pais=pais)
                st.session_state["dataset_api"] = ds_api
                st.success(
                    f"✔ {ds_api.get_dimensiones()[0]} universidades obtenidas para '{pais}'"
                )
            except Exception as e:
                st.error(f"Error al consultar la API: {e}")

    if "dataset_api" in st.session_state:
        ds_api = st.session_state["dataset_api"]
        df_api = ds_api.get_datos()

        st.markdown("#### Vista previa del dataset obtenido")
        st.dataframe(df_api.head(20), use_container_width=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Filas</div>
                <div class="value">{ds_api.get_dimensiones()[0]}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Columnas</div>
                <div class="value">{ds_api.get_dimensiones()[1]}</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="label">Origen</div>
                <div class="value" style="font-size:0.95rem;">API REST</div>
            </div>
            """, unsafe_allow_html=True)

        st.caption(f"Endpoint: {ds_api.origen}  ·  params: {ds_api.metadata.get('params')}")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Usar este dataset en el resto de la app", use_container_width=True):
                st.session_state["dataset"] = ds_api
                st.session_state["nombre_ds"] = ds_api.nombre
                st.success(
                    "Dataset de la API activado como dataset principal. "
                    "Ve a 'Vista del dataset', 'Ext. B' o 'Ext. E' para analizarlo."
                )
        with col2:
            csv_bytes = df_api.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "Descargar como CSV",
                csv_bytes,
                file_name=f"universidades_{pais}.csv",
                mime="text/csv",
                use_container_width=True,
            )

elif pagina == "Ext. E — Clustering y PCA/t-SNE":
    st.markdown('<span class="ext-badge">EXTENSIÓN E</span>', unsafe_allow_html=True)
    st.markdown("## Clustering y reducción de dimensionalidad")

    if "dataset" not in st.session_state:
        st.warning("Primero carga un dataset desde la barra lateral.")
        st.stop()

    ds = st.session_state["dataset"]
    df = ds.get_datos().copy()
    df_num = df.select_dtypes(include="number").dropna(axis=1)

    if df_num.shape[1] < 2:
        st.error("El dataset necesita al menos 2 columnas numéricas.")
        st.stop()

    st.markdown(f"**Columnas numéricas detectadas:** {', '.join(df_num.columns)}")

    col1, col2 = st.columns(2)
    with col1:
        k = st.slider("Número de clusters (k) para KMeans", 2, 10, 3)
    with col2:
        metodo_dim = st.selectbox("Reducción de dimensionalidad", ["PCA", "t-SNE", "Ambos"])

    if st.button("Ejecutar análisis completo", use_container_width=True, type="primary"):
        with st.spinner("Aplicando clustering y reducción de dimensionalidad..."):
            try:
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(df_num)

                # ── KMeans ──────────────────────────────────
                km = KMeans(n_clusters=k, random_state=42, n_init=10)
                etiquetas = km.fit_predict(X_scaled)
                sil = silhouette_score(X_scaled, etiquetas)

                st.session_state["etiquetas_e"] = etiquetas
                st.session_state["X_scaled_e"]  = X_scaled
                st.session_state["sil_e"]        = sil
                st.session_state["k_e"]          = k
                st.session_state["metodo_e"]     = metodo_dim
                st.session_state["df_num_e"]     = df_num

            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

    # ── Resultados ──────────────────────────────────────────
    if "etiquetas_e" in st.session_state:
        etiquetas = st.session_state["etiquetas_e"]
        X_scaled  = st.session_state["X_scaled_e"]
        sil       = st.session_state["sil_e"]
        k_used    = st.session_state["k_e"]
        df_num_r  = st.session_state["df_num_e"]

        st.markdown("---")
        st.markdown("### Resultados de KMeans")

        conteo = pd.Series(etiquetas).value_counts().sort_index()

        col1, col2, col3 = st.columns(3)
        col1.metric("Clusters", k_used)
        col2.metric("Silhouette Score", f"{sil:.4f}")
        col3.metric("Registros totales", len(etiquetas))

        st.markdown(f"""
        <div class="info-box">
            <b>Silhouette Score: {sil:.4f}</b><br>
            {'Buena separación (> 0.5)' if sil > 0.5 else 'Separación moderada — prueba con otro k'}
        </div>
        """, unsafe_allow_html=True)

        # Gráfico de distribución
        PALETA = ["#1F4E79","#C55A11","#375623","#7030A0",
                  "#C00000","#0070C0","#00B050","#FF6600"]

        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        fig.patch.set_facecolor("#F7F9FC")

        # Barras
        ax = axes[0]
        ax.set_facecolor("#F7F9FC")
        colores = [PALETA[i % len(PALETA)] for i in range(k_used)]
        bars = ax.bar([f"Cluster {i}" for i in conteo.index],
                      conteo.values, color=colores, edgecolor="white", width=0.55)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.3,
                    str(int(bar.get_height())),
                    ha="center", fontsize=10, fontweight="bold")
        ax.set_ylabel("Registros")
        ax.set_title("Distribución de clusters", fontweight="bold", color="#1F4E79")
        ax.spines[["top","right"]].set_visible(False)

        # Pastel
        ax2 = axes[1]
        ax2.set_facecolor("#F7F9FC")
        ax2.pie(conteo.values,
                labels=[f"Cluster {i}" for i in conteo.index],
                colors=colores, autopct="%1.1f%%",
                startangle=90, pctdistance=0.82,
                wedgeprops={"edgecolor": "white", "linewidth": 2})
        ax2.set_title("Proporción por cluster", fontweight="bold", color="#1F4E79")

        fig.suptitle(f"KMeans — k={k_used}", fontsize=12, fontweight="bold", color="#1F4E79", y=1.02)
        st.pyplot(fig)
        plt.close(fig)

        # ── Método del codo ─────────────────────────────────
        st.markdown("### Método del codo")
        inercias = []
        k_range = range(2, min(11, len(X_scaled)))
        for ki in k_range:
            km_i = KMeans(n_clusters=ki, random_state=42, n_init=10)
            km_i.fit(X_scaled)
            inercias.append(km_i.inertia_)

        fig2, ax3 = plt.subplots(figsize=(7, 3.5))
        fig2.patch.set_facecolor("#F7F9FC")
        ax3.set_facecolor("#F7F9FC")
        ax3.plot(list(k_range), inercias, "o-", color="#1F4E79", linewidth=2.2, markersize=8)
        ax3.axvline(k_used, color="#C55A11", linestyle="--", linewidth=1.5, label=f"k={k_used} seleccionado")
        ax3.set_xlabel("Número de clusters (k)")
        ax3.set_ylabel("Inercia (WCSS)")
        ax3.set_title("Método del codo", fontweight="bold", color="#1F4E79")
        ax3.legend(fontsize=9)
        ax3.spines[["top","right"]].set_visible(False)
        ax3.grid(True, linestyle="--", alpha=0.4)
        st.pyplot(fig2)
        plt.close(fig2)

        # ── Reducción de dimensionalidad ────────────────────
        metodo = st.session_state["metodo_e"]

        def scatter_2d(proyeccion, titulo, xlabel, ylabel):
            fig, ax = plt.subplots(figsize=(8, 5))
            fig.patch.set_facecolor("#F7F9FC")
            ax.set_facecolor("#F7F9FC")
            for c in np.unique(etiquetas):
                mask = etiquetas == c
                ax.scatter(proyeccion[mask, 0], proyeccion[mask, 1],
                           c=PALETA[c % len(PALETA)],
                           label=f"Cluster {c}", alpha=0.78, s=60,
                           edgecolors="white", linewidth=0.5)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.set_title(titulo, fontweight="bold", color="#1F4E79")
            ax.legend(fontsize=9, title="Cluster")
            ax.spines[["top","right"]].set_visible(False)
            return fig

        if metodo in ("PCA", "Ambos"):
            st.markdown("### PCA — Proyección en 2D")
            pca = PCA(n_components=2, random_state=42)
            comp = pca.fit_transform(X_scaled)
            var = pca.explained_variance_ratio_
            fig_pca = scatter_2d(
                comp,
                f"PCA — Varianza explicada: PC1={var[0]*100:.1f}%  PC2={var[1]*100:.1f}%",
                f"PC1 ({var[0]*100:.1f}%)", f"PC2 ({var[1]*100:.1f}%)"
            )
            st.pyplot(fig_pca)
            plt.close(fig_pca)

            # Varianza acumulada
            pca_full = PCA(random_state=42).fit(X_scaled)
            acum = np.cumsum(pca_full.explained_variance_ratio_)
            fig_var, ax_var = plt.subplots(figsize=(7, 3))
            fig_var.patch.set_facecolor("#F7F9FC")
            ax_var.set_facecolor("#F7F9FC")
            ax_var.plot(range(1, len(acum)+1), acum * 100, "o-",
                        color="#C55A11", linewidth=2, markersize=7)
            ax_var.axhline(90, color="#375623", linestyle="--", linewidth=1.5, label="90% varianza")
            ax_var.set_xlabel("Número de componentes")
            ax_var.set_ylabel("Varianza acumulada (%)")
            ax_var.set_title("Varianza explicada acumulada — PCA", fontweight="bold", color="#1F4E79")
            ax_var.legend(fontsize=9)
            ax_var.grid(True, linestyle="--", alpha=0.4)
            ax_var.spines[["top","right"]].set_visible(False)
            st.pyplot(fig_var)
            plt.close(fig_var)

        if metodo in ("t-SNE", "Ambos"):
            st.markdown("### t-SNE — Proyección en 2D")
            perp = min(30, max(5, len(X_scaled) // 3))
            with st.spinner(f"Calculando t-SNE (perplexity={perp})..."):
                tsne = TSNE(n_components=2, perplexity=perp, random_state=42, n_iter=1000)
                proy = tsne.fit_transform(X_scaled)
            fig_tsne = scatter_2d(
                proy,
                f"t-SNE — Proyección no lineal 2D (perplexity={perp})",
                "t-SNE Dimensión 1", "t-SNE Dimensión 2"
            )
            st.pyplot(fig_tsne)
            plt.close(fig_tsne)

        # Dataset con clusters
        st.markdown("### Dataset con clusters asignados")
        df_resultado = ds.get_datos().copy()
        df_resultado["Cluster"] = etiquetas
        st.dataframe(df_resultado.head(20), use_container_width=True)

        csv = df_resultado.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar dataset con clusters",
            data=csv,
            file_name="dataset_con_clusters.csv",
            mime="text/csv",
        )
