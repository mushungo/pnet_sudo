---
nombre: "auditar_cct"
version: "1.1.0"
descripcion: "Detecta objetos de PeopleNet creados o modificados recientemente (por usuario o rango de fechas) que no están registrados en un CCT dado. Cobertura genérica: BDL, canales, nómina, presentaciones, reglas y sentencias."
parametros:
  - nombre: "cct_task_id"
    tipo: "string"
    descripcion: "El ID del Control de Cambio a auditar. Ej: CONTROL_CAMBIO_258_2026."
    requerido: true
  - nombre: "id_secuser"
    tipo: "string"
    descripcion: "Opcional. Filtrar objetos tocados por este usuario (ID_SECUSER). Ej: JPEREZ."
    requerido: false
  - nombre: "fecha_desde"
    tipo: "string"
    descripcion: "Opcional. Fecha de inicio del rango de búsqueda en DT_LAST_UPDATE (formato YYYY-MM-DD). Ej: 2026-01-01."
    requerido: false
  - nombre: "fecha_hasta"
    tipo: "string"
    descripcion: "Opcional. Fecha de fin del rango de búsqueda en DT_LAST_UPDATE (formato YYYY-MM-DD). Si se omite, se usa la fecha actual."
    requerido: false
---

## Documentación de la Skill: `auditar_cct`

### Propósito

Esta skill detecta **gaps de registro en un CCT**: objetos de PeopleNet que han sido creados o modificados en la base de datos (según los campos auditables `ID_SECUSER`, `DT_LAST_UPDATE` e `ID_APPROLE` que PeopleNet rellena automáticamente en todas las tablas tecnológicas) pero que todavía **no están registrados** en el Control de Cambio indicado.

Es genérica y cubre todos los dominios de PeopleNet: BDL (fields), canales (items), nómina (payroll items), presentaciones (T3s), reglas y sentencias. No está acotada a ningún tipo de objeto concreto.

### Contexto: Campos Auditables Universales

PeopleNet rellena automáticamente tres campos en **todas** las tablas tecnológicas al crear o modificar un objeto:

| Campo | Descripción |
|---|---|
| `ID_SECUSER` | Usuario que realizó la última modificación. |
| `DT_LAST_UPDATE` | Fecha y hora de la última modificación. |
| `ID_APPROLE` | Rol de aplicación utilizado en esa operación. |

Esto permite hacer un barrido transversal de actividad sin depender del tipo de objeto.

### Tablas Tecnológicas Cubiertas

| Tipo CCT | Tabla de metadatos | Campo ID clave |
|---|---|---|
| FIELD | `M4RDC_FIELDS` | `ID_FIELD`, `ID_OBJECT` |
| ITEM | `M4RCH_ITEMS` | `ID_ITEM`, `ID_TI` |
| PAYROLL ITEM | `M4RCH_PAYROLL_ITEM` | `ID_PAYROLL_ITEM`, `ID_T3` |
| PRESENTATION | `M4RCH_T3S` | `ID_T3` |
| RULE | `M4RCH_RULES` | `ID_RULE`, `ID_TI` |
| CONCEPT | `M4RCH_CONCEPTS` | `ID_CONCEPT` |
| SENTENCE | `M4RCH_SENTENCES` | `ID_SENTENCE` |
| PHYSICAL SCRIPT | `INFORMATION_SCHEMA.COLUMNS` (tablas físicas SQL Server) | sin `DT_LAST_UPDATE` propio — inferido por los objetos lógicos asociados |

> **Nota:** Los PHYSICAL SCRIPTs no tienen campos auditables propios; se infieren a partir de los FIELDs o ITEMs lógicos que los referencian.

### Herramienta Python

Esta skill está respaldada por el script `tools/cct/audit_cct.py`, que implementa el flujo completo descrito a continuación:

