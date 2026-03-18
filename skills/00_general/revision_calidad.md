---
# Metadata estructurada de la Skill
nombre: "revision_calidad"
version: "0.1.0"
descripcion: "Analiza el código del proyecto para identificar problemas de calidad, consistencia y adherencia a los estándares definidos en AGENTS.md."
parametros:
  - nombre: "ruta"
    tipo: "string"
    descripcion: "Ruta al fichero o directorio a analizar. Si se omite, analiza todo el proyecto."
    requerido: false
---

## Documentación de la Skill: `revision_calidad`

### Propósito
Esta skill permite a los agentes (como "El Guardián" o "El Crítico") ejecutar un análisis de calidad sobre el código del proyecto, verificando el cumplimiento de las convenciones definidas en `AGENTS.md`: indentación, longitud de línea, convenciones de nombres, estructura de imports, etc.

### Flujo de Trabajo
1. **Identificar ficheros**: Localiza los ficheros Python del proyecto.
2. **Analizar código**: Revisa cada fichero buscando desviaciones de los estándares.
3. **Generar informe**: Produce un informe con los hallazgos organizados por severidad.

### Estado
**No implementada.** Pendiente de desarrollo.
