"""
visualization/analisis_no_supervisado.py
Extensión E del Examen Extraordinario:
  - Clustering con KMeans
  - Reducción de dimensionalidad con PCA y t-SNE
  - Visualizaciones integradas al estilo del proyecto
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

warnings.filterwarnings("ignore")

# Paleta corporativa (igual que visualizador.py)
AZUL    = "#1F4E79"
VERDE   = "#375623"
NARANJA = "#C55A11"
GRIS    = "#404040"
FONDO   = "#F7F9FC"

plt.rcParams.update({
    "figure.facecolor": FONDO,
    "axes.facecolor":   FONDO,
    "axes.edgecolor":   GRIS,
    "axes.labelcolor":  GRIS,
    "xtick.color":      GRIS,
    "ytick.color":      GRIS,
    "text.color":       GRIS,
    "font.family":      "DejaVu Sans",
    "axes.titlesize":   11,
    "axes.labelsize":   9,
})

PALETA_CLUSTERS = [
    "#1F4E79", "#C55A11", "#375623", "#7030A0",
    "#C00000", "#0070C0", "#00B050", "#FF6600",
]


class AnalizadorNoSupervisado:
    """
    Agrupa (KMeans) y visualiza datos en 2D mediante PCA o t-SNE.
    Se integra con la clase Dataset del proyecto.
    """

    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self._etiquetas_cluster = None
        self._df_num = None
        self._X_scaled = None

    # ── Utilidades internas ───────────────────────────────

    def _guardar(self, fig, nombre_archivo):
        ruta = os.path.join(self.output_dir, nombre_archivo)
        fig.savefig(ruta, dpi=130, bbox_inches="tight", facecolor=FONDO)
        plt.close(fig)
        print(f"    → Gráfico guardado: {ruta}")
        return ruta

    def _titulo_figura(self, fig, texto):
        fig.text(0.5, 0.98, texto, ha="center", va="top",
                 fontsize=13, fontweight="bold", color=AZUL)
        fig.text(0.5, 0.955, "IPN — Escuela Superior de Cómputo",
                 ha="center", va="top", fontsize=8, color=GRIS, style="italic")

    def _preparar_datos(self, dataset):
        """Extrae columnas numéricas y escala con StandardScaler."""
        df = dataset.get_datos()
        df_num = df.select_dtypes(include="number").dropna(axis=1)

        if df_num.shape[1] < 2:
            raise ValueError(
                "El dataset necesita al menos 2 columnas numéricas para el análisis."
            )

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_num)
        self._df_num = df_num
        self._X_scaled = X_scaled
        return df_num, X_scaled

    # ── Método de codo (elegir k óptimo) ─────────────────

    def grafico_codo(self, dataset, k_max=10, prefijo="cluster"):
        """
        Genera el gráfico del método del codo para elegir el número
        óptimo de clusters.
        """
        _, X_scaled = self._preparar_datos(dataset)
        inercias = []
        k_range = range(2, min(k_max + 1, len(X_scaled)))

        for k in k_range:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            km.fit(X_scaled)
            inercias.append(km.inertia_)

        fig, ax = plt.subplots(figsize=(7, 4))
        self._titulo_figura(fig, "Método del Codo — Número óptimo de clusters")
        ax.plot(list(k_range), inercias, "o-", color=AZUL, linewidth=2, markersize=7)
        ax.set_xlabel("Número de clusters (k)")
        ax.set_ylabel("Inercia (WCSS)")
        ax.set_title("Seleccione el k donde la curva 'quiebra'", pad=8)
        ax.grid(True, linestyle="--", alpha=0.5)
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        return self._guardar(fig, f"{prefijo}_codo.png")

    # ── KMeans ───────────────────────────────────────────

    def clustering_kmeans(self, dataset, n_clusters=3, prefijo="cluster"):
        """
        Aplica KMeans al dataset, imprime métricas y guarda
        un gráfico de distribución de clusters.
        Devuelve el DataFrame original con columna 'Cluster' agregada.
        """
        df_num, X_scaled = self._preparar_datos(dataset)

        print(f"\n  Aplicando KMeans con k={n_clusters}...")
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        etiquetas = km.fit_predict(X_scaled)
        self._etiquetas_cluster = etiquetas

        # Métricas
        sil = silhouette_score(X_scaled, etiquetas)
        inercia = km.inertia_
        print(f"    ✔ Silhouette Score : {sil:.4f}  (más cercano a 1 = mejor separación)")
        print(f"    ✔ Inercia (WCSS)   : {inercia:.2f}")

        # DataFrame con cluster asignado
        df_resultado = dataset.get_datos().copy()
        df_resultado["Cluster"] = etiquetas

        # Conteo por cluster
        conteo = pd.Series(etiquetas).value_counts().sort_index()
        print(f"\n  Distribución de clusters:")
        for c, n in conteo.items():
            print(f"    Cluster {c}: {n} registros")

        # Gráfico de barras de distribución
        fig, ax = plt.subplots(figsize=(7, 4))
        self._titulo_figura(fig, f"Distribución de Clusters (KMeans k={n_clusters})")
        colores = [PALETA_CLUSTERS[i % len(PALETA_CLUSTERS)] for i in range(n_clusters)]
        ax.bar([f"Cluster {i}" for i in conteo.index],
               conteo.values, color=colores, edgecolor="white", width=0.6)
        ax.set_ylabel("Cantidad de registros")
        ax.set_title("Registros asignados a cada cluster", pad=8)
        for i, v in enumerate(conteo.values):
            ax.text(i, v + 0.3, str(v), ha="center", fontsize=9, fontweight="bold")
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        self._guardar(fig, f"{prefijo}_kmeans_distribucion.png")

        return df_resultado, sil

    # ── PCA ──────────────────────────────────────────────

    def reduccion_pca(self, dataset, n_components=2, prefijo="pca"):
        """
        Aplica PCA y visualiza los datos en 2D, coloreados por cluster si existe.
        También imprime la varianza explicada por cada componente.
        """
        df_num, X_scaled = self._preparar_datos(dataset)

        n_comp_real = min(n_components, X_scaled.shape[1], X_scaled.shape[0])
        pca = PCA(n_components=n_comp_real, random_state=42)
        componentes = pca.fit_transform(X_scaled)

        varianza = pca.explained_variance_ratio_
        print(f"\n  PCA — Varianza explicada por componente:")
        for i, v in enumerate(varianza):
            print(f"    PC{i+1}: {v*100:.2f}%")
        print(f"    Total acumulado: {varianza.sum()*100:.2f}%")

        # Gráfico 2D
        fig, axes = plt.subplots(1, 2, figsize=(13, 5))
        self._titulo_figura(fig, "Reducción de Dimensionalidad — PCA")

        # ── Panel izquierdo: scatter de componentes ──
        ax = axes[0]
        if self._etiquetas_cluster is not None and len(self._etiquetas_cluster) == len(componentes):
            etiquetas = self._etiquetas_cluster
            for c in np.unique(etiquetas):
                mask = etiquetas == c
                ax.scatter(componentes[mask, 0], componentes[mask, 1],
                           c=PALETA_CLUSTERS[c % len(PALETA_CLUSTERS)],
                           label=f"Cluster {c}", alpha=0.75, s=50, edgecolors="white", linewidth=0.4)
            ax.legend(fontsize=8, title="Cluster")
        else:
            ax.scatter(componentes[:, 0], componentes[:, 1],
                       c=AZUL, alpha=0.6, s=50, edgecolors="white", linewidth=0.4)

        ax.set_xlabel(f"PC1 ({varianza[0]*100:.1f}% var.)")
        ax.set_ylabel(f"PC2 ({varianza[1]*100:.1f}% var.)" if n_comp_real > 1 else "PC2")
        ax.set_title("Proyección 2D (PC1 vs PC2)", pad=8)

        # ── Panel derecho: varianza explicada acumulada ──
        ax2 = axes[1]
        varianza_full = PCA(random_state=42).fit(X_scaled).explained_variance_ratio_
        acumulada = np.cumsum(varianza_full)
        ax2.plot(range(1, len(acumulada) + 1), acumulada * 100,
                 "o-", color=NARANJA, linewidth=2, markersize=6)
        ax2.axhline(90, color=VERDE, linestyle="--", linewidth=1.2, label="90% varianza")
        ax2.set_xlabel("Número de componentes")
        ax2.set_ylabel("Varianza explicada acumulada (%)")
        ax2.set_title("Varianza acumulada vs. componentes", pad=8)
        ax2.legend(fontsize=8)
        ax2.grid(True, linestyle="--", alpha=0.4)

        fig.tight_layout(rect=[0, 0, 1, 0.93])
        return self._guardar(fig, f"{prefijo}_pca_2d.png")

    # ── t-SNE ─────────────────────────────────────────────

    def reduccion_tsne(self, dataset, perplexity=30, prefijo="tsne"):
        """
        Aplica t-SNE para visualizar estructuras no lineales en 2D.
        """
        df_num, X_scaled = self._preparar_datos(dataset)

        # t-SNE necesita perplexity < n_samples
        perp = min(perplexity, max(5, len(X_scaled) // 3))
        print(f"\n  Aplicando t-SNE (perplexity={perp})... puede tomar unos segundos.")

        tsne = TSNE(n_components=2, perplexity=perp, random_state=42, n_iter=1000)
        proyeccion = tsne.fit_transform(X_scaled)

        fig, ax = plt.subplots(figsize=(8, 6))
        self._titulo_figura(fig, "Reducción de Dimensionalidad — t-SNE")

        if self._etiquetas_cluster is not None and len(self._etiquetas_cluster) == len(proyeccion):
            etiquetas = self._etiquetas_cluster
            for c in np.unique(etiquetas):
                mask = etiquetas == c
                ax.scatter(proyeccion[mask, 0], proyeccion[mask, 1],
                           c=PALETA_CLUSTERS[c % len(PALETA_CLUSTERS)],
                           label=f"Cluster {c}", alpha=0.75, s=55,
                           edgecolors="white", linewidth=0.4)
            ax.legend(fontsize=9, title="Cluster")
        else:
            ax.scatter(proyeccion[:, 0], proyeccion[:, 1],
                       c=AZUL, alpha=0.65, s=55, edgecolors="white", linewidth=0.4)

        ax.set_xlabel("t-SNE Dimensión 1")
        ax.set_ylabel("t-SNE Dimensión 2")
        ax.set_title(f"Proyección t-SNE 2D (perplexity={perp})", pad=8)
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        return self._guardar(fig, f"{prefijo}_tsne_2d.png")

    # ── Análisis completo (acceso directo desde el menú) ──

    def analisis_completo(self, dataset, n_clusters=3, prefijo="nosup"):
        """
        Ejecuta el flujo completo:
          1. Método del codo
          2. KMeans
          3. PCA
          4. t-SNE
        """
        print(f"\n{'═'*55}")
        print(f"  ANÁLISIS NO SUPERVISADO: {dataset.nombre}")
        print(f"{'═'*55}")

        rutas = []
        rutas.append(self.grafico_codo(dataset, prefijo=prefijo))
        _, sil = self.clustering_kmeans(dataset, n_clusters=n_clusters, prefijo=prefijo)
        rutas.append(self.reduccion_pca(dataset, prefijo=prefijo))
        rutas.append(self.reduccion_tsne(dataset, prefijo=prefijo))

        print(f"\n  ✔ Análisis no supervisado completado.")
        print(f"  ✔ Silhouette Score final: {sil:.4f}")
        return [r for r in rutas if r]
