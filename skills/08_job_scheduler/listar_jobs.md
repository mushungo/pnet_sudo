---
nombre: "listar_job_scheduler_tasks"
version: "1.0.0"
descripcion: "Lista las tareas programadas del Job Scheduler de PeopleNet, tanto del sistema moderno (SCHED_TASKS) como del legacy (JOB_DEF)."
parametros:
  - nombre: "legacy"
    tipo: "boolean"
    descripcion: "Si es true, lista los trabajos del sistema legacy (M4RJS_JOB_DEF) en lugar del moderno."
    requerido: false
---

## Documentación de la Skill: `listar_job_scheduler_tasks`

### Propósito
Lista las tareas programadas registradas en el Job Scheduler de PeopleNet. Soporta ambos subsistemas de planificación: el **moderno** (M4RJS_SCHED_TASKS) y el **legacy** (M4RJS_JOB_DEF).

### Contexto del Job Scheduler
PeopleNet tiene un subsistema de planificación de trabajos con **66 tablas M4RJS_***:

**Sistema moderno (SCHED_TASKS)**:
- ~94K tareas programadas en `M4RJS_SCHED_TASKS`
- ~108K ejecuciones en `M4RJS_TASK_EXE`
- ~214K subtareas en `M4RJS_SUBTASK_EXE`
- Soporte para parámetros, notificaciones, calendarios, recursos

**Sistema legacy (JOB_DEF)**:
- ~1,166 definiciones en `M4RJS_JOB_DEF`
- Tipos: OLD_FORMAT (0), LN4 (1), ADMIN (2)

**Estados de ejecución**: 0=Executed, 1=Waiting, 2=Executing, 3=Cancelling, 4=Expired, 5=Cancelled, 6=Interrupted, 10=Aborting, 11=Aborted

### Ejemplo de Uso
```bash
# Sistema moderno (por defecto)
python -m tools.job_scheduler.list_job_scheduler_tasks

# Sistema legacy
python -m tools.job_scheduler.list_job_scheduler_tasks --legacy
```

**Resultado esperado (moderno):**
```json
{
  "status": "success",
  "count": 500,
  "tasks": [
    {
      "id_sched_task": "abc123",
      "organization": "ORG1",
      "id_bp": "CALC_PAYROLL",
      "status": 0,
      "status_name": "Executed",
      "num_executions": 45
    }
  ]
}
```
