---
nombre: "describir_business_process"
version: "1.0.0"
descripcion: "Obtiene el detalle completo de un Business Process: definición, presentaciones, roles y menús asociados."
parametros:
  - nombre: "id_bp"
    tipo: "string"
    requerido: true
    descripcion: "Identificador del Business Process"
  - nombre: "include_menus"
    tipo: "boolean"
    requerido: false
    descripcion: "Incluir menús que usan este BP"
  - nombre: "include_roles"
    tipo: "boolean"
    requerido: false
    descripcion: "Incluir roles autorizados por este BP"
---

## Documentacion de la Skill: `describir_business_process`

### Proposito
Obtiene el detalle completo de un Business Process (BP) de PeopleNet, incluyendo: definición básica, descripciones extensas, presentaciones asociadas, roles autorizados, y menús que lo invocan.

### Datos Recuperados
| Sección | Tabla | Descripción |
|---|---|---|
| Definición | `M4RBP_DEF` | Nombres cortos, seguridad, canal, estado |
| Descripciones | `M4RBP_DEF1` | Descripciones largas multilingue |
| Presentaciones | `M4RCH_TASK_PRESENTATION` | Presentaciones vinculadas |
| Roles | `M4RBP_APPROLE` | Roles autorizados (con --include-roles) |
| Menús | `M4RMN_OPTIONS` | Opciones de menú que usan este BP (con --include-menus) |

### Campos Clave de M4RBP_DEF
- **ID_BP**: identificador único del Business Process
- **N_BP{ESP,ENG,...}**: nombre corto (7 idiomas)
- **DESC_BP{ESP,ENG,...}**: descripción larga (en M4RBP_DEF1)
- **SECURITY_TYPE**: tipo de seguridad (0=None, 1=Audit, 2=Full)
- **ID_T3**: canal (M4Object) asociado
- **SOC_DEPENDENT**: si depende de sociedad
- **STATE**: estado (0=Active, 1=Inactive, 2=Obsolete)
- **OWNER_FLAG**: nivel de herencia (Standard=1, Corporate=40-49, Country=rango específico por país)
- **ID_APPROLE**: rol de aplicación por defecto
- **ADMINISTRATIVE**: si es administrativo
- **CONCURRENCY_LEVEL**: nivel de concurrencia
- **SELF_RECOVER**: si se auto-recupera ante errores

### Decodificación de Campos Numéricos

**SECURITY_TYPE** (tipo de seguridad del BP):

| Valor | Significado | BPs con este valor |
|---|---|---|
| 0 | Sin seguridad | 2.722 |
| 1 | Auditoría | 3 |
| 2 | Seguridad completa | 1.262 |

**STATE** (estado del BP):

| Valor | Significado | BPs con este valor |
|---|---|---|
| 0 | Activo | 3.900 |
| 1 | Inactivo/Deprecated | 82 |
| 2 | Obsoleto | 5 |

**OWNER_FLAG** (nivel de herencia):

| Valor | Significado |
|---|---|
| 1 | Standard |
| 2 | Estándar extendido |
| 10 | Corporate |
| 20 | Corporate extendido |
| 40-49 | Country (rango por país) |
| >50 | Custom |

### Código Ejecutable (M4RBP_EXE_CODE)
Un BP puede tener código asociado según el tipo de cliente que lo ejecuta:

| CODE_TYPE | Significado |
|---|---|
| 1 | Cliente Windows |
| 2 | LN4 |
| 3 | Cliente Java |
| 4 | Cliente ligero |
| 5 | Otro |

El campo `RECOVERABLE` indica si el BP es recuperable ante errores.

### Subtareas (M4RBP_STRUCT)
Un BP puede estar compuesto por otros BPs como subtareas ( pasos ):
- **LOCAL_ID**: orden del paso en la secuencia
- **ID_SUBTASK**: BP que se ejecuta como paso
- **LOCAL_NAME/LOCAL_DESC**: nombre y descripción del paso

### Parámetros (M4RBP_PARAM_DEF)
Los BPs pueden tener parámetros de entrada/salida:
- **ID_TYPE**: tipo de dato del parámetro
- **SCOPE_TYPE**: ámbito (0=Input, 1=Output, 2=InputOutput)
- **PARAM_ORDINAL**: orden del parámetro
- **FLOW_TYPE**: tipo de flujo
- **TASK_SOURCE**: origen de la tarea

### Arquitectura de Seguridad: BP + Roles
La seguridad de un BP se controla en cascada:

| Tabla | Controla |
|---|---|
| `M4RBP_DEF.ID_APPROLE` | Rol de aplicación por defecto |
| `M4RBP_APPROLE.ID_APPROLE` | Roles adicionales autorizados |
| `M4RMN_OPTIONS.ID_BP` | Qué menús invocan este BP |
| `M4RBP_APPROLE.ID_APPROLE_BP` | Identificador del rol en el BP |

