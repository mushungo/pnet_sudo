# AGENTS.md

This document provides guidelines for agentic coding agents working in this repository.

## Inicio de Sesión (EJECUTAR SIEMPRE AL COMENZAR)

**Al iniciar una nueva sesión, el agente DEBE ejecutar estos pasos antes de hacer cualquier otra cosa:**

1.  **Recuperar contexto de Engram:** Llamar a `mem_context(project="pnet_sudo")` para obtener el estado de sesiones anteriores, descubrimientos y decisiones previas.
2.  **Registrar inicio de sesión:** Llamar a `mem_session_start(id="session-<FECHA>-<TEMA>", project="pnet_sudo")` con un ID descriptivo.
3.  **Presentar un resumen breve** al usuario con lo recuperado: qué se hizo antes, qué quedó pendiente, y en qué punto está el proyecto.

### Contexto del Proyecto

**pnet_sudo** es un toolkit de introspección de metadatos de PeopleNet con agentes de IA, skills y herramientas Python. Los subsistemas principales son:

| Subsistema | Directorio | Descripción |
|---|---|---|
| **BDL** | `tools/bdl/` | Herramientas para la Business Data Layer (list, get, build dictionary) + Physical Layer |
| **M4Object** | `tools/m4object/` | Herramientas para canales/m4objects (list, get, build dictionary) + Conectores |
| **Sentences** | `tools/sentences/` | Herramientas para sentences (definiciones de acceso a datos SQL-like) |
| **Dependencies** | `tools/dependencies/` | Análisis de impacto y trazado de dependencias entre items |
| **Security** | `tools/security/` | Herramientas para usuarios, roles y permisos de aplicación |
| **LN4 LSP** | `ln4_lsp/` | Language Server Protocol para el lenguaje LN4 de PeopleNet |
| **VS Code Extension** | `vscode-ln4/` | Extensión VS Code con syntax highlighting y cliente LSP |
| **Skills** | `skills/` | Skills documentales para agentes (Markdown con YAML frontmatter) |
| **Agentes** | `agentes/` | Definiciones de agentes especializados |
| **General** | `tools/general/` | Utilidades compartidas (db_utils.py) |

### LN4 LSP — Estado Actual

El LSP para LN4 está **completo en 6 fases + mejoras incrementales**:

| Fase | Descripción | Directorio/Archivos clave |
|---|---|---|
| 1 | Gramática ANTLR4 + Parser | `ln4_lsp/grammar/LN4.g4`, `ln4_lsp/generated/` |
| 2 | Servidor LSP (pygls, STDIO/TCP) | `ln4_lsp/server.py`, `ln4_lsp/__main__.py` |
| 3 | Diagnósticos semánticos | `ln4_lsp/semantic.py`, `ln4_lsp/ln4_builtins.py` |
| 4 | Autocompletado + Hover | `ln4_lsp/completion.py` |
| 5 | Go-to-definition | `ln4_lsp/symbol_index.py`, `ln4_lsp/db_resolver.py`, `ln4_lsp/definition.py` |
| 6 | Extensión VS Code | `vscode-ln4/` (package.json, extension.ts, tmLanguage, etc.) |
| + | Signature Help (built-in + TI methods) | `ln4_lsp/signature_help.py` |
| + | Completion contextual de TI items | `ln4_lsp/completion.py` (tras "TI.") |
| + | Hover DB para TI.ITEM con ITEM_ARGS | `ln4_lsp/completion.py`, `ln4_lsp/db_resolver.py` |

**Cómo ejecutar el LSP:**
```bash
python -m ln4_lsp          # STDIO (modo normal para editores)
python -m ln4_lsp --tcp    # TCP (para desarrollo/debug)
```

**Cómo ejecutar los tests:**
```bash
python -m ln4_lsp.tests.test_parser        # 13 samples
python -m ln4_lsp.tests.test_semantic       # 23 tests
python -m ln4_lsp.tests.test_completion     # 37 tests
python -m ln4_lsp.tests.test_symbol_index   # 21 tests
python -m ln4_lsp.tests.test_definition     # 16 tests
python -m ln4_lsp.tests.test_db_resolver    # 24 tests (requiere DB)
python -m ln4_lsp.tests.test_signature_help # 31 tests
python -m ln4_lsp.tests.test_server         # 27 tests
python -m ln4_lsp.tests.test_lsp_integration # 4 end-to-end tests
```

**Regenerar parser ANTLR4** (requiere Java 11):
```bash
"C:\java\jdk-11.0.26.4-hotspot\bin\java.exe" -jar "ln4_lsp/grammar/antlr-4.13.2-complete.jar" -Dlanguage=Python3 -visitor -o "ln4_lsp/generated" "ln4_lsp/grammar/LN4.g4"
```

**Empaquetar extensión VS Code:**
```bash
cd vscode-ln4 && npm install && npx @vscode/vsce package --allow-missing-repository
```

### Conexión a Base de Datos

Las herramientas de `tools/` y el `db_resolver.py` del LSP se conectan a SQL Server mediante `tools/general/db_utils.py`. La configuración de conexión se lee de `.env` (no committeado). Sin DB disponible, los tests de DB se auto-saltan y el DBResolver devuelve `None` gracefully.

## Build, Lint, and Test Commands

This project does not have a conventional build, lint, or test process. It is a collection of Python scripts, JSON files, and Markdown documents.

### Running Scripts

The Python scripts are intended to be run directly from the command line.

**Example:**
```bash
python tools/bdl/build_bdl_dictionary.py
```

### Testing

Las herramientas Python en `tools/` no tienen tests automatizados. Para el **LN4 LSP** sí hay 8 suites de tests (ver sección "LN4 LSP — Estado Actual" arriba). Al modificar código del LSP, ejecutar los tests relevantes para verificar que no hay regresiones.

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
*   `pnet/cct/<nombre_cct>` — Descubrimientos sobre Controles de Cambio (CCT).
*   `pnet/nomina/<nombre_concepto>` — Descubrimientos sobre conceptos de nómina.
*   `pnet/arquitectura/<concepto>` — Conceptos arquitectónicos de PeopleNet.
*   `proyecto/decision/<nombre>` — Decisiones de diseño del proyecto.
*   `proyecto/refactor/<area>` — Notas sobre refactorizaciones realizadas.
*   `sesion/<fecha>` — Resúmenes de sesiones de trabajo.

## Cursor and Copilot Rules

There are no `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md` files in this repository.
