# tools/general/format_json.py
"""
Formatea y valida ficheros JSON del proyecto.

TODO: Implementar la lógica de formateo consistente (indentación de 2 espacios)
y validación contra los JSON Schemas definidos en schemas/.
"""
import sys
import json


def format_json_file(file_path):
    """Lee un fichero JSON, lo valida y lo reescribe con formato consistente.

    Args:
        file_path: Ruta al fichero JSON a formatear.

    Raises:
        NotImplementedError: Este script aún no está implementado.
    """
    raise NotImplementedError(
        f"El formateo de JSON para '{file_path}' no está implementado."
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Uso: python -m tools.general.format_json \"ruta/al/fichero.json\""}, indent=2))
        sys.exit(1)

    try:
        format_json_file(sys.argv[1])
    except NotImplementedError as e:
        print(json.dumps({"status": "not_implemented", "message": str(e)}, indent=2))
        sys.exit(1)
