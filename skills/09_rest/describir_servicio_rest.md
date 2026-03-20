---
nombre: "describir_servicio_rest"
version: "1.0.0"
descripcion: "Obtiene los detalles completos de un TI de integración REST/WS, incluyendo items, argumentos de métodos, y código LN4."
parametros:
  - nombre: "id_ti"
    tipo: "string"
    descripcion: "El identificador del TI de integración. Ej: 'CCO_API_WS_REST'."
    requerido: true
---

## Documentación de la Skill: `describir_servicio_rest`

### Propósito
Obtiene la definición completa de un TI de integración de PeopleNet: sus campos, métodos, argumentos y código fuente LN4. Útil para entender la interfaz de un servicio REST, conector SAP, o web service.

### Información Retornada
- **TI principal**: Canal, nodo, CSTYPE, objetos BDL asociados
- **Items**: Campos (ITEM_TYPE=2) y métodos (ITEM_TYPE=3) con tipo M4
- **Argumentos**: Para cada método, sus argumentos con tipo y dirección (input/output)
- **Reglas LN4**: Código fuente de los métodos (truncado a 2000 caracteres)

### Tablas Consultadas
- `M4RCH_TIS` — Definición del TI
- `M4RCH_ITEMS` — Items (campos y métodos)
- `M4RCH_ITEM_ARGS` — Argumentos de los métodos
- `M4RCH_RULES3` — Código fuente LN4

### Ejemplo de Uso
```bash
python -m tools.rest.get_rest_service "CCO_API_WS_REST"
```

**Resultado esperado:**
```json
{
  "id_ti": "CCO_API_WS_REST",
  "channel": "CCO_API_WS_REST",
  "cstype": 7,
  "cstype_name": "No-BDL",
  "items": [
    {"id_item": "_CCO_CLIENT_ID", "item_type": 2, "item_type_name": "Field"},
    {"id_item": "WS_GET", "item_type": 3, "item_type_name": "Method"}
  ],
  "method_args": {
    "WS_GET": [
      {"id_argument": "URL", "position": 1, "m4_type": 6, "is_output": false},
      {"id_argument": "RESPONSE", "position": 2, "m4_type": 6, "is_output": true}
    ]
  },
  "rules": [
    {"id_item": "WS_GET", "source_code": "...LN4 code..."}
  ]
}
```
