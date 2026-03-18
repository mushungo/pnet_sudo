---
# Metadata estructurada de la Skill
nombre: "describir_bdl_object"
version: "1.0.0"
descripcion: "Obtiene la definición completa de un Objeto Lógico (BDL) de PeopleNet, incluyendo todos sus campos y propiedades principales."
# Parámetros que la skill espera recibir.
parametros:
  - nombre: "id_object"
    tipo: "string"
    descripcion: "El identificador único del Objeto Lógico (BDL) a describir. Ej: 'ACO_CR_SAL_STRUC'."
    requerido: true
---

# (Documentación para humanos)

## Documentación de la Skill: `describir_bdl_object`

### Propósito
Esta skill sirve como la principal herramienta de introspección para la Base de Datos Lógica (BDL) de PeopleNet. Consulta el repositorio de metadatos para construir y devolver una representación estructurada (JSON) de un objeto lógico y sus campos.

### Flujo de Trabajo
La skill invoca el script `tools/bdl/get_bdl_object.py`, que realiza los siguientes pasos:
1.  **Conexión a la BD**: Se conecta a la base de datos usando las credenciales del entorno.
2.  **Consulta de Metadatos**: Ejecuta una consulta con `JOIN` sobre las tablas `M4RDC_LOGIC_OBJECT` y `M4RDC_FIELDS`.
3.  **Estructuración de Datos**: Formatea los resultados en un único objeto JSON que contiene los detalles del objeto y una lista anidada de sus campos.
4.  **Devolución de Resultados**: Imprime el objeto JSON a la salida estándar para que el agente lo pueda procesar.

### Ejemplos de Uso
Un agente (como "El Intérprete") invocaría esta skill a través de la herramienta `bash` de la siguiente manera:

**Comando:**
```bash
python -m tools.bdl.get_bdl_object "ACO_CR_SAL_STRUC"
```

**Resultado esperado (ejemplo):**
```json
{
  "id_object": "ACO_CR_SAL_STRUC",
  "object_real_name": "M4ACO_CR_SAL_STRUC",
  "description": "Auditoría estructura salarial",
  "fields": [
    {
      "id_field": "ID_SAL_STR_ST",
      "field_real_name": "ID_SAL_STR_ST",
      "type": "STRING",
      "is_primary_key": true,
      // ... más propiedades del campo
    }
    // ... más campos
  ]
}
```
