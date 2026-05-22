import os
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
 
warnings.filterwarnings("ignore")
 
# Paleta corporativa
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
 
 
class Visualizador:
    """Genera gráficos EDA y los guarda en disco."""
 
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
 
    # ── utilidades internas ───────────────────
 
    def _guardar(self, fig, nombre_archivo):
        ruta = os.path.join(self.output_dir, nombre_archivo)
        fig.savefig(ruta, dpi=130, bbox_inches="tight", facecolor=FONDO)
        plt.close(fig)
        print(f"    → Gráfico guardado: {ruta}")
        return ruta
 
    def _titulo_figura(self, fig, texto, fuente="IPN — Escuela Superior de Cómputo"):
        fig.text(0.5, 0.98, texto, ha="center", va="top",
                 fontsize=13, fontweight="bold", color=AZUL)
        fig.text(0.5, 0.955, fuente, ha="center", va="top",
                 fontsize=8, color=GRIS, style="italic")
 
    # ── EDA genérico para cualquier Dataset ──
 
    def eda_completo(self, dataset, prefijo="eda"):
        """
        Realiza un EDA completo sobre un Dataset:
          1. Resumen estadístico (imprime en consola)
          2. Gráfico de valores nulos
          3. Distribuciones de columnas numéricas
          4. Distribuciones de columnas categóricas
          5. Mapa de calor de correlaciones
        Devuelve la lista de rutas de imágenes generadas.
        """
        df     = dataset.get_datos()
        nombre = dataset.nombre
        rutas  = []
 
        print(f"\n{'═'*55}")
        print(f"  EDA: {nombre}")
        print(f"{'═'*55}")
        print(f"  Dimensiones : {df.shape[0]} filas × {df.shape[1]} columnas")
        print(f"  Columnas    : {list(df.columns)}")
        print(f"\n  Tipos de datos:")
        print(df.dtypes.to_string())
        print(f"\n  Estadísticos descriptivos (numéricas):")
        num_cols = df.select_dtypes(include="number").columns.tolist()
        if num_cols:
            print(df[num_cols].describe().round(2).to_string())
        nulos = df.isnull().sum()
        nulos_total = nulos.sum()
        print(f"\n  Valores nulos por columna:")
        print(nulos.to_string())
        print(f"  Total nulos: {nulos_total}  ({100*nulos_total/df.size:.1f}% del dataset)")
 
        # ── 1. Mapa de nulos ─────────────────
        rutas.append(self._grafico_nulos(df, nombre, prefijo))
 
        # ── 2. Distribuciones numéricas ──────
        if num_cols:
            rutas.append(self._grafico_numericas(df, num_cols, nombre, prefijo))
 
        # ── 3. Distribuciones categóricas ────
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if cat_cols:
            rutas.append(self._grafico_categoricas(df, cat_cols, nombre, prefijo))
 
        # ── 4. Correlaciones ─────────────────
        if len(num_cols) >= 2:
            rutas.append(self._grafico_correlacion(df, num_cols, nombre, prefijo))
 
        return [r for r in rutas if r]
 
    # ── Gráficos individuales ─────────────────
 
    def _grafico_nulos(self, df, nombre, prefijo):
        nulos = df.isnull().sum()
        if nulos.sum() == 0:
            print("    (Sin valores nulos — gráfico de nulos omitido)")
            return None
 
        fig, ax = plt.subplots(figsize=(8, max(3, len(df.columns) * 0.45)))
        self._titulo_figura(fig, f"Valores Nulos — {nombre}")
        colores = [NARANJA if v > 0 else AZUL for v in nulos.values]
        ax.barh(nulos.index, nulos.values, color=colores, edgecolor="white", height=0.6)
        ax.set_xlabel("Cantidad de nulos")
        ax.set_title("Nulos por columna", pad=8)
        for i, v in enumerate(nulos.values):
            if v > 0:
                ax.text(v + 0.1, i, str(v), va="center", fontsize=8, color=NARANJA)
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        return self._guardar(fig, f"{prefijo}_nulos.png")
 
    def _grafico_numericas(self, df, num_cols, nombre, prefijo):
        n    = len(num_cols)
        cols = min(3, n)
        rows = (n + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols,
                                 figsize=(cols * 4.5, rows * 3.2),
                                 squeeze=False)
        self._titulo_figura(fig, f"Distribuciones Numéricas — {nombre}")
        for idx, col in enumerate(num_cols):
            r, c = divmod(idx, cols)
            ax   = axes[r][c]
            data = df[col].dropna()
            ax.hist(data, bins=20, color=AZUL, edgecolor="white", alpha=0.85)
            ax.axvline(data.mean(),   color=NARANJA, linestyle="--", linewidth=1.2, label="Media")
            ax.axvline(data.median(), color=VERDE,   linestyle=":",  linewidth=1.2, label="Mediana")
            ax.set_title(col, fontweight="bold")
            ax.set_xlabel("Valor")
            ax.set_ylabel("Frecuencia")
            ax.legend(fontsize=7)
        # Ocultar ejes vacíos
        for idx in range(n, rows * cols):
            r, c = divmod(idx, cols)
            axes[r][c].set_visible(False)
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        return self._guardar(fig, f"{prefijo}_numericas.png")
 
    def _grafico_categoricas(self, df, cat_cols, nombre, prefijo):
        n    = len(cat_cols)
        cols = min(2, n)
        rows = (n + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols,
                                 figsize=(cols * 5.5, rows * 3.5),
                                 squeeze=False)
        self._titulo_figura(fig, f"Variables Categóricas — {nombre}")
        paleta = [AZUL, VERDE, NARANJA, "#7030A0", "#C00000",
                  "#0070C0", "#00B050", "#FF0000"]
        for idx, col in enumerate(cat_cols):
            r, c = divmod(idx, cols)
            ax   = axes[r][c]
            vc   = df[col].value_counts().head(12)
            bars = ax.bar(range(len(vc)), vc.values,
                          color=[paleta[i % len(paleta)] for i in range(len(vc))],
                          edgecolor="white", width=0.65)
            ax.set_xticks(range(len(vc)))
            ax.set_xticklabels(vc.index, rotation=35, ha="right", fontsize=8)
            ax.set_title(col, fontweight="bold")
            ax.set_ylabel("Frecuencia")
            for bar, val in zip(bars, vc.values):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.3, str(val),
                        ha="center", va="bottom", fontsize=7)
        for idx in range(n, rows * cols):
            r, c = divmod(idx, cols)
            axes[r][c].set_visible(False)
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        return self._guardar(fig, f"{prefijo}_categoricas.png")
 
    def _grafico_correlacion(self, df, num_cols, nombre, prefijo):
        corr = df[num_cols].corr()
        fig, ax = plt.subplots(figsize=(max(5, len(num_cols) * 1.1),
                                        max(4, len(num_cols) * 0.9)))
        self._titulo_figura(fig, f"Mapa de Correlación — {nombre}")
        mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
        sns.heatmap(corr, ax=ax, annot=True, fmt=".2f",
                    cmap="RdYlGn", center=0, linewidths=0.5,
                    linecolor="white", annot_kws={"size": 8},
                    cbar_kws={"shrink": 0.8})
        ax.set_title("Correlaciones (Pearson)", pad=8)
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        return self._guardar(fig, f"{prefijo}_correlacion.png")
 
    # ── Gráfico extra: top estudiantes ────────
 
    def top_estudiantes(self, df_cal, df_est, output_name="top_estudiantes.png"):
        """Ranking de los 10 mejores estudiantes por promedio de calificaciones."""
        df_cal = df_cal.copy()
        for col in ["Parcial1", "Parcial2", "Final"]:
            df_cal[col] = pd.to_numeric(df_cal[col], errors="coerce")
        df_cal["Promedio_Cal"] = df_cal[["Parcial1", "Parcial2", "Final"]].mean(axis=1)
        ranking = (df_cal.groupby("ID_Estudiante")["Promedio_Cal"]
                         .mean().sort_values(ascending=False).head(10))
        fig, ax = plt.subplots(figsize=(9, 4))
        self._titulo_figura(fig, "Top 10 Estudiantes por Promedio de Calificaciones")
        colores = [AZUL if i > 0 else NARANJA for i in range(len(ranking))]
        bars = ax.barh(ranking.index.astype(str)[::-1],
                       ranking.values[::-1], color=colores[::-1],
                       edgecolor="white", height=0.6)
        ax.set_xlabel("Promedio de Calificaciones")
        ax.set_title("Ranking: promedio (Parcial1 + Parcial2 + Final) / 3", pad=6)
        for bar, val in zip(bars, ranking.values[::-1]):
            ax.text(val + 0.2, bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}", va="center", fontsize=8)
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        return self._guardar(fig, output_name)
 
    def promedio_por_curso(self, df_cal, output_name="promedio_cursos.png"):
        """Promedio de nota final por curso."""
        df_cal = df_cal.copy()
        df_cal["Final"] = pd.to_numeric(df_cal["Final"], errors="coerce")
        prom = df_cal.groupby("Curso")["Final"].mean().sort_values()
        fig, ax = plt.subplots(figsize=(9, 5))
        self._titulo_figura(fig, "Promedio de Calificación Final por Curso")
        colores = [VERDE if v >= prom.mean() else NARANJA for v in prom.values]
        ax.barh(prom.index, prom.values, color=colores, edgecolor="white", height=0.65)
        ax.axvline(prom.mean(), color=GRIS, linestyle="--", linewidth=1.2, label="Promedio global")
        ax.set_xlabel("Promedio Final")
        ax.legend(fontsize=8)
        for i, v in enumerate(prom.values):
            ax.text(v + 0.2, i, f"{v:.1f}", va="center", fontsize=8)
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        return self._guardar(fig, output_name)