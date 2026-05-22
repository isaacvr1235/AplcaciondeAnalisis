# Aplicación de Análisis de Datos — IPN / ESCOM

## Descripción

Aplicación en Python que implementa un pipeline completo de ciencia de datos utilizando Programación Orientada a Objetos (POO). Cubre desde la carga y gestión de datos (CSV, TSV, SQL, NoSQL, Web Scraping) hasta el análisis exploratorio y la visualización de resultados.

## Requisitos

- Python 3.10 o superior
- Dependencias listadas en `requeriments.txt`

## Instalación

```bash
pip install -r requeriments.txt
```

## Ejecución

```bash
python main_eda.py
```

Se desplegará un menú interactivo con las siguientes opciones:

1. **Cargar archivo CSV** — Carga `estudiantes.csv`
2. **Cargar archivo TSV** — Carga `calificaciones.tsv`
3. **Conexión SQL** — Crea base de datos SQLite y permite consultas
4. **Análisis Exploratorio (EDA)** — Genera gráficos estadísticos por fuente de datos
5. **Simulación NoSQL** — Genera datos con estructura documental tipo MongoDB
6. **Web Scraping** — Extrae datos no estructurados de la web y los convierte a DataFrames
7. **Ver datasets cargados** — Lista todos los datasets en memoria

## Estructura del Proyecto

```
APLICACIONPARANALISIS/
├── main_eda.py              # Punto de entrada con menú interactivo
├── main.py                  # Skeleton del pipeline completo
├── data/
│   ├── data.py              # Dataset, DataLoader, DataSplitter
│   ├── nosql_simulator.py   # Simulación de datos NoSQL
│   └── web_scraper.py       # Web Scraping
├── visualization/
│   └── visualizador.py      # Gráficos EDA
├── models/
│   └── models.py            # Jerarquía de modelos ML
├── preprocessing/
│   └── transformers.py      # Transformaciones de datos
├── evaluation/
│   └── metrics.py           # Métricas de evaluación
├── pipeline/
│   └── pipeline.py          # Orquestador del flujo
├── output/                  # Gráficos e imágenes generados
├── estudiantes.csv          # Dataset de estudiantes
├── calificaciones.tsv       # Dataset de calificaciones
└── datos_universidad.xlsx   # Datos adicionales
```

## Integrantes

- Chávez Torres Alejandro
- Tavera Chamorro Manuel Alejandro
- Valle Ramírez José Isaac
