# tools/general/trace.py
"""
Modulo de trazas para pnet_sudo.

Lee la configuracion de regmeta.xml y escribe trazas con doble salida:
  - Texto plano (.log): con timestamp y header del proceso, legible y grepable
  - JSON lines (.jsonl): estructurado, para analisis programatico

Uso:
    from tools.general.trace import Tracer

    tracer = Tracer("DATABASE")
    tracer.info("Conexion establecida", server="myserver", database="mydb")
    tracer.sql("SELECT TOP 10 * FROM M4RCH_TIS", rows=10, elapsed_ms=45)
    tracer.error("Timeout al ejecutar query", query="SELECT ...")
"""
import os
import sys
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime


# Ruta al proyecto y ficheros de configuracion/logs
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "regmeta.xml")
_LOGS_DIR = os.path.join(_PROJECT_ROOT, ".logs")

# Cache de configuracion (se lee una sola vez por proceso)
_config_cache = None
_config_mtime = None


def _load_config():
    """Lee regmeta.xml y devuelve un dict {nombre_traza: bool}.

    Cachea el resultado y solo recarga si el fichero ha cambiado (por mtime).
    Si el fichero no existe o tiene errores, devuelve un dict vacio
    (todas las trazas desactivadas).
    """
    global _config_cache, _config_mtime

    if not os.path.exists(_CONFIG_PATH):
        _config_cache = {}
        return _config_cache

    try:
        current_mtime = os.path.getmtime(_CONFIG_PATH)
    except OSError:
        _config_cache = {}
        return _config_cache

    if _config_cache is not None and _config_mtime == current_mtime:
        return _config_cache

    try:
        tree = ET.parse(_CONFIG_PATH)
        root = tree.getroot()
        config = {}
        for trace_elem in root.findall(".//trace"):
            name = trace_elem.get("name", "")
            value = trace_elem.get("value", "0")
            if name:
                config[name] = value == "1"
        _config_cache = config
        _config_mtime = current_mtime
        return config
    except (ET.ParseError, OSError) as e:
        print(f"[TRACE] Error leyendo regmeta.xml: {e}", file=sys.stderr)
        _config_cache = {}
        return _config_cache


def is_trace_enabled(trace_name):
    """Comprueba si una categoria de traza esta activada en regmeta.xml.

    Args:
        trace_name: Nombre de la traza (e.g. "Database_trace").

    Returns:
        bool: True si la traza esta activada (value="1").
    """
    config = _load_config()
    return config.get(trace_name, False)


def reload_config():
    """Fuerza la recarga de regmeta.xml en la proxima consulta."""
    global _config_cache, _config_mtime
    _config_cache = None
    _config_mtime = None


class Tracer:
    """Escritor de trazas con doble salida (texto + JSON lines).

    Cada instancia esta asociada a un proceso/subsistema (e.g. "DATABASE",
    "CCT", "LSP", "M4OBJECTS") que aparece como header en las trazas.

    Args:
        process: Nombre del proceso/subsistema (aparece en el header).
        trace_name: Nombre de la variable en regmeta.xml que controla
                    si las trazas de este proceso estan activas.
                    Default: "{process}_trace" (e.g. "DATABASE" -> "Database_trace").
        log_file: Nombre del fichero .log (sin ruta). Default: "pnet_sudo.log".
    """

    def __init__(self, process, trace_name=None, log_file="pnet_sudo.log"):
        self.process = process.upper()
        self.trace_name = trace_name or f"{process.capitalize()}_trace"
        self._log_path = os.path.join(_LOGS_DIR, log_file)
        self._jsonl_path = os.path.join(
            _LOGS_DIR,
            log_file.rsplit(".", 1)[0] + ".jsonl"
        )
        # Asegurar que el directorio de logs existe
        os.makedirs(_LOGS_DIR, exist_ok=True)

    @property
    def enabled(self):
        """Devuelve True si la traza esta activada."""
        return is_trace_enabled(self.trace_name)

    def _write(self, level, message, **extra):
        """Escribe una linea de traza en ambos formatos si la traza esta activa.

        Args:
            level: Nivel de la traza (INFO, SQL, ERROR, WARN, DEBUG).
            message: Mensaje principal de la traza.
            **extra: Campos adicionales que se incluyen en el JSON.
        """
        if not self.enabled:
            return

        now = datetime.now()
        ts = now.strftime("%Y-%m-%d %H:%M:%S.") + f"{now.microsecond // 1000:03d}"

        # --- Texto plano (.log) ---
        text_line = f"{ts} [{self.process}] [{level}] {message}"
        if extra:
            details = " | ".join(f"{k}={v}" for k, v in extra.items())
            text_line += f" | {details}"

        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(text_line + "\n")
        except OSError as e:
            print(f"[TRACE] Error escribiendo {self._log_path}: {e}", file=sys.stderr)

        # --- JSON lines (.jsonl) ---
        json_record = {
            "timestamp": ts,
            "process": self.process,
            "level": level,
            "message": message,
        }
        json_record.update(extra)

        try:
            with open(self._jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(json_record, default=str, ensure_ascii=False) + "\n")
        except OSError as e:
            print(f"[TRACE] Error escribiendo {self._jsonl_path}: {e}", file=sys.stderr)

    def info(self, message, **extra):
        """Traza informativa."""
        self._write("INFO", message, **extra)

    def sql(self, query, **extra):
        """Traza especifica para consultas SQL."""
        # Compactar la query a una linea para el log de texto
        compact_query = " ".join(query.split())
        self._write("SQL", compact_query, **extra)

    def error(self, message, **extra):
        """Traza de error."""
        self._write("ERROR", message, **extra)

    def warn(self, message, **extra):
        """Traza de advertencia."""
        self._write("WARN", message, **extra)

    def debug(self, message, **extra):
        """Traza de depuracion (detallada)."""
        self._write("DEBUG", message, **extra)


# --- Tracer global para base de datos (el mas comun) ---
db_tracer = Tracer("DATABASE", trace_name="Database_trace")
