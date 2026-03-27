import os
from data.data import DataLoader

def main():
    print("Iniciando el Pipeline de Ciencia de Datos...\n")
    
    loader = DataLoader()

    ruta_descargas = r"C:\Users\Isaac\Downloads\datasets"
    ruta_estudiantes = os.path.join(ruta_descargas, "estudiantes.csv")
    ruta_adicional = os.path.join(ruta_descargas, "StudentsPerformance.csv") 

    print("-" * 40)
    print("PRUEBA 1: Carga de estudiantes.csv")
    print("-" * 40)
    try:
        dataset_estudiantes = loader.cargar_csv(ruta_estudiantes)
        print("\nVista previa de los datos (head):")
        print(dataset_estudiantes.head())
        print(f"\nMetadatos: {dataset_estudiantes.n_filas} filas, {dataset_estudiantes.n_columnas} columnas.")
    except Exception as e:
        print(e)

    print("\n" + "-" * 40)
    print("PRUEBA 2: Carga de archivo adicional")
    print("-" * 40)
    try:
        dataset_adicional = loader.cargar_csv(ruta_adicional)
        print("\nVista previa de los datos (head):")
        print(dataset_adicional.head())
        print(f"\nMetadatos: {dataset_adicional.n_filas} filas, {dataset_adicional.n_columnas} columnas.")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
