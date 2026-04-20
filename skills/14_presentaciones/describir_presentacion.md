---
nombre: "describir_presentacion"
version: "1.0.0"
descripcion: "Obtiene el detalle completo de una presentación de PeopleNet: definición, herencia, canales (T3) y Business Processes vinculados."
parametros:
  - nombre: "id_presentation"
    tipo: "string"
    requerido: true
    descripcion: "Identificador de la presentación (ej: SRTC_TK_MN_IP_AUTH_CFG)"
  - nombre: "include_channels"
    tipo: "boolean"
    requerido: false
    descripcion: "Incluir canales (T3) que usan esta presentación"
  - nombre: "include_bps"
    tipo: "boolean"
    requerido: false
    descripcion: "Incluir Business Processes vinculados"
---

## Documentacion de la Skill: `describir_presentacion`

### Proposito
Obtiene el detalle completo de una presentación de PeopleNet, incluyendo: definición multilingue, tipo, herencia de presentación base, canales (T3) que la utilizan con su estilo de visualización, y Business Processes vinculados.

### Datos Recuperados
| Sección | Tabla | Descripción |
|---|---|---|
| Definición | `M4RPT_PRESENTATION` | Descripciones 7 idiomas, tipo, owner, flags |
| Herencia | `M4RPT_PRES_INHERIT` | Presentación base de la que hereda |
| Canales | `M4RPT_PRES_STYLE` | T3s que usan esta presentación (con --include-channels) |
| BPs | `M4RCH_TASK_PRESENTATION` + `M4RBP_DEF` | BPs vinculados (con --include-bps) |

### Campos Clave de M4RPT_PRESENTATION
- **ID_PRESENTATION**: identificador lógico único (varchar 40)
- **DESCRIPTION{ESP,ENG,...}**: descripción en 7 idiomas (varchar 30 — campo corto)
- **PRESENTATION_TYPE**: tipo de presentación (ver decodificación)
- **OWNER_FLAG**: nivel de herencia (por rangos, igual que BPs y menús)
- **READ_ONLY**: si la presentación está bloqueada para edición
- **IS_MODIFIED**: si ha sido modificada localmente
- **BLOCKROBOT**: excluida de la indexación por robot de búsqueda
- **ID_ORG_TYPE**: tipo de organización (filtro de visibilidad)
- **DT_CREATE**: fecha de creación
- **DT_LAST_UPDATE**: última modificación

### Decodificación de PRESENTATION_TYPE
| Valor | Nombre | Descripción | Ejemplo |
|---|---|---|---|
| 0 | OBL | Presentación de pantalla estándar (~90% del catálogo) | `SCO_EMPLOYEE`, `SRTC_TK_MN_IP_AUTH_CFG` |
| 1 | DP | Data Provider — canal de nómina | `SCO_DP_PAYROLL_CHANNEL` |
| 2 | Template | Plantilla base reutilizable | `Master_Template`, `SRTC_PARAM_TEMPLATE` |
| 3 | QBF | Query By Form (lista dinámica de presentaciones) | `M.QBF.PRESENTATION_LIST` |
| 4 | Include | Fragmento incluible en otras presentaciones | `CRVE_INCL_COUNTRY` |

### Decodificación de PRESENTATION_STYLE (M4RPT_PRES_STYLE)
Cuando una presentación se vincula a un canal T3, puede tener un estilo de visualización:
| Valor | Nombre | Uso |
|---|---|---|
| 10 | Normal | Interfaz clásica |
| 11 | Light | Interfaz ligera / modo compacto |
| 12 | Responsive | Interfaz adaptativa (PNet 8+) |

### Herencia de Presentaciones
`M4RPT_PRES_INHERIT` (3.455 filas) registra la jerarquía de herencia entre presentaciones. Cada presentación puede heredar de una base (nivel 1 = herencia directa). La consulta recupera solo el nivel 1.

