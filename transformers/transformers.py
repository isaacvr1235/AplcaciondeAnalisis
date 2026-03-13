class Transformacion:

    def fit(self, dataset):
        pass

    def transform(self, dataset):
        return dataset

    def fit_transform(self, dataset):
        self.fit(dataset)
        return self.transform(dataset)


class LimpiadorNulos(Transformacion):

    def fit(self, dataset):
        pass

    def transform(self, dataset):
        pass


class Scaler(Transformacion):

    def _init_(self):
        self.mean = None
        self.std = None

    def fit(self, dataset):
        pass

    def transform(self, dataset):
        pass
    