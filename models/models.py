"""
models/models.py
Jerarquía de modelos ML con implementación real usando scikit-learn.

NOTA: este módulo se desarrolló originalmente como Extensión B del Examen
Extraordinario (comparación automática de modelos supervisados). Ya NO es
la extensión presentada (se sustituyó por la Extensión D — integración de
API externa, ver data/api_loader.py y menu/api_menu.py). Se conserva aquí
como código funcional de respaldo.
"""

from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression as SKLogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report
)
import pandas as pd
import numpy as np


# ══════════════════════════════════════════════════════
# Jerarquía base (conservada del proyecto original)
# ══════════════════════════════════════════════════════

class Modelo:
    def entrenar(self, X, y):
        pass

    def predecir(self, X):
        pass


class ModeloSupervisado(Modelo):
    def entrenar(self, X, y):
        pass


class ModeloNoSupervisado(Modelo):
    def entrenar(self, X):
        pass


class Regresion(ModeloSupervisado):
    pass


class Clasificacion(ModeloSupervisado):
    pass


# ══════════════════════════════════════════════════════
# Implementaciones reales (Extensión B)
# ══════════════════════════════════════════════════════

class ModeloArbolDecision(Clasificacion):
    """Árbol de decisión con scikit-learn."""

    def __init__(self, max_depth=5, random_state=42):
        self.max_depth = max_depth
        self.random_state = random_state
        self._modelo = DecisionTreeClassifier(
            max_depth=max_depth,
            random_state=random_state
        )
        self.nombre = "Árbol de Decisión"

    def entrenar(self, X, y):
        self._modelo.fit(X, y)
        return self

    def predecir(self, X):
        return self._modelo.predict(X)


class ModeloRegresionLogistica(Clasificacion):
    """Regresión logística con scikit-learn."""

    def __init__(self, max_iter=1000, random_state=42):
        self.max_iter = max_iter
        self.random_state = random_state
        self._modelo = SKLogisticRegression(
            max_iter=max_iter,
            random_state=random_state
        )
        self.nombre = "Regresión Logística"

    def entrenar(self, X, y):
        self._modelo.fit(X, y)
        return self

    def predecir(self, X):
        return self._modelo.predict(X)


class ModeloRandomForest(Clasificacion):
    """Random Forest con scikit-learn."""

    def __init__(self, n_estimators=100, max_depth=5, random_state=42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self._modelo = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state
        )
        self.nombre = "Random Forest"

    def entrenar(self, X, y):
        self._modelo.fit(X, y)
        return self

    def predecir(self, X):
        return self._modelo.predict(X)


# ══════════════════════════════════════════════════════
# Comparador automático de modelos (núcleo de la Extensión B)
# ══════════════════════════════════════════════════════

class ComparadorModelos:
    """
    Entrena y compara automáticamente múltiples modelos de clasificación
    sobre el mismo conjunto de datos.
    """

    def __init__(self):
        self.modelos = [
            ModeloArbolDecision(),
            ModeloRegresionLogistica(),
            ModeloRandomForest(),
        ]
        self.resultados = []

    def comparar(self, X_train, y_train, X_test, y_test):
        """
        Entrena todos los modelos y evalúa con métricas estándar.
        Devuelve un DataFrame con el resumen comparativo.
        """
        self.resultados = []

        for modelo in self.modelos:
            print(f"\n  Entrenando: {modelo.nombre}...")
            try:
                modelo.entrenar(X_train, y_train)
                y_pred = modelo.predecir(X_test)

                acc  = accuracy_score(y_test, y_pred)
                prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
                rec  = recall_score(y_test, y_pred, average="weighted", zero_division=0)
                f1   = f1_score(y_test, y_pred, average="weighted", zero_division=0)

                self.resultados.append({
                    "Modelo":     modelo.nombre,
                    "Accuracy":   round(acc,  4),
                    "Precision":  round(prec, 4),
                    "Recall":     round(rec,  4),
                    "F1-Score":   round(f1,   4),
                    "_y_pred":    y_pred,       # interno, para matriz de confusión
                })
                print(f"    ✔ Accuracy={acc:.4f}  F1={f1:.4f}")

            except Exception as e:
                print(f"    ✖ Error en {modelo.nombre}: {e}")

        return self._tabla_resumen()

    def _tabla_resumen(self):
        """DataFrame con las métricas (sin la columna interna _y_pred)."""
        if not self.resultados:
            return pd.DataFrame()
        df = pd.DataFrame(self.resultados).drop(columns=["_y_pred"])
        df = df.sort_values("F1-Score", ascending=False).reset_index(drop=True)
        return df

    def mejor_modelo(self):
        """Devuelve el nombre del modelo con mayor F1-Score."""
        if not self.resultados:
            return None
        mejor = max(self.resultados, key=lambda r: r["F1-Score"])
        return mejor["Modelo"]

    def reporte_detallado(self, y_test):
        """Imprime el classification_report de cada modelo."""
        for r in self.resultados:
            print(f"\n  {'─'*45}")
            print(f"  Modelo: {r['Modelo']}")
            print(classification_report(y_test, r["_y_pred"], zero_division=0))


# Clases vacías conservadas por compatibilidad con el pipeline original
class DecisionTree(Clasificacion):
    def entrenar(self, X, y): pass
    def predecir(self, X): pass


class ModeloRegresionLineal(Regresion):
    def entrenar(self, X, y): pass
    def predecir(self, X): pass


class ModeloMetricas:
    def evaluar(self, modelo, X_test, y_test): pass