### Convenciones de Nomenclatura
Los prefijos del ID de presentación indican el módulo y tipo:
| Prefijo | Módulo | Ejemplo |
|---|---|---|
| `SCO_` | Core / SSFF (Standard Corporate) | `SCO_EMPLOYEE` |
| `SRCO_` | Standard Corporate Objects | `SRCO_PA_MT_HR_TYPE` |
| `SRTC_` | Standard Training/Configuration | `SRTC_TK_MN_IP_AUTH_CFG` |
| `CRVE_` | Country Venezuela | `CRVE_MT_NIVEL_SALARI` |
| `CRCO_` | Country Colombia | `CRCO_TR_HR_LOG_EMAIL_TRAB` |
| `CCO_` | Client Corporate Objects | `CCO_MONTHLY_PAY` |
| `QBF.` | Query By Form (tipo 3) | `QBF.CRVE_MT_DOCUM_LIST` |

### Transporte RAMDL
| Objeto RAMDL | Qué transporta |
|---|---|
| `PRESENTATION` | Definición de la presentación (objeto principal) |
| `MAPPING PRESENTATION` | Relación BP ↔ Presentación (`M4RCH_TASK_PRESENTATION`) — desde v60400+ |

### Tablas Relacionadas Adicionales
| Tabla | Descripción | Filas (CAF) |
|---|---|---|
| `M4RPT_DOCU_PRES` | Inventario de items y canales incluidos en la presentación | 103.294 |
| `M4RPT_PRES_INHERIT` | Árbol de herencia entre presentaciones | 3.455 |
| `M4RPT_PRES_STYLE` | Estilo de visualización por T3 | 1.067 |
| `M4RCH_TASK_PRESENTATION` | Relación BP ↔ Presentación | 375 |
| `M4RCH_PRES_MENU` | Relación Presentación ↔ Menú (vacía en CAF) | 0 |
| `SPR_DIN_PRESENTS` | Presentaciones dinámicas (herencia por país) | 78 |

### Ejemplo de Uso
```bash
# Definición básica
python -m tools.presentations.get_presentation SRTC_TK_MN_IP_AUTH_CFG

# Con canales que usan la presentación
python -m tools.presentations.get_presentation SRTC_TK_MN_IP_AUTH_CFG --include-channels

# Con BPs vinculados
python -m tools.presentations.get_presentation SRTC_TK_MN_IP_AUTH_CFG --include-bps

# Completo
python -m tools.presentations.get_presentation SRTC_TK_MN_IP_AUTH_CFG --include-channels --include-bps
```

**Resultado esperado (completo):**
```json
{
  "id_presentation": "SRTC_TK_MN_IP_AUTH_CFG",
  "descriptions": {
    "esp": "Autorización de puestos client",
    "eng": "Autorización de puestos client"
  },
  "presentation_type": "0",
  "presentation_type_name": "OBL",
  "owner_flag": "1",
  "owner_flag_name": "Standard",
  "read_only": false,
  "is_modified": true,
  "base_presentation": null,
  "inherited_by_count": 0,
  "channels": [
    {
      "id_t3": "SRTC_TK_MN_IP_AUTH_CFG",
      "name_esp": "Autorización de puestos cliente",
      "presentation_style": "12",
      "presentation_style_name": "Responsive"
    }
  ],
  "channels_count": 1,
  "business_processes": [
    {
      "id_bp": "BP_AUTH_IP",
      "name_esp": "Autorización de puestos cliente",
      "name_eng": "Client Workstation Authorization",
      "id_t3": null,
      "id_approle": "M4ADM"
    },
    {
      "id_bp": "BP_AUTH_IP_PLTF",
      "name_esp": "Autorización de puestos cliente (grupo usuarios)",
      "name_eng": "Client Workstation Authorization (User Group)",
      "id_t3": null,
      "id_approle": "M4DEVELOPER"
    }
  ],
  "business_processes_count": 2
}
```

### Ver también
- `listar_presentaciones` — buscar y filtrar el catálogo de presentaciones
- `describir_business_process` — detalle de un BP incluyendo sus presentaciones
- `describir_menu` → `--include-bp` — cadena completa menú → BP → presentación
