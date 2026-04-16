---
nombre: "rastrear_concepto_en_recibo"
version: "1.0.0"
descripcion: "Ingeniería inversa bottom-up: dado un concepto de nómina conocido, encuentra en qué recibos/filas aparece, qué nodo lo calcula y qué ítem LN4 lo alimenta."
parametros:
  - nombre: "id_concepto"
    tipo: "string"
    descripcion: "ID del concepto de nómina a rastrear (ej. 'ID_CONCEPTO', 'TEXTO_BUSQUEDA'). Se usa como patrón LIKE en la búsqueda."
    requerido: true
  - nombre: "id_report"
    tipo: "string"
    descripcion: "Limitar la búsqueda a un informe específico (SCO_ID_REPORT). Si se omite, se busca en todos los informes."
    requerido: false
---

## Documentación de la Skill: `rastrear_concepto_en_recibo`

### Propósito

Realiza ingeniería inversa **bottom-up** del recibo de nómina: partiendo de un concepto conocido
(o parte de su nombre), localiza todas sus apariciones en el recibo y remonta la cadena hasta
el canal de cálculo y el ítem LN4 que lo alimenta.

```
Concepto conocido (ej. "TEXTO_BUSQUEDA")
  └─ ¿En qué filas del recibo aparece?   (M4SCO_ROWS: ID_PAYROLL_ITEM / SCO_ID_NODE)
       └─ ¿En qué celdas?                (M4SCO_ROW_COL_DEF: SCO_ID_NODE / SCO_ID_ITEM)
            └─ ¿Qué canal lo calcula?    (M4RCH_T3S via ID_T3_PI)
                 └─ ¿Qué ítem LN4?       (M4RCH_ITEMS via SCO_ID_ITEM)
                      └─ ¿Existe en M4RCH_PAYROLL_ITEM? (verificación cruzada)
```

Permite responder: **"¿En qué parte del recibo aparece este concepto y cómo se calcula?"**

---

### Flujo de Trabajo

#### Paso 1 — Buscar el concepto en las filas del recibo

Buscar en `M4SCO_ROWS` por nombre de fila, `ID_PAYROLL_ITEM`, `ID_T3_PI` o `SCO_ID_NODE`:

```bash
# Búsqueda global en todos los informes
python -m tools.nomina.get_payslip_layout --list-rows --search "<ID_CONCEPTO>"

# Búsqueda acotada a un informe específico
python -m tools.nomina.get_payslip_layout --list-rows --report "<SCO_ID_REPORT>" --search "<ID_CONCEPTO>"
```

**Interpretar el resultado:**

| Caso | Qué significa |
|---|---|
| `id_payroll_item` contiene el término | El concepto es el acumulado que imprime esa fila |
| `sco_id_node` contiene el término | El concepto es el nodo de cálculo vinculado a esa fila |
| `id_t3_pi` contiene el término | El canal completo está asociado a esa fila |
| `sco_nm_rowesp` contiene el término | Coincidencia por etiqueta descriptiva (puede ser indirecta) |

---

#### Paso 2 — Buscar el concepto en las celdas del recibo

Buscar en `M4SCO_ROW_COL_DEF` para encontrar en qué columnas y celdas aparece el nodo/ítem:

```bash
# Requiere conocer el informe y cuerpo (obtenidos en Paso 1)
python -m tools.nomina.get_payslip_layout --list-cells \
  --report "<SCO_ID_REPORT>" \
  --body "<SCO_ID_BODY>" \
  --search "<ID_CONCEPTO>"
```

**Columnas clave a observar:**

| Campo | Significado |
|---|---|
| `sco_id_node` | Nodo del canal que produce el valor impreso |
| `sco_id_item` | Ítem LN4 del nodo cuyo valor se muestra |
| `sfr_id_source_node` / `sfr_id_source_item` | Fuente alternativa (acumulado de otro nodo) |
| `sco_id_row` | Fila en la que aparece esta celda |
| `sco_id_column` | Columna del recibo (ej. "importe", "días", "etiqueta") |

Si el concepto aparece en `sco_id_item` o `sfr_id_source_item`, es el **valor final impreso**.
Si aparece en `sco_id_node` o `sfr_id_source_node`, es el **nodo calculador**.

---

#### Paso 3 — Verificar en M4RCH_PAYROLL_ITEM

Confirmar que el concepto existe formalmente como payroll item y obtener su definición:

```bash
# Búsqueda por texto en ID_ITEM, ID_CONCEPT e ID_TI
python -m tools.m4object.get_payroll_item --search "<ID_CONCEPTO>"

# Detalle completo si ya se conoce el TI y el item
python -m tools.m4object.get_payroll_item --ti "<ID_T3_PI>" --item "<ID_PAYROLL_ITEM>"
```

