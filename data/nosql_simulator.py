import json
import random
import os
import pandas as pd
from datetime import datetime, timedelta
from data.data import Dataset


class SimuladorNoSQL:
    """
    Simula datos con estructura tipo documento (NoSQL).
    Genera colecciones de documentos JSON con campos anidados,
    listas y subdocumentos, imitando una base de datos documental
    como MongoDB.
    """

    def __init__(self, seed=42):
        random.seed(seed)
        self._carreras = [
            "Ingeniería en Sistemas", "Ingeniería Civil", "Medicina",
            "Derecho", "Arquitectura", "Psicología", "Contaduría",
            "Comunicación", "Biología", "Física"
        ]
        self._cursos = [
            "Cálculo", "Álgebra", "Programación", "Física",
            "Química", "Historia", "Inglés", "Ética",
            "Economía", "Biología", "Estadística", "Base de Datos"
        ]
        self._nombres = [
            "Miguel", "Ana", "Carlos", "Lucía", "Pedro",
            "María", "Javier", "Sofía", "Diego", "Valentina",
            "Andrés", "Camila", "Fernando", "Isabella", "Ricardo"
        ]
        self._apellidos = [
            "García", "Martínez", "López", "Hernández", "González",
            "Rodríguez", "Pérez", "Sánchez", "Ramírez", "Torres",
            "Flores", "Rivera", "Gómez", "Díaz", "Morales"
        ]

    # ── Generación de colecciones ─────────────

    def generar_estudiantes(self, n=15):
        """
        Genera n documentos de estudiantes con estructura anidada:
        - datos_personales: {nombre, apellido, edad, correo}
        - academico: {carrera, semestre, promedio, materias_cursadas}
        - contacto: {telefono, direccion: {calle, ciudad, cp}}
        """
        estudiantes = []
        for i in range(1, n + 1):
            nombre = random.choice(self._nombres)
            apellido = random.choice(self._apellidos)
            n_materias = random.randint(3, 6)
            materias = random.sample(self._cursos, n_materias)
            doc = {
                "_id": f"EST-{1000 + i}",
                "datos_personales": {
                    "nombre": nombre,
                    "apellido": apellido,
                    "edad": random.randint(18, 30),
                    "correo": f"{nombre.lower()}.{apellido.lower()}{i}@universidad.edu.mx"
                },
                "academico": {
                    "carrera": random.choice(self._carreras),
                    "semestre": random.randint(1, 12),
                    "promedio": round(random.uniform(6.0, 10.0), 2),
                    "materias_cursadas": materias
                },
                "contacto": {
                    "telefono": f"55{random.randint(10000000, 99999999)}",
                    "direccion": {
                        "calle": f"Calle {random.randint(1, 200)} #{random.randint(1, 500)}",
                        "ciudad": random.choice(["CDMX", "Guadalajara", "Monterrey",
                                                  "Puebla", "Querétaro"]),
                        "codigo_postal": f"{random.randint(10000, 99999)}"
                    }
                },
                "fecha_inscripcion": (datetime(2020, 1, 1) +
                                     timedelta(days=random.randint(0, 1800))
                                     ).strftime("%Y-%m-%d"),
                "activo": random.choice([True, True, True, False])
            }
            estudiantes.append(doc)
        return estudiantes

    def generar_cursos(self, n=12):
        """
        Genera n documentos de cursos con estructura anidada:
        - info: {nombre, departamento, creditos}
        - horario: [{dia, hora_inicio, hora_fin}]
        - profesor: {nombre, titulo}
        """
        departamentos = ["Ciencias Básicas", "Ingeniería", "Humanidades",
                         "Ciencias Sociales", "Ciencias de la Salud"]
        titulos = ["Dr.", "Mtro.", "Ing.", "Lic."]
        cursos = []
        for i in range(n):
            nombre_curso = self._cursos[i % len(self._cursos)]
            n_horarios = random.randint(1, 3)
            dias = random.sample(["Lunes", "Martes", "Miércoles",
                                  "Jueves", "Viernes"], n_horarios)
            hora_base = random.choice([7, 9, 11, 13, 15, 17])
            doc = {
                "_id": f"CUR-{200 + i}",
                "info": {
                    "nombre": nombre_curso,
                    "departamento": random.choice(departamentos),
                    "creditos": random.choice([4, 6, 8, 10])
                },
                "horario": [
                    {
                        "dia": dia,
                        "hora_inicio": f"{hora_base:02d}:00",
                        "hora_fin": f"{hora_base + 2:02d}:00"
                    } for dia in dias
                ],
                "profesor": {
                    "nombre": f"{random.choice(titulos)} {random.choice(self._nombres)} "
                              f"{random.choice(self._apellidos)}",
                    "titulo": random.choice(["Doctorado", "Maestría", "Licenciatura"])
                },
                "cupo_maximo": random.randint(20, 40),
                "inscritos": random.randint(10, 35)
            }
            cursos.append(doc)
        return cursos

    # ── Aplanar documentos → DataFrame ────────

    def aplanar_estudiantes(self, documentos):
        """Convierte documentos anidados de estudiantes a un DataFrame plano."""
        registros = []
        for doc in documentos:
            registro = {
                "id": doc["_id"],
                "nombre": doc["datos_personales"]["nombre"],
                "apellido": doc["datos_personales"]["apellido"],
                "edad": doc["datos_personales"]["edad"],
                "correo": doc["datos_personales"]["correo"],
                "carrera": doc["academico"]["carrera"],
                "semestre": doc["academico"]["semestre"],
                "promedio": doc["academico"]["promedio"],
                "num_materias": len(doc["academico"]["materias_cursadas"]),
                "materias": ", ".join(doc["academico"]["materias_cursadas"]),
                "telefono": doc["contacto"]["telefono"],
                "ciudad": doc["contacto"]["direccion"]["ciudad"],
                "codigo_postal": doc["contacto"]["direccion"]["codigo_postal"],
                "fecha_inscripcion": doc["fecha_inscripcion"],
                "activo": doc["activo"]
            }
            registros.append(registro)
        return pd.DataFrame(registros)

    def aplanar_cursos(self, documentos):
        """Convierte documentos anidados de cursos a un DataFrame plano."""
        registros = []
        for doc in documentos:
            dias = ", ".join([h["dia"] for h in doc["horario"]])
            horario_str = "; ".join(
                [f'{h["dia"]} {h["hora_inicio"]}-{h["hora_fin"]}' for h in doc["horario"]]
            )
            registro = {
                "id": doc["_id"],
                "curso": doc["info"]["nombre"],
                "departamento": doc["info"]["departamento"],
                "creditos": doc["info"]["creditos"],
                "profesor": doc["profesor"]["nombre"],
                "titulo_profesor": doc["profesor"]["titulo"],
                "dias": dias,
                "horario": horario_str,
                "cupo_maximo": doc["cupo_maximo"],
                "inscritos": doc["inscritos"],
                "ocupacion_pct": round(doc["inscritos"] / doc["cupo_maximo"] * 100, 1)
            }
            registros.append(registro)
        return pd.DataFrame(registros)

    # ── Método principal ──────────────────────

    def generar_y_convertir(self, output_dir=None):
        """
        Genera ambas colecciones, las guarda como JSON y las convierte
        a DataFrames envueltos en objetos Dataset.
        Retorna: (docs_est, docs_cur, dataset_est, dataset_cur)
        """
        docs_est = self.generar_estudiantes(15)
        docs_cur = self.generar_cursos(12)

        # Guardar JSON si se indica directorio
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "nosql_estudiantes.json"), "w",
                      encoding="utf-8") as f:
                json.dump(docs_est, f, ensure_ascii=False, indent=2)
            with open(os.path.join(output_dir, "nosql_cursos.json"), "w",
                      encoding="utf-8") as f:
                json.dump(docs_cur, f, ensure_ascii=False, indent=2)
            print(f"  ✔ JSON guardados en: {output_dir}")

        df_est = self.aplanar_estudiantes(docs_est)
        df_cur = self.aplanar_cursos(docs_cur)

        ds_est = Dataset(
            nombre="NoSQL_Estudiantes",
            datos=df_est,
            origen="Simulación NoSQL (documento)",
            metadata={"formato": "NoSQL/JSON", "entidades": "estudiantes",
                       "n_documentos": len(docs_est)}
        )
        ds_cur = Dataset(
            nombre="NoSQL_Cursos",
            datos=df_cur,
            origen="Simulación NoSQL (documento)",
            metadata={"formato": "NoSQL/JSON", "entidades": "cursos",
                       "n_documentos": len(docs_cur)}
        )

        print(f"  ✔ Colección 'estudiantes': {len(docs_est)} documentos → DataFrame {df_est.shape}")
        print(f"  ✔ Colección 'cursos':      {len(docs_cur)} documentos → DataFrame {df_cur.shape}")

        return docs_est, docs_cur, ds_est, ds_cur

    def mostrar_ejemplo_documento(self, doc):
        """Imprime un documento JSON formateado para demostración."""
        print(json.dumps(doc, ensure_ascii=False, indent=2))
