---
nombre: "listar_workflows"
version: "1.0.0"
descripcion: "Lista todos los procesos de workflow (BPC) definidos en PeopleNet, incluyendo conteos de estados, transiciones e instancias."
parametros: []
---

## Documentación de la Skill: `listar_workflows`

### Propósito
Lista todas las definiciones de procesos de workflow (BPC — Business Process Configuration) registradas en el motor de workflow de PeopleNet. Cada BPC define un flujo de trabajo con estados, transiciones, tareas y datos.

### Contexto del Motor de Workflow
PeopleNet implementa un motor de workflow completo basado en el modelo **BPC/BPO**:
- **BPC** (Business Process Configuration) = plantilla/definición del workflow
- **BPO** (Business Process Object) = instancia en ejecución
- **STATE** = nodos del grafo (estados del workflow)
- **TRANSITION** = aristas dirigidas entre estados
- **TASK** = actividades asignadas en cada estado
- **WORKITEM** = asignaciones de trabajo a usuarios

### Tablas Principales
- `M4RWF_BPC` — Definiciones de proceso (59 registros típicos)
- `M4RWF_STATE` — Estados del workflow (311 total)
- `M4RWF_TRANSITION` — Transiciones entre estados (298 total)
- `M4RWF_BPO` — Instancias de workflow (~68K)
- `M4RWF_WORKITEM` — Ítems de trabajo (~266K)

### Flujo de Trabajo
1. Conecta a la BD de metadatos de PeopleNet.
2. Consulta `M4RWF_BPC` con subconsultas de conteo para STATE, TRANSITION y BPO.
3. Devuelve JSON con nombre, tipo, clasificación, estado de publicación y estadísticas.

### Ejemplo de Uso
```bash
python -m tools.workflow.list_workflows
```

**Resultado esperado:**
```json
{
  "status": "success",
  "workflows": [
    {
      "id_bpc": 2,
      "name": "Order Process",
      "type": 1,
      "classification": "GENERAL",
      "pub_status": 1,
      "num_states": 5,
      "num_transitions": 6,
      "num_instances": 1250
    }
  ]
}
```
