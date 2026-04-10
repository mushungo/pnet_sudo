---
# Metadata estructurada de la Skill
nombre: "verificar_concepto_nomina"
version: "1.0.0"
descripcion: "Verifica si un concepto de nómina (o sus ajustes) tiene todos sus componentes estándar creados en BD y registrados en una CCT."
parametros:
  - nombre: "id_concepto"
    tipo: "string"
    descripcion: "El ID del concepto de nómina principal o de sus ajustes. Ej: CVE_CUENTA_BIENESTAR, CVE_AJ_CUENTA_BIENESTAR_A."
    requerido: true
  - nombre: "cct_task_id"
    tipo: "string"
    descripcion: "Opcional. El ID del Control de Cambio (CCT_TASK_ID) donde debería estar registrado el concepto. Ej: CONTROL_CAMBIO_258_2026."
    requerido: false
---

## Documentación de la Skill: `verificar_concepto_nomina`

### Propósito
Esta skill automatiza la verificación de la integridad de un concepto de nómina de PeopleNet. Asegura que todos los elementos necesarios (FIELDs, ITEMs, PAYROLL ITEM, PHYSICAL SCRIPT, PRESENTATION asociada, etc.) estén creados en la base de datos y, opcionalmente, correctamente registrados en un Control de Cambio (CCT).

### Flujo de Trabajo
La skill consultará las tablas de metadatos de PeopleNet (`M4RDC_FIELDS`, `M4RCH_ITEMS`, `M4RCH_PAYROLL_ITEM`, `INFORMATION_SCHEMA.COLUMNS`, `M4RCT_OBJECTS`, etc.) para:

1.  **Identificar conceptos relacionados**: Si se proporciona un concepto principal (ej. `CVE_CUENTA_BIENESTAR`), también se verificarán sus conceptos de ajuste (`CVE_AJ_CUENTA_BIENESTAR_A`, `CVE_AJ_CUENTA_BIENESTAR_D`).
2.  **Verificar existencia en BD**: Para cada concepto (principal y ajustes), comprobará:
    *   **FIELDs**: En `CVE_AC_HR_PERIOD` y `CVE_SM_AC_HR_PERIOD` (en `M4RDC_FIELDS`).
    *   **ITEMs**: En `CVE_AUX_AC_HRPERIOD` y `CVE_HRPERIOD_CALC` (en `M4RCH_ITEMS`).
    *   **PAYROLL ITEM**: En `CVE_DP_PAYROLL_CHANNEL` (en `M4RCH_PAYROLL_ITEM`).
    *   **PHYSICAL SCRIPT**: Confirmará que las columnas correspondientes existen en las tablas físicas `M4CVE_AC_HR_PERIOD` y `M4CVE_SM_AC_HR_PER`.
    *   **PRESENTATION**: Verificará la existencia del T3 `CVE_DP_PAYROLL_CHANNEL`.
3.  **Verificar registro en CCT (si se proporciona)**: Si se especifica un `cct_task_id`, la skill consultará `M4RCT_OBJECTS` para confirmar que todos los objetos del concepto (FIELDs, ITEMs, PAYROLL ITEM, PHYSICAL SCRIPT, y la entrada de MODIFIED de la PRESENTATION) están correctamente registrados en el Control de Cambio.
4.  **Generar un informe**: Se presentará un informe por cada concepto, detallando el estado de cada componente (creado en BD y/o registrado en CCT) y resaltando los elementos faltantes.

### Datos Disponibles
-   **Concepto de nómina**: ID del concepto, y de sus ajustes si aplica.
-   **Estado de componentes en BD**: Si cada FIELD, ITEM, PAYROLL ITEM, y la columna física asociada existe.
-   **Estado de registro en CCT**: Si cada componente está o no registrado en el CCT especificado.

### Ejemplos de Uso
**Verificar un concepto principal sin CCT:**
```bash
python -m tools.nomina.verify_payroll_concept "CVE_CUENTA_BIENESTAR"
```

**Verificar un concepto con su CCT:**
```bash
python -m tools.nomina.verify_payroll_concept "CVE_CUENTA_BIENESTAR" --cct-task-id "CONTROL_CAMBIO_258_2026"
```
