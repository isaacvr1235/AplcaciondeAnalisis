"""
utils/helpers.py
Funciones auxiliares reutilizables en todo el proyecto.
"""

import os
import re

# ── Constantes de presentación ────────────────────────

SEPARATOR = "\n" + "=" * 60
LINE = "─" * 45

# ── Colores ANSI para terminal ────────────────────────

class Color:
    """Códigos ANSI para resaltar texto en terminal."""
    OK      = "\033[92m"   # verde
    WARN    = "\033[93m"   # amarillo
    FAIL    = "\033[91m"   # rojo
    INFO    = "\033[96m"   # cyan
    BOLD    = "\033[1m"
    RESET   = "\033[0m"

    @staticmethod
    def ok(texto):
        return f"{Color.OK}{texto}{Color.RESET}"

    @staticmethod
    def warn(texto):
        return f"{Color.WARN}{texto}{Color.RESET}"

    @staticmethod
    def fail(texto):
        return f"{Color.FAIL}{texto}{Color.RESET}"

    @staticmethod
    def info(texto):
        return f"{Color.INFO}{texto}{Color.RESET}"

    @staticmethod
    def bold(texto):
        return f"{Color.BOLD}{texto}{Color.RESET}"


# ── Input seguro ──────────────────────────────────────

def pedir_input(mensaje, default=None, validar=None, opciones=None):
    """
    Solicita input al usuario con validación opcional.

    Args:
        mensaje: Texto a mostrar.
        default: Valor por defecto si el usuario presiona Enter.
        validar: Función que recibe el valor y retorna True/False.
        opciones: Lista de valores válidos (case-insensitive).

    Returns:
        str: Valor ingresado (o default).
    """
    sufijo = f" [{default}]" if default else ""
    while True:
        valor = input(f"  {mensaje}{sufijo}: ").strip()
        if not valor and default is not None:
            return default
        if not valor:
            print(f"  {Color.warn('⚠')} Este campo es obligatorio.")
            continue
        if opciones:
            if valor.lower() not in [o.lower() for o in opciones]:
                print(f"  {Color.warn('⚠')} Opciones válidas: {', '.join(opciones)}")
                continue
        if validar and not validar(valor):
            continue
        return valor


def pedir_si_no(mensaje, default="s"):
    """Pregunta sí/no y retorna True/False."""
    sufijo = "[S/n]" if default == "s" else "[s/N]"
    while True:
        resp = input(f"  {mensaje} {sufijo}: ").strip().lower()
        if not resp:
            return default == "s"
        if resp in ("s", "si", "sí", "y", "yes"):
            return True
        if resp in ("n", "no"):
            return False
        print(f"  {Color.warn('⚠')} Responda s o n.")


def pedir_opcion(opciones_dict, mensaje="Seleccione una opción"):
    """
    Muestra opciones numeradas y retorna la clave seleccionada.

    Args:
        opciones_dict: dict {clave: descripción}
        mensaje: Texto del prompt.

    Returns:
        str: Clave seleccionada.
    """
    claves = list(opciones_dict.keys())
    for clave in claves:
        print(f"  {clave}. {opciones_dict[clave]}")
    while True:
        op = input(f"\n  {mensaje}: ").strip()
        if op in claves:
            return op
        print(f"  {Color.warn('⚠')} Opción no válida. Intente de nuevo.")


# ── Validaciones ──────────────────────────────────────

def validar_ruta_archivo(ruta, extensiones=None):
    """
    Valida que un archivo exista y opcionalmente que tenga
    una extensión permitida.

    Returns:
        tuple: (es_valido: bool, mensaje: str)
    """
    if not os.path.isfile(ruta):
        return False, f"Archivo no encontrado: {ruta}"
    if extensiones:
        ext = os.path.splitext(ruta)[1].lower()
        if ext not in extensiones:
            return False, f"Extensión '{ext}' no soportada. Permitidas: {extensiones}"
    return True, "OK"


def validar_url(url):
    """Validación básica de formato URL."""
    patron = re.compile(
        r'^https?://'
        r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*'
        r'[a-zA-Z]{2,}'
        r'(?:/[^\s]*)?$'
    )
    return bool(patron.match(url))


def validar_puerto(valor):
    """Verifica que el valor sea un puerto válido (1-65535)."""
    try:
        p = int(valor)
        return 1 <= p <= 65535
    except ValueError:
        return False


# ── Formateo ──────────────────────────────────────────

def titulo_seccion(texto, ancho=60):
    """Imprime un título con formato de sección."""
    print(SEPARATOR)
    print(f"  {texto}")
    print("=" * ancho)


def mostrar_exito(mensaje):
    print(f"  {Color.ok('✔')} {mensaje}")


def mostrar_error(mensaje):
    print(f"  {Color.fail('✖')} {mensaje}")


def mostrar_advertencia(mensaje):
    print(f"  {Color.warn('⚠')} {mensaje}")


def mostrar_info(mensaje):
    print(f"  {Color.info('ℹ')} {mensaje}")


def pausar():
    """Pausa hasta que el usuario presione Enter."""
    input(f"\n  Presione ENTER para continuar...")
