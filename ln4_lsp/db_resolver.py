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
        variable_arguments: Si el item acepta argumentos variables adicionales
                            más allá de los declarados en M4RCH_ITEM_ARGS
                            (M4RCH_ITEMS.VARIABLE_ARGUMENTS = True).
    """

    __slots__ = [
        "name", "kind", "ti_name", "item_name", "channel_name",
        "item_type", "m4_type", "description_esp", "description_eng",
        "source_code", "rule_id", "start_date", "arguments",
        "variable_arguments",
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
        self.variable_arguments = kwargs.get("variable_arguments", False)

    def __repr__(self):
        parts = [f"{self.kind}:{self.name}"]
        if self.ti_name:
            parts.append(f"TI={self.ti_name}")
        if self.channel_name:
            parts.append(f"CH={self.channel_name}")
        return f"ResolvedSymbol({', '.join(parts)})"


class ResolvedSentence:
    """Resultado de la resolución de una sentence contra la BD.

    Attributes:
        sentence_id: Identificador de la sentence.
        description_esp: Descripción en español.
        description_eng: Descripción en inglés.
        sentence_type: Tipo de sentence (código numérico de M4RCH_SENTENCES).
        is_distinct: Si la sentence tiene SELECT DISTINCT.
        apisql: SQL compilado (de M4RCH_SENTENCES3) o filtro abstracto
                (de M4RCH_SENTENCES1) si no hay compilado. Puede ser None.
        objects: Lista de dicts {id_object, alias, is_basis} con los objetos
                 BDL referenciados por la sentence (de M4RCH_SENT_OBJECTS).
    """

    __slots__ = [
        "sentence_id", "description_esp", "description_eng",
        "sentence_type", "is_distinct", "apisql", "objects",
    ]

    def __init__(self, sentence_id, description_esp=None, description_eng=None,
                 sentence_type=None, is_distinct=False):
        self.sentence_id = sentence_id
        self.description_esp = description_esp
        self.description_eng = description_eng
        self.sentence_type = sentence_type
        self.is_distinct = is_distinct
        self.apisql = None
        self.objects = []

    def __repr__(self):
        return f"ResolvedSentence({self.sentence_id})"


class ResolvedBDLObject:
    """Resultado de la resolución de un objeto BDL lógico contra la BD.

    Attributes:
        object_id: Identificador del objeto (ID_OBJECT).
        description_esp: Descripción en español (N_OBJECTESP).
        description_eng: Descripción en inglés (N_OBJECTENG).
        real_object: Nombre de la tabla/vista física (ID_REAL_OBJECT).
        object_type: Tipo de objeto BDL (ID_OBJECT_TYPE).
        fields: Lista de dicts {id_field, description_esp, real_field, m4_type}
                con los primeros 10 campos del objeto (de M4RDC_LOGIC_FIELDS).
    """

    __slots__ = [
        "object_id", "description_esp", "description_eng",
        "real_object", "object_type", "fields",
    ]

    def __init__(self, object_id, description_esp=None, description_eng=None,
                 real_object=None, object_type=None):
        self.object_id = object_id
        self.description_esp = description_esp
        self.description_eng = description_eng
        self.real_object = real_object
        self.object_type = object_type
        self.fields = []

    def __repr__(self):
        return f"ResolvedBDLObject({self.object_id})"


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
                    i.ID_READ_FIELD, i.ID_WRITE_FIELD,
                    i.VARIABLE_ARGUMENTS
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
                variable_arguments=bool(row.VARIABLE_ARGUMENTS),
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
                    i.N_SYNONYMESP, i.N_SYNONYMENG, i.N_ITEM,
                    i.VARIABLE_ARGUMENTS
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
                    variable_arguments=bool(row.VARIABLE_ARGUMENTS),
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
    # resolve_all_args_for_ti — batch fetch de argumentos de un TI
    # -----------------------------------------------------------------
    def resolve_all_args_for_ti(self, ti_name):
        """Obtiene los argumentos de TODOS los items de un TI en batch.

        Ejecuta una sola consulta a M4RCH_ITEM_ARGS filtrando por ID_TI,
        agrupa los resultados por ID_ITEM y los cachea individualmente.
        Esto evita N+1 queries cuando se listan los items de un TI para
        autocompletado contextual.

        Args:
            ti_name: Nombre del TI.

        Returns:
            Dict {item_name: [arg_dicts]} con los argumentos agrupados.
            Vacío si hay error o no hay argumentos.
        """
        ti_upper = ti_name.upper()
        conn = self._get_connection()
        if not conn:
            return {}

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    a.ID_ITEM, a.ID_ARGUMENT, a.POSITION,
                    a.ID_M4_TYPE, a.ID_ARGUMENT_TYPE,
                    a.PREC, a.SCALE
                FROM M4RCH_ITEM_ARGS a
                WHERE a.ID_TI = ?
                ORDER BY a.ID_ITEM, a.POSITION
            """, ti_upper)
            rows = cursor.fetchall()

            grouped = {}
            for row in rows:
                item_id = row.ID_ITEM
                if item_id not in grouped:
                    grouped[item_id] = []
                grouped[item_id].append({
                    "name": row.ID_ARGUMENT,
                    "position": row.POSITION,
                    "m4_type": row.ID_M4_TYPE,
                    "arg_type": row.ID_ARGUMENT_TYPE,
                    "precision": row.PREC,
                    "scale": row.SCALE,
                })

            # Cachear cada item individualmente en _item_args_cache
            for item_id, args in grouped.items():
                self._item_args_cache[(ti_upper, item_id)] = args

            logger.debug(
                "Batch args para TI %s: %d items con args (%d args total)",
                ti_upper, len(grouped), len(rows),
            )
            return grouped

        except Exception as e:
            logger.error("Error batch args de TI %s: %s", ti_name, e)
            return {}

    # -----------------------------------------------------------------
    # list_ti_items_with_args — items + args en batch (2 queries)
    # -----------------------------------------------------------------
    def list_ti_items_with_args(self, ti_name):
        """Lista todos los items de un TI con sus argumentos pre-cargados.

        Combina list_ti_items + resolve_all_args_for_ti en 2 queries
        (items + args) y adjunta los argumentos a cada ResolvedSymbol.
        Óptimo para autocompletado contextual después de 'TI.'.

        Args:
            ti_name: Nombre del TI.

        Returns:
            Lista de ResolvedSymbol con arguments poblado, o lista vacía.
        """
        # 1. Batch fetch de args (1 query, cachea individualmente)
        all_args = self.resolve_all_args_for_ti(ti_name)

        # 2. Lista de items (1 query)
        items = self.list_ti_items(ti_name)

        # 3. Adjuntar args a cada item
        for item in items:
            item_args = all_args.get(item.item_name)
            item.arguments = item_args if item_args else None

        return items

    # -----------------------------------------------------------------
    # resolve_sentence — obtiene metadatos y SQL de una sentence
    # -----------------------------------------------------------------
    def resolve_sentence(self, sentence_id):
        """Obtiene los metadatos y SQL compilado de una sentence.

        Consulta M4RCH_SENTENCES (metadatos) y M4RCH_SENTENCES3 (APISQL
        compilado completo). Si no hay APISQL compilado cae sobre
        M4RCH_SENTENCES1 (filtro abstracto).

        Args:
            sentence_id: Identificador de la sentence.

        Returns:
            ResolvedSentence o None si no se encuentra.
        """
        conn = self._get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            # Metadatos base
            cursor.execute("""
                SELECT
                    s.ID_SENTENCE, s.N_SENTENCEESP, s.N_SENTENCEENG,
                    s.ID_SENT_TYPE, s.IS_DISTINCT
                FROM M4RCH_SENTENCES s
                WHERE s.ID_SENTENCE = ?
            """, sentence_id.upper())
            row = cursor.fetchone()

            if not row:
                return None

            result = ResolvedSentence(
                sentence_id=row.ID_SENTENCE,
                description_esp=row.N_SENTENCEESP,
                description_eng=row.N_SENTENCEENG,
                sentence_type=row.ID_SENT_TYPE,
                is_distinct=bool(row.IS_DISTINCT) if row.IS_DISTINCT is not None else False,
            )

            # APISQL compilado (SENTENCES3)
            cursor.execute("""
                SELECT APISQL
                FROM M4RCH_SENTENCES3
                WHERE ID_SENTENCE = ?
            """, sentence_id.upper())
            apisql_row = cursor.fetchone()
            if apisql_row and apisql_row.APISQL:
                result.apisql = apisql_row.APISQL.strip()
            else:
                # Fallback: filtro abstracto (SENTENCES1)
                cursor.execute("""
                    SELECT FILTER
                    FROM M4RCH_SENTENCES1
                    WHERE ID_SENTENCE = ?
                """, sentence_id.upper())
                filter_row = cursor.fetchone()
                result.apisql = filter_row.FILTER.strip() if filter_row and filter_row.FILTER else None

            # Objetos BDL referenciados (SENT_OBJECTS)
            cursor.execute("""
                SELECT ID_OBJECT, ALIAS_OBJECT, IS_BASIS
                FROM M4RCH_SENT_OBJECTS
                WHERE ID_SENTENCE = ?
                ORDER BY IS_BASIS DESC, ALIAS_OBJECT
            """, sentence_id.upper())
            result.objects = [
                {"id_object": r.ID_OBJECT, "alias": r.ALIAS_OBJECT, "is_basis": bool(r.IS_BASIS)}
                for r in cursor.fetchall()
            ]

            return result

        except Exception as e:
            logger.error("Error resolviendo sentence %s: %s", sentence_id, e)
            return None

    # -----------------------------------------------------------------
    # list_sentences_for_object — sentences que referencian un objeto BDL
    # -----------------------------------------------------------------
    def list_sentences_for_object(self, object_id):
        """Lista las sentences que referencian un objeto BDL dado.

        Consulta M4RCH_SENT_OBJECTS para obtener las sentences que usan
        el objeto (directamente o como join).

        Args:
            object_id: Identificador del objeto BDL (ID_OBJECT).

        Returns:
            Lista de dicts {sentence_id, alias, is_basis}, o lista vacía.
        """
        conn = self._get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT so.ID_SENTENCE, so.ALIAS_OBJECT, so.IS_BASIS,
                       s.N_SENTENCEESP
                FROM M4RCH_SENT_OBJECTS so
                JOIN M4RCH_SENTENCES s ON so.ID_SENTENCE = s.ID_SENTENCE
                WHERE so.ID_OBJECT = ?
                ORDER BY so.IS_BASIS DESC, so.ID_SENTENCE
            """, object_id.upper())
            return [
                {
                    "sentence_id": r.ID_SENTENCE,
                    "alias": r.ALIAS_OBJECT,
                    "is_basis": bool(r.IS_BASIS),
                    "description_esp": r.N_SENTENCEESP,
                }
                for r in cursor.fetchall()
            ]
        except Exception as e:
            logger.error("Error listando sentences para objeto %s: %s", object_id, e)
            return []

    # -----------------------------------------------------------------
    # resolve_bdl_object — metadatos de un objeto BDL lógico
    # -----------------------------------------------------------------
    def resolve_bdl_object(self, object_id):
        """Obtiene los metadatos de un objeto BDL lógico y sus campos principales.

        Consulta M4RDC_LOGIC_OBJECT (cabecera) y M4RDC_FIELDS (campos).
        Retorna hasta 10 campos ordenados por POSITION para no saturar el hover.

        Args:
            object_id: Identificador del objeto BDL (ID_OBJECT).

        Returns:
            ResolvedBDLObject o None si no se encuentra.
        """
        conn = self._get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    o.ID_OBJECT, o.ID_TRANS_OBJESP, o.ID_TRANS_OBJENG,
                    o.REAL_NAME, o.ID_OBJECT_TYPE
                FROM M4RDC_LOGIC_OBJECT o
                WHERE o.ID_OBJECT = ?
            """, object_id.upper())
            row = cursor.fetchone()

            if not row:
                return None

            result = ResolvedBDLObject(
                object_id=row.ID_OBJECT,
                description_esp=row.ID_TRANS_OBJESP,
                description_eng=row.ID_TRANS_OBJENG,
                real_object=row.REAL_NAME,
                object_type=row.ID_OBJECT_TYPE,
            )

            # Campos principales (hasta 10)
            cursor.execute("""
                SELECT TOP 10
                    f.ID_FIELD, f.ID_TRANS_FLDESP, f.REAL_NAME, f.ID_TYPE
                FROM M4RDC_FIELDS f
                WHERE f.ID_OBJECT = ?
                ORDER BY f.POSITION
            """, object_id.upper())
            result.fields = [
                {
                    "id_field": r.ID_FIELD,
                    "description_esp": r.ID_TRANS_FLDESP,
                    "real_field": r.REAL_NAME,
                    "m4_type": r.ID_TYPE,
                }
                for r in cursor.fetchall()
            ]

            return result

        except Exception as e:
            logger.error("Error resolviendo BDL object %s: %s", object_id, e)
            return None

    # -----------------------------------------------------------------
    # resolve_bdl_for_item — BDL object asociado a un item de TI
    # -----------------------------------------------------------------
    def resolve_bdl_for_item(self, ti_name, item_name):
        """Obtiene el objeto BDL de lectura asociado a un item de TI.

        Resuelve M4RCH_ITEMS.ID_READ_OBJECT → resolve_bdl_object().
        Si no hay objeto de lectura, intenta con ID_WRITE_OBJECT.

        Args:
            ti_name: Nombre del TI.
            item_name: Nombre del item.

        Returns:
            ResolvedBDLObject o None si el item no tiene objeto BDL asociado.
        """
        conn = self._get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ID_READ_OBJECT, ID_WRITE_OBJECT
                FROM M4RCH_ITEMS
                WHERE ID_TI = ? AND ID_ITEM = ?
            """, ti_name.upper(), item_name.upper())
            row = cursor.fetchone()

            if not row:
                return None

            object_id = row.ID_READ_OBJECT or row.ID_WRITE_OBJECT
            if not object_id:
                return None

            return self.resolve_bdl_object(object_id)

        except Exception as e:
            logger.error("Error resolviendo BDL para item %s.%s: %s", ti_name, item_name, e)
            return None

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