### Relación BP → Presentación
La relación entre un BP y su presentación se almacena en `M4RCH_TASK_PRESENTATION`:

| Campo | Descripción |
|---|---|
| ID_BP | Business Process |
| ID_PRESENTATION | Presentación asociada |
| ID_APPROLE | Rol requerido para esta presentación |
| DT_LAST_UPDATE | Fecha de última modificación |

Esta tabla pertenece al objeto RAMDL del editor de canales (`SCH_TASK_PRESENTATION`), no al objeto `BUSINESS PROCESS`.

### Transporte RAMDL
Los BPs se transportan entre entornos mediante:

| Objeto RAMDL | Versiones | Tablas |
|---|---|---|
| `BUSINESS PROCESS` | v60250+ | M4RBP_DEF, M4RBP_DEF1 |
| `SECURITY BP` | v60250+ | M4RBP_APPROLE |
| `MAPPING PRESENTATION` | v60400+ | M4RCH_TASK_PRESENTATION |

### Gotchas
- Un BP puede aparecer en hasta 3 campos de menú: `ID_BP`, `ID_BP_AUX_1`, `ID_BP_AUX_2`
- La presentación puede tener rol propio (`M4RCH_TASK_PRESENTATION.ID_APPROLE`) que puede diferir del rol del BP
- `M4RBP_ROLE_EXCEPT` gestiona excepciones de rol (pendiente de investigar)

### Flujo de Trabajo
1. Conecta a la BD de metadatos.
2. Consulta la definición en M4RBP_DEF.
3. Obtiene descripciones largas de M4RBP_DEF1.
4. Recupera presentaciones asociadas de M4RCH_TASK_PRESENTATION.
5. Opcionalmente lista roles autorizados (M4RBP_APPROLE).
6. Opcionalmente lista menús que invocan este BP (M4RMN_OPTIONS).

### Ejemplo de Uso
```bash
# Detalle básico
python -m tools.business_process.get_bp HRM_EMPLOYEES_BP

# Con menús que usan este BP
python -m tools.business_process.get_bp HRM_EMPLOYEES_BP --include-menus

# Con roles autorizados
python -m tools.business_process.get_bp HRM_EMPLOYEES_BP --include-roles
```

**Resultado esperado:**
```json
{
  "id_bp": "HRM_EMPLOYEES_BP",
  "names": {
    "esp": "Gestión de empleados",
    "eng": "Employee management"
  },
  "security_type": 2,
  "security_type_decoded": "Seguridad completa",
  "id_t3": "CRVE_PA_TR_PERSON",
  "soc_dependent": false,
  "state": 0,
  "state_decoded": "Activo",
  "owner_flag": 1,
  "owner_flag_decoded": "Standard",
  "id_approle": "HRM_MANAGER",
  "administrative": 0,
  "concurrency_level": 0,
  "self_recover": true,
  "dt_last_update": "2025-01-15 10:30:00",
  "descriptions": {
    "esp": "Permite gestionar el ciclo de vida completo del empleado.",
    "eng": "Manages the complete employee lifecycle."
  },
  "presentations": [
    {
      "id_presentation": "CRVE_MT_TR_PERSON",
      "id_approle": "HRM_MANAGER",
      "dt_last_update": "2025-01-15 10:30:00"
    }
  ],
  "client_code": [
    {
      "code_type": "Cliente Windows",
      "code_type_raw": 1,
      "recoverable": false,
      "dt_last_update": "2025-01-15 10:30:00"
    },
    {
      "code_type": "LN4",
      "code_type_raw": 2,
      "recoverable": true,
      "dt_last_update": "2025-01-15 10:30:00"
    }
  ],
  "subtasks": [
    {
      "local_id": 0,
      "id_subtask": "HRM_EMPLOYEES_INIT",
      "local_name": "HRM_EMPLOYEES_INIT",
      "local_desc": "Inicialización"
    },
    {
      "local_id": 1,
      "id_subtask": "HRM_EMPLOYEES_VALIDATE",
      "local_name": "HRM_EMPLOYEES_VALIDATE",
      "local_desc": "Validación de datos"
    }
  ],
  "parameters": [
    {
      "id_param": "P_ID_PERSON",
      "name_esp": "ID Persona",
      "id_type": 1,
      "scope_type": 0,
      "param_ordinal": 1,
      "flow_type": 1
    }
  ],
  "roles": [
    {
      "id_approle_bp": "HRM_MANAGER",
      "id_approle": "HRM_MANAGER"
    }
  ],
  "menus": [
    {
      "id_menu": "HRM_EMPLOYEES",
      "name_esp": "Empleados",
      "name_eng": "Employees",
      "id_approle": "HRM_MANAGER",
      "position": 1
    }
  ]
}
```
