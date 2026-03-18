# tools/bdl/build_extended_types_dictionary.py
"""
Genera una base de conocimiento en Markdown de todos los Tipos Extendidos
de la Base de Datos Lógica (BDL) de PeopleNet.

Similar a build_bdl_dictionary.py pero para tipos extendidos.
Consulta la tabla M4RDC_EXTENDED_TPS y genera un fichero .md por cada tipo,
más un índice maestro en docs/01_bdl/extended_types/.

TODO: Implementar la lógica de generación siguiendo el patrón
de build_bdl_dictionary.py.
"""
import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def build_extended_types_dictionary():
    """Genera todos los ficheros Markdown del diccionario de tipos extendidos.

    Raises:
        NotImplementedError: Este script aún no está implementado.
    """
    raise NotImplementedError(
        "La generación del diccionario de tipos extendidos no está implementada. "
        "Consulta build_bdl_dictionary.py como referencia de implementación."
    )


if __name__ == "__main__":
    try:
        build_extended_types_dictionary()
    except NotImplementedError as e:
        print(json.dumps({"status": "not_implemented", "message": str(e)}, indent=2))
        sys.exit(1)
