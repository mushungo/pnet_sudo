---
nombre: "listar_presentaciones"
version: "1.0.0"
descripcion: "Lista las presentaciones registradas en PeopleNet con filtros por canal (T3), Business Process, tipo y texto libre."
parametros:
  - nombre: "search"
    tipo: "string"
    requerido: false
    descripcion: "Buscar en ID_PRESENTATION, descripción ESP o ENG"
  - nombre: "t3"
    tipo: "string"
    requerido: false
    descripcion: "Filtrar por canal (ID_T3) via M4RPT_PRES_STYLE"
  - nombre: "bp"
    tipo: "string"
    requerido: false
    descripcion: "Filtrar por Business Process via M4RCH_TASK_PRESENTATION"
  - nombre: "type"
    tipo: "integer"
    requerido: false
    descripcion: "Filtrar por PRESENTATION_TYPE (0=OBL, 1=DP, 2=Template, 3=QBF, 4=Include)"
  - nombre: "limit"
    tipo: "integer"
    requerido: false
    descripcion: "Máximo de resultados (default 200)"
---

## Documentacion de la Skill: `listar_presentaciones`

### Proposito
Lista las presentaciones de PeopleNet (catálogo `M4RPT_PRESENTATION`) con filtros opcionales por canal, Business Process, tipo y texto libre.

### Tablas Consultadas
| Tabla | Rol |
|---|---|
| `M4RPT_PRESENTATION` | Catálogo principal de presentaciones (3.202 filas en CAF) |
| `M4RPT_PRES_STYLE` | Relación presentación ↔ canal T3 (filtro `--t3`) |
| `M4RCH_TASK_PRESENTATION` | Relación BP ↔ presentación (filtro `--bp`) |

### Decodificación de PRESENTATION_TYPE
| Valor | Nombre | Descripción |
|---|---|---|
| 0 | OBL | Presentación estándar (pantalla normal, tipo más común ~90%) |
| 1 | DP | Data Provider — vinculada a canales de nómina/payroll |
| 2 | Template | Plantilla base reutilizable |
| 3 | QBF | Query By Form — lista dinámica de presentaciones |
| 4 | Include | Fragmento incluible dentro de otras presentaciones |

### Decodificación de OWNER_FLAG (por rangos)
| Rango | Significado |
|---|---|
| 0 | Sin propietario |
| 1 | Standard |
| 2 | Standard Extendido |
| 10-19 | Standard Premium |
| 20 | Corporate |
| 40-49 | Country |
| 50-99 | Client |
| >99 | Custom (localización específica) |

### Arquitectura: Cadena Menú → BP → Presentación
```
M4RMN_OPTIONS (menú)
    ↓ ID_BP
M4RBP_DEF (Business Process)
    ↓ ID_BP
M4RCH_TASK_PRESENTATION (375 filas en CAF)
    ↓ ID_PRESENTATION
M4RPT_PRESENTATION (3.202 filas)
    ↓ ID_PRESENTATION
M4RPT_PRES_STYLE (1.067 filas) — relación con canal T3
```

La tabla `M4RCH_TASK_PRESENTATION` pertenece al objeto lógico BDL **`SCH_TASK_PRESENTATION`** (familia `SCH_*`, editor de canales). Se transporta en RAMDL como objeto **`MAPPING PRESENTATION`** (disponible desde v60400+).

### Ejemplo de Uso
```bash
# Listar todas (primeras 200)
python -m tools.presentations.list_presentations

# Buscar por nombre
python -m tools.presentations.list_presentations --search "empleado"

# Ver presentaciones de un canal específico
python -m tools.presentations.list_presentations --t3 SCO_EMPLOYEE

# Ver presentaciones de un BP
python -m tools.presentations.list_presentations --bp BP_AUTH_IP

# Solo presentaciones tipo QBF (listas dinámicas)
python -m tools.presentations.list_presentations --type 3

# Includes del país Venezuela
python -m tools.presentations.list_presentations --type 4 --search "CRVE"
```

**Resultado esperado:**
```json
{
  "status": "success",
  "total": 1,
  "filters": {"bp": "BP_AUTH_IP", "type": null, "limit": 200},
  "presentations": [
    {
      "id_presentation": "SRTC_TK_MN_IP_AUTH_CFG",
      "description_esp": "Autorización de puestos client",
      "presentation_type": "0",
      "presentation_type_name": "OBL",
      "owner_flag": "1",
      "owner_flag_name": "Standard",
      "read_only": false,
      "is_modified": true
    }
  ]
}
```

### Ver también
- `describir_presentacion` — detalle completo de una presentación (canales, BPs, herencia)
- `describir_business_process` — detalle de un BP (incluye sus presentaciones)
- `describir_menu` → `--include-bp` — cadena completa menú → BP → presentación
