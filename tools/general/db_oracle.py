# tools/general/db_oracle.py
"""
Adaptador de conexión para Oracle Database via python-oracledb.

Este módulo encapsula la lógica de conexión específica de Oracle.
Usa el modo "thin" de python-oracledb: no requiere Oracle Instant Client instalado.

No debe ser importado directamente por las tools — usar db_utils.py.

Instalación del driver:
    pip install oracledb

Variables .env requeridas:
    DB_ENGINE=oracle
    DB_HOST=servidor.oracle.com
    DB_PORT=1521               (opcional, default 1521)
    DB_SERVICE=nombre_servicio (Service Name, no SID)
    DB_USERNAME=usuario
    DB_PASSWORD=contraseña
    DB_SCHEMA=esquema          (opcional, si es distinto del usuario)
"""
import time

from tools.general.trace import db_tracer
from tools.general.sql_dialect import OracleDialect


def connect(config):
    """Crea y devuelve una conexión oracledb a Oracle Database.

    Args:
        config (dict): Diccionario con las claves de configuración leídas del .env:
            - DB_HOST       (obligatorio)
            - DB_SERVICE    (obligatorio)
            - DB_USERNAME   (obligatorio)
            - DB_PASSWORD   (obligatorio)
            - DB_PORT       (opcional, default: 1521)
            - DB_SCHEMA     (opcional, default: DB_USERNAME)

    Returns:
        oracledb.Connection: Conexión activa en modo thin.

    Raises:
        ImportError: Si python-oracledb no está instalado.
        ValueError: Si faltan claves obligatorias.
        oracledb.DatabaseError: Si la conexión falla.
    """
    try:
        import oracledb
    except ImportError:
        raise ImportError(
            "El driver 'oracledb' no está instalado. "
            "Instálalo con: pip install oracledb"
        )

    host = config.get("DB_HOST")
    port = config.get("DB_PORT", "1521")
    service = config.get("DB_SERVICE")
    username = config.get("DB_USERNAME")
    password = config.get("DB_PASSWORD")
    schema = config.get("DB_SCHEMA")  # opcional

    missing = [k for k, v in {"DB_HOST": host, "DB_SERVICE": service,
                               "DB_USERNAME": username, "DB_PASSWORD": password}.items() if not v]
    if missing:
        raise ValueError(
            f"Faltan variables de entorno para Oracle: {', '.join(missing)}. "
            "Revisa el fichero .env del proyecto."
        )

    dsn = f"{host}:{port}/{service}"
    db_tracer.info("Abriendo conexion Oracle (thin)", dsn=dsn, user=username)
    t0 = time.perf_counter()

    try:
        conn = oracledb.connect(user=username, password=password, dsn=dsn)

        # Si se especifica un esquema distinto al usuario, cambiar el contexto
        if schema and schema.upper() != username.upper():
            cursor = conn.cursor()
            cursor.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {schema}")
            cursor.close()
            db_tracer.info("Esquema Oracle establecido", schema=schema)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        db_tracer.info("Conexion Oracle establecida", elapsed_ms=f"{elapsed_ms:.1f}", dsn=dsn)
        return conn
    except Exception as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        db_tracer.error("Fallo de conexion Oracle", elapsed_ms=f"{elapsed_ms:.1f}",
                        dsn=dsn, error=str(e))
        raise


def get_dialect():
    """Devuelve el dialecto SQL para Oracle."""
    return OracleDialect()
