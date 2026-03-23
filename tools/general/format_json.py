# tools/general/format_json.py
"""
Formatea y valida ficheros JSON del proyecto.

Lee un fichero JSON, lo valida sintácticamente, y lo reescribe con formato
consistente (indentación de 2 espacios, UTF-8, newline final).
Opcionalmente puede validar contra un JSON Schema si se proporciona.

Uso:
    python -m tools.general.format_json "ruta/al/fichero.json"
    python -m tools.general.format_json "ruta/al/fichero.json" --check       # Solo verificar, no reescribir
    python -m tools.general.format_json "ruta/al/fichero.json" --schema "schemas/mi_schema.json"
"""
import sys
import json


def format_json_file(file_path, check_only=False, schema_path=None):
    """Lee un fichero JSON, lo valida y opcionalmente lo reescribe con formato consistente.

    Args:
        file_path: Ruta al fichero JSON a formatear.
        check_only: Si es True, solo verifica el formato sin reescribir.
        schema_path: Ruta opcional a un JSON Schema para validación.

    Returns:
        dict con status y detalles del resultado.
    """
    # 1. Leer y parsear el fichero
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()
    except FileNotFoundError:
        return {"status": "error", "message": f"Fichero no encontrado: '{file_path}'."}
    except Exception as e:
        return {"status": "error", "message": f"Error leyendo fichero: {e}"}

    try:
        data = json.loads(original_content)
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"JSON inválido en '{file_path}': {e}",
            "line": e.lineno,
            "column": e.colno,
        }

    # 2. Validar contra JSON Schema si se proporcionó
    schema_errors = []
    if schema_path:
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)

            try:
                import jsonschema
                validator = jsonschema.Draft7Validator(schema)
                for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
                    schema_errors.append({
                        "path": list(error.path),
                        "message": error.message,
                    })
            except ImportError:
                return {
                    "status": "error",
                    "message": "Se requiere el paquete 'jsonschema' para validación contra schema. Instálalo con: pip install jsonschema"
                }
        except FileNotFoundError:
            return {"status": "error", "message": f"Schema no encontrado: '{schema_path}'."}
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Schema JSON inválido en '{schema_path}': {e}"}

    # 3. Generar el contenido formateado (2 espacios, ensure_ascii=False, newline final)
    formatted_content = json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n"

    # 4. Verificar si ya está formateado correctamente
    already_formatted = (original_content == formatted_content)

    result = {
        "status": "success",
        "file": file_path,
        "valid_json": True,
        "already_formatted": already_formatted,
    }

    if schema_path:
        result["schema_valid"] = len(schema_errors) == 0
        if schema_errors:
            result["schema_errors"] = schema_errors

    # 5. Reescribir si no está en modo check-only y el formato cambió
    if not check_only and not already_formatted:
        try:
            with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(formatted_content)
            result["reformatted"] = True
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Error escribiendo fichero: {e}"
            return result
    else:
        result["reformatted"] = False

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Formatea y valida ficheros JSON del proyecto.")
    parser.add_argument("file", help="Ruta al fichero JSON a formatear.")
    parser.add_argument("--check", action="store_true", help="Solo verificar formato, no reescribir.")
    parser.add_argument("--schema", default=None, help="Ruta a un JSON Schema para validación.")

    args = parser.parse_args()
    result = format_json_file(args.file, check_only=args.check, schema_path=args.schema)
    print(json.dumps(result, indent=2, default=str))
