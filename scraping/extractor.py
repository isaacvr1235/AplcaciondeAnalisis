"""
scraping/extractor.py
Extrae datos del HTML según las opciones seleccionadas por el usuario.
Cada método retorna una lista de dicts para convertir fácilmente a DataFrame.
"""

import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class Extractor:
    """Extrae diferentes tipos de datos de un objeto BeautifulSoup."""

    def __init__(self, soup, url_base=""):
        self.soup = soup
        self.url_base = url_base

    # ── Texto completo ────────────────────────

    def extraer_todo(self):
        """Extrae todo el contenido visible de la página."""
        registros = []
        registros.extend(self.extraer_encabezados())
        registros.extend(self.extraer_parrafos())
        registros.extend(self.extraer_links())
        registros.extend(self.extraer_imagenes())
        registros.extend(self.extraer_tablas_como_registros())
        return registros

    def extraer_texto(self):
        """Extrae todo el texto visible como registros."""
        registros = []
        for i, elem in enumerate(self.soup.find_all(string=True), 1):
            texto = elem.strip()
            if texto and elem.parent.name not in ("script", "style", "meta", "link"):
                registros.append({
                    "tipo": "texto",
                    "etiqueta": elem.parent.name,
                    "contenido": texto,
                    "longitud": len(texto),
                    "n_palabras": len(texto.split()),
                })
        return registros

    # ── Encabezados ───────────────────────────

    def extraer_encabezados(self):
        """Extrae encabezados h1-h6."""
        registros = []
        for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            for elem in self.soup.find_all(tag):
                texto = elem.get_text(strip=True)
                if texto:
                    registros.append({
                        "tipo": "encabezado",
                        "nivel": tag,
                        "contenido": texto,
                        "longitud": len(texto),
                        "n_palabras": len(texto.split()),
                    })
        return registros

    # ── Párrafos ──────────────────────────────

    def extraer_parrafos(self):
        """Extrae todos los párrafos."""
        registros = []
        for i, p in enumerate(self.soup.find_all("p"), 1):
            texto = p.get_text(strip=True)
            if texto:
                registros.append({
                    "tipo": "parrafo",
                    "numero": i,
                    "contenido": texto,
                    "longitud": len(texto),
                    "n_palabras": len(texto.split()),
                })
        return registros

    # ── Tablas ────────────────────────────────

    def extraer_tablas(self):
        """Extrae tablas HTML y las retorna como lista de DataFrames."""
        import pandas as pd
        tablas = []
        for i, table in enumerate(self.soup.find_all("table"), 1):
            try:
                dfs = pd.read_html(str(table))
                if dfs:
                    df = dfs[0]
                    tablas.append({"numero": i, "dataframe": df})
            except Exception:
                continue
        return tablas

    def extraer_tablas_como_registros(self):
        """Extrae tablas como registros planos para incluir en resultados generales."""
        registros = []
        for i, table in enumerate(self.soup.find_all("table"), 1):
            caption = table.find("caption")
            titulo = caption.get_text(strip=True) if caption else f"Tabla_{i}"
            filas = table.find_all("tr")
            registros.append({
                "tipo": "tabla",
                "numero": i,
                "titulo": titulo,
                "filas": len(filas),
                "contenido": f"Tabla con {len(filas)} filas",
            })
        return registros

    # ── Imágenes ──────────────────────────────

    def extraer_imagenes(self):
        """Extrae URLs y atributos de imágenes."""
        registros = []
        for img in self.soup.find_all("img"):
            src = img.get("src", "")
            if src:
                src = urljoin(self.url_base, src)
            registros.append({
                "tipo": "imagen",
                "src": src,
                "alt": img.get("alt", ""),
                "titulo": img.get("title", ""),
                "width": img.get("width", ""),
                "height": img.get("height", ""),
            })
        return registros

    # ── Links ─────────────────────────────────

    def extraer_links(self):
        """Extrae todos los enlaces."""
        registros = []
        for a in self.soup.find_all("a", href=True):
            href = a["href"]
            href_completo = urljoin(self.url_base, href)
            texto = a.get_text(strip=True)
            registros.append({
                "tipo": "link",
                "texto": texto,
                "href": href_completo,
                "es_externo": not href_completo.startswith(self.url_base),
            })
        return registros

    # ── Productos (heurística) ────────────────

    def extraer_productos(self):
        """
        Intenta detectar productos en la página buscando patrones comunes
        de e-commerce (nombre, precio, imagen).
        """
        registros = []

        # Buscar patrones de precio
        precio_regex = re.compile(r'[\$€£¥]\s*[\d,]+\.?\d*|\d+[\.,]\d{2}\s*(?:USD|MXN|EUR|GBP)')

        # Selectores comunes de productos
        selectores_producto = [
            "[class*='product']", "[class*='item']", "[class*='card']",
            "[data-product]", "[itemtype*='Product']",
            ".product", ".item", ".card",
        ]

        for selector in selectores_producto:
            elementos = self.soup.select(selector)
            if elementos:
                for elem in elementos:
                    nombre = ""
                    precio = ""
                    imagen = ""

                    # Buscar nombre en encabezados o links
                    for tag in ["h1", "h2", "h3", "h4", "a"]:
                        t = elem.find(tag)
                        if t and t.get_text(strip=True):
                            nombre = t.get_text(strip=True)
                            break

                    # Buscar precio
                    texto_elem = elem.get_text()
                    precios = precio_regex.findall(texto_elem)
                    if precios:
                        precio = precios[0]

                    # Buscar imagen
                    img = elem.find("img")
                    if img and img.get("src"):
                        imagen = urljoin(self.url_base, img["src"])

                    if nombre or precio:
                        registros.append({
                            "tipo": "producto",
                            "nombre": nombre[:200],
                            "precio": precio,
                            "imagen": imagen,
                        })
                if registros:
                    break  # Usar el primer selector que funcione

        return registros

    # ── Correos electrónicos ──────────────────

    def extraer_correos(self):
        """Extrae direcciones de correo electrónico."""
        texto = self.soup.get_text()
        patron = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
        correos = list(set(patron.findall(texto)))

        # También buscar en href mailto:
        for a in self.soup.find_all("a", href=True):
            if a["href"].startswith("mailto:"):
                email = a["href"].replace("mailto:", "").split("?")[0]
                if email not in correos:
                    correos.append(email)

        return [{"tipo": "correo", "contenido": c} for c in correos]

    # ── Teléfonos ─────────────────────────────

    def extraer_telefonos(self):
        """Extrae números de teléfono."""
        texto = self.soup.get_text()
        patron = re.compile(
            r'(?:\+?\d{1,3}[\s\-.]?)?\(?\d{2,4}\)?[\s\-.]?\d{3,4}[\s\-.]?\d{3,4}'
        )
        telefonos = list(set(patron.findall(texto)))

        # También buscar en href tel:
        for a in self.soup.find_all("a", href=True):
            if a["href"].startswith("tel:"):
                tel = a["href"].replace("tel:", "")
                if tel not in telefonos:
                    telefonos.append(tel)

        return [{"tipo": "telefono", "contenido": t.strip()} for t in telefonos if len(t.strip()) >= 7]

    # ── Redes sociales ────────────────────────

    def extraer_redes_sociales(self):
        """Extrae enlaces a redes sociales."""
        redes = {
            "facebook": re.compile(r'facebook\.com/[^"\s]+'),
            "twitter": re.compile(r'(?:twitter|x)\.com/[^"\s]+'),
            "instagram": re.compile(r'instagram\.com/[^"\s]+'),
            "linkedin": re.compile(r'linkedin\.com/[^"\s]+'),
            "youtube": re.compile(r'youtube\.com/[^"\s]+'),
            "tiktok": re.compile(r'tiktok\.com/[^"\s]+'),
            "github": re.compile(r'github\.com/[^"\s]+'),
        }
        registros = []
        html_text = str(self.soup)
        for red, patron in redes.items():
            encontrados = patron.findall(html_text)
            for url in set(encontrados):
                registros.append({
                    "tipo": "red_social",
                    "red": red,
                    "url": "https://" + url.rstrip('"\'/>)'),
                })
        return registros

    # ── Etiquetas HTML personalizadas ─────────

    def extraer_por_etiquetas(self, etiquetas, clase_css=None, id_html=None):
        """
        Extrae contenido de etiquetas HTML específicas.
        Opcionalmente filtra por clase CSS o ID.
        """
        registros = []
        for etiqueta in etiquetas:
            etiqueta = etiqueta.strip()
            filtros = {}
            if clase_css:
                filtros["class_"] = clase_css
            if id_html:
                filtros["id"] = id_html

            elementos = self.soup.find_all(etiqueta, **filtros)
            for elem in elementos:
                texto = elem.get_text(strip=True)
                if texto:
                    registros.append({
                        "tipo": "etiqueta_personalizada",
                        "etiqueta": etiqueta,
                        "clase": clase_css or "",
                        "id": id_html or "",
                        "contenido": texto[:500],
                        "longitud": len(texto),
                    })
        return registros

    # ── Selector CSS personalizado ────────────

    def extraer_por_css(self, selector):
        """Extrae contenido usando un selector CSS."""
        registros = []
        elementos = self.soup.select(selector)
        for i, elem in enumerate(elementos, 1):
            texto = elem.get_text(strip=True)
            registros.append({
                "tipo": "selector_css",
                "selector": selector,
                "numero": i,
                "contenido": texto[:500] if texto else "",
                "html": str(elem)[:300],
                "longitud": len(texto) if texto else 0,
            })
        return registros

    # ── XPath personalizado ───────────────────

    def extraer_por_xpath(self, xpath, html_text):
        """Extrae contenido usando XPath."""
        registros = []
        try:
            from lxml import etree
            tree = etree.HTML(html_text)
            elementos = tree.xpath(xpath)
            for i, elem in enumerate(elementos, 1):
                if hasattr(elem, "text"):
                    texto = elem.text or ""
                    texto_completo = etree.tostring(elem, encoding="unicode", method="text").strip()
                else:
                    texto_completo = str(elem).strip()

                registros.append({
                    "tipo": "xpath",
                    "xpath": xpath,
                    "numero": i,
                    "contenido": texto_completo[:500],
                    "longitud": len(texto_completo),
                })
        except Exception as e:
            from utils.helpers import mostrar_error
            mostrar_error(f"Error ejecutando XPath: {e}")

        return registros
