class Dataset:

    def _init_(self, nombre=None, datos=None, origen=None, fecha_carga=None, metadata=None):
        self.nombre = nombre
        self.datos = datos
        self.origen = origen
        self.fecha_carga = fecha_carga
        self.metadata = metadata

    def get_dimensiones(self):
        return None

    def get_columnas(self):
        return None

    def get_datos(self):
        return self.datos

    def info(self):
        pass

    def head(self, n):
        return None

    def guardar(self, ruta):
        pass


class DataLoader:

    def cargar(self, ruta):
        pass


class DatasetSplit:

    def _init_(self, train, test):
        self.train = train
        self.test = test


class DataSplitter:

    def _init_(self, test_size=0.2, random_state=42):
        self.test_size = test_size
        self.random_state = random_state

    def split(self, dataset):

        train = dataset
        test = dataset

        return DatasetSplit(train, test)
    