---
nombre: "identificar_items_recibo"
version: "1.0.0"
descripcion: "Recorre la cadena completa del recibo de nómina (salida a papel) hacia los conceptos de cálculo: recibo → filas → conceptos acumulados → canal de nómina → nodo/ítem LN4."
parametros:
  - nombre: "id_report"
    tipo: "string"
    descripcion: "ID del informe/recibo (SCO_ID_REPORT). Si no se conoce, ejecutar primero el Paso 1 para descubrirlo."
    requerido: false
  - nombre: "id_body"
    tipo: "string"
    descripcion: "ID del cuerpo/sección del recibo (SCO_ID_BODY). Opcional: si se omite se devuelven todas las secciones del informe."
    requerido: false
  - nombre: "search"
    tipo: "string"
    descripcion: "Texto libre para filtrar filas por nombre de fila, ID de concepto o nodo (ej. 'JUBIL', 'SUELDO', 'BIENESTAR')."
    requerido: false
---

## Documentación de la Skill: `identificar_items_recibo`

### Propósito

Traza la cadena completa **top-down** del recibo de nómina:

```
Recibo (SCO_ID_REPORT)
  └─ Cuerpo (SCO_ID_BODY)
       └─ Fila (M4SCO_ROWS)            ← concepto acumulado (ID_PAYROLL_ITEM, ID_T3_PI)
            └─ Celda (M4SCO_ROW_COL_DEF) ← concepto de cálculo (SCO_ID_NODE, SCO_ID_ITEM)
                 └─ Canal/Nodo (M4RCH_T3S / M4RCH_NODES)  ← lógica LN4
```

Permite responder: **"¿Qué conceptos de cálculo alimentan cada línea del recibo de salarios?"**

---

### Flujo de Trabajo

#### Paso 1 — Descubrir los informes/recibos disponibles

Si no se conoce el `SCO_ID_REPORT`, listar todos los informes configurados:

```bash
python -m tools.nomina.get_payslip_layout --list-reports
```

Identificar el informe de interés por su nombre o ID (p. ej. `RECIBO_NOMINA`, `PAYSLIP_VEN`).

---

#### Paso 2 — Listar todas las filas del recibo

Con el `SCO_ID_REPORT` identificado, obtener todas las filas con sus conceptos vinculados:

```bash
python -m tools.nomina.get_payslip_layout --list-rows --report "<SCO_ID_REPORT>"
```

Opcionalmente filtrar por texto para localizar un área específica:

```bash
python -m tools.nomina.get_payslip_layout --list-rows --report "<SCO_ID_REPORT>" --search "<TEXTO>"
```

**Columnas clave del resultado:**

| Campo | Significado |
|---|---|
| `sco_id_row` | Número de fila |
| `sco_nm_rowesp` / `sco_nm_roweng` | Etiqueta visible en el recibo |
| `id_payroll_item` | Concepto acumulado → enlaza con `M4RCH_PAYROLL_ITEM` |
| `id_t3_pi` | Canal/TI de nómina que contiene el concepto (M4Object) |
| `sco_id_node` | Nodo de cálculo del canal |
| `sco_id_body` | Sección del recibo donde aparece la fila |
| `sco_order` | Orden de aparición en la sección |

---

#### Paso 3 — Detallar el concepto acumulado (payroll item)

Para cada fila con `id_payroll_item` relevante, obtener su definición completa:

```bash
python -m tools.m4object.get_payroll_item --ti "<id_t3_pi>" --item "<id_payroll_item>"
```

Esto devuelve el concepto desde `M4RCH_PAYROLL_ITEM` enriquecido con `M4RCH_ITEMS`:
- Tipo de ítem (cálculo, acumulado, constante)
- Nombre en español/inglés
- Campo BDL de lectura asociado

---

#### Paso 4 — Obtener las celdas (conceptos de cálculo por columna)

Para cada fila de interés, obtener qué valor se imprime en cada columna:

```bash
python -m tools.nomina.get_payslip_layout --row \
  --report "<SCO_ID_REPORT>" \
  --body "<SCO_ID_BODY>" \
  --row-id <SCO_ID_ROW>
```

O listar todas las celdas de un cuerpo completo:

```bash
python -m tools.nomina.get_payslip_layout --list-cells \
  --report "<SCO_ID_REPORT>" \
  --body "<SCO_ID_BODY>"
```

