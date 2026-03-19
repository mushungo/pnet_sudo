# =============================================================================
# ln4_lsp/db_resolver.py — Resolución de símbolos contra la BD de PeopleNet
# =============================================================================
# Tier 2 del go-to-definition: consulta las tablas M4RCH_* para resolver
# referencias a TIs, items, métodos y canales.
#
# Consultas principales:
#   1. resolve_item(ti_name, item_name) → busca en M4RCH_ITEMS
#   2. resolve_rule_source(ti_name, item_name) → busca en M4RCH_RULES3
#   3. resolve_ti(ti_name) → busca en M4RCH_TIS
#   4. resolve_channel(channel_name) → busca en M4RCH_T3S
#   5. resolve_channel_item(channel, ti, item) → cross-channel resolution
#   6. resolve_item_args(ti_name, item_name) → busca en M4RCH_ITEM_ARGS
#
# La conexión a BD es opcional — si no está disponible, retorna None
# y el servidor degrada a Tier 1 (in-document only).
# =============================================================================

import sys
import os
import logging
from datetime import datetime

logger = logging.getLogger("ln4-lsp")


# =============================================================================
# Resultado de resolución
# =============================================================================
class ResolvedSymbol:
    """Resultado de una resolución de símbolo contra la BD.

    Attributes:
        name: Nombre del símbolo resuelto.
        kind: Tipo de entidad ("item", "method", "ti", "channel", "rule").
        ti_name: ID del TI (si aplica).
        item_name: ID del ITEM (si aplica).
        channel_name: ID del canal T3 (si aplica).
        item_type: Tipo de item (1=Method, 2=Property, 3=Field, 4=Concept).
        m4_type: Tipo M4 del item.
        description_esp: Descripción en español.
        description_eng: Descripción en inglés.
        source_code: Código fuente de la regla (si es un item con regla).
        rule_id: ID de la regla (si aplica).
        start_date: Fecha de inicio de la regla (si aplica).
        arguments: Lista de dicts con argumentos del item (de M4RCH_ITEM_ARGS).
                   Cada dict: {name, position, m4_type, arg_type, precision, scale}.
    """

    __slots__ = [
        "name", "kind", "ti_name", "item_name", "channel_name",
        "item_type", "m4_type", "description_esp", "description_eng",
        "source_code", "rule_id", "start_date", "arguments",
    ]

    def __init__(self, name, kind, **kwargs):
        self.name = name
        self.kind = kind
        self.ti_name = kwargs.get("ti_name")
        self.item_name = kwargs.get("item_name")
        self.channel_name = kwargs.get("channel_name")
        self.item_type = kwargs.get("item_type")
        self.m4_type = kwargs.get("m4_type")
        self.description_esp = kwargs.get("description_esp")
        self.description_eng = kwargs.get("description_eng")
        self.source_code = kwargs.get("source_code")
        self.rule_id = kwargs.get("rule_id")
        self.start_date = kwargs.get("start_date")
        self.arguments = kwargs.get("arguments")

    def __repr__(self):
        parts = [f"{self.kind}:{self.name}"]
        if self.ti_name:
            parts.append(f"TI={self.ti_name}")
        if self.channel_name:
            parts.append(f"CH={self.channel_name}")
        return f"ResolvedSymbol({', '.join(parts)})"


# =============================================================================
# Constantes de tipo de item
# =============================================================================
ITEM_TYPE_METHOD = 1
ITEM_TYPE_PROPERTY = 2
ITEM_TYPE_FIELD = 3
ITEM_TYPE_CONCEPT = 4

ITEM_TYPE_NAMES = {
    ITEM_TYPE_METHOD: "Method",
    ITEM_TYPE_PROPERTY: "Property",
    ITEM_TYPE_FIELD: "Field",
    ITEM_TYPE_CONCEPT: "Concept",
}


