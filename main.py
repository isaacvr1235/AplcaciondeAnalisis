from pipeline.pipeline import Pipeline
from data.data import DataLoader
from transformers.transformers import LimpiadorNulos, Scaler
from models.models import ModeloRegresionLineal
from evaluation.metrics import Metricas


class Main:

    def main(self):

        loader = DataLoader()
        dataset = loader.cargar("datos.csv")

        pipeline = Pipeline()
        pipeline.agregar_paso(LimpiadorNulos())
        pipeline.agregar_paso(Scaler())

        modelo = ModeloRegresionLineal()
        metricas = Metricas()

        pipeline.modelo = modelo
        pipeline.metricas = metricas

        pipeline.ejecutar(dataset)


if _name_ == "_main_":
    Main().main()