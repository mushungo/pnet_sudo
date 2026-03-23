---
nombre: "listar_funciones_ln4"
version: "1.0.0"
descripcion: "Lista todas las funciones LN4 del repositorio de PeopleNet, con grupo, argumentos y nivel de función."
parametros:
  - nombre: "group_filter"
    tipo: "string"
    descripcion: "Filtrar por grupo de funciones (ID_FUNC_GROUP). Ej: 'MATH', 'STRING'."
    requerido: false
  - nombre: "groups"
    tipo: "boolean"
    descripcion: "Si se pasa --groups, lista solo los grupos de funciones disponibles en vez de las funciones individuales."
    requerido: false
herramienta: "tools.bdl.list_ln4_functions"
---

## Documentación de la Skill: `listar_funciones_ln4`

### Propósito
Lista todas las funciones LN4 registradas en el repositorio de metadatos. Las funciones LN4 son funciones del lenguaje de scripting de PeopleNet, agrupadas por categoría funcional (matemáticas, cadenas, fechas, etc.).

### Nota Organizacional
> La herramienta reside en `tools/bdl/` porque las funciones LN4 se almacenan en tablas de metadatos de la capa BDL (`M4RCH_LN4_FUNCTION`, `M4RCH_FUNC_GROUPS`, `M4RCH_LN4_FUNC_ARG`). La skill se organiza bajo `02_m4object/` por afinidad de dominio (LN4 es el lenguaje de scripting que opera sobre los m4objects).

### Flujo de Trabajo
1. **Conexión a la BD**: Se conecta usando las credenciales del entorno.
2. **Consulta con JOINs**: Ejecuta un SELECT sobre `M4RCH_LN4_FUNCTION` con JOIN a `M4RCH_FUNC_GROUPS` y `M4RCH_LN4_FUNCTIO1` (comentarios), más subconsulta de conteo sobre `M4RCH_LN4_FUNC_ARG`.
3. **Filtrado opcional**: Permite filtrar por grupo o listar solo los grupos.
4. **Resultado JSON**: Devuelve la lista con nombre, grupo, comentarios, conteo de args y nivel.

### Ejemplos de Uso

**Listar todas las funciones:**
```bash
python -m tools.bdl.list_ln4_functions
```

**Filtrar por grupo:**
```bash
python -m tools.bdl.list_ln4_functions "MATH"
```

**Listar solo los grupos:**
```bash
python -m tools.bdl.list_ln4_functions --groups
```
