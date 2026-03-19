---
# Metadata estructurada de la Skill
nombre: "describir_indice_logico"
version: "1.0.0"
descripcion: "Obtiene la definición completa de un Índice Lógico de la BDL de PeopleNet, incluyendo sus columnas y columnas INCLUDE."
# Parámetros que la skill espera recibir.
parametros:
  - nombre: "id_index"
    tipo: "string"
    descripcion: "El identificador del índice lógico. Ej: 'IDX_001'."
    requerido: true
  - nombre: "id_object"
    tipo: "string"
    descripcion: "El identificador del objeto lógico al que pertenece el índice."
    requerido: true
---

# (Documentación para humanos)

## Documentación de la Skill: `describir_indice_logico`

### Propósito
Esta skill permite introspeccionar los Índices Lógicos definidos en la BDL de PeopleNet. Los índices lógicos definen las estrategias de indexación sobre los objetos lógicos (tablas). Hay 326 índices con 527 columnas regulares y 14 columnas INCLUDE. La skill consulta las tablas `M4RDC_INDEX`, `M4RDC_INDEX_COLS` y `M4RDC_INDEX_INCLUDE_COLS`.

### Flujo de Trabajo
La skill invoca el script `tools/bdl/get_index.py`, que realiza los siguientes pasos:
1.  **Conexión a la BD**: Se conecta a la base de datos usando las credenciales del entorno.
2.  **Consulta de Índice**: Ejecuta una consulta sobre `M4RDC_INDEX` con JOIN a `M4RDC_LOGIC_OBJECT`.
3.  **Consulta de Columnas**: Ejecuta consultas sobre `M4RDC_INDEX_COLS` y `M4RDC_INDEX_INCLUDE_COLS` para obtener las columnas del índice.
4.  **Estructuración de Datos**: Formatea los resultados en un único objeto JSON.
5.  **Devolución de Resultados**: Imprime el objeto JSON a la salida estándar.

### Datos Disponibles
- **Índice**: ID, objeto, unicidad, nombre real, réplica en todas las tablas, fechas.
- **Columnas**: campos ordenados por posición.
- **Columnas INCLUDE**: campos de inclusión no indexados pero almacenados.

### Listado de Índices
Para obtener un listado de todos los índices:
```bash
python -m tools.bdl.list_indexes
```

Para filtrar por objeto:
```bash
python -m tools.bdl.list_indexes "NOMBRE_OBJETO"
```

### Generación de Diccionario
Para generar la documentación Markdown completa de todos los índices:
```bash
python -m tools.bdl.build_indexes_dictionary
```
Los ficheros se generan en `docs/01_bdl/indexes/`.

### Ejemplos de Uso
**Comando:**
```bash
python -m tools.bdl.get_index "IDX_001" "MI_OBJETO"
```
