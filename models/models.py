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


class ModeloRegresionLineal(Regresion):

    def entrenar(self, X, y):
        pass

    def predecir(self, X):
        pass


class DecisionTree(Clasificacion):

    def entrenar(self, X, y):
        pass

    def predecir(self, X):
        pass


class LogisticRegression(Clasificacion):

    def entrenar(self, X, y):
        pass

    def predecir(self, X):
        pass


class ModeloMetricas:

    def evaluar(self, modelo, X_test, y_test):
        pass