# tools/general/db_utils.py
"""
Módulo centralizado de conexión a la base de datos.

Proporciona funciones para crear conexiones a la BD de PeopleNet
usando las credenciales definidas en el fichero .env del proyecto.

Las operaciones de conexión se trazan automáticamente si Database_trace=1
en regmeta.xml. Las trazas se escriben en .logs/pnet_sudo.log y .jsonl.
"""
import os
import re
import time
from contextlib import contextmanager

import pyodbc
from dotenv import load_dotenv

from tools.general.trace import db_tracer


def get_db_connection():
    """Crea y devuelve una conexión a la base de datos de PeopleNet.

    Lee las credenciales del fichero .env en la raíz del proyecto.
    El llamante es responsable de cerrar la conexión cuando termine.

    Returns:
        pyodbc.Connection: Conexión activa a la base de datos.

    Raises:
        ValueError: Si faltan variables de entorno requeridas.
        pyodbc.Error: Si la conexión a la base de datos falla.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    load_dotenv(os.path.join(project_root, ".env"))

    db_server = os.getenv("DB_SERVER")
    db_name = os.getenv("DB_DATABASE")
    db_user = os.getenv("DB_USERNAME")
    db_password = os.getenv("DB_PASSWORD")
    db_driver = os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}")

    if not all([db_server, db_name, db_user, db_password]):
        raise ValueError(
            "Faltan variables de entorno para la conexión a la base de datos. "
            "Revisa que el fichero .env contenga DB_SERVER, DB_DATABASE, DB_USERNAME y DB_PASSWORD."
        )

    db_tracer.info("Abriendo conexion", server=db_server, database=db_name, user=db_user)
    t0 = time.perf_counter()

    try:
        conn_str = f"DRIVER={db_driver};SERVER={db_server};DATABASE={db_name};UID={db_user};PWD={db_password}"
        conn = pyodbc.connect(conn_str)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        db_tracer.info("Conexion establecida", elapsed_ms=f"{elapsed_ms:.1f}", server=db_server, database=db_name)
        return conn
    except Exception as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        db_tracer.error("Fallo de conexion", elapsed_ms=f"{elapsed_ms:.1f}", server=db_server, error=str(e))
        raise


@contextmanager
def db_connection():
    """Context manager para conexiones a la base de datos.

    Abre una conexión y garantiza que se cierre al salir del bloque,
    incluso si se produce una excepción.

    Uso:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")

    Yields:
        pyodbc.Connection: Conexión activa a la base de datos.
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
