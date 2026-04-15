---
nombre: "listar_dependencias_ti"
version: "1.0.0"
descripcion: "Lista un resumen de dependencias por item para un TI completo — cuántas dependencias internas, externas y de canal tiene cada item."
parametros:
  - nombre: "id_ti"
    tipo: "string"
    descripcion: "Identificador del TI a analizar."
    requerido: true
herramienta: "tools.dependencies.list_dependencies"
---

## Documentación de la Skill: `listar_dependencias_ti`

### Propósito
Proporciona una vista panorámica de las dependencias de un TI completo. Para cada item del TI, muestra cuántas dependencias internas tiene, cuántos otros items lo usan, y cuántas conexiones externas y de canal existen.

### Flujo de Trabajo
1. **Agrupación interna**: Agrupa M4RCH_INTERNAL_DEP por ID_ITEM e ID_ITEM_USED.
2. **Agrupación externa**: Agrupa M4RCH_EXTERNAL_DEP por usos y dependientes.
3. **Agrupación de canal**: Agrupa M4RCH_CHANNEL_DEP por usos y dependientes.
4. **Unificación**: Combina todos los items en una lista con conteos por tipo.

### Ejemplos de Uso

```bash
python -m tools.dependencies.list_dependencies "MI_TI"
```

**Resultado esperado:**
```json
{
  "status": "success",
  "id_ti": "MI_TI",
  "total_items": 42,
  "items": [
    {
      "id_item": "ITEM_X",
      "internal_deps": 5,
      "internal_used_by": 3,
      "external_uses": 2,
      "external_dependents": 1,
      "channel_uses": 0,
      "channel_dependents": 0
    }
  ]
}
```
