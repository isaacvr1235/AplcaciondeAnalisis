"""
scraping/exporter.py
Exporta los resultados del scraping en diferentes formatos.
Genera metadata automáticamente.
"""

import os
import json
from datetime import datetime
import pandas as pd
from utils.helpers import mostrar_exito, mostrar_error, pedir_input, pedir_opcion


class Exporter:
    """Exporta datos del scraping a archivos en diferentes formatos."""

    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _generar_nombre(self, extension):
        """Genera nombre de archivo automático con timestamp."""
        ts = datetime.now().strftime("%Y_%m_%d_%H_%M")
        return f"scraping_{ts}.{extension}"

    def exportar_interactivo(self, df, metadata=None):
        """
        Flujo interactivo: pregunta formato y ruta, guarda archivo y metadata.

        Args:
            df: DataFrame con los datos.
            metadata: dict con metadata del scraping.

        Returns:
            str: ruta del archivo guardado.
        """
        print("\n  ¿En qué formato desea guardar los resultados?")
        formato = pedir_opcion({
            "1": "CSV",
            "2": "Excel (.xlsx)",
            "3": "JSON",
            "4": "TXT (tabulado)",
            "0": "No guardar",
        }, "Formato")

        if formato == "0":
            return None

        extensiones = {"1": "csv", "2": "xlsx", "3": "json", "4": "txt"}
        ext = extensiones[formato]

        nombre_auto = self._generar_nombre(ext)
        nombre = pedir_input("Nombre del archivo", default=nombre_auto)

        if not nombre.endswith(f".{ext}"):
            nombre += f".{ext}"

        ruta_dir = pedir_input("Directorio donde guardar", default=self.output_dir)
        os.makedirs(ruta_dir, exist_ok=True)
        ruta = os.path.join(ruta_dir, nombre)

        try:
            if formato == "1":
                self.guardar_csv(df, ruta)
            elif formato == "2":
                self.guardar_excel(df, ruta)
            elif formato == "3":
                self.guardar_json(df, ruta)
            elif formato == "4":
                self.guardar_txt(df, ruta)

            # Guardar metadata
            if metadata:
                ruta_meta = ruta.rsplit(".", 1)[0] + "_metadata.json"
                self.guardar_metadata(metadata, ruta_meta)

            return ruta

        except Exception as e:
            mostrar_error(f"Error al guardar: {e}")
            return None

    # ── Formatos individuales ─────────────────

    def guardar_csv(self, df, ruta):
        """Guarda DataFrame como CSV."""
        df.to_csv(ruta, index=False, encoding="utf-8-sig")
        mostrar_exito(f"CSV guardado: {ruta} ({len(df)} registros)")

    def guardar_excel(self, df, ruta):
        """Guarda DataFrame como Excel."""
        df.to_excel(ruta, index=False, engine="openpyxl")
        mostrar_exito(f"Excel guardado: {ruta} ({len(df)} registros)")

    def guardar_json(self, df, ruta):
        """Guarda DataFrame como JSON."""
        df.to_json(ruta, orient="records", force_ascii=False, indent=2)
        mostrar_exito(f"JSON guardado: {ruta} ({len(df)} registros)")

    def guardar_txt(self, df, ruta):
        """Guarda DataFrame como texto tabulado."""
        df.to_csv(ruta, index=False, sep="\t", encoding="utf-8-sig")
        mostrar_exito(f"TXT guardado: {ruta} ({len(df)} registros)")

    # ── Metadata ──────────────────────────────

    def guardar_metadata(self, metadata, ruta):
        """Guarda metadata del scraping como JSON."""
        metadata["fecha_exportacion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)
        mostrar_exito(f"Metadata guardada: {ruta}")

    @staticmethod
    def crear_metadata(url, status_code, tipo_scraping, tiempo_respuesta,
                       cantidad_registros, tipos_extraidos):
        """Crea el dict de metadata del scraping."""
        return {
            "url": url,
            "fecha_scraping": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status_http": status_code,
            "tipo_scraping": tipo_scraping,
            "tiempo_respuesta": f"{tiempo_respuesta}s",
            "cantidad_registros": cantidad_registros,
            "tipos_datos_extraidos": tipos_extraidos,
        }
