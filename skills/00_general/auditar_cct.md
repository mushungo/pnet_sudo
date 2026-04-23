---
nombre: "auditar_cct"
version: "1.2.0"
descripcion: "Detecta objetos de PeopleNet creados o modificados recientemente (por usuario o rango de fechas) que no están registrados en un CCT dado. Cobertura genérica: BDL, canales, nómina, presentaciones, reglas y sentencias."
parametros:
  - nombre: "cct_task_id"
    tipo: "string"
    descripcion: "El ID del Control de Cambio a auditar. Ej: CCT_TASK_ID."
    requerido: true
  - nombre: "id_secuser"
    tipo: "string"
    descripcion: "Opcional. Filtrar objetos tocados por este usuario (ID_SECUSER). Ej: usuario.ejemplo."
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
| CONCEPT | `M4RCH_CONCEPTS` | `ID_TI`, `ID_ITEM` (clave compuesta) |
| SENTENCE | `M4RCH_SENTENCES` | `ID_SENTENCE` |
| PHYSICAL SCRIPT | `INFORMATION_SCHEMA.COLUMNS` (tablas físicas SQL Server) | sin `DT_LAST_UPDATE` propio — inferido por los objetos lógicos asociados |

> **Nota:** Los PHYSICAL SCRIPTs no tienen campos auditables propios; se infieren a partir de los FIELDs o ITEMs lógicos que los referencian.

### Herramienta Python

Esta skill está respaldada por el script `tools/cct/audit_cct.py`, que implementa el flujo completo descrito a continuación:

```bash
python -m tools.cct.audit_cct "<CCT_TASK_ID>" --user <usuario.ejemplo>
python -m tools.cct.audit_cct "<CCT_TASK_ID>" --from <YYYY-MM-DD> --to <YYYY-MM-DD>
python -m tools.cct.audit_cct "<CCT_TASK_ID>" --user <usuario.ejemplo> --from <YYYY-MM-DD>
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

4. **Cruzar resultados con el CCT** (con verificación de parent): Comparar el conjunto de objetos encontrados en el barrido contra los `CCT_OBJECT_ID` ya registrados en el CCT. Para ITEM y FIELD se verifica también que el parent (canal `ID_TI` / objeto BDL `ID_OBJECT`) coincida. Se distinguen tres categorías:
    - **Ya en CCT con parent correcto**: cobertura completa.
    - **Gaps (faltan en CCT)**: objeto no registrado en absoluto.
    - **Wrong parent**: objeto registrado en CCT pero con parent distinto al de BD — hay entradas del CCT que apuntan a canales/objetos incorrectos.

5. **Detectar canales/objects sin cobertura (parent gaps)**: Para cada ITEM y FIELD barrido, verificar si el pair `(objeto, parent_BD)` está cubierto en el CCT. Si el objeto está registrado en el CCT para otros parents pero no para el parent de BD, se reporta en `parent_gaps`. Esta sección es complementaria a `wrong_parent`.

6. **Inferir PHYSICAL SCRIPTs faltantes**: Para cada FIELD barrido, determinar si existe una columna física asociada en las tablas SQL Server (via `INFORMATION_SCHEMA.COLUMNS`, patrón `M4<ID_OBJECT>%`) que no tenga un PHYSICAL SCRIPT registrado en el CCT.

7. **Clasificar RULE gaps como cubiertos por NS ITEM**: Las reglas de un ítem en un canal quedan automáticamente cubiertas cuando ese ITEM está registrado en el CCT para ese canal (el objeto RAMDL `NS ITEM` incluye todas las reglas vía `read-table SCH_RULES → call-object RULE`). Los gaps de RULE que tienen el ITEM padre registrado se clasifican como `covered_by_ns_item`.

8. **Generar informe de gaps**: Presentar un informe estructurado por tipo de objeto con las siguientes secciones:
    - **Ya en CCT**: objetos del barrido que ya están registrados (para confirmar cobertura).
    - **Gaps (faltan en CCT)**: objetos modificados en BD que no están en el CCT.
    - **Wrong parent**: objetos en el CCT con parent incorrecto.
    - **parent_gaps**: combinaciones (objeto, parent BD) no cubiertas en el CCT.
    - **physical_script_gaps**: columnas físicas sin PHYSICAL SCRIPT en el CCT.
    - **covered_by_ns_item** (solo RULE): reglas cubiertas implícitamente por el NS ITEM.
    - **Resumen**: conteo de gaps por tipo.

### Datos Disponibles en el Informe

- Cabecera del CCT: ID, versión, nombre, estado, si ha sido traspasado.
- Por cada objeto en el barrido: ID del objeto, tabla origen, usuario que lo modificó, fecha de modificación, rol utilizado.
- Estado de registro en el CCT: si el objeto ya está en `M4RCT_OBJECTS` o no, y si el parent es correcto.
- `parent_gaps`: lista de pares (objeto, parent BD) que faltan en el CCT aunque el objeto esté registrado para otros parents.
- `physical_script_gaps`: columnas físicas que existen en SQL Server sin PHYSICAL SCRIPT en el CCT.
- `covered_by_ns_item`: reglas de RULE cubiertas implícitamente por el NS ITEM del canal.
- Lista final de gaps con tipo de objeto.

### Notas Técnicas Importantes

- **`M4RCH_CONCEPTS`** usa clave compuesta `(ID_TI, ID_ITEM)`. No existe columna `ID_CONCEPT`.
- **`PHYSICAL SCRIPT`** no tiene tabla de metadatos propia con `DT_LAST_UPDATE`. Se infiere a partir de `INFORMATION_SCHEMA.COLUMNS` usando el patrón `M4 + ID_OBJECT` (truncado a 16 chars total) para encontrar la tabla física.
- **`NS ITEM`** (objeto RAMDL) incluye automáticamente todas las reglas del ítem en ese canal. No es necesario registrar reglas explícitamente si el ITEM está en el CCT.
- Los **PHYSICAL SCRIPTs** suelen cubrir varias tablas físicas en un solo registro de CCT (ej: ALTER TABLE en `M4CVE_AC_HR_PERIOD` y `M4CVE_SM_AC_HR_PER` en el mismo script). El `physical_script_gaps` puede dar falsos negativos si el script aún no se ha ejecutado (las columnas no existen en `INFORMATION_SCHEMA` hasta que se corra el ALTER TABLE).

### Ejemplos de Uso

**Auditar gaps de un CCT para objetos modificados por un usuario específico:**
```
Usa la skill auditar_cct con cct_task_id="<CCT_TASK_ID>" e id_secuser="<usuario.ejemplo>"
```

**Auditar gaps de un CCT para objetos tocados en un rango de fechas:**
```
Usa la skill auditar_cct con cct_task_id="<CCT_TASK_ID>", fecha_desde="<YYYY-MM-DD>" y fecha_hasta="<YYYY-MM-DD>"
```

**Auditar combinando usuario y rango de fechas:**
```
Usa la skill auditar_cct con cct_task_id="<CCT_TASK_ID>", id_secuser="<usuario.ejemplo>" y fecha_desde="<YYYY-MM-DD>"
```
