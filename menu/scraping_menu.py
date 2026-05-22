"""
menu/scraping_menu.py
Menú wizard interactivo para Web Scraping.
Guía al usuario paso a paso sin nada hardcodeado.
"""

import pandas as pd
from utils.helpers import (
    titulo_seccion, mostrar_exito, mostrar_error, mostrar_advertencia,
    mostrar_info, pedir_input, pedir_si_no, pedir_opcion, SEPARATOR
)
from scraping.validators import (
    validar_url, verificar_sitio, detectar_tipo_pagina,
    validar_selector_css, validar_xpath
)
from scraping.scraper import Scraper
from scraping.extractor import Extractor
from scraping.cleaner import Cleaner
from scraping.exporter import Exporter
from data.data import Dataset


def wizard_scraping(datasets_cargados, output_dir="output"):
    """
    Flujo wizard completo de Web Scraping.
    Retorna los datasets generados (o dict vacío si se cancela).
    """
    titulo_seccion("Web Scraping — Wizard Interactivo")

    # ══════════════════════════════════════════
    # PASO 1: Ingreso de URL
    # ══════════════════════════════════════════
    print("\n  ── Paso 1: URL del sitio web ──\n")

    url = pedir_input("Ingrese la URL del sitio web")
    es_valida, url = validar_url(url)
    if not es_valida:
        mostrar_error(f"URL no válida: {url}")
        return {}

    # Verificar accesibilidad
    info_sitio = verificar_sitio(url)
    if not info_sitio["exito"]:
        if not pedir_si_no("El sitio no respondió correctamente. ¿Desea intentar de todos modos?", default="n"):
            return {}

    response = info_sitio.get("response")
    url_final = info_sitio.get("url_final", url)

    # ══════════════════════════════════════════
    # PASO 2: Tipo de scraping
    # ══════════════════════════════════════════
    print(f"\n  ── Paso 2: Tipo de scraping ──\n")

    tipo_opcion = pedir_opcion({
        "1": "HTML estático (requests + BeautifulSoup)",
        "2": "Página dinámica (JavaScript) — requiere Selenium",
        "3": "Detectar automáticamente",
    }, "Seleccione tipo de scraping")

    tipo_scraping = "estatico"

    if tipo_opcion == "3" and response:
        tipo_scraping = detectar_tipo_pagina(response)
    elif tipo_opcion == "2":
        tipo_scraping = "dinamico"

    if tipo_scraping == "dinamico":
        mostrar_advertencia("Scraping dinámico seleccionado.")
        mostrar_info("Se requiere Selenium + Chrome/Firefox. Verificando...")
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            mostrar_exito("Selenium disponible.")
        except ImportError:
            mostrar_error("Selenium no está instalado.")
            mostrar_info("Instálelo con: pip install selenium")
            mostrar_info("Continuando con scraping estático como alternativa.")
            tipo_scraping = "estatico"

    # Obtener HTML
    scraper = Scraper()

    if tipo_scraping == "estatico":
        from bs4 import BeautifulSoup
        if response:
            soup = BeautifulSoup(response.text, "html.parser")
            html_text = response.text
        else:
            soup, resp = scraper.descargar(url_final)
            if not soup:
                mostrar_error("No se pudo descargar el HTML.")
                return {}
            html_text = resp.text
    else:
        # Scraping dinámico con Selenium
        soup, html_text = _scraping_selenium(url_final)
        if not soup:
            return {}

    extractor = Extractor(soup, url_base=url_final)

    # ══════════════════════════════════════════
    # PASO 3: Selección de datos a extraer
    # ══════════════════════════════════════════
    print(f"\n  ── Paso 3: ¿Qué desea extraer? ──\n")
    print("  Puede seleccionar múltiples opciones separadas por coma.")
    print("  Ejemplo: 1,3,5\n")

    opciones_datos = {
        "1": "Todo el contenido",
        "2": "Texto",
        "3": "Encabezados (h1-h6)",
        "4": "Párrafos",
        "5": "Tablas",
        "6": "Imágenes",
        "7": "Links",
        "8": "Productos (detección automática)",
        "9": "Correos electrónicos",
        "10": "Teléfonos",
        "11": "Redes sociales",
        "12": "Etiquetas HTML específicas",
        "13": "Selector CSS personalizado",
        "14": "XPath personalizado",
    }

    for k, v in opciones_datos.items():
        print(f"  {k:>2}. {v}")

    seleccion_raw = pedir_input("\nOpciones (separadas por coma)", default="1")
    seleccion = [s.strip() for s in seleccion_raw.split(",")]

    # Recopilar todos los datos extraídos
    todos_registros = []
    tablas_extraidas = []
    tipos_extraidos = []

    for sel in seleccion:
        if sel == "1":
            todos_registros.extend(extractor.extraer_todo())
            tipos_extraidos.append("todo")
        elif sel == "2":
            todos_registros.extend(extractor.extraer_texto())
            tipos_extraidos.append("texto")
        elif sel == "3":
            todos_registros.extend(extractor.extraer_encabezados())
            tipos_extraidos.append("encabezados")
        elif sel == "4":
            todos_registros.extend(extractor.extraer_parrafos())
            tipos_extraidos.append("parrafos")
        elif sel == "5":
            tablas = extractor.extraer_tablas()
            tablas_extraidas.extend(tablas)
            todos_registros.extend(extractor.extraer_tablas_como_registros())
            tipos_extraidos.append("tablas")
        elif sel == "6":
            todos_registros.extend(extractor.extraer_imagenes())
            tipos_extraidos.append("imagenes")
        elif sel == "7":
            todos_registros.extend(extractor.extraer_links())
            tipos_extraidos.append("links")
        elif sel == "8":
            todos_registros.extend(extractor.extraer_productos())
            tipos_extraidos.append("productos")
        elif sel == "9":
            todos_registros.extend(extractor.extraer_correos())
            tipos_extraidos.append("correos")
        elif sel == "10":
            todos_registros.extend(extractor.extraer_telefonos())
            tipos_extraidos.append("telefonos")
        elif sel == "11":
            todos_registros.extend(extractor.extraer_redes_sociales())
            tipos_extraidos.append("redes_sociales")
        elif sel == "12":
            registros = _wizard_etiquetas_html(extractor)
            todos_registros.extend(registros)
            tipos_extraidos.append("etiquetas_html")
        elif sel == "13":
            registros = _wizard_selector_css(extractor, soup)
            todos_registros.extend(registros)
            tipos_extraidos.append("selector_css")
        elif sel == "14":
            registros = _wizard_xpath(extractor, html_text)
            todos_registros.extend(registros)
            tipos_extraidos.append("xpath")

    # ══════════════════════════════════════════
    # PASO 4: Profundidad
    # ══════════════════════════════════════════
    if pedir_si_no("\n¿Desea hacer scraping con profundidad (seguir enlaces internos)?", default="n"):
        prof = pedir_opcion({
            "1": "Seguir enlaces internos — nivel 1",
            "2": "Seguir enlaces internos — nivel 2",
            "3": "Personalizado",
        }, "Profundidad")

        niveles = {"1": 1, "2": 2}
        if prof == "3":
            n = pedir_input("Nivel de profundidad (1-5)", default="1")
            try:
                nivel = min(int(n), 5)
            except ValueError:
                nivel = 1
        else:
            nivel = niveles[prof]

        max_pag = pedir_input("Máximo de páginas a visitar", default="20")
        try:
            max_pag = int(max_pag)
        except ValueError:
            max_pag = 20

        paginas = scraper.scraping_con_profundidad(url_final, profundidad=nivel,
                                                    max_paginas=max_pag)
        # Extraer de cada página adicional (la primera ya se procesó)
        for pag_url, pag_soup in paginas[1:]:
            ext_pag = Extractor(pag_soup, url_base=pag_url)
            for sel in seleccion:
                todos_registros.extend(_extraer_por_opcion(ext_pag, sel, pag_soup, ""))

    # ══════════════════════════════════════════
    # PASO 5: Paginación
    # ══════════════════════════════════════════
    if pedir_si_no("\n¿Desea detectar y seguir paginación?", default="n"):
        pag_modo = pedir_opcion({
            "1": "Detectar automáticamente",
            "2": "Selector CSS manual para 'siguiente'",
        }, "Modo de paginación")

        selector_next = None
        if pag_modo == "2":
            selector_next = pedir_input("Selector CSS del botón siguiente (ej: .next-page)")

        max_pag = pedir_input("Máximo de páginas", default="5")
        try:
            max_pag = int(max_pag)
        except ValueError:
            max_pag = 5

        paginas = scraper.scraping_con_paginacion(url_final, selector_next=selector_next,
                                                    max_paginas=max_pag)
        for pag_url, pag_soup in paginas[1:]:
            ext_pag = Extractor(pag_soup, url_base=pag_url)
            for sel in seleccion:
                todos_registros.extend(_extraer_por_opcion(ext_pag, sel, pag_soup, ""))

    # ══════════════════════════════════════════
    # PASO 6: Limitación
    # ══════════════════════════════════════════
    if len(todos_registros) > 0:
        print(f"\n  Se encontraron {len(todos_registros)} registros en total.")
        lim = pedir_opcion({
            "1": "Todos los registros",
            "2": "Primeros N registros",
        }, "¿Cuántos elementos conservar?")

        if lim == "2":
            n = pedir_input("¿Cuántos?", default="100")
            try:
                n = int(n)
                todos_registros = todos_registros[:n]
                mostrar_info(f"Limitado a {n} registros.")
            except ValueError:
                pass

    # ══════════════════════════════════════════
    # PASO 7: Limpieza
    # ══════════════════════════════════════════
    if todos_registros and pedir_si_no("\n¿Desea aplicar limpieza a los datos?", default="n"):
        print("\n  Opciones de limpieza (separadas por coma):")
        print("  1. Eliminar HTML residual")
        print("  2. Limpiar espacios")
        print("  3. Eliminar duplicados")
        print("  4. Normalizar texto (minúsculas)")
        print("  5. Eliminar caracteres especiales")
        print("  6. Convertir fechas")

        limp_sel = pedir_input("Opciones", default="1,2,3")
        mapa_limpieza = {
            "1": "html", "2": "espacios", "3": "duplicados",
            "4": "normalizar", "5": "caracteres", "6": "fechas"
        }
        opciones_limpieza = set()
        for s in limp_sel.split(","):
            s = s.strip()
            if s in mapa_limpieza:
                opciones_limpieza.add(mapa_limpieza[s])

        cleaner = Cleaner()
        antes = len(todos_registros)
        todos_registros = cleaner.aplicar_limpieza(todos_registros, opciones_limpieza)
        mostrar_exito(f"Limpieza aplicada. Registros: {antes} → {len(todos_registros)}")

    # ══════════════════════════════════════════
    # PASO 8: Vista previa
    # ══════════════════════════════════════════
    if not todos_registros and not tablas_extraidas:
        mostrar_advertencia("No se extrajeron datos.")
        return {}

    print(f"\n  ── Vista previa ──")
    print(f"  Registros encontrados: {len(todos_registros)}")

    if todos_registros:
        df = pd.DataFrame(todos_registros)
        print(f"  Columnas: {list(df.columns)}")
        print(f"\n{df.head(10).to_string(index=False)}")

    if tablas_extraidas:
        print(f"\n  Tablas HTML extraídas: {len(tablas_extraidas)}")
        for t in tablas_extraidas:
            print(f"    Tabla {t['numero']}: {t['dataframe'].shape}")

    # ══════════════════════════════════════════
    # PASO 9: Reporte de calidad
    # ══════════════════════════════════════════
    if todos_registros:
        _reporte_calidad(df)

    if not pedir_si_no("\n¿Desea continuar y guardar los resultados?"):
        mostrar_info("Scraping descartado.")
        return {}

    # ══════════════════════════════════════════
    # PASO 10: Guardado
    # ══════════════════════════════════════════
    print(f"\n  ── Guardado de resultados ──")
    exporter = Exporter(output_dir=output_dir)

    metadata = Exporter.crear_metadata(
        url=url_final,
        status_code=info_sitio.get("status_code", 0),
        tipo_scraping=tipo_scraping,
        tiempo_respuesta=info_sitio.get("tiempo_respuesta", 0),
        cantidad_registros=len(todos_registros),
        tipos_extraidos=tipos_extraidos,
    )

    datasets_resultado = {}

    if todos_registros:
        ruta = exporter.exportar_interactivo(df, metadata=metadata)
        if ruta:
            mostrar_exito(f"Datos guardados en: {ruta}")

        # Guardar como Dataset en memoria
        ds = Dataset(
            nombre="WebScraping",
            datos=df,
            origen=url_final,
            metadata={"formato": "Web Scraping", "tipos": tipos_extraidos}
        )
        clave = f"ws_{url_final.split('//')[1].split('/')[0].replace('.', '_')}"
        datasets_cargados[clave] = ds
        datasets_resultado[clave] = ds
        mostrar_exito(f"Dataset almacenado como '{clave}'")

    # Guardar tablas HTML como datasets separados
    for t in tablas_extraidas:
        clave_tabla = f"ws_tabla_{t['numero']}"
        ds_tabla = Dataset(
            nombre=f"Tabla_{t['numero']}_de_{url_final}",
            datos=t["dataframe"],
            origen=url_final,
            metadata={"formato": "Web Scraping", "tipo": "tabla_html"}
        )
        datasets_cargados[clave_tabla] = ds_tabla
        datasets_resultado[clave_tabla] = ds_tabla

    # ══════════════════════════════════════════
    # PASO 11: EDA opcional
    # ══════════════════════════════════════════
    if pedir_si_no("\n¿Desea realizar análisis exploratorio (EDA) de los datos extraídos?", default="n"):
        return datasets_resultado  # Señal al menú principal para lanzar EDA

    return datasets_resultado


