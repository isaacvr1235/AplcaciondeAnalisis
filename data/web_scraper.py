import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from data.data import Dataset


class WebScraper:
    """
    Obtiene datos no estructurados de páginas web mediante Web Scraping
    y los convierte en información estructurada (DataFrames).
    """

    def __init__(self):
        self.headers = {
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8"
        }

    # ── Obtener HTML ──────────────────────────

    def obtener_html(self, url):
        """Descarga el HTML de una URL y retorna un objeto BeautifulSoup."""
        print(f"  Descargando: {url}")
        respuesta = requests.get(url, headers=self.headers, timeout=15)
        respuesta.raise_for_status()
        respuesta.encoding = respuesta.apparent_encoding
        soup = BeautifulSoup(respuesta.text, "html.parser")
        print(f"  ✔ HTML obtenido ({len(respuesta.text):,} caracteres)")
        return soup

    # ── Extraer repositorios trending de GitHub ──

    def scraping_github_trending(self, url="https://github.com/trending"):
        """
        Extrae los repositorios en tendencia de GitHub.
        Datos no estructurados (HTML) → DataFrame estructurado.
        """
        soup = self.obtener_html(url)

        articulos = soup.find_all("article", class_="Box-row")
        registros = []

        for art in articulos:
            # Nombre del repositorio
            h2 = art.find("h2")
            if not h2:
                continue
            enlace = h2.find("a")
            if not enlace:
                continue
            repo_path = enlace.get("href", "").strip("/")
            partes = repo_path.split("/")
            autor = partes[0] if len(partes) > 0 else ""
            nombre_repo = partes[1] if len(partes) > 1 else repo_path

            # Descripción
            desc_tag = art.find("p", class_=re.compile("col-9|my-1"))
            descripcion = desc_tag.get_text(strip=True) if desc_tag else ""

            # Lenguaje
            lang_span = art.find("span", itemprop="programmingLanguage")
            lenguaje = lang_span.get_text(strip=True) if lang_span else "N/A"

            # Estrellas totales
            estrellas_tags = art.find_all("a", class_="Link")
            estrellas_total = ""
            forks = ""
            for a_tag in estrellas_tags:
                href = a_tag.get("href", "")
                text = a_tag.get_text(strip=True)
                if "/stargazers" in href:
                    estrellas_total = text
                elif "/forks" in href:
                    forks = text

            # Estrellas hoy
            estrellas_hoy_span = art.find("span", class_="d-inline-block float-sm-right")
            estrellas_hoy = ""
            if estrellas_hoy_span:
                estrellas_hoy = estrellas_hoy_span.get_text(strip=True)
                estrellas_hoy = re.sub(r"[^\d,.]", "", estrellas_hoy)

            registros.append({
                "autor": autor,
                "repositorio": nombre_repo,
                "descripcion": descripcion[:150] if descripcion else "",
                "lenguaje": lenguaje,
                "estrellas": estrellas_total,
                "forks": forks,
                "estrellas_hoy": estrellas_hoy,
                "url": f"https://github.com/{repo_path}"
            })

        df = pd.DataFrame(registros)
        print(f"  ✔ Repositorios extraídos: {len(registros)}")
        return df

    # ── Extraer texto no estructurado genérico ──

    def extraer_texto(self, url):
        """
        Extrae texto no estructurado de una página web:
        título, párrafos, encabezados y listas.
        Retorna un diccionario con la información cruda.
        """
        soup = self.obtener_html(url)

        titulo = soup.find("title")
        titulo = titulo.get_text(strip=True) if titulo else "Sin título"

        encabezados = []
        for tag in ["h1", "h2", "h3"]:
            for h in soup.find_all(tag):
                texto = h.get_text(strip=True)
                if texto:
                    encabezados.append({"nivel": tag, "texto": texto})

        parrafos = [p.get_text(strip=True) for p in soup.find_all("p")
                    if p.get_text(strip=True)]

        listas = []
        for ul in soup.find_all(["ul", "ol"]):
            items = [li.get_text(strip=True) for li in ul.find_all("li")]
            if items:
                listas.append(items)

        resultado = {
            "titulo": titulo,
            "url": url,
            "n_encabezados": len(encabezados),
            "n_parrafos": len(parrafos),
            "n_listas": len(listas),
            "encabezados": encabezados,
            "parrafos": parrafos,
            "listas": listas
        }

        print(f"  ✔ Texto extraído: {len(encabezados)} encabezados, "
              f"{len(parrafos)} párrafos, {len(listas)} listas")

        return resultado

    # ── Convertir texto no estructurado → DataFrame ──

    def texto_a_dataframe(self, datos_texto, nombre="TextoWeb"):
        """
        Convierte el texto no estructurado extraído en DataFrames
        estructurados para análisis.
        Retorna: (ds_encabezados, ds_parrafos)
        """
        # DataFrame de encabezados
        if datos_texto["encabezados"]:
            df_enc = pd.DataFrame(datos_texto["encabezados"])
            df_enc["longitud"] = df_enc["texto"].str.len()
            df_enc["n_palabras"] = df_enc["texto"].str.split().str.len()
        else:
            df_enc = pd.DataFrame(columns=["nivel", "texto", "longitud", "n_palabras"])

        ds_enc = Dataset(
            nombre=f"{nombre}_encabezados",
            datos=df_enc,
            origen=datos_texto["url"],
            metadata={"formato": "Web Scraping", "tipo": "encabezados",
                       "pagina": datos_texto["titulo"]}
        )

        # DataFrame de párrafos
        if datos_texto["parrafos"]:
            registros = []
            for i, p in enumerate(datos_texto["parrafos"], 1):
                registros.append({
                    "parrafo_num": i,
                    "texto": p[:200] + "..." if len(p) > 200 else p,
                    "longitud": len(p),
                    "n_palabras": len(p.split())
                })
            df_par = pd.DataFrame(registros)
        else:
            df_par = pd.DataFrame(columns=["parrafo_num", "texto",
                                            "longitud", "n_palabras"])

        ds_par = Dataset(
            nombre=f"{nombre}_parrafos",
            datos=df_par,
            origen=datos_texto["url"],
            metadata={"formato": "Web Scraping", "tipo": "párrafos",
                       "pagina": datos_texto["titulo"]}
        )

        print(f"  ✔ Encabezados → DataFrame {df_enc.shape}")
        print(f"  ✔ Párrafos    → DataFrame {df_par.shape}")

        return ds_enc, ds_par

    # ── Método completo de demostración ───────

    def scraping_completo(self, url="https://github.com/trending", nombre="WebScraping"):
        """
        Realiza scraping completo:
        1. Si es GitHub trending → extrae repos como DataFrame
        2. Extrae texto no estructurado → DataFrames
        Retorna: dict con todos los datasets generados
        """
        print(f"\n{'=' * 55}")
        print(f"  Web Scraping: {url}")
        print(f"{'=' * 55}")

        resultado = {"repos": None, "encabezados": None, "parrafos": None}

        # Repositorios trending (datos tabulares desde HTML no estructurado)
        if "github.com/trending" in url:
            print("\n  --- Extracción de repositorios trending ---")
            df_repos = self.scraping_github_trending(url)
            ds_repos = Dataset(
                nombre=f"{nombre}_repos_trending",
                datos=df_repos,
                origen=url,
                metadata={"formato": "Web Scraping",
                          "tipo": "repositorios GitHub trending"}
            )
            resultado["repos"] = ds_repos

        # Texto no estructurado
        print("\n  --- Extracción de texto no estructurado ---")
        texto = self.extraer_texto(url)
        ds_enc, ds_par = self.texto_a_dataframe(texto, nombre)
        resultado["encabezados"] = ds_enc
        resultado["parrafos"] = ds_par

        return resultado
