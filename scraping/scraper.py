"""
scraping/scraper.py
Scraper principal: descarga HTML y coordina con el Extractor.
"""

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from utils.helpers import mostrar_exito, mostrar_error, mostrar_info, mostrar_advertencia
from scraping.extractor import Extractor
from scraping.paginator import Paginator


class Scraper:
    """
    Descarga HTML de sitios web y coordina la extracción de datos.
    Soporta profundidad de scraping y paginación.
    """

    def __init__(self, timeout=15, delay=1.0):
        self.timeout = timeout
        self.delay = delay
        self.headers = {
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        }
        self.paginator = Paginator(headers=self.headers, timeout=timeout, delay=delay)

    def descargar(self, url):
        """
        Descarga el HTML de una URL.
        Retorna (soup, response) o (None, None) si falla.
        """
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "html.parser")
            return soup, resp
        except Exception as e:
            mostrar_error(f"Error descargando {url}: {e}")
            return None, None

    def crear_extractor(self, soup, url):
        """Crea un Extractor para el HTML descargado."""
        from scraping.validators import obtener_dominio
        return Extractor(soup, url_base=obtener_dominio(url))

    def scraping_con_profundidad(self, url, profundidad=0, max_paginas=50):
        """
        Realiza scraping con profundidad de enlaces internos.

        Args:
            url: URL inicial.
            profundidad: 0=solo esta página, 1=seguir enlaces nivel 1, etc.
            max_paginas: máximo de páginas a visitar en total.

        Returns:
            list de tuples (url, BeautifulSoup)
        """
        dominio = urlparse(url).netloc
        visitadas = set()
        por_visitar = [(url, 0)]  # (url, nivel_actual)
        resultados = []

        while por_visitar and len(resultados) < max_paginas:
            url_actual, nivel = por_visitar.pop(0)

            if url_actual in visitadas:
                continue

            visitadas.add(url_actual)
            soup, resp = self.descargar(url_actual)

            if not soup:
                continue

            resultados.append((url_actual, soup))
            mostrar_info(f"[Nivel {nivel}] {url_actual}")

            # Si no hemos alcanzado la profundidad máxima, extraer enlaces
            if nivel < profundidad:
                for a in soup.find_all("a", href=True):
                    href = urljoin(url_actual, a["href"])
                    parsed = urlparse(href)
                    # Solo enlaces internos, sin fragmentos
                    if (parsed.netloc == dominio
                            and href not in visitadas
                            and not parsed.fragment):
                        href_limpio = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        if parsed.query:
                            href_limpio += f"?{parsed.query}"
                        if href_limpio not in visitadas:
                            por_visitar.append((href_limpio, nivel + 1))

                time.sleep(self.delay)

        mostrar_exito(f"Scraping completado: {len(resultados)} páginas visitadas")
        return resultados

    def scraping_con_paginacion(self, url, selector_next=None, max_paginas=10):
        """
        Realiza scraping siguiendo paginación.

        Args:
            url: URL de la primera página.
            selector_next: selector CSS para botón "siguiente" (None=auto).
            max_paginas: máximo de páginas.

        Returns:
            list de tuples (url, BeautifulSoup)
        """
        return self.paginator.iterar_paginas(url, selector=selector_next,
                                              max_paginas=max_paginas)
