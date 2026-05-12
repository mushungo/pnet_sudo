# tools/general/db_oracle.py
"""
Adaptador de conexión para Oracle Database via python-oracledb.

Este módulo encapsula la lógica de conexión específica de Oracle.
Usa el modo "thin" de python-oracledb: no requiere Oracle Instant Client instalado.

No debe ser importado directamente por las tools — usar db_utils.py.

Instalación del driver:
    pip install oracledb

Variables .env — Service Name (más moderno):
    DB_ENGINE=oracle
    DB_HOST=servidor.oracle.com
    DB_PORT=1521               (opcional, default 1521)
    DB_SERVICE=nombre_servicio
    DB_USERNAME=usuario
    DB_PASSWORD=contraseña
    DB_SCHEMA=esquema          (opcional, si es distinto del usuario)

Variables .env — SID (legacy, servidores más antiguos):
    DB_ENGINE=oracle
    DB_HOST=servidor.oracle.com
    DB_PORT=1944               (el puerto puede no ser el estándar 1521)
    DB_SID=nombre_sid
    DB_USERNAME=usuario
    DB_PASSWORD=contraseña
"""
import time

from tools.general.trace import db_tracer
from tools.general.sql_dialect import OracleDialect


def _build_dsn(config):
    """Construye el DSN de conexión Oracle.

    Soporta dos modos:
    - Service Name: host:port/service  (DB_SERVICE)
    - SID legacy:   descriptor completo (DB_SID)

    El modo SID usa el descriptor largo porque oracledb thin requiere
    el formato explícito para SID (no acepta host:port:sid directamente).

    Args:
        config (dict): Configuración del .env.

    Returns:
        tuple: (dsn_str, label_para_log)

    Raises:
        ValueError: Si no se puede determinar el modo de conexión.
    """
    host = config.get("DB_HOST")
    port = config.get("DB_PORT", "1521")
    service = config.get("DB_SERVICE")
    sid = config.get("DB_SID")

    if not host:
        raise ValueError("Falta DB_HOST en el fichero .env del proyecto Oracle.")

    if service:
        # Modo moderno: host:port/service
        dsn = f"{host}:{port}/{service}"
        label = f"{host}:{port}/{service} (Service Name)"
    elif sid:
        # Modo legacy SID: descriptor completo requerido por oracledb thin
        dsn = (
            f"(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={host})(PORT={port}))"
            f"(CONNECT_DATA=(SID={sid})))"
        )
        label = f"{host}:{port}/{sid} (SID)"
    else:
        raise ValueError(
            "El fichero .env del proyecto Oracle debe incluir DB_SERVICE (Service Name) "
            "o DB_SID (SID legacy). Revisa la configuración."
        )

    return dsn, label


def connect(config):
    """Crea y devuelve una conexión oracledb a Oracle Database.

    Args:
        config (dict): Diccionario con las claves de configuración leídas del .env.

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

    username = config.get("DB_USERNAME")
    password = config.get("DB_PASSWORD")
    schema = config.get("DB_SCHEMA")

    missing = [k for k, v in {"DB_USERNAME": username, "DB_PASSWORD": password}.items() if not v]
    if missing:
        raise ValueError(
            f"Faltan variables de entorno para Oracle: {', '.join(missing)}. "
            "Revisa el fichero .env del proyecto."
        )

    dsn, label = _build_dsn(config)
    db_tracer.info("Abriendo conexion Oracle (thin)", dsn=label, user=username)
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
        db_tracer.info("Conexion Oracle establecida", elapsed_ms=f"{elapsed_ms:.1f}", dsn=label)
        return conn
    except Exception as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        db_tracer.error("Fallo de conexion Oracle", elapsed_ms=f"{elapsed_ms:.1f}",
                        dsn=label, error=str(e))
        raise


def get_dialect():
    """Devuelve el dialecto SQL para Oracle."""
    return OracleDialect()