# ══════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES DEL WIZARD
# ══════════════════════════════════════════════════════════════

def _wizard_etiquetas_html(extractor):
    """Sub-wizard para etiquetas HTML personalizadas."""
    print(f"\n  ── Etiquetas HTML personalizadas ──")
    etiquetas_raw = pedir_input("Ingrese etiquetas separadas por coma (ej: div, p, h1, span)")
    etiquetas = [e.strip() for e in etiquetas_raw.split(",")]

    clase_css = None
    if pedir_si_no("¿Desea filtrar por clase CSS?", default="n"):
        clase_css = pedir_input("Nombre de clase CSS (ej: product-card)")

    id_html = None
    if pedir_si_no("¿Desea filtrar por ID?", default="n"):
        id_html = pedir_input("ID del elemento (ej: main-content)")

    registros = extractor.extraer_por_etiquetas(etiquetas, clase_css=clase_css, id_html=id_html)
    mostrar_info(f"Encontrados: {len(registros)} elementos")

    if registros:
        print(f"  Vista previa:")
        for r in registros[:5]:
            print(f"    <{r['etiqueta']}> → {r['contenido'][:80]}...")

    return registros


def _wizard_selector_css(extractor, soup):
    """Sub-wizard para selector CSS personalizado."""
    print(f"\n  ── Selector CSS personalizado ──")
    selector = pedir_input("Ingrese selector CSS (ej: .product-card .price)")

    n, elementos = validar_selector_css(soup, selector)
    mostrar_info(f"Elementos encontrados: {n}")

    if n == 0:
        mostrar_advertencia("El selector no encontró elementos.")
        return []

    registros = extractor.extraer_por_css(selector)

    if registros:
        print(f"  Vista previa:")
        for r in registros[:5]:
            print(f"    [{r['numero']}] {r['contenido'][:80]}...")

    return registros


