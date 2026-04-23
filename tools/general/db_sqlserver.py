# tools/general/db_sqlserver.py
"""
Adaptador de conexión para Microsoft SQL Server via pyodbc.

Este módulo encapsula la lógica de conexión específica de SQL Server.
No debe ser importado directamente por las tools — usar db_utils.py.
"""
import time

import pyodbc

from tools.general.trace import db_tracer
from tools.general.sql_dialect import SqlServerDialect


def connect(config):
    """Crea y devuelve una conexión pyodbc a SQL Server.

    Args:
        config (dict): Diccionario con las claves de configuración leídas del .env:
            - DB_SERVER     (obligatorio)
            - DB_DATABASE   (obligatorio)
            - DB_USERNAME   (obligatorio)
            - DB_PASSWORD   (obligatorio)
            - DB_DRIVER     (opcional, default: {ODBC Driver 17 for SQL Server})

    Returns:
        pyodbc.Connection: Conexión activa.

    Raises:
        ValueError: Si faltan claves obligatorias.
        pyodbc.Error: Si la conexión falla.
    """
    server = config.get("DB_SERVER")
    database = config.get("DB_DATABASE")
    username = config.get("DB_USERNAME")
    password = config.get("DB_PASSWORD")
    driver = config.get("DB_DRIVER", "{ODBC Driver 17 for SQL Server}")

    missing = [k for k, v in {"DB_SERVER": server, "DB_DATABASE": database,
                               "DB_USERNAME": username, "DB_PASSWORD": password}.items() if not v]
    if missing:
        raise ValueError(
            f"Faltan variables de entorno para SQL Server: {', '.join(missing)}. "
            "Revisa el fichero .env del proyecto."
        )

    db_tracer.info("Abriendo conexion SQL Server", server=server, database=database, user=username)
    t0 = time.perf_counter()

    try:
        conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        conn = pyodbc.connect(conn_str)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        db_tracer.info("Conexion SQL Server establecida", elapsed_ms=f"{elapsed_ms:.1f}",
                       server=server, database=database)
        return conn
    except Exception as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        db_tracer.error("Fallo de conexion SQL Server", elapsed_ms=f"{elapsed_ms:.1f}",
                        server=server, error=str(e))
        raise


def get_dialect():
    """Devuelve el dialecto SQL para SQL Server."""
    return SqlServerDialect()
