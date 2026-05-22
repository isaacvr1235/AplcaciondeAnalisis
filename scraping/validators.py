"""
scraping/validators.py
Validaciones de URL, respuesta HTTP, selectores CSS/XPath.
"""

import re
import time
import requests
from urllib.parse import urlparse
from utils.helpers import mostrar_exito, mostrar_error, mostrar_info, mostrar_advertencia


def validar_url(url):
    """Valida formato de URL. Retorna (es_valida, url_corregida)."""
    if not url:
        return False, url

    # Agregar esquema si falta
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    patron = re.compile(
        r'^https?://'
        r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*'
        r'[a-zA-Z]{2,}'
        r'(?::\d{1,5})?'
        r'(?:/[^\s]*)?$'
    )
    return bool(patron.match(url)), url


def verificar_sitio(url, timeout=15, max_reintentos=2):
    """
    Verifica si el sitio responde. Retorna dict con info de la respuesta.
    Maneja timeout, redirecciones, errores de conexión.
    """
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    }

    for intento in range(1, max_reintentos + 1):
        try:
            inicio = time.time()
            resp = requests.get(
                url, headers=headers, timeout=timeout,
                allow_redirects=True
            )
            tiempo = round(time.time() - inicio, 2)

            resultado = {
                "exito": True,
                "status_code": resp.status_code,
                "status_text": resp.reason,
                "tiempo_respuesta": tiempo,
                "url_final": resp.url,
                "redireccion": resp.url != url,
                "content_type": resp.headers.get("Content-Type", ""),
                "encoding": resp.encoding,
                "tamaño": len(resp.content),
                "response": resp,
            }

            if resp.status_code == 200:
                mostrar_exito(f"Sitio accesible")
                print(f"  Status: {resp.status_code} {resp.reason}")
                print(f"  Tiempo de respuesta: {tiempo}s")
                print(f"  Tamaño: {len(resp.content):,} bytes")
                if resultado["redireccion"]:
                    mostrar_info(f"Redirigido a: {resp.url}")
            elif resp.status_code == 403:
                mostrar_advertencia(f"Acceso prohibido (403). El sitio puede bloquear scrapers.")
                resultado["exito"] = False
            elif resp.status_code == 404:
                mostrar_error(f"Página no encontrada (404).")
                resultado["exito"] = False
            elif resp.status_code >= 500:
                mostrar_error(f"Error del servidor ({resp.status_code}). Intente más tarde.")
                resultado["exito"] = False
            else:
                mostrar_advertencia(f"Status: {resp.status_code} {resp.reason}")

            return resultado

        except requests.exceptions.Timeout:
            mostrar_advertencia(f"Timeout en intento {intento}/{max_reintentos} ({timeout}s)")
        except requests.exceptions.ConnectionError:
            mostrar_error(f"No se pudo conectar al servidor (intento {intento}/{max_reintentos})")
        except requests.exceptions.TooManyRedirects:
            mostrar_error("Demasiadas redirecciones. URL posiblemente incorrecta.")
            return {"exito": False, "error": "too_many_redirects"}
        except requests.exceptions.RequestException as e:
            mostrar_error(f"Error de conexión: {e}")
            return {"exito": False, "error": str(e)}

        if intento < max_reintentos:
            mostrar_info(f"Reintentando en 2 segundos...")
            time.sleep(2)

    mostrar_error("No se pudo acceder al sitio web después de varios intentos.")
    return {"exito": False, "error": "max_reintentos"}


def detectar_tipo_pagina(response):
    """
    Intenta detectar si la página depende de JavaScript.
    Retorna 'estatico' o 'dinamico'.
    """
    html = response.text.lower()

    indicadores_js = [
        "react", "angular", "vue", "next", "nuxt",
        "__next", "__nuxt", "gatsby",
        "window.__initial", "window.__state",
        "data-reactroot", "ng-app", "v-app",
        '<div id="root"></div>',
        '<div id="app"></div>',
        "bundle.js", "chunk.js", "webpack",
    ]

    # Contar cuánto contenido visible hay vs scripts
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # Texto visible
    texto_visible = soup.get_text(strip=True)
    scripts = soup.find_all("script")
    n_scripts = len(scripts)

    conteo_indicadores = sum(1 for ind in indicadores_js if ind in html)

    es_dinamico = (
        conteo_indicadores >= 3
        or (len(texto_visible) < 200 and n_scripts > 5)
        or '<div id="root"></div>' in html
        or '<div id="app"></div>' in html
    )

    if es_dinamico:
        mostrar_info("Página detectada como DINÁMICA (depende de JavaScript)")
        mostrar_info(f"  Indicadores JS encontrados: {conteo_indicadores}")
        mostrar_info(f"  Scripts: {n_scripts}, Texto visible: {len(texto_visible)} chars")
    else:
        mostrar_info("Página detectada como ESTÁTICA (HTML renderizado)")
        mostrar_info(f"  Texto visible: {len(texto_visible)} chars, Scripts: {n_scripts}")

    return "dinamico" if es_dinamico else "estatico"


def validar_selector_css(soup, selector):
    """Valida un selector CSS contra el HTML. Retorna (n_encontrados, elementos)."""
    try:
        elementos = soup.select(selector)
        return len(elementos), elementos
    except Exception as e:
        mostrar_error(f"Selector CSS inválido: {e}")
        return 0, []


def validar_xpath(html_text, xpath):
    """Valida un XPath contra el HTML. Retorna (n_encontrados, elementos)."""
    try:
        from lxml import etree
        tree = etree.HTML(html_text)
        elementos = tree.xpath(xpath)
        return len(elementos), elementos
    except Exception as e:
        mostrar_error(f"XPath inválido: {e}")
        return 0, []


def obtener_dominio(url):
    """Extrae el dominio base de una URL."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"
