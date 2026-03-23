---
nombre: "describir_objeto_ramdl"
version: "1.0.0"
descripcion: "Obtiene la definición completa de un Objeto RAMDL (transporte) del repositorio de PeopleNet, incluyendo sus versiones y contenido XML."
parametros:
  - nombre: "id_object"
    tipo: "string"
    descripcion: "El identificador del objeto RAMDL a describir. Ej: 'ALERT', 'APP_ROLE'."
    requerido: true
herramienta: "tools.bdl.get_ramdl_object"
---

## Documentación de la Skill: `describir_objeto_ramdl`

### Nota Organizacional
> La herramienta reside en `tools/bdl/` porque los objetos RAMDL se almacenan en tablas de metadatos de la capa BDL (`M4RDC_RAMDL_OBJECTS`, `M4RDC_RAMDL_OBJEC1`, `M4RDC_RAMDL_VER`). La skill se organiza bajo `04_ramdl/` por afinidad de dominio (RAMDL es el subsistema de transporte de metadatos).

### Propósito
Esta skill permite introspeccionar los Objetos RAMDL (RAM-DL Transport Objects) del repositorio de metadatos de PeopleNet. Los objetos RAMDL son las unidades de transporte que la herramienta de traspasos (RAM-DL) usa para mover definiciones y metadatos entre entornos. Hay 199 objetos con múltiples rangos de versión, cada uno con su XML de definición. Las versiones RAMDL cubren desde la v60250 hasta la v99999.

La skill consulta las tablas `M4RDC_RAMDL_OBJECTS`, `M4RDC_RAMDL_OBJEC1` y `M4RDC_RAMDL_VER`.

### Flujo de Trabajo
La skill invoca el script `tools/bdl/get_ramdl_object.py`, que realiza los siguientes pasos:
1.  **Conexión a la BD**: Se conecta a la base de datos usando las credenciales del entorno.
2.  **Consulta de Objeto**: Ejecuta una consulta con JOIN entre `M4RDC_RAMDL_OBJECTS` y `M4RDC_RAMDL_OBJEC1` para obtener todas las versiones del objeto y la presencia de XML.
3.  **Estructuración de Datos**: Formatea los resultados en un único objeto JSON.
4.  **Devolución de Resultados**: Imprime el objeto JSON a la salida estándar.

### Datos Disponibles
- **Objeto**: ID, nombre (ESP/ENG), número de versiones.
- **Versiones**: versión mínima, versión máxima, presencia y tamaño de XML de definición.

### Listado de Objetos
Para obtener un listado de todos los objetos RAMDL:
```bash
python -m tools.bdl.list_ramdl_objects
```

Para listar las versiones RAMDL registradas:
```bash
python -m tools.bdl.list_ramdl_objects --versions
```

### Generación de Diccionario
Para generar la documentación Markdown completa:
```bash
python -m tools.bdl.build_ramdl_dictionary
```
Los ficheros se generan en `docs/04_ramdl/objects/`.

### Ejemplos de Uso
**Comando:**
```bash
python -m tools.bdl.get_ramdl_object "ALERT"
```

**Resultado esperado (ejemplo):**
```json
{
  "status": "success",
  "ramdl_object": {
    "id_object": "ALERT",
    "name": "Alertas de usuario",
    "version_count": 1,
    "versions": [
      {
        "ver_lowest": 71600,
        "ver_highest": 81000,
        "name": "Alertas de usuario",
        "name_eng": null,
        "has_xml": true,
        "xml_length": 5432
      }
    ]
  }
}
```
