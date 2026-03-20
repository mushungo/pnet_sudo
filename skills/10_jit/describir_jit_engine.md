---
nombre: "describir_jit_engine"
version: "1.0.0"
descripcion: "Referencia del motor JIT de PeopleNet — funciones de compilación y ejecución dinámica de código LN4."
parametros: []
---

## Documentación de la Skill: `describir_jit_engine`

### Propósito
Documentación de referencia del motor JIT (Just-In-Time) de PeopleNet — el subsistema que permite compilar y ejecutar código LN4 dinámicamente en tiempo de ejecución.

### Funciones del JIT Engine (Grupo 0140 — 14 funciones)

#### Ejecución directa (single-shot)
| Función | Descripción | Uso en reglas |
|---|---|---|
| `clcExecuteLn4JIT(code, ...)` | Compila y ejecuta código LN4 en un solo paso | 93 reglas |

Este es el patrón más común. El código se pasa como string y se ejecuta inmediatamente.

#### Compilación pre-compiled (hot loops)
| Función | Descripción | Uso en reglas |
|---|---|---|
| `clcPrepareJIT(code, handle, ...)` | Pre-compila código y devuelve un handle | 7-8 reglas |
| `clcExecuteJIT(handle, ...)` | Ejecuta código pre-compilado por handle | 7-8 reglas |
| `clcReleaseJIT(handle)` | Libera un handle de código compilado | 7-8 reglas |

Para loops donde el mismo código se ejecuta repetidamente con diferentes datos.

#### Compilación y verificación
| Función | Descripción |
|---|---|
| `clcCompile(code, handle)` | Compila código sin ejecutar |
| `CompileBlock(code, handle)` | Similar a clcCompile, para bloques |
| `clcCheckSyntax(code, result)` | Verificación de sintaxis sin compilación completa |
| `clcRestoreSource(handle, source)` | Reconstruye código fuente desde handle compilado |

#### Conversión y utilidades
| Función | Descripción |
|---|---|
| `clcSourceToNumber(code)` | Evalúa expresión LN4 y retorna número |
| `clcSourceToString(code)` | Evalúa expresión LN4 y retorna string |
| `clcSourceToId(code)` | Evalúa expresión LN4 y retorna identificador |
| `clcGetPolish(code)` | Obtiene representación en notación polaca |
| `clcOldTiToIdTi(old)` | Convierte ID de TI legacy a formato actual |
| `LocalTest(code)` | Ejecuta prueba local |

### Patrones de Uso

#### Patrón 1: Ejecución directa (más común)
```
sCode = "TI.FIELD = " + sValue
clcExecuteLn4JIT(sCode)
```

#### Patrón 2: Job Scheduler
```
// El Job Scheduler ejecuta tareas via JIT
clcExecuteLn4JIT(GET_ARGUMENT("AI_CODE"))
```

#### Patrón 3: Pre-compilación para loops
```
clcPrepareJIT(sFormula, hJIT)
// ... en cada iteración del loop:
clcExecuteJIT(hJIT)
// ... al final:
clcReleaseJIT(hJIT)
```

#### Patrón 4: Verificación de sintaxis (QBF)
```
clcCheckSyntax(sExpression, nResult)
If nResult = 0 Then
    // Sintaxis válida
End If
```

### Subsistemas que Usan JIT
- **Rule Engine** (`RL_DEF`): Ejecución dinámica de reglas
- **Job Scheduler** (`M4CJS_EXECUTOR`): Ejecución de tareas programadas
- **Calendar/Scheduling**: Cálculos de fechas dinámicos
- **QBF Framework**: Validación de expresiones de usuario
- **Dynamic Dispatch**: Ejecución de código construido programáticamente

### Nota
El JIT Engine es un conjunto de funciones built-in del grupo 0140, documentadas en `ln4_lsp/data/ln4_builtins.json`. No requiere herramientas Python específicas — las 14 funciones ya están disponibles en el autocompletado y hover del LSP.
