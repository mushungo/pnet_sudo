---
nombre: "describir_sentence_apisql"
version: "2.0.0"
descripcion: "Obtiene el SQL compilado (APISQL) de una sentence de PeopleNet, junto con el filtro abstracto y los objetos BDL referenciados. Incluye documentación completa del ciclo de vida del SQL en runtime."
parametros:
  - nombre: "id_sentence"
    tipo: "string"
    descripcion: "El identificador de la sentence. Ej: 'SENT_EMPLOYEES'."
    requerido: true
---

## Documentación de la Skill: `describir_sentence_apisql`

### Propósito
Obtiene el SQL compilado (APISQL) de una sentence de PeopleNet. Complementa la skill `describir_sentence` mostrando el SQL generado internamente por el motor, que usa un dialecto propietario.

---

### Dialecto APISQL
El APISQL no es SQL estándar. Usa una sintaxis propietaria de PeopleNet:
- `@FIELD = A.COLUMN` — Binding de SELECT: mapea una columna física al nombre lógico del campo en el canal
- `&OBJECT` — Referencia a un objeto BDL (el motor resuelve `&OBJECT` → tabla/vista física en runtime)
- `#FUNC()` — Funciones built-in del motor (`#TODAY()`, `#SUM()`, `#TRIM()`, `#COUNT(*)`, etc.)
- `?(type,size,prec)` — Parámetro tipado posicional (sustituido en runtime por el valor de `SYS_PARAM`)
  - type: 1=num, 2=str, 4=date, 5=datetime, 6=long
- `(+)` — Oracle-style outer join

---

### Las 4 Capas del Ciclo de Vida SQL en PeopleNet

El SQL que finalmente ejecuta el motor puede provenir de 4 capas distintas, en orden de precedencia:

#### Capa 1 — APISQL compilado en design-time (`M4RCH_SENTENCES3.APISQL`)
- Es la fuente de SQL estática definida en el diseñador de sentences.
- Cubre el **99.5%** de las sentences (aprox. 15.350 en total).
- Se usa por defecto cuando no hay `SYS_SENTENCE` ni `DYN_FILTER` activos.
- Se accede mediante la tool `get_sentence_apisql.py`.

#### Capa 2 — `SYS_SENTENCE` + `SYS_PARAM` (loading declarativo)
- `SYS_SENTENCE` (`ID_INTERNAL_TYPE = 20`) es un item Property que define qué SQL usar en la siguiente llamada a `Load_Blk()` / `Load_Prg()`.
- **7.636 items** de este tipo en la BD.
- Puede contener:
  - El **ID de una sentence** de `M4RCH_SENTENCES` (por nombre).
  - Un **APISQL inline** construido dinámicamente en código LN4 en runtime.
- Se asigna en LN4 justo antes del Load:
  ```ln4
  TI.SYS_SENTENCE = "FROM &OBJETO A WHERE A.CAMPO = ?(2,30,0)"
  TI.SYS_PARAM = valor_parametro
  TI.Load_Blk()
  ```
  O con el ID de una sentence existente:
  ```ln4
  TI.SYS_SENTENCE = "TABLE_FILTER"
  TI.Load_Blk()
  ```
- `SYS_PARAM` (`ID_INTERNAL_TYPE = 33`) es el receptor de los valores para los `?(type,size,prec)` del APISQL, en **orden posicional**.
  - **3.937 items** de este tipo en la BD.
  - Se referencia desde `SYS_SENTENCE` mediante `ID_ITEM_AUX` (relación en `M4RCH_ITEMS`).
  - Ejemplo real:
    ```ln4
    SCO_SYS_SENTENCE = ARG_SCO_SENTENCE
    SCO_SYS_PARAM = ARG_SCO_PARAM
    Load_Blk()
    ```
- Patrón con APISQL inline construido en LN4:
  ```ln4
  AD_DD_FIELDS.SYS_SENTENCE = "FROM &SDD_FIELDS A WHERE (" + FIELD_FILTER + ")"
  AD_DD_FIELDS.Load_Blk()
  ```
- Patrón con SELECT + parámetro dinámico:
  ```ln4
  SYS_SENTENCE = "SELECT @HAS_RECORDS = #COUNT(*) FROM &" + ID_OBJECT
  Load_Prg()
  ```

