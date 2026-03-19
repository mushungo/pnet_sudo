---
# Metadata estructurada de la Skill
nombre: "describir_vista_sql"
version: "1.0.0"
descripcion: "Obtiene la definición completa de una Vista SQL del repositorio de PeopleNet, incluyendo su código fuente SQL y metadatos."
# Parámetros que la skill espera recibir.
parametros:
  - nombre: "id_object"
    tipo: "string"
    descripcion: "El identificador único de la Vista a describir. Ej: 'CCO_EVAL360', 'CCO_EVAL360_ANSWERS'."
    requerido: true
---

# (Documentación para humanos)

## Documentación de la Skill: `describir_vista_sql`

### Propósito
Esta skill permite introspeccionar las Vistas SQL definidas en el repositorio de metadatos de PeopleNet. Las vistas son objetos lógicos cuyo contenido se define mediante una sentencia SQL SELECT almacenada en `M4RDC_VIEW_CODE1`. Hay 112 vistas en el repositorio. La skill consulta las tablas `M4RDC_VIEW_CODE` y `M4RDC_VIEW_CODE1` para construir y devolver una representación estructurada (JSON) de la vista con su código fuente SQL.

### Flujo de Trabajo
La skill invoca el script `tools/bdl/get_view.py`, que realiza los siguientes pasos:
1.  **Conexión a la BD**: Se conecta a la base de datos usando las credenciales del entorno.
2.  **Consulta de Vista**: Ejecuta una consulta con `JOIN` sobre `M4RDC_VIEW_CODE`, `M4RDC_VIEW_CODE1` y `M4RDC_LOGIC_OBJECT` para obtener los metadatos y el código SQL de la vista.
3.  **Estructuración de Datos**: Formatea los resultados en un único objeto JSON.
4.  **Devolución de Resultados**: Imprime el objeto JSON a la salida estándar para que el agente lo pueda procesar.

### Datos Disponibles
- **Vista**: ID, descripción (ESP/ENG), nombre físico, si es real, fechas de creación/modificación, AppRole.
- **Código SQL**: El código fuente completo de la sentencia SELECT que define la vista.

### Listado de Vistas
Para obtener un listado de todas las vistas disponibles:
```bash
python -m tools.bdl.list_views
```

### Generación de Diccionario
Para generar la documentación Markdown completa de todas las vistas:
```bash
python -m tools.bdl.build_views_dictionary
```
Los ficheros se generan en `docs/01_bdl/views/`.

### Ejemplos de Uso
Un agente invocaría esta skill a través de la herramienta `bash` de la siguiente manera:

**Comando:**
```bash
python -m tools.bdl.get_view "CCO_EVAL360"
```

**Resultado esperado (ejemplo):**
```json
{
  "status": "success",
  "view": {
    "id_object": "CCO_EVAL360",
    "description": "Vista de Evaluación 360",
    "description_eng": "360 Evaluation View",
    "real_name": "CCO_EVAL360",
    "is_real": true,
    "dt_create": "2020-01-15 00:00:00",
    "dt_closed": null,
    "dt_mod": "2021-06-10 00:00:00",
    "id_approle": "CSA_APPROLE",
    "id_secuser": "META4",
    "view_code": "SELECT A.ID_ORGANIZATION, A.SCO_ID_HR, ..."
  }
}
```
