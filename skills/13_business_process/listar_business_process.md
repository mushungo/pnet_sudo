---
nombre: "listar_business_process"
version: "1.0.0"
descripcion: "Lista los Business Processes (tareas) de PeopleNet con filtros por texto, canal o presentación asociada."
parametros:
  - nombre: "search"
    tipo: "string"
    requerido: false
    descripcion: "Texto a buscar en ID o nombre ESP/ENG"
  - nombre: "t3"
    tipo: "string"
    requerido: false
    descripcion: "Filtrar por ID_T3 (canal al que pertenece el BP)"
  - nombre: "with_presentation"
    tipo: "boolean"
    requerido: false
    descripcion: "Solo BPs que tienen una presentación asociada"
  - nombre: "limit"
    tipo: "integer"
    requerido: false
    descripcion: "Máximo de resultados (default 200)"
---

## Documentacion de la Skill: `listar_business_process`

### Proposito
Lista los Business Processes (tareas) registrados en el catálogo de PeopleNet. Un Business Process (BP) es una tarea de negocio que se vincula a menús y puede tener una presentación asociada.

### Contexto del Sistema de Business Processes
PeopleNet implementa un sistema de tareas de negocio con las siguientes características:
- Cada opción de menú se vincula a un BP mediante `ID_BP` en `M4RMN_OPTIONS`
- Un BP puede tener hasta 3 tareas auxiliares (`ID_BP_AUX_1`, `ID_BP_AUX_2`)
- Los BPs controlan la seguridad ACL junto con los roles de aplicación

### Arquitectura: BP → Presentación → Menú
La cadena completa de navegación en PeopleNet es:

```
M4RCH_T3S (canal) → M4RBP_DEF (Business Process) → M4RCH_TASK_PRESENTATION → M4RPT_PRESENTATION
                                                                                  ↓
M4RMN_OPTIONS (menú) ← ID_BP ←──────────────────────────────────────────────────
```

| Tabla | Relación |
|---|---|
| `M4RMN_OPTIONS.ID_BP` | Menú → BP |
| `M4RBP_DEF` | Catálogo de BPs |
| `M4RCH_TASK_PRESENTATION` | BP → Presentación |
| `M4RPT_PRESENTATION` | Catálogo de presentaciones |

### Case Module BUSINESS PROCESS
El módulo lógico `BUSINESS PROCESS` agrupa los siguientes objetos BDL:

| Objeto | Tabla Física | Descripción |
|---|---|---|
| `SBP_DEF` | `M4RBP_DEF` + `M4RBP_DEF1` | Catálogo de BPs (definición, nombres, seguridad) |
| `SBP__PAR_DINAMIC` | `M4RBP_PARAM_DEF` | Parámetros de BPs |
| `SBP_DEF` | `M4RBP_APPROLE` | Roles autorizados por BP |
| `SCH_TASK_PRESENTATION` | `M4RCH_TASK_PRESENTATION` | Relación BP → Presentación |

### Transporte RAMDL
Los Business Processes se transportan entre entornos mediante paquetes RAMDL:

| Objeto RAMDL | Versiones | Qué transporta |
|---|---|---|
| `BUSINESS PROCESS` | v60250+ | Definición de BPs (M4RBP_DEF, M4RBP_DEF1) |
| `SECURITY BP` | v60250+ | Seguridad de BPs (M4RBP_APPROLE) |
| `MAPPING PRESENTATION` | v60400+ | Relación BP ↔ Presentación (M4RCH_TASK_PRESENTATION) |

### Gotchas
- No todos los BPs tienen una presentación asociada. Usar `--with-presentation` para filtrar solo los que la tienen.
- La relación BP→Presentación está en la tabla `M4RCH_TASK_PRESENTATION`, que pertenece al objeto RAMDL del editor de canales (`SCH_*`), no al objeto `BUSINESS PROCESS`.
- El campo `ID_T3` en `M4RBP_DEF` indica el canal al que pertenece el BP, pero frecuentemente está vacío.

### Decodificación de Campos Numéricos

**SECURITY_TYPE** (tipo de seguridad del BP):

| Valor | Significado |
|---|---|
| 0 | Sin seguridad |
| 1 | Auditoría |
| 2 | Seguridad completa |

**STATE** (estado del BP):

| Valor | Significado |
|---|---|
| 0 | Activo |
| 1 | Inactivo/Deprecated |
| 2 | Obsoleto |

**OWNER_FLAG** (nivel de herencia):

| Valor | Significado |
|---|---|
| 1 | Standard |
| 2 | Estándar extendido |
| 10 | Corporate |
| 20 | Corporate extendido |
| 40-49 | Country (rango por país) |
| >50 | Custom |

**CODE_TYPE en M4RBP_EXE_CODE** (tipos de cliente):

| Valor | Significado |
|---|---|
| 1 | Cliente Windows |
| 2 | LN4 |
| 3 | Cliente Java |
| 4 | Cliente ligero |

### Flujo de Trabajo
1. Conecta a la BD de metadatos de PeopleNet.
2. Consulta M4RBP_DEF con JOIN a M4RBP_DEF1 (descripciones) y M4RCH_TASK_PRESENTATION.
3. Aplica filtros opcionales: búsqueda por texto, canal (ID_T3), o solo BPs con presentación.
4. Devuelve JSON con ID, nombres, seguridad, canal, estado y presentación asociada.

### Ejemplo de Uso
```bash
# Listar todos los BPs (hasta 200)
python -m tools.business_process.list_bp

# Buscar BPs por texto
python -m tools.business_process.list_bp --search "empleado"

# BPs de un canal específico
python -m tools.business_process.list_bp --t3 CRVE_PA_TR_PERSON

# Solo BPs con presentación asociada
python -m tools.business_process.list_bp --with-presentation
```

**Resultado esperado:**
```json
{
  "status": "success",
  "total": 15,
  "filters": {"search": "empleado", "t3": null, "with_presentation": false, "limit": 200},
  "business_processes": [
    {
      "id_bp": "HRM_EMPLOYEES_BP",
      "name_esp": "Gestión de empleados",
      "name_eng": "Employee management",
      "security_type": 2,
      "id_t3": "CRVE_PA_TR_PERSON",
      "state": 0,
      "owner_flag": 1,
      "id_approle": "HRM_MANAGER",
      "id_presentation": "CRVE_MT_TR_PERSON",
      "dt_last_update": "2025-01-15 10:30:00"
    }
  ]
}
```
