# tools/general/db_utils.py
"""
Módulo centralizado de conexión a la base de datos.

Soporta múltiples proyectos y múltiples motores de BD (SQL Server, Oracle).
El proyecto activo se selecciona con la variable de entorno PNET_PROJECT
o con el argumento --project en los scripts que lo admitan.

Resolución del fichero .env (en orden de prioridad):
  1. projects/<PNET_PROJECT>/.env   si PNET_PROJECT está definido
  2. .env en la raíz del repo       como fallback de compatibilidad

Uso básico (sin cambios respecto a la versión anterior):
    from tools.general.db_utils import db_connection, get_dialect

    with db_connection() as conn:
        d = get_dialect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {d.select_prefix(10)} * FROM M4RCH_SENTENCES {d.select_suffix(10)}")

Las operaciones de conexión se trazan automáticamente si Database_trace=1
en regmeta.xml. Las trazas se escriben en .logs/pnet_sudo.log y .jsonl.
"""
import os
import re
import time
from contextlib import contextmanager

from dotenv import dotenv_values
from dotenv import load_dotenv

from tools.general.trace import db_tracer


# ---------------------------------------------------------------------------
# Resolución de configuración por proyecto
# ---------------------------------------------------------------------------

def _resolve_env_path():
    """Localiza el fichero .env correcto según PNET_PROJECT.

    Returns:
        str: Ruta absoluta al fichero .env a cargar.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    pnet_project = os.environ.get("PNET_PROJECT", "").strip()

    if pnet_project:
        candidate = os.path.join(project_root, "projects", pnet_project, ".env")
        if os.path.isfile(candidate):
            return candidate
        db_tracer.info(
            "PNET_PROJECT definido pero .env no encontrado, usando raiz",
            project=pnet_project, candidate=candidate
        )

    # Fallback: .env en la raíz (compatibilidad con la configuración anterior)
    return os.path.join(project_root, ".env")


def _load_config():
    """Carga y devuelve el diccionario de configuración del proyecto activo.

    Returns:
        dict: Claves de configuración (DB_ENGINE, DB_SERVER, etc.)
    """
    env_path = _resolve_env_path()
    # dotenv_values no modifica os.environ — devuelve un dict limpio
    config = dict(dotenv_values(env_path))
    # Permitir también sobreescribir desde variables de entorno del sistema
    for key in list(config.keys()):
        if key in os.environ:
            config[key] = os.environ[key]
    return config


# ---------------------------------------------------------------------------
# Adaptadores (cargados dinámicamente según DB_ENGINE)
# ---------------------------------------------------------------------------

_ADAPTERS = {
    "sqlserver": "tools.general.db_sqlserver",
    "oracle": "tools.general.db_oracle",
}


def _get_adapter(engine_name):
    """Importa y devuelve el módulo adaptador para el motor indicado.

    Args:
        engine_name: "sqlserver" o "oracle".

    Returns:
        module: Módulo adaptador con funciones connect() y get_dialect().

    Raises:
        ValueError: Si el motor no está soportado.
    """
    import importlib
    key = (engine_name or "sqlserver").strip().lower()
    module_path = _ADAPTERS.get(key)
    if module_path is None:
        supported = ", ".join(_ADAPTERS.keys())
        raise ValueError(
            f"Motor de BD no soportado: '{engine_name}'. "
            f"Valores válidos: {supported}"
        )
    return importlib.import_module(module_path)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def get_db_connection():
    """Crea y devuelve una conexión a la base de datos del proyecto activo.

    El motor y las credenciales se leen del .env del proyecto seleccionado
    por PNET_PROJECT (o del .env raíz como fallback).
    El llamante es responsable de cerrar la conexión cuando termine.

    Returns:
        Connection: Conexión activa (pyodbc.Connection o oracledb.Connection).

    Raises:
        ValueError: Si faltan variables de entorno requeridas o el motor no es soportado.
        Exception: Si la conexión a la base de datos falla.
    """
    config = _load_config()
    engine = config.get("DB_ENGINE", "sqlserver")
    adapter = _get_adapter(engine)
    return adapter.connect(config)


def get_dialect():
    """Devuelve el dialecto SQL del proyecto activo.

    Permite a las tools construir queries portables usando los métodos
    del dialecto en lugar de SQL engine-specific.

    Returns:
        SqlDialect: Instancia del dialecto (SqlServerDialect u OracleDialect).
    """
    config = _load_config()
    engine = config.get("DB_ENGINE", "sqlserver")
    adapter = _get_adapter(engine)
    return adapter.get_dialect()


@contextmanager
def db_connection():
    """Context manager para conexiones a la base de datos.

    Abre una conexión al proyecto activo y garantiza que se cierre al salir
    del bloque, incluso si se produce una excepción.

    Uso:
        with db_connection() as conn:
            d = get_dialect()
            cursor = conn.cursor()
            cursor.execute(f"SELECT {d.select_prefix(10)} * FROM tabla {d.select_suffix(10)}")

    Yields:
        Connection: Conexión activa a la base de datos.
    """
    conn = get_db_connection()
    try:
        yield conn
    except Exception as e:
        db_tracer.error("Excepcion durante uso de conexion", error=str(e))
        raise
    finally:
        db_tracer.info("Cerrando conexion")
        conn.close()


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def get_active_project():
    """Devuelve el nombre del proyecto activo.

    Returns:
        str: Nombre del proyecto (valor de PNET_PROJECT) o 'default' si no está definido.
    """
    return os.environ.get("PNET_PROJECT", "").strip() or "default"


def safe_filename(name):
    """Sanitiza un nombre para usarlo como nombre de fichero en Windows.

    Reemplaza caracteres no válidos en Windows (/ \\ : * ? \" < > |)
    y espacios por guiones bajos.

    Args:
        name: Nombre a sanitizar.

    Returns:
        str: Nombre seguro para usar como fichero.
    """
    return re.sub(r'[/\\:*?"<>|\s]+', "_", name)