#### Capa 3 — `DYN_FILTER` (filtro de usuario en runtime)
- Existen **dos variantes**:

  **a) Columna `M4RCH_NODES.DYN_FILTER = 1`** (activación a nivel nodo):
  - Indica que el nodo acepta filtros dinámicos del usuario (Query Builder).
  - **91 nodos** en la BD tienen esta columna activa.
  - Cuando está activo, el motor ignora los `SYS_SENTENCE` de los items del nodo y aplica el filtro construido por el usuario.

  **b) Item `DYN_FILTER` (`ID_INTERNAL_TYPE = 34`)** (activación programática):
  - **86 items** de este tipo en la BD.
  - Se asigna desde LN4 como un APISQL inline:
    ```ln4
    DYN_FILTER = "SELECT @CAMPO = A.CAMPO FROM &OBJETO A WHERE A.STATUS = ?(2,1,0)"
    ```
  - Patrón típico: si `DYN_FILTER <> NullValue()`, el código LN4 resetea todos los `SYS_SENTENCE` del nodo a `" "` (vacío) para que el filtro dinámico tome control exclusivo.
  - Ejemplo real (canal `CVE_TR_HR_PERIOD`, regla `APPLY_DYN_FILTER`):
    ```ln4
    IF DYN_FILTER <> NullValue() THEN
        SYS_SENTENCE = " "
        SYS_SENTENCE_FILTER = " "
        Load_Blk()
    END IF
    ```

#### Capa 4 — `ExecuteSQL()` (APISQL imperativo)
- Es un item con regla CPP (no LN4) contenido en un TI de tipo `EXE_APISQL` (`ID_CSTYPE` correspondiente).
- Se usa para ejecutar APISQL imperativo fuera del flujo `Load_Blk` / `Load_Prg`.
- No sigue el ciclo de vida de sentences — es ejecución directa de SQL propietario.

---

### Resumen de Conteos en BD

| Concepto | Tabla | Condición | Cantidad |
|---|---|---|---|
| Sentences con APISQL | `M4RCH_SENTENCES3` | — | ~15.350 |
| Items SYS_SENTENCE | `M4RCH_ITEMS` | `ID_INTERNAL_TYPE = 20` | 7.636 |
| Items SYS_PARAM | `M4RCH_ITEMS` | `ID_INTERNAL_TYPE = 33` | 3.937 |
| Items DYN_FILTER | `M4RCH_ITEMS` | `ID_INTERNAL_TYPE = 34` | 86 |
| Nodos con DYN_FILTER activo | `M4RCH_NODES` | `DYN_FILTER = 1` | 91 |

---

### Tablas Consultadas

| Tabla | Contenido |
|---|---|
| `M4RCH_SENTENCES` | Metadatos de la sentence (`ID_SENT_TYPE`, `IS_DISTINCT`, etc.) |
| `M4RCH_SENTENCES1` | `FILTER` — template abstracto (filter clause) |
| `M4RCH_SENTENCES2` | APISQL parcial (FROM clause) |
| `M4RCH_SENTENCES3` | `APISQL` — SQL compilado completo (design-time) |
| `M4RCH_SENTENCES4` | APISQL extra (ORDER BY, GROUP BY) |
| `M4RCH_SENT_OBJECTS` | Objetos BDL referenciados (`ALIAS_OBJECT`, `IS_BASIS`) |
| `M4RCH_ITEMS` | Items SYS_SENTENCE / SYS_PARAM / DYN_FILTER (`ID_INTERNAL_TYPE`) |
| `M4RCH_NODES` | Nodos con `DYN_FILTER = 1` |

---

### Ejemplo de Uso
```bash
python -m tools.sentences.get_sentence_apisql "SENT_EMPLOYEES"
```

**Resultado esperado:**
```json
{
  "id_sentence": "SENT_EMPLOYEES",
  "is_distinct": false,
  "sent_type": 0,
  "filter_template": "@FIELD1 = A.COL1 AND @FIELD2 = B.COL2",
  "apisql_from": "FROM &EMPLOYEE A LEFT JOIN &DEPARTMENT B ON ...",
  "apisql": "SELECT @EMP_ID = A.ID_EMPLOYEE, @EMP_NAME = A.NAME FROM &EMPLOYEE A WHERE A.STATUS = ?(2,1,0)",
  "apisql_extra": "ORDER BY A.NAME",
  "objects": [
    {"id_object": "EMPLOYEE", "alias": "A", "is_basis": true}
  ]
}
```
