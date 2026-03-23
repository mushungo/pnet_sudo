---
nombre: "revision_calidad"
version: "1.0.0"
descripcion: "Analiza el código del proyecto para identificar problemas de calidad, consistencia y adherencia a los estándares definidos en AGENTS.md."
parametros:
  - nombre: "ruta"
    tipo: "string"
    descripcion: "Ruta al fichero o directorio a analizar. Si se omite, analiza todo el proyecto."
    requerido: false
  - nombre: "severity"
    tipo: "string"
    descripcion: "Severidad mínima a reportar: 'info', 'warning' o 'error'. Por defecto: 'info'."
    requerido: false
herramienta: "tools.general.revision_calidad"
---

## Documentación de la Skill: `revision_calidad`

### Propósito
Esta skill permite a los agentes (como "El Guardián" o "El Crítico") ejecutar un análisis de calidad sobre el código del proyecto, verificando el cumplimiento de las convenciones definidas en `AGENTS.md`: indentación, longitud de línea, convenciones de nombres, estructura de imports, etc.

### Reglas Verificadas
| Regla | Severidad | Descripción |
|---|---|---|
| `indent-tabs` | error | Detecta tabuladores en la indentación (se esperan 4 espacios). |
| `line-length` | warning | Líneas que superan los 120 caracteres. |
| `import-order` | warning | Imports fuera de orden: stdlib → third-party → local. |
| `naming-function` | warning | Funciones que no siguen `snake_case`. |
| `naming-class` | warning | Clases que no siguen `PascalCase`. |

### Flujo de Trabajo
1. **Identificar ficheros**: Localiza recursivamente los ficheros Python del path dado (o todo el proyecto).
2. **Analizar código**: Aplica las reglas de indentación, longitud de línea, orden de imports y naming.
3. **Generar informe**: Produce un JSON con hallazgos por fichero, organizados por severidad y regla.

### Ejemplos de Uso

**Analizar todo el proyecto:**
```bash
python -m tools.general.revision_calidad
```

**Analizar un directorio específico:**
```bash
python -m tools.general.revision_calidad "tools/bdl/"
```

**Analizar un fichero, solo warnings y errores:**
```bash
python -m tools.general.revision_calidad "tools/bdl/list_bdl_objects.py" --severity warning
```
