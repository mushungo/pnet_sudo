---
# Metadata estructurada de la Skill
nombre: "describir_modulo_datos"
version: "1.0.0"
descripcion: "Obtiene la definición completa de un Módulo de Datos (Case Module) de PeopleNet, incluyendo todos sus objetos y relaciones asignados."
# Parámetros que la skill espera recibir.
parametros:
  - nombre: "id_module"
    tipo: "string"
    descripcion: "El identificador único del Módulo de Datos a describir. Ej: 'BENEFITS_PLAN_DEFINITION', 'CCO_GASTOS_MED'."
    requerido: true
---

# (Documentación para humanos)

## Documentación de la Skill: `describir_modulo_datos`

### Propósito
Esta skill permite introspeccionar los Módulos de Datos (Case Modules) del repositorio de metadatos de PeopleNet. Los módulos de datos agrupan objetos lógicos (BDL) y sus relaciones en dominios funcionales, actuando como un mapa organizativo de la base de datos lógica. La skill consulta las tablas `M4RDD_CASE_MODULES`, `M4RDD_CMOD_OBJS` y `M4RDD_CMOD_RELS` para construir una representación estructurada (JSON) del módulo con todos sus objetos y relaciones.

### Flujo de Trabajo
La skill invoca el script `tools/bdl/get_case_module.py`, que realiza los siguientes pasos:
1.  **Conexión a la BD**: Se conecta a la base de datos usando las credenciales del entorno.
2.  **Consulta de Módulo**: Ejecuta una consulta sobre `M4RDD_CASE_MODULES` para obtener los detalles del módulo.
3.  **Consulta de Objetos**: Ejecuta una consulta con `JOIN` sobre `M4RDD_CMOD_OBJS` y `M4RDC_LOGIC_OBJECT` para obtener todos los objetos asignados al módulo con sus descripciones y tipos.
4.  **Consulta de Relaciones**: Ejecuta una consulta con `JOIN` sobre `M4RDD_CMOD_RELS` y `M4RDC_RELATIONS` para obtener todas las relaciones asignadas al módulo con sus detalles.
5.  **Estructuración de Datos**: Formatea los resultados en un único objeto JSON que contiene los detalles del módulo, la lista de objetos y la lista de relaciones.
6.  **Devolución de Resultados**: Imprime el objeto JSON a la salida estándar para que el agente lo pueda procesar.

### Datos Disponibles
- **Módulo**: ID, nombre (ESP/ENG), owner flag, dependencia cross-module, ownership, usability.
- **Objetos**: ID, descripción, tipo de objeto, estado oculto/visible, estado, fechas de creación/cierre.
- **Relaciones**: ID relación, objeto hijo, objeto padre, tipo de relación, estilo de línea, estado oculto/visible.

### Listado de Módulos
Para obtener un listado de todos los módulos de datos disponibles:
```bash
python -m tools.bdl.list_case_modules
```

### Generación de Diccionario
Para generar la documentación Markdown completa de todos los módulos:
```bash
python -m tools.bdl.build_case_modules_dictionary
```
Los ficheros se generan en `docs/01_bdl/case_modules/`.

### Ejemplos de Uso
Un agente invocaría esta skill a través de la herramienta `bash` de la siguiente manera:

**Comando:**
```bash
python -m tools.bdl.get_case_module "BENEFITS_PLAN_DEFINITION"
```

**Resultado esperado (ejemplo):**
```json
{
  "id_module": "BENEFITS_PLAN_DEFINITION",
  "name": "Definición de Plan de Beneficios",
  "name_eng": "Benefits Plan Definition",
  "owner_flag": "CSA",
  "dep_cross_mod": null,
  "ownership": "CSA",
  "usability": "PUB",
  "objects": [
    {
      "id_object": "BEN_PLAN",
      "description": "Plan de beneficios",
      "object_type": "TABLE",
      "hidden": false,
      "status": "ACTIVE",
      "dt_create": "2001-01-01",
      "dt_closed": null
    }
  ],
  "relations": [
    {
      "id_object": "BEN_PLAN_DETAIL",
      "id_relation": "BEN_PLAN_TO_DETAIL",
      "id_parent_object": "BEN_PLAN",
      "relation_type": "FK",
      "line_style": null,
      "hidden": false,
      "dt_create": "2001-01-01",
      "dt_closed": null
    }
  ],
  "object_count": 47,
  "relation_count": 171
}
```
