"""
scraping/cleaner.py
Limpieza de datos extraídos por el scraper.
"""

import re
import html as html_module


class Cleaner:
    """Aplica diferentes transformaciones de limpieza a los datos extraídos."""

    @staticmethod
    def limpiar_html(texto):
        """Elimina etiquetas HTML de un texto."""
        if not isinstance(texto, str):
            return texto
        limpio = re.sub(r'<[^>]+>', '', texto)
        return html_module.unescape(limpio)

    @staticmethod
    def limpiar_espacios(texto):
        """Normaliza espacios en blanco."""
        if not isinstance(texto, str):
            return texto
        texto = re.sub(r'\s+', ' ', texto)
        return texto.strip()

    @staticmethod
    def eliminar_caracteres_especiales(texto):
        """Elimina caracteres no alfanuméricos excepto puntuación básica."""
        if not isinstance(texto, str):
            return texto
        return re.sub(r'[^\w\s.,;:!?¿¡\-()@#$%&/=+\'"áéíóúñüÁÉÍÓÚÑÜ]', '', texto)

    @staticmethod
    def normalizar_texto(texto):
        """Convierte a minúsculas y normaliza."""
        if not isinstance(texto, str):
            return texto
        return texto.lower().strip()

    @staticmethod
    def convertir_fechas(texto):
        """Intenta detectar y normalizar formatos de fecha comunes."""
        if not isinstance(texto, str):
            return texto
        patrones = [
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', r'\3-\2-\1'),
            (r'(\d{1,2})-(\d{1,2})-(\d{4})', r'\3-\2-\1'),
        ]
        for patron, reemplazo in patrones:
            texto = re.sub(patron, reemplazo, texto)
        return texto

    def aplicar_limpieza(self, registros, opciones):
        """
        Aplica las limpiezas seleccionadas a una lista de registros (dicts).

        Args:
            registros: lista de dicts con los datos.
            opciones: set con las limpiezas a aplicar.
                Opciones: 'html', 'espacios', 'duplicados', 'normalizar',
                          'caracteres', 'fechas'

        Returns:
            lista de dicts limpiados.
        """
        campos_texto = ["contenido", "texto", "nombre", "alt", "titulo"]

        for reg in registros:
            for campo in campos_texto:
                if campo in reg and isinstance(reg[campo], str):
                    valor = reg[campo]
                    if "html" in opciones:
                        valor = self.limpiar_html(valor)
                    if "espacios" in opciones:
                        valor = self.limpiar_espacios(valor)
                    if "caracteres" in opciones:
                        valor = self.eliminar_caracteres_especiales(valor)
                    if "normalizar" in opciones:
                        valor = self.normalizar_texto(valor)
                    if "fechas" in opciones:
                        valor = self.convertir_fechas(valor)
                    reg[campo] = valor

        # Eliminar duplicados
        if "duplicados" in opciones:
            vistos = set()
            unicos = []
            for reg in registros:
                clave = str(sorted(reg.items()))
                if clave not in vistos:
                    vistos.add(clave)
                    unicos.append(reg)
            registros = unicos

        # Eliminar registros vacíos
        registros = [
            r for r in registros
            if any(v for k, v in r.items() if k in campos_texto and v)
        ]

        return registros
