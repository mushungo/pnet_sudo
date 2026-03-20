---
nombre: "describir_workflow"
version: "1.0.0"
descripcion: "Obtiene la definición completa de un proceso de workflow (BPC), incluyendo estados, transiciones, tareas, datos, delegaciones y estadísticas."
parametros:
  - nombre: "id_bpc"
    tipo: "integer"
    descripcion: "El identificador numérico del BPC (Business Process Configuration). Ej: 2."
    requerido: true
---

## Documentación de la Skill: `describir_workflow`

### Propósito
Obtiene la definición completa de un proceso de workflow de PeopleNet, permitiendo entender su estructura de estados, transiciones, tareas asignadas y variables de datos.

### Arquitectura BPC/BPO
Cada BPC es un **grafo dirigido** con:
- **Estados** (STATE): nodos con posiciones X/Y para el diseñador visual, tipos de asignación, plazos
- **Transiciones** (TRANSITION): aristas con condiciones opcionales (IS_CONDITION + VALUE_COND)
- **Tareas** (TASK): actividades asociadas a cada estado
- **Datos** (DATADEF): variables del workflow disponibles durante la ejecución
- **Delegaciones** (DELEGATION): reasignaciones con rango de fechas y rol de aplicación
- **Work Items**: asignaciones individuales a usuarios (conteo)

### Tablas Consultadas
- `M4RWF_BPC` — Definición principal (nombre multilingual, deadline, seguridad)
- `M4RWF_STATE` — Estados del grafo (posición visual, tipo, deadline)
- `M4RWF_TRANSITION` — Transiciones (from→to, condiciones, visibilidad)
- `M4RWF_TASK` — Tareas (nombre, estado asociado)
- `M4RWF_DATADEF` — Variables de datos del workflow
- `M4RWF_DELEGATION` — Delegaciones (responsable→delegado, fechas, rol)
- `M4RWF_BPO` / `M4RWF_WORKITEM` — Conteos de instancias

### Ejemplo de Uso
```bash
python -m tools.workflow.get_workflow 2
```

**Resultado esperado:**
```json
{
  "id_bpc": 2,
  "name_esp": "Proceso de Pedido",
  "name_eng": "Order Process",
  "type": 1,
  "states": [
    {"id_state": 1, "name": "Inicio", "type": 0, "position": {"x": 100, "y": 50}},
    {"id_state": 2, "name": "Aprobación", "type": 1, "position": {"x": 300, "y": 50}}
  ],
  "transitions": [
    {"id_transition": 1, "from_state": 1, "to_state": 2, "is_condition": false}
  ],
  "tasks": [
    {"id_task": 1, "id_state": 2, "name": "Aprobar Pedido"}
  ],
  "data_definitions": [...],
  "delegations": [...],
  "instance_count": 1250,
  "workitem_count": 3500
}
```
