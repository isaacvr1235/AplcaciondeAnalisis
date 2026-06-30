"""
menu/api_menu.py
Wizard interactivo para la Extensión D del Examen Extraordinario:
integración de una nueva fuente de datos (API REST) al flujo existente.
"""

import os
import sys

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DIR)

from data.api_loader import APILoader
from utils.helpers import (
    titulo_seccion, mostrar_exito, mostrar_error, mostrar_advertencia,
    mostrar_info, pedir_input, pedir_si_no, pedir_opcion, validar_url
)

# APIs públicas de ejemplo que no requieren llave/autenticación,
# útiles para la demostración en vivo.
APIS_SUGERIDAS = {
    "1": {
        "nombre": "PokeAPI — lista de Pokémon",
        "url": "https://pokeapi.co/api/v2/pokemon",
        "params": {"limit": 50},
        "ruta_registros": "results",
    },
    "2": {
        "nombre": "REST Countries — países",
        "url": "https://restcountries.com/v3.1/all",
        "params": {"fields": "name,capital,population,region,area"},
        "ruta_registros": None,
    },
    "3": {
        "nombre": "JSONPlaceholder — usuarios de prueba",
        "url": "https://jsonplaceholder.typicode.com/users",
        "params": None,
        "ruta_registros": None,
    },
    "4": {
        "nombre": "Open-Meteo — clima actual CDMX",
        "url": "https://api.open-meteo.com/v1/forecast",
        "params": {"latitude": 19.43, "longitude": -99.13, "current_weather": "true"},
        "ruta_registros": None,
    },
}


def wizard_api(datasets_cargados, output_dir=None):
    """
    Wizard paso a paso para consultar una API y agregarla a datasets_cargados.
    Devuelve la lista de claves nuevas agregadas (para encadenar EDA),
    igual que wizard_scraping.
    """
    titulo_seccion("Extensión D — Integración de nueva fuente de datos (API)")

    loader = APILoader()
    nuevas_claves = []

    print("\n  APIs públicas sugeridas (sin necesidad de API key):")
    opciones = {k: v["nombre"] for k, v in APIS_SUGERIDAS.items()}
    opciones["5"] = "Ingresar una URL de API personalizada"
    opciones["0"] = "Volver al menú principal"

    sel = pedir_opcion(opciones, "Seleccione una opción")

    if sel == "0":
        return nuevas_claves

    if sel in APIS_SUGERIDAS:
        preset = APIS_SUGERIDAS[sel]
        url = preset["url"]
        params = preset["params"]
        ruta_registros = preset["ruta_registros"]
        print(f"\n  Endpoint: {url}")
        if params:
            print(f"  Parámetros: {params}")
    else:
        url = pedir_input("URL completa del endpoint (debe iniciar con http:// o https://)",
                           validar=validar_url)

        params = {}
        if pedir_si_no("¿Desea agregar parámetros de consulta (query params)?", default="n"):
            print("  Ingrese pares clave=valor. Deje vacío para terminar.")
            while True:
                par = input("  Parámetro (clave=valor): ").strip()
                if not par:
                    break
                if "=" not in par:
                    mostrar_advertencia("Formato inválido. Use clave=valor.")
                    continue
                clave, valor = par.split("=", 1)
                params[clave.strip()] = valor.strip()
        params = params or None

        mostrar_info(
            "Si la API envuelve los registros dentro de una clave "
            "(ej. {\"results\": [...]} o {\"data\": {\"items\": [...]}}), "
            "indique la ruta. Si no sabe, deje vacío para detección automática."
        )
        ruta_registros = pedir_input("Ruta de los registros dentro del JSON (opcional)",
                                      default="")
        ruta_registros = ruta_registros or None

    # ── Consultar y cargar ──────────────────────────────
    try:
        nombre_sugerido = APIS_SUGERIDAS.get(sel, {}).get("nombre", "API_dataset")
        nombre_sugerido = nombre_sugerido.split(" — ")[0].replace(" ", "_")
        nombre = pedir_input("Nombre para este dataset", default=nombre_sugerido)

        ds = loader.cargar_api(url, params=params, ruta_registros=ruta_registros, nombre=nombre)

    except (ConnectionError, ValueError, KeyError) as e:
        mostrar_error(str(e))
        return nuevas_claves
    except Exception as e:
        mostrar_error(f"Error inesperado al consultar la API: {e}")
        return nuevas_claves

    # ── Guardar en memoria ───────────────────────────────
    clave = nombre.lower().replace(" ", "_")
    if clave in datasets_cargados:
        i = 2
        while f"{clave}_{i}" in datasets_cargados:
            i += 1
        clave = f"{clave}_{i}"

    datasets_cargados[clave] = ds
    nuevas_claves.append(clave)

    ds.info()
    print("  Vista previa (primeras 5 filas):")
    print(ds.head(5).to_string(index=False))
    mostrar_exito(f"Dataset de API almacenado como '{clave}'")

    return nuevas_claves
