---
# Metadata estructurada de la Skill
nombre: "gestionar_memoria"
version: "1.0.0"
descripcion: "Gestiona la memoria persistente del proyecto mediante las herramientas MCP de Engram. Permite guardar, buscar y recuperar observaciones entre sesiones de trabajo."
parametros:
  - nombre: "accion"
    tipo: "string"
    descripcion: "La acción a realizar: 'iniciar_sesion', 'guardar', 'buscar', 'recuperar_contexto', 'cerrar_sesion'."
    requerido: true
  - nombre: "contenido"
    tipo: "string"
    descripcion: "El contenido de la observación (para la acción 'guardar') o el texto de búsqueda (para la acción 'buscar')."
    requerido: false
  - nombre: "topic_key"
    tipo: "string"
    descripcion: "La clave temática para clasificar la observación (para la acción 'guardar'). Usar convenciones de AGENTS.md."
    requerido: false
---

## Documentación de la Skill: `gestionar_memoria`

### Propósito
Esta skill documenta cómo los agentes deben interactuar con **Engram**, el sistema de memoria persistente del proyecto. Engram permite que los descubrimientos, decisiones de diseño y hallazgos sobre PeopleNet sobrevivan entre sesiones de opencode.

### Requisitos Previos
- El binario `engram.exe` debe estar en el `PATH` del sistema.
- El servidor HTTP de Engram debe estar en ejecución (`engram serve`). El script `iniciar_contexto_pnet.cmd` lo inicia automáticamente.
- El servidor MCP de Engram debe estar configurado en `opencode.json`.

### Flujo de Trabajo por Acción

#### 1. Iniciar Sesión (`iniciar_sesion`)
Al comienzo de una nueva sesión de trabajo:
1.  Llamar a `mem_context` para recuperar el estado de la sesión anterior.
2.  Si no hay sesión activa, llamar a `mem_session_start` para registrar el inicio.

#### 2. Guardar Observación (`guardar`)
Cuando se descubre algo importante (hallazgo sobre PeopleNet, decisión de diseño, bug encontrado):
1.  Usar `mem_suggest_topic_key` para obtener una clave temática consistente (o elegir una manualmente según las convenciones).
2.  Llamar a `mem_save` con el `topic_key` y el contenido de la observación.

**Convenciones para `topic_key`:**
| Patrón | Uso |
|---|---|
| `pnet/bdl/<nombre_objeto>` | Descubrimientos sobre objetos de la BDL |
| `pnet/m4object/<nombre_canal>` | Descubrimientos sobre m4objects/canales |
| `pnet/arquitectura/<concepto>` | Conceptos arquitectónicos de PeopleNet |
| `proyecto/decision/<nombre>` | Decisiones de diseño del proyecto |
| `proyecto/refactor/<area>` | Notas sobre refactorizaciones realizadas |
| `sesion/<fecha>` | Resúmenes de sesiones de trabajo |

#### 3. Buscar Conocimiento Previo (`buscar`)
Antes de investigar un tema desde cero:
1.  Llamar a `mem_search` con el texto de búsqueda.
2.  Analizar los resultados para evitar trabajo duplicado.
3.  Si se necesita una observación específica, usar `mem_get_observation` con su ID.

#### 4. Recuperar Contexto (`recuperar_contexto`)
Después de cualquier compactación o reinicio de contexto de opencode:
1.  Llamar a `mem_context` inmediatamente.
2.  Revisar el estado recuperado antes de continuar con cualquier tarea.

#### 5. Cerrar Sesión (`cerrar_sesion`)
Al finalizar una sesión de trabajo significativa:
1.  Llamar a `mem_session_summary` para generar un resumen automático.
2.  Llamar a `mem_session_end` para cerrar la sesión.

### Herramientas MCP Disponibles

| Herramienta | Descripción |
|---|---|
| `mem_save` | Guarda una nueva observación con `topic_key` y contenido |
| `mem_update` | Actualiza una observación existente por ID |
| `mem_delete` | Elimina una observación por ID |
| `mem_suggest_topic_key` | Sugiere un `topic_key` consistente |
| `mem_search` | Busca observaciones por texto libre (FTS5) |
| `mem_session_summary` | Genera un resumen de la sesión actual |
| `mem_context` | Recupera el contexto de la sesión |
| `mem_timeline` | Muestra la línea de tiempo de observaciones |
| `mem_get_observation` | Obtiene una observación específica por ID |
| `mem_save_prompt` | Guarda un prompt reutilizable |
| `mem_stats` | Muestra estadísticas de la memoria |
| `mem_session_start` | Inicia una nueva sesión de trabajo |
| `mem_session_end` | Finaliza la sesión de trabajo actual |

### Ejemplos de Uso

**Guardar un descubrimiento sobre la BDL:**
```
mem_save(topic_key="pnet/bdl/ACO_CR_SAL_STRUC", content="El objeto ACO_CR_SAL_STRUC contiene 47 campos y se relaciona con ACO_CR_SAL_HEADER mediante el campo ID_SALARY_CONCEPT.")
```

**Buscar conocimiento previo sobre un tema:**
```
mem_search(query="salary concept structure")
```

**Recuperar contexto tras compactación:**
```
mem_context()
```

### Agentes Recomendados
- **El Arquitecto** y **El Documentalista**: Gestión completa de sesiones (inicio, resumen, cierre).
- **El Intérprete** y **El Cartógrafo**: Guardan descubrimientos sobre la arquitectura de PeopleNet.
- **El Detective**: Persiste hallazgos de depuración.
- **El Narrador**: Persiste resúmenes de documentación.
- **Todos los agentes**: Buscan conocimiento previo y recuperan contexto tras compactación.
