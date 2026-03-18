---
# Metadata estructurada de la Skill
nombre: "describir_funcion_extendida"
version: "1.0.0"
descripcion: "Obtiene la definición completa de una Función Extendida del repositorio de PeopleNet, incluyendo sus argumentos, tipo de retorno y documentación detallada."
# Parámetros que la skill espera recibir.
parametros:
  - nombre: "id_function"
    tipo: "string"
    descripcion: "El identificador único de la Función Extendida a describir. Ej: 'CONCAT', 'ADD_DAYS', 'SUM'."
    requerido: true
---

# (Documentación para humanos)

## Documentación de la Skill: `describir_funcion_extendida`

### Propósito
Esta skill permite introspeccionar las Funciones Extendidas del repositorio de metadatos de PeopleNet. Estas funciones (ABS, ADD_DAYS, CONCAT, SUM, TODAY, etc.) son funciones predefinidas que se pueden usar en reglas, fórmulas y expresiones dentro de PeopleNet. La skill consulta las tablas `M4RDC_EXTENDED_FUN` y `M4RDC_EXT_FUNC_ARG` para construir y devolver una representación estructurada (JSON) de la función con todos sus argumentos.

### Flujo de Trabajo
La skill invoca el script `tools/bdl/get_extended_function.py`, que realiza los siguientes pasos:
1.  **Conexión a la BD**: Se conecta a la base de datos usando las credenciales del entorno.
2.  **Consulta de Función**: Ejecuta una consulta con `JOIN` sobre `M4RDC_EXTENDED_FUN` y `M4RDC_LU_M4_TYPES` para obtener los detalles de la función y su tipo de retorno.
3.  **Consulta de Argumentos**: Ejecuta una segunda consulta sobre `M4RDC_EXT_FUNC_ARG` con `JOIN` a `M4RDC_LU_M4_TYPES` para obtener todos los argumentos ordenados por posición.
4.  **Estructuración de Datos**: Formatea los resultados en un único objeto JSON que contiene los detalles de la función y una lista anidada de sus argumentos.
5.  **Devolución de Resultados**: Imprime el objeto JSON a la salida estándar para que el agente lo pueda procesar.

### Datos Disponibles
- **Función**: ID, nombre (ESP/ENG), tipo de retorno, precisión, escala, uso frecuente, documentación detallada con ejemplos.
- **Argumentos**: posición, nombre, tipo M4, obligatoriedad, valores mínimo y máximo.

### Listado de Funciones
Para obtener un listado de todas las funciones extendidas disponibles:
```bash
python -m tools.bdl.list_extended_functions
```

### Generación de Diccionario
Para generar la documentación Markdown completa de todas las funciones:
```bash
python -m tools.bdl.build_extended_functions_dictionary
```
Los ficheros se generan en `docs/01_bdl/extended_functions/`.

### Ejemplos de Uso
Un agente invocaría esta skill a través de la herramienta `bash` de la siguiente manera:

**Comando:**
```bash
python -m tools.bdl.get_extended_function "CONCAT"
```

**Resultado esperado (ejemplo):**
```json
{
  "id_function": "CONCAT",
  "name": "Concatenar",
  "name_eng": "Concatenate",
  "return_type_id": 2,
  "return_type_name": "Cadena Variable",
  "precision": 255,
  "scale": null,
  "owner_flag": "CSA",
  "frequent_use": true,
  "frequent_use_order": 5,
  "details": "Concatena dos o más cadenas de texto...",
  "details_eng": "Concatenates two or more text strings...",
  "ownership": "CSA",
  "usability": "PUB",
  "arguments": [
    {
      "position": 1,
      "name": "STRING1",
      "type_id": 2,
      "type_name": "Cadena Variable",
      "is_mandatory": true,
      "value_min": null,
      "value_max": null,
      "owner_flag": "CSA"
    }
  ]
}
```
