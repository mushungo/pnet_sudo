---
nombre: "describir_ti_bdl_schema"
version: "1.1.0"
descripcion: "Traza la relación inversa TI -> BDL -> objetos físicos SQL: dado un TI (o canal), muestra qué objetos lógicos BDL, tablas físicas SQL y columnas están vinculados."
parametros:
  - nombre: "id_ti"
    tipo: "string"
    descripcion: "El identificador del TI a trazar. Ej: EMPLOYEE_TI, SCO_REAL_TM_PRD."
    requerido: false
  - nombre: "id_t3"
    tipo: "string"
    descripcion: "El identificador del canal (T3). Expande todos los TIs montados en ese canal."
    requerido: false
  - nombre: "include_fields"
    tipo: "boolean"
    descripcion: "Si true, incluye el mapeo campo-a-campo (columna SQL <-> campo lógico BDL). Puede ser muy verboso."
    requerido: false
---

## Documentación de la Skill: `describir_ti_bdl_schema`

### Propósito

Esta skill permite a los agentes trazar la cadena completa desde un TI (Technical Instance) hasta las tablas físicas SQL que PeopleNet utiliza para leer y escribir datos. Es la pregunta inversa a "¿qué M4Objects usan esta tabla BDL?" — aquí se parte del TI y se llega a las tablas SQL.

La cadena de resolución es:

```
TI (M4RCH_TIS)
├─ ID_READ_OBJECT / ID_WRITE_OBJECT
│   └─ M4RDC_LOGIC_OBJECT (objeto lógico BDL)
│        └─ M4RDC_REAL_OBJECTS (tablas SQL físicas)
│             └─ M4RDC_REAL_FIELDS (columnas SQL <-> campos lógicos)
├─ ID_READ_SENTENCE / ID_WRITE_SENTENCE (APISQL, si existen)
└─ Items con overrides (M4RCH_ITEMS con ID_READ_OBJECT distinto al TI)
```

### Dos niveles de binding BD

En PeopleNet el vínculo con la BD existe en **dos niveles distintos**:

**Nivel TI** (`M4RCH_TIS`):
- `ID_READ_OBJECT` / `ID_WRITE_OBJECT` — objeto BDL por defecto para todo el bloque de datos del TI.
- `ID_READ_SENTENCE` / `ID_WRITE_SENTENCE` — sentence APISQL alternativa o complementaria para el bloque completo.
- Define el comportamiento de lectura/escritura de todos los items del bloque salvo que tengan override propio.

**Nivel item** (`M4RCH_ITEMS`):
- `ID_READ_OBJECT` / `ID_READ_FIELD` — objeto BDL y campo concreto del que lee **este item individualmente**.
- `ID_WRITE_OBJECT` / `ID_WRITE_FIELD` — objeto BDL y campo al que escribe **este item individualmente**.
- `ID_READ_SENTENCE` / `ID_WRITE_SENTENCE` — sentence que refina la lectura/escritura de este item.
- Cuando difiere del nivel TI, se denomina **override**: el item lee o escribe de un objeto BDL distinto al del bloque. Hay ~17k overrides de lectura y ~2.8k de escritura en esta BD.

Ver skill `binding_bd_items` para la documentación completa del mecanismo de binding a nivel de item.

**Nota importante:** Este tool detecta los overrides de items (items con `ID_READ_OBJECT` o `ID_WRITE_OBJECT` distinto al del TI padre) y resuelve sus cadenas BDL de forma independiente.

### Flujo de Trabajo

La skill invoca el script `tools/m4object/get_ti_bdl_schema.py`, que realiza:

1. **Si se pasa `--ti`**: Consulta `M4RCH_TIS` para obtener los objetos BDL y sentences del TI.
2. **Si se pasa `--t3`**: Consulta `M4RCH_NODES` JOIN `M4RCH_TIS` para expandir todos los TIs del canal.
3. **Por cada TI**:
   - Resuelve `ID_READ_OBJECT` y `ID_WRITE_OBJECT` contra `M4RDC_LOGIC_OBJECT`.
   - Para cada objeto lógico, obtiene las tablas físicas desde `M4RDC_REAL_OBJECTS`.
   - Con `--fields`, agrega el mapeo `M4RDC_REAL_FIELDS` (columna SQL <-> campo lógico).
   - Busca items con overrides de BDL (items que apuntan a objetos distintos al TI padre).
   - Resuelve las cadenas BDL de los overrides.
4. **Ensamblaje**: Genera un JSON con todos los objetos BDL y tablas SQL referenciadas, incluyendo un resumen.

### Datos Disponibles

- **TI**: ID, nombre ESP/ENG, TI base, flags (sistema, genera SQL).
- **Objetos BDL de lectura/escritura**: ID del objeto lógico, nombre real, descripción.
- **Sentences**: ID de sentence de lectura/escritura (si existen).
- **Tablas físicas SQL**: nombre de tabla, tipo (table/overflow/view/master_overflow), flag IS_PRINCIPAL, PK.
- **Campos** (con `--fields`): columna SQL, campo lógico BDL, objeto lógico.
- **Overrides de items**: items que apuntan a un BDL distinto al del TI padre, con sus propias cadenas BDL resueltas.
- **Resumen** (modo `--t3`): conteos de TIs, objetos BDL únicos, tablas SQL únicas.

### Casos de Uso Típicos

1. **"¿Qué tablas SQL escribe este TI?"** — para entender el impacto de una regla LN4 o un concepto de nómina.
2. **"¿Qué tablas físicas toca este canal?"** — para planificar un script SQL o un CCT.
3. **"¿Hay items que lean de tablas distintas al TI principal?"** — para detectar cross-joins o side effects.

### Ejemplos de Uso

**TI individual (básico):**
```bash
python -m tools.m4object.get_ti_bdl_schema --ti "EMPLOYEE_TI"
```

**Todos los TIs de un canal:**
```bash
python -m tools.m4object.get_ti_bdl_schema --t3 "SCO_MNG_DEV_PRODUCT"
```

**Con mapeo campo-a-campo:**
```bash
python -m tools.m4object.get_ti_bdl_schema --ti "EMPLOYEE_TI" --fields
```

**Resultado esperado (ejemplo simplificado):**
```json
{
  "status": "success",
  "mode": "single_ti",
  "ti": {
    "id_ti": "EMPLOYEE_TI",
    "name_esp": "Empleado",
    "read_object_id": "EMPLOYEES",
    "write_object_id": "EMPLOYEES",
    "read_bdl": {
      "id_object": "EMPLOYEES",
      "real_name": "Empleados",
      "physical_tables": [
        {
          "sql_table": "M4EMP_EMPLOYEE",
          "object_type": "table",
          "is_principal": true
        },
        {
          "sql_table": "M4EMP_EMPLOYEE_OVF",
          "object_type": "overflow",
          "is_principal": false
        }
      ]
    },
    "item_overrides": [
      {
        "id_item": "CVE_PHOTO",
        "read_object": "EMPLOYEE_PHOTOS",
        "write_object": "EMPLOYEE_PHOTOS"
      }
    ],
    "all_sql_tables": ["M4EMP_EMPLOYEE", "M4EMP_EMPLOYEE_OVF", "M4EMP_PHOTOS"]
  }
}
```
