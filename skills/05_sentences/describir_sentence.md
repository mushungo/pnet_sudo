---
nombre: "describir_sentence"
version: "1.0.0"
descripcion: "Obtiene la definición completa de una sentence de PeopleNet, incluyendo objetos FROM, JOINs, filtros, funciones y columnas calculadas."
parametros:
  - nombre: "id_sentence"
    tipo: "string"
    descripcion: "El identificador único de la sentence. Ej: 'EMPLOYEE_DATA_LOAD'."
    requerido: true
---

## Documentación de la Skill: `describir_sentence`

### Propósito
Obtiene la definición completa de una sentence — la unidad de acceso a datos de PeopleNet. Una sentence es análoga a un SELECT SQL con FROM, JOIN, WHERE, ORDER BY y columnas calculadas, pero almacenada como metadatos.

### Flujo de Trabajo
1. **Consulta principal**: Obtiene la sentence de M4RCH_SENTENCES.
2. **Objetos (FROM)**: Lista los objetos BDL referenciados con sus alias desde SENT_OBJECTS.
3. **Relaciones (JOIN)**: Lista las relaciones entre objetos desde SENT_OBJ_REL con tipo (INNER/LEFT/OUTER).
4. **Campos de filtro**: Lista campos de WHERE/ORDER BY/GROUP BY desde SENT_ADD_FLD.
5. **Funciones SQL**: Lista funciones usadas desde SENT_FUNCS.
6. **Cálculos**: Lista columnas calculadas con expresiones desde SENT_CALCULU.

### Ejemplos de Uso

```bash
python -m tools.sentences.get_sentence "MI_SENTENCE_ID"
```

**Resultado esperado:**
```json
{
  "id_sentence": "MI_SENTENCE_ID",
  "sent_type": 1,
  "objects": [
    {"id_object": "EMPLOYEE", "alias": "A", "is_basis": true}
  ],
  "joins": [...],
  "filter_fields": [...],
  "functions": [...],
  "calculated_columns": [...]
}
```
