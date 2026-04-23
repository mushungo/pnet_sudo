# tools/general/sql_dialect.py
"""
Abstracción de dialecto SQL para soportar múltiples motores de base de datos.

Cada motor (SQL Server, Oracle) implementa la misma interfaz SqlDialect.
Las tools usan siempre los métodos del dialecto — nunca SQL engine-specific directo.

Uso típico:
    from tools.general.db_utils import db_connection, get_dialect

    with db_connection() as conn:
        d = get_dialect()
        cursor = conn.cursor()
        cursor.execute(f\"\"\"
            SELECT {d.select_prefix(100)} ID_OBJECT, NAME
            FROM M4RCH_SENTENCES
            WHERE LAST_UPDATE >= {d.today()}
            {d.select_suffix(100)}
        \"\"\")

Métodos disponibles:
    d.today()               → GETDATE() / SYSDATE
    d.isnull(col, val)      → ISNULL(col, val) / NVL(col, val)
    d.cast_varchar(col)     → CAST(col AS VARCHAR) / TO_CHAR(col)
    d.concat(*cols)         → col1 + col2 / col1 || col2
    d.select_prefix(n)      → "TOP n" / ""   (va tras SELECT)
    d.select_suffix(n)      → ""  / "FETCH FIRST n ROWS ONLY"  (va al final)
    d.engine                → "sqlserver" / "oracle"
"""


class SqlDialect:
    """Clase base de dialecto SQL. No instanciar directamente."""

    engine = None  # "sqlserver" | "oracle"

    def today(self):
        """Devuelve la expresión de fecha/hora actual del motor."""
        raise NotImplementedError

    def isnull(self, col, val):
        """Equivalente a COALESCE(col, val) con la función nativa del motor.

        Args:
            col: Nombre de la columna o expresión.
            val: Valor a devolver si col es NULL.

        Returns:
            str: Expresión SQL.
        """
        raise NotImplementedError

    def cast_varchar(self, col, length=None):
        """Convierte una expresión al tipo texto del motor.

        Args:
            col: Columna o expresión a convertir.
            length: Longitud máxima (opcional, ignorado en Oracle TO_CHAR simple).

        Returns:
            str: Expresión SQL.
        """
        raise NotImplementedError

    def concat(self, *cols):
        """Concatena columnas o literales con el operador nativo del motor.

        Args:
            *cols: Columnas o literales a concatenar.

        Returns:
            str: Expresión SQL de concatenación.
        """
        raise NotImplementedError

    def select_prefix(self, n):
        """Fragmento que va inmediatamente después de SELECT para limitar filas.

        En SQL Server: "TOP n"
        En Oracle: "" (el límite va al final con select_suffix)

        Args:
            n: Número máximo de filas.

        Returns:
            str: Fragmento SQL (puede ser cadena vacía).
        """
        raise NotImplementedError

    def select_suffix(self, n):
        """Fragmento que va al final de la query para limitar filas.

        En SQL Server: "" (el límite ya está en select_prefix)
        En Oracle: "FETCH FIRST n ROWS ONLY"

        Args:
            n: Número máximo de filas.

        Returns:
            str: Fragmento SQL (puede ser cadena vacía).
        """
        raise NotImplementedError

    def param(self):
        """Placeholder de parámetro para queries parametrizadas.

        SQL Server / pyodbc: ?
        Oracle / oracledb:   :1, :2, ... (pero para simplicidad devolvemos ?)
                             oracledb en modo pyodbc-compat acepta ?

        Returns:
            str: Placeholder de parámetro.
        """
        return "?"


# ---------------------------------------------------------------------------
# SQL Server
# ---------------------------------------------------------------------------

class SqlServerDialect(SqlDialect):
    """Dialecto para Microsoft SQL Server (via pyodbc)."""

    engine = "sqlserver"

    def today(self):
        return "GETDATE()"

    def isnull(self, col, val):
        return f"ISNULL({col}, {val})"

    def cast_varchar(self, col, length=None):
        if length:
            return f"CAST({col} AS VARCHAR({length}))"
        return f"CAST({col} AS VARCHAR)"

    def concat(self, *cols):
        return " + ".join(cols)

    def select_prefix(self, n):
        return f"TOP {n}"

    def select_suffix(self, n):
        return ""


# ---------------------------------------------------------------------------
# Oracle
# ---------------------------------------------------------------------------

class OracleDialect(SqlDialect):
    """Dialecto para Oracle Database (via python-oracledb)."""

    engine = "oracle"

    def today(self):
        return "SYSDATE"

    def isnull(self, col, val):
        return f"NVL({col}, {val})"

    def cast_varchar(self, col, length=None):
        # TO_CHAR convierte cualquier tipo a texto en Oracle
        return f"TO_CHAR({col})"

    def concat(self, *cols):
        return " || ".join(cols)

    def select_prefix(self, n):
        # En Oracle el límite va al FINAL, no al inicio
        return ""

    def select_suffix(self, n):
        return f"FETCH FIRST {n} ROWS ONLY"


# ---------------------------------------------------------------------------
# Factoría
# ---------------------------------------------------------------------------

_DIALECTS = {
    "sqlserver": SqlServerDialect,
    "oracle": OracleDialect,
}


def get_dialect_for_engine(engine_name):
    """Devuelve la instancia de dialecto para el motor indicado.

    Args:
        engine_name: "sqlserver" o "oracle" (insensible a mayúsculas).

    Returns:
        SqlDialect: Instancia del dialecto correspondiente.

    Raises:
        ValueError: Si el motor no está soportado.
    """
    key = (engine_name or "sqlserver").strip().lower()
    cls = _DIALECTS.get(key)
    if cls is None:
        supported = ", ".join(_DIALECTS.keys())
        raise ValueError(
            f"Motor de BD no soportado: '{engine_name}'. "
            f"Valores válidos: {supported}"
        )
    return cls()
