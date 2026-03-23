---
nombre: "describir_conector"
version: "1.0.0"
descripcion: "Obtiene el detalle completo de un conector entre dos nodos de un m4object, incluyendo items conectados y parámetros de sentence."
parametros:
  - nombre: "id_t3"
    tipo: "string"
    descripcion: "Identificador del canal (T3). Ej: 'CHANNEL_EMPLOYEES'."
    requerido: true
  - nombre: "id_ti"
    tipo: "string"
    descripcion: "Identificador del TI origen."
    requerido: true
  - nombre: "id_node"
    tipo: "string"
    descripcion: "Identificador del nodo origen."
    requerido: true
  - nombre: "id_ti_used"
    tipo: "string"
    descripcion: "Identificador del TI destino."
    requerido: true
  - nombre: "id_node_used"
    tipo: "string"
    descripcion: "Identificador del nodo destino."
    requerido: true
herramienta: "tools.m4object.get_connector"
---

## Documentación de la Skill: `describir_conector`

### Propósito
Obtiene el detalle completo de un conector específico entre dos nodos de un m4object. Los conectores definen las relaciones de ejecución y parametrización entre TIs (Table Instances) dentro de un canal.

### Contexto
En PeopleNet, los conectores (`M4RCH_CONNECTORS`) son aristas dirigidas entre nodos de un canal que definen:
- **Tipo de conexión**: call (1), self/bidirectional (3)
- **Items conectados** (`M4RCH_CONCTOR_ITEM`): mapeos entre items del TI origen y destino con precedencia, trigger mode y tipo de contexto
- **Parámetros de sentence** (`M4RCH_CONCTOR_PAR`): campos y alias para parametrizar las sentences del TI destino

### Flujo de Trabajo
1. **Conexión a la BD**: Se conecta usando las credenciales del entorno.
2. **Consulta principal**: Busca el conector en `M4RCH_CONNECTORS` por los 5 campos clave.
3. **Items conectados**: Consulta `M4RCH_CONCTOR_ITEM` para los mapeos entre items.
4. **Parámetros**: Consulta `M4RCH_CONCTOR_PAR` para los parámetros de sentence.
5. **Resultado JSON**: Devuelve el conector con items y parámetros.

### Ejemplos de Uso

```bash
python -m tools.m4object.get_connector "CHANNEL_HR" "TI_EMP" "NODE_1" "TI_SALARY" "NODE_2"
```

**Resultado esperado:**
```json
{
  "id_t3": "CHANNEL_HR",
  "id_ti": "TI_EMP",
  "id_node": "NODE_1",
  "id_ti_used": "TI_SALARY",
  "id_node_used": "NODE_2",
  "connection_type": "call",
  "id_sentence": "SENT_EMP_SALARY",
  "items": [
    {
      "id_item": "ITEM_1",
      "id_item_used": "ITEM_2",
      "precedence": "before",
      "cstype": "parameter"
    }
  ],
  "sentence_params": [
    {
      "id_sentence": "SENT_EMP_SALARY",
      "id_field": "ID_EMPLOYEE",
      "alias": "EMP_ID"
    }
  ]
}
```
