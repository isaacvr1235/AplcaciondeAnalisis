from pipeline.pipeline import Pipeline
from data.data import DataLoader
from transformers.transformers import ProcesadorDatos
from models.models import ModeloRegresionLineal
from evaluation.metrics import Metricas

class Main:
    def main(self):
        loader = DataLoader()
        dataset = loader.cargar("estudiantes (1).csv")

        pipeline = Pipeline()
        
        paso_limpieza = ProcesadorDatos(accion='limpieza', metodo=2, columnas=['Edad', 'Promedio'])
        pipeline.agregar_paso(paso_limpieza)

        paso_escalado = ProcesadorDatos(accion='scaler', metodo=1, columnas=['Edad', 'Promedio'])
        pipeline.agregar_paso(paso_escalado)

        modelo = ModeloRegresionLineal()
        metricas = Metricas()

        pipeline.modelo = modelo
        pipeline.metricas = metricas

        pipeline.ejecutar(dataset)

if _name_ == "_main_":
    Main().main()
