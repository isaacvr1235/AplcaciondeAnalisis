from data.data import DataSplitter


class Pipeline:

    def __init__(self):
        self.pasos = []
        self.modelo = None
        self.metricas = None
        self.splitter = DataSplitter()

    def agregar_paso(self, transformacion):
        self.pasos.append(transformacion)

    def ejecutar(self, dataset):
        if dataset is None:
            print("  [Error] El dataset proporcionado está vacío o es nulo.")
            return

        # 1. Proteger el bucle de transformaciones
        for i, paso in enumerate(self.pasos):
            try:
                dataset = paso.fit_transform(dataset)
            except Exception as e:
                nombre_paso = paso.__class__.__name__
                print(f"  [Error] El pipeline falló en el paso {i+1} ({nombre_paso}).")
                print(f"  Detalle técnico: {e}")
                return  # Abortamos el pipeline si un paso falla

        # 2. Proteger la división de datos
        try:
            split = self.splitter.split(dataset)
            X_train = split.train
            X_test = split.test
        except Exception as e:
            print(f"  [Error] Falló la división de datos (Train/Test).")
            print(f"  Detalle técnico: {e}")
            return

        # 3. Proteger el entrenamiento y predicción
        if self.modelo:
            try:
                self.modelo.entrenar(X_train, None)
                pred = self.modelo.predecir(X_test)
            except Exception as e:
                print(f"  [Error] Falló el entrenamiento o predicción del modelo.")
                print(f"  Detalle técnico: {e}")
                return

            # 4. Proteger la evaluación (solo si el modelo tuvo éxito)
            if self.metricas:
                try:
                    self.metricas.calcular_metricas(None, pred)
                except Exception as e:
                    print(f"  [Error] Falló el cálculo de métricas de evaluación.")
                    print(f"  Detalle técnico: {e}")