```bash
python -m tools.cct.audit_cct "CONTROL_CAMBIO_258_2026" --user JPEREZ
python -m tools.cct.audit_cct "CONTROL_CAMBIO_258_2026" --from 2026-01-01 --to 2026-03-25
python -m tools.cct.audit_cct "CONTROL_CAMBIO_258_2026" --user JPEREZ --from 2026-03-01
```

Se requiere al menos `--user` o `--from` para acotar el barrido.

### Flujo de Trabajo

1. **Leer cabecera del CCT**: Consultar `M4RCT_TASK` con el `cct_task_id` dado para obtener estado, versión y nombre.

2. **Leer objetos ya registrados en el CCT**: Consultar `M4RCT_OBJECTS` para obtener todos los `CCT_OBJECT_ID` ya presentes en el CCT. Este es el conjunto de referencia para detectar gaps.

3. **Barrer tablas tecnológicas**: Para cada tabla de la lista anterior, ejecutar una consulta filtrando por `ID_SECUSER` y/o `DT_LAST_UPDATE` según los parámetros recibidos. Ejemplo de patrón de consulta:

    ```sql
    SELECT ID_FIELD, ID_OBJECT, ID_SECUSER, DT_LAST_UPDATE, ID_APPROLE
    FROM M4RDC_FIELDS
    WHERE ID_SECUSER = :id_secuser          -- si se proporcionó
      AND DT_LAST_UPDATE >= :fecha_desde    -- si se proporcionó
      AND DT_LAST_UPDATE <= :fecha_hasta    -- si se proporcionó
    ORDER BY DT_LAST_UPDATE DESC
    ```

    Repetir para `M4RCH_ITEMS`, `M4RCH_PAYROLL_ITEM`, `M4RCH_T3S`, `M4RCH_RULES`, `M4RCH_CONCEPTS`, `M4RCH_SENTENCES`.

4. **Cruzar resultados con el CCT**: Comparar el conjunto de objetos encontrados en el barrido contra los `CCT_OBJECT_ID` ya registrados en el CCT. Identificar los **objetos en BD que no están en el CCT** (gaps).

5. **Inferir PHYSICAL SCRIPTs faltantes**: Para cada FIELD o ITEM con gap detectado, determinar si existe una columna física asociada en las tablas SQL Server (via `INFORMATION_SCHEMA.COLUMNS`) que tampoco esté en el CCT como PHYSICAL SCRIPT.

6. **Generar informe de gaps**: Presentar un informe estructurado por tipo de objeto con tres secciones:
    - **Ya en CCT**: objetos del barrido que ya están registrados (para confirmar cobertura).
    - **Gaps (faltan en CCT)**: objetos modificados en BD que no están en el CCT — estos son los candidatos a añadir.
    - **Resumen**: conteo de gaps por tipo de objeto y recomendación de acción.

### Datos Disponibles en el Informe

- Cabecera del CCT: ID, versión, nombre, estado, si ha sido traspasado.
- Por cada objeto en el barrido: ID del objeto, tabla origen, usuario que lo modificó, fecha de modificación, rol utilizado.
- Estado de registro en el CCT: si el objeto ya está en `M4RCT_OBJECTS` o no.
- Lista final de gaps con tipo de objeto y acción sugerida (NEW o MODIFIED según si el objeto existía antes o es nuevo).

### Ejemplos de Uso

**Auditar gaps de un CCT para objetos modificados por un usuario específico:**
```
Usa la skill auditar_cct con cct_task_id="CONTROL_CAMBIO_258_2026" e id_secuser="JPEREZ"
```

**Auditar gaps de un CCT para objetos tocados en un rango de fechas:**
```
Usa la skill auditar_cct con cct_task_id="CONTROL_CAMBIO_258_2026", fecha_desde="2026-01-01" y fecha_hasta="2026-03-25"
```

**Auditar combinando usuario y rango de fechas:**
```
Usa la skill auditar_cct con cct_task_id="CONTROL_CAMBIO_258_2026", id_secuser="JPEREZ" y fecha_desde="2026-03-01"
```