def _wizard_xpath(extractor, html_text):
    """Sub-wizard para XPath personalizado."""
    print(f"\n  ── XPath personalizado ──")
    xpath = pedir_input("Ingrese expresión XPath (ej: //div[@class='product'])")

    n, elementos = validar_xpath(html_text, xpath)
    mostrar_info(f"Elementos encontrados: {n}")

    if n == 0:
        mostrar_advertencia("El XPath no encontró elementos.")
        return []

    registros = extractor.extraer_por_xpath(xpath, html_text)

    if registros:
        print(f"  Vista previa:")
        for r in registros[:5]:
            print(f"    [{r['numero']}] {r['contenido'][:80]}...")

    return registros


def _extraer_por_opcion(extractor, opcion, soup, html_text):
    """Extrae datos según la opción numérica (para páginas adicionales)."""
    mapa = {
        "1": extractor.extraer_todo,
        "2": extractor.extraer_texto,
        "3": extractor.extraer_encabezados,
        "4": extractor.extraer_parrafos,
        "6": extractor.extraer_imagenes,
        "7": extractor.extraer_links,
        "8": extractor.extraer_productos,
        "9": extractor.extraer_correos,
        "10": extractor.extraer_telefonos,
        "11": extractor.extraer_redes_sociales,
    }
    if opcion in mapa:
        return mapa[opcion]()
    return []


