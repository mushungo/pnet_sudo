# tools/general/db_utils.py
"""
Módulo centralizado de conexión a la base de datos.

Proporciona funciones para crear conexiones a la BD de PeopleNet
usando las credenciales definidas en el fichero .env del proyecto.
"""
import os
from contextlib import contextmanager

import pyodbc
from dotenv import load_dotenv


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

    conn_str = f"DRIVER={db_driver};SERVER={db_server};DATABASE={db_name};UID={db_user};PWD={db_password}"
    return pyodbc.connect(conn_str)


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
    finally:
        conn.close()
