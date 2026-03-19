---
nombre: "listar_conectores"
version: "1.0.0"
descripcion: "Lista los conectores a nivel de nodo de un M4Object, mostrando cómo se interconectan los nodos para ejecutar lógica y cargar datos."
parametros:
  - nombre: "id_t3"
    tipo: "string"
    descripcion: "Identificador del canal (T3)."
    requerido: true
  - nombre: "id_ti"
    tipo: "string"
    descripcion: "Filtrar por TI específico."
    requerido: false
  - nombre: "id_node"
    tipo: "string"
    descripcion: "Filtrar por nodo específico (requiere id_ti)."
    requerido: false
---

## Documentación de la Skill: `listar_conectores`

### Propósito
Los conectores a nivel de nodo definen el "cableado" interno de un M4Object — cómo los nodos se conectan entre sí para ejecutar reglas, cargar datos y propagar contexto. Esta skill complementa el listado de conectores a nivel de canal (T3_CONNTORS) con el detalle de ejecución intra-nodo.

### Flujo de Trabajo
1. **Consulta**: Une M4RCH_CONNECTORS con M4RCH_CONCTOR_ITEM para obtener conteos.
2. **Filtrado**: Opcionalmente filtra por TI o nodo.
3. **Resultado**: Lista de conectores con tipo de conexión, sentence asociada y conteo de items conectados.

### Ejemplos de Uso

```bash
python -m tools.m4object.list_connectors "MI_CANAL"
python -m tools.m4object.list_connectors "MI_CANAL" --ti "MI_TI"
python -m tools.m4object.list_connectors "MI_CANAL" --ti "MI_TI" --node "MI_NODO"
```