def _reporte_calidad(df):
    """Muestra reporte de calidad de los datos extraídos."""
    print(f"\n  ── Reporte de calidad ──")

    total = len(df)
    tipos = df["tipo"].value_counts() if "tipo" in df.columns else pd.Series()

    for tipo, conteo in tipos.items():
        print(f"  ✔ {tipo}: {conteo} encontrados")

    # Campos vacíos
    if "contenido" in df.columns:
        vacios = df["contenido"].isna().sum() + (df["contenido"] == "").sum()
        if vacios > 0:
            print(f"  ⚠ Elementos vacíos: {vacios}")
        else:
            print(f"  ✔ Sin elementos vacíos")

    # Duplicados
    duplicados = df.duplicated().sum()
    if duplicados > 0:
        print(f"  ⚠ Registros duplicados: {duplicados}")
    else:
        print(f"  ✔ Sin duplicados")

    # Links rotos (si hay imágenes)
    if "src" in df.columns:
        sin_src = (df["src"] == "").sum() + df["src"].isna().sum()
        if sin_src > 0:
            print(f"  ⚠ Imágenes sin URL: {sin_src}")

    print(f"\n  Total registros: {total}")


def _scraping_selenium(url):
    """Realiza scraping con Selenium para páginas dinámicas."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from bs4 import BeautifulSoup
        import time

        mostrar_info("Iniciando navegador headless...")

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)

        mostrar_info(f"Cargando: {url}")
        driver.get(url)

        # Esperar a que cargue JavaScript
        time.sleep(3)

        html_text = driver.page_source
        soup = BeautifulSoup(html_text, "html.parser")

        driver.quit()
        mostrar_exito("Página dinámica cargada exitosamente.")

        return soup, html_text

    except Exception as e:
        mostrar_error(f"Error con Selenium: {e}")
        mostrar_info("Asegúrese de tener Chrome y ChromeDriver instalados.")
        return None, None
