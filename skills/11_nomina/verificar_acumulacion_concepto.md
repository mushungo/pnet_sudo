---
nombre: "verificar_acumulacion_concepto"
version: "1.0.0"
descripcion: "Determina si un concepto de nómina acumula su valor en un objeto BDL de acumulado, y en cuál. Basado en los campos ID_WRITE_OBJECT e ID_WRITE_FIELD de M4RCH_ITEMS."
parametros:
  - nombre: "id_ti"
    tipo: "string"
    descripcion: "El identificador del TI que contiene el concepto. Ej: 'ID_TI_CALCULO'."
    requerido: true
  - nombre: "id_item"
    tipo: "string"
    descripcion: "El identificador del item/concepto a verificar. Si se omite, devuelve todos los conceptos del TI clasificados."
    requerido: false
---

## Documentación de la Skill: `verificar_acumulacion_concepto`

### Propósito

Determina si un concepto de nómina **persiste su valor calculado** en un objeto BDL de acumulado al final de la pasada de cálculo, o si es un valor **transitorio** (auxiliar de cálculo que no se guarda).

### Fundamento técnico

Un concepto de nómina es un item de `M4RCH_ITEMS`. El motor persiste su valor si y solo si ese item tiene binding de escritura configurado. El mecanismo es el mismo para cualquier item de PeopleNet — no es específico de nómina. Ver skill `binding_bd_items` para la documentación completa del mecanismo.

En el contexto de nómina:

| Campo `M4RCH_ITEMS` | Valor | Significado |
|---|---|---|
| `ID_WRITE_OBJECT` | tiene valor | **Acumula** — el motor escribe el valor en ese objeto BDL al salvar |
| `ID_WRITE_OBJECT` | `NULL` | **No acumula** — valor transitorio de cálculo, no persiste en BD |
| `ID_WRITE_FIELD` | siempre acompaña a `ID_WRITE_OBJECT` | Campo específico del acumulado donde se escribe |

Los conceptos que **no acumulan** son típicamente: porcentajes, tasas, indicadores booleanos, bases de cálculo intermedias, contadores de días/horas de ausencia. Se usan durante la ejecución de la nómina pero su resultado no necesita persistirse.

### Verificar un concepto concreto

```sql
SELECT
    c.ID_TI,
    c.ID_ITEM,
    i.ID_WRITE_OBJECT                                        AS acumulado_destino,
    i.ID_WRITE_FIELD                                         AS campo_destino,
    CASE
        WHEN i.ID_WRITE_OBJECT IS NOT NULL THEN 'ACUMULA'
        ELSE 'NO ACUMULA'
    END                                                      AS acumula
FROM M4RCH_CONCEPTS c
JOIN M4RCH_ITEMS i ON i.ID_TI = c.ID_TI AND i.ID_ITEM = c.ID_ITEM
WHERE c.ID_TI  = '<ID_TI_CALCULO>'   -- sustituir por el TI objetivo
  AND c.ID_ITEM = '<ID_CONCEPTO>'    -- sustituir por el concepto a verificar
```

### Listar todos los conceptos de un TI clasificados

```sql
SELECT
    c.ID_ITEM,
    i.ID_WRITE_OBJECT                                        AS acumulado_destino,
    i.ID_WRITE_FIELD                                         AS campo_destino,
    CASE
        WHEN i.ID_WRITE_OBJECT IS NOT NULL THEN 'ACUMULA'
        ELSE 'NO ACUMULA'
    END                                                      AS acumula
FROM M4RCH_CONCEPTS c
JOIN M4RCH_ITEMS i ON i.ID_TI = c.ID_TI AND i.ID_ITEM = c.ID_ITEM
WHERE c.ID_TI = '<ID_TI_CALCULO>'    -- sustituir por el TI objetivo
ORDER BY acumula DESC, c.ID_ITEM
```

### Ejemplo ilustrativo (canal de cálculo de nómina genérico)

De N conceptos en un canal típico:
- **~79% acumulan** → escriben en el objeto BDL de acumulado de período (`*_AC_HR_PERIOD`)
- **~21% no acumulan** → porcentajes, tasas, indicadores booleanos, bases de prorrateo

```
CONCEPTO_SALARIO_BASE  → ACUMULA   (escribe en ID_ACUMULADO.CONCEPTO_SALARIO_BASE)
CONCEPTO_HORAS_EXTRA   → ACUMULA   (escribe en ID_ACUMULADO.CONCEPTO_HORAS_EXTRA)
CONCEPTO_PORCENTAJE    → NO ACUMULA
CONCEPTO_TASA_CAMBIO   → NO ACUMULA
CONCEPTO_DIAS_DESC     → NO ACUMULA
```

### Identificar el objeto BDL de acumulado

`ID_WRITE_OBJECT` contiene el ID del **objeto lógico BDL** del acumulado, no el nombre de la tabla física. Para obtener la tabla física:

```sql
SELECT
    o.ID_TRANS_OBJESP,
    o.REAL_NAME          AS tabla_fisica_principal
FROM M4RDC_LOGIC_OBJECT o
WHERE o.ID_TRANS_OBJESP = '<ID_WRITE_OBJECT>'   -- el valor de ID_WRITE_OBJECT
   OR o.ID_TRANS_OBJENG = '<ID_WRITE_OBJECT>'
```

Para ver todas las tablas físicas del acumulado (principal + overflow), usar la skill `describir_ti_bdl_schema`.

### Estadísticas globales (referencia)

| Métrica | Valor |
|---|---|
| Total conceptos en BD con `ID_WRITE_OBJECT` (acumulan) | ~949 |
| Total conceptos en BD sin `ID_WRITE_OBJECT` (no acumulan) | ~255 |
| Porcentaje que acumula | ~79% |
| Objetos BDL de escritura habituales | `*_AC_HR_PERIOD` (acumulados de período), `*_SM_AC_HR_PERIOD` (semestral), `SCO_AC_HR_PERIOD` (estándar) |

### Relaciones con otras skills

- **`binding_bd_items`** — Mecanismo general de binding BD de items; el presente skill es su aplicación al dominio de nómina.
- **`describir_ti_bdl_schema`** — Traza el objeto BDL destino hasta sus tablas físicas SQL.
- **`verificar_concepto_nomina`** — Verifica la integridad completa de un concepto (FIELDs, ITEMs, columna física, CCT).
