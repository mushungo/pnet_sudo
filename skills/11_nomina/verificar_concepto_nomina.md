---
# Metadata estructurada de la Skill
nombre: "verificar_concepto_nomina"
version: "2.0.0"
descripcion: "Verifica si un concepto de nómina (o sus ajustes) tiene todos sus componentes estándar creados en BD y registrados en una CCT."
parametros:
  - nombre: "id_concepto"
    tipo: "string"
    descripcion: "El ID del concepto de nómina principal o de sus ajustes. Ej: ID_CONCEPTO, ID_AJ_CONCEPTO_A."
    requerido: true
  - nombre: "cct_task_id"
    tipo: "string"
    descripcion: "Opcional. El ID del Control de Cambio (CCT_TASK_ID) donde debería estar registrado el concepto. Ej: CCT_TASK_ID."
    requerido: false
---

## Documentación de la Skill: `verificar_concepto_nomina`

### Propósito
Esta skill orquesta la verificación de la integridad de un concepto de nómina de PeopleNet usando las tools existentes del proyecto. Asegura que todos los elementos necesarios (FIELDs, ITEMs, PAYROLL ITEM, columnas físicas, PRESENTATION asociada, etc.) estén creados en la base de datos y, opcionalmente, correctamente registrados en un Control de Cambio (CCT).

> No existe una tool monolítica para este flujo. Se ejecuta como una secuencia de llamadas a tools independientes ya disponibles.

### Arquitectura estándar de un concepto de nómina

Un concepto de nómina en PeopleNet sigue este patrón estructural estándar:

| Componente | Tabla de metadatos | Descripción |
|---|---|---|
| FIELD | `M4RDC_FIELDS` | Campo en el objeto BDL de acumulado de período |
| FIELD | `M4RDC_FIELDS` | Campo en el objeto BDL de acumulado semestral/anual (si aplica) |
| ITEM | `M4RCH_ITEMS` | Item en el TI auxiliar de acumulación |
| ITEM | `M4RCH_ITEMS` | Item en el TI de cálculo principal |
| PAYROLL ITEM | `M4RCH_PAYROLL_ITEM` | Registro formal del concepto en el canal de nómina |
| PHYSICAL SCRIPT | `INFORMATION_SCHEMA.COLUMNS` | Columna física en las tablas SQL de acumulado |
| PRESENTATION | `M4RCH_T3S` | Canal de nómina propietario del concepto |

Los conceptos de ajuste siguen el mismo patrón con un sufijo convencional (ej. `_A` para abono, `_D` para débito).

### Flujo de Trabajo

#### Paso 1 — Verificar el PAYROLL ITEM

Confirmar que el concepto existe formalmente en `M4RCH_PAYROLL_ITEM`:

```bash
python -m tools.m4object.get_payroll_item --ti "<ID_TI_PAYROLL>" --item "<ID_CONCEPTO>"
# O por búsqueda de texto si no se conoce el TI exacto:
python -m tools.m4object.get_payroll_item --search "<ID_CONCEPTO>"
```

Verificar:
- Que el registro existe en `M4RCH_PAYROLL_ITEM`
- El `ID_TI` propietario del concepto
- El tipo de ítem (calculado, acumulado, constante)

---

#### Paso 2 — Verificar los ITEMs en los TIs de cálculo y acumulación

Con el `ID_TI` obtenido en el paso anterior, inspeccionar los TIs relacionados:

```bash
# Canal de nómina principal
python -m tools.m4object.get_m4object --ti "<ID_TI_CALCULO>"

# Canal auxiliar de acumulación (si existe)
python -m tools.m4object.get_m4object --ti "<ID_TI_AUX_ACUM>"
```

Verificar que el item del concepto (y sus ajustes si aplica) existe en `M4RCH_ITEMS` con sus parámetros correctos.

---

#### Paso 3 — Verificar los FIELDs en los objetos BDL de acumulado

Identificar el objeto BDL de acumulado donde escribe el concepto (campo `ID_WRITE_OBJECT` en `M4RCH_ITEMS`) y verificar que los campos existen:

```bash
python -m tools.bdl.get_bdl_object <ID_OBJETO_ACUMULADO>
```

Ver skill `verificar_acumulacion_concepto` para obtener el `ID_WRITE_OBJECT` del concepto.

---

#### Paso 4 — Verificar las columnas físicas (PHYSICAL SCRIPT)

Confirmar que las columnas físicas asociadas existen en las tablas SQL:

```bash
python -m tools.bdl.get_real_object <ID_TABLA_FISICA_ACUMULADO>
```

O directamente con la tool de schema BDL→físico:

```bash
python -m tools.m4object.get_ti_bdl_schema --ti "<ID_TI_CALCULO>"
```

---

#### Paso 5 (opcional) — Verificar registro en CCT

Si se especifica un `cct_task_id`, auditar que todos los objetos del concepto están registrados en el Control de Cambio:

```bash
python -m tools.cct.audit_cct "<CCT_TASK_ID>" --user <ID_SECUSER>
# O por rango de fechas:
python -m tools.cct.audit_cct "<CCT_TASK_ID>" --from <YYYY-MM-DD>
```

Ver skill `auditar_cct` para interpretar el informe de gaps.

---

#### Paso 6 — Generar informe de integridad

Al completar los pasos, construir una tabla resumen por concepto (principal + ajustes):

| Componente | Existe en BD | En CCT | Observaciones |
|---|---|---|---|
| FIELD en acumulado período | ✅ / ❌ | ✅ / ❌ / N/A | |
| FIELD en acumulado semestral | ✅ / ❌ | ✅ / ❌ / N/A | |
| ITEM en TI auxiliar | ✅ / ❌ | ✅ / ❌ / N/A | |
| ITEM en TI de cálculo | ✅ / ❌ | ✅ / ❌ / N/A | |
| PAYROLL ITEM | ✅ / ❌ | ✅ / ❌ / N/A | |
| Columna física tabla acumulado | ✅ / ❌ | ✅ / ❌ / N/A | |

### Relaciones con otras skills

- **`verificar_acumulacion_concepto`** — Obtiene el `ID_WRITE_OBJECT` del concepto (paso 3).
- **`describir_payroll_item`** — Detalla el registro en `M4RCH_PAYROLL_ITEM` (paso 1).
- **`describir_m4object`** — Describe el canal de nómina y sus items (paso 2).
- **`describir_ti_bdl_schema`** — Traza TI → BDL → tablas físicas (paso 4).
- **`auditar_cct`** — Verifica registro en CCT (paso 5).
- **`rastrear_concepto_en_recibo`** — Complemento: verifica si el concepto tiene representación en el recibo de nómina.
