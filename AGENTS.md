# AGENTS.md

This document provides guidelines for agentic coding agents working in this repository.

## Build, Lint, and Test Commands

This project does not have a conventional build, lint, or test process. It is a collection of Python scripts, JSON files, and Markdown documents.

### Running Scripts

The Python scripts are intended to be run directly from the command line.

**Example:**
```bash
python tools/bdl/build_bdl_dictionary.py
```

### Testing

There are no automated tests in this project. When modifying a script, you should manually test it to ensure it works as expected.

### Linting

There is no linter configured for this project. Please adhere to the code style guidelines below to maintain consistency.

## Code Style Guidelines

### Python

#### Formatting

*   **Indentation**: Use 4 spaces for indentation.
*   **Line Length**: Keep lines under 120 characters.
*   **Whitespace**: Use whitespace to improve readability.
*   **Quotes**: Use double quotes for strings.

#### Imports

*   Imports should be at the top of the file.
*   Standard library imports should be first, followed by third-party imports, and then local application imports.
*   The `sys.path` is modified in some scripts to import local modules. This is an acceptable pattern in this repository.

**Example:**
```python
import sys
import os
from datetime import datetime
from collections import defaultdict

# Ajustar el sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.general.db_utils import get_db_connection
```

#### Naming Conventions

*   **Functions**: Use `snake_case` (e.g., `fetch_all_metadata`).
*   **Variables**: Use `snake_case` (e.g., `project_root`).
*   **Classes**: Use `PascalCase` (e.g., `MyClass`).
*   **Constants**: Use `UPPER_CASE` (e.g., `MY_CONSTANT`).

#### Types

*   This project does not use type hints.

#### Error Handling

*   Use `try...except...finally` blocks to handle exceptions and ensure that resources are properly cleaned up (e.g., closing database connections).

**Example:**
```python
try:
    # Code that may raise an exception
except Exception as e:
    print(f"An error occurred: {e}", file=sys.stderr)
finally:
    # Clean up resources
```

#### Comments

*   Use comments to explain the purpose of code that is not self-evident.
*   Use docstrings to explain the purpose of functions and modules.

### JSON

*   JSON files should be well-formatted with an indentation of 2 spaces.

### Markdown

*   Use Markdown for documentation.
*   Follow standard Markdown conventions.

## Memoria Persistente (Engram)

Este proyecto utiliza [Engram](https://github.com/Gentleman-Programming/engram) como sistema de memoria persistente para los agentes de IA. Engram proporciona herramientas MCP que permiten guardar, buscar y recuperar observaciones entre sesiones.

### Protocolo de Memoria

Los agentes deben seguir estas reglas al interactuar con la memoria:

1.  **Inicio de sesión:** Al comenzar una nueva sesión de trabajo, llamar a `mem_context` para recuperar el estado previo antes de continuar. Si hay una sesión activa, usar `mem_session_start` para registrar el inicio.
2.  **Guardar descubrimientos:** Usar `mem_save` para persistir hallazgos importantes, decisiones de diseño, descubrimientos sobre la arquitectura de PeopleNet, y cualquier información que deba sobrevivir entre sesiones.
3.  **Buscar conocimiento previo:** Antes de investigar algo de cero, usar `mem_search` para verificar si ya existe conocimiento previo sobre el tema.
4.  **Resumen de sesión:** Al finalizar una sesión de trabajo significativa, usar `mem_session_summary` para generar un resumen y `mem_session_end` para cerrar la sesión.
5.  **Supervivencia ante compactación:** Después de cualquier compactación o reinicio de contexto, llamar a `mem_context` para recuperar el estado de la sesión antes de continuar.

### Herramientas MCP de Engram Disponibles

| Herramienta | Descripción |
|---|---|
| `mem_save` | Guarda una nueva observación con `topic_key` y contenido. |
| `mem_update` | Actualiza una observación existente por ID. |
| `mem_delete` | Elimina una observación por ID. |
| `mem_suggest_topic_key` | Sugiere un `topic_key` consistente para una observación. |
| `mem_search` | Busca observaciones por texto libre (FTS5). |
| `mem_session_summary` | Genera un resumen de la sesión actual. |
| `mem_context` | Recupera el contexto de la sesión (usar tras compactación). |
| `mem_timeline` | Muestra la línea de tiempo de observaciones. |
| `mem_get_observation` | Obtiene una observación específica por ID. |
| `mem_save_prompt` | Guarda un prompt reutilizable. |
| `mem_stats` | Muestra estadísticas de la memoria. |
| `mem_session_start` | Inicia una nueva sesión de trabajo. |
| `mem_session_end` | Finaliza la sesión de trabajo actual. |

### Convenciones para `topic_key`

Usar nombres descriptivos en `snake_case` que sigan el dominio del proyecto:

*   `pnet/bdl/<nombre_objeto>` — Descubrimientos sobre objetos de la BDL.
*   `pnet/m4object/<nombre_canal>` — Descubrimientos sobre m4objects/canales.
*   `pnet/arquitectura/<concepto>` — Conceptos arquitectónicos de PeopleNet.
*   `proyecto/decision/<nombre>` — Decisiones de diseño del proyecto.
*   `proyecto/refactor/<area>` — Notas sobre refactorizaciones realizadas.
*   `sesion/<fecha>` — Resúmenes de sesiones de trabajo.

## Cursor and Copilot Rules

There are no `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md` files in this repository.
