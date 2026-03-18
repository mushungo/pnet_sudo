---
# Metadata estructurada de la Skill
nombre: "describir_relaciones_bdl"
version: "1.0.0"
descripcion: "Describe todas las relaciones lógicas, tanto entrantes como salientes, de un Objeto de la BDL, incluyendo los campos que las componen."
# Parámetros que la skill espera recibir.
parametros:
  - nombre: "id_object"
    tipo: "string"
    descripcion: "El identificador único del Objeto Lógico (BDL) cuyas relaciones se quieren analizar. Ej: 'STD_PERSON'."
    requerido: true
---

# (Documentación para humanos)

## Documentación de la Skill: `describir_relaciones_bdl`

### Propósito
Esta es una skill fundamental para entender el modelo de datos de PeopleNet. Permite a los agentes (como "El Cartógrafo") y a los desarrolladores mapear cómo se conectan las entidades de negocio entre sí. Responde a la pregunta: "¿Con qué otros objetos se relaciona este objeto y cómo?".

### Flujo de Trabajo
La skill invoca el script `tools.bdl.get_bdl_relations.py`, que realiza los siguientes pasos:
1.  **Conexión a la BD**: Se conecta a la base de datos.
2.  **Consulta de Relaciones**: Ejecuta una consulta sobre `M4RDC_RELATIONS` para encontrar todas las relaciones donde el objeto participa.
3.  **Consulta de Campos**: Realiza una segunda consulta sobre `M4RDC_RLTION_FLDS` para obtener todos los mapeos de campos.
4.  **Ensamblaje Jerárquico**: Procesa los resultados y los organiza en un único objeto JSON.

### Ejemplos de Uso
**Comando:**
```bash
python -m tools.bdl.get_bdl_relations "STD_PERSON"
```