**Columnas clave del resultado (M4SCO_ROW_COL_DEF):**

| Campo | Significado |
|---|---|
| `sco_id_node` | Nodo del canal que calcula el valor de la celda |
| `sco_id_item` | Ítem LN4 del nodo cuyo valor se imprime |
| `sfr_id_source_node` / `sfr_id_source_item` | Nodo/ítem fuente alternativo (p. ej. acumulado histórico) |
| `sco_labelesp` / `sco_labeleng` | Etiqueta de la columna para esa celda |
| `sco_constant` | Valor constante fijo (sin nodo/ítem) |
| `sco_cancel_row` | Si esta celda puede anular la fila entera |

---

#### Paso 5 — Describir el canal/nodo de cálculo

Con el `id_t3_pi` (canal) y el `sco_id_node` (nodo), describir la lógica LN4:

```bash
python -m tools.m4object.get_m4object --ti "<id_t3_pi>"
```

Para incluir el código fuente LN4 del nodo:

```bash
python -m tools.m4object.get_m4object --ti "<id_t3_pi>" --include-rules
```

Esto revela:
- Qué items del canal se usan (M4RCH_ITEMS, M4RCH_ITEM_ARGS)
- La lógica de cálculo en LN4 (M4RCH_RULES3)
- Los conceptos de nómina del TI (M4RCH_CONCEPTS)

---

### Tabla resumen: salida esperada del análisis completo

Al ejecutar los 5 pasos, el agente debe construir una tabla de esta forma:

| Fila recibo | Etiqueta | ID_PAYROLL_ITEM | Canal (T3) | Nodo cálculo | Ítem LN4 | Tipo |
|---|---|---|---|---|---|---|
| 10 | Sueldo base | CVE_SUELDO_BASE | CVE_DP_PAYROLL | CALC_SUELDO | CVE_SUELDO | Acumulado |
| 20 | Plan Jubilación | CVE_PLAN_JUBIL | CVE_DP_JUBIL | CALC_JUBIL | CVE_APORT_JUBIL | Cálculo |
| ... | ... | ... | ... | ... | ... | ... |

---

### Ejemplos de uso completo

**Caso 1 — Identificar todos los items de un recibo:**
```bash
# Paso 1: descubrir informes
python -m tools.nomina.get_payslip_layout --list-reports

# Paso 2: filas del recibo con sus conceptos
python -m tools.nomina.get_payslip_layout --list-rows --report "RECIBO_NOMINA"

# Paso 3: detalle del concepto acumulado de la fila 20
python -m tools.m4object.get_payroll_item --ti "CVE_DP_PAYROLL" --item "CVE_PLAN_JUBIL"

# Paso 4: celdas de la fila 20 (nodo/ítem de cálculo)
python -m tools.nomina.get_payslip_layout --row --report "RECIBO_NOMINA" --body "CUERPO_PPAL" --row-id 20

# Paso 5: canal de cálculo completo
python -m tools.m4object.get_m4object --ti "CVE_DP_JUBIL" --include-rules
```

**Caso 2 — Búsqueda directa por concepto en el recibo:**
```bash
# Buscar filas que incluyan "JUBIL" en nombre o concepto
python -m tools.nomina.get_payslip_layout --list-rows --report "RECIBO_NOMINA" --search "JUBIL"

# Buscar celdas en todo un cuerpo que mencionen "JUBIL"
python -m tools.nomina.get_payslip_layout --list-cells --report "RECIBO_NOMINA" --body "CUERPO_PPAL" --search "JUBIL"
```

---

### Relación con otras herramientas

| Skill / Tool | Relación |
|---|---|
| `describir_salida_papel` | Documenta las tablas M4SCO_* y el modelo de datos base |
| `describir_payroll_item` | Detalla el concepto acumulado (`ID_PAYROLL_ITEM`) encontrado en el Paso 3 |
| `describir_m4object` | Describe el canal de nómina (`ID_T3_PI`) encontrado en el Paso 2 |
| `rastrear_concepto_en_recibo` | Dirección inversa: dado un concepto, encuentra en qué recibos aparece |
| `verificar_concepto_nomina` | Verificación de integridad cruzada de un concepto (BD + CCT) |
