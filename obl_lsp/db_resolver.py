# obl_lsp/db_resolver.py
"""
Abstracción de acceso a datos para el OBL LSP.
Soporta backend de Base de Datos (SQL Server) y está preparado para Backend Remoto.
"""
import os
import sys
import logging

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import db_connection

logger = logging.getLogger("obl-lsp")

class DataResolver:
    """Base class para resolver metadatos."""
    def get_channel_info(self, id_channel): raise NotImplementedError()
    def get_node_info(self, id_node): raise NotImplementedError()
    def get_item_info(self, id_item): raise NotImplementedError()
    def get_presentation_info(self, id_presentation): raise NotImplementedError()

class DbResolver(DataResolver):
    """Implementación usando SQL Server directo."""
    
    def get_channel_info(self, id_channel):
        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ID_CHANNEL, N_CHANNEL FROM M4RCH_CHANNELS WHERE ID_CHANNEL = ?", id_channel)
                row = cursor.fetchone()
                return {"id": row.ID_CHANNEL, "name": row.N_CHANNEL} if row else None
        except Exception as e:
            logger.error(f"Error resolving channel {id_channel}: {e}")
            return None

    def get_node_info(self, id_node):
        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ID_NODE, N_NODE, ID_CHANNEL FROM M4RCH_NODES WHERE ID_NODE = ?", id_node)
                row = cursor.fetchone()
                return {"id": row.ID_NODE, "name": row.N_NODE, "channel": row.ID_CHANNEL} if row else None
        except Exception as e:
            logger.error(f"Error resolving node {id_node}: {e}")
            return None

    def get_item_info(self, id_item):
        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ID_ITEM, N_ITEM, ID_INTERNAL_TYPE FROM M4RCH_ITEMS WHERE ID_ITEM = ?", id_item)
                row = cursor.fetchone()
                return {"id": row.ID_ITEM, "name": row.N_ITEM, "type": row.ID_INTERNAL_TYPE} if row else None
        except Exception as e:
            logger.error(f"Error resolving item {id_item}: {e}")
            return None

    def get_presentation_info(self, id_presentation):
        try:
            with db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ID_PRESENTATION, N_PRESENTATION FROM M4RPT_PRESENTATION WHERE ID_PRESENTATION = ?", id_presentation)
                row = cursor.fetchone()
                return {"id": row.ID_PRESENTATION, "name": row.N_PRESENTATION} if row else None
        except Exception as e:
            logger.error(f"Error resolving presentation {id_presentation}: {e}")
            return None

class RemoteResolver(DataResolver):
    """Implementación preparada para API remota."""
    def __init__(self, base_url):
        self.base_url = base_url

    def get_channel_info(self, id_channel):
        # TODO: Implementar con requests cuando la API esté disponible
        return {"id": id_channel, "name": f"Remote Channel {id_channel} (API Placeholder)"}

    def get_node_info(self, id_node):
        return {"id": id_node, "name": f"Remote Node {id_node} (API Placeholder)", "channel": "UNKNOWN"}

    def get_item_info(self, id_item):
        return {"id": id_item, "name": f"Remote Item {id_item} (API Placeholder)", "type": 0}

    def get_presentation_info(self, id_presentation):
        return {"id": id_presentation, "name": f"Remote Presentation {id_presentation} (API Placeholder)"}

# Singleton or Factory access
_resolver = None

def get_resolver():
    global _resolver
    if _resolver is None:
        # Por ahora usamos DB, pero permitimos override por env var
        if os.getenv("PNET_REMOTE_URL"):
            _resolver = RemoteResolver(os.getenv("PNET_REMOTE_URL"))
        else:
            _resolver = DbResolver()
    return _resolver