Confirmar:
- `id_concept`: concepto acumulado registrado
- `id_ti`: canal de nómina propietario
- Tipo de ítem (calculado, acumulado, constante)

---

#### Paso 4 — Describir el canal de cálculo

Con el `ID_T3_PI` encontrado en los pasos anteriores, obtener la definición completa del canal:

```bash
# Vista general del canal (items, conceptos M4RCH_CONCEPTS)
python -m tools.m4object.get_m4object --ti "<ID_T3_PI>"

# Con código fuente LN4 de los nodos
python -m tools.m4object.get_m4object --ti "<ID_T3_PI>" --include-rules
```

Esto proporciona:
- Lista de items del canal (`M4RCH_ITEMS`) con sus tipos
- Firmas de métodos (`M4RCH_ITEM_ARGS`)
- Código LN4 de los nodos relevantes (`M4RCH_RULES3`)
- Conceptos de nómina del TI (`M4RCH_CONCEPTS`)

---

#### Paso 5 (opcional) — Verificación de integridad cruzada

Si se necesita confirmar que el concepto está correctamente implementado en todos sus componentes
(FIELDs, ITEMs, PAYROLL ITEM, tablas físicas, CCT), usar la skill complementaria:

```
usar_skill('verificar_concepto_nomina', { "id_concepto": "<ID_CONCEPTO>", "cct_task_id": "<OPCIONAL>" })
```

---

### Tabla resumen: salida esperada del análisis completo

Al ejecutar los pasos, construir una tabla de esta forma:

| Informe | Cuerpo | Fila | Etiqueta fila | Columna | Nodo cálculo | Ítem LN4 | Fuente altern. | En PAYROLL_ITEM |
|---|---|---|---|---|---|---|---|---|
| ID_REPORT | ID_BODY | N | Etiqueta concepto | IMPORTE | ID_NODO_CALC | ID_ITEM_LN4 | — | Sí |
| ID_REPORT | ID_BODY | M | Etiqueta total | ACUM | ID_NODO_CALC | ID_ITEM_LN4 | ID_NODO_HIST | Sí |

---

### Ejemplos de uso completo

**Caso típico — Rastrear un concepto en todos los recibos:**

```bash
# Paso 1: encontrar filas donde aparece el concepto
python -m tools.nomina.get_payslip_layout --list-rows --search "<TEXTO_BUSQUEDA>"

# Paso 2: celdas en el cuerpo encontrado
python -m tools.nomina.get_payslip_layout --list-cells \
  --report "<SCO_ID_REPORT>" --body "<SCO_ID_BODY>" --search "<TEXTO_BUSQUEDA>"

# Paso 3: verificar en payroll items
python -m tools.m4object.get_payroll_item --search "<TEXTO_BUSQUEDA>"

# Paso 4: describir el canal de cálculo
python -m tools.m4object.get_m4object --ti "<ID_T3_PI>" --include-rules
```

**Caso con búsqueda amplia (variantes del término):**

```bash
# Probar variantes si el término inicial no da resultados
python -m tools.nomina.get_payslip_layout --list-rows --search "<VARIANTE_1>"
python -m tools.nomina.get_payslip_layout --list-rows --search "<VARIANTE_2>"
python -m tools.nomina.get_payslip_layout --list-rows --search "<VARIANTE_3>"
```

---

### Criterios de éxito

El rastreo es completo cuando se puede responder:

1. **¿En qué fila(s) del recibo aparece el concepto?** → `SCO_ID_ROW` + etiqueta
2. **¿Es un concepto acumulado o de cálculo?** → tipo de ítem en `M4RCH_PAYROLL_ITEM`
3. **¿Qué canal (T3) lo gestiona?** → `ID_T3_PI`
4. **¿Qué nodo e ítem LN4 producen el valor impreso?** → `SCO_ID_NODE` + `SCO_ID_ITEM`
5. **¿Existe formalmente en `M4RCH_PAYROLL_ITEM`?** → confirmación de integridad

---

### Relación con otras herramientas

| Skill / Tool | Relación |
|---|---|
| `describir_salida_papel` | Documenta las tablas M4SCO_* y el modelo de datos base |
| `identificar_items_recibo` | Dirección opuesta: del recibo hacia los conceptos (top-down) |
| `describir_payroll_item` | Detalla el concepto acumulado encontrado en el Paso 3 |
| `describir_m4object` | Describe el canal de nómina (`ID_T3_PI`) encontrado en el Paso 4 |
| `verificar_concepto_nomina` | Verificación de integridad cruzada del concepto (BD + CCT) |
