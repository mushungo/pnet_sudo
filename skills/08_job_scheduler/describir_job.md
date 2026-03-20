---
nombre: "describir_job_scheduler_task"
version: "1.0.0"
descripcion: "Obtiene los detalles completos de una tarea programada del Job Scheduler, incluyendo parámetros, ejecuciones recientes, y código asociado."
parametros:
  - nombre: "id_sched_task"
    tipo: "string"
    descripcion: "El identificador de la tarea programada en M4RJS_SCHED_TASKS."
    requerido: true
---

## Documentación de la Skill: `describir_job_scheduler_task`

### Propósito
Obtiene la definición completa de una tarea del Job Scheduler de PeopleNet, incluyendo sus parámetros, historial de ejecuciones, subtareas, y notificaciones asociadas.

### Arquitectura del Job Scheduler
Cada tarea programada combina:
- **SCHED_TASKS**: Definición de scheduling (organización, prioridad, servidor, estado)
- **M4RBP_DEF**: Definición del proceso de negocio (código LN4, tipo, categoría)
- **DEF_PARAMS**: Parámetros de la tarea (nombre + valor)
- **TASK_EXE**: Historial de ejecuciones (fecha, duración, estado, servidor)
- **SUBTASK_EXE**: Subtareas de cada ejecución
- **NOTIFICATIONS**: Notificaciones por evento (inicio, fin, error)

Los jobs ejecutan LN4 dinámicamente vía JIT: `clcExecuteLn4JIT(GET_ARGUMENT("AI_CODE"))`

### Tablas Consultadas
- `M4RJS_SCHED_TASKS` — Definición principal
- `M4RBP_DEF` — Definición del proceso (CODE_TYPE: 1=Win, 2=LN4, 3=Java, 4=Thin)
- `M4RJS_DEF_PARAMS` — Parámetros de la tarea
- `M4RJS_TASK_EXE` — Ejecuciones (últimas 20)
- `M4RJS_SUBTASK_EXE` — Conteo de subtareas
- `M4RJS_NOTIFICATIONS` — Notificaciones configuradas

### Ejemplo de Uso
```bash
python -m tools.job_scheduler.get_job_scheduler_task "abc123-def456"
```

**Resultado esperado:**
```json
{
  "id_sched_task": "abc123-def456",
  "organization": "ORG1",
  "id_bp": "CALC_PAYROLL",
  "status_name": "Waiting",
  "task_definition": {
    "name": "Cálculo de Nómina",
    "code_type_name": "LN4"
  },
  "parameters": [
    {"id_param": 1, "param_name": "PERIOD"}
  ],
  "recent_executions": [...],
  "subtask_count": 12,
  "notifications": [...]
}
```
