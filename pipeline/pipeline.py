from data.data import DataSplitter


class Pipeline:

    def _init_(self):
        self.pasos = []
        self.modelo = None
        self.metricas = None
        self.splitter = DataSplitter()

    def agregar_paso(self, transformacion):
        self.pasos.append(transformacion)

    def ejecutar(self, dataset):

        for paso in self.pasos:
            dataset = paso.fit_transform(dataset)

        split = self.splitter.split(dataset)

        X_train = split.train
        X_test = split.test

        if self.modelo:
            self.modelo.entrenar(X_train, None)
            pred = self.modelo.predecir(X_test)

        if self.metricas:
            self.metricas.calcular_metricas(None, pred)
        
