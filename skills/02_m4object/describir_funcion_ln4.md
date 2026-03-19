---
# Metadata estructurada de la Skill
nombre: "describir_funcion_ln4"
version: "1.0.0"
descripcion: "Obtiene la definición completa de una función LN4 del repositorio de PeopleNet, incluyendo sus argumentos, grupo funcional y documentación."
# Parámetros que la skill espera recibir.
parametros:
  - nombre: "id_ln4_function"
    tipo: "number"
    descripcion: "El identificador numérico de la función LN4 a describir. Ej: 1, 50, 100."
    requerido: true
---

# (Documentación para humanos)

## Documentación de la Skill: `describir_funcion_ln4`

### Propósito
Esta skill permite introspeccionar las funciones del lenguaje propietario LN4 de PeopleNet. LN4 es el lenguaje de scripting usado en reglas, fórmulas y lógica de negocio dentro de Meta4Objects. Hay 301 funciones organizadas en 21 grupos funcionales (funciones básicas, cadenas, conversión de tipos, matemáticas, fechas, monedas, archivos, registros, BDL, Meta4Objects, nómina, etc.).

La skill consulta las tablas `M4RCH_LN4_FUNCTION`, `M4RCH_LN4_FUNCTIO1`, `M4RCH_LN4_FUNC_ARG`, `M4RCH_FUNC_GROUPS` y `M4RDC_LU_M4_TYPES`.

### Flujo de Trabajo
La skill invoca el script `tools/bdl/get_ln4_function.py`, que realiza los siguientes pasos:
1.  **Conexión a la BD**: Se conecta a la base de datos usando las credenciales del entorno.
2.  **Consulta de Función**: Ejecuta una consulta con `JOIN` sobre `M4RCH_LN4_FUNCTION`, `M4RCH_FUNC_GROUPS` y `M4RCH_LN4_FUNCTIO1` para obtener los detalles y comentarios de la función.
3.  **Consulta de Argumentos**: Ejecuta una segunda consulta sobre `M4RCH_LN4_FUNC_ARG` con `JOIN` a `M4RDC_LU_M4_TYPES` para obtener todos los argumentos ordenados por posición.
4.  **Estructuración de Datos**: Formatea los resultados en un único objeto JSON.
5.  **Devolución de Resultados**: Imprime el objeto JSON a la salida estándar.

### Datos Disponibles
- **Función**: ID numérico, nombre, grupo funcional, nivel, si acepta argumentos variables, comentario/documentación (ESP/ENG).
- **Argumentos**: posición, nombre, tipo M4, tipo de argumento, opcionalidad, comentario descriptivo.

### Listado de Funciones
Para obtener un listado de todas las funciones LN4:
```bash
python -m tools.bdl.list_ln4_functions
```

Para listar solo los grupos de funciones:
```bash
python -m tools.bdl.list_ln4_functions --groups
```

Para filtrar por grupo:
```bash
python -m tools.bdl.list_ln4_functions "0050"
```

### Generación de Diccionario
Para generar la documentación Markdown completa de todas las funciones LN4:
```bash
python -m tools.bdl.build_ln4_dictionary
```
Los ficheros se generan en `docs/02_ln4/functions/`.

### Ejemplos de Uso
**Comando:**
```bash
python -m tools.bdl.get_ln4_function 1
```

**Resultado esperado (ejemplo):**
```json
{
  "status": "success",
  "function": {
    "id_ln4_function": 1,
    "name": "clcCompile",
    "item": null,
    "variable_arguments": false,
    "function_level": null,
    "group_id": "0140",
    "group_name": "Funciones de ejecución de código JIT",
    "comment": "Compiles the current item.",
    "comment_eng": "Compiles the current item.",
    "arguments": []
  }
}
```
