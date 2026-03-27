class ProcesadorDatos:
    def _init_(self, accion, metodo, columnas=None):
        self.accion = accion
        self.metodo = metodo
        self.columnas = columnas

    def fit_transform(self, dataset):
        df = dataset.copy()
        cols = self.columnas if self.columnas is not None else df.columns

        if self.accion == 'limpieza':
            df[cols] = self.limpieza(df[cols], self.metodo)
        elif self.accion == 'scaler':
            df[cols] = self.scaler(df[cols], self.metodo)

        return df

    def limpieza(self, dataframe, metodo):
        if metodo == 1:
            pass
        elif metodo == 2:
            pass
        return dataframe

    def scaler(self, dataframe, metodo):
        if metodo == 1:
            pass
        elif metodo == 2:
            pass
        return dataframe

    
