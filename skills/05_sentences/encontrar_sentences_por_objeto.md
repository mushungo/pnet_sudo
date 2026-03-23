---
nombre: "encontrar_sentences_por_objeto"
version: "1.0.0"
descripcion: "Encuentra todas las sentences que referencian un Objeto Lógico (BDL) dado en su cláusula FROM."
herramienta: "tools.sentences.find_sentence_by_object"
parametros:
  - nombre: "id_object"
    tipo: "string"
    descripcion: "Identificador del objeto BDL a buscar (ej: 'EMPLOYEE', 'STD_PERSON')."
    requerido: true
  - nombre: "detail"
    tipo: "boolean"
    descripcion: "Si true, incluye la lista completa de objetos y JOINs de cada sentence encontrada."
    requerido: false
---

## Documentación de la Skill: `encontrar_sentences_por_objeto`

### Propósito

Cierra la brecha de trazabilidad entre la BDL y las sentences. Dado un objeto lógico, responde: "¿Qué sentences lo usan en su FROM?". Esto es esencial para **análisis de impacto**: antes de modificar un objeto BDL (agregar/renombrar/eliminar campos), necesitas saber qué sentences se verán afectadas.

Complementa a `encontrar_usos_bdl_object` (que busca usos en m4objects/canales) cubriendo la otra dimensión de dependencia: el acceso a datos vía sentences.

### Flujo de Trabajo

1. **Búsqueda en SENT_OBJECTS**: Localiza todas las sentences donde `ID_OBJECT = ?` en `M4RCH_SENT_OBJECTS`.
2. **Enriquecimiento**: Para cada sentence, agrega conteos de objetos totales, JOINs y filtros.
3. **Detalle opcional** (`--detail`): Incluye la lista completa de objetos (FROM) y JOINs de cada sentence, útil para entender el contexto de uso del objeto.

### Ejemplos de Uso

**Búsqueda simple:**
```bash
python -m tools.sentences.find_sentence_by_object "EMPLOYEE"
```

**Con detalle de objetos y JOINs:**
```bash
python -m tools.sentences.find_sentence_by_object "EMPLOYEE" --detail
```

**Resultado esperado:**
```json
{
  "status": "success",
  "bdl_object_searched": "EMPLOYEE",
  "count": 42,
  "sentences": [
    {
      "id_sentence": "SENT_EMPLOYEE_LOAD",
      "alias_in_sentence": "A",
      "is_basis": true,
      "sent_type": 1,
      "total_objects": 3,
      "total_joins": 2,
      "total_filters": 5
    }
  ]
}
```

### Caso de uso: Análisis de Impacto Cruzado

Para evaluar el impacto completo de un cambio en un objeto BDL:

1. `encontrar_usos_bdl_object` → qué **canales** (m4objects) lo usan
2. `encontrar_sentences_por_objeto` → qué **sentences** lo referencian
3. `describir_relaciones_bdl` → qué **relaciones lógicas** conectan con otros objetos

Estos tres resultados cubren las 3 dimensiones de dependencia de un objeto BDL en PeopleNet.
