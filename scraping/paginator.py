"""
scraping/paginator.py
Detección y navegación de paginación en sitios web.
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from utils.helpers import mostrar_exito, mostrar_error, mostrar_info, mostrar_advertencia


class Paginator:
    """Detecta y navega la paginación de un sitio web."""

    SELECTORES_AUTO = [
        "a.next", "a.next-page", "a[rel='next']",
        ".pagination a:last-child", ".pager .next a",
        "a[aria-label='Next']", "a[aria-label='Siguiente']",
        "li.next a", ".next a", "[class*='next'] a",
        "a:contains('Next')", "a:contains('Siguiente')",
        "a:contains('»')", "a:contains('→')",
    ]

    def __init__(self, headers=None, timeout=15, delay=1.5):
        self.headers = headers or {
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"),
        }
        self.timeout = timeout
        self.delay = delay

    def detectar_paginacion(self, soup, url_actual):
        """
        Intenta detectar automáticamente el enlace de siguiente página.
        Retorna la URL de la siguiente página o None.
        """
        for selector in self.SELECTORES_AUTO:
            try:
                elem = soup.select_one(selector)
                if elem and elem.get("href"):
                    next_url = urljoin(url_actual, elem["href"])
                    if next_url != url_actual:
                        return next_url
            except Exception:
                continue

        # Buscar por texto
        for texto in ["Next", "Siguiente", "›", "»", "→"]:
            elem = soup.find("a", string=re.compile(re.escape(texto), re.I))
            if elem and elem.get("href"):
                next_url = urljoin(url_actual, elem["href"])
                if next_url != url_actual:
                    return next_url

        return None

    def detectar_por_selector(self, soup, selector, url_actual):
        """Usa un selector CSS personalizado para encontrar siguiente página."""
        try:
            elem = soup.select_one(selector)
            if elem and elem.get("href"):
                return urljoin(url_actual, elem["href"])
        except Exception as e:
            mostrar_error(f"Error con selector de paginación: {e}")
        return None

    def iterar_paginas(self, url_inicio, selector=None, max_paginas=10):
        """
        Itera sobre las páginas de un sitio. Retorna lista de
        (url, soup) por cada página visitada.

        Args:
            url_inicio: URL de la primera página.
            selector: selector CSS para "siguiente" (None = auto-detectar).
            max_paginas: máximo de páginas a visitar.

        Returns:
            list de tuples (url, BeautifulSoup)
        """
        paginas = []
        urls_visitadas = set()
        url_actual = url_inicio
        dominio = urlparse(url_inicio).netloc

        for i in range(1, max_paginas + 1):
            if url_actual in urls_visitadas:
                mostrar_advertencia(f"Loop detectado en página {i}. Deteniendo.")
                break

            # No salir del dominio
            if urlparse(url_actual).netloc != dominio:
                mostrar_advertencia(f"URL fuera del dominio original. Deteniendo.")
                break

            urls_visitadas.add(url_actual)

            try:
                mostrar_info(f"Página {i}: {url_actual}")
                resp = requests.get(url_actual, headers=self.headers, timeout=self.timeout)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                paginas.append((url_actual, soup))

            except Exception as e:
                mostrar_error(f"Error en página {i}: {e}")
                break

            # Buscar siguiente
            if selector:
                next_url = self.detectar_por_selector(soup, selector, url_actual)
            else:
                next_url = self.detectar_paginacion(soup, url_actual)

            if not next_url:
                mostrar_info(f"No se encontró siguiente página. Total: {i}")
                break

            url_actual = next_url

            if i < max_paginas:
                time.sleep(self.delay)

        return paginas
