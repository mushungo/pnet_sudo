---
nombre: "encontrar_tis_por_sentence"
version: "1.0.0"
descripcion: "Encuentra todos los TIs (Technical Instances) que usan una sentence dada, trazando la relación inversa sentence -> TIs."
herramienta: "tools.sentences.find_ti_by_sentence"
parametros:
  - nombre: "id_sentence"
    tipo: "string"
    descripcion: "Identificador de la sentence a buscar."
    requerido: true
  - nombre: "detail"
    tipo: "boolean"
    descripcion: "Si true, incluye el canal (T3), nodo y categoría donde se monta cada TI."
    requerido: false
---

## Documentación de la Skill: `encontrar_tis_por_sentence`

### Propósito

Cierra la brecha de trazabilidad inversa entre sentences y M4Objects. Dado un ID de sentence, responde: "¿Qué TIs la consumen como sentence de lectura o escritura?". Esto es esencial para **análisis de impacto**: antes de modificar una sentence (cambiar objetos, JOINs o filtros), necesitas saber qué TIs se verán afectados.

Complementa a `encontrar_sentences_por_objeto` (que va BDL -> sentences) cubriendo la otra dirección: sentence -> TIs -> canales.

### Flujo de Trabajo

1. **Búsqueda en M4RCH_TIS**: Localiza todos los TIs donde `ID_READ_SENTENCE = ?` o `ID_WRITE_SENTENCE = ?`.
2. **Clasificación de uso**: Cada resultado indica si la sentence se usa para lectura (READ), escritura (WRITE) o ambas.
3. **Detalle opcional** (`--detail`): JOIN con `M4RCH_NODES` y `M4RCH_T3S` para resolver en qué canal y nodo está montado cada TI.

### Datos Disponibles

- **TI**: ID, nombre ESP/ENG, objetos BDL de lectura/escritura, flag sistema.
- **Uso**: Lista indicando si la sentence se usa para READ, WRITE, o ambos.
- **Canal** (con `--detail`): ID_T3, nombre del canal, categoría.
- **Nodo** (con `--detail`): ID_NODE, nombre del nodo.

### Ejemplos de Uso

**Búsqueda básica:**
```bash
python -m tools.sentences.find_ti_by_sentence "SEN_EMPLOYEE"
```

**Con detalle de canal y nodo:**
```bash
python -m tools.sentences.find_ti_by_sentence "SEN_EMPLOYEE" --detail
```

### Resultado Esperado (ejemplo simplificado)

```json
{
  "status": "success",
  "sentence_searched": "SEN_EMPLOYEE",
  "count": 3,
  "total_rows": 5,
  "tis": [
    {
      "id_ti": "CCO_EMPLOYEE_DATA",
      "name_esp": "Datos del empleado",
      "usage": ["READ"],
      "read_object": "EMPLOYEE",
      "channel": "CCO_EMPLOYEE",
      "category": "HR_ADMIN"
    }
  ]
}
```