# =============================================================================
# DBResolver — resuelve símbolos contra la BD
# =============================================================================
class DBResolver:
    """Resuelve referencias de símbolos LN4 contra la BD de PeopleNet.

    Utiliza una conexión perezosa (lazy) — se conecta solo cuando se
    necesita resolver algo. Si la BD no está disponible, los métodos
    retornan None sin lanzar excepciones.

    Uso:
        resolver = DBResolver()
        result = resolver.resolve_item("MY_TI", "MY_ITEM")
        if result:
            print(result.source_code)
        resolver.close()
    """

    def __init__(self, connection=None):
        """Inicializa el resolver.

        Args:
            connection: Conexión pyodbc existente (opcional).
                       Si no se proporciona, se creará una bajo demanda.
        """
        self._conn = connection
        self._own_connection = connection is None
        self._available = None  # None = no verificado aún
        self._item_args_cache = {}  # Cache: (ti, item) → list of arg dicts

    def _get_connection(self):
        """Obtiene la conexión a BD (lazy initialization)."""
        if self._conn is not None:
            return self._conn

        try:
            # Importar aquí para evitar dependencia circular y
            # permitir que el LSP funcione sin BD
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from tools.general.db_utils import get_db_connection
            self._conn = get_db_connection()
            self._own_connection = True
            self._available = True
            logger.info("DBResolver: conexión a BD establecida")
            return self._conn
        except Exception as e:
            logger.warning("DBResolver: BD no disponible: %s", e)
            self._available = False
            return None

    @property
    def is_available(self):
        """Indica si la BD está disponible."""
        if self._available is None:
            self._get_connection()
        return self._available

    def close(self):
        """Cierra la conexión si fue creada por este resolver."""
        if self._conn and self._own_connection:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
            self._available = None
        self._item_args_cache.clear()

    # -----------------------------------------------------------------
    # resolve_item — busca un item por TI + nombre
    # -----------------------------------------------------------------
    def resolve_item(self, ti_name, item_name):
        """Resuelve un item de TI (TI.ITEM, TI.METHOD, @ITEM, #ITEM).

        Busca en M4RCH_ITEMS por (ID_TI, ID_ITEM).

        Args:
            ti_name: Nombre del TI.
            item_name: Nombre del item.

        Returns:
            ResolvedSymbol o None si no se encuentra.
        """
        conn = self._get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    i.ID_TI, i.ID_ITEM, i.ID_ITEM_TYPE, i.ID_M4_TYPE,
                    i.N_SYNONYMESP, i.N_SYNONYMENG, i.N_ITEM,
                    i.ID_READ_OBJECT, i.ID_WRITE_OBJECT,
                    i.ID_READ_FIELD, i.ID_WRITE_FIELD
                FROM M4RCH_ITEMS i
                WHERE i.ID_TI = ? AND i.ID_ITEM = ?
            """, ti_name.upper(), item_name.upper())
            row = cursor.fetchone()

            if not row:
                return None

            return ResolvedSymbol(
                name=row.ID_ITEM,
                kind="item",
                ti_name=row.ID_TI,
                item_name=row.ID_ITEM,
                item_type=row.ID_ITEM_TYPE,
                m4_type=row.ID_M4_TYPE,
                description_esp=row.N_SYNONYMESP,
                description_eng=row.N_SYNONYMENG,
            )
        except Exception as e:
            logger.error("Error resolviendo item %s.%s: %s", ti_name, item_name, e)
            return None

    # -----------------------------------------------------------------
    # resolve_rule_source — obtiene el código fuente de una regla
    # -----------------------------------------------------------------
    def resolve_rule_source(self, ti_name, item_name):
        """Obtiene el código fuente de la regla asociada a un item.

        Busca en M4RCH_RULES + M4RCH_RULES3. Si hay múltiples reglas,
        retorna la de mayor prioridad / más reciente.

        Args:
            ti_name: Nombre del TI.
            item_name: Nombre del item.

        Returns:
            ResolvedSymbol con source_code, o None si no tiene regla.
        """
        conn = self._get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1
                    r.ID_TI, r.ID_ITEM, r.ID_RULE, r.DT_START,
                    r.ID_CODE_TYPE, r.RULE_ORDER,
                    CAST(r3.SOURCE_CODE AS VARCHAR(MAX)) AS SOURCE_CODE
                FROM M4RCH_RULES r
                JOIN M4RCH_RULES3 r3
                    ON r.ID_TI = r3.ID_TI
                    AND r.ID_ITEM = r3.ID_ITEM
                    AND r.DT_START = r3.DT_START
                    AND r.ID_RULE = r3.ID_RULE
                WHERE r.ID_TI = ? AND r.ID_ITEM = ?
                    AND r.ID_CODE_TYPE = 1
                    AND DATALENGTH(r3.SOURCE_CODE) > 0
                ORDER BY r.RULE_ORDER
            """, ti_name.upper(), item_name.upper())
            row = cursor.fetchone()

            if not row:
                return None

            return ResolvedSymbol(
                name=row.ID_ITEM,
                kind="rule",
                ti_name=row.ID_TI,
                item_name=row.ID_ITEM,
                source_code=row.SOURCE_CODE,
                rule_id=row.ID_RULE,
                start_date=row.DT_START,
            )
        except Exception as e:
            logger.error("Error obteniendo source de %s.%s: %s", ti_name, item_name, e)
            return None

    # -----------------------------------------------------------------
    # resolve_ti — busca un TI por nombre
    # -----------------------------------------------------------------
    def resolve_ti(self, ti_name):
        """Resuelve un Technical Instance por nombre.

        Args:
            ti_name: Nombre del TI.

        Returns:
            ResolvedSymbol o None.
        """
        conn = self._get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    t.ID_TI, t.N_TIESP, t.N_TIENG,
                    t.ID_TI_BASE, t.ID_READ_OBJECT, t.ID_WRITE_OBJECT,
                    t.IS_SYSTEM_TI
                FROM M4RCH_TIS t
                WHERE t.ID_TI = ?
            """, ti_name.upper())
            row = cursor.fetchone()

            if not row:
                return None

            return ResolvedSymbol(
                name=row.ID_TI,
                kind="ti",
                ti_name=row.ID_TI,
                description_esp=row.N_TIESP,
                description_eng=row.N_TIENG,
            )
        except Exception as e:
            logger.error("Error resolviendo TI %s: %s", ti_name, e)
            return None

    # -----------------------------------------------------------------
    # resolve_channel — busca un canal T3 por nombre
    # -----------------------------------------------------------------
    def resolve_channel(self, channel_name):
        """Resuelve un canal (T3/m4object) por nombre.

        Args:
            channel_name: Nombre del canal.

        Returns:
            ResolvedSymbol o None.
        """
        conn = self._get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    t.ID_T3, t.N_T3ESP, t.N_T3ENG,
                    t.ID_CATEGORY, t.ID_SUBCATEGORY
                FROM M4RCH_T3S t
                WHERE t.ID_T3 = ?
            """, channel_name.upper())
            row = cursor.fetchone()

            if not row:
                return None

            return ResolvedSymbol(
                name=row.ID_T3,
                kind="channel",
                channel_name=row.ID_T3,
                description_esp=row.N_T3ESP,
                description_eng=row.N_T3ENG,
            )
        except Exception as e:
            logger.error("Error resolviendo channel %s: %s", channel_name, e)
            return None

    # -----------------------------------------------------------------
    # resolve_channel_item — cross-channel resolution
    # -----------------------------------------------------------------
    def resolve_channel_item(self, channel_name, ti_name, item_name):
        """Resuelve una referencia cross-channel: CHANNEL!TI.ITEM.

        Primero verifica que el TI pertenece al canal (via M4RCH_NODES),
        luego busca el item en ese TI.

        Args:
            channel_name: Nombre del canal.
            ti_name: Nombre del TI.
            item_name: Nombre del item.

        Returns:
            ResolvedSymbol o None.
        """
        conn = self._get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            # Verificar que el TI pertenece al canal via NODES
            cursor.execute("""
                SELECT n.ID_T3, n.ID_NODE, n.ID_TI
                FROM M4RCH_NODES n
                WHERE n.ID_T3 = ? AND n.ID_TI = ?
            """, channel_name.upper(), ti_name.upper())
            node_row = cursor.fetchone()

            if not node_row:
                # El TI no pertenece a este canal
                return None

            # Buscar el item en el TI
            result = self.resolve_item(ti_name, item_name)
            if result:
                result.channel_name = channel_name.upper()
            return result

        except Exception as e:
            logger.error(
                "Error resolviendo channel item %s!%s.%s: %s",
                channel_name, ti_name, item_name, e,
            )
            return None

    # -----------------------------------------------------------------
    # list_ti_items — lista todos los items de un TI
    # -----------------------------------------------------------------
    def list_ti_items(self, ti_name):
        """Lista todos los items de un TI.

        Útil para autocompletado contextual después de "TI.".

        Args:
            ti_name: Nombre del TI.

        Returns:
            Lista de ResolvedSymbol, o lista vacía.
        """
        conn = self._get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    i.ID_TI, i.ID_ITEM, i.ID_ITEM_TYPE, i.ID_M4_TYPE,
                    i.N_SYNONYMESP, i.N_SYNONYMENG, i.N_ITEM
                FROM M4RCH_ITEMS i
                WHERE i.ID_TI = ?
                ORDER BY i.ITEM_ORDER, i.ID_ITEM
            """, ti_name.upper())
            rows = cursor.fetchall()

            results = []
            for row in rows:
                results.append(ResolvedSymbol(
                    name=row.ID_ITEM,
                    kind="item",
                    ti_name=row.ID_TI,
                    item_name=row.ID_ITEM,
                    item_type=row.ID_ITEM_TYPE,
                    m4_type=row.ID_M4_TYPE,
                    description_esp=row.N_SYNONYMESP,
                    description_eng=row.N_SYNONYMENG,
                ))
            return results

        except Exception as e:
            logger.error("Error listando items de TI %s: %s", ti_name, e)
            return []

    # -----------------------------------------------------------------
    # resolve_item_args — obtiene los argumentos de un item
    # -----------------------------------------------------------------
    def resolve_item_args(self, ti_name, item_name):
        """Obtiene los argumentos de un item desde M4RCH_ITEM_ARGS.

        Los argumentos representan los parámetros de métodos/funciones de TI.
        Se cachean por (ti, item) ya que se consultan repetidamente
        durante signature help (cada keystroke dispara una consulta).

        Args:
            ti_name: Nombre del TI.
            item_name: Nombre del item.

        Returns:
            Lista de dicts con keys: name, position, m4_type, arg_type,
            precision, scale. Lista vacía si no hay argumentos o error.
        """
        key = (ti_name.upper(), item_name.upper())
        if key in self._item_args_cache:
            return self._item_args_cache[key]

        conn = self._get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    a.ID_ARGUMENT, a.POSITION,
                    a.ID_M4_TYPE, a.ID_ARGUMENT_TYPE,
                    a.PREC, a.SCALE
                FROM M4RCH_ITEM_ARGS a
                WHERE a.ID_TI = ? AND a.ID_ITEM = ?
                ORDER BY a.POSITION
            """, key[0], key[1])
            rows = cursor.fetchall()

            args = []
            for row in rows:
                args.append({
                    "name": row.ID_ARGUMENT,
                    "position": row.POSITION,
                    "m4_type": row.ID_M4_TYPE,
                    "arg_type": row.ID_ARGUMENT_TYPE,
                    "precision": row.PREC,
                    "scale": row.SCALE,
                })

            self._item_args_cache[key] = args
            return args

        except Exception as e:
            logger.error("Error obteniendo args de %s.%s: %s", ti_name, item_name, e)
            self._item_args_cache[key] = []
            return []

    # -----------------------------------------------------------------
    # resolve_item_with_args — resolve_item + resolve_item_args combinados
    # -----------------------------------------------------------------
    def resolve_item_with_args(self, ti_name, item_name):
        """Resuelve un item y adjunta sus argumentos si los tiene.

        Combina resolve_item + resolve_item_args en una sola llamada
        para simplificar el uso desde hover y signature help.

        Args:
            ti_name: Nombre del TI.
            item_name: Nombre del item.

        Returns:
            ResolvedSymbol con arguments poblado, o None.
        """
        result = self.resolve_item(ti_name, item_name)
        if result is None:
            return None

        args = self.resolve_item_args(ti_name, item_name)
        result.arguments = args if args else None
        return result

    # -----------------------------------------------------------------
    # find_tis_for_channel — lista los TIs de un canal
    # -----------------------------------------------------------------
    def find_tis_for_channel(self, channel_name):
        """Lista los TIs que pertenecen a un canal.

        Args:
            channel_name: Nombre del canal (ID_T3).

        Returns:
            Lista de ResolvedSymbol con kind="ti", o lista vacía.
        """
        conn = self._get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT
                    n.ID_TI, t.N_TIESP, t.N_TIENG
                FROM M4RCH_NODES n
                JOIN M4RCH_TIS t ON n.ID_TI = t.ID_TI
                WHERE n.ID_T3 = ?
                ORDER BY n.ID_TI
            """, channel_name.upper())
            rows = cursor.fetchall()

            results = []
            for row in rows:
                results.append(ResolvedSymbol(
                    name=row.ID_TI,
                    kind="ti",
                    ti_name=row.ID_TI,
                    channel_name=channel_name.upper(),
                    description_esp=row.N_TIESP,
                    description_eng=row.N_TIENG,
                ))
            return results

        except Exception as e:
            logger.error("Error listando TIs de channel %s: %s", channel_name, e)
            return []


# =============================================================================
# Singleton global
# =============================================================================
_resolver = None


def get_resolver():
    """Obtiene la instancia singleton del DBResolver.

    Se inicializa perezosamente al primer uso.
    """
    global _resolver
    if _resolver is None:
        _resolver = DBResolver()
    return _resolver


def reset_resolver():
    """Cierra y resetea el singleton (para tests o reconexión)."""
    global _resolver
    if _resolver is not None:
        _resolver.close()
        _resolver = None
