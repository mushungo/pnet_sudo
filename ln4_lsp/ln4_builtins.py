# =============================================================================
# ln4_lsp/ln4_builtins.py — Registro de funciones y constantes built-in de LN4
# =============================================================================
# Carga el catálogo de funciones desde ln4_lsp/data/ln4_builtins.json
# y define las constantes predefinidas del lenguaje.
#
# El JSON se genera con: python -m ln4_lsp.tools.export_builtins
# =============================================================================

import json
import os
import logging

logger = logging.getLogger("ln4-lsp")


# =============================================================================
# Constantes predefinidas de LN4
# =============================================================================
# Estas constantes se parsean como IDENTIFIER en la gramática y se resuelven
# aquí en el análisis semántico. Extraídas del corpus real (66 M4_ únicas + otras).

LN4_CONSTANTS = {
    # -- Booleanos / Resultado --
    "M4_TRUE", "M4_FALSE",
    "M4_SUCCESS", "M4_ERROR",

    # -- Comparación (usados como argumentos, no como operadores) --
    "M4_EQUAL", "EQUAL",
    "GREATER", "GREATER_OR_EQUAL",
    "LESS", "LESS_OR_EQUAL",
    "NOT_EQUAL",

    # -- Valores especiales --
    "NULL", "NOTHING", "EMPTY",
    "M4_MINUS_INF", "M4_PLUS_INF",

    # -- Logging --
    "M4_ERRORLOG", "M4_DEBUGINFOLOG", "M4_WARNINGLOG",

    # -- Autoload --
    "M4_AUTOLOAD_OFF", "M4_AUTOLOAD_NODESAYS",

    # -- Instance sharing --
    "M4_INSTANCE_GLOBAL_SHARED", "M4_INSTANCE_NOT_SHARED",

    # -- Rollback --
    "M4_ROLLBACK", "M4_ROLLBACK_RESUME",

    # -- Trimming --
    "M4_TRIM_ALL",

    # -- Tipos --
    "M4_TYPE_FIELD",

    # -- Scope --
    "M4_SCOPE_REGISTER", "M4_SCOPE_ALL",

    # -- Cadenas especiales --
    "M4_CR", "M4_TAB", "M4_NEW_LINE", "M4_DOUBLE_QUOTE",

    # -- Tiempo --
    "M4_DAY", "M4_MONTH", "M4_YEAR", "M4_TIMESTAMP",

    # -- Otros frecuentes --
    "M4_RETURN",
    "M4_ORGANIZATION_L2_TYPE_FATHER",
}


# =============================================================================
# Catálogo de funciones built-in
# =============================================================================
class LN4FunctionCatalog:
    """Catálogo de funciones built-in de LN4, cargado desde JSON.

    Proporciona:
        - Verificación de existencia de funciones
        - Validación de aridad (número de argumentos)
        - Acceso a metadatos (descripción, argumentos, grupo)
    """

    def __init__(self):
        self._functions = {}
        self._loaded = False

    def load(self, json_path=None):
        """Carga el catálogo desde el archivo JSON.

        Args:
            json_path: Ruta al archivo JSON. Si es None, usa la ruta por defecto.
        """
        if json_path is None:
            json_path = os.path.join(
                os.path.dirname(__file__), "data", "ln4_builtins.json"
            )

        if not os.path.exists(json_path):
            logger.warning(
                "Catálogo de funciones no encontrado: %s. "
                "Ejecutar: python -m ln4_lsp.tools.export_builtins",
                json_path,
            )
            self._loaded = False
            return False

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._functions = {}
            for name, func_data in data.get("functions", {}).items():
                # Normalizar a uppercase para búsqueda case-insensitive
                self._functions[name.upper()] = func_data

            self._loaded = True
            logger.info("Catálogo cargado: %d funciones", len(self._functions))
            return True

        except Exception as e:
            logger.error("Error al cargar catálogo: %s", e)
            self._loaded = False
            return False

    @property
    def is_loaded(self):
        """Indica si el catálogo fue cargado exitosamente."""
        return self._loaded

    def has_function(self, name):
        """Verifica si una función existe en el catálogo.

        Args:
            name: Nombre de la función (case-insensitive).

        Returns:
            True si la función existe.
        """
        return name.upper() in self._functions

    def get_function(self, name):
        """Obtiene los metadatos de una función.

        Args:
            name: Nombre de la función (case-insensitive).

        Returns:
            Dict con metadatos de la función, o None si no existe.
        """
        return self._functions.get(name.upper())

    def validate_args(self, name, arg_count):
        """Valida el número de argumentos de una llamada a función.

        Args:
            name: Nombre de la función.
            arg_count: Número de argumentos proporcionados.

        Returns:
            None si es válido, o string con mensaje de error.
        """
        func = self.get_function(name)
        if func is None:
            return None  # Función desconocida, no validar aquí

        min_args = func.get("min_args", 0)
        max_args = func.get("max_args")  # None = argumentos variables

        if max_args is None:
            # Función con argumentos variables: solo validar mínimo
            if arg_count < min_args:
                return (
                    f"'{func['name']}' requiere al menos {min_args} argumento(s), "
                    f"se proporcionaron {arg_count}"
                )
        else:
            if arg_count < min_args:
                return (
                    f"'{func['name']}' requiere al menos {min_args} argumento(s), "
                    f"se proporcionaron {arg_count}"
                )
            if arg_count > max_args:
                return (
                    f"'{func['name']}' acepta como máximo {max_args} argumento(s), "
                    f"se proporcionaron {arg_count}"
                )

        return None

    def get_all_names(self):
        """Retorna un set con todos los nombres de funciones (uppercase)."""
        return set(self._functions.keys())

    def __len__(self):
        return len(self._functions)


# -- Instancia global del catálogo (singleton) --------------------------------
_catalog = None


def get_catalog():
    """Obtiene la instancia singleton del catálogo de funciones.

    Se carga automáticamente la primera vez.
    """
    global _catalog
    if _catalog is None:
        _catalog = LN4FunctionCatalog()
        _catalog.load()
    return _catalog


def is_known_constant(name):
    """Verifica si un nombre es una constante predefinida de LN4.

    Args:
        name: Nombre del identificador (case-insensitive).

    Returns:
        True si es una constante conocida.
    """
    return name.upper() in LN4_CONSTANTS